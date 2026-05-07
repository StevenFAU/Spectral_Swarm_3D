"""Phase 5 Tier 1.C — cross-sweep compressibility audit.

Reproducible analysis script. Run from repo root::

    /home/otacon/Spectral_Swarm_3D/.venv/bin/python3 outputs/tier1_compressibility/_make_audit.py

Outputs
-------
- ``outputs/tier1_compressibility/audit_aggregates.json``
    All numerical support for the cross-sweep audit (per-(sweep, condition)
    Φ / phi_norm σ / bimodality / σ_u where computed; high-w_a check;
    vanilla-baseline equivalence verification).
- ``outputs/tier1_compressibility/cross_sweep_panel.png``
    Scatter (σ_u × phi_norm cross-seed σ), color-coded by sweep, annotated
    quadrants for §4.3 compressibility regime vs. coherent baseline.

Method
------
1. Read each sweep's ``cross_seed_summary.csv`` → Φ mean/std, phi_norm σ.
2. Read each sweep's ``per_seed_summary.csv`` → per-seed steady-state
   means → 1000-resample bootstrap percentile CI on the cross-seed mean.
3. Pool per-window Φ across seeds restricted to ``window_idx >= quantile(2/3)``
   (Tier 1.B steady-state convention) → Hartigan dip p + KDE mode count
   (default-bandwidth gaussian_kde, local maxima above 5% of peak,
   argrelextrema order=5; identical to Tier 1.B ``_make_distributions.py``).
4. σ_u re-runs (deterministic D6 simulator) for the three sweeps where the
   §4.2/§4.3 verdicts rest:
      * alignment_sweep (4 cond × 10 seeds = 40)
      * jamming_sweep (3 cond × 10 seeds = 30)
      * leadership_sweep — reuse Tier 1.A ``aggregates.json`` (no re-run).
   For the other 8 sweeps the σ_u column is left empty with a "not
   computed for this audit" footnote — these are not load-bearing for
   the §4.2 (alignment) or §4.3 (jamming) verdicts.
5. Vanilla-boids equivalence check via per-seed parquet hashing
   (extends the Tier 1.B audit's three-condition verification).
6. High-w_a non-monotonicity check (alignment w_a=1.2 vs 1.8) — Cohen's
   d on per-seed means + bootstrap CI on the difference + CI overlap.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import diptest
import matplotlib
import numpy as np
import pandas as pd
import yaml
from scipy.signal import argrelextrema
from scipy.stats import gaussian_kde

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.model import BoidSwarmModel3D  # noqa: E402

OUT_DIR = REPO_ROOT / "outputs" / "tier1_compressibility"
OUTPUTS_DIR = REPO_ROOT / "outputs"
CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"
TIER1A_AGG_PATH = OUT_DIR / "aggregates.json"

# ── steady-state and bimodality conventions (match Tier 1.B) ──────────────────
SS_QUANTILE = 2 / 3
DIP_P_THRESHOLD = 0.20
KDE_HEIGHT_FRAC = 0.05
KDE_ORDER = 5

# ── bootstrap conventions (match Tier 1.A) ────────────────────────────────────
B_BOOT = 1000
RNG_SEED = 0

# ── simulator constants (mirror _make_aggregates.py) ──────────────────────────
T_STEPS = 500
W_DEFAULT = 40
STRIDE_DEFAULT = 5
SWEEP_DEFAULTS = {"stride": STRIDE_DEFAULT}


# ══════════════════════════════════════════════════════════════════════════════
# Sweep × condition catalog
# ══════════════════════════════════════════════════════════════════════════════

# Each entry: (sweep_name, default_scenario, [(cond_name, scenario, overrides)],
# n_seeds, sweep_kind). sweep_kind ∈ {"primary", "sensitivity"}.
SWEEPS: list[dict[str, Any]] = [
    {
        "sweep": "alignment_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("wa_0.0", "none", {"w_a": 0.0}),
            ("wa_0.6", "none", {"w_a": 0.6}),
            ("wa_1.2", "none", {"w_a": 1.2}),
            ("wa_1.8", "none", {"w_a": 1.8}),
        ],
    },
    {
        "sweep": "jamming_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("alpha_0.2", "jamming", {"jam_alpha": 0.2}),
            ("alpha_0.5", "jamming", {"jam_alpha": 0.5}),
            ("alpha_1.0", "jamming", {"jam_alpha": 1.0}),
        ],
    },
    {
        "sweep": "leadership_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("lambda_0.0", "leader", {"leader_strength": 0.0}),
            ("lambda_0.8", "leader", {"leader_strength": 0.8}),
            ("lambda_1.6", "leader", {"leader_strength": 1.6}),
            ("lambda_2.4", "leader", {"leader_strength": 2.4}),
        ],
    },
    {
        "sweep": "milling_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("mu_0.0", "milling", {"milling_mu": 0.0}),
            ("mu_0.4", "milling", {"milling_mu": 0.4}),
            ("mu_0.8", "milling", {"milling_mu": 0.8}),
            ("mu_1.2", "milling", {"milling_mu": 1.2}),
        ],
    },
    {
        "sweep": "split_merge_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("none", "none", {}),
            ("split_merge", "split_merge", {}),
        ],
    },
    {
        "sweep": "noise_sweep",
        "kind": "primary",
        "n_seeds": 10,
        "conditions": [
            ("sigma_0.0", "none", {"noise_sigma": 0.0}),
            ("sigma_0.05", "none", {"noise_sigma": 0.05}),
            ("sigma_0.1", "none", {"noise_sigma": 0.1}),
            ("sigma_0.2", "none", {"noise_sigma": 0.2}),
            ("sigma_0.5", "none", {"noise_sigma": 0.5}),
        ],
    },
    {
        "sweep": "n_sensitivity_N80",
        "kind": "sensitivity",
        "n_seeds": 5,
        "conditions": [
            ("wa_0.0", "none", {"N": 80, "w_a": 0.0}),
            ("wa_0.6", "none", {"N": 80, "w_a": 0.6}),
            ("wa_1.2", "none", {"N": 80, "w_a": 1.2}),
            ("wa_1.8", "none", {"N": 80, "w_a": 1.8}),
        ],
    },
    {
        "sweep": "n_sensitivity_N160",
        "kind": "sensitivity",
        "n_seeds": 5,
        "conditions": [
            ("wa_0.0", "none", {"N": 160, "w_a": 0.0}),
            ("wa_0.6", "none", {"N": 160, "w_a": 0.6}),
            ("wa_1.2", "none", {"N": 160, "w_a": 1.2}),
            ("wa_1.8", "none", {"N": 160, "w_a": 1.8}),
        ],
    },
    {
        "sweep": "w_sensitivity",
        "kind": "sensitivity",
        "n_seeds": 5,
        "conditions": [
            ("W30", "none", {"W": 30}),
            ("W40", "none", {"W": 40}),
            ("W50", "none", {"W": 50}),
            ("W60", "none", {"W": 60}),
        ],
    },
    {
        "sweep": "alignment_rule_sensitivity",
        "kind": "sensitivity",
        "n_seeds": 5,
        "conditions": [
            ("mean", "none", {"alignment_rule": "mean", "w_a": 1.0}),
            ("sum", "none", {"alignment_rule": "sum", "w_a": 1.0}),
        ],
    },
    {
        "sweep": "sensitivity",
        "kind": "sensitivity",
        "n_seeds": 5,
        "conditions": [
            (f"{est}_{feat}", "none", {"estimator": est, "feature_set": feat,
                                       "W": 50 if feat == "full" else 40})
            for est in ["ksg", "histogram", "gaussian"]
            for feat in ["kinematic", "vxvyvz", "full"]
        ],
    },
]

# σ_u re-runs only for these sweeps (the three on which §4.2/§4.3 rest).
# Noise sweep included after the n=10 cross-sweep aggregation surfaced
# noise σ=0.2 as a non-pre-registered §4.2 transitional-peak candidate
# (steady-state dip p ≈ 0.000, modes = 2, mean Φ above both noise endpoints).
# σ_u verification at the candidate strengthens the verdict's mechanism claim.
SIGMA_U_SWEEPS = {"alignment_sweep", "jamming_sweep", "noise_sweep"}
# leadership reused from Tier 1.A; noise σ=0.05 byte-identical to vanilla baseline,
# σ_u value is identical to leadership λ=0.0; recomputed for completeness.


# ══════════════════════════════════════════════════════════════════════════════
# Aggregation utilities
# ══════════════════════════════════════════════════════════════════════════════

def bootstrap_ci(values: np.ndarray, b: int = B_BOOT, seed: int = RNG_SEED) -> tuple[float, float]:
    """Percentile bootstrap CI on the mean (resampling input with replacement)."""
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(b, values.size))
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, seed: int = RNG_SEED) -> tuple[float, float]:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx_a = rng.integers(0, a.size, size=(B_BOOT, a.size))
    idx_b = rng.integers(0, b.size, size=(B_BOOT, b.size))
    diffs = a[idx_a].mean(axis=1) - b[idx_b].mean(axis=1)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    s_a = a.std(ddof=1)
    s_b = b.std(ddof=1)
    pooled = np.sqrt((s_a ** 2 + s_b ** 2) / 2.0)
    if pooled == 0:
        return float("inf") if a.mean() != b.mean() else 0.0
    return float((a.mean() - b.mean()) / pooled)


def steady_state_phi_pooled(parquet_paths: list[Path]) -> tuple[np.ndarray, list[float]]:
    """Pool per-window Φ across seeds restricted to window_idx >= quantile(2/3)."""
    pooled: list[float] = []
    seed_means: list[float] = []
    for p in parquet_paths:
        df = pd.read_parquet(p)
        thresh = df["window_idx"].quantile(SS_QUANTILE)
        ss = df[df["window_idx"] >= thresh]["phi_spectral"].to_numpy()
        pooled.extend(ss.tolist())
        seed_means.append(float(ss.mean()))
    return np.array(pooled, dtype=np.float64), seed_means


def count_kde_modes(values: np.ndarray) -> int:
    """Local maxima of default-bandwidth gaussian_kde above 5% of peak."""
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 3 or np.ptp(values) == 0:
        return 1
    kde = gaussian_kde(values)
    x = np.linspace(values.min(), values.max(), 2000)
    y = kde(x)
    height = KDE_HEIGHT_FRAC * y.max()
    maxima_idx = argrelextrema(y, np.greater, order=KDE_ORDER)[0]
    modes = int((y[maxima_idx] >= height).sum())
    return max(modes, 1)


def bimodality(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size < 4:
        return {"dip_p": float("nan"), "kde_modes": 1, "std_iqr": float("nan"),
                "bimodal": False, "n": int(values.size)}
    _, dip_p = diptest.diptest(values)
    modes = count_kde_modes(values)
    q25, q75 = np.percentile(values, [25, 75])
    iqr = q75 - q25
    std_iqr = float(values.std(ddof=1) / iqr) if iqr > 0 else float("nan")
    return {
        "dip_p": float(dip_p),
        "kde_modes": int(modes),
        "std_iqr": std_iqr,
        "bimodal": bool(modes >= 2 and dip_p < DIP_P_THRESHOLD),
        "n": int(values.size),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Vanilla-boids equivalence check (extension of Tier 1.B audit's verification)
# ══════════════════════════════════════════════════════════════════════════════

def hash_parquet(path: Path) -> str:
    df = pd.read_parquet(path)
    return hashlib.md5(df.to_csv(index=False).encode()).hexdigest()


def verify_vanilla_equivalence() -> dict[str, Any]:
    """Hash seed 0 parquets across candidate vanilla-baseline conditions.

    Tier 1.B audit verified three (jamming α=1.0, leader λ=0.0, milling μ=0.0)
    at commit `7a5b58e`. This audit extends to all candidate vanilla-default
    conditions: noise σ=0.05 (default noise_sigma), split_merge "none", and
    the n=5 sensitivity-default conditions (W40, alignment_rule mean,
    sensitivity ksg_kinematic).
    """
    candidates_n10 = [
        ("jamming_sweep", "alpha_1.0"),
        ("leadership_sweep", "lambda_0.0"),
        ("milling_sweep", "mu_0.0"),
        ("noise_sweep", "sigma_0.05"),
        ("split_merge_sweep", "none"),
    ]
    candidates_n5 = [
        ("w_sensitivity", "W40"),
        ("alignment_rule_sensitivity", "mean"),
        ("sensitivity", "ksg_kinematic"),
    ]
    hashes_10 = {f"{s}/{c}": hash_parquet(OUTPUTS_DIR / s / c / "seed0.parquet")
                 for s, c in candidates_n10}
    hashes_5 = {f"{s}/{c}": hash_parquet(OUTPUTS_DIR / s / c / "seed0.parquet")
                for s, c in candidates_n5}
    n10_match = len(set(hashes_10.values())) == 1
    n5_match = len(set(hashes_5.values())) == 1
    return {
        "n10_candidates": list(hashes_10.keys()),
        "n10_seed0_hashes": hashes_10,
        "n10_byte_identical": n10_match,
        "n5_candidates": list(hashes_5.keys()),
        "n5_seed0_hashes": hashes_5,
        "n5_byte_identical": n5_match,
        "n10_n5_share_seed0": (
            n10_match and n5_match
            and next(iter(hashes_10.values())) == next(iter(hashes_5.values()))
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# σ_u re-runs (deterministic D6 simulator)
# ══════════════════════════════════════════════════════════════════════════════

def _build_config_for_condition(
    base: dict[str, Any], scenario: str, overrides: dict[str, Any]
) -> dict[str, Any]:
    cfg = {**base, **SWEEP_DEFAULTS, **overrides}
    cfg["scenario"] = scenario
    return cfg


def run_capture_velocities(
    scenario: str, overrides: dict[str, Any], seed: int, base_cfg: dict[str, Any]
) -> tuple[np.ndarray, int]:
    """Re-run the simulator and return ``velocities`` of shape ``(T, N, 3)``.

    Deterministic per (config, seed) — bit-identical to ``run_sweep.py``'s
    re-run path. Returns velocities and resolved N (which can vary in
    n_sensitivity sweeps).
    """
    cfg = _build_config_for_condition(base_cfg, scenario, overrides)
    model = BoidSwarmModel3D(cfg, scenario_name=scenario, seed=seed)
    N = len(model.swarm)
    velocities = np.empty((T_STEPS, N, 3), dtype=np.float64)
    for t in range(T_STEPS):
        model.step()
        velocities[t] = model._velocities()
    return velocities, N


def windowed_sigma_u(velocities: np.ndarray, W: int, stride: int) -> np.ndarray:
    """Per-window σ_u: per-agent L2 norm of per-channel stds, averaged across agents.

    Mirrors Tier 1.A ``windowed_sigma_u_per_window`` — speed is held invariant
    by the model, so dividing by speed=1.0 yields unit velocities directly.
    """
    T = velocities.shape[0]
    n_windows = (T - W) // stride + 1
    out = np.empty(n_windows, dtype=np.float64)
    for k in range(n_windows):
        t0 = k * stride
        win = velocities[t0:t0 + W]  # (W, N, 3)
        per_chan_std = win.std(axis=0, ddof=0)  # (N, 3)
        per_agent_l2 = np.linalg.norm(per_chan_std, axis=1)  # (N,)
        out[k] = float(per_agent_l2.mean())
    return out


def steady_slice(n_windows: int) -> slice:
    start = n_windows - max(n_windows // 3, 1)
    return slice(start, n_windows)


# ══════════════════════════════════════════════════════════════════════════════
# Cross-sweep aggregation
# ══════════════════════════════════════════════════════════════════════════════

def load_per_seed_phi(sweep: str, condition: str) -> np.ndarray:
    """Per-seed steady-state Φ means from ``per_seed_summary.csv`` (D2 protocol)."""
    df = pd.read_csv(OUTPUTS_DIR / sweep / "per_seed_summary.csv")
    sub = df[df["condition"] == condition]
    return sub["phi_spectral_mean"].to_numpy(dtype=np.float64)


def load_per_seed_phi_norm(sweep: str, condition: str) -> np.ndarray:
    df = pd.read_csv(OUTPUTS_DIR / sweep / "per_seed_summary.csv")
    sub = df[df["condition"] == condition]
    return sub["phi_norm_mean"].to_numpy(dtype=np.float64)


def aggregate_sweep_condition(
    sweep: str, condition: str, scenario: str, overrides: dict[str, Any],
    base_cfg: dict[str, Any], compute_sigma_u: bool, seeds: list[int],
    leadership_sigma_u_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute the full row for one (sweep, condition)."""
    # ---- Φ aggregates ------------------------------------------------------
    per_seed_phi = load_per_seed_phi(sweep, condition)
    per_seed_phi_norm = load_per_seed_phi_norm(sweep, condition)
    phi_mean = float(per_seed_phi.mean())
    phi_lo, phi_hi = bootstrap_ci(per_seed_phi)
    phi_norm_mean = float(per_seed_phi_norm.mean())
    phi_norm_cs_sigma = float(per_seed_phi_norm.std(ddof=1))

    # ---- Bimodality on pooled steady-state per-window Φ ---------------------
    parquets = sorted((OUTPUTS_DIR / sweep / condition).glob("seed*.parquet"))
    pooled_ss, seed_ss_means = steady_state_phi_pooled(parquets)
    bim = bimodality(pooled_ss)

    # ---- σ_u (re-run for critical sweeps; reuse for leadership) -------------
    sigma_u_block: dict[str, Any] = {"computed": False, "reason": "out of audit scope"}
    if sweep == "leadership_sweep" and condition in leadership_sigma_u_cache:
        cached = leadership_sigma_u_cache[condition]
        per_seed_sigma_u = np.asarray(cached["per_seed"], dtype=np.float64)
        sigma_u_block = {
            "computed": True,
            "source": "Tier 1.A aggregates.json",
            "per_seed": per_seed_sigma_u.tolist(),
            "mean": float(per_seed_sigma_u.mean()),
            "ci95_lo": float(cached["ci95_lo"]),
            "ci95_hi": float(cached["ci95_hi"]),
        }
    elif compute_sigma_u and sweep in SIGMA_U_SWEEPS:
        per_seed_sigma_u = np.empty(len(seeds), dtype=np.float64)
        # W and stride from base config (sweep may override W, but for the
        # σ_u-relevant sweeps alignment / jamming use defaults).
        W_eff = int({**base_cfg, **overrides}.get("W", W_DEFAULT))
        for j, s in enumerate(seeds):
            t0 = time.time()
            velocities, _ = run_capture_velocities(scenario, overrides, s, base_cfg)
            sigma_u_w = windowed_sigma_u(velocities, W_eff, STRIDE_DEFAULT)
            ss = steady_slice(sigma_u_w.size)
            per_seed_sigma_u[j] = float(sigma_u_w[ss].mean())
            print(f"  σ_u {sweep}/{condition} seed={s}: {per_seed_sigma_u[j]:.4f} "
                  f"({time.time()-t0:.1f}s)")
        s_lo, s_hi = bootstrap_ci(per_seed_sigma_u)
        sigma_u_block = {
            "computed": True,
            "source": "this audit (re-run)",
            "per_seed": per_seed_sigma_u.tolist(),
            "mean": float(per_seed_sigma_u.mean()),
            "ci95_lo": s_lo,
            "ci95_hi": s_hi,
        }

    return {
        "sweep": sweep,
        "condition": condition,
        "n_seeds": len(seeds),
        "phi_spectral": {
            "per_seed": per_seed_phi.tolist(),
            "mean": phi_mean,
            "ci95_lo": phi_lo,
            "ci95_hi": phi_hi,
            "std_seed": float(per_seed_phi.std(ddof=1)),
        },
        "phi_norm": {
            "mean": phi_norm_mean,
            "cross_seed_sigma": phi_norm_cs_sigma,
            "per_seed": per_seed_phi_norm.tolist(),
        },
        "bimodality_steady_state_pooled": bim,
        "sigma_u": sigma_u_block,
    }


# ══════════════════════════════════════════════════════════════════════════════
# High-w_a non-monotonicity check
# ══════════════════════════════════════════════════════════════════════════════

def high_wa_check() -> dict[str, Any]:
    phi_12 = load_per_seed_phi("alignment_sweep", "wa_1.2")
    phi_18 = load_per_seed_phi("alignment_sweep", "wa_1.8")
    diff = float(phi_18.mean() - phi_12.mean())  # positive = w_a=1.8 above w_a=1.2
    diff_lo, diff_hi = bootstrap_diff_ci(phi_18, phi_12)
    d = cohens_d(phi_18, phi_12)
    lo_12, hi_12 = bootstrap_ci(phi_12)
    lo_18, hi_18 = bootstrap_ci(phi_18)
    ci_overlap = (lo_12 <= hi_18) and (lo_18 <= hi_12)
    # Verdict thresholds from prompt:
    # real if Cohen's d >= 0.3 AND CIs disjoint or close (treat "close" as touching).
    if abs(d) >= 0.3 and not ci_overlap:
        verdict = "real"
    elif abs(d) < 0.3 and ci_overlap:
        verdict = "null"
    else:
        verdict = "ambiguous"
    return {
        "phi_wa_1.2": {"mean": float(phi_12.mean()),
                       "ci95": (lo_12, hi_12),
                       "per_seed": phi_12.tolist()},
        "phi_wa_1.8": {"mean": float(phi_18.mean()),
                       "ci95": (lo_18, hi_18),
                       "per_seed": phi_18.tolist()},
        "diff_18_minus_12": diff,
        "diff_ci95": (diff_lo, diff_hi),
        "cohens_d_18_vs_12": d,
        "ci_overlap": ci_overlap,
        "verdict": verdict,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Figure: σ_u × phi_norm cross-seed σ scatter
# ══════════════════════════════════════════════════════════════════════════════

def render_cross_sweep_panel(rows: list[dict[str, Any]], out_path: Path) -> None:
    """Scatter of (σ_u, phi_norm cross-seed σ); only conditions with σ_u computed."""
    plotted: list[tuple[str, str, float, float, str]] = []
    for r in rows:
        if not r["sigma_u"].get("computed", False):
            continue
        plotted.append((r["sweep"], r["condition"],
                        float(r["sigma_u"]["mean"]),
                        float(r["phi_norm"]["cross_seed_sigma"]),
                        r["condition"]))
    if not plotted:
        print("  cross_sweep_panel.png — no σ_u points; skipping figure")
        return

    sweep_colors = {
        "alignment_sweep": "#1f77b4",   # blue
        "jamming_sweep": "#d62728",     # red
        "leadership_sweep": "#2ca02c",  # green
    }
    sweep_markers = {
        "alignment_sweep": "o",
        "jamming_sweep": "s",
        "leadership_sweep": "^",
    }

    fig, ax = plt.subplots(figsize=(8, 6.5))

    # Reference quadrant lines: A2 α=0.2 reference σ_u ≈ 0.21 (mid of 0.17–0.26),
    # phi_norm cross-seed σ = 0.025; A2 α=1.0 phi_norm cross-seed σ = 0.086.
    ref_phi_norm_compress = 0.025
    ref_phi_norm_coherent = 0.086
    ax.axhline(ref_phi_norm_compress, color="gray", lw=0.6, ls="--",
               alpha=0.7, zorder=0)
    ax.axhline(ref_phi_norm_coherent, color="gray", lw=0.6, ls=":",
               alpha=0.7, zorder=0)

    seen_sweeps: set[str] = set()
    for sweep, condition, sig_u, phi_n, label in plotted:
        ax.scatter(sig_u, phi_n,
                   color=sweep_colors.get(sweep, "#7f7f7f"),
                   marker=sweep_markers.get(sweep, "x"),
                   s=80, edgecolors="black", linewidths=0.5,
                   label=sweep if sweep not in seen_sweeps else None,
                   zorder=3)
        seen_sweeps.add(sweep)
        ax.annotate(label, (sig_u, phi_n),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=7.5, alpha=0.85)

    # Annotated A2 reference points (just markers; not from re-runs).
    ax.scatter(0.215, 0.025, marker="*", s=220, color="black",
               edgecolors="white", linewidths=1.2, zorder=4,
               label="A2 reference (jamming α=0.2)")
    ax.annotate("A2 α=0.2\n(§4.3 reference)", (0.215, 0.025),
                xytext=(8, -14), textcoords="offset points",
                fontsize=8, fontweight="bold")

    ax.set_xlabel(r"$\sigma_u$ — within-window directional std "
                  "(steady-state cross-seed mean)", fontsize=10)
    ax.set_ylabel(r"phi_norm cross-seed $\sigma$"
                  " (per-edge $\\Phi$ regularization across seeds)", fontsize=10)
    ax.set_title(
        "Cross-sweep compressibility-signature scatter\n"
        r"low $\sigma_u$ + low phi_norm $\sigma$ → §4.3 compressibility regime",
        fontsize=11)
    ax.grid(True, alpha=0.3, zorder=0)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.92)

    fig.text(0.5, 0.02,
             "Dashed line = A2 α=0.2 phi_norm σ (0.025).  "
             "Dotted line = A2 α=1.0 phi_norm σ (0.086).  "
             "σ_u not computed for the other 7 sweeps (out of audit scope).",
             ha="center", fontsize=8, color="#444444")

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Wrote {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# Main pipeline
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    with open(CONFIG_PATH) as f:
        base_cfg = yaml.safe_load(f)

    # ---- Reusable leadership σ_u from Tier 1.A -----------------------------
    leadership_sigma_u_cache: dict[str, dict[str, Any]] = {}
    if TIER1A_AGG_PATH.exists():
        with open(TIER1A_AGG_PATH) as f:
            tier1a = json.load(f)
        for cond_key, payload in tier1a.get("per_condition", {}).items():
            leadership_sigma_u_cache[cond_key] = payload["sigma_u"]
        print(f"[init] Loaded leadership σ_u from {TIER1A_AGG_PATH.name}: "
              f"{list(leadership_sigma_u_cache.keys())}")

    # ---- Vanilla equivalence check -----------------------------------------
    print("[1/4] Vanilla-boids equivalence verification ...")
    vanilla = verify_vanilla_equivalence()
    print(f"  n=10 vanilla cluster (seed 0 byte-identical): {vanilla['n10_byte_identical']} "
          f"({len(vanilla['n10_candidates'])} conditions)")
    print(f"  n=5 sensitivity-default cluster (seed 0 byte-identical): "
          f"{vanilla['n5_byte_identical']} ({len(vanilla['n5_candidates'])} conditions)")
    print(f"  n=10 and n=5 share seed 0: {vanilla['n10_n5_share_seed0']}")

    # ---- Per-(sweep, condition) aggregation --------------------------------
    print("[2/4] Aggregating per-condition rows ...")
    rows: list[dict[str, Any]] = []
    for sweep_def in SWEEPS:
        sweep = sweep_def["sweep"]
        n_seeds = sweep_def["n_seeds"]
        seeds = list(range(n_seeds))
        compute_sigma_u = sweep in SIGMA_U_SWEEPS
        for (cond_name, scenario, overrides) in sweep_def["conditions"]:
            t0 = time.time()
            print(f"  {sweep}/{cond_name} (n={n_seeds}, σ_u re-run={compute_sigma_u})")
            row = aggregate_sweep_condition(
                sweep=sweep,
                condition=cond_name,
                scenario=scenario,
                overrides=overrides,
                base_cfg=base_cfg,
                compute_sigma_u=compute_sigma_u,
                seeds=seeds,
                leadership_sigma_u_cache=leadership_sigma_u_cache,
            )
            row["kind"] = sweep_def["kind"]
            rows.append(row)
            print(f"    Φ={row['phi_spectral']['mean']:.2f} "
                  f"[{row['phi_spectral']['ci95_lo']:.2f}, "
                  f"{row['phi_spectral']['ci95_hi']:.2f}], "
                  f"phi_norm σ={row['phi_norm']['cross_seed_sigma']:.4f}, "
                  f"dip p={row['bimodality_steady_state_pooled']['dip_p']:.3f}, "
                  f"modes={row['bimodality_steady_state_pooled']['kde_modes']}, "
                  f"t={time.time()-t0:.1f}s")

    # ---- High-w_a non-monotonicity check -----------------------------------
    print("[3/4] High-w_a non-monotonicity check ...")
    high_wa = high_wa_check()
    print(f"  Φ(w_a=1.2) = {high_wa['phi_wa_1.2']['mean']:.2f} "
          f"CI {high_wa['phi_wa_1.2']['ci95']}; "
          f"Φ(w_a=1.8) = {high_wa['phi_wa_1.8']['mean']:.2f} "
          f"CI {high_wa['phi_wa_1.8']['ci95']}")
    print(f"  diff = {high_wa['diff_18_minus_12']:+.3f} "
          f"CI {high_wa['diff_ci95']}, "
          f"d = {high_wa['cohens_d_18_vs_12']:+.3f}, "
          f"ci_overlap = {high_wa['ci_overlap']}, "
          f"verdict = {high_wa['verdict']}")

    # ---- Save aggregates JSON ----------------------------------------------
    print("[4/4] Writing audit_aggregates.json + cross_sweep_panel.png ...")
    aggregates = {
        "schema_version": 1,
        "method": {
            "T": T_STEPS,
            "W_default": W_DEFAULT,
            "stride_default": STRIDE_DEFAULT,
            "ss_quantile": SS_QUANTILE,
            "dip_p_threshold": DIP_P_THRESHOLD,
            "kde_height_frac": KDE_HEIGHT_FRAC,
            "kde_order": KDE_ORDER,
            "bootstrap_B": B_BOOT,
            "bootstrap_seed": RNG_SEED,
            "sigma_u_sweeps_recomputed": sorted(SIGMA_U_SWEEPS),
            "sigma_u_sweeps_reused_from_tier1A": ["leadership_sweep"],
        },
        "vanilla_baseline_equivalence": vanilla,
        "rows": rows,
        "high_wa_non_monotonicity_check": high_wa,
    }

    out_json = OUT_DIR / "audit_aggregates.json"
    with open(out_json, "w") as f:
        json.dump(aggregates, f, indent=2, sort_keys=False, default=float)
    print(f"  Wrote {out_json}")

    fig_path = OUT_DIR / "cross_sweep_panel.png"
    render_cross_sweep_panel(rows, fig_path)

    elapsed = time.time() - t_start
    print(f"\nDone. Total elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
