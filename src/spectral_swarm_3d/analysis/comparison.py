"""Phase 5 — Cross-method comparison analysis (3D port of 2D Spectral_Swarm v0.1-2d-poc).

Public API
----------
load_sweep_runs(sweep_dir)
    Load all per-run Parquet files under a sweep directory.  Option A: returns a
    (sweep_data, is_shared_baseline) tuple; callers that do not need the sidecar
    can ignore the second element.

time_aligned_summary(window_df)
    Return a tidy DataFrame of spectral / TDA / classical metrics aligned by
    window_idx (3D replaces 2D's center_step with window_idx).

time_aligned_seed_mean(runs)
    Average time-aligned metrics across seeds.

cross_condition_sensitivity(sweep_data, n_bootstrap, collapse_shared_baseline)
    For each metric, compute eta-squared (one-way ANOVA effect size) across conditions.
    collapse_shared_baseline=True pools the eight VANILLA_BASELINE_CONDITIONS to one entry.

agreement_divergence_matrix(sweep_data, sweep_label, collapse_shared_baseline)
    Spearman rank correlation between phi_spectral and each TDA summary across the
    time series, per condition.

agreement_divergence_with_pvalues(sweep_data, sweep_label)
    Same as agreement_divergence_matrix but returns (rho_df, pval_df).

matched_control_deltas(sweep_data, control_label)
    Perturbation-minus-control steady-state deltas for each metric.

monitoring_roc(runs, t_on, t_off, W)
    Binary event detection: ROC AUC for each metric as a perturbation detector.
    3D uses t_start/t_end columns for strict-containment labelling.

per_window_distribution_summary(window_df, metric, steady_state_only)
    Bimodality diagnostics (dip p, KDE mode count, std/IQR, N) for one metric.
    Mirrors _make_distributions.py methodology so results agree codebase-wide.

Shared-baseline awareness
-------------------------
VANILLA_BASELINE_CONDITIONS enumerates the eight (sweep, condition) tuples that
are byte-identical vanilla-boids runs under D6 deterministic seeding (five at n=10,
three at n=5 sensitivity-default subset), verified at audit commit fec6079.

load_sweep_runs (Option A) returns a sidecar dict[str, bool] alongside the usual
condition -> runs mapping so callers can detect the equivalence without inspecting
the constant directly.  cross_condition_sensitivity and agreement_divergence_matrix
accept collapse_shared_baseline=False (default, matching 2D semantics); Tier 2.C
passes True to avoid inflating cross-scenario agreement metrics.
"""

from __future__ import annotations

from pathlib import Path

import diptest as _diptest
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema
from scipy.stats import gaussian_kde
from sklearn.metrics import roc_auc_score


# ---------------------------------------------------------------------------
# Metric groups — column names from analyze_run output (3D schema, Phase 4 C2)
# ---------------------------------------------------------------------------

SPECTRAL_METRICS = ["phi_spectral", "phi_norm"]

TDA_METRICS = [
    "snap_TP_0", "snap_MP_0", "snap_B_base_0", "snap_B_prev_0",
    "snap_TP_1", "snap_MP_1", "snap_B_base_1", "snap_B_prev_1",
    "snap_TP_2", "snap_MP_2", "snap_B_base_2", "snap_B_prev_2",
    "traj_TP_0", "traj_MP_0", "traj_B_base_0", "traj_B_prev_0",
    "traj_TP_1", "traj_MP_1", "traj_B_base_1", "traj_B_prev_1",
    "traj_TP_2", "traj_MP_2", "traj_B_base_2", "traj_B_prev_2",
]

CLASSICAL_METRICS = [
    "polarization", "milling_score", "angular_momentum_norm",
    "local_density", "LCC_fraction",
]

ALL_METRICS = SPECTRAL_METRICS + TDA_METRICS + CLASSICAL_METRICS

# TDA summaries used in agreement/divergence heatmaps — extended to H2 (C2)
_TDA_COMPARE = [
    "snap_TP_0", "snap_TP_1", "snap_TP_2",
    "snap_MP_0", "snap_MP_1", "snap_MP_2",
    "snap_B_base_0", "snap_B_base_1", "snap_B_base_2",
    "traj_TP_0", "traj_TP_1", "traj_TP_2",
    "traj_MP_0", "traj_MP_1", "traj_MP_2",
    "traj_B_base_0", "traj_B_base_1", "traj_B_base_2",
]

# ---------------------------------------------------------------------------
# Shared-baseline conditions (audit commit fec6079, audit_aggregates.json)
# ---------------------------------------------------------------------------

VANILLA_BASELINE_CONDITIONS: set[tuple[str, str]] = {
    # Five n=10 conditions — byte-identical vanilla-boids parquets
    ("jamming_sweep",             "alpha_1.0"),
    ("leadership_sweep",          "lambda_0.0"),
    ("milling_sweep",             "mu_0.0"),
    ("noise_sweep",               "sigma_0.05"),
    ("split_merge_sweep",         "none"),
    # Three n=5 sensitivity-default conditions — 5-seed subsets of the same set
    ("w_sensitivity",             "W40"),
    ("alignment_rule_sensitivity","mean"),
    ("sensitivity",               "ksg_kinematic"),
}

# Condition-name-only set for collapse lookups within a single sweep.
_VANILLA_CONDITION_NAMES: frozenset[str] = frozenset(
    cond for _, cond in VANILLA_BASELINE_CONDITIONS
)

# Bimodality thresholds — match _make_distributions.py exactly
_DIP_P_THRESHOLD = 0.20
_KDE_HEIGHT_FRAC = 0.05
_KDE_ORDER = 5
_SS_QUANTILE = 2 / 3


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sweep_runs(
    sweep_dir: Path,
) -> tuple[dict[str, list[tuple[int, pd.DataFrame]]], dict[str, bool]]:
    """Load all per-run Parquet files under a sweep directory.

    Option A shared-baseline design: returns a (sweep_data, is_shared_baseline)
    tuple so callers can detect vanilla-baseline equivalence without consulting
    VANILLA_BASELINE_CONDITIONS directly.  The second element is a sidecar dict
    mapping condition label -> bool; callers that do not need it can unpack as
    ``sweep_data, _ = load_sweep_runs(...)``.

    Returns:
        (sweep_data, is_shared_baseline) where:
          sweep_data maps condition label -> list of (seed, DataFrame) tuples.
          is_shared_baseline maps condition label -> True iff the condition is
          one of the eight VANILLA_BASELINE_CONDITIONS for this sweep.
        Both dicts are empty when sweep_dir does not exist.
    """
    sweep_dir = Path(sweep_dir)
    if not sweep_dir.is_dir():
        return {}, {}

    sweep_name = sweep_dir.name
    result: dict[str, list[tuple[int, pd.DataFrame]]] = {}
    for cond_dir in sorted(sweep_dir.iterdir()):
        if not cond_dir.is_dir():
            continue
        runs: list[tuple[int, pd.DataFrame]] = []
        for pq in sorted(cond_dir.glob("seed*.parquet")):
            seed = int(pq.stem.replace("seed", ""))
            runs.append((seed, pd.read_parquet(pq)))
        if runs:
            result[cond_dir.name] = runs

    is_shared: dict[str, bool] = {
        cond: (sweep_name, cond) in VANILLA_BASELINE_CONDITIONS
        for cond in result
    }
    return result, is_shared


# ---------------------------------------------------------------------------
# 1. Time-aligned summary
# ---------------------------------------------------------------------------

def time_aligned_summary(window_df: pd.DataFrame) -> pd.DataFrame:
    """Extract spectral, TDA, and classical metrics aligned by window_idx.

    3D parquets index windows by window_idx / t_start / t_end rather than
    2D's center_step.  This function uses window_idx as the alignment key;
    if window_idx is absent it falls back to t_start.

    Args:
        window_df: per-window DataFrame from analyze_run (one seed).

    Returns:
        DataFrame with window_idx as index and all available metric columns.
    """
    idx_col = "window_idx" if "window_idx" in window_df.columns else "t_start"
    cols = [idx_col] + [c for c in ALL_METRICS if c in window_df.columns]
    return window_df[cols].copy().set_index(idx_col)


def time_aligned_seed_mean(
    runs: list[tuple[int, pd.DataFrame]],
) -> pd.DataFrame:
    """Average time-aligned metrics across seeds (aligning on window_idx).

    Args:
        runs: list of (seed, window_df) tuples for one condition.

    Returns:
        DataFrame indexed by window_idx with mean metric values.
    """
    aligned = [time_aligned_summary(df) for _, df in runs]
    combined = pd.concat(aligned, keys=range(len(aligned)))
    return combined.groupby(level=1).mean()


# ---------------------------------------------------------------------------
# 2. Cross-condition sensitivity (eta-squared)
# ---------------------------------------------------------------------------

def _eta2_from_groups(group_values: list[np.ndarray]) -> float:
    """Compute eta-squared from a list of per-group value arrays."""
    all_vals = np.concatenate(group_values)
    grand_mean = all_vals.mean()
    ss_total = np.sum((all_vals - grand_mean) ** 2)
    ss_between = sum(len(v) * (v.mean() - grand_mean) ** 2 for v in group_values)
    return ss_between / ss_total if ss_total > 0 else 0.0


def _collapse_baseline(
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]],
) -> dict[str, list[tuple[int, pd.DataFrame]]]:
    """Pool all vanilla-baseline conditions into one 'vanilla_baseline' key."""
    merged: dict[str, list[tuple[int, pd.DataFrame]]] = {}
    baseline_runs: list[tuple[int, pd.DataFrame]] = []
    for condition, runs in sweep_data.items():
        if condition in _VANILLA_CONDITION_NAMES:
            baseline_runs.extend(runs)
        else:
            merged[condition] = runs
    if baseline_runs:
        merged["vanilla_baseline"] = baseline_runs
    return merged


def cross_condition_sensitivity(
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]],
    n_bootstrap: int = 0,
    collapse_shared_baseline: bool = False,
) -> pd.DataFrame:
    """Compute eta-squared for each metric across conditions.

    For each metric, performs one-way ANOVA across conditions using
    the steady-state mean (final third) per run. Eta-squared measures
    the fraction of variance explained by the condition label.

    Args:
        sweep_data: condition_label -> [(seed, window_df), ...].
        n_bootstrap: number of bootstrap resamples for 95% CI. When 0, ci_lo
            and ci_hi are NaN.
        collapse_shared_baseline: when True, pools the eight
            VANILLA_BASELINE_CONDITIONS into a single 'vanilla_baseline' entry
            before computing eta-squared.  Default False preserves 2D semantics.

    Returns:
        DataFrame indexed by metric name with columns eta2, ci_lo, ci_hi,
        sorted descending by eta2.
    """
    if collapse_shared_baseline:
        sweep_data = _collapse_baseline(sweep_data)

    condition_records: dict[str, list[dict]] = {}
    for condition, runs in sweep_data.items():
        recs = []
        for _, df in runs:
            n = len(df)
            cutoff = n * 2 // 3
            recs.append(df.iloc[cutoff:].mean(numeric_only=True).to_dict())
        condition_records[condition] = recs

    all_records = [
        {**rec, "condition": cond}
        for cond, recs in condition_records.items()
        for rec in recs
    ]

    if not all_records:
        return pd.DataFrame(columns=["eta2", "ci_lo", "ci_hi"])

    summary_df = pd.DataFrame(all_records)
    metrics = [c for c in ALL_METRICS if c in summary_df.columns]
    groups = summary_df.groupby("condition")

    eta2_vals: dict[str, float] = {}
    for m in metrics:
        group_values = [g[m].dropna().values for _, g in groups]
        group_values = [v for v in group_values if len(v) > 0]
        if len(group_values) < 2:
            eta2_vals[m] = np.nan
        else:
            eta2_vals[m] = _eta2_from_groups(group_values)

    ci_lo: dict[str, float] = {m: np.nan for m in metrics}
    ci_hi: dict[str, float] = {m: np.nan for m in metrics}

    if n_bootstrap > 0:
        rng_bs = np.random.default_rng(seed=0)
        bs_eta2: dict[str, list[float]] = {m: [] for m in metrics}

        condition_list = list(condition_records.keys())
        for _ in range(n_bootstrap):
            bs_records = []
            for cond in condition_list:
                recs = condition_records[cond]
                n = len(recs)
                idx = rng_bs.integers(0, n, size=n)
                bs_records.extend([{**recs[i], "condition": cond} for i in idx])

            bs_df = pd.DataFrame(bs_records)
            bs_groups = bs_df.groupby("condition")
            for m in metrics:
                gv = [g[m].dropna().values for _, g in bs_groups]
                gv = [v for v in gv if len(v) > 0]
                if len(gv) < 2:
                    bs_eta2[m].append(np.nan)
                else:
                    bs_eta2[m].append(_eta2_from_groups(gv))

        for m in metrics:
            arr = np.array(bs_eta2[m], dtype=float)
            finite = arr[np.isfinite(arr)]
            if len(finite) > 0:
                ci_lo[m] = float(np.percentile(finite, 2.5))
                ci_hi[m] = float(np.percentile(finite, 97.5))

    result = pd.DataFrame(
        {"eta2": eta2_vals, "ci_lo": ci_lo, "ci_hi": ci_hi}
    ).sort_values("eta2", ascending=False)
    return result


# ---------------------------------------------------------------------------
# 3. Agreement / divergence matrix (Spearman correlation)
# ---------------------------------------------------------------------------

def agreement_divergence_matrix(
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]],
    sweep_label: str = "",
    collapse_shared_baseline: bool = False,
) -> pd.DataFrame:
    """Spearman correlation of phi_spectral vs each TDA metric per condition.

    For each condition, computes the seed-averaged time series, then
    Spearman rank-correlates phi_spectral against each TDA summary.

    Args:
        sweep_data: condition_label -> [(seed, window_df), ...].
        sweep_label: optional label for the sweep (added as column).
        collapse_shared_baseline: when True, pools the eight
            VANILLA_BASELINE_CONDITIONS into 'vanilla_baseline' before
            computing correlations.  Default False preserves 2D semantics.

    Returns:
        DataFrame with columns: condition, sweep, <tda_metric_1>, ..., <tda_metric_n>.
        Values are Spearman rho.  Rows are conditions.
    """
    if collapse_shared_baseline:
        sweep_data = _collapse_baseline(sweep_data)

    rows: list[dict] = []
    for condition, runs in sweep_data.items():
        mean_ts = time_aligned_seed_mean(runs)
        if "phi_spectral" not in mean_ts.columns or len(mean_ts) < 3:
            continue

        row: dict[str, object] = {"condition": condition, "sweep": sweep_label}
        phi = mean_ts["phi_spectral"].values
        for tda_col in _TDA_COMPARE:
            if tda_col not in mean_ts.columns:
                row[tda_col] = np.nan
                continue
            tda_vals = mean_ts[tda_col].values
            mask = np.isfinite(phi) & np.isfinite(tda_vals)
            if mask.sum() < 3:
                row[tda_col] = np.nan
                continue
            rho, _ = stats.spearmanr(phi[mask], tda_vals[mask])
            row[tda_col] = rho
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def agreement_divergence_with_pvalues(
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]],
    sweep_label: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Spearman rho and p-values for phi_spectral vs each TDA metric per condition.

    Identical to agreement_divergence_matrix but also returns the p-value
    DataFrame so callers can assess statistical significance.

    Args:
        sweep_data: condition_label -> [(seed, window_df), ...].
        sweep_label: optional label for the sweep (added as column in both dfs).

    Returns:
        (rho_df, pval_df) — both have the same shape and column structure.
    """
    rho_rows: list[dict] = []
    pval_rows: list[dict] = []

    for condition, runs in sweep_data.items():
        mean_ts = time_aligned_seed_mean(runs)
        if "phi_spectral" not in mean_ts.columns or len(mean_ts) < 3:
            continue

        rho_row: dict[str, object] = {"condition": condition, "sweep": sweep_label}
        pval_row: dict[str, object] = {"condition": condition, "sweep": sweep_label}
        phi = mean_ts["phi_spectral"].values

        for tda_col in _TDA_COMPARE:
            if tda_col not in mean_ts.columns:
                rho_row[tda_col] = np.nan
                pval_row[tda_col] = np.nan
                continue
            tda_vals = mean_ts[tda_col].values
            mask = np.isfinite(phi) & np.isfinite(tda_vals)
            if mask.sum() < 3:
                rho_row[tda_col] = np.nan
                pval_row[tda_col] = np.nan
                continue
            rho, pval = stats.spearmanr(phi[mask], tda_vals[mask])
            rho_row[tda_col] = rho
            pval_row[tda_col] = pval

        rho_rows.append(rho_row)
        pval_rows.append(pval_row)

    if not rho_rows:
        empty = pd.DataFrame()
        return empty, empty

    return pd.DataFrame(rho_rows), pd.DataFrame(pval_rows)


# ---------------------------------------------------------------------------
# 4. Matched-control deltas
# ---------------------------------------------------------------------------

def matched_control_deltas(
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]],
    control_label: str,
) -> pd.DataFrame:
    """Perturbation-minus-control steady-state deltas for each metric.

    Args:
        sweep_data: condition_label -> [(seed, window_df), ...].
        control_label: which condition serves as control (e.g. "alpha_1.0").

    Returns:
        DataFrame with one row per non-control condition, columns are
        metric deltas (condition mean - control mean).
    """
    if control_label not in sweep_data:
        return pd.DataFrame()

    def condition_mean(runs: list[tuple[int, pd.DataFrame]]) -> dict[str, float]:
        summaries = []
        for _, df in runs:
            n = len(df)
            cutoff = n * 2 // 3
            summaries.append(df.iloc[cutoff:].mean(numeric_only=True))
        return pd.DataFrame(summaries).mean().to_dict()

    control_means = condition_mean(sweep_data[control_label])

    rows: list[dict] = []
    for condition, runs in sweep_data.items():
        if condition == control_label:
            continue
        cond_means = condition_mean(runs)
        delta: dict[str, object] = {"condition": condition}
        for m in ALL_METRICS:
            if m in cond_means and m in control_means:
                delta[m] = cond_means[m] - control_means[m]
        rows.append(delta)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# 5. Monitoring benchmark (ROC AUC)
# ---------------------------------------------------------------------------

def monitoring_roc(
    runs: list[tuple[int, pd.DataFrame]],
    t_on: int,
    t_off: int,
    W: int = 1,
) -> pd.Series:
    """Compute ROC AUC for each metric as a binary event detector.

    3D version uses t_start/t_end columns for strict-containment labelling
    (consistent with aggregation.aggregate_event_phases §3.8 semantics).
    A window is labelled 1 iff t_start >= t_on AND t_end <= t_off.

    W is kept for API parity with 2D but is unused when t_start/t_end are
    present; it is only applied as a half-width fallback if the DataFrame
    has center_step instead (legacy 2D data).

    Args:
        runs: list of (seed, window_df) for one condition.
        t_on: perturbation start step.
        t_off: perturbation end step.
        W: window width (unused in 3D; retained for API compatibility).

    Returns:
        Series indexed by metric, values are AUC in [0.5, 1.0].
    """
    all_labels: list[np.ndarray] = []
    all_scores: dict[str, list[np.ndarray]] = {}

    for _, df in runs:
        if "t_start" in df.columns and "t_end" in df.columns:
            label = (
                (df["t_start"].values >= t_on) & (df["t_end"].values <= t_off)
            ).astype(int)
        else:
            # Fallback: 2D center_step strict-containment
            half_l = W // 2
            half_r = W - half_l
            cs = df["center_step"].values
            label = ((cs - half_l >= t_on) & (cs + half_r <= t_off)).astype(int)
        all_labels.append(label)
        for m in ALL_METRICS:
            if m in df.columns:
                all_scores.setdefault(m, []).append(df[m].values)

    labels = np.concatenate(all_labels)
    if labels.sum() == 0 or labels.sum() == len(labels):
        return pd.Series(dtype=float)

    aucs: dict[str, float] = {}
    for m, score_arrays in all_scores.items():
        scores = np.concatenate(score_arrays)
        finite = np.isfinite(scores)
        if finite.sum() < 10 or labels[finite].sum() == 0:
            aucs[m] = np.nan
            continue
        auc = roc_auc_score(labels[finite], scores[finite])
        aucs[m] = max(auc, 1.0 - auc)

    return pd.Series(aucs).sort_values(ascending=False)


# ---------------------------------------------------------------------------
# 6. Per-window distribution summary (D14 reporting hook)
# ---------------------------------------------------------------------------

def per_window_distribution_summary(
    window_df: pd.DataFrame,
    metric: str,
    steady_state_only: bool = True,
) -> dict:
    """Bimodality diagnostics for one metric across per-window values.

    Mirrors the methodology from outputs/tier1_compressibility/distributions/
    _make_distributions.py exactly so results agree across the codebase:
      - diptest.diptest for Hartigan's dip statistic and p-value
      - scipy.stats.gaussian_kde with default bandwidth
      - argrelextrema(order=5) for local-maximum detection
      - local maxima must exceed 5% of KDE peak height to count as modes
      - steady-state: window_idx >= quantile(2/3) when steady_state_only=True

    Used by Tier 3.A figure generation and Tier 2.C aggregated bimodality columns.

    Args:
        window_df: per-window DataFrame for one seed (or pooled across seeds).
        metric: column name to analyse (e.g. 'phi_spectral').
        steady_state_only: if True, restrict to steady-state windows
            (window_idx >= quantile(2/3)).

    Returns:
        dict with keys:
          n_windows  -- number of windows analysed (after steady-state filter)
          dip_p      -- Hartigan's dip test p-value
          mode_count -- number of KDE modes above height threshold
          std_iqr    -- std / IQR ratio (NaN if IQR == 0)
          bimodal    -- bool: dip_p < 0.20 AND mode_count >= 2
    """
    if metric not in window_df.columns:
        return {"n_windows": 0, "dip_p": np.nan, "mode_count": np.nan,
                "std_iqr": np.nan, "bimodal": False}

    if steady_state_only and "window_idx" in window_df.columns:
        thresh = window_df["window_idx"].quantile(_SS_QUANTILE)
        sub = window_df[window_df["window_idx"] >= thresh]
    else:
        sub = window_df

    vals = sub[metric].dropna().values

    if len(vals) < 5:
        return {"n_windows": int(len(vals)), "dip_p": np.nan, "mode_count": np.nan,
                "std_iqr": np.nan, "bimodal": False}

    _, dip_p = _diptest.diptest(vals)

    kde = gaussian_kde(vals)
    x = np.linspace(vals.min(), vals.max(), 2000)
    y = kde(x)
    height_thresh = _KDE_HEIGHT_FRAC * y.max()
    maxima_idx = argrelextrema(y, np.greater, order=_KDE_ORDER)[0]
    mode_count = max(int(np.sum(y[maxima_idx] >= height_thresh)), 1)

    q25, q75 = np.percentile(vals, [25, 75])
    iqr = q75 - q25
    std_iqr = float(vals.std(ddof=1) / iqr) if iqr > 0 else float("nan")

    return {
        "n_windows": int(len(vals)),
        "dip_p": float(dip_p),
        "mode_count": int(mode_count),
        "std_iqr": std_iqr,
        "bimodal": bool((mode_count >= 2) and (dip_p < _DIP_P_THRESHOLD)),
    }
