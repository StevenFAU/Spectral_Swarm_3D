# Phase 5 — Tier 3.A Figure Composition Plan

**Generated:** 2026-05-07.
**Author session:** Opus 4.7 xhigh, Tier 3.A composition only (no rendering).
**Inputs consumed:**
- `Phase5.md` Tier 3.A (eight-figure spec, pre-registered)
- `outputs/comparison/cross_sweep/findings_summary.md` (Tier 2.C narrative)
- `outputs/tier1_compressibility/cross_sweep_audit.md` (Tier 1.C verdict)
- `outputs/tier1_compressibility/leadership_prediction_verdict.md` (Tier 1.A Outcome 4)
- `outputs/tier1_compressibility/distributions/bimodality_audit.md` (Tier 1.B atlas)
- `outputs/surrogates/README_summary.md` (Tier 2.B nulls + method validation)
- `outputs/comparison/cross_sweep/scenario_summary.csv` (38-row canonical fact sheet)
- `outputs/comparison/cross_sweep/scenario_agreement_spearman.csv` (cross-condition×metric Spearman matrix)
- `outputs/comparison/cross_sweep/monitoring_roc.csv` (155-row per-metric AUC)
- `outputs/comparison/{jamming_sweep,split_merge_sweep}/matched_control_deltas.csv`
- `outputs/comparison/<sweep>/eta_squared.csv` (per-sweep η² with bootstrap CI)
- `src/spectral_swarm_3d/analysis/plotting.py` (existing 2D-mirror style — `configure_style`, `_save`, color/marker idiom)
- Legacy 2D-mirror figures already on disk under `outputs/figures/<sweep>/` (12 sweep subdirectories)

**Scope of this document.** Composition decisions for the eight Tier 3.A figures. No matplotlib code. No rendering. The renderer (Sonnet) session consumes this document and produces files under `outputs/figures/composition/` (new subdirectory; legacy per-sweep figures stay where they are).

**Empirical picture this composition is built around** (post-Tier-2.C):

- **§4.2 transitional peak — confirmed at TWO instances across orthogonal axes:** `alignment w_a=0.6` (dip p=0.102, modes=2; mean-peak partial — the alignment "disordered" endpoint w_a=0.0 has cohesion+separation MI elevation so cannot test mean-peak cleanly) and `noise σ=0.2` (dip p=7.6×10⁻⁶ — strongest in the audit; full mean-peak signature; Φ=144.63 above sync σ=0.0 (129.65) AND random σ=0.5 (85.03); surrogate z=32.92 is the strongest in Tier 2.B).
- **§4.3 compressibility — confirmed at ONE instance:** `jamming α=0.2` (Φ=187.23, +38.6% above vanilla baseline α=1.0 at 135.05; CIs disjoint; σ_u floor-locked at 0.59 above coherent α=1.0 at 0.52; phi_norm cross-seed σ low at 0.027; surrogate z=16.17, observed > null in the §4.3-prediction direction).
- **Leadership Outcome 4 — Φ collapse via leader-block partition, NOT compressibility:** `leadership λ=2.4` (Φ=8.73 vs vanilla baseline 135.05, d=+5.0, CIs disjoint); MI matrix block-structured around 8-leader cluster; Fiedler-bipartition ⟷ leader-membership pair agreement = 1.000 (perfect); MI mean low (0.19) and ρ(MI, −d) moderate-strong (+0.30) — three of four A2 compressibility descriptors fail.
- **split_merge §4.3 candidate flag — exploratory only:** seed-0 single-seed surrogate z=−5.08 (observed below null), but Φ=105.41 is *below* vanilla baseline (wrong direction for §4.3); event-sweep confound; σ_u not computed. Reported as "exploratory candidate, not confirmed §4.3 instance."
- **Method validation:** synthetic AR(1) i.i.d. control passes (z=−0.53 within surrogate 95% CI). z=3.12 boundary-synchrony floor from disabled-interaction control; all eight scenario z-scores either clearly above this (smallest positive: leadership λ=1.6 at z=8.38) or below by signed direction (split_merge z=−5.08).

The headline empirical claim is therefore: **the Bailey & Schneider (2025) §4.2/§4.3 mechanism is empirically grounded in this 3D swarm across three orthogonal perturbation axes — alignment coupling (§4.2), additive noise (§4.2), and jamming severity (§4.3) — with the leadership-coupling axis tested-and-disconfirmed as a third compressibility instance, falling instead under a structurally distinct leader-block-partition mechanism.** This three-mechanism-family picture is what the primary figure must communicate.

---

## §0 — Cross-figure conventions

### Color palette (per sweep family, categorical)

ColorBrewer Set1 hexes, assigned per sweep family. These are the canonical colors used wherever a figure plots multiple sweeps on a shared axis (figs 4, 6, 7) or color-codes scenarios in a legend (fig 1's mechanism rows borrow them for their respective sweep's instance).

| Sweep | Hex | Color name |
|---|---|---|
| `alignment_sweep` | `#E41A1C` | red |
| `jamming_sweep` | `#377EB8` | blue |
| `leadership_sweep` | `#4DAF4A` | green |
| `noise_sweep` | `#984EA3` | purple |
| `milling_sweep` | `#FF7F00` | orange |
| `split_merge_sweep` | `#A65628` | brown |
| `vanilla_baseline` (collapsed alias) | `#999999` | neutral gray |
| `n_sensitivity_*`, `w_sensitivity`, `alignment_rule_sensitivity`, `sensitivity` | `#F781BF`, `#FFFF33` (varied; sub-categorical) | pink / yellow tones |

**Within-sweep ordering** (when a figure plots conditions within one sweep on a shared axis — e.g., fig 1 row col 3 trajectories): use a sequential lightness ramp from the sweep's hue. The endpoint corresponding to the §4.2/§4.3 instance is rendered at full saturation; the coherent / vanilla-baseline endpoint at the lightest tint. This makes the instance condition pop visually without breaking the family-color identity.

**Why Set1 over Dark2 / tab10:** Set1 has been used in the legacy 2D-mirror per-sweep figures already on disk (`outputs/figures/<sweep>/agreement_*.{pdf,png}`); inheriting it preserves visual continuity for any reader who has seen the 2D internal report. The renderer should confirm the legacy figures' hex codes and align if they differ — but Set1 is the safe default per the original 2D code's `tab:blue` / `tab:orange` style, which Set1 is a near-equivalent alternative for printable output.

### Marker conventions (per metric family, where multiple metrics share an axis)

| Metric family | Marker | Use cases |
|---|---|---|
| Spectral (`phi_spectral`, `phi_norm`) | `o` (filled circle) | figs 2, 3, 4, 6, 7 |
| TDA H0 (`*_TP_0`, `*_MP_0`, `*_B_base_0`) | `D` (filled diamond) | figs 2, 3, 4, 7 |
| TDA H1 (`*_TP_1`, `*_MP_1`, `*_B_base_1`) | `s` (filled square) | figs 2, 3, 4, 7 |
| TDA H2 (`*_TP_2`, `*_MP_2`, `*_B_base_2`) | `^` (filled triangle) | figs 2, 3, 4, 7 — H2 emphasized in figure 4 caption since it's a 3D-only addition |
| Classical (`polarization`, `sigma_u`, `angular_momentum_norm`) | `+` (plus, then `x` if more than one classical line) | figs 1, 2, 3 |

Marker-shape conveys metric family; line-color conveys sweep / scenario. On figures where only one metric per panel renders (fig 1 Φ-distribution panels, fig 8 snapshots), markers are not used and color carries semantics.

### Significance and annotation conventions

- **95% bootstrap CIs** rendered as **shaded bands** along sweep-axis lines (figs 1 col 3, 7) and as **error bars** on bar charts (fig 3 sensitivity, fig 5 deltas, fig 6 surrogate).
- **CI-disjointness flag** on bar charts: pairs of bars whose CIs do not overlap get a small bracket and `*` between them; pairs that overlap get no annotation. Not asterisks-by-significance-level (we are not running formal hypothesis tests at the figure level — bootstrap CIs are the primary uncertainty representation).
- **§4.2-confirmed instance**: small gold-filled open circle (`o` with `markerfacecolor='#FFD700'`) annotation overlaid on the relevant data point, plus an in-panel text label "§4.2 (n=2 instances)" or "§4.2" depending on space.
- **§4.3-confirmed instance**: small filled triangle annotation (`^`, `markerfacecolor='#FFD700'`); label "§4.3".
- **Leader-block partition**: small filled square (`s`, `markerfacecolor='#FFD700'`); label "leader-block".
- **Exploratory split_merge §4.3 candidate**: hollow diamond (`D`, `markerfacecolor='none'`); footnote "(exploratory: single-seed)" in caption.
- **Boundary-synchrony floor** (z=3.12 from disabled-interaction control): horizontal dashed gray line on fig 6 (surrogate null comparison) at z=3.12, with text label "boundary-synchrony floor (z=3.12)" right-aligned. Caption clarifies this is a model-level effect, not a method bias.
- **Surrogate-significant scenarios**: in fig 6, observed-vs-surrogate bars whose observed point exceeds the surrogate 95% CI are annotated with the z-score numerically above the bar (e.g., "z=16.17"). Bars whose observed point is below the surrogate CI (only `split_merge` at z=−5.08) are colored differently (light brown — the sweep's family color but de-saturated) and labeled "z=−5.08 (exploratory)".
- **Vanilla-baseline collapse mark** (`†`): in figures showing per-condition data where any condition is byte-identical to the vanilla baseline, that condition's label gets a `†` superscript. Caption legend: "† byte-identical to vanilla-boids baseline (8-condition collapse — see audit table)."
- **Sub-threshold / underpowered** (e.g., n=5 sensitivity sweeps): `‡` superscript with caption note.

### §4.2 / §4.3 / leader-block visual flags (cross-figure linkage)

The same scenario shows up in multiple figures (e.g., `noise σ=0.2` is in figs 1, 4, 6); a small mechanism-family glyph appears next to the scenario label every time it's plotted, so the reader picks up the linkage without re-reading the caption. The three glyphs are gold-filled (`#FFD700` interior, black outline) at ~0.7× the marker size used for data points, placed immediately to the left of the scenario name in any axis label, legend entry, or annotation:

- §4.2 — `o` (open circle, gold-filled)
- §4.3 — `^` (triangle, gold-filled)
- Leader-block — `s` (square, gold-filled)

The exploratory split_merge candidate gets a hollow diamond (`D`, no fill) instead of a gold-filled glyph, to mark "candidate, not confirmed."

### Shared-baseline handling

The eight byte-identical vanilla-boids conditions are handled differently by figure type:

- **Cross-sweep figures (figs 4 agreement heatmap, fig 6 surrogate null):** collapsed to a single `vanilla_baseline` row/entry. Caption explicitly enumerates the collapsed conditions in a footnote (5 at n=10: `jamming α=1.0`, `leader λ=0.0`, `milling μ=0.0`, `noise σ=0.05`, `split_merge none`; 3 at n=5 sensitivity-default: `w_sensitivity W40`, `alignment_rule_sensitivity mean`, `sensitivity ksg_kinematic`).
- **Per-sweep figures (figs 2, 3, 5):** the boundary-value condition (e.g., `α=1.0` in jamming) is plotted as itself, since it is part of that sweep's grid. Its identity as the vanilla baseline is footnoted (`†`) in the panel caption.
- **Primary figure (fig 1):** the `§4.3 row's col 2` panel shows the per-window Φ distribution at jamming α=1.0 and labels it "vanilla_baseline (= jamming α=1.0)" with `†`. Similarly for the `leader-block row's col 2` showing leadership λ=0.0 = vanilla.

### Figure dimensions and DPI

Inherit from `analysis/plotting.py` `configure_style()`: `font.size=12`, `figure.dpi=150`, `savefig.dpi=300`, `savefig.bbox="tight"`, `savefig.pad_inches=0.1`. Save both PDF (vector, primary deliverable) and PNG (raster, for embedding in markdown previews and the Tier 3.C internal report draft). Paper figure dimensions consistent with single-column journal width (~7 inches wide) for supplementary figures and double-column (~14 inches) for the primary figure.

---

## §1 — Figure 1 (PRIMARY): Three-mechanism cross-sweep panel

### Composition decision: Option II (mechanism-organized 3-row layout)

The original Phase5.md spec for figure 1 was a 3×4 grid with rows = `alignment`, `jamming`, `leadership` (perturbation-axis rows) and columns = `coherent-Φ-dist`, `disordered-Φ-dist`, `σ_u`, `phi_norm σ`. That spec was written assuming Tier 1.A would land Outcome 1 (compressibility-as-general-mechanism). Post-Outcome-4 plus the cross-sweep audit's two §4.2-instances finding, the row-by-perturbation-axis logic is empirically wrong for the headline picture: the three findings fall into three structurally distinct **mechanism families** (§4.2 transitional bimodality, §4.3 compressibility-Φ-inversion, leader-block partition), with §4.2 spanning two perturbation axes.

**Option I (Phase5.md preserved with leadership row reframed)** would force the leadership row's σ_u and phi_norm σ panels to do double duty — they're in the original spec because compressibility was the row's mechanism, but post-Outcome-4 those panels show the *failure* of compressibility, not its presence. Caption gymnastics. Reader has to mentally distinguish "this panel corroborates the row's mechanism" from "this panel disconfirms what the row's mechanism was supposed to be." Option I also doesn't accommodate the second §4.2 instance (`noise σ=0.2`), which the cross-sweep audit's verdict treats as a load-bearing finding (`dip p=7.6×10⁻⁶` — strongest in the audit; full mean-peak signature).

**Option III (4-row including noise as its own row)** preserves the perturbation-axis grouping but inflates to 16 panels and breaks the column semantics (the alignment row's col 1/2 endpoints `w_a=0.0` (cohesion-elevated MI, Φ=361) vs `w_a=1.2` (coherent, Φ=118) are not the same kind of "disordered-vs-coherent" pair as the noise row's σ=0.5 random vs σ=0.0 sync; they are not visually comparable across rows).

**Option II (mechanism-organized 3-row)** is what I'm choosing. Rows = `§4.2 transitional bimodality`, `§4.3 compressibility-Φ-inversion`, `leader-block partition`. Columns are parallel across rows but row-specific in semantics:

| Row | Col 1 | Col 2 | Col 3 | Col 4 |
|---|---|---|---|---|
| **§4.2** transitional bimodality | per-window Φ histogram at `noise σ=0.2` (instance #1) — annotate `dip p=7.6e-6, modes=2`; gold ○ "§4.2" | per-window Φ histogram at `alignment w_a=0.6` (instance #2) — annotate `dip p=0.102, modes=2`; gold ○ "§4.2" | Φ cross-seed mean across the **noise sweep** (σ ∈ {0.0, 0.05, 0.05†, 0.1, 0.2, 0.5}) with 95% CI band; arrow-annotation pointing to σ=0.2 peak above both endpoints | Φ cross-seed mean across the **alignment sweep** (w_a ∈ {0.0, 0.6, 1.2, 1.8}) with CI band; arrow-annotation pointing to w_a=0.6 transitional bimodality region |
| **§4.3** compressibility-Φ-inversion | per-window Φ histogram at `jamming α=0.2` (instance) — annotate `dip p=0.984, unimodal narrow`; gold ▲ "§4.3" | per-window Φ histogram at `vanilla_baseline (= jamming α=1.0†)` — annotate `dip p=0.914, unimodal`; † footnote | Φ cross-seed mean across the **jamming sweep** (α ∈ {0.2, 0.5, 1.0†}) with 95% CI band; bar-style or line; arrow-annotation: "+38.6% inversion above coherent baseline" | σ_u and phi_norm cross-seed σ across the jamming sweep (twin-y-axis OR two stacked sub-panels) — left axis σ_u showing floor-lock at α=0.2 (0.5925 above α=1.0's 0.5183); right axis phi_norm σ showing reduction (0.027 vs 0.091) |
| **Leader-block** partition | per-window Φ histogram at `leadership λ=2.4` (instance) — annotate `Φ=8.73, std/IQR=2.6 heavy-tailed`; gold ■ "leader-block" | per-window Φ histogram at `leadership λ=0.0 (= vanilla_baseline†)` — annotate `Φ=135.05`; † footnote | Φ cross-seed mean across the **leadership sweep** (λ ∈ {0.0†, 0.8, 1.6, 2.4}) with 95% CI band; arrow-annotation: "Φ collapse at λ≥1.6 — opposite direction from §4.3" | MI matrix at λ=2.4 (8×8 leader-block + 32×32 follower bulk visible) as a heatmap (cmap='viridis'); inset text "Fiedler ⟷ leader-membership = 1.000"; sub-axes of follower-bulk-only could be shown beneath if space permits |

**Headline message** (caption lead sentence): *Three mechanism families operate across the 3D Vicsek/Bailey swarm sweeps — §4.2 transitional bimodality at moderate alignment coupling and at moderate additive noise, §4.3 compressibility-Φ-inversion at high jamming severity, and a structurally distinct leader-block partition Φ collapse at high leadership weight; each family has its own load-bearing signature, and each is supported by within-window distribution evidence (cols 1–2), cross-condition Φ ordering (col 3), and a mechanism-specific descriptor (col 4).*

### Layout

- 3 rows × 4 columns. Total figure dimensions: ~14 in wide × ~10 in tall (double-column journal format). Each panel ~3 in × 3 in plotting area; row labels on far left.
- Shared y-axis within col 1 / col 2 of each row (Φ histogram densities can use shared scale per row but not across rows because Φ magnitudes differ by 20× across the leader-block row vs §4.2 row; renderer uses log-scale x for col 1+2 OR per-row independent x-axis with prominent x-tick labels).
- Row labels: "§4.2 transitional bimodality", "§4.3 compressibility-Φ-inversion", "leader-block partition Φ collapse".
- Column headers (above row 1 only): "instance distribution", "comparator distribution", "Φ across axis", "mechanism signature".
- Mechanism-family glyph (gold ○ / ▲ / ■) appears once per row, large, immediately left of the row label, doubling as a legend tab.
- Caption directly under the figure includes per-row sub-headlines:
  - §4.2: "*Two instances confirmed; cross-axis verification of B&S §4.2.*"
  - §4.3: "*One instance confirmed at jamming α=0.2; +38.6% mean Φ inversion above coherent baseline.*"
  - leader-block: "*Φ ordering matches Outcome 4 prediction direction; mechanism diagnostic shows block-structured MI matrix, not the uniformly-elevated A2 §4.3 signature.*"

### Data sources

| Panel | Source files |
|---|---|
| §4.2 row col 1 | `outputs/noise_sweep/sigma_0.2/seed*/*.parquet` per-window phi_spectral; pooled across 10 seeds, steady-state windows only (`window_idx ≥ quantile(2/3)`, ~310 windows) |
| §4.2 row col 2 | `outputs/alignment_sweep/wa_0.6/seed*/*.parquet`, same pooling |
| §4.2 row col 3 | `outputs/comparison/cross_sweep/scenario_summary.csv` rows for `noise_sweep` × `{sigma_0.0, sigma_0.05, sigma_0.1, sigma_0.2, sigma_0.5}`; phi_xseed_mean + phi_xseed_ci_lo/hi |
| §4.2 row col 4 | same scenario_summary.csv but `alignment_sweep` × `{wa_0.0, wa_0.6, wa_1.2, wa_1.8}` |
| §4.3 row col 1 | `outputs/jamming_sweep/alpha_0.2/seed*/*.parquet` |
| §4.3 row col 2 | `outputs/jamming_sweep/alpha_1.0/seed*/*.parquet` (= vanilla_baseline parquets) |
| §4.3 row col 3 | scenario_summary.csv rows for `jamming_sweep` × `{alpha_0.2, alpha_0.5, alpha_1.0}` |
| §4.3 row col 4 | scenario_summary.csv `sigma_u_xseed_mean` and `phi_norm_xseed_sigma` for the same three jamming conditions |
| Leader-block row col 1 | `outputs/leadership_sweep/lambda_2.4/seed*/*.parquet` |
| Leader-block row col 2 | `outputs/leadership_sweep/lambda_0.0/seed*/*.parquet` (= vanilla_baseline parquets) |
| Leader-block row col 3 | scenario_summary.csv rows for `leadership_sweep` × `{lambda_0.0, lambda_0.8, lambda_1.6, lambda_2.4}` |
| Leader-block row col 4 | `outputs/tier1_compressibility/mechanism_diagnostic.npz` (MI matrix at λ=2.4 representative window) |

### Open questions for the renderer

- **Histogram bin choice for cols 1+2:** number of bins per panel (suggestion: Freedman–Diaconis on the pooled-310-window data per condition) and whether to overlay a KDE curve. The bimodality dip-test result is the load-bearing signal — visual histogram should make the modes visually obvious. If FD bins look chunky on `dip p=7.6e-6` data, prefer narrower bins; if they look noisy on `dip p=0.984` (jamming α=0.2), prefer wider bins.
- **Axis sharing** within row 1 cols 1+2 (both §4.2 instances): whether to force a shared x-axis (Φ range) — `noise σ=0.2` has Φ in [50, 250], `alignment w_a=0.6` has Φ in [50, 250] roughly (mean=139). A shared range would help visual comparison of the two instances. Renderer's call.
- **Col 4 layout for leader-block row:** MI matrix at λ=2.4 is 40×40 (10-agent placeholder × ... actually the 3D model has N=40 agents, so 40×40 MI matrix). Renderer should re-confirm matrix dimensions from `mechanism_diagnostic.npz`. The matrix may need to be re-ordered so the 8 leaders are first; the block structure becomes visually obvious as a high-MI 8×8 block in the upper-left.
- **Whether to include the §4.3 row's col 4 phi_norm σ on the same panel as σ_u**: twin-y-axis is fine if labels are clean; otherwise render as two stacked mini-panels within col 4.
- **Whether row 3 col 4 should also include MI matrix at λ=0.0** for visual contrast (would convert col 4 into a 1×2 mini-grid showing block-structure-vs-uniform). Could be done if space allows; otherwise the λ=2.4 matrix alone with caption-text-mention of the λ=0.0 contrast is sufficient.

---

## §2 — Figure 2: Time-series overlays per scenario

### Layout

Per Phase5.md spec: per-scenario, three-panel time series with shared time axis. Spectral metrics on top axis, TDA (including H2) on middle axis, classical on bottom axis.

Five scenarios with annotated event windows or interpretive markers:

1. `none` (vanilla baseline) — no events; reference.
2. `jamming α=0.2` — jam interval [200, 400] step shaded vertically.
3. `split_merge none` (= vanilla; skip; redundant with #1) → instead use `split_merge split_merge` (the actual event scenario) — split [200, 300] and merge [300, 400] shaded with two distinct light shades.
4. `alignment w_a=0.6` (the §4.2 instance) — no event; annotate "transitional regime, bimodal per-window Φ".
5. `noise σ=0.2` (the §4.2 instance) — no event; annotate "transitional noise, peak Φ, dip p=7.6e-6".
6. `leadership λ=2.4` (Outcome 4) — no event; annotate "leader-block partition, Φ=8.73 << baseline".
7. `milling μ=0.8` — no event; annotate "rotational coherence".
8. `jamming α=1.0` (= vanilla_baseline) — included as an explicit comparator for `jamming α=0.2`; can be plotted as a thin gray line behind the α=0.2 curve in scenario #2 panel rather than as its own row.

So the figure ends up as **6 sub-figures in a vertical stack** (one per scenario, three panels each), or rendered as 6 separate PDFs since per-scenario time-series is already the convention in `outputs/figures/<sweep>/timeseries_<sweep>_<condition>.{pdf,png}`. The renderer should pick whichever format fits the report layout — separate PDFs are easier for the report draft; a single stacked figure is harder to read but cohesive.

**Recommendation:** keep them as **6 separate figures** (one per scenario), filenames `timeseries_<scenario_label>_3panel.{pdf,png}`. Tier 3.C report's Methods section can include 1-2 representative ones (probably `jamming α=0.2` and `noise σ=0.2` as the §4.3 and §4.2 instances) inline, with the rest in supplementary.

### Headline message (per-scenario; caption lead sentence)

- jamming α=0.2: *Φ_spectral elevation visible during the jam interval [200, 400] aligns with TDA snap_TP_1 spike and polarization drop — the §4.3 inversion timing.*
- noise σ=0.2: *Φ_spectral and snap_TP_1 oscillate together at moderate noise; bimodal per-window Φ visible as alternating high/low windows on the spectral panel.*
- alignment w_a=0.6: *Transitional alignment — Φ_spectral fluctuates window-to-window between high (turning) and low (steady-flight) modes; polarization is moderate steady.*
- leadership λ=2.4: *Φ_spectral collapsed (~5–10 window-to-window) — leader-block partition; polarization is moderate (~0.6) — the swarm is coordinated but Φ_spectral is suppressed by the partition geometry.*
- milling μ=0.8: *Φ_spectral elevated rotational regime; angular_momentum_norm distinct from non-milling scenarios.*
- split_merge: *Coordinated flock dissolves during split [200, 300]; reassembly visible during merge [300, 400]; Φ drops below the surrogate null during the dissolution interval — exploratory candidate for compressibility-via-dissolution.*

### Data sources

- `outputs/<sweep>/<condition>/seed*/*.parquet` — per-step time series, seed-averaged before plotting (existing legacy figs use seed-averaged; preserve that).
- For event annotations: `scripts/run_sweep.py` config files specify the event windows (jam_start/end, split/merge timings).

### Open questions for the renderer

- **Whether to plot all seeds as light traces with the seed-mean as a heavy line**, or just the seed-mean with a CI band. Existing 2D-mirror legacy figs use seed-mean only. Recommendation: seed-mean + CI band (1.96 × seed-std/√N) for consistency with cross-seed CIs elsewhere.
- **Whether to include the H2 metrics by default** or as an opt-in second variant. Phase5.md spec emphasizes H2 as a 3D-specific addition; default to including all three TDA dimensions on the middle panel. If H2 is empirically uninformative for some scenarios, the renderer can drop it and note in caption.

---

## §3 — Figure 3: Sensitivity bar charts per sweep

### Layout

Per Phase5.md spec: η² with bootstrap 95% CIs as horizontal bar charts per sweep. KSG estimator (primary). Histogram NOT plotted (sign-only per D11). Gaussian estimator as cross-validation, secondary panel.

11 sweeps × 1 figure each = 11 figures, named `sensitivity_<sweep>.{pdf,png}`. These already exist on disk under `outputs/figures/<sweep>/` from Tier 2.C; the composition session is mostly reaffirming the legacy convention with a few annotations added.

**Per-figure structure:**

- Horizontal bars, one per metric (Φ_spectral, polarization, σ_u, snap_TP_0/1/2, snap_MP_0/1/2, snap_B_base_0/1/2, traj_TP_0/1/2, traj_MP_0/1/2, traj_B_base_0/1/2, angular_momentum_norm) — typically ~16 bars per sweep.
- Bar color = sweep family color (per §0).
- η² value on x-axis with 95% CI error bars (right-side cap for bootstrap CI upper bound).
- Spectral metric (Φ_spectral) bar gets a gold ○/▲/■ glyph if the sweep contains a §4.2/§4.3/leader-block instance.
- Histogram η²: rendered as faint *gray dashed* bars stacked at the bottom (sign-only — interpretation as "presence of any direction-of-effect, not magnitude"). Caption explicitly states sign-only per D11.

### Headline message

*Per-sweep effect-size (η²) ranking of metrics. KSG primary; Gaussian as cross-estimator validation. Sweeps containing §4.2/§4.3/leader-block instances are flagged on Φ_spectral.*

### Data sources

- `outputs/comparison/<sweep>/eta_squared.csv` — per-sweep, per-metric η² with bootstrap CIs.
- `outputs/tables/sensitivity_<sweep>.csv` — same data, alternate format.

### Open questions for the renderer

- **Sort order for bars**: by η² descending (clearest empirical reading) vs. by metric family (Spectral / TDA / Classical, then by metric within family). Legacy 2D figs use η² descending — recommend preserving that, with a horizontal divider where sub-categories change rank order. Renderer's call after seeing first version.

---

## §4 — Figure 4: Agreement/divergence heatmap (Bailey 2026 hypothesis test)

### Layout

Per Phase5.md spec: Spearman correlation matrix between metric families across all sweep × condition combinations. H2 columns explicitly included.

The data file `outputs/comparison/cross_sweep/scenario_agreement_spearman.csv` is wide: rows = scenario (sweep × condition, 38 of them after vanilla collapse), columns = 18 TDA metrics (snap_TP_0/1/2, snap_MP_0/1/2, snap_B_base_0/1/2, traj_TP_0/1/2, traj_MP_0/1/2, traj_B_base_0/1/2). Each cell is the Spearman ρ of that scenario's per-window TDA metric series against per-window Φ_spectral.

**Render as a heatmap:**

- 38 rows × 18 columns. Row labels: scenario name with sweep-family color tag. Column labels: TDA metric name with H0/H1/H2 marker glyph (per §0).
- Cell color: `RdBu_r` cmap, vmin=−1, vmax=+1. Same convention as `analysis/plotting.py:plot_agreement_heatmap`.
- Colorbar on right with "Spearman ρ (TDA vs Φ_spectral)" label.
- Annotate cells where |ρ| > 0.5 with the value (white text on dark background, black on light).
- Mark the `vanilla_baseline` row distinctively (dashed border or thicker outline) — caption footnotes the 8-condition collapse.
- Mark §4.2/§4.3/leader-block rows with their gold glyph next to row label.
- Mark the exploratory split_merge §4.3 candidate with hollow ◇ next to row label and "(exploratory)" footnote.
- H2 column block visually emphasized (e.g., subtle background shading on the H2 column triplet) per Phase5.md's framing as a 3D-specific addition.

### Headline message

*Spearman correlation between Φ_spectral and 18 TDA persistence metrics across all 38 scenarios (sweep × condition, vanilla-baseline collapsed). Strong positive correlation = spectral and topological metrics agree; near-zero or negative = they diverge. The Bailey 2026 core hypothesis predicts agreement in coherent regimes and divergence in regimes where higher-dimensional persistence captures dynamics not visible to spectral measures (the "when do they diverge?" finding).*

### Data sources

- `outputs/comparison/cross_sweep/scenario_agreement_spearman.csv` — 38 rows × 18 metric columns.

### Open questions for the renderer

- **Row sort order**: alphabetical by sweep + condition (legacy default), OR clustered by similarity (hierarchical clustering on the 18-column row vectors). Clustering may surface block structure (groups of scenarios that have similar agreement patterns); if it does, use clustered order — that's the empirical reading. If no clear blocks emerge, use alphabetical for predictable navigation.
- **Whether to compute additional pairwise agreements** (e.g., classical-vs-spectral, classical-vs-TDA) and stack them as side-by-side heatmaps. Phase5.md's spec emphasizes "across metric families"; adding a 2nd heatmap (Classical-vs-Spectral) and a 3rd (Classical-vs-TDA) would broaden the figure to a 1×3 or 2×2 panel. Recommend keeping it as Spectral-vs-TDA only for fig 4 (the headline divergence figure), and rendering the other agreements as supplementary fig 4b if the renderer wants. Renderer's call.

---

## §5 — Figure 5: Matched-control deltas

### Layout

Per Phase5.md spec: pre/during/post bar charts per metric for event sweeps (jamming, split_merge). The legacy 2D-mirror figures `deltas_<sweep>.{pdf,png}` already exist for these sweeps under `outputs/figures/<sweep>/`.

**Composition for jamming sweep:** 3-panel grid (pre [0, 200], during [200, 400], post [400, 1000]) × multiple metrics on x-axis, bar height = per-metric mean during that interval. Comparator: same metric in the matched control (jamming α=1.0 = vanilla baseline). Delta = perturbed − control; bar height represents the delta with bootstrap 95% CI.

**Composition for split_merge sweep:** similar 3-panel grid with split [200, 300] and merge [300, 400] periods.

Two figures total: `deltas_jamming_event.{pdf,png}` and `deltas_split_merge_event.{pdf,png}`.

### Headline message

- Jamming: *During the jam interval [200, 400], Φ_spectral, σ_u, and snap_TP_1 elevate above the matched control; polarization drops. The §4.3 compressibility signature is visible in the during-jam window, including the predicted MI elevation despite the disordered geometry.*
- Split_merge: *During the split interval [200, 300], Φ_spectral drops below both the pre-event level and the matched control. This is the only interval in the entire dataset where Φ falls below null (z=−5.08 in the surrogate test); flagged as exploratory §4.3 candidate, mechanism distinct from jamming compressibility.*

### Data sources

- `outputs/comparison/jamming_sweep/matched_control_deltas.csv`
- `outputs/comparison/split_merge_sweep/matched_control_deltas.csv`

### Open questions for the renderer

- **Whether to overlay seed-individual deltas as light dots** behind the bar mean. Recommend yes — provides the per-seed spread visually and signals N=10.
- **Whether to break out the split_merge sweep into split-only and merge-only sub-panels**. The two events have distinct dynamics (dissolution vs reassembly); plotting split [200, 300] and merge [300, 400] separately would surface that. Recommend yes.

---

## §6 — Figure 6: Surrogate null comparison

### Layout

Observed Φ_spectral vs surrogate null distribution per scenario, with z-scores. 8 science scenarios + 2 method-validation control scenarios = 10 entries.

**Recommended layout: vertical bar chart with paired observed/surrogate bars per scenario.**

- y-axis: scenario name (10 entries: 8 science + disabled_interaction + synthetic_iid).
- x-axis: Φ_spectral value.
- Per scenario, two bars side-by-side: light-color bar = surrogate mean (with error bar = 95% CI); dark-color bar = observed Φ.
- Color = sweep family color per §0; for `none` use vanilla_baseline gray.
- Z-score annotation on right of each bar pair.
- **Boundary-synchrony floor** (z=3.12): horizontal dashed gray line in z-score panel (if a separate z-score sub-panel is included), with text label. Alternatively, render the bar pairs in two sub-panels: top sub-panel = Φ values per scenario; bottom sub-panel = z-scores as a separate horizontal bar chart with the z=3.12 line.
- **Exploratory split_merge** (z=−5.08, observed below surrogate): rendered with the bar bordered in a different style (dashed) and labeled "(exploratory: single-seed, below null)".
- **Synthetic_iid** (z=−0.53) and **disabled_interaction** (z=3.12, the floor itself): rendered with a distinguishing style (e.g., light striped background) labeled "method-validation control".

### Headline message

*The circular-shift surrogate null is method-validated by the synthetic AR(1) i.i.d. control (z=−0.53, within surrogate 95% CI). Eight science scenarios all show observed Φ above the surrogate null at z ≥ 8.38 (well above the z=3.12 boundary-synchrony floor from disabled-interaction control), with one exception: split_merge during its event window shows observed below the null at z=−5.08 — an exploratory compressibility-direction candidate from a single seed. The strongest above-null result is `noise σ=0.2` at z=32.92, corroborating the §4.2 transitional-peak finding at the surrogate level.*

### Data sources

- `outputs/surrogates/<scenario>_null.csv` per scenario.
- `outputs/surrogates/README_summary.md` summary table (already in the format needed).

### Open questions for the renderer

- **Whether to render observed and surrogate as bars** vs **observed as a point with surrogate as a CI box**. Bars are more standard for null-comparison figures; recommend bars.
- **Z-score sub-panel inclusion**: whether to put z-scores in a side bar chart (right sub-panel) or as numerical annotations only on the main bars. Recommend a side bar chart — z is the load-bearing inferential quantity, deserves its own visual.

---

## §7 — Figure 7: Monitoring ROC

### Layout

Per Phase5.md spec: per-metric AUC for detecting perturbation onset, combined across event sweeps (jamming + split_merge). Single horizontal bar chart, one bar per metric.

- y-axis: metric name (Spectral / TDA / Classical), grouped by family with row separators.
- x-axis: AUC (0.5 = chance, 1.0 = perfect detection).
- Bar color: family color (Spectral = darker tint of vanilla; TDA = green-blue gradient by H0/H1/H2; Classical = orange tint).
- Marker glyph per family (per §0).
- Vertical reference line at AUC=0.5 (chance).
- Top-N=5 metrics annotated with AUC value to right of bar.
- Sort by AUC descending.

Existing legacy figs at `outputs/comparison/cross_sweep/monitoring_roc.png` may already render this (the `monitoring_roc.csv` is the data source) — renderer should check the existing figure as a starting point.

### Headline message

*Per-metric AUC for detecting jamming and split-merge event onset, combined across the two event sweeps. The top metrics for monitoring perturbation onset are <to be determined by the data; likely traj_TP_0 and snap_MP_0 based on monitoring_roc.csv top-5>; Φ_spectral itself is in the upper-mid range, validating its monitoring utility while showing it is not the strongest single onset detector.*

### Data sources

- `outputs/comparison/cross_sweep/monitoring_roc.csv` — 155 rows: (sweep, condition, metric, auc).

### Open questions for the renderer

- **Whether to break out per-event-sweep AUCs** alongside the combined. Phase5.md says "combined"; legacy fig may already do this. If both are useful (separate jamming and split-merge AUC per metric), render as a 1×2 sub-panel.
- **Number of metrics shown**: 18+ metrics is a lot of bars. If the figure becomes too tall, consider showing only top-10 with "rest in supplementary" annotation. Recommend top-10 for primary (or supplementary placement) version, full 18 in supplementary if needed.

---

## §8 — Figure 8: 3D scenario snapshots

### Layout

Per Phase5.md spec: `plot_snapshot_3d` output for each of 5 scenarios at a representative steady-state step, Fiedler-partition colored.

5 scenarios as a 1×5 grid (or 2×3 with one cell blank if 1×5 is too wide):

1. `none` (= vanilla_baseline) — coherent flock, agents coloured by Fiedler bipartition.
2. `alignment w_a=0.6` — transitional regime; bimodal-Φ window snapshot.
3. `jamming α=0.2` — during jam interval; agents wobbling but coherent positions.
4. `split_merge split_merge` — during split [200, 300]; flock dissolved into two clusters.
5. `milling μ=0.8` — rotational steady-state.

Or include 6 scenarios as 2×3, adding `leadership λ=2.4` to show the leader-block partition geometry: leaders clustered tightly, followers spread.

**Per-snapshot:**

- 3D scatter plot with `mpl_toolkits.mplot3d`.
- Agents as filled spheres, colored by Fiedler bipartition (2 classes; e.g., red vs blue).
- For `leadership λ=2.4`: leaders rendered in larger size or different marker (e.g., star) so the 8-leader cluster is visible.
- Axis box at the 50³ container dimensions (axis limits 0–50 on x, y, z).
- View angle (elev, azim): pick one that shows depth structure clearly per scenario; renderer should iterate. Suggestion: elev=20, azim=45 as default.
- Subtitle per snapshot: scenario name + step number + Φ_spectral at that window.
- Caption explains Fiedler bipartition and notes the leader-cluster visibility for `leadership λ=2.4`.

### Headline message

*3D scatter snapshots of each scenario at a representative steady-state window, colored by Fiedler bipartition of the per-window MI matrix. The Fiedler partition aligns with leader-membership at leadership λ=2.4 (illustrating the leader-block partition mechanism), reflects geometric proximity in coherent and milling regimes, and is at chance for compressibility (jamming α=0.2) and transitional (alignment w_a=0.6) regimes.*

### Data sources

- `outputs/<sweep>/<condition>/seed0/*.parquet` per scenario — pick the steady-state window whose Φ_spectral is closest to the per-seed steady-state mean (consistency with `mechanism_diagnostic.npz`'s window selection in Tier 1.A).
- For per-step agent positions: derived from telemetry CSV stored alongside parquets, OR re-run from scenario configuration using the deterministic D6 seeding (snapshot only, no re-analysis).

### Open questions for the renderer

- **Seed and window selection per scenario:** Tier 1.A's selection rule (seed whose per-seed steady-state Φ is closest to cross-seed median; window whose Φ is closest to that seed's mean) gives good representative snapshots. Use the same rule for all 5 (or 6) scenarios.
- **View angle per scenario:** may differ. Renderer should iterate after first version.
- **Whether to render with axes box or "clean" no-axes mode:** axes box provides scale; clean mode is more visually striking. Recommend axes box for the science figure; clean for any cover-image variant.

---

## §9 — Primary vs supplementary classification

### Primary figures (4 figures, ~12–15 minutes of reader time at the Discussion stage)

1. **Figure 1 — Three-mechanism cross-sweep panel.** The headline empirical contribution. Communicates the §4.2 (×2 instances) + §4.3 (×1 instance) + leader-block (Outcome 4 disconfirmation as result) story in one image. Without this figure the reader has to assemble the three mechanisms from disparate sub-figures.
2. **Figure 4 — Agreement/divergence heatmap.** The Bailey 2026 core hypothesis test ("when do spectral and topological metrics agree vs diverge?"). H2 columns are 3D-specific. Cross-sweep view essential.
3. **Figure 6 — Surrogate null comparison.** The method-validation figure. Without it the cross-agent integration claims are not defensible. Includes the explicit boundary-synchrony floor annotation, which is a methodological item that the report's Methods section refers to.
4. **Figure 8 — 3D scenario snapshots.** Visual primer for the swarm dynamics, especially the leader-block partition geometry. Without a visual, "leader-block partition" reads as an abstract mechanism; the snapshot makes it tangible.

### Supplementary figures (4 figures, appendix or supplementary materials)

1. **Figure 2 — Time-series overlays per scenario.** 6 scenarios × 3 panels each = 18 panels of detail. Important for verification and audit but not narrative-load-bearing for the headline. The Tier 3.C report's Methods section can include 1–2 representative ones inline (e.g., `jamming α=0.2` and `noise σ=0.2`); the rest go in supplementary.
2. **Figure 3 — Sensitivity bar charts per sweep.** 11 separate figures. Per-sweep η² is verification-grade detail; the cross-sweep ranking is more efficiently communicated by a single ranked table in the text.
3. **Figure 5 — Matched-control deltas.** Two figures (jamming, split_merge). Pre/during/post is detail-level; the headline (jamming compressibility direction; split_merge below-null exploratory) is captured in fig 1 and fig 6 respectively. Fig 5 provides the audit trail.
4. **Figure 7 — Monitoring ROC.** Per-metric AUC ranking is a "which metric to monitor in production" finding — important for downstream applications but secondary to the §4.2/§4.3 narrative. Supplementary placement keeps the report focused.

### Justification

The post-Outcome-4 narrative is "three mechanism families across orthogonal perturbation axes, with one pre-registered extension tested-and-disconfirmed." The primary figures make that claim and provide its methodological warrant (fig 1 = claim, fig 4 = where the spectral/TDA agreement holds, fig 6 = method validation, fig 8 = visual context). The supplementary figures provide audit-grade detail for any reader who wants to verify a sub-claim or re-rank metrics for a different downstream purpose. Splitting 4 + 4 keeps the body of the report focused without sacrificing reproducibility.

---

## §10 — Renderer handoff notes (for the next Sonnet session)

### Render order

1. **Figure 1 first.** It sets the design vocabulary (color palette tested, mechanism-glyph rendering tested, gold-fill annotation tested, †/‡ footnote tested, multi-row caption layout tested). Get fig 1 right before continuing.
2. **Figure 4 second.** The 38×18 heatmap is the second-largest visual; row clustering vs alphabetical decision (open question above) should be made early because it affects the visual reading.
3. **Figure 6 third.** Surrogate comparison; relatively self-contained; renders fast.
4. **Figure 8 fourth.** 3D snapshots take iteration on view angles. Allow time.
5. **Figures 2, 3, 5, 7** (supplementary) last. These can borrow heavily from existing legacy 2D-mirror figures already at `outputs/figures/<sweep>/`. Light edits: add §4.2/§4.3/leader-block glyphs; add †/‡ footnotes; ensure color palette consistency. Most of the rendering work here is verification, not new design.

### Iteration likelihood

- **Figure 1** — high. The col 4 layout for the leader-block row (MI matrix vs Fiedler-correspondence inset) is the most uncertain panel; first render will likely need adjustment. The §4.2 row shared-x-axis decision (cols 1+2) needs visual confirmation before locking in. Caption sub-headlines may need wordsmithing per row.
- **Figure 4** — medium. Row clustering decision after seeing the first version.
- **Figure 6** — low. Standard bar chart; existing data is clean.
- **Figure 8** — high. View angles per scenario may all need adjustment after first render.

### Library / version requirements

- matplotlib 3.x, numpy, pandas, scipy — all already in the project's lock file.
- For fig 8 (3D): `mpl_toolkits.mplot3d.Axes3D`. Existing in stdlib matplotlib.
- For animations (Tier 3.B, separate session): ffmpeg writer; not needed for Tier 3.A.
- Existing `analysis/plotting.py` provides `configure_style`, `_save`, `plot_time_series`, `plot_sensitivity_bars`, `plot_agreement_heatmap`, `plot_control_deltas`, `plot_monitoring_auc`. The renderer should extend that file with new functions for fig 1 (`plot_three_mechanism_panel` or similar) and for fig 8 (`plot_snapshot_3d`); figs 2, 3, 4, 5, 7 use existing functions (light extension for the new annotations).

### Output paths

- All Tier 3.A figures output to **`outputs/figures/composition/`** (new subdirectory). This separates the curated Tier 3.A composed figures from the legacy 2D-mirror per-sweep figures already at `outputs/figures/<sweep>/` (which were generated by Tier 2.C and are still useful as audit-grade detail but are not the curated publication set).
- Save both PDF (vector, primary) and PNG (raster, for markdown previews) per existing `_save` convention.
- Filenames:
  - `fig1_three_mechanism_panel.{pdf,png}`
  - `fig2_timeseries_<scenario>.{pdf,png}` (per scenario)
  - `fig3_sensitivity_<sweep>.{pdf,png}` (per sweep) — or symlink/copy from existing legacy `outputs/figures/<sweep>/sensitivity_<sweep>.{pdf,png}` after annotation pass
  - `fig4_agreement_heatmap.{pdf,png}`
  - `fig5_deltas_<event>.{pdf,png}` (jamming, split_merge)
  - `fig6_surrogate_null.{pdf,png}`
  - `fig7_monitoring_roc.{pdf,png}`
  - `fig8_snapshots_3d.{pdf,png}`

### Renderer responsibilities NOT specified here

- Exact bin counts for histograms (FD recommended, but renderer adjusts after first render).
- Exact font sizes within panels (use `analysis/plotting.py:configure_style` defaults; tweak only if labels overlap).
- Exact tick spacing on shared axes.
- Whether to include gridlines on time-series panels (legacy 2D figs use no grid; preserve unless the renderer sees a readability issue).

The renderer has full latitude within the design framework set above. Re-run iteration after seeing first versions is expected and budgeted.

---

## Appendix — Open questions for planning-level discussion (NOT renderer's responsibility)

These surfaced during composition; flagging here per the prompt's "do not modify Phase5.md, but flag conflicts" instruction. Not blocking for the renderer session.

1. **Phase5.md's figure 1 spec is empirically obsolete.** The 3×4 grid with rows=alignment/jamming/leadership and cols=coherent-Φ-dist/disordered-Φ-dist/σ_u/phi_norm σ was written for Outcome 1. Post-Outcome-4 the row-by-perturbation-axis logic is wrong because §4.2 spans two axes (alignment + noise) and the leadership row is now showing a *different* mechanism than the one its column structure was designed for. This composition session chose the mechanism-organized 3-row layout (Option II) instead — flagged here in case the planning document wants to record that the original spec is superseded.
2. **Phase5.md figure 1 also doesn't anticipate the noise sweep's role.** The cross-sweep audit elevated `noise σ=0.2` to a confirmed §4.2 instance; Phase5.md figure 1's row structure doesn't include noise. If the plan is updated, the recommendation is to replace the figure 1 spec with the Option II layout above (mechanism rows; noise σ=0.2 in §4.2 row col 1).
3. **The surrogate set tested in Tier 2.B does not include alignment w_a=0.6.** It includes alignment w_a=1.8 instead. If a §4.2 surrogate test on `alignment w_a=0.6` would corroborate the bimodality finding (analogous to the noise σ=0.2 z=32.92 result), that's a small additional Tier 2.B run worth flagging — but it is a Tier 2.B add, not a Tier 3.A composition decision.
4. **The Fig 1 leader-block row col 4 (MI matrix at λ=2.4) requires a representative seed/window.** Tier 1.A used seed 0 window 89; that's the canonical choice. The renderer should reuse it. If the user wants a different representative (e.g., to illustrate the partition stability across seeds), that's a Tier 1.A re-extraction, not a Tier 3.A composition decision.
5. **Phase5.md figure 8 (3D scenario snapshots) lists "5 scenarios"; this composition recommends 6 (adding leadership λ=2.4) for the leader-block partition visualization.** If keeping it strictly to 5 per the plan, drop `none` (vanilla baseline) since it's the least informative — but having vanilla as a reference is useful. Recommend 6; flag here as a deviation from the literal Phase5.md spec.

These items are notes; they do not affect the renderer's work. They go in the Tier 3.C report's "Notes on plan deviations" section if one is included.

---

## Stop point

This document is the deliverable of Tier 3.A. The next session (Sonnet) renders the figures from this composition. Tier 3.B (animations) and Tier 3.C (internal report draft) are out of scope for this session.
