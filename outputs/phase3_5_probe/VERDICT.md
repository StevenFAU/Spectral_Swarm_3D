# Phase 3.5 Probe — Verdict

**Date:** 2026-04-21  
**Git commit:** see `outputs/phase3_5_probe/*/seed*_metadata.json`  
**Probe conditions:** scenarios `none`, `split_merge`, `jamming`; seeds 0, 1, 2; T=500, W=40, stride=5, N=40, KSG estimator, kinematic features.  
**Steady-state:** final third of windows (~steps 310–499, 31 windows out of 93).

---

## Summary Table (steady-state means)

| scenario | seed | phi_spectral | polarization | milling_score | angular_momentum_norm | traj_TP_1 | traj_MP_1 | snap_TP_0 | snap_TP_1 |
|----------|------|-------------|-------------|--------------|----------------------|-----------|-----------|-----------|-----------|
| none | 0 | 125.12 | 0.6535 | 0.7326 | 16.644 | 2.7012 | 0.8829 | 99.30 | 1.4566 |
| none | 1 | 158.23 | 0.8141 | 0.8205 | 17.503 | 1.7567 | 0.7077 | 104.85 | 1.3223 |
| none | 2 | 113.15 | 0.6498 | 0.8304 | 15.002 | 2.2657 | 0.8247 | 118.64 | 1.4020 |
| split_merge | 0 | 83.97 | 0.7359 | 0.6803 | 13.405 | 1.4666 | 0.6500 | 85.28 | 1.4641 |
| split_merge | 1 | 112.58 | 0.6127 | 0.8220 | 13.413 | 1.6783 | 0.7621 | 94.10 | 1.0033 |
| split_merge | 2 | 193.76 | 0.7428 | 0.7908 | 16.106 | 1.3787 | 0.6175 | 72.02 | 1.1380 |
| jamming | 0 | 123.59 | 0.7209 | 0.6344 | 10.562 | 2.7412 | 0.8275 | 119.57 | 1.6632 |
| jamming | 1 | 168.97 | 0.8550 | 0.8670 | 21.220 | 1.3029 | 0.6322 | 96.71 | 2.0708 |
| jamming | 2 | 142.08 | 0.7534 | 0.8293 | 12.471 | 2.1643 | 0.8467 | 119.38 | 2.0335 |

---

## Q1. Does `traj_TP_1` reliably separate `split_merge` from `none` across 3 seeds?

Per-seed values:

| Seed | none traj_TP_1 | split_merge traj_TP_1 | Ratio (sm/none) |
|------|---------------|-----------------------|-----------------|
| 0 | 2.7012 | 1.4666 | 0.54× |
| 1 | 1.7567 | 1.6783 | 0.96× |
| 2 | 2.2657 | 1.3787 | 0.61× |

**No clean separation.** The direction is consistent across seeds — `none` has higher `traj_TP_1` than `split_merge` in all three cases — but seed 1 is essentially a tie (0.96×), and the effect is in the "wrong" direction for topological-event detection: we would expect a group-splitting event to *increase* trajectory H1, not decrease it. The consistent but inverted direction suggests that the two coherent sub-flocks formed during split_merge each produce low-variance, low-H1 trajectory clouds (strong within-group alignment suppresses trajectory-cloud loops), while the baseline flock's mild disorder generates more H1. This is a mechanistic interpretation, not a separation result. As a detector of the split_merge event, `traj_TP_1` fails: it would flag the *baseline* as more topologically interesting, not the event.

---

## Q2. Does `traj_TP_1` reliably separate `jamming` from `none` across 3 seeds?

Per-seed values:

| Seed | none traj_TP_1 | jamming traj_TP_1 | Ratio (jam/none) |
|------|---------------|-------------------|-----------------|
| 0 | 2.7012 | 2.7412 | 1.02× |
| 1 | 1.7567 | 1.3029 | 0.74× |
| 2 | 2.2657 | 2.1643 | 0.96× |

**No.** The sign reverses: seed 0 has jamming marginally above baseline; seeds 1 and 2 have baseline above jamming. All three ratios are near 1.0 (range 0.74–1.02), indicating no signal above within-scenario variance. This is the same pathology Phase 3 observed for milling-vs-baseline: the direction of the H1 difference is not reproducible across seeds, and the magnitudes are indistinguishable from the noise level expected at N=40.

---

## Q3. Is the H1-on-trajectory-clouds issue milling-specific or more general?

**The H1 issue is more general.**

The sign-reversal pattern that Phase 3 established for milling-vs-baseline is replicated here for jamming-vs-baseline. For jamming, `traj_TP_1` shows the same unreliable behaviour: no consistent direction across seeds, with differences well within the inter-seed variance range. For split_merge, the direction is consistent but inverted (baseline always higher), the seed-1 effect is negligible, and the signal cannot be used as a positive detector of the event.

Across all three non-milling contrasts tested in this probe, `traj_TP_1` at N=40 fails to function as a reliable observable:
- **Jamming**: sign reversal. Cannot be used.
- **Split_merge**: consistent suppression relative to baseline, not enhancement. Mechanistically plausible but not a useful positive control.

**Implication for Phase 4:** `traj_TP_1` (and by extension `traj_TP_1`'s companion `traj_MP_1`) should be demoted from the primary TDA observable set alongside `traj_TP_2` and `snap_TP_2` (already dropped in D9). The trajectory-cloud H1 branch is a secondary/exploratory dimension at N=40. The TDA contribution to Phase 4 rests primarily on the snapshot pipeline, not the trajectory pipeline.

The H1-noise mechanism is likely finite-size: at N=40 the trajectory cloud has only 40 points in a W×d = 160-dimensional ambient space. Ripser's Vietoris-Rips complex at this sparsity level produces H1 bars whose persistence is dominated by the ambient geometry of 40 random high-dimensional points, not the coordination signal. This is the same geometric argument that killed H2 on trajectory clouds in D9 (coverage threshold in high ambient dimension), now extended to H1.

---

## Unexpected observations

**1. `snap_TP_1` (snapshot H1) cleanly separates jamming from baseline.**

| Seed | none snap_TP_1 | jamming snap_TP_1 | Ratio (jam/none) |
|------|--------------|-------------------|-----------------|
| 0 | 1.4566 | 1.6632 | 1.14× |
| 1 | 1.3223 | 2.0708 | 1.57× |
| 2 | 1.4020 | 2.0335 | 1.45× |

All three seeds: jamming > none. The effect size is moderate (1.14–1.57×) but the direction is robust. This is the opposite of the trajectory result for jamming: where `traj_TP_1` fails, `snap_TP_1` succeeds. The spatial snapshot during jamming appears to preserve more H1 loops (intermediate-scale spatial structure) than the baseline, possibly because jamming disrupts cohesion and creates less-polarised, geometrically more disordered spatial configurations.

This observation motivates promoting `snap_TP_1` as a candidate primary TDA observable for Phase 4, in place of the trajectory-cloud quantities. Whether it generalises to other scenarios and whether the effect survives the full alignment and jamming sweeps is a Phase 4 question, but the signal is robust enough to track.

**2. `snap_TP_1` does not separate split_merge from baseline.**

Seed 0: essentially equal (1.46 vs 1.46). Seeds 1–2: split_merge slightly lower. No consistent signal. The snapshot topology during split_merge — even during the group-separation phase — does not differ from baseline at this N. This is consistent with the snapshot H2 finding from Phase 3 (spatial snapshot topology at N=40 lacks resolution for subtle structural changes).

**3. `snap_TP_0` is suppressed for split_merge across all seeds.**

none means: 99.30, 104.85, 118.64 (mean ≈ 107.6).  
split_merge: 85.28, 94.10, 72.02 (mean ≈ 83.8), consistently lower.

Lower `snap_TP_0` indicates shorter-lived H0 bars (connected components merge at smaller Rips radius), which implies tighter spatial clustering during split_merge. This is consistent with two cohesive sub-flocks forming during the split phase: each group is internally tight, reducing the scale at which points connect. The effect is worth noting but is not a clean topological-event detection — it would need comparison to a known two-cluster configuration to establish baseline separation.

**4. `phi_spectral` and classical metrics show high within-scenario variance across seeds.**

`phi_spectral` ranges for split_merge are 83.97–193.76, entirely overlapping the none range of 113.15–158.23. Classical metrics show similar overlap. At 3 seeds this is not statistically interpretable, but the pattern is consistent with Phase 3 findings and justifies Phase 4's 10-seed design for primary sweeps.

---

## Phase 4 implications

1. **Demote trajectory TDA branch.** `traj_TP_1`, `traj_MP_1` (and the already-dropped H2 trajectory variants) should be listed as secondary/exploratory in Phase 4's pass/fail criteria. The milling positive control (`traj_TP_1` vs milling sweep, which had seed 0 success but seeds 2–4 reversal per D9) is unreliable and should not be carried forward as a primary check.

2. **Elevate `snap_TP_1`.** Replace the trajectory H1 positive control with a snapshot H1 check: `snap_TP_1` for jamming > baseline across seeds. This probe provides a 3/3-seed positive result. Phase 4 should write the jamming-sweep pass criterion around `snap_TP_1`, not `traj_TP_1`.

3. **Classical measures and Phi_spectral remain the primary quantitative observables.** The snapshot TDA adds interpretable secondary signal (particularly `snap_TP_1` for jamming); the trajectory TDA branch is retained for completeness but not relied on for Phase 4's primary conclusions.

These implications should be formalised in a Phase 4 plan revision session (separate from this probe session, per CLAUDE.md phase discipline).
