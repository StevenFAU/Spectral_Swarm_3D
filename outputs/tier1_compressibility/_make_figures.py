"""Phase 5 Tier 1.A — render the two required figures from saved aggregates.

Run after ``_make_aggregates.py`` has produced ``aggregates.json``,
``mechanism_diagnostic.npz``, and ``per_window_timeseries.npz``::

    /home/otacon/Spectral_Swarm_3D/.venv/bin/python3 outputs/tier1_compressibility/_make_figures.py

Outputs
-------
- ``outputs/tier1_compressibility/leadership_panel.png`` — 2×2 panel:
  Φ + σ_u + leader compactness + per-window Φ histograms.
- ``outputs/tier1_compressibility/mi_matrix_diagnostic.png`` — side-by-side
  Fiedler-reordered MI heatmaps at λ=0.0 and λ=2.4 with descriptor table.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "outputs" / "tier1_compressibility"

CONDITIONS = [0.0, 0.8, 1.6, 2.4]
COND_LABELS = [f"λ={c}" for c in CONDITIONS]
COND_COLORS = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]

W = 40
STRIDE = 5


# =============================================================================
# Panel figure
# =============================================================================


def _means_and_cis(agg: dict, key_metric: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    """Pull (means, ci_lo, ci_hi, per_seed_arrays) for one metric across conditions."""
    means = np.array([agg["per_condition"][f"lambda_{c}"][key_metric]["mean"] for c in CONDITIONS])
    lo = np.array([agg["per_condition"][f"lambda_{c}"][key_metric]["ci95_lo"] for c in CONDITIONS])
    hi = np.array([agg["per_condition"][f"lambda_{c}"][key_metric]["ci95_hi"] for c in CONDITIONS])
    per_seed = [
        np.array(agg["per_condition"][f"lambda_{c}"][key_metric]["per_seed"]) for c in CONDITIONS
    ]
    return means, lo, hi, per_seed


def render_panel(agg: dict, ts: dict[str, np.ndarray]) -> Path:
    fig = plt.figure(figsize=(13, 10), dpi=150)
    gs = GridSpec(2, 2, figure=fig, wspace=0.28, hspace=0.34)

    # ---- (a) Φ_spectral with per-seed scatter ------------------------------
    ax = fig.add_subplot(gs[0, 0])
    means, lo, hi, per_seed = _means_and_cis(agg, "phi_spectral")
    yerr = np.stack([means - lo, hi - means])
    x = np.arange(len(CONDITIONS))
    ax.errorbar(
        x, means, yerr=yerr, fmt="o", color="black", capsize=5, lw=1.5, ms=8,
        label="cross-seed mean ± 95% bootstrap CI",
    )
    rng = np.random.default_rng(1)
    for j, ps in enumerate(per_seed):
        jitter = (rng.random(len(ps)) - 0.5) * 0.18
        ax.scatter(np.full(len(ps), x[j]) + jitter, ps, alpha=0.55, s=30, color=COND_COLORS[j])
    # Highlight seed 8 at λ=2.4.
    seed_idx = 8
    seed8_phi = per_seed[3][seed_idx]
    ax.scatter([x[3]], [seed8_phi], marker="*", s=240, edgecolor="red",
               facecolor="none", lw=2.0, label=f"seed 8 (outlier, Φ={seed8_phi:.1f})")
    ax.set_xticks(x)
    ax.set_xticklabels(COND_LABELS)
    ax.set_ylabel("Φ_spectral (steady-state mean per seed)")
    ax.set_title("(a)  Φ_spectral by condition")
    ax.set_yscale("symlog", linthresh=1.0)
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.25)

    # ---- (b) σ_u -----------------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    means, lo, hi, per_seed = _means_and_cis(agg, "sigma_u")
    yerr = np.stack([means - lo, hi - means])
    ax.errorbar(x, means, yerr=yerr, fmt="o", color="black", capsize=5, lw=1.5, ms=8)
    for j, ps in enumerate(per_seed):
        jitter = (rng.random(len(ps)) - 0.5) * 0.18
        ax.scatter(np.full(len(ps), x[j]) + jitter, ps, alpha=0.55, s=30, color=COND_COLORS[j])
    ax.set_xticks(x); ax.set_xticklabels(COND_LABELS)
    ax.set_ylabel("σ_u (within-window directional std)")
    ax.set_title("(b)  σ_u by condition\nPredicted: monotonic compression at high λ")
    ax.grid(alpha=0.25)

    # ---- (c) leader compactness --------------------------------------------
    ax = fig.add_subplot(gs[1, 0])
    means, lo, hi, per_seed = _means_and_cis(agg, "leader_compactness")
    yerr = np.stack([means - lo, hi - means])
    ax.errorbar(x, means, yerr=yerr, fmt="o", color="black", capsize=5, lw=1.5, ms=8)
    for j, ps in enumerate(per_seed):
        jitter = (rng.random(len(ps)) - 0.5) * 0.18
        ax.scatter(np.full(len(ps), x[j]) + jitter, ps, alpha=0.55, s=30, color=COND_COLORS[j])
    ax.set_xticks(x); ax.set_xticklabels(COND_LABELS)
    ax.set_ylabel("Mean leader–leader pairwise distance (steady-state)")
    ax.set_title("(c)  Leader-group compactness by condition")
    ax.set_yscale("symlog", linthresh=0.5)
    ax.grid(alpha=0.25)

    # ---- (d) per-window Φ histograms ---------------------------------------
    ax = fig.add_subplot(gs[1, 1])
    for j, c in enumerate(CONDITIONS):
        key = f"lambda_{str(c).replace('.', '_')}_phi"
        all_phi = ts[key].ravel()  # all windows × 10 seeds = 930 windows
        bm = agg["bimodality"][f"lambda_{c}"]
        label = (
            f"{COND_LABELS[j]}: dip_p={bm['dip_p']:.2f}, "
            f"modes={bm['kde_modes']}, std/IQR={bm['std_over_iqr']:.2f}"
        )
        ax.hist(
            all_phi, bins=60, alpha=0.55, color=COND_COLORS[j], label=label, density=True,
            histtype="stepfilled", edgecolor=COND_COLORS[j],
        )
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlabel("Φ_spectral (per-window, pooled across 10 seeds)")
    ax.set_ylabel("density")
    ax.set_title("(d)  Per-window Φ distribution by condition")
    ax.legend(loc="upper right", fontsize=7.5)
    ax.grid(alpha=0.25)

    fig.suptitle(
        "Phase 5 Tier 1.A — Leadership sweep: Φ, σ_u, leader compactness, Φ distribution",
        fontsize=13, y=0.995,
    )
    out_path = OUT_DIR / "leadership_panel.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


# =============================================================================
# MI-matrix diagnostic figure
# =============================================================================


def fiedler_reorder(MI: np.ndarray) -> np.ndarray:
    """Return permutation that reorders rows/cols by ascending Fiedler eigenvector."""
    from spectral_swarm_3d.analysis.spectral import fiedler_vector, normalized_laplacian
    L = normalized_laplacian(MI)
    f = fiedler_vector(0.5 * (L + L.T))
    return np.argsort(f)


def render_mi_diagnostic(agg: dict, mech: dict[str, np.ndarray]) -> Path:
    import sys
    sys.path.insert(0, str(REPO_ROOT / "src"))

    M_low = mech["lambda_0_0_MI"]
    M_high = mech["lambda_2_4_MI"]
    is_leader_low = mech["lambda_0_0_is_leader"].astype(bool)
    is_leader_high = mech["lambda_2_4_is_leader"].astype(bool)
    fied_low = mech["lambda_0_0_fiedler"]
    fied_high = mech["lambda_2_4_fiedler"]
    meta_low = mech["lambda_0_0_meta"]
    meta_high = mech["lambda_2_4_meta"]

    perm_low = fiedler_reorder(M_low)
    perm_high = fiedler_reorder(M_high)

    Mr_low = M_low[np.ix_(perm_low, perm_low)]
    Mr_high = M_high[np.ix_(perm_high, perm_high)]

    # Shared color scale: pick max across both matrices.
    vmax = max(M_low.max(), M_high.max())

    fig = plt.figure(figsize=(15, 9), dpi=150)
    gs = GridSpec(
        2, 3,
        width_ratios=[1.0, 1.0, 0.85],
        height_ratios=[1.0, 0.18],
        figure=fig, wspace=0.18, hspace=0.40,
    )

    # ---- λ=0.0 heatmap -----------------------------------------------------
    axL = fig.add_subplot(gs[0, 0])
    imL = axL.imshow(Mr_low, cmap="viridis", vmin=0, vmax=vmax, aspect="equal")
    axL.set_title(
        f"λ=0.0  (rep seed {int(meta_low[0])}, window {int(meta_low[1])}, "
        f"steps {int(meta_low[2])}–{int(meta_low[3])})"
    )
    axL.set_xlabel("agent (Fiedler-reordered)")
    axL.set_ylabel("agent (Fiedler-reordered)")
    # Mark leaders with a tick on the axis.
    leaders_perm_low = np.array([is_leader_low[perm_low[i]] for i in range(len(perm_low))])
    for i in np.where(leaders_perm_low)[0]:
        axL.axhline(i, color="red", lw=0.4, alpha=0.5)
        axL.axvline(i, color="red", lw=0.4, alpha=0.5)

    # ---- λ=2.4 heatmap -----------------------------------------------------
    axR = fig.add_subplot(gs[0, 1])
    imR = axR.imshow(Mr_high, cmap="viridis", vmin=0, vmax=vmax, aspect="equal")
    axR.set_title(
        f"λ=2.4  (rep seed {int(meta_high[0])}, window {int(meta_high[1])}, "
        f"steps {int(meta_high[2])}–{int(meta_high[3])})"
    )
    axR.set_xlabel("agent (Fiedler-reordered)")
    leaders_perm_high = np.array(
        [is_leader_high[perm_high[i]] for i in range(len(perm_high))]
    )
    for i in np.where(leaders_perm_high)[0]:
        axR.axhline(i, color="red", lw=0.4, alpha=0.5)
        axR.axvline(i, color="red", lw=0.4, alpha=0.5)

    # ---- Colorbar ----------------------------------------------------------
    cbar_ax = fig.add_axes([0.665, 0.32, 0.012, 0.50])
    fig.colorbar(imR, cax=cbar_ax, label="MI (nats)")

    # ---- Descriptor table --------------------------------------------------
    axT = fig.add_subplot(gs[0, 2])
    axT.set_axis_off()
    rows = [
        ("metric", "A2 α=0.2\n(compressibility)", "A2 α=1.0\n(coherent)", "λ=0.0", "λ=2.4"),
    ]

    a02 = agg["mechanism_diagnostic"]["A2_reference"]["alpha_0.2"]
    a10 = agg["mechanism_diagnostic"]["A2_reference"]["alpha_1.0"]
    md0 = agg["mechanism_diagnostic"]["lambda_0.0"]
    md4 = agg["mechanism_diagnostic"]["lambda_2.4"]
    rows += [
        ("MI mean", f"{a02['MI_mean']:.3f}", f"{a10['MI_mean']:.3f}",
         f"{md0['MI_mean']:.3f}", f"{md4['MI_mean']:.3f}"),
        ("MI std", f"{a02['MI_std']:.3f}", f"{a10['MI_std']:.3f}",
         f"{md0['MI_std']:.3f}", f"{md4['MI_std']:.3f}"),
        ("MI Q25/50/75",
         f"{a02['MI_q25']:.2f}/{a02['MI_q50']:.2f}/{a02['MI_q75']:.2f}",
         f"{a10['MI_q25']:.2f}/{a10['MI_q50']:.2f}/{a10['MI_q75']:.2f}",
         f"{md0['MI_q25']:.2f}/{md0['MI_q50']:.2f}/{md0['MI_q75']:.2f}",
         f"{md4['MI_q25']:.2f}/{md4['MI_q50']:.2f}/{md4['MI_q75']:.2f}"),
        ("ρ(MI, -d)", f"{a02['spearman_r_MI_neg_d']:+.2f}", f"{a10['spearman_r_MI_neg_d']:+.2f}",
         f"{md0['spearman_r_MI_neg_d']:+.2f}", f"{md4['spearman_r_MI_neg_d']:+.2f}"),
        ("Fiedler/kmeans\nagreement",
         f"{a02['fiedler_kmeans_pair_agreement']:.2f}",
         f"{a10['fiedler_kmeans_pair_agreement']:.2f}",
         f"{md0['fiedler_kmeans_pair_agreement']:.2f}",
         f"{md4['fiedler_kmeans_pair_agreement']:.2f}"),
        ("Fiedler λ_2", f"{a02['fiedler_eigval']:.2f}", f"{a10['fiedler_eigval']:.2f}",
         f"{md0['fiedler_eigval']:.2f}", f"{md4['fiedler_eigval']:.2f}"),
        ("MI top-eig gap\n(top1 - top2)",
         f"{a02['MI_gap_top1_top2']:.1f}",
         f"{a10['MI_gap_top1_top2']:.1f}",
         f"{md0['MI_gap_top1_top2']:.1f}",
         f"{md4['MI_gap_top1_top2']:.1f}"),
    ]
    table = axT.table(
        cellText=[r[1:] for r in rows[1:]],
        rowLabels=[r[0] for r in rows[1:]],
        colLabels=[r for r in rows[0][1:]],
        loc="center",
        cellLoc="center",
        rowLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 1.7)
    axT.set_title("Structural descriptors (A2 reference vs leadership rep windows)", fontsize=10)

    # ---- Bottom strip: interpretation + leader marker key ------------------
    axN = fig.add_subplot(gs[1, :])
    axN.set_axis_off()
    interp = (
        "Compressibility signature (A2 α=0.2): high uniform MI, ρ near 0, agreement ≈ chance (0.5), "
        "large MI eigenvalue gap (>10).  Coherent baseline (A2 α=1.0): low MI, ρ ≈ +0.4, "
        "agreement ≈ 0.78, small gap (≈ 1.8).\n"
        f"At λ=2.4 the MI matrix has chance-level Fiedler/kmeans agreement (matches compressibility) "
        f"but MI mean is low ({md4['MI_mean']:.2f} not ≈ 0.49), spatial dependence is moderate-strong "
        f"(ρ ≈ {md4['spearman_r_MI_neg_d']:+.2f}, not ≈ +0.10), and the eigenvalue gap is intermediate "
        f"({md4['MI_gap_top1_top2']:.1f}, not >10).  3/4 descriptors fail the compressibility signature.\n"
        "Red guide lines mark leader agents (8 of 40)."
    )
    axN.text(0.01, 0.95, interp, fontsize=9.5, va="top", wrap=True)

    fig.suptitle(
        "MI matrix diagnostic — λ=0.0 vs λ=2.4 (Fiedler-reordered, shared color scale)",
        fontsize=13, y=0.995,
    )
    out_path = OUT_DIR / "mi_matrix_diagnostic.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    with open(OUT_DIR / "aggregates.json") as f:
        agg = json.load(f)
    mech = dict(np.load(OUT_DIR / "mechanism_diagnostic.npz"))
    ts = dict(np.load(OUT_DIR / "per_window_timeseries.npz"))

    p1 = render_panel(agg, ts)
    print(f"Wrote {p1}")
    p2 = render_mi_diagnostic(agg, mech)
    print(f"Wrote {p2}")


if __name__ == "__main__":
    main()
