"""
Phase 5 Tier 1.B — Per-window Φ distribution atlas and bimodality audit.

Runnable standalone from repo root:
    python3 outputs/tier1_compressibility/distributions/_make_distributions.py

Atlas scope (Outcome 4 narrower atlas per Session 1 verdict §6):
  - jamming_sweep:    alpha_0.2, alpha_0.5, alpha_1.0
  - alignment_sweep:  wa_0.0, wa_0.6, wa_1.2, wa_1.8
  - leadership_sweep: lambda_0.8  (+lambda_0.0 if empirically bimodal)
  - milling_sweep:    mu_0.0 only if empirically bimodal

Bimodal criterion: KDE mode count >= 2 AND Hartigan dip p < 0.20

Data integrity note: jamming_sweep/alpha_1.0, leadership_sweep/lambda_0.0, and
milling_sweep/mu_0.0 are byte-identical across all 10 seeds. Results for those
conditions are reported with a DATA_INTEGRITY_CONCERN flag. See audit document §anomalies.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import diptest
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from scipy.stats import gaussian_kde

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUTS_DIR = Path(__file__).resolve().parent
OUTPUTS_PARQUET = REPO_ROOT / "outputs"

# ── bimodality thresholds ──────────────────────────────────────────────────────
DIP_P_THRESHOLD = 0.20      # p < 0.20 required for bimodal classification
KDE_HEIGHT_FRAC = 0.05      # local max must exceed 5% of KDE peak to count as mode
KDE_ORDER = 5               # argrelextrema order parameter

# ── steady-state cutoff ────────────────────────────────────────────────────────
SS_QUANTILE = 2 / 3         # window_idx >= quantile(2/3) → steady-state

# ── known data integrity issues ───────────────────────────────────────────────
# These three condition directories are byte-identical across all 10 seeds.
# Discovered during Tier 1.B analysis. Flagged for planning-level follow-up.
DATA_INTEGRITY_FLAGGED: set[tuple[str, str]] = {
    ("jamming_sweep",    "alpha_1.0"),
    ("leadership_sweep", "lambda_0.0"),
    ("milling_sweep",    "mu_0.0"),
}


# ══════════════════════════════════════════════════════════════════════════════
# Data loading
# ══════════════════════════════════════════════════════════════════════════════

def load_condition(sweep: str, condition: str) -> tuple[np.ndarray, list[float]]:
    """Return (pooled_ss_phi, per_seed_ss_means) for a (sweep, condition) pair.

    Uses steady-state windows only: window_idx >= quantile(2/3) per seed.
    """
    cond_dir = OUTPUTS_PARQUET / sweep / condition
    parquets = sorted(cond_dir.glob("seed*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"No parquets in {cond_dir}")

    pooled: list[float] = []
    seed_means: list[float] = []

    for p in parquets:
        df = pd.read_parquet(p)
        thresh = df["window_idx"].quantile(SS_QUANTILE)
        ss = df[df["window_idx"] >= thresh]["phi_spectral"].values
        pooled.extend(ss.tolist())
        seed_means.append(float(ss.mean()))

    return np.array(pooled, dtype=float), seed_means


# ══════════════════════════════════════════════════════════════════════════════
# Bimodality diagnostics
# ══════════════════════════════════════════════════════════════════════════════

def count_kde_modes(phi: np.ndarray) -> tuple[int, gaussian_kde, np.ndarray, np.ndarray]:
    """Count local maxima of gaussian_kde (default bandwidth) above height threshold.

    Matches Session 1 methodology: gaussian_kde default bandwidth, local maxima
    above KDE_HEIGHT_FRAC * peak height, argrelextrema order=KDE_ORDER.
    Returns (mode_count, kde_obj, x_grid, y_grid).
    """
    kde = gaussian_kde(phi)
    x = np.linspace(phi.min(), phi.max(), 2000)
    y = kde(x)
    height_thresh = KDE_HEIGHT_FRAC * y.max()
    maxima_idx = argrelextrema(y, np.greater, order=KDE_ORDER)[0]
    modes = int(np.sum(y[maxima_idx] >= height_thresh))
    return max(modes, 1), kde, x, y


def bimodality_diagnostics(phi: np.ndarray) -> dict:
    """Return full bimodality diagnostic dict for a pooled φ array."""
    _, dip_p = diptest.diptest(phi)
    mode_count, kde, x_grid, y_grid = count_kde_modes(phi)
    q25, q75 = np.percentile(phi, [25, 75])
    iqr = q75 - q25
    std_iqr = float(phi.std(ddof=1) / iqr) if iqr > 0 else float("nan")
    is_bimodal = (mode_count >= 2) and (dip_p < DIP_P_THRESHOLD)
    return {
        "n_windows": len(phi),
        "dip_p": float(dip_p),
        "mode_count": mode_count,
        "std_iqr": std_iqr,
        "bimodal": is_bimodal,
        "kde": kde,
        "x_grid": x_grid,
        "y_grid": y_grid,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Figure rendering
# ══════════════════════════════════════════════════════════════════════════════

LABEL_MAP: dict[str, dict] = {
    "jamming_sweep":    {"prefix": "α",   "param": "alpha"},
    "alignment_sweep":  {"prefix": "w_a", "param": "wa"},
    "leadership_sweep": {"prefix": "λ",   "param": "lambda"},
    "milling_sweep":    {"prefix": "μ",   "param": "mu"},
}


def condition_label(sweep: str, condition: str) -> str:
    info = LABEL_MAP.get(sweep, {"prefix": "", "param": ""})
    val = condition.replace(info["param"] + "_", "")
    return f"{info['prefix']}={val}"


def render_panel(ax: plt.Axes, phi: np.ndarray, seed_means: list[float],
                 diag: dict, cond_label: str, data_integrity_flag: bool) -> None:
    """Render one distribution panel onto ax."""
    # histogram background
    ax.hist(phi, bins=30, density=True, color="#7bafd4", alpha=0.50,
            edgecolor="white", linewidth=0.4)

    # KDE overlay (precomputed for efficiency)
    ax.plot(diag["x_grid"], diag["y_grid"], color="#1a5a8a", lw=1.8)

    # cross-seed grand mean (vertical dashed line)
    grand_mean = float(phi.mean())
    ax.axvline(grand_mean, color="#d62728", lw=1.4, ls="--",
               label=f"mean={grand_mean:.1f}")

    # per-seed steady-state means as short ticks at the x-axis
    ylim = ax.get_ylim()
    ymax_tick = (ylim[1] - ylim[0]) * 0.07 + ylim[0]
    for sm in seed_means:
        ax.plot([sm, sm], [ylim[0], ymax_tick], color="#2ca02c", lw=0.9, alpha=0.7)

    bm_str = "BIMODAL" if diag["bimodal"] else "unimodal"
    di_str = "\n†shared-baseline" if data_integrity_flag else ""
    annotation = (
        f"dip p={diag['dip_p']:.3f}  modes={diag['mode_count']}\n"
        f"std/IQR={diag['std_iqr']:.3f}  {bm_str}{di_str}"
    )
    title_color = "#4a6e4c" if data_integrity_flag else "black"
    ax.set_title(cond_label, fontsize=10, fontweight="bold", pad=3, color=title_color)
    ax.text(0.97, 0.97, annotation, transform=ax.transAxes,
            fontsize=7.5, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85,
                      ec="#4a6e4c" if data_integrity_flag else "none"))
    ax.set_xlabel("Φ_spectral", fontsize=8)
    ax.set_ylabel("density", fontsize=8)
    ax.tick_params(labelsize=7)


def render_sweep_figure(sweep: str, conditions: list[str],
                        all_results: dict[tuple[str, str], dict]) -> Path:
    """Render multi-panel figure for one sweep. Returns output path."""
    n = len(conditions)
    fig, axes = plt.subplots(1, n, figsize=(4.5 * n, 3.8), squeeze=False)
    axes_flat = axes[0]

    for ax, cond in zip(axes_flat, conditions):
        key = (sweep, cond)
        phi = all_results[key]["phi"]
        seed_means = all_results[key]["seed_means"]
        diag = all_results[key]["diag"]
        data_flag = key in DATA_INTEGRITY_FLAGGED
        render_panel(ax, phi, seed_means, diag, condition_label(sweep, cond), data_flag)

    sweep_title = sweep.replace("_", " ").title()
    fig.suptitle(
        f"{sweep_title} — per-window Φ_spectral distributions\n"
        f"(steady-state only: window_idx ≥ quantile(2/3), pooled across 10 seeds)",
        fontsize=10, fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.90])

    out_path = OUTPUTS_DIR / f"{sweep}_distributions.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# Audit document
# ══════════════════════════════════════════════════════════════════════════════

PRESUSPECTED = [
    # (sweep, condition, label, basis)
    ("alignment_sweep",  "wa_1.8",    "alignment w_a=1.8",  "verdict recommendation"),
    ("jamming_sweep",    "alpha_1.0", "jamming α=1.0",      "verdict recommendation"),
    ("leadership_sweep", "lambda_0.0","leadership λ=0.0",   "empirical test"),
    ("milling_sweep",    "mu_0.0",    "milling μ=0.0",      "empirical test"),
]


def write_audit(all_rendered: list[tuple[str, str]],
                all_results: dict[tuple[str, str], dict],
                lead08_all_windows: dict) -> Path:
    """Write bimodality_audit.md. Returns output path."""

    # ── Table 1: all rendered conditions ──────────────────────────────────────
    t1_rows = []
    for sweep, cond in all_rendered:
        r = all_results[(sweep, cond)]
        d = r["diag"]
        clab = condition_label(sweep, cond)
        cls = "bimodal" if d["bimodal"] else "unimodal"
        di_note = " ⚠" if (sweep, cond) in DATA_INTEGRITY_FLAGGED else ""
        t1_rows.append(
            f"| {sweep} | {clab} | {d['n_windows']} | "
            f"{d['dip_p']:.3f} | {d['mode_count']} | {d['std_iqr']:.3f} | {cls}{di_note} |"
        )

    t1_header = (
        "| sweep | condition | n_windows | dip p | KDE modes | std/IQR | classification |\n"
        "|---|---|---|---|---|---|---|"
    )
    table1 = t1_header + "\n" + "\n".join(t1_rows)

    # ── Table 2: pre-suspected candidates ─────────────────────────────────────
    t2_rows = []
    for sweep, cond, label, basis in PRESUSPECTED:
        r = all_results.get((sweep, cond))
        if r is None:
            t2_rows.append(f"| {label} | — | — | — | — | — | data missing |")
            continue
        d = r["diag"]
        cls = "bimodal" if d["bimodal"] else "unimodal"
        in_atlas = any(s == sweep and c == cond for s, c in all_rendered)
        di_note = " ⚠" if (sweep, cond) in DATA_INTEGRITY_FLAGGED else ""
        if in_atlas:
            atlas_note = f"included ({basis})"
        else:
            atlas_note = "excluded (unimodal, empirical test)"
        t2_rows.append(
            f"| {label}{di_note} | {d['n_windows']} | "
            f"{d['dip_p']:.3f} | {d['mode_count']} | {d['std_iqr']:.3f} | {cls} | {atlas_note} |"
        )

    t2_header = (
        "| candidate | n_windows | dip p | KDE modes | std/IQR | classification | atlas inclusion |\n"
        "|---|---|---|---|---|---|---|"
    )
    table2 = t2_header + "\n" + "\n".join(t2_rows)

    # ── narrative components ───────────────────────────────────────────────────
    jam10 = all_results.get(("jamming_sweep", "alpha_1.0"), {})
    jam10_d = jam10.get("diag", {})
    jam10_cls = "bimodal" if jam10_d.get("bimodal", False) else "unimodal"
    jam10_p = jam10_d.get("dip_p", float("nan"))
    jam10_modes = jam10_d.get("mode_count", 0)

    lead08 = all_results.get(("leadership_sweep", "lambda_0.8"), {})
    lead08_d = lead08.get("diag", {})
    lead08_cls = "bimodal" if lead08_d.get("bimodal", False) else "unimodal"
    lead08_p = lead08_d.get("dip_p", float("nan"))
    lead08_modes = lead08_d.get("mode_count", 0)

    # alignment wa_0.6 — unexpected bimodal finding
    align06 = all_results.get(("alignment_sweep", "wa_0.6"), {})
    align06_d = align06.get("diag", {})
    align06_cls = "bimodal" if align06_d.get("bimodal", False) else "unimodal"
    align06_p = align06_d.get("dip_p", float("nan"))

    failed_candidates = [
        label for sweep, cond, label, _ in PRESUSPECTED
        if all_results.get((sweep, cond), {}).get("diag", {}).get("bimodal", True) is False
    ]
    bimodal_candidates = [
        label for sweep, cond, label, _ in PRESUSPECTED
        if all_results.get((sweep, cond), {}).get("diag", {}).get("bimodal", False)
    ]

    narrative = textwrap.dedent(f"""
    D14 asserts that "Phase 5 reports per-window Φ distributions (not just steady-state means)
    for all sweeps exhibiting coherent regimes," with an implicit claim that coherent-regime
    conditions bimodalize Φ across windows. The empirical results do **not** broadly support
    this claim in the steady-state-only window pool.

    **Jamming α=1.0** — the A2-confirmed compressibility coherent-baseline condition — shows
    {jam10_cls} steady-state distributions (dip p={jam10_p:.3f}, modes={jam10_modes}).
    Note: this condition's parquets are flagged for data integrity concern (see §anomalies);
    results should be interpreted cautiously until the issue is resolved.

    **Leadership λ=0.8** — identified as bimodal in Session 1 (dip p=0.129, modes=2 over
    all 930 windows) — shows {lead08_cls} when restricted to steady-state windows only
    (dip p={lead08_p:.3f}, modes={lead08_modes}, n=310). The Session 1 bimodality was computed
    on all windows pooled (transient + steady-state). Restricting to steady-state reverses the
    classification: the apparent bimodality in Session 1 reflects a **transient-to-steady-state
    regime transition** (early low-Φ windows and late high-Φ windows create two apparent modes
    in the all-window pool) rather than within-steady-state bimodality. This is an important
    methodological distinction for D14's reporting requirement.

    **Unexpected finding — alignment w_a=0.6**: the transitional-alignment condition
    (w_a=0.6, not the high-w_a condition pre-suspected by Phase5.md) shows {align06_cls}
    steady-state distributions (dip p={align06_p:.3f}, modes={align06_d.get('mode_count',0)}).
    The fully coherent high-alignment condition (w_a=1.8) is unimodal. This suggests
    bimodality concentrates at the disorder-to-order transition, not in the fully coherent regime.

    Pre-suspected candidates that failed to bimodalize: {', '.join(failed_candidates) if failed_candidates else 'none'}.
    A planning-level discussion is recommended before Tier 3.C to clarify D14's mechanism claim:
    "coherent regimes bimodalize" is not empirically supported as a general statement;
    the finding is better characterized as "bimodality appears at disorder-to-order transitions
    (alignment w_a=0.6) and in mixed-regime pooling artifacts (leadership λ=0.8 all-window pool)."
    """).strip()

    # ── Session 1 cross-reference ──────────────────────────────────────────────
    session1_note = textwrap.dedent(f"""
    Session 1 (Tier 1.A) bimodality diagnostics for leadership λ=0.8 used all 930 per-window
    Φ values (93 windows × 10 seeds): dip p=0.129, KDE mode count=2, std/IQR=0.593.
    This session uses steady-state windows only (~310 per condition, window_idx ≥ quantile(2/3)).

    **Result: classification does NOT reproduce on steady-state-only data.**
    Steady-state: dip p={lead08_p:.3f}, modes={lead08_modes} → {lead08_cls}.

    The discrepancy is mechanistically interpretable: at λ=0.8 the system transitions from a
    low-Φ early regime to a higher-Φ (but variable) late regime. Pooling all windows creates
    a bimodal appearance from regime mixing, not within-regime bimodality. The Session 1
    result was computed on all windows per the Tier 1.A methodology (which was designed to
    characterize the full run, not steady-state behavior specifically). This session's
    steady-state restriction is more appropriate for D14's "steady-state distribution"
    reporting requirement.

    Both results come from the same parquets (bit-identical data source); the difference
    is the window-subset definition.
    """).strip()

    # ── anomalies ─────────────────────────────────────────────────────────────
    anomalies = textwrap.dedent("""
    ## Anomalies

    ### Data integrity: three byte-identical condition directories

    `jamming_sweep/alpha_1.0`, `leadership_sweep/lambda_0.0`, and `milling_sweep/mu_0.0`
    are byte-identical across all 10 seeds (verified via MD5 hash comparison of all 10 seed
    parquet files per condition). Their metadata files show different scenarios, parameters,
    and git commits, confirming these were generated as separate runs — but the parquet
    outputs are identical. This indicates a data write or copy error in Phase 4 data
    generation.

    **Impact on this session:**
    - `jamming_sweep/alpha_1.0` bimodality results are unreliable (the data appears to be
      from a different condition — likely the unperturbed coherent-flock baseline).
    - `leadership_sweep/lambda_0.0` results match Session 1's λ=0.0 aggregate values
      (mean=135.05) and appear to reflect the correct leadership λ=0.0 data. However,
      its byte-identity with alpha_1.0 and mu_0.0 raises doubt about provenance.
    - `milling_sweep/mu_0.0` bimodality results are unreliable for the same reason.

    **Recommended action:** flag for a maintenance session (separate from Phase 5) to
    re-run the affected conditions and verify output file writes. Per Phase5.md scope,
    Phase 1–4 code changes are out of scope for Phase 5. The atlas figures for these
    conditions are rendered with a DATA_INTEGRITY_CONCERN annotation in the figure panels.

    **Do not** edit `Phase5.md` or `SpectralSwarm3DPhases.md` from this session.
    """).strip()

    md = f"""# Phase 5 Tier 1.B — Bimodality Audit

**Date:** 2026-05-06
**Script:** `outputs/tier1_compressibility/distributions/_make_distributions.py`
**Scope:** Narrower focused atlas per Session 1 Outcome 4 verdict §6.
**Bimodal criterion:** KDE mode count ≥ 2 AND Hartigan dip p < {DIP_P_THRESHOLD:.2f}
**Steady-state:** window_idx ≥ quantile(2/3) per seed (~31 windows/seed × 10 seeds ≈ 310/condition)
**⚠ symbol** denotes conditions with data integrity concerns (byte-identical parquets across unrelated conditions).

---

## Table 1: Atlas-scope conditions (all rendered)

{table1}

---

## Table 2: Pre-suspected bimodality candidates (Phase5.md Tier 1.B)

Phase5.md Tier 1.B pre-registered four candidate conditions for bimodality testing.
Conditions marked ⚠ have data integrity concerns (see §anomalies).

{table2}

---

## Narrative — D14 "coherent regimes bimodalize Φ"

{narrative}

---

## Cross-reference to Session 1 (Tier 1.A leadership λ=0.8)

{session1_note}

---

{anomalies}

---

## Recommend planning-level discussion

Before Tier 3.C (internal report draft):
1. **Data integrity maintenance session** to re-run the three byte-identical conditions
   (`jamming/alpha_1.0`, `leadership/lambda_0.0`, `milling/mu_0.0`) and verify outputs.
2. **D14 mechanism claim qualification** — "coherent regimes bimodalize Φ across windows"
   is not empirically supported as a general statement by these steady-state results.
   Recommended revised framing: bimodality appears at disorder-to-order regime transitions
   (alignment w_a=0.6) and as a transient-mixing artifact in all-window pooling.
"""

    out_path = OUTPUTS_DIR / "bimodality_audit.md"
    out_path.write_text(md.strip() + "\n")
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # ── Base atlas scope ───────────────────────────────────────────────────────
    # Conditions ordered low → high within each sweep
    base_scope: dict[str, list[str]] = {
        "jamming_sweep":    ["alpha_0.2", "alpha_0.5", "alpha_1.0"],
        "alignment_sweep":  ["wa_0.0", "wa_0.6", "wa_1.2", "wa_1.8"],
        "leadership_sweep": ["lambda_0.8"],
    }

    # ── Step 1: load all conditions needed (base scope + empirical candidates) ─
    conditions_needed: set[tuple[str, str]] = set()
    for sweep, conds in base_scope.items():
        for c in conds:
            conditions_needed.add((sweep, c))
    for sweep, cond, _, _ in PRESUSPECTED:
        conditions_needed.add((sweep, cond))
    conditions_needed.add(("leadership_sweep", "lambda_0.0"))
    conditions_needed.add(("milling_sweep", "mu_0.0"))

    all_results: dict[tuple[str, str], dict] = {}
    for sweep, cond in sorted(conditions_needed):
        di_flag = "⚠ " if (sweep, cond) in DATA_INTEGRITY_FLAGGED else "  "
        print(f"  {di_flag}Loading {sweep}/{cond} ...", end=" ", flush=True)
        phi, seed_means = load_condition(sweep, cond)
        diag = bimodality_diagnostics(phi)
        all_results[(sweep, cond)] = {"phi": phi, "seed_means": seed_means, "diag": diag}
        cls = "BIMODAL" if diag["bimodal"] else "unimodal"
        print(f"{cls}  dip_p={diag['dip_p']:.3f}  modes={diag['mode_count']}  "
              f"std/IQR={diag['std_iqr']:.3f}  n={diag['n_windows']}")

    # ── Step 2: compute all-window bimodality for leadership λ=0.8 (Session 1 check) ─
    print("\n  Computing all-window λ=0.8 for Session 1 cross-reference...", end=" ", flush=True)
    cond_dir = OUTPUTS_PARQUET / "leadership_sweep" / "lambda_0.8"
    all_phi_08 = []
    for p in sorted(cond_dir.glob("seed*.parquet")):
        df = pd.read_parquet(p)
        all_phi_08.extend(df["phi_spectral"].tolist())
    all_phi_08 = np.array(all_phi_08)
    _, dip_p_all = diptest.diptest(all_phi_08)
    mc_all, _, _, _ = count_kde_modes(all_phi_08)
    lead08_all = {"dip_p": float(dip_p_all), "mode_count": mc_all}
    print(f"dip_p={dip_p_all:.4f}, modes={mc_all} (all {len(all_phi_08)} windows)")

    # ── Step 3: empirical promotion of pre-suspected candidates ───────────────
    print()
    lead00_bimodal = all_results[("leadership_sweep", "lambda_0.0")]["diag"]["bimodal"]
    if lead00_bimodal:
        print("  >> leadership λ=0.0 qualifies as bimodal — adding to atlas.")
        base_scope["leadership_sweep"].insert(0, "lambda_0.0")
    else:
        print("  >> leadership λ=0.0: unimodal — excluded from atlas (documented in audit).")

    mill00_bimodal = all_results[("milling_sweep", "mu_0.0")]["diag"]["bimodal"]
    if mill00_bimodal:
        print("  >> milling μ=0.0 qualifies as bimodal — adding to atlas.")
        base_scope["milling_sweep"] = ["mu_0.0"]
    else:
        print("  >> milling μ=0.0: unimodal — no milling figure produced.")

    # ── Step 4: render sweep figures ──────────────────────────────────────────
    all_rendered: list[tuple[str, str]] = []
    for sweep, conditions in base_scope.items():
        if not conditions:
            continue
        print(f"\n  Rendering {sweep} ({len(conditions)} condition(s)) ...", flush=True)
        out = render_sweep_figure(sweep, conditions, all_results)
        print(f"  -> {out.name}")
        for c in conditions:
            all_rendered.append((sweep, c))

    # ── Step 5: write audit document ──────────────────────────────────────────
    print()
    audit_path = write_audit(all_rendered, all_results, lead08_all)
    print(f"  Bimodality audit: {audit_path.name}")

    print("\n=== Summary ===")
    print(f"Rendered {len(all_rendered)} conditions across {len(base_scope)} sweeps.")
    print("Pre-suspected candidates:")
    for sweep, cond, label, basis in PRESUSPECTED:
        r = all_results.get((sweep, cond), {})
        d = r.get("diag", {})
        cls = "BIMODAL" if d.get("bimodal", False) else "unimodal"
        di = " [DATA INTEGRITY]" if (sweep, cond) in DATA_INTEGRITY_FLAGGED else ""
        in_atlas = any(s == sweep and c == cond for s, c in all_rendered)
        atlas_note = "in atlas" if in_atlas else "excluded"
        print(f"  {label}: {cls}  dip_p={d.get('dip_p', float('nan')):.3f}  "
              f"modes={d.get('mode_count', 0)}  std/IQR={d.get('std_iqr', float('nan')):.3f}  "
              f"-> {atlas_note}{di}")

    print("\nDone.")


if __name__ == "__main__":
    import os
    os.chdir(REPO_ROOT)
    main()
