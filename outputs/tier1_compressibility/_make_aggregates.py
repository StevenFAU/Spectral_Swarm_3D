"""Phase 5 Tier 1.A — leadership prediction aggregate computation.

Reproducible analysis script. Run from repo root::

    /home/otacon/Spectral_Swarm_3D/.venv/bin/python3 outputs/tier1_compressibility/_make_aggregates.py

Outputs
-------
- ``outputs/tier1_compressibility/aggregates.json`` — all numeric support for
  the verdict (per-condition Φ / σ_u / compactness, pairwise comparisons,
  bimodality, mechanism diagnostic, per-seed table).
- ``outputs/tier1_compressibility/mechanism_diagnostic.npz`` — MI matrices,
  positions, partitions for the rep windows (used by the figure scripts).

Method
------
1. Read the existing per-window parquets (``outputs/leadership_sweep/...``)
   for Φ_spectral and phi_norm time series (already computed in Phase 4).
2. Re-run the simulator for each (λ, seed) — bit-reproducible (D6) — and
   capture per-step positions and unit-velocities. Compute per-window σ_u
   (within-agent directional std) and leader-group compactness (mean
   pairwise distance among agents with ``is_leader == True``).
3. Aggregate across seeds with 1000-resample bootstrap CIs (D2 protocol).
4. Pairwise comparisons of per-seed steady-state Φ across {0.0, 0.8, 1.6}
   each vs 2.4 (Cohen's d on per-seed means + bootstrap CI on the
   mean difference).
5. Mechanism diagnostic: for one representative seed each at λ=0.0 and
   λ=2.4 (rep = closest to cross-seed median per-seed Φ), and one
   representative steady-state window (closest to per-seed mean Φ),
   compute the MI matrix and the full A2 row of structural descriptors.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from scipy.cluster.vq import kmeans2
from scipy.spatial.distance import pdist, squareform

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.features import extract_features
from spectral_swarm_3d.analysis.mi import mi_matrix_ksg, standardize_window
from spectral_swarm_3d.analysis.spectral import (
    fiedler_bipartition,
    fiedler_vector,
    normalized_laplacian,
    phi_spectral as phi_spectral_fn,
)
from spectral_swarm_3d.model import BoidSwarmModel3D

import diptest  # noqa: E402


CONDITIONS = [0.0, 0.8, 1.6, 2.4]
SEEDS = list(range(10))
T_STEPS = 500
W = 40
STRIDE = 5
B_BOOT = 1000  # D2 bootstrap resamples
RNG_SEED = 0  # for bootstrap reproducibility

OUT_DIR = REPO_ROOT / "outputs" / "tier1_compressibility"
PARQUET_ROOT = REPO_ROOT / "outputs" / "leadership_sweep"
CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"


# =============================================================================
# Simulator re-run helpers
# =============================================================================


def _build_config(leader_strength: float) -> dict[str, Any]:
    """Build config matching the leadership_sweep parquets (stride=5 per B2)."""
    with open(CONFIG_PATH) as f:
        base = yaml.safe_load(f)
    cfg = dict(base)
    cfg["stride"] = STRIDE
    cfg["leader_strength"] = float(leader_strength)
    cfg["scenario"] = "leader"
    return cfg


def run_and_capture(
    leader_strength: float, seed: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Re-run simulator deterministically; return (positions, velocities, is_leader).

    positions, velocities: (T, N, 3). is_leader: (N,) boolean.
    """
    cfg = _build_config(leader_strength)
    model = BoidSwarmModel3D(cfg, scenario_name="leader", seed=seed)
    is_leader = np.array([ag.leader_group >= 0 for ag in model.swarm], dtype=bool)
    N = len(model.swarm)
    positions = np.empty((T_STEPS, N, 3), dtype=np.float64)
    velocities = np.empty((T_STEPS, N, 3), dtype=np.float64)
    for t in range(T_STEPS):
        model.step()
        positions[t] = model._positions()
        velocities[t] = model._velocities()
    return positions, velocities, is_leader


def features_via_telemetry(leader_strength: float, seed: int) -> np.ndarray:
    """Re-run simulator with telemetry capture and return ``extract_features`` output.

    This routes through the canonical CSV → ``extract_features`` path (same as
    ``analyze_run``) so that downstream MI matrices match the published parquets
    bit-for-bit. Direct in-process feature construction can drift after
    ``standardize_window`` because the speed channel has ε-level float jitter
    that is rounded differently by CSV write/read vs. raw numpy.

    Returns
    -------
    np.ndarray, shape (T, N, 4) — kinematic features (speed, u_x, u_y, u_z).
    """
    import tempfile

    cfg = _build_config(leader_strength)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        tel_path = Path(tf.name)
    try:
        model = BoidSwarmModel3D(
            cfg, scenario_name="leader", seed=seed, telemetry_path=tel_path
        )
        model.run(T=T_STEPS)
        tel = pd.read_csv(tel_path)
        features = extract_features(tel, "kinematic")
        return features
    finally:
        tel_path.unlink(missing_ok=True)


# =============================================================================
# Per-window features from re-run state
# =============================================================================


def windowed_sigma_u_per_window(
    velocities: np.ndarray, speed: float = 1.0
) -> np.ndarray:
    """Per-window σ_u: per-agent L2 norm of per-channel stds, averaged across agents.

    Parameters
    ----------
    velocities : (T, N, 3)
    speed : float, default 1.0 (held invariant by the model)

    Returns
    -------
    np.ndarray, shape (n_windows,) — per-window σ_u.
    """
    u = velocities / speed  # (T, N, 3) — unit velocities since speed is invariant
    n_windows = (T_STEPS - W) // STRIDE + 1
    out = np.empty(n_windows, dtype=np.float64)
    for k in range(n_windows):
        t0 = k * STRIDE
        win = u[t0 : t0 + W]  # (W, N, 3)
        per_chan_std = win.std(axis=0, ddof=0)  # (N, 3)
        per_agent_l2 = np.linalg.norm(per_chan_std, axis=1)  # (N,)
        out[k] = float(per_agent_l2.mean())
    return out


def windowed_compactness_per_window(
    positions: np.ndarray, is_leader: np.ndarray
) -> np.ndarray:
    """Per-window leader-group compactness = mean pairwise distance among leaders.

    Per step: mean of pairwise leader-leader distances. Per window: average
    across the W=40 steps in the window.

    Parameters
    ----------
    positions : (T, N, 3)
    is_leader : (N,) bool

    Returns
    -------
    np.ndarray, shape (n_windows,) — per-window mean leader pairwise distance.
    """
    leader_idx = np.where(is_leader)[0]
    if leader_idx.size < 2:
        n_windows = (T_STEPS - W) // STRIDE + 1
        return np.full(n_windows, np.nan, dtype=np.float64)
    n_windows = (T_STEPS - W) // STRIDE + 1
    out = np.empty(n_windows, dtype=np.float64)
    # Per-step pairwise mean distance among leaders, then window average.
    leader_pos = positions[:, leader_idx, :]  # (T, k_lead, 3)
    per_step_means = np.empty(T_STEPS, dtype=np.float64)
    for t in range(T_STEPS):
        d = pdist(leader_pos[t], metric="euclidean")
        per_step_means[t] = float(d.mean())
    for k in range(n_windows):
        t0 = k * STRIDE
        out[k] = float(per_step_means[t0 : t0 + W].mean())
    return out


# =============================================================================
# Aggregation: per-seed steady-state means and bootstrap CIs
# =============================================================================


def steady_state_indices(n_windows: int) -> slice:
    """Final third of windows (matches aggregate_steady_state semantics)."""
    start = n_windows - max(n_windows // 3, 1)
    return slice(start, n_windows)


def bootstrap_ci(values: np.ndarray, b: int = B_BOOT, seed: int = RNG_SEED) -> tuple[float, float]:
    """Percentile bootstrap CI on the mean (resampling the input with replacement)."""
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(b, values.size))
    boot_means = values[idx].mean(axis=1)
    return float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's d (pooled std with ddof=1) on two equal-size groups of seed means."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    s_a = a.std(ddof=1)
    s_b = b.std(ddof=1)
    pooled = np.sqrt((s_a ** 2 + s_b ** 2) / 2.0)
    if pooled == 0:
        return float("inf") if a.mean() != b.mean() else 0.0
    return float((a.mean() - b.mean()) / pooled)


def bootstrap_diff_ci(
    a: np.ndarray, b: np.ndarray, seed: int = RNG_SEED
) -> tuple[float, float]:
    """Bootstrap CI on (mean(a) - mean(b)), resampling each group independently."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx_a = rng.integers(0, a.size, size=(B_BOOT, a.size))
    idx_b = rng.integers(0, b.size, size=(B_BOOT, b.size))
    diffs = a[idx_a].mean(axis=1) - b[idx_b].mean(axis=1)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


# =============================================================================
# Bimodality diagnostics on pooled per-window Φ
# =============================================================================


def kde_mode_count(
    values: np.ndarray, height_frac: float = 0.10, n_grid: int = 512
) -> int:
    """Count local maxima in a Gaussian KDE of *values* above height_frac × max.

    Default bandwidth (Silverman). Mode = strict local max on the grid above
    a height threshold to suppress KDE wiggle.
    """
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 3 or np.ptp(values) == 0:
        return 1
    kde = stats.gaussian_kde(values)
    lo, hi = values.min(), values.max()
    pad = 0.05 * (hi - lo + 1e-12)
    grid = np.linspace(lo - pad, hi + pad, n_grid)
    pdf = kde(grid)
    threshold = float(pdf.max()) * height_frac
    # Strict interior local maxima above threshold.
    is_max = (pdf[1:-1] > pdf[:-2]) & (pdf[1:-1] > pdf[2:]) & (pdf[1:-1] > threshold)
    n_modes = int(is_max.sum())
    return max(n_modes, 1)


def std_iqr_ratio(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 2:
        return float("nan")
    iqr = float(np.percentile(values, 75) - np.percentile(values, 25))
    if iqr == 0:
        return float("inf")
    return float(values.std(ddof=0) / iqr)


def bimodality_diagnostics(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 4:
        return {
            "dip_stat": float("nan"),
            "dip_p": float("nan"),
            "kde_modes": 1,
            "std_over_iqr": float("nan"),
            "n": int(values.size),
        }
    dip, p = diptest.diptest(values)
    return {
        "dip_stat": float(dip),
        "dip_p": float(p),
        "kde_modes": kde_mode_count(values),
        "std_over_iqr": std_iqr_ratio(values),
        "n": int(values.size),
    }


# =============================================================================
# Mechanism diagnostic — A2 reference signature on representative windows
# =============================================================================


def fiedler_kmeans_pair_agreement(
    positions: np.ndarray, fiedler_part: np.ndarray, seed: int = 0
) -> tuple[float, np.ndarray]:
    """Pairwise agreement between Fiedler bipartition and 2-cluster spatial KMeans.

    Returns (agreement_fraction, kmeans_labels). Chance = 0.5.

    Pair agreement: for every pair (i<j), the two methods agree iff
    (part_F[i]==part_F[j]) == (part_K[i]==part_K[j]). Agreement = mean over
    all C(N,2) pairs of the indicator (matches A2's reported metric).
    """
    centroids, labels = kmeans2(
        positions, k=2, seed=seed, minit="++", missing="warn"
    )
    N = positions.shape[0]
    same_F = fiedler_part[:, None] == fiedler_part[None, :]
    same_K = labels[:, None] == labels[None, :]
    iu = np.triu_indices(N, k=1)
    agree = (same_F[iu] == same_K[iu]).mean()
    return float(agree), labels


def mi_matrix_descriptors(
    M: np.ndarray, positions: np.ndarray, seed_kmeans: int = 0
) -> dict[str, Any]:
    """Compute the A2 reference table of structural descriptors.

    M: (N, N) MI matrix (zero diag). positions: (N, 3) at the chosen step.
    """
    N = M.shape[0]
    iu = np.triu_indices(N, k=1)
    off_diag = M[iu]

    # Pairwise distances among agents at this step.
    dist = squareform(pdist(positions))
    dist_off = dist[iu]

    # Spearman rank correlation between MI and -distance (per A2: positive
    # value indicates closer pairs share more MI).
    spearman_r, spearman_p = stats.spearmanr(off_diag, -dist_off)

    # Fiedler bipartition + Laplacian λ_2.
    L = normalized_laplacian(M)
    eigvals, _ = np.linalg.eigh(0.5 * (L + L.T))
    eigvals_sorted = np.sort(eigvals)
    fiedler_eigval = float(eigvals_sorted[1])
    part = fiedler_bipartition(L)

    # Fiedler vs KMeans-2 spatial agreement.
    pair_agree, km_labels = fiedler_kmeans_pair_agreement(
        positions, part, seed=seed_kmeans
    )

    # MI-matrix top eigenvalue / 2nd eigenvalue ratio + gap.
    M_eigvals, _ = np.linalg.eigh(0.5 * (M + M.T))
    M_eig_sorted = np.sort(M_eigvals)[::-1]  # descending
    top1, top2 = float(M_eig_sorted[0]), float(M_eig_sorted[1])
    gap = top1 - top2
    ratio = top1 / top2 if top2 != 0 else float("inf")

    # Φ_spectral and phi_norm at this MI matrix.
    phi = float(phi_spectral_fn(M, part))
    cross_edges = int(((part[:, None] != part[None, :]) & np.triu(np.ones_like(M, dtype=bool), 1)).sum())
    phi_n = phi / cross_edges if cross_edges > 0 else 0.0

    return {
        "phi_spectral": phi,
        "phi_norm": phi_n,
        "cross_edges": cross_edges,
        "MI_mean": float(off_diag.mean()),
        "MI_std": float(off_diag.std(ddof=0)),
        "MI_q25": float(np.percentile(off_diag, 25)),
        "MI_q50": float(np.percentile(off_diag, 50)),
        "MI_q75": float(np.percentile(off_diag, 75)),
        "MI_min": float(off_diag.min()),
        "MI_max": float(off_diag.max()),
        "spearman_r_MI_neg_d": float(spearman_r),
        "spearman_p_MI_neg_d": float(spearman_p),
        "fiedler_eigval": fiedler_eigval,
        "fiedler_kmeans_pair_agreement": pair_agree,
        "MI_top1": top1,
        "MI_top2": top2,
        "MI_gap_top1_top2": gap,
        "MI_ratio_top1_top2": ratio,
        "fiedler_partition": part.tolist(),
        "kmeans_labels": [int(x) for x in km_labels],
    }


# =============================================================================
# Main pipeline
# =============================================================================


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    # ---- 1. Load existing parquets -----------------------------------------
    print("[1/5] Loading existing per-window parquets ...")
    per_seed_parquets: dict[float, dict[int, pd.DataFrame]] = {}
    for lam in CONDITIONS:
        per_seed_parquets[lam] = {}
        for s in SEEDS:
            path = PARQUET_ROOT / f"lambda_{lam}" / f"seed{s}.parquet"
            df = pd.read_parquet(path)
            per_seed_parquets[lam][s] = df

    # Sanity check expected window count.
    sample_df = per_seed_parquets[0.0][0]
    n_windows = len(sample_df)
    ss = steady_state_indices(n_windows)
    print(f"  n_windows per run = {n_windows}; steady-state slice = {ss.start}..{n_windows-1}")

    # ---- 2. Re-run simulator and compute σ_u + compactness -----------------
    print("[2/5] Re-running simulator (40 runs, ~5–10s each) ...")
    sim_data: dict[float, dict[int, dict[str, np.ndarray]]] = {}
    for lam in CONDITIONS:
        sim_data[lam] = {}
        for s in SEEDS:
            t0 = time.time()
            pos, vel, is_leader = run_and_capture(lam, s)
            sigma_u_w = windowed_sigma_u_per_window(vel)
            compact_w = windowed_compactness_per_window(pos, is_leader)
            sim_data[lam][s] = {
                "positions": pos,
                "velocities": vel,
                "is_leader": is_leader,
                "sigma_u_per_window": sigma_u_w,
                "compactness_per_window": compact_w,
            }
            print(
                f"  λ={lam}, seed={s}: σ_u_ss={sigma_u_w[ss].mean():.4f}, "
                f"compact_ss={compact_w[ss].mean():.3f}, t={time.time()-t0:.1f}s"
            )

    # ---- 3. Per-condition aggregates ---------------------------------------
    print("[3/5] Computing per-condition aggregates ...")
    aggregates: dict[str, Any] = {
        "schema_version": 1,
        "method": {
            "T": T_STEPS,
            "W": W,
            "stride": STRIDE,
            "n_seeds": len(SEEDS),
            "n_windows_per_run": n_windows,
            "steady_state_window_start": ss.start,
            "n_steady_state_windows": n_windows - ss.start,
            "bootstrap_B": B_BOOT,
            "bootstrap_seed": RNG_SEED,
            "sigma_u_aggregation": "L2 norm of per-channel stds, averaged across agents",
        },
        "per_condition": {},
        "per_seed_table": [],
        "pairwise_comparisons": {},
        "bimodality": {},
        "phi_norm_cross_seed_sigma": {},
        "outlier_sensitivity": {},
        "mechanism_diagnostic": {},
    }

    # Per-seed steady-state means.
    per_seed_phi: dict[float, np.ndarray] = {}
    per_seed_phi_norm: dict[float, np.ndarray] = {}
    per_seed_sigma_u: dict[float, np.ndarray] = {}
    per_seed_compact: dict[float, np.ndarray] = {}
    per_seed_pol: dict[float, np.ndarray] = {}

    # Pooled per-window Φ for bimodality diagnostics (per condition).
    pooled_phi: dict[float, np.ndarray] = {}

    for lam in CONDITIONS:
        phi_means = np.zeros(len(SEEDS))
        phi_norm_means = np.zeros(len(SEEDS))
        sigma_u_means = np.zeros(len(SEEDS))
        compact_means = np.zeros(len(SEEDS))
        pol_means = np.zeros(len(SEEDS))
        pooled = []
        for j, s in enumerate(SEEDS):
            df = per_seed_parquets[lam][s]
            ss_df = df.iloc[ss]
            phi_means[j] = float(ss_df["phi_spectral"].mean())
            phi_norm_means[j] = float(ss_df["phi_norm"].mean())
            pol_means[j] = float(ss_df["polarization"].mean())
            sigma_u = sim_data[lam][s]["sigma_u_per_window"]
            compact = sim_data[lam][s]["compactness_per_window"]
            sigma_u_means[j] = float(sigma_u[ss].mean())
            compact_means[j] = float(compact[ss].mean())
            pooled.append(df["phi_spectral"].to_numpy())  # full run, not just steady-state
        per_seed_phi[lam] = phi_means
        per_seed_phi_norm[lam] = phi_norm_means
        per_seed_sigma_u[lam] = sigma_u_means
        per_seed_compact[lam] = compact_means
        per_seed_pol[lam] = pol_means
        pooled_phi[lam] = np.concatenate(pooled)

        # Cross-seed bootstrap CIs.
        phi_lo, phi_hi = bootstrap_ci(phi_means)
        phi_norm_lo, phi_norm_hi = bootstrap_ci(phi_norm_means)
        sigma_lo, sigma_hi = bootstrap_ci(sigma_u_means)
        compact_lo, compact_hi = bootstrap_ci(compact_means)

        aggregates["per_condition"][f"lambda_{lam}"] = {
            "n_seeds": len(SEEDS),
            "phi_spectral": {
                "per_seed": phi_means.tolist(),
                "mean": float(phi_means.mean()),
                "std_seed": float(phi_means.std(ddof=1)),
                "ci95_lo": phi_lo,
                "ci95_hi": phi_hi,
                "min": float(phi_means.min()),
                "max": float(phi_means.max()),
            },
            "phi_norm": {
                "per_seed": phi_norm_means.tolist(),
                "mean": float(phi_norm_means.mean()),
                "std_seed": float(phi_norm_means.std(ddof=1)),
                "ci95_lo": phi_norm_lo,
                "ci95_hi": phi_norm_hi,
            },
            "sigma_u": {
                "per_seed": sigma_u_means.tolist(),
                "mean": float(sigma_u_means.mean()),
                "ci95_lo": sigma_lo,
                "ci95_hi": sigma_hi,
            },
            "leader_compactness": {
                "per_seed": compact_means.tolist(),
                "mean": float(compact_means.mean()),
                "ci95_lo": compact_lo,
                "ci95_hi": compact_hi,
            },
            "polarization_mean": float(pol_means.mean()),
        }

        # phi_norm cross-seed σ — std across the 10 per-seed steady-state means.
        aggregates["phi_norm_cross_seed_sigma"][f"lambda_{lam}"] = float(
            phi_norm_means.std(ddof=1)
        )

        # Bimodality on pooled per-window Φ across all 10 seeds.
        aggregates["bimodality"][f"lambda_{lam}"] = bimodality_diagnostics(pooled_phi[lam])

    # ---- Per-seed table for verdict markdown -------------------------------
    for lam in CONDITIONS:
        for j, s in enumerate(SEEDS):
            row = {
                "lambda": lam,
                "seed": int(s),
                "phi_steady_state_mean": float(per_seed_phi[lam][j]),
                "phi_norm_steady_state_mean": float(per_seed_phi_norm[lam][j]),
                "sigma_u_steady_state": float(per_seed_sigma_u[lam][j]),
                "leader_compactness_steady_state": float(per_seed_compact[lam][j]),
                "polarization_steady_state": float(per_seed_pol[lam][j]),
            }
            # Outlier flag — Tukey 1.5*IQR on within-condition Φ.
            phis = per_seed_phi[lam]
            q25, q75 = np.percentile(phis, [25, 75])
            iqr = q75 - q25
            row["is_outlier_tukey15"] = bool(
                (per_seed_phi[lam][j] > q75 + 1.5 * iqr)
                or (per_seed_phi[lam][j] < q25 - 1.5 * iqr)
            )
            aggregates["per_seed_table"].append(row)

    # ---- 4. Pairwise comparisons (vs λ=2.4) --------------------------------
    print("[4/5] Pairwise comparisons vs λ=2.4 ...")
    ref = per_seed_phi[2.4]
    for lam_other in [0.0, 0.8, 1.6]:
        other = per_seed_phi[lam_other]
        diff_lo, diff_hi = bootstrap_diff_ci(other, ref)
        aggregates["pairwise_comparisons"][f"phi_lambda_{lam_other}_vs_lambda_2.4"] = {
            "n": len(SEEDS),
            "mean_other": float(other.mean()),
            "mean_2.4": float(ref.mean()),
            "diff_other_minus_2.4": float(other.mean() - ref.mean()),
            "diff_ci95_lo": diff_lo,
            "diff_ci95_hi": diff_hi,
            "cohens_d": cohens_d(other, ref),
            "ci_overlap": (
                aggregates["per_condition"][f"lambda_{lam_other}"]["phi_spectral"]["ci95_lo"]
                <= aggregates["per_condition"]["lambda_2.4"]["phi_spectral"]["ci95_hi"]
            )
            and (
                aggregates["per_condition"]["lambda_2.4"]["phi_spectral"]["ci95_lo"]
                <= aggregates["per_condition"][f"lambda_{lam_other}"]["phi_spectral"]["ci95_hi"]
            ),
        }

    # ---- Outlier sensitivity at λ=2.4 (drop seed 8) ------------------------
    phi24 = per_seed_phi[2.4]
    seed8_idx = SEEDS.index(8)
    phi24_no8 = np.delete(phi24, seed8_idx)
    no8_lo, no8_hi = bootstrap_ci(phi24_no8)
    aggregates["outlier_sensitivity"]["lambda_2.4_drop_seed_8"] = {
        "n_seeds": len(phi24_no8),
        "phi_mean_with_seed_8": float(phi24.mean()),
        "phi_mean_without_seed_8": float(phi24_no8.mean()),
        "phi_ci95_lo_without_seed_8": no8_lo,
        "phi_ci95_hi_without_seed_8": no8_hi,
        "seed_8_phi": float(phi24[seed8_idx]),
    }
    # Also re-run pairwise comparisons without seed 8 to see if any flip.
    for lam_other in [0.0, 0.8, 1.6]:
        other = per_seed_phi[lam_other]
        diff_lo, diff_hi = bootstrap_diff_ci(other, phi24_no8)
        aggregates["outlier_sensitivity"][
            f"phi_lambda_{lam_other}_vs_lambda_2.4_no8"
        ] = {
            "diff_other_minus_2.4_no8": float(other.mean() - phi24_no8.mean()),
            "diff_ci95_lo": diff_lo,
            "diff_ci95_hi": diff_hi,
            "cohens_d": cohens_d(other, phi24_no8),
        }

    # ---- 5. Mechanism diagnostic at λ=0.0 and λ=2.4 ------------------------
    print("[5/5] Mechanism diagnostic — MI matrices at representative windows ...")
    mech: dict[str, Any] = {}
    rep_payload: dict[str, dict[str, Any]] = {}

    for lam in [0.0, 2.4]:
        # Pick representative seed = closest to cross-seed median per-seed Φ.
        phi_seeds = per_seed_phi[lam]
        med = float(np.median(phi_seeds))
        rep_seed_idx = int(np.argmin(np.abs(phi_seeds - med)))
        rep_seed = SEEDS[rep_seed_idx]

        # Per-seed steady-state mean Φ.
        seed_ss_phi_mean = phi_seeds[rep_seed_idx]

        # Pick representative window = steady-state window with phi closest to mean.
        df = per_seed_parquets[lam][rep_seed]
        ss_df = df.iloc[ss]
        rep_window_pos = int(np.argmin(np.abs(ss_df["phi_spectral"].to_numpy() - seed_ss_phi_mean)))
        rep_window_idx = int(ss_df.iloc[rep_window_pos]["window_idx"])
        rep_t_start = int(ss_df.iloc[rep_window_pos]["t_start"])
        rep_t_end = int(ss_df.iloc[rep_window_pos]["t_end"])
        rep_phi_orig = float(ss_df.iloc[rep_window_pos]["phi_spectral"])
        rep_phi_norm_orig = float(ss_df.iloc[rep_window_pos]["phi_norm"])

        # Reconstruct features through the canonical telemetry CSV → extract_features
        # path so the resulting MI matrix matches the parquet's pipeline bit-for-bit.
        # (Direct in-process construction drifts after standardization because of
        # ε-level float jitter in the speed channel.)
        positions = sim_data[lam][rep_seed]["positions"]
        features_full = features_via_telemetry(lam, rep_seed)  # (T, N, 4)
        win_slice = slice(rep_t_start, rep_t_start + W)
        window_features = features_full[win_slice]

        Xs = standardize_window(window_features)
        M = mi_matrix_ksg(Xs, k=5, noise_eps=1e-10)
        # Position at end of window (mirrors snapshot-TDA convention).
        pos_at_end = positions[rep_t_start + W - 1]

        descriptors = mi_matrix_descriptors(M, pos_at_end, seed_kmeans=0)
        descriptors_extra = {
            "lambda": lam,
            "rep_seed": rep_seed,
            "rep_window_idx": rep_window_idx,
            "rep_t_start": rep_t_start,
            "rep_t_end": rep_t_end,
            "rep_window_phi_from_parquet": rep_phi_orig,
            "rep_window_phi_norm_from_parquet": rep_phi_norm_orig,
            "rep_window_phi_recomputed": descriptors["phi_spectral"],
            "rep_window_phi_norm_recomputed": descriptors["phi_norm"],
            "per_seed_steady_state_mean_phi": float(seed_ss_phi_mean),
        }
        mech[f"lambda_{lam}"] = {**descriptors_extra, **descriptors}

        rep_payload[f"lambda_{lam}"] = {
            "MI_matrix": M,
            "positions_window_end": pos_at_end,
            "fiedler_partition": np.asarray(descriptors["fiedler_partition"], dtype=int),
            "kmeans_labels": np.asarray(descriptors["kmeans_labels"], dtype=int),
            "is_leader": sim_data[lam][rep_seed]["is_leader"],
            "rep_seed": rep_seed,
            "rep_window_idx": rep_window_idx,
            "rep_t_start": rep_t_start,
            "rep_t_end": rep_t_end,
        }

    aggregates["mechanism_diagnostic"] = mech
    # A2 reference (from outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md §2).
    aggregates["mechanism_diagnostic"]["A2_reference"] = {
        "alpha_0.2": {
            "MI_mean": 0.491,
            "MI_std": 0.209,
            "MI_q25": 0.33,
            "MI_q50": 0.48,
            "MI_q75": 0.63,
            "spearman_r_MI_neg_d": 0.10,
            "spearman_p_MI_neg_d": 0.005,
            "fiedler_kmeans_pair_agreement": 0.50,
            "fiedler_eigval": 0.926,
            "MI_top1": 20.4,
            "MI_top2": 1.1,
            "MI_gap_top1_top2": 18.7,
            "phi_norm_cross_seed_sigma_10seed": 0.025,
            "interpretation": "compressibility signature (uniform MI, agreement=chance, large gap)",
        },
        "alpha_1.0": {
            "MI_mean": 0.099,
            "MI_std": 0.100,
            "MI_q25": 0.03,
            "MI_q50": 0.08,
            "MI_q75": 0.14,
            "spearman_r_MI_neg_d": 0.40,
            "spearman_p_MI_neg_d": 0.0,
            "fiedler_kmeans_pair_agreement": 0.78,
            "fiedler_eigval": 0.463,
            "MI_top1": 4.10,
            "MI_top2": 2.32,
            "MI_gap_top1_top2": 1.77,
            "phi_norm_cross_seed_sigma_10seed": 0.086,
            "interpretation": "coherent-baseline signature (low MI, high spatial coupling, small gap)",
        },
    }

    # Save aggregates (JSON-friendly).
    out_json = OUT_DIR / "aggregates.json"
    with open(out_json, "w") as f:
        json.dump(aggregates, f, indent=2, sort_keys=False, default=float)
    print(f"  Wrote {out_json}")

    # Save MI matrices + position payload for figure rendering.
    npz_path = OUT_DIR / "mechanism_diagnostic.npz"
    np.savez(
        npz_path,
        lambda_0_0_MI=rep_payload["lambda_0.0"]["MI_matrix"],
        lambda_0_0_positions=rep_payload["lambda_0.0"]["positions_window_end"],
        lambda_0_0_fiedler=rep_payload["lambda_0.0"]["fiedler_partition"],
        lambda_0_0_kmeans=rep_payload["lambda_0.0"]["kmeans_labels"],
        lambda_0_0_is_leader=rep_payload["lambda_0.0"]["is_leader"],
        lambda_0_0_meta=np.array(
            [
                rep_payload["lambda_0.0"]["rep_seed"],
                rep_payload["lambda_0.0"]["rep_window_idx"],
                rep_payload["lambda_0.0"]["rep_t_start"],
                rep_payload["lambda_0.0"]["rep_t_end"],
            ]
        ),
        lambda_2_4_MI=rep_payload["lambda_2.4"]["MI_matrix"],
        lambda_2_4_positions=rep_payload["lambda_2.4"]["positions_window_end"],
        lambda_2_4_fiedler=rep_payload["lambda_2.4"]["fiedler_partition"],
        lambda_2_4_kmeans=rep_payload["lambda_2.4"]["kmeans_labels"],
        lambda_2_4_is_leader=rep_payload["lambda_2.4"]["is_leader"],
        lambda_2_4_meta=np.array(
            [
                rep_payload["lambda_2.4"]["rep_seed"],
                rep_payload["lambda_2.4"]["rep_window_idx"],
                rep_payload["lambda_2.4"]["rep_t_start"],
                rep_payload["lambda_2.4"]["rep_t_end"],
            ]
        ),
    )
    print(f"  Wrote {npz_path}")

    # Save per-window time series (Φ + σ_u + compactness) for the panel figure.
    panel_path = OUT_DIR / "per_window_timeseries.npz"
    panel_payload: dict[str, np.ndarray] = {}
    for lam in CONDITIONS:
        per_seed_phi_ts = np.stack(
            [per_seed_parquets[lam][s]["phi_spectral"].to_numpy() for s in SEEDS]
        )  # (10, n_windows)
        per_seed_sig_ts = np.stack(
            [sim_data[lam][s]["sigma_u_per_window"] for s in SEEDS]
        )
        per_seed_cmp_ts = np.stack(
            [sim_data[lam][s]["compactness_per_window"] for s in SEEDS]
        )
        key = f"lambda_{str(lam).replace('.', '_')}"
        panel_payload[f"{key}_phi"] = per_seed_phi_ts
        panel_payload[f"{key}_sigma_u"] = per_seed_sig_ts
        panel_payload[f"{key}_compactness"] = per_seed_cmp_ts
    np.savez(panel_path, **panel_payload)
    print(f"  Wrote {panel_path}")

    elapsed = time.time() - t_start
    print(f"\nDone. Total elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
