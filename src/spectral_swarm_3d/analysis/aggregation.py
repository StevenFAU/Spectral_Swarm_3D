"""Per-run aggregation and sweep-level statistics for the 3D swarm pipeline.

Phase 4 implementation. See SpectralSwarm3DPhases.md §Phase 4, C2, D2.

Functions
---------
analyze_run
    Full per-window analysis on one telemetry CSV (spectral + classical + TDA).
aggregate_steady_state
    Final-third steady-state summary with optional D2 bootstrap CIs.
aggregate_event_phases
    Pre/during/post event-phase aggregation per §3.8 strict containment.
time_to_coordination
    Steps to first sustained polarization above threshold.
aggregate_across_seeds
    Cross-seed mean + std from per-seed summaries.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

from spectral_swarm_3d.analysis.features import extract_features
from spectral_swarm_3d.analysis.mi import (
    mi_matrix_gaussian,
    mi_matrix_histogram,
    mi_matrix_ksg,
    standardize_window,
)
from spectral_swarm_3d.analysis.spectral import (
    fiedler_bipartition,
    normalized_laplacian,
    phi_spectral as _phi_spectral_fn,
)
from spectral_swarm_3d.analysis.tda import (
    compute_persistence,
    persistence_summaries,
    snapshot_cloud,
    trajectory_cloud,
)

_log = logging.getLogger(__name__)

_ESTIMATOR_FNS = {
    "ksg": mi_matrix_ksg,
    "histogram": mi_matrix_histogram,
    "gaussian": mi_matrix_gaussian,
}

# Columns excluded from bootstrap aggregation (index/label columns, not metrics).
_NON_METRIC_COLS = {"window_idx", "t_start", "t_end"}


def _lcc_fraction(positions: np.ndarray, threshold: float) -> float:
    """Fraction of agents in the largest connected component at radius *threshold*."""
    N = len(positions)
    if N == 0:
        return 0.0
    tree = cKDTree(positions)
    pairs = list(tree.query_pairs(r=threshold))
    if not pairs:
        return 1.0 / N
    rows_idx = [p[0] for p in pairs] + [p[1] for p in pairs]
    cols_idx = [p[1] for p in pairs] + [p[0] for p in pairs]
    adj = csr_matrix(
        (np.ones(2 * len(pairs), dtype=np.int8), (rows_idx, cols_idx)), shape=(N, N)
    )
    _, labels = connected_components(adj, directed=False)
    return float(np.bincount(labels).max()) / N


def _estimator_kwargs(config: dict) -> dict[str, Any]:
    estimator = config.get("estimator", "ksg")
    if estimator == "ksg":
        return {
            "k": int(config.get("k_ksg", 5)),
            "noise_eps": float(config.get("mi_tie_break_noise", 1e-10)),
        }
    if estimator == "histogram":
        return {"n_bins": int(config.get("n_bins_hist", 8))}
    return {}


def analyze_run(telemetry_path: str, config: dict) -> pd.DataFrame:
    """Full per-window analysis on one telemetry CSV. Implements Phase 4 / C2.

    For each sliding window (length W, stride S):

    * **Spectral**: MI matrix → normalized Laplacian → Fiedler bipartition →
      Φ_spectral (sum over cut) and ``phi_norm`` (per-cut-edge mean).
    * **Classical**: per-step polarization, milling score, angular-momentum norm
      averaged over the window; local_density from telemetry; LCC_fraction at
      the last step.
    * **Snapshot TDA**: Ripser on the last-step spatial snapshot (augmented if
      configured) → TP/MP/B_base/B_prev for k ∈ {0, 1, 2}.
    * **Trajectory TDA**: Ripser on the W×d trajectory cloud (standardized
      features) → same four summaries per dimension.

    Parameters
    ----------
    telemetry_path:
        Path to telemetry CSV produced by BoidSwarmModel3D.
    config:
        Full effective config. May include ``"scenario"`` for event-phase use
        downstream. The ``W``, ``stride``, ``feature_set``, ``estimator``,
        ``L``, ``snapshot_augmented``, ``snapshot_beta``, ``fixed_cc_threshold``,
        and ``tda_maxdim`` keys are read here.

    Returns
    -------
    pd.DataFrame
        One row per analysis window. Columns: ``window_idx``, ``t_start``,
        ``t_end``, then spectral / classical / snapshot-TDA / trajectory-TDA
        metric columns per C2.
    """
    tel = pd.read_csv(telemetry_path)
    tel = tel.sort_values(["step", "agent_id"], kind="stable").reset_index(drop=True)

    W = int(config.get("W", 40))
    stride = int(config.get("stride", 1))
    feature_set = str(config.get("feature_set", "kinematic"))
    estimator = str(config.get("estimator", "ksg"))
    L = float(config.get("L", 50.0))
    center = np.array([L / 2.0, L / 2.0, L / 2.0])
    snapshot_aug = bool(config.get("snapshot_augmented", False))
    beta = float(config.get("snapshot_beta", 0.35))
    cc_thresh = float(config.get("fixed_cc_threshold", 6.0))
    tda_maxdim = int(config.get("tda_maxdim", 2))

    if estimator not in _ESTIMATOR_FNS:
        raise ValueError(f"Unknown estimator {estimator!r}; expected {sorted(_ESTIMATOR_FNS)}")
    est_fn = _ESTIMATOR_FNS[estimator]
    est_kw = _estimator_kwargs(config)

    features = extract_features(tel, feature_set)  # (T, N, d)
    T_steps, N, _d = features.shape
    steps_sorted = np.sort(tel["step"].unique())

    # Pre-extract positions, velocities, local_density arrays: (T, N, 3) and (T, N).
    step_pos = tel[["x", "y", "z"]].to_numpy(dtype=np.float64).reshape(T_steps, N, 3)
    step_vel = tel[["vx", "vy", "vz"]].to_numpy(dtype=np.float64).reshape(T_steps, N, 3)
    step_ld = tel["local_density"].to_numpy(dtype=np.float64).reshape(T_steps, N)

    # Vectorize classical metrics across all T steps.
    # Polarization: ||(1/N) Σ v_hat_i||
    v_norms = np.linalg.norm(step_vel, axis=-1, keepdims=True)  # (T, N, 1)
    v_hat = step_vel / np.where(v_norms > 1e-12, v_norms, 1.0)
    v_hat = np.where(v_norms > 1e-12, v_hat, 0.0)
    all_pol = np.linalg.norm(v_hat.mean(axis=1), axis=-1)  # (T,)

    # Milling score: mean |r_hat × v_hat| per step
    r = step_pos - center  # (T, N, 3)
    r_norms = np.linalg.norm(r, axis=-1, keepdims=True)
    r_hat = r / np.where(r_norms > 1e-12, r_norms, 1.0)
    r_hat = np.where(r_norms > 1e-12, r_hat, 0.0)
    crosses = np.cross(r_hat, v_hat)  # (T, N, 3)
    all_ms = np.linalg.norm(crosses, axis=-1).mean(axis=1)  # (T,)

    # Angular momentum norm: ||(1/N) Σ r_i × v_i||
    L_vec = np.cross(r, step_vel).mean(axis=1)  # (T, 3)
    all_amn = np.linalg.norm(L_vec, axis=-1)  # (T,)

    # LCC fraction: computed at the last step of each window (cached).
    n_windows = (T_steps - W) // stride + 1
    last_step_idxs = {k * stride + W - 1 for k in range(n_windows)}
    lcc_cache: dict[int, float] = {
        t_idx: _lcc_fraction(step_pos[t_idx], cc_thresh) for t_idx in last_step_idxs
    }

    rows: list[dict[str, Any]] = []
    baseline_snap_dgms: list[np.ndarray] | None = None
    baseline_traj_dgms: list[np.ndarray] | None = None
    prev_snap_dgms: list[np.ndarray] | None = None
    prev_traj_dgms: list[np.ndarray] | None = None

    for k in range(n_windows):
        t0 = k * stride
        t1 = t0 + W

        window_feat = features[t0:t1]  # (W, N, d)
        Xs = standardize_window(window_feat)

        # Spectral
        M = est_fn(Xs, **est_kw)
        L_lap = normalized_laplacian(M)
        part = fiedler_bipartition(L_lap)
        phi = _phi_spectral_fn(M, part)
        cross_edges = int(np.triu(part[:, None] != part[None, :], k=1).sum())
        phi_n = phi / cross_edges if cross_edges > 0 else 0.0

        # Classical (window means from pre-computed arrays)
        pol = float(all_pol[t0:t1].mean())
        ms = float(all_ms[t0:t1].mean())
        amn = float(all_amn[t0:t1].mean())
        ld = float(step_ld[t0:t1].mean())
        lcc = lcc_cache[t1 - 1]

        # Snapshot TDA (last step of window)
        cloud_s = snapshot_cloud(
            step_pos[t1 - 1],
            augmented=snapshot_aug,
            velocities=step_vel[t1 - 1] if snapshot_aug else None,
            beta=beta,
        )
        snap_dgms = compute_persistence(cloud_s, maxdim=tda_maxdim)
        snap_sums = persistence_summaries(
            snap_dgms,
            baseline_dgms=baseline_snap_dgms,
            prev_dgms=prev_snap_dgms,
            maxdim=tda_maxdim,
        )

        # Trajectory TDA (standardized window features)
        traj_pts = trajectory_cloud(Xs)  # (N, W*d)
        traj_dgms = compute_persistence(traj_pts, maxdim=tda_maxdim)
        traj_sums = persistence_summaries(
            traj_dgms,
            baseline_dgms=baseline_traj_dgms,
            prev_dgms=prev_traj_dgms,
            maxdim=tda_maxdim,
        )

        if k == 0:
            baseline_snap_dgms = snap_dgms
            baseline_traj_dgms = traj_dgms
        prev_snap_dgms = snap_dgms
        prev_traj_dgms = traj_dgms

        row: dict[str, Any] = {
            "window_idx": k,
            "t_start": int(steps_sorted[t0]),
            "t_end": int(steps_sorted[t1 - 1]),
            "phi_spectral": phi,
            "phi_norm": phi_n,
            "polarization": pol,
            "milling_score": ms,
            "angular_momentum_norm": amn,
            "local_density": ld,
            "LCC_fraction": lcc,
        }
        for dim in range(tda_maxdim + 1):
            row[f"snap_TP_{dim}"] = snap_sums[f"TP_{dim}"]
            row[f"snap_MP_{dim}"] = snap_sums[f"MP_{dim}"]
            row[f"snap_B_base_{dim}"] = snap_sums[f"B_base_{dim}"]
            row[f"snap_B_prev_{dim}"] = snap_sums[f"B_prev_{dim}"]
        for dim in range(tda_maxdim + 1):
            row[f"traj_TP_{dim}"] = traj_sums[f"TP_{dim}"]
            row[f"traj_MP_{dim}"] = traj_sums[f"MP_{dim}"]
            row[f"traj_B_base_{dim}"] = traj_sums[f"B_base_{dim}"]
            row[f"traj_B_prev_{dim}"] = traj_sums[f"B_prev_{dim}"]

        rows.append(row)

    _log.debug("analyze_run: %d windows from %s", n_windows, telemetry_path)
    return pd.DataFrame(rows)


def _metric_cols(df: pd.DataFrame) -> list[str]:
    """Return numeric columns excluding index/label columns."""
    numeric = df.select_dtypes(include=np.number).columns.tolist()
    return [c for c in numeric if c not in _NON_METRIC_COLS]


def aggregate_steady_state(
    run_results: pd.DataFrame,
    config: dict,
    bootstrap_ci: bool = True,
    n_bootstrap: int = 1000,
) -> dict:
    """Aggregate the final-third steady-state windows. Implements D2.

    Parameters
    ----------
    run_results:
        Output of :func:`analyze_run`.
    config:
        Run config (unused directly; reserved for future window-length logic).
    bootstrap_ci:
        If True (default), compute 1000-resample 95% bootstrap CIs by
        resampling the steady-state windows with replacement (D2). Returns
        ``{"mean": {...}, "ci_lo": {...}, "ci_hi": {...}}``. If False, returns
        ``{column: mean}`` for backward compatibility.
    n_bootstrap:
        Number of bootstrap resamples (default 1000 per D2).

    Returns
    -------
    dict
        When ``bootstrap_ci=True``: ``{"mean": {col: float}, "ci_lo": {col: float},
        "ci_hi": {col: float}}``. When False: ``{col: float}``.
    """
    n = len(run_results)
    if n == 0:
        return {"mean": {}, "ci_lo": {}, "ci_hi": {}} if bootstrap_ci else {}
    steady_start = n - max(n // 3, 1)
    ss = run_results.iloc[steady_start:]
    cols = _metric_cols(ss)

    means = {c: float(ss[c].mean()) for c in cols}

    if not bootstrap_ci:
        return means

    n_ss = len(ss)
    vals = ss[cols].to_numpy(dtype=np.float64)  # (n_ss, n_cols)
    rng = np.random.default_rng(0)  # fixed seed: reproducible CIs for same data
    idx = rng.integers(0, n_ss, size=(n_bootstrap, n_ss))
    boot_means = vals[idx].mean(axis=1)  # (n_bootstrap, n_cols)
    ci_lo = dict(zip(cols, np.percentile(boot_means, 2.5, axis=0).tolist()))
    ci_hi = dict(zip(cols, np.percentile(boot_means, 97.5, axis=0).tolist()))

    return {"mean": means, "ci_lo": ci_lo, "ci_hi": ci_hi}


def aggregate_event_phases(
    run_results: pd.DataFrame,
    config: dict,
    bootstrap_ci: bool = True,
    n_bootstrap: int = 1000,
) -> dict[str, dict | None]:
    """Aggregate pre/during/post event-phase windows (strict containment §3.8).

    A window is assigned to a phase iff it is *fully contained*:

    * **pre**: ``t_end < t_on``
    * **during**: ``t_start >= t_on`` and ``t_end <= t_off``
    * **post**: ``t_start > t_off``

    Transition windows (overlapping a phase boundary) are excluded.

    Parameters
    ----------
    run_results:
        Output of :func:`analyze_run`.
    config:
        Must contain the scenario and corresponding event-timing keys.
        Scenario is read from ``config.get("scenario", "none")``.
        Jamming: ``jam_t_on``, ``jam_t_off``. Split-merge: ``split_t_on``,
        ``split_t_off``.
    bootstrap_ci:
        Whether to compute bootstrap CIs within each phase (D2). Resamples
        within-phase only.
    n_bootstrap:
        Number of bootstrap resamples.

    Returns
    -------
    dict
        ``{"pre": result_or_None, "during": result_or_None, "post": result_or_None}``.
        Phases with no windows are ``None``. Result format matches
        :func:`aggregate_steady_state`.
    """
    scenario = str(config.get("scenario", "none"))
    t_on: int | None = None
    t_off: int | None = None
    if scenario == "jamming":
        t_on = int(config.get("jam_t_on", 0))
        t_off = int(config.get("jam_t_off", 9999))
    elif scenario == "split_merge":
        t_on = int(config.get("split_t_on", 0))
        t_off = int(config.get("split_t_off", 9999))

    if t_on is None:
        return {"pre": None, "during": None, "post": None}

    df = run_results
    t_s, t_e = df["t_start"], df["t_end"]

    def _agg(mask: pd.Series) -> dict | None:
        sub = df[mask]
        if len(sub) == 0:
            return None
        cols = _metric_cols(sub)
        means = {c: float(sub[c].mean()) for c in cols}
        if not bootstrap_ci:
            return means
        n_sub = len(sub)
        vals = sub[cols].to_numpy(dtype=np.float64)
        rng = np.random.default_rng(0)
        idx = rng.integers(0, n_sub, size=(n_bootstrap, n_sub))
        boot_means = vals[idx].mean(axis=1)
        ci_lo = dict(zip(cols, np.percentile(boot_means, 2.5, axis=0).tolist()))
        ci_hi = dict(zip(cols, np.percentile(boot_means, 97.5, axis=0).tolist()))
        return {"mean": means, "ci_lo": ci_lo, "ci_hi": ci_hi}

    return {
        "pre": _agg(t_e < t_on),
        "during": _agg((t_s >= t_on) & (t_e <= t_off)),
        "post": _agg(t_s > t_off),
    }


def time_to_coordination(
    run_results: pd.DataFrame,
    threshold: float = 0.65,
    n_consecutive: int = 2,
) -> int:
    """Steps to first sustained polarization >= *threshold* for *n_consecutive* windows.

    Returns the ``t_start`` step of the first qualifying window, or -1 if the
    criterion is never met.
    """
    if "polarization" not in run_results.columns:
        return -1
    pol = run_results["polarization"].to_numpy()
    t_starts = run_results["t_start"].to_numpy()
    n = len(pol)
    for i in range(n - n_consecutive + 1):
        if np.all(pol[i : i + n_consecutive] >= threshold):
            return int(t_starts[i])
    return -1


def aggregate_across_seeds(seed_summaries: list[dict], config: dict) -> dict:
    """Combine per-seed steady-state summaries into sweep-level stats.

    Computes mean and std of per-seed *means* across seeds. Per-seed bootstrap
    CIs are kept separate and not pooled — they represent within-run uncertainty,
    while std-of-means represents across-run variability.

    Parameters
    ----------
    seed_summaries:
        List of outputs from :func:`aggregate_steady_state`. Each entry may be
        either ``{"mean": {col: val}, "ci_lo": ..., "ci_hi": ...}`` (bootstrap)
        or ``{col: val}`` (no bootstrap). Mixed lists are handled.
    config:
        Run config (unused directly; reserved).

    Returns
    -------
    dict
        ``{col: {"mean": float, "std": float, "n": int}}``.
    """
    means_list: list[dict[str, float]] = []
    for s in seed_summaries:
        if isinstance(s, dict) and "mean" in s and isinstance(s["mean"], dict):
            means_list.append(s["mean"])
        else:
            means_list.append({k: v for k, v in s.items() if isinstance(v, (int, float))})

    if not means_list:
        return {}

    all_cols: list[str] = list(means_list[0].keys())
    result: dict[str, dict] = {}
    for col in all_cols:
        vals = np.array(
            [m[col] for m in means_list if col in m],
            dtype=np.float64,
        )
        result[col] = {
            "mean": float(np.nanmean(vals)) if vals.size else float("nan"),
            "std": float(np.nanstd(vals)) if vals.size else float("nan"),
            "n": int(vals.size),
        }
    return result
