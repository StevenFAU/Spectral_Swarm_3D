# Render Notes — Phase 5 Tier 3.A

**Session:** Sonnet 4.6, 2026-05-07.
**Composition plan commit:** b981317.

## Decisions beyond composition plan

### Figure 1 — axis scaling and histograms (iteration performed)

**Iteration required:** FD (Freedman-Diaconis) binning produced only 8 bins for the §4.2
bimodal distributions (noise σ=0.2: IQR ≈ 160 due to two widely-separated modes → FD bin
width ≈ 45). The composition plan explicitly anticipated this: "if FD bins look chunky, prefer
narrower bins." Fixed by applying min_bins=30 floor (bin width ≈ 12, adequate to reveal modal
structure). The §4.3 and leader-block rows were not affected (unimodal/log distributions).

- §4.2 row cols 1+2: shared linear x-axis (both noise σ=0.2 and alignment w_a=0.6 have Φ
  in [50, 250] range — shared range enables direct comparison). Bins: min_bins=30 applied.
- §4.3 row cols 1+2: shared linear x-axis. Jamming α=0.2 and vanilla baseline share
  overlapping Φ range.
- Leader-block row col 1 (λ=2.4): log x-axis applied (Φ range ~2–40, ratio >> 10).
- Leader-block row col 2 (λ=0.0): linear x-axis (Φ range ~60–250).
- Leader-block row col 3 (trajectory): log y-axis applied (λ=0 Φ≈135 vs λ=1.6 Φ≈7,
  ratio ≈ 19 > 10 threshold).
- Col 4 §4.3 row: twin-y-axis for σ_u (left) and φ_norm σ (right), with alpha_1.0
  (vanilla) values sourced from scenario_summary.csv 'multiple/vanilla_baseline' row
  (sigma_u=0.5183, phi_norm_sigma=0.079; plan cited 0.091 which was approximate).
- Col 4 leader-block row: single MI matrix at λ=2.4 with leaders first (not 1×2 mini-grid
  with λ=0 comparison), to fit panel size budget. Caption references λ=0 contrast in text.

### Figure 4 — row sort order

Hierarchical clustering (Ward linkage on 18-column Spearman-ρ row vectors) chosen over
alphabetical because the Ward dendrogram revealed a moderate block structure separating
high-|ρ| coherent scenarios from near-zero/mixed scenarios. See figure for cluster groupings.

### Figure 8 — position data and Fiedler partition

- Leadership λ=2.4 and λ=0.0 (used for "none/vanilla" panel): exact positions and Fiedler
  partition from mechanism_diagnostic.npz (Tier 1.A canonical windows).
- Other 4 scenarios (alignment wa_0.6, jamming α=0.2, split_merge, milling μ=0.8): positions
  obtained by briefly re-running BoidSwarmModel3D to the representative window (composition
  plan §8 "re-run from scenario configuration using the deterministic D6 seeding, snapshot
  only, no re-analysis"). Fiedler partition for these scenarios uses k-means(k=2) spatial
  proxy — consistent with the caption's statement that "Fiedler partition reflects geometric
  proximity in coherent and milling regimes."
- For jamming α=0.2: window selected during event interval [200, 400] as specified in plan.
- For split_merge: window selected during split interval [200, 300] as specified in plan.

### Figure 2 — time series

- Seed-mean + 1.96 × std / √N CI band (normal approximation, not bootstrap) — adequate
  for visualization given N=10 seeds and the supplementary purpose of this figure.
- H2 TDA metrics included on middle panel (snap_TP_2, traj_TP_2) per 3D-specific emphasis
  in Phase5.md.

### Figure 3 — sensitivity

- Bars sorted by η² descending (legacy convention per 2D-mirror figures).
- η² bootstrap CIs shown where ci_lo/ci_hi available in eta_squared.csv.

### Surrogate z-score drift

- The plan noted "z=32.91 / z=32.92" for alignment_wa_0.6 / noise_sigma_0.2. Actual values
  from README_summary.md are z=32.91 and z=32.92 — consistent. The plan also cited
  phi_norm σ at α=1.0 as 0.091; actual data shows 0.079338 (from vanilla_baseline row).
  Used actual data throughout; plan values were rounded.

## Column drift between plan and actual data

- scenario_summary.csv: does NOT include per-sweep vanilla-baseline conditions as individual
  rows (alpha_1.0, lambda_0.0, sigma_0.05 etc.); they appear only as row 37
  (sweep='multiple', condition='vanilla_baseline'). The σ_u and φ_norm σ for vanilla
  baseline sourced from this consolidated row.
- scenario_agreement_spearman.csv: condition column format is "sweep/condition" not plain
  "condition" — handled in figure 4 label extraction.
- cross_seed_summary.csv: uses 'phi_spectral_mean'/'phi_spectral_std' not
  'phi_xseed_mean'/'phi_xseed_ci_lo/hi'. Bootstrap CIs approximated from std + N.

## New functions added to plotting.py

- `plot_snapshot_3d`: implemented inline in render script (not yet extracted to plotting.py).
  See figure 8 section.
- `plot_three_mechanism_panel`: implemented inline in render script.
- These should be extracted to plotting.py in a follow-up cleanup session.

## Anomalies

- noise_sweep/sigma_0.05 is the vanilla baseline; phi_spectral_mean = 135.0 in
  cross_seed_summary, matching vanilla_baseline row in scenario_summary. Plotted with †.
- milling_sweep/mu_0.0 also appears in the directory but is the vanilla baseline; not
  plotted as a separate milling condition.
- Figure 8 simulator runs for 4 scenarios add ~30–90 seconds of rendering time; this is
  expected and within the "snapshot only, no re-analysis" scope.
