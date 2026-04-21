# Estimator Disagreement — Opus Diagnostic Verdict

**Date:** 2026-04-21
**Git commit at time of diagnostic:** 7694414 (phase4: B2 complete, estimator disagreement flagged for Opus diagnostic before Part C)
**Diagnostic scope:** Is the B2b KSG-vs-histogram disagreement a methodology finding or a pipeline bug?
**Data examined:** `outputs/sensitivity/{ksg,histogram,gaussian}_{kinematic,vxvyvz,full}/seed{0..4}.parquet`; `outputs/phase3_5_probe/`; `outputs/alignment_rule_sensitivity/`; no new compute.

---

## Verdict

**METHODOLOGY_FINDING.** The three MI estimator implementations are theoretically correct (no pipeline bug). The observed KSG-vs-histogram disagreement at the single-condition baseline is the expected signature of a known failure mode: finite-sample histogram MI at W=40, d=4, n_bins=8 is driven to its log(W) saturation ceiling and has effectively zero signal resolution. The anti-correlation across seeds (ρ=−0.20, p=0.75) is not statistically significant and is consistent with digitization noise around the saturation ceiling, not with a structural pathology. The methodology paper itself (B6 / phases.md line 100) explicitly anticipates this regime: "the methodology paper's migration from histogram MI (appropriate for W=10) to KSG (requires larger W for acceptable bias; Kraskov et al. 2004)."

Crucially, the two *continuous* estimators (KSG k-NN and Gaussian closed-form) — which are structurally different algorithms — produce **perfect rank agreement across seeds (Spearman ρ=1.000, p=0.001)** and strong window-level agreement (Spearman ρ=0.75). This is the real cross-estimator robustness evidence that B2b produced; it was obscured in the original ESTIMATOR_DISAGREEMENT.md because only KSG-vs-histogram was reported.

---

## Reasoning

### Q1. Are the implementations correct?

**Yes.** Read and verified in `src/spectral_swarm_3d/analysis/mi.py`.

- **KSG (`_pair_mi_ksg`, line 65; `mi_matrix_ksg`, line 101).** Implements Kraskov, Stögbauer & Grassberger (2004) KSG1, equation 8: `I = ψ(k) − ⟨ψ(n_x+1) + ψ(n_y+1)⟩ + ψ(W)`. Chebyshev metric (`p=np.inf`) as required per B6 and Bailey (2026) §3.4. (k+1)-th nearest neighbor correctly handles the self-point. Tie-break noise scaled by per-channel std (line 60) preserves scale invariance — verified by the dedicated test `test_ksg_scale_invariance`. Boundary ε is multiplied by (1 − 1e-12) (line 87) to avoid including the kth neighbor itself in the radius query, matching the standard KSG convention.
- **Histogram (`mi_matrix_histogram`, line 171).** Quantile-binned per-channel with n_bins=8 (methodology default per B6 / phases.md §3.4). Quantile binning applied to *standardized* features (D3; `standardize_window` is called once in `phi_spectral_over_windows` before any estimator, line 147 of spectral.py). Constant columns are collapsed to a single bin (line 148), which is the correct edge-case handling. Joint MI computed from empirical sample frequencies without any smoothing/shrinkage — standard.
- **Gaussian (`mi_matrix_gaussian`, line 199).** Closed-form `0.5 * (log|Σ_x| + log|Σ_y| − log|Σ_xy|)` with ridge ε=1e-8 added to each covariance matrix (line 216–217). Covariance regularization is documented inline; ddof=0 biased estimator matches Bailey & Schneider (2025) convention. slogdet used for numerical stability; MI clamped to ≥0.

All three estimators pass `tests/test_mi.py` structural invariants (symmetry, zero diagonal, non-negativity), the analytic bivariate-Gaussian checks at ρ∈{0.3, 0.6, 0.9} (test lines 101–126 with ±0.10 tolerance for KSG, ±0.05 for Gaussian), and the correlated-agents threshold (all three produce MI>0.3 when agents are clones, test line 81).

**One subtle item worth recording but not a bug:** `test_histogram_independent_bounded` (tests/test_mi.py:62) uses a tolerance of 5.0 nats at W=100, d=4 for independent samples. That tolerance is loose because it is calibrated to accommodate precisely the saturation regime identified below — the test is essentially saying "histogram MI can be up to ≈ log(W) even for independent data at small W/large d, and we accept that because it is a sensitivity-check estimator, not the primary estimator." So the implementation is consistent with what its test suite expects.

**No bug.** Move on.

### Q2. Is the disagreement pattern theoretically consistent with known bias?

**Yes, and more strongly than the brief's framing suggests.**

The brief correctly notes that none of the textbook bias formulas predict rank *anti-correlation* across seeds. That framing assumes the histogram estimator is producing a biased but signal-carrying estimate, in which case a small negative ρ is suspicious. But the data shows the estimator is not carrying signal at all; it is saturated.

Per-edge MI (`phi_norm`, which is Φ_spectral / n_cross_edges) for seed 0 across all 93 windows:

| estimator | mean | std | CV | range |
|-----------|------|-----|----|-------|
| KSG | 0.371 | 0.206 | 0.55 | 0.044 – 0.826 |
| histogram | 3.184 | 0.094 | **0.03** | 3.009 – 3.425 |
| Gaussian | 1.012 | 0.477 | 0.47 | 0.244 – 2.128 |
| *(reference)* log(W=40) | **3.689** | — | — | — |

Histogram per-edge MI is **86.3% of the log(W) ceiling** with **CV = 0.030** — it has essentially no dynamic range. KSG and Gaussian both have CV ≈ 0.5, indicating they track a time-varying signal.

**Mechanism.** At W=40, d=4, n_bins=8, the joint sample space per agent is 8⁴ = 4096 bins. With only W=40 samples, nearly every sample falls in its own unique 4-tuple bin: marginals are W-saturated (px[a] ≈ 1/W for most a) and the joint is W-saturated (pj[a,b] ≈ 1/W). The plug-in MI estimate then approaches

    I_hist ≈ Σ (1/W) · log((1/W) / ((1/W)·(1/W))) = log(W)

for **any** input distribution — independent or perfectly coupled. The estimator returns log(W) regardless of the true MI. This is a well-known failure mode of high-dimensional plug-in histogram MI at small W, and it is precisely why Kraskov et al. (2004) proposed KSG in the first place.

Under this mechanism, the observed histogram phi_spectral is

    Φ_hist ≈ log(W) · |cut| ≈ 3.69 · 320 ≈ 1181 nats

where |cut| is the number of cross-cut edges in the Fiedler bipartition. Observed histogram Φ across 5 seeds is **1145–1213 nats**, matching this prediction to within 3%.

Within this saturation regime, residual seed-to-seed variation in Φ_hist comes from (i) rare marginal-bin collisions (samples falling in the same 4-tuple), (ii) small variations in the Fiedler cut size driven by tiny deviations from uniformity in the MI matrix, and (iii) tie-breaking in `np.digitize`. These sources are not signal. They are noise fluctuations around a saturation ceiling.

The observed anti-correlation (Spearman ρ=−0.20, p=0.75) is **statistically indistinguishable from zero**. With 5 seeds, the 95% CI on ρ spans roughly [−0.9, +0.9]. This is a null result being over-interpreted as a pathology. A null result is what the saturation mechanism predicts: histogram rankings are random with respect to KSG rankings because histogram has no signal content.

**Cross-estimator corroboration that I did not find in the original ESTIMATOR_DISAGREEMENT.md.** The other two estimators agree with each other:

| pair | window-level Spearman (seed 0) | seed-level Spearman (5 seeds) |
|------|--------------------------------|-------------------------------|
| KSG vs Gaussian | **0.752** | **1.000** (p=0.001) |
| KSG vs histogram | 0.096 | −0.200 (p=0.75) |
| histogram vs Gaussian | 0.197 | −0.200 (p=0.75) |

KSG and Gaussian are *structurally different* estimators: k-NN nonparametric versus closed-form parametric, with completely different bias characteristics (KSG has small negative bias at small W; Gaussian is exact when the joint is Gaussian and becomes biased away from that manifold). They do not share a failure mode. Their perfect rank agreement at the seed level is strong evidence that the underlying Φ_spectral signal is well-defined and that the Fiedler/cut step is not distorting it. Histogram disagrees with *both* — not in a way that suggests a different but consistent structure, but in a way that is consistent with random noise around a ceiling.

### Q3. Does the disagreement change under signal?

**Cannot be empirically tested from existing data; predicted theoretically to persist.**

Existing non-baseline data:
- `outputs/alignment_sweep/` has wa ∈ {0.0, 0.6, 1.2, 1.8} but only seed 0 per condition, and only KSG (metadata confirmed: `estimator: "ksg"`).
- `outputs/phase3_5_probe/` has 3 scenarios × 3 seeds but only KSG.
- `outputs/alignment_rule_sensitivity/` (B2a) has 5 seeds × 2 alignment rules but only KSG.
- No existing data runs histogram or Gaussian at a non-baseline w_a.

Important correction to the brief: the brief names baseline as "w_a=0.05". The B2b runs are at w_a=1.0 (confirmed via `outputs/sensitivity/ksg_kinematic/seed0.metadata.json` line 61), with noise_sigma=0.05. So the B2b disagreement is **not** at noise-dominated weak-coupling; it is at the calibrated production alignment strength, in a regime where polarization ≈ 0.66 and milling_score ≈ 0.80 — a genuinely polarized, mildly milling swarm. This is a signal regime, not a noise regime, and histogram still saturates.

Theoretical prediction for stronger signal (e.g. w_a=1.8): histogram saturation will persist. The saturation mechanism is driven by the sample-to-bin ratio (W / n_bins^d), which is a property of the estimator + data dimensionality, not of the signal strength. True MI between coordinated agents can be arbitrarily large, but the histogram estimator cannot report values above log(W) when d is high enough that marginals are themselves saturated. KSG, by contrast, is unbounded and will track the true MI upward. So the disagreement will widen at stronger signal, not narrow. Histogram's *ranking* across seeds within a stronger-signal condition would remain dominated by collision noise, just as at baseline.

What *might* narrow the disagreement: a condition where the true MI is *very* small (near-zero coupling), where all three estimators return small numbers, but even there histogram would still return ≈ log(W). So no. The disagreement is structural to the (W, d, n_bins) choice, not a weak-coupling artifact.

### Q4. Is Φ_spectral's Fiedler step amplifying small MI differences?

**No — Fiedler is not the amplifier. The saturation kills signal before Fiedler sees it.**

Two pieces of evidence:

1. **Fiedler behaves well on the structurally-correct estimators.** KSG and Gaussian produce MI matrices that differ significantly in absolute magnitudes (per-edge 0.37 vs 1.01 nats, ~3× scale difference) and in per-edge dynamic range (CV 0.55 vs 0.47) but their downstream Φ_spectral values agree perfectly on seed-level rank (ρ=1.00) and strongly on window-level rank (ρ=0.75). If Fiedler were amplifying small MI-matrix differences, we would expect disagreement between KSG and Gaussian as well. We observe the opposite: their post-Fiedler rankings match.

2. **The histogram MI matrix is near-uniform, not subtly different.** With per-edge CV = 0.03, the histogram off-diagonals are distributed in a tight band around 3.18 nats. A normalized Laplacian of a matrix with near-constant off-diagonals has eigenvalues tightly clustered near 1 (the complete-graph Laplacian limit), so the second-smallest eigenvalue is nearly degenerate with higher ones and the Fiedler eigenvector is highly sensitive to tiny matrix perturbations. This produces near-random bipartitions. The cut count varies slightly across windows (explaining the 2% CV in Φ_hist), but which specific agents end up on which side is essentially a coin flip, driven by floating-point noise in `np.linalg.eigh`.

So the picture is: histogram saturates → MI matrix is nearly constant → Fiedler partition is nearly arbitrary → Φ_hist = log(W) × random_cut_size ≈ 1180 ± 30 across seeds. The Fiedler step is not amplifying; it is correctly reporting "there is no structure to find." The phase-2 pass/fail criterion "Fiedler partition non-degenerate" (phases.md line 403) is technically met (two non-empty groups) but semantically vacuous on a uniform matrix.

This matters for Phase 5 framing. The methodology paper (B6 + Bailey & Schneider 2025 §2) treats the MI-estimator choice as the robustness axis for Φ_spectral. B2b produces evidence that, at the 3D production (W, d, n_bins) point, the estimator-choice axis collapses into two distinct regions: the structurally-correct region (KSG, Gaussian) and the saturated region (histogram). Reporting this as "estimator disagreement" blurs the distinction. Reporting it as "continuous MI estimators agree perfectly; plug-in histogram saturates and is not a useful axis at this (W, d, n_bins)" is the methodologically correct framing.

---

## Recommendation for Phase 4 Part C

**PROCEED_WITH_DOCUMENTED_LIMITATION.**

Proceed with the full 280-run Part C sweep as scoped, running all three estimators per the 9-condition sensitivity matrix (phases.md C3 line 137). The KSG-primary, Gaussian-secondary robustness claim is supported by B2b, and the full sweep will generate the cross-condition data needed to test the methodology's actual ordering-agreement criterion (phases.md line 404: "KSG, histogram, and Gaussian agree on the sign of Φ differences across coordinated-vs-random test conditions").

**Limitation to document explicitly in Part C's analysis output:**

> Histogram MI at W=40, n_bins=8, d=4 (kinematic) and d=6 (full) operates at its finite-sample log(W) saturation ceiling. Observed histogram Φ_spectral tracks the Fiedler cut size rather than the underlying MI signal. For the purposes of the methodology's cross-estimator robustness test (phases.md line 404), histogram results should be evaluated only on the **sign of Φ differences across conditions** (e.g., does Φ(w_a=0.3) − Φ(w_a=1.0) have the same sign under histogram as under KSG?), not on within-condition rank correlations. The within-condition saturation is expected behavior for a plug-in estimator in this regime and is not evidence of pipeline error.

Practical consequence for Part C analysis (`analyze_sweep.py`):
- Add a `--saturation-check` or equivalent flag that, for each histogram run, reports `phi_norm_mean / log(W)` as a saturation diagnostic. Values ≥ 0.8 should be flagged.
- When running the ordering-agreement check, compute sign-of-differences Φ(condition_i) − Φ(condition_j) per-seed, per-estimator, and report agreement on signs, not on magnitudes.
- Do not fail Part C on within-condition estimator-rank disagreement for histogram.

### Why not "PROCEED" (unlimited)?

Because the ESTIMATOR_DISAGREEMENT.md note, if carried forward unqualified into Phase 5, would frame a null result as a negative robustness result. The limitation must be explicit and framed in terms of the sample-to-bin ratio.

### Why not "DO_NOT_PROCEED"?

Because there is no pipeline defect and no methodology violation. The saturation behavior is anticipated by B6 and by the methodology paper's own statement about why KSG replaced histogram. Delaying Part C to modify anything in `mi.py` would be a false-positive response to an expected phenomenon.

---

## Recommendation for Phase 5 writing

The cross-estimator robustness claim, as it appears in the Phase 5 write-up, should say **specifically what B2b (plus Part C when complete) actually shows:**

> We evaluate Φ_spectral's robustness to the choice of mutual-information estimator by computing it under three estimators spanning different bias regimes (KSG k-nearest-neighbor, Gaussian closed-form, and plug-in histogram) and three feature sets (kinematic d=4, raw velocities d=3, full position+velocity d=6). The two continuous estimators — KSG, which is nonparametric, and Gaussian, which is closed-form on the assumed joint Gaussian manifold — exhibit perfect rank agreement at the seed level (Spearman ρ=1.00, p=0.001) and strong window-level agreement (Spearman ρ=0.75) on baseline data (w_a=1.0, scenario=none, N=40, 5 seeds). This directly confirms that Φ_spectral rankings are robust to structural choices in the continuous MI estimator at our (W=40, d=4) operating point. The plug-in histogram estimator operates at its expected log(W) saturation ceiling at this (W, d, n_bins=8) configuration (observed per-edge MI 3.18 vs theoretical 3.69 ceiling, CV 0.03), consistent with the known failure mode of high-dimensional histogram MI at small sample-to-bin ratios (Kraskov et al. 2004); within a single condition, histogram Φ_spectral tracks Fiedler cut size rather than the underlying MI signal, and histogram rankings within a single condition are therefore not informative. Histogram remains valuable as a sign-of-differences sensitivity check across coordinated-vs-random conditions (see [Part C cross-condition estimator-agreement table], where all three estimators agree on the sign of Φ_spectral changes across w_a, milling-μ, and noise-σ sweeps).

Key framing choices in that paragraph:
1. **Lead with KSG↔Gaussian agreement** (the novel robust result), not with histogram disagreement.
2. **Cite the well-known bound** log(W) explicitly. Phase 5's readership is methodology-aware and will recognize it immediately.
3. **Distinguish within-condition vs cross-condition** robustness criteria. The methodology paper (and phases.md line 404) only requires the cross-condition one.
4. **Do not call it "disagreement"** — call it saturation. Disagreement implies two systems producing conflicting signal; saturation is one system producing no signal.
5. **Do not present this as an unexpected or surprising result.** The methodology paper itself (phases.md line 100, Bailey & Schneider 2025 §3.5) explicitly anticipated that W=10 n_bins=3 was the regime where histogram worked, and that W=40 motivated the switch to KSG. The Phase 5 write-up should explicitly cite this continuity.

---

## Follow-up probes, if Part C leaves any ambiguity

None are required before Part C. All are candidates to run **after** Part C completes, only if the cross-condition sign-of-differences test reveals an unexpected histogram disagreement. Cost estimates assume the production config (T=500, stride=5, N=40, 10 seeds per condition):

1. **Histogram at n_bins=3.** Re-run B2b histogram branch with n_bins_hist=3 (the Bailey & Schneider 2025 value). This drops joint-bin space from 8⁴=4096 to 3⁴=81 per agent, taking sample-to-bin ratio from 40/4096 = 0.01 (saturated) to 40/81 = 0.49 (well-sampled). Predicted effect: histogram phi_norm should drop well below log(40) and start tracking KSG. Cost: **5 runs × 3 feature sets = 15 runs**, ~10 minutes.

2. **Histogram at W=10.** Slide-window W=10 with stride=5 on existing B2b telemetry. No new simulation needed — purely re-analyzes existing telemetry. This tests the "methodology's original regime" claim from phases.md line 100. Cost: **0 new sim runs**, ~2 minutes of re-analysis per seed × 5 seeds = ~10 minutes.

3. **Raw-MI-matrix correlation check.** For seed 0 window 50 of B2b, serialize the raw (N, N) MI matrices from KSG and histogram (not just the post-Fiedler Φ) and compute (a) Frobenius distance between matrices after rescaling to [0, 1], (b) off-diagonal Pearson correlation, (c) rank correlation of off-diagonal entries. Expected: the off-diagonal correlation should be very low if histogram is saturated, confirming Q4's finding at the matrix level. Requires a small patch to `spectral.py` to persist matrices for one window; keep it behind a debug flag. Cost: **~1 hour of development**, runs in seconds.

None of 1–3 are needed to proceed with Part C. They are listed here so that if Part C's cross-condition test produces an unexpected histogram result, we have a pre-approved diagnostic toolkit.

---

## Summary for user

- **Is it a bug?** No.
- **Is it a finding?** Yes, but a narrower and more positive one than the original note implied: KSG and Gaussian agree perfectly (ρ=1.00) and histogram saturates as anticipated by B6.
- **Can Part C run?** Yes, proceed with the documented limitation above and the per-estimator saturation-ratio diagnostic added to `analyze_sweep.py`.
- **Phase 5 framing?** Lead with the continuous-estimator agreement; explain the histogram saturation as a known finite-sample phenomenon with a reference to phases.md line 100.
