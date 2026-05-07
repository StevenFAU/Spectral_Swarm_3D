"""Phase 5 Tier 2.B: circular-shift surrogate null distributions (D1).

Implements trajectory-shuffled surrogates for Phi_spectral significance testing.
Each agent's time series is independently circularly shifted, destroying cross-agent
temporal dependence while preserving marginal distributions per agent (D1).

Public API
----------
circular_shift_telemetry(telemetry_array, rng) -> shuffled_array
surrogate_phi_spectral(telemetry_array, rng, n_shuffles, config) -> dict
run_surrogate_test(scenario_label, sweep_dir, condition, seed, rng_seed, ...) -> pd.DataFrame
"""
from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Circular shift (D1 shuffle protocol)
# ---------------------------------------------------------------------------

def circular_shift_telemetry(
    telemetry_array: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Independently circularly shift each agent's time series (D1).

    Implements Phase5.md §Tier 2.B surrogate protocol: per-agent random
    circular offset on the T-axis destroys cross-agent temporal dependence
    while preserving each agent's marginal distribution exactly.

    Parameters
    ----------
    telemetry_array : np.ndarray
        Shape (T, N, D) per-step per-agent feature array.
    rng : np.random.Generator
        Random generator for per-agent shift amounts (uniform over [0, T)).

    Returns
    -------
    np.ndarray
        Shape (T, N, D) shuffled copy with independent per-agent shifts.
        Marginal distributions per agent are preserved; cross-agent temporal
        dependence is destroyed.
    """
    T, N, _ = telemetry_array.shape
    shifts = rng.integers(0, T, size=N)
    shuffled = telemetry_array.copy()
    for n in range(N):
        shuffled[:, n, :] = np.roll(telemetry_array[:, n, :], int(shifts[n]), axis=0)
    return shuffled


# ---------------------------------------------------------------------------
# 2. Surrogate Phi_spectral distribution (per-window and mean-over-windows)
# ---------------------------------------------------------------------------

def surrogate_phi_spectral(
    telemetry_array: np.ndarray,
    rng: np.random.Generator,
    n_shuffles: int = 10,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute observed and surrogate Phi_spectral null distributions.

    Generates n_shuffles circular-shift surrogates and computes the per-window
    Phi_spectral time series for each. Headline metric is the mean-over-windows
    comparison per Phase5.md §135. Per-window null fractions support §139
    framing-(b) quantification.

    Parameters
    ----------
    telemetry_array : np.ndarray
        Shape (T, N, d) per-step per-agent feature array.
    rng : np.random.Generator
        Random generator for surrogate shifts.
    n_shuffles : int
        Number of circular-shift surrogates (D1 default: 10).
    config : dict, optional
        Analysis config; reads W, stride, estimator, k_ksg, mi_tie_break_noise.
        Defaults match default.yaml sweep settings (W=40, stride=5, ksg).

    Returns
    -------
    dict with keys:
        observed_phi              -- mean Phi over windows (headline observed)
        observed_windows          -- per-window Phi array, shape (n_windows,)
        surrogate_phi_distribution -- (n_shuffles,) array of per-surrogate means
        surrogate_mean            -- mean of surrogate distribution
        surrogate_95ci            -- (lo, hi) 2.5th/97.5th percentile of surrogates
        surrogate_std             -- std of surrogate distribution (ddof=1)
        z_score                   -- (observed_phi - surrogate_mean) / surrogate_std
        per_window_null_frac      -- (n_windows,) fraction of surrogates below observed
        surrogate_window_matrix   -- (n_shuffles, n_windows) per-window surrogate phis
    """
    from spectral_swarm_3d.analysis.spectral import phi_spectral_over_windows

    if config is None:
        config = {}

    W = int(config.get("W", 40))
    stride = int(config.get("stride", 5))
    estimator = str(config.get("estimator", "ksg"))

    est_kw: dict[str, Any] = {}
    if estimator == "ksg":
        est_kw = {
            "k": int(config.get("k_ksg", 5)),
            "noise_eps": float(config.get("mi_tie_break_noise", 1e-10)),
        }
    elif estimator == "histogram":
        est_kw = {"n_bins": int(config.get("n_bins_hist", 8))}

    # Observed per-window Phi
    observed_windows = phi_spectral_over_windows(
        telemetry_array, W=W, stride=stride, estimator=estimator, **est_kw
    )
    observed_phi = float(observed_windows.mean())

    # Surrogate per-window Phi distributions
    surr_window_lists: list[np.ndarray] = []
    for i in range(n_shuffles):
        _log.debug("Computing surrogate %d/%d...", i + 1, n_shuffles)
        shuffled = circular_shift_telemetry(telemetry_array, rng)
        surr_windows = phi_spectral_over_windows(
            shuffled, W=W, stride=stride, estimator=estimator, **est_kw
        )
        surr_window_lists.append(surr_windows)

    surr_matrix = np.array(surr_window_lists)  # (n_shuffles, n_windows)
    surr_means = surr_matrix.mean(axis=1)       # (n_shuffles,)

    surrogate_mean = float(surr_means.mean())
    surrogate_std = float(surr_means.std(ddof=1)) if n_shuffles > 1 else 0.0
    surrogate_95ci = (
        float(np.percentile(surr_means, 2.5)),
        float(np.percentile(surr_means, 97.5)),
    )
    z_score = (
        (observed_phi - surrogate_mean) / surrogate_std
        if surrogate_std > 0
        else float("nan")
    )

    # Per-window null fraction: at each window index, fraction of surrogate runs
    # whose Phi at that window is below the observed Phi. Supports §139 framing-(b).
    per_window_null_frac = (surr_matrix < observed_windows[None, :]).mean(axis=0)

    return {
        "observed_phi": observed_phi,
        "observed_windows": observed_windows,
        "surrogate_phi_distribution": surr_means,
        "surrogate_mean": surrogate_mean,
        "surrogate_95ci": surrogate_95ci,
        "surrogate_std": surrogate_std,
        "z_score": z_score,
        "per_window_null_frac": per_window_null_frac,
        "surrogate_window_matrix": surr_matrix,
    }


# ---------------------------------------------------------------------------
# 3. Per-scenario wrapper
# ---------------------------------------------------------------------------

def run_surrogate_test(
    scenario_label: str,
    sweep_dir: Path | str,
    condition: str,
    seed: int,
    rng_seed: int,
    n_shuffles: int = 10,
    *,
    config: dict[str, Any] | None = None,
    scenario_name: str | None = None,
) -> pd.DataFrame:
    """Per-scenario surrogate test: deterministically re-run, compute null distribution.

    Loads the exact config from the seed's metadata JSON (ensuring byte-identical
    reproduction per D6), re-runs the simulation to obtain raw telemetry features,
    then applies the D1 circular-shift surrogate protocol.

    The observed Phi is also cross-checked against the canonical parquet to verify
    methodology consistency (Phase5.md Tier 2.B validation check 2).

    Parameters
    ----------
    scenario_label : str
        Human-readable scenario label for output columns and CSV filenames.
    sweep_dir : Path | str
        Path to the sweep output directory (contains condition sub-directories
        with *.parquet and *.metadata.json files).
    condition : str
        Condition sub-directory name (e.g. "alpha_0.2", "wa_1.8").
    seed : int
        Simulation seed (pre-committed seed 0 per Phase5.md).
    rng_seed : int
        RNG seed for surrogate circular shifts.
    n_shuffles : int
        Number of circular-shift surrogates per D1 (default 10).
    config : dict, optional
        Explicit analysis config. If None, loaded from the seed's metadata JSON.
    scenario_name : str, optional
        BoidSwarmModel3D scenario name ("none", "jamming", "leader",
        "split_merge", "milling"). If None, read from metadata JSON.

    Returns
    -------
    pd.DataFrame
        Tidy frame with n_shuffles + 1 rows (one per surrogate plus observed).
        Columns: scenario, shuffle_idx, kind, phi_spectral_mean,
                 surrogate_mean, surrogate_95ci_lo, surrogate_95ci_hi,
                 z_score, surrogate_std, parquet_phi_mean, parquet_match.
        Surrogate rows have parquet_phi_mean=NaN and parquet_match=NaN.
    """
    from spectral_swarm_3d.analysis.features import extract_features
    from spectral_swarm_3d.model import BoidSwarmModel3D

    sweep_dir = Path(sweep_dir)
    cond_dir = sweep_dir / condition

    # Load config and scenario_name from metadata JSON if not provided
    meta_path = cond_dir / f"seed{seed}.metadata.json"
    if config is None or scenario_name is None:
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Metadata JSON not found: {meta_path}. "
                "Pass config and scenario_name explicitly or ensure parquet metadata exists."
            )
        with meta_path.open() as f:
            meta = json.load(f)
        if config is None:
            config = dict(meta["config"])
        if scenario_name is None:
            scenario_name = str(meta["scenario"])

    # Deterministic re-run to obtain raw telemetry (D6 seed-0 pre-commitment)
    _log.info(
        "Re-running %s (sweep=%s condition=%s scenario=%s seed=%d)...",
        scenario_label, sweep_dir.name, condition, scenario_name, seed,
    )
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        tel_path = Path(tf.name)

    try:
        model = BoidSwarmModel3D(
            config=config,
            scenario_name=scenario_name,
            seed=seed,
            telemetry_path=tel_path,
        )
        model.run()
        tel = pd.read_csv(tel_path)
    finally:
        tel_path.unlink(missing_ok=True)

    tel = tel.sort_values(["step", "agent_id"], kind="stable").reset_index(drop=True)
    feature_set = str(config.get("feature_set", "kinematic"))
    features = extract_features(tel, feature_set)

    # Load canonical parquet phi for cross-check (validation check 2)
    parquet_path = cond_dir / f"seed{seed}.parquet"
    parquet_phi_mean: float = float("nan")
    if parquet_path.exists():
        pq_df = pd.read_parquet(parquet_path)
        if "phi_spectral" in pq_df.columns:
            parquet_phi_mean = float(pq_df["phi_spectral"].mean())

    # Compute surrogate null distribution
    rng = np.random.default_rng(rng_seed)
    result = surrogate_phi_spectral(features, rng, n_shuffles=n_shuffles, config=config)

    observed_phi = result["observed_phi"]

    # Methodology consistency check: re-run phi vs canonical parquet phi
    if not np.isnan(parquet_phi_mean) and parquet_phi_mean > 0:
        rel_diff = abs(observed_phi - parquet_phi_mean) / parquet_phi_mean
        parquet_match = bool(rel_diff < 0.02)  # 2% tolerance; should be near-exact
    else:
        parquet_match = bool(not np.isnan(parquet_phi_mean))

    _log.info(
        "%s: observed_phi=%.3f parquet_phi=%.3f match=%s z=%.2f",
        scenario_label, observed_phi, parquet_phi_mean, parquet_match, result["z_score"],
    )

    # Build tidy DataFrame
    common: dict[str, Any] = {
        "scenario": scenario_label,
        "surrogate_mean": result["surrogate_mean"],
        "surrogate_95ci_lo": result["surrogate_95ci"][0],
        "surrogate_95ci_hi": result["surrogate_95ci"][1],
        "z_score": result["z_score"],
        "surrogate_std": result["surrogate_std"],
    }

    rows: list[dict[str, Any]] = [{
        **common,
        "shuffle_idx": -1,
        "kind": "observed",
        "phi_spectral_mean": observed_phi,
        "parquet_phi_mean": parquet_phi_mean,
        "parquet_match": parquet_match,
    }]
    for i, phi_mean in enumerate(result["surrogate_phi_distribution"]):
        rows.append({
            **common,
            "shuffle_idx": i,
            "kind": "surrogate",
            "phi_spectral_mean": float(phi_mean),
            "parquet_phi_mean": float("nan"),
            "parquet_match": float("nan"),
        })

    return pd.DataFrame(rows)
