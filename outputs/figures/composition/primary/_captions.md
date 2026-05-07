# Primary Figure Captions — Phase 5 Tier 3.A

## Figure 1 — Three-mechanism cross-sweep panel

Three mechanism families operate across the 3D Vicsek/Bailey swarm sweeps — §4.2 transitional
bimodality at moderate alignment coupling and at moderate additive noise, §4.3
compressibility-Φ-inversion at high jamming severity, and a structurally distinct leader-block
partition Φ collapse at high leadership weight; each family has its own load-bearing signature,
supported by within-window distribution evidence (cols 1–2), cross-condition Φ ordering (col 3),
and a mechanism-specific descriptor (col 4).

**Row 1 — §4.2 transitional bimodality:** Two instances confirmed; cross-axis verification of
B&S §4.2. Dip test p=7.6×10⁻⁶ at noise σ=0.2 (strongest in the cross-sweep audit); dip p=0.102
at alignment w_a=0.6. Both instances show z≈32.9 surrogate corroboration.

**Row 2 — §4.3 compressibility-Φ-inversion:** One instance confirmed at jamming α=0.2;
+38.6% mean Φ inversion above coherent baseline. σ_u floor-locked (0.5925 vs 0.5183); φ_norm
σ reduced (0.025 vs 0.079) — compressed variance signature.

**Row 3 — leader-block partition Φ collapse:** Φ ordering matches Outcome 4 prediction
direction; MI matrix shows block-structured 8×8 leader cluster (leaders first, white dashed
separator). Fiedler bipartition ⟷ leader-membership = 1.000 (perfect). †vanilla-boids baseline
(byte-identical to leadership λ=0.0 / jamming α=1.0 / noise σ=0.05 etc.).

## Figure 4 — Agreement/divergence heatmap

Spearman correlation between Φ_spectral and 18 TDA persistence metrics across all 38 scenarios
(sweep × condition, vanilla-baseline included as separate row). Strong positive correlation =
spectral and topological metrics agree; near-zero or negative = divergence. H2 columns (3D-specific)
shaded. Row order: hierarchical clustering on 18-column row vectors. ○=§4.2 instance, ▲=§4.3
instance, ■=leader-block, ◇=exploratory split_merge. The Bailey 2026 core hypothesis predicts
agreement in coherent regimes and divergence in regimes where higher-dimensional persistence
captures dynamics not visible to spectral measures.

## Figure 6 — Surrogate null comparison

The circular-shift surrogate null is method-validated by the synthetic AR(1) i.i.d. control
(z=−0.53, within surrogate 95% CI). Eight science scenarios all show observed Φ above the
surrogate null at z ≥ 8.38 (well above the z=3.12 boundary-synchrony floor from disabled-interaction
control). The strongest above-null result is noise σ=0.2 at z=32.92 (§4.2 instance) and
alignment w_a=0.6 at z=32.91 (§4.2 instance). Split_merge shows observed below the null at
z=−5.08 — exploratory compressibility-direction candidate (single-seed). Dark bars = observed Φ;
light bars = surrogate mean ± 95% CI. Method-validation controls shown with gray hatching.

## Figure 8 — 3D scenario snapshots

3D scatter snapshots of six scenarios at representative steady-state windows, colored by Fiedler
bipartition of the per-window MI matrix (MI-computed for leadership λ=2.4 and λ=0.0; spatial
k-means proxy for other scenarios — appropriate since the Fiedler partition reflects geometric
proximity in coherent/milling regimes). Red/blue = Fiedler bipartition classes. At leadership
λ=2.4, larger markers indicate leader agents; the Fiedler bipartition aligns with leader-membership
with perfect agreement (= 1.000), visually illustrating the leader-block partition mechanism.
Box dimensions: 50³ container.
