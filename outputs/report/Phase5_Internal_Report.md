# Phase 5 — Internal Report

**Project:** Spectral Swarm 3D — extension of the Bailey (2026) and Bailey & Schneider (2025) swarm-analysis framework from 2D to 3D.
**Phase:** 5 — Comparison Analysis, Surrogates, Figures, and Internal Report.
**Document type:** Internal report (draft). Closing artefact of Phase 5's interpretation tier; supersedes none — the comprehensive empirical record from which any future external manuscript would distill.
**Date:** 2026-05-07.
**Audience:** project research team and future reviewers picking up Phase 5 as input to Phase 6 or to a published manuscript.
**Status:** revised draft incorporating reviewer feedback (compressibility vs redundancy-saturation discriminator added at §5.5; methodology-limit cross-references at §9.6; framework-level falsifiability statement at §9.7; §4.3 verdict tightened in §5.6; §8.2 z-score framing corrected; cross-seed/single-seed clarification at §4.4). Subsequent revisions will polish prose, refine figure captions, and add external citations.

---

## §1 — Executive summary

Phase 5 of the Spectral Swarm 3D project tested the Bailey & Schneider (2025) §4.2/§4.3 compressibility framework in a 3D Vicsek/Bailey swarm (N=40 agents in a 50³ reflective box, T=500 time steps per run, 10 seeds per primary condition, 11 sweep families). The framework predicts two empirically distinguishable phenomena: a **§4.2 transitional Φ peak** in which the spectral integration measure Φ_spectral becomes per-window bimodal at the disorder-to-order regime boundary, and a **§4.3 compressibility-Φ-inversion** in which Φ at a moderately disordered regime exceeds Φ at the same sweep's coherent baseline because the coherent regime spends time in low-entropy steady-flight windows that drag the mean down. Phase 5 was structured around three Bailey & Schneider 3D candidates pre-registered before any code was run: §4.2 transitional bimodality on the alignment axis, §4.3 compressibility on the jamming axis (already established at A2 commit `cc23aa9`), and a pre-registered prediction (Phase5.md Tier 1.A) that the leadership sweep would produce a third compressibility instance via leader-group compactness compressing within-window σ_u.

Phase 5 returned three substantive empirical contributions. First, the **§4.2 transitional Φ peak is confirmed at two instances** across orthogonal perturbation axes: alignment coupling at `w_a = 0.6` (Tier 1.B steady-state per-window dip test p = 0.102, modes = 2) and additive noise at `σ = 0.2` (Tier 1.C dip test p = $7.6 \times 10^{-6}$, modes = 2; mean Φ peaks above both endpoints at +7% over the synchronized end and +70% over the random end). The two-instance verification, established by the cross-sweep audit, exceeds the Phase 5 pre-registration's expectation of a single transitional-peak instance. Both instances corroborate at the surrogate level (z = 32.91 and z = 32.92 — the strongest in the eight-scenario Tier 2.B null-comparison set). Second, the **§4.3 compressibility-Φ-inversion is confirmed at jamming α=0.2** with a +38.6% mean-Φ inversion above the same sweep's coherent baseline (`Φ(α=0.2) = 187.23`, 95% CI [181.61, 193.74]; baseline `Φ(α=1.0) = 135.05`, 95% CI [115.95, 155.30]); σ_u floor-locked at 0.5925 (above the coherent baseline's 0.5183), phi_norm cross-seed σ reduced to 0.027 (vs 0.079 at baseline), per-window Φ unimodal-narrow (dip p = 0.984), and surrogate z = 16.17 confirming that the elevated Φ reflects real cross-agent integration rather than a confound. Third, the **pre-registered leadership extension is disconfirmed (Tier 1.A Outcome 4) but contributes a structurally distinct mechanism**: at λ = 2.4, Φ does collapse from baseline 135.05 to 8.73 (Cohen's d = +5.0, CIs disjoint), but the MI matrix is **block-structured around an 8-leader cluster** (Fiedler bipartition perfectly separates leaders from followers, agreement = 1.000) rather than uniformly elevated as compressibility would predict, σ_u is not compressed (it is in fact slightly higher at high λ than at baseline), and three of four A2-reference compressibility descriptors fail at λ = 2.4. The Φ collapse is a real empirical phenomenon, but the **mechanism is leader-block partition**, not §4.3 compressibility.

Phase 5's methodological contribution is a documented surrogate-method validation history. The pre-registered positive control (noise σ = 0.5) failed because boids at that noise level retain real cross-agent structure (Tier 2.B observed polarization = 0.46 at z = 17.58); a disabled-interaction control failed at z = 3.12 due to reflective-wall boundary synchrony coupling agents through shared boundary-reflection events; a third attempt — a synthetic per-agent AR(1) i.i.d. control — passed at z = −0.53 within the surrogate 95% CI, validating the circular-shift surrogate protocol. The boundary-synchrony floor at z = 3.12 is preserved as a model-level effect, not a method bias; all eight science-scenario z-scores exceed it.

What Phase 5 does establish: the Bailey & Schneider §4.2/§4.3 framework is empirically grounded in this 3D swarm across **three orthogonal perturbation axes** (alignment coupling, additive noise, jamming severity), with the framework operating mechanism-specifically rather than sweep-agnostically. What Phase 5 does not establish: a unified compressibility mechanism across all coordination regimes — the leadership axis was tested and produces a structurally distinct phenomenon. What Phase 5 leaves open: a single-seed exploratory split_merge surrogate result (z = −5.08, observed below null) flags split_merge as a possible additional §4.3 candidate at the dissolution-event level, but the Φ direction is wrong (mean Φ at split_merge falls below the coherent baseline rather than above) and the σ_u signature was not computed; this is reported as an exploratory flag, not a confirmed third instance. The two-instance §4.2 result is empirically stronger than the original pre-registration anticipated; the §4.3 result is jamming-specific rather than the multi-sweep generalization originally hoped for; the leadership extension's disconfirmation is itself a result, not a caveat.

---

## §2 — Introduction

### 2.1 The Bailey 2026 / Bailey & Schneider 2025 framework

The methodology paper anchoring this project (Bailey 2026, *Spectral and Topological Methods Comparison in Swarms*) specifies a measurement pipeline for collective-motion data: per-window mutual-information graphs over a kinematic feature set, Fiedler bipartition of the normalized Laplacian, and the spectral integration measure Φ_spectral defined as the unnormalized MI cut sum across the bipartition. The companion paper (Bailey & Schneider 2025, *When Wholes Resist Decomposition: A Spectral Measure of Epistemic Emergence*) introduces Φ_spectral and validates its behaviour across random, transitional, synchronized, and CTLN systems. Two of that paper's predictions are load-bearing for Phase 5:

- **§4.2 (transitional Φ peak):** at the disorder-to-order phase boundary, the per-window distribution of Φ becomes bimodal — windows alternate between high-Φ turning/wobble episodes (in which the swarm reorients and within-window dynamic amplitude is large) and low-Φ steady-flight episodes (in which the swarm holds heading and within-window dynamic amplitude is small). The mean of this bimodal distribution sits between the random-regime mean and the synchronized-regime mean, producing a transitional peak when the random endpoint is genuinely B&S-random.
- **§4.3 (compressibility-Φ-inversion):** the synchronized regime is *compressible* in the information-theoretic sense — its intrinsic within-window entropy is small, so MI values are small even though static coordination (polarization) is high. A regime that prevents this compressibility, by floor-locking within-window dynamic amplitude above the steady-flight low, will register higher mean Φ than the coherent baseline despite producing visibly less coherent dynamics. Phase 4 established this empirically for the jamming sweep (A2 diagnostic, commit `cc23aa9`).

The 3D extension — a separate codebase from the 2D proof of concept (`github.com/StevenFAU/Spectral_Swarm`, frozen at tag `v0.1-2d-poc`) — restores the methodology paper's KSG MI estimator and mean alignment rule (deviations the 2D code had introduced for pipeline-budget reasons), adds H2 persistent homology for enclosed-void detection in 3D, and uses a velocity-projected milling tangent that produces spherical-shell configurations rather than the fixed-axis equatorial ring a naïve 3D extension would generate. Cluster D decisions D11 (histogram-MI saturation), D12 (angular_momentum_norm 3D geometry), D13 (split-merge snap_TP_0 non-replication), and D14 (compressibility framework) anchor the Phase 5 interpretation.

### 2.2 Phase 5 pre-registration

Phase 5 was scoped before Tier 1 ran. The pre-registered structure had three tiers:

- **Tier 1 (Opus-first):** interpretation-first analysis on existing Phase 4 data, no new simulation. Tier 1.A tested the leadership compressibility prediction. Tier 1.B produced the per-window distribution atlas. Tier 1.C synthesized the cross-sweep verdict.
- **Tier 2 (Sonnet-first):** the comparison pipeline ported from 2D with H2 column additions (Tier 2.A), surrogate-null testing (Tier 2.B), and aggregated cross-scenario tables (Tier 2.C).
- **Tier 3 (mixed):** publication figures composed around the Tier 1 verdict (Tier 3.A), 3D scenario animations (Tier 3.B, separate session), and this internal report (Tier 3.C).

The four-outcome framework for Tier 1.A's leadership prediction was specified in Phase5.md before the analysis ran:

- **Outcome 1** — leadership prediction confirmed *with compressibility mechanism*. Φ non-monotone in λ, σ_u compressed at high λ, MI matrix uniformly elevated at λ = 2.4. This was the result that would have made compressibility a general mechanism; the Phase 5 writeup would have led with mechanism.
- **Outcome 2** — directionally confirmed but weak. σ_u and compactness behave as predicted but Φ ordering is monotone.
- **Outcome 3** — disconfirmed. Φ monotone, σ_u behaves differently. Compressibility narrows to a jamming-specific finding.
- **Outcome 4** — Φ ordering confirmed but mechanism differs (block-structured MI rather than uniformly elevated). The Φ drop at high λ would be real but mechanistically distinct from compressibility, and would need to be reported as its own finding under a different name.

The data fall on Outcome 4. The cross-sweep audit (Tier 1.C, commit `fec6079`) further established that the §4.2 transitional peak is confirmed at two instances rather than one, lifting the §4.2 evidence beyond what the pre-registration anticipated.

### 2.3 The Phase 5 question, as it now reads

The question Phase 5 was registered to answer was: *does the Bailey & Schneider §4.2/§4.3 compressibility framework operate as a general mechanism across orthogonal perturbation axes in a 3D swarm, with the leadership extension serving as the direct test of generality?* The answer is: the framework operates **mechanism-specifically across three orthogonal axes (alignment, noise, jamming)** with the leadership axis tested and producing a **structurally distinct mechanism** (leader-block partition) rather than a third compressibility instance. The mechanism's empirical reach is broader than one sweep but narrower than universal — exactly what the four-outcome pre-registration was designed to discriminate.

This report documents the empirical evidence for that finding tier by tier, addresses four prose-engagement items the figure review surfaced (asymmetric §4.2 visual evidence, the standalone MI matrix diagnostic relative to Figure 1, the noise σ = 0.5 reclassification in Figure 6, and the §4.2 instances' separation in Figure 4's hierarchical clustering), and closes with what Phase 5 establishes, what it narrows, what it unexpectedly contributes, and what it leaves open for Phase 6.

---

## §3 — Methods

This section documents the simulation, analysis pipeline, bimodality methodology, cross-sweep aggregation, surrogate-method validation history, and multi-Claude session structure. Methodological detail is reproducible from the code at commit `5974061` (HEAD at the time of report drafting) and earlier; specific commits are cited where their introduction is load-bearing.

### 3.1 Simulation

The 3D swarm uses `BoidSwarmModel3D` (Mesa 3.4 with `mesa.experimental.continuous_space.ContinuousSpace` in 3 dimensions; A1, ter Hoeven et al. 2025), N = 40 agents in a 50 \times 50$\times$50 reflective box with vision radius r_v = 10 (A2 — preserves the expected uniform neighbour count from 2D: `(N−1)·(4π/3)·r_v³/L³ ≈ 1.31`, matching 2D's `≈ 1.22`). The boids dynamics use mean alignment (A6 methodology restoration; the 2D code's sum variant is preserved as a config flag), velocity-projected milling tangent (A3 — reduces to the 2D fixed-axis prescription in the planar limit but produces spherical-shell configurations in 3D suitable for H2 detection), and synchronous vectorized updates per agent step (A7, preserving the 2D and standard-flocking convention; Reynolds 1987, Vicsek et al. 1995). Initial conditions place agents uniformly in the box with velocities drawn uniformly on the unit 2-sphere via inverse-CDF sampling (A4). T = 500 time steps per run, 10 seeds per primary condition, 5 seeds per sensitivity sweep. All randomness is via explicit seeds; under D6 deterministic seeding, runs reproduce bit-identical trajectories for the same seed.

### 3.2 Analysis pipeline

Φ_spectral is computed per window via the Bailey 2026 §3.4 specification, with three estimator implementations available (B6): Kraskov–Stögbauer–Grassberger (KSG) k-nearest-neighbour with k = 5 and Chebyshev metric (primary; restored from the 2D code's Gaussian default); histogram with 8 bins per channel (sensitivity check, sign-only interpretation per D11 because the $8^4$ = 4096-cell joint symbol space exceeds W = 40 samples and saturates plug-in MI at log(W) ≈ 3.69); and Gaussian closed-form (retained for 2D-to-3D direct comparability). Per-agent per-channel within-window standardization (D3) is an explicit step in `mi.py`, with a dedicated test verifying mean-0 std-1 outputs along the W-axis. Tie-breaking noise (~U(−1e-10, 1e-10)) is added to continuous features before k-NN estimation per Kraskov et al. (2004) standard practice.

Per-window MI matrices feed `spectral.py`: the normalized Laplacian `L = I − D^{−1/2} W D^{−1/2}` is constructed; eigendecomposition via `np.linalg.eigh` produces the second-smallest-eigenvalue eigenvector (the Fiedler vector), sign-thresholded with a deterministic first-non-zero-positive convention; Φ_spectral is the unnormalized MI cut sum across the resulting bipartition, in nats. The auxiliary observable `phi_norm = Φ_spectral / cross_edges` removes the cut-size component and isolates per-edge MI magnitude.

The TDA pipeline (Phase 3, B4) extends Bailey 2026 §3.5's Ripser-based persistence computation to maxdim = 2, producing eight new H2 columns alongside the H0/H1 columns from the 2D pipeline (`snap_TP_2`, `snap_MP_2`, `snap_B_base_2`, `traj_TP_2`, `traj_MP_2`, `traj_B_base_2`, plus prev-versions). The primary spatial-snapshot TDA observables are `snap_TP_1` (jamming primary positive control per Phase 4) and `snap_TP_0` (split-merge probe; D13 documents that the snap_TP_0 split-merge direction does not replicate at 10 seeds). H2 is exploratory in 3D at N = 40 because the spherical-shell milling configuration (R ≈ 11, shell thickness ≈ 0.7) puts enclosed voids below Rips filtration resolution (D9); H2 is reported but not used as pass/fail.

Per-window aggregation produces Parquet files under `outputs/<sweep>/<condition>/seed*/*.parquet`; these are byte-stable across re-runs under D6 and are the canonical data substrate for all Tier 1, 2, and 3 analyses.

### 3.3 Bimodality methodology

Per Phase 5 D14's reporting requirement, bimodality of the per-window Φ distribution is computed on **steady-state-only pooling**: window indices `$\geq$ quantile(2/3)` per seed, pooled across all 10 seeds (~31 windows per seed  \times  10 seeds ≈ 310 windows per condition; ~155 for n=5 sensitivity sweeps). The Tier 1.B audit (commit `4f821ae`) established this convention after the Tier 1.A all-windows pooling produced different bimodality classifications for `leadership λ = 0.8` (modes = 2, dip p = 0.13 on all-windows; modes = 1, dip p = 0.91 on steady-state-only) — the apparent bimodality on the all-windows pool was a transient-mixing artefact rather than within-steady-state bimodality.

The bimodality criterion is `dip p < 0.20` (Hartigan dip test) AND `KDE mode count $\geq$ 2` (Gaussian-kernel KDE with default bandwidth). Conditions with `modes $\geq$ 2` but `dip p $\geq$ 0.20` are heavy-tailed unimodal-with-shoulder, not statistically bimodal at this n; they are reported for transparency but excluded from the §4.2 candidate set. The std/IQR ratio is reported as a secondary heavy-tailedness indicator.

### 3.4 Cross-sweep aggregation

The Tier 2.C aggregation (commit `f0ad4aa`, `outputs/comparison/cross_sweep/scenario_summary.csv`, 38 rows) collapses the 11 sweep families  \times  per-condition combinations into a single fact sheet with Φ cross-seed mean and 95% bootstrap CI (1000 resamples on per-seed steady-state means per D2), σ_u where Tier 1.C re-computed it (alignment, jamming, leadership, noise sweeps), bimodality diagnostics, and surrogate z-scores where Tier 2.B tested.

The **vanilla-baseline collapse** is a Tier 1.C-derived design choice (`audit_aggregates.json::vanilla_baseline_equivalence`). Eight conditions across the 11 sweeps are byte-identical runs that all reduce to vanilla boids at their respective boundary values under D6 deterministic seeding: five at n = 10 (`jamming α = 1.0`, `leader λ = 0.0`, `milling μ = 0.0`, `noise σ = 0.05`, `split_merge none`) and three at n = 5 sensitivity-defaults (`w_sensitivity W40`, `alignment_rule_sensitivity mean`, `sensitivity ksg_kinematic`). These are byte-identical because (i) `jamming α = 1.0` multiplies all weights by 1.0 (IEEE 754 identity), (ii) `leader λ = 0.0` produces zero leader force without altering the v_tilde representation (IEEE 754 `x + ±0.0 = x`), (iii) `milling μ = 0.0` returns zero force per agent, and (iv) the unconditional RNG draws produce identical state at every step regardless of `scenario_name`. Cross-scenario agreement statistics in Tier 2.C must collapse these eight conditions to a single `vanilla_baseline` entry — otherwise pairs containing any two of the eight inflate Spearman ρ artifically. The Tier 2.C `scenario_summary.csv` carries the collapsed entry as row 37 (`sweep = "multiple"`, `condition = "vanilla_baseline"`, with `shared_baseline_alias` listing the eight collapsed conditions).

Per-sweep η² with bootstrap CIs follows the D2 protocol (1000 resamples on per-seed values); histogram-estimator η² columns are reported with the D11 sign-only flag.

### 3.5 Surrogate-method validation history

The Tier 2.B surrogate analysis runs circular-shift nulls (D1, Phase5.md): for each of seven primary scenarios + `none` baseline, on simulation seed 0, 10 surrogate shuffles per run, with each agent's telemetry independently circularly shifted by a uniform random offset over `[0, T)`. Marginal distributions per agent are preserved exactly; cross-agent temporal dependence is destroyed.

The method-validation history is documented in `outputs/surrogates/README_summary.md`. Three positive-control attempts were made:

**Attempt 1 — noise σ = 0.5 designed positive control: failed (z = 17.58).** Phase5.md §141 pre-registered noise σ = 0.5 as the surrogate-method positive control on the assumption that a high-noise condition would produce near-random telemetry and observed Φ ≈ surrogate Φ. The Tier 2.B run produced observed Φ = 82.07 vs surrogate mean 70.86 (95% CI [70.26, 72.11]), z = 17.58 — observed substantially above null. Diagnosis: the boids dynamics at σ = 0.5 with `w_a = 1.0` and `vision_radius = 10.0` *retain real cross-agent temporal structure* (observed polarization = 0.46). The shuffle is working correctly; the sanity-check assumption did not hold. The σ = 0.5 condition is a science finding (a moderately disordered boids regime that nevertheless integrates information cross-agent), not a method-validation entry. Discussed in §4 below relative to Figure 6.

**Attempt 2 — disabled-interaction simulator control: failed at the boundary-synchrony floor (z = 3.12).** A control run with all boid weights set to zero (`w_a = w_c = w_s = 0`, scenario `none`) produced z = 3.12 — observed Φ slightly above surrogate. With no boid forces, agents move ballistically except where the reflective box walls reverse their velocity. Wall reflections create correlated velocity reversals (u-component sign-flips) across agents occupying similar regions of the 50³ box; this is a genuine cross-agent statistical dependence arising from boundary geometry rather than from the boids dynamics. Circular-shift cannot remove it because it is real per-agent autocorrelation driven by shared boundary-reflection events, not a temporal-offset artefact. The z = 3.12 is preserved as a **model-level boundary-synchrony floor**, not a surrogate-method bias: any per-scenario z $\leq$ 3.12 is ambiguous between real cross-agent integration and boundary-synchrony inheritance. All eight science-scenario z-scores exceed this floor by a comfortable margin (the smallest positive z is 8.38 at leadership λ = 1.6).

**Attempt 3 — synthetic per-agent AR(1) i.i.d. control: passed (z = −0.53).** A telemetry generator that fits a per-agent AR(1) process to the disabled-interaction base data and bootstraps each agent's time series independently (no cross-agent dependence by construction) produced observed Φ = 51.003, surrogate 95% CI = [50.687, 51.565], z = −0.53 — observed within the surrogate 95% CI. The circular-shift surrogate correctly identifies data with no cross-agent temporal structure. Method validated. The eight per-scenario nulls (commit `2603b83`) are interpretable as written.

The pre-registered Phase5.md §141 framing of noise σ = 0.5 as the method positive control is therefore reclassified post-hoc: the noise σ = 0.5 condition is a science scenario, not a method-validation entry. Figure 6 (surrogate null comparison) renders noise σ = 0.5 alongside the seven other science scenarios; its bar represents a real cross-agent integration finding (consistent with Bailey & Schneider's prediction that boids retain partial coordination at moderate noise) emerging from a failed methodological assumption. The reclassification is documented honestly in the Tier 2.B README and is a small but real contribution of the Phase 5 surrogate work; it is not a method failure.

### 3.6 Multi-Claude session structure

Phase 5 was executed across nine Claude Code sessions (Phase5.md §"Session structure"): an Opus-max planning chat producing the Phase5.md scoping document, then alternating Opus and Sonnet execution sessions for Tier 1 (Opus 4.7 max for 1.A and 1.C interpretation; Sonnet 4.6 for 1.B mechanical atlas), Tier 2 (Sonnet 4.6 throughout — comparison-pipeline porting, surrogate implementation, aggregation runs), and Tier 3 (Opus 4.7 xhigh for figure composition; Sonnet 4.6 for figure rendering and animation generation; Opus 4.7 max for this report draft). The model-allocation discipline was: Sonnet for engineering and mechanical orchestration; Opus for bounded interpretive synthesis where reasoning depth on uncertainty discipline matters most. Each session ended with a commit + push and a verdict document that the next session consumed as input. The orchestration pattern is methodologically reproducible — the prompts that produced each session's deliverable are in the project's session-log channel (not committed to the repo, but available on request).

This multi-session execution model is itself a methodological choice worth noting: the "interpretation-first" Tier 1 ordering (Opus interpretation before Sonnet code work) was specifically designed to surface the Outcome 4 finding before any Tier 2 code was written, so that downstream tier scope could be conditionally narrowed (Tier 1.B narrower atlas; Tier 3.A figure composition reorganized around the three-mechanism finding rather than a compressibility-as-headline structure). The acknowledged tradeoff (interpretive calls on data that has not yet been through the full comparison pipeline) was judged acceptable because the histogram-estimator sign-only stance per D11 means the Tier 2.A re-runs cannot contradict Tier 1's KSG+Gaussian agreement; if Tier 2 had surfaced a contradiction, the correct response was to pause Tier 3 and re-examine Tier 1, not to paper over the contradiction. Tier 2.C did not surface such a contradiction.

---

## §4 — Results: §4.2 transitional Φ peak

The Bailey & Schneider §4.2 prediction has two sub-components: (i) **per-window Φ bimodality** at the disorder-to-order regime boundary, with the bimodal mean falling between the random and synchronized endpoint means; and (ii) when the random endpoint is genuinely B&S-random (independent dynamics, low MI), the **mean Φ peaks** at the transitional condition above both endpoints. The Phase 5 cross-sweep audit (Tier 1.C, commit `fec6079`) identifies two confirmed instances of this prediction across orthogonal perturbation axes — alignment coupling and additive noise — and addresses one prose-engagement item that distinguishes them empirically: the alignment instance can test the bimodality component but not the mean-peak component cleanly, while the noise instance tests both.

### 4.1 Bimodality at alignment w_a = 0.6

The Tier 1.B atlas (commit `4f821ae`) identified `alignment_sweep` `w_a = 0.6` as the only steady-state-pooled bimodal condition in its eight-condition scope: dip p = 0.102, KDE modes = 2, std/IQR = 0.551, n = 310 windows pooled across 10 seeds. Cross-seed mean Φ = 138.73 (95% CI [116.55, 160.50]), with cross-seed σ_u = 0.5201 sitting between the disordered endpoint (`w_a = 0.0`, σ_u = 0.7941) and the coherent endpoint (`w_a = 1.2`, σ_u = 0.5061). The bimodality signature is visually evident in `outputs/figures/composition/primary/fig1_three_mechanism_panel.png` (Row 1, Column 2): two distinct peaks separated by a visible dip in the per-window Φ histogram. Mechanistically, this is the §4.2 within-window-bimodality prediction: at moderate alignment coupling, the synchronized flock alternates window-by-window between turning/realignment events (high σ_u, high MI) and steady-flight intervals (low σ_u, low MI), producing the bimodal per-window Φ that B&S §4.2 expects at the transitional regime.

### 4.2 Bimodality and mean-peak at noise σ = 0.2

The Tier 1.C cross-sweep audit identified `noise_sweep` `σ = 0.2` as a second §4.2 instance with empirical evidence at least as strong as the alignment instance, and on one component (mean-peak) considerably stronger. The bimodality signature is the strongest in the entire 11-sweep audit: dip p = $7.6 \times 10^{-6}$ (four orders of magnitude beyond the 0.20 criterion threshold), KDE modes = 2, std/IQR = 0.544, n = 310 windows pooled across 10 seeds. The two modes are unambiguous in the per-window histogram. Cross-seed mean Φ = 144.63 (95% CI [125.58, 163.49]).

Crucially, the **mean-Φ-peak component is satisfied** at noise σ = 0.2:

| Condition       | Cross-seed Φ mean | 95% CI                |
|---|---|---|
| `σ = 0.0` (synchronized endpoint, no noise) | 129.65 | [121.32, 137.91] |
| `σ = 0.05` (vanilla baseline †)              | 135.05 | [115.95, 155.30] |
| `σ = 0.1`                                   | 128.50 | [110.91, 147.00] |
| **`σ = 0.2` (transitional, bimodal)**       | **144.63** | [125.58, 163.49] |
| `σ = 0.5` (random endpoint, high noise)     | 85.03 | [77.33, 92.92]   |

Φ at σ = 0.2 exceeds Φ at every neighbouring noise condition AND both endpoints: +11.5% above the synchronized endpoint and +70.2% above the random endpoint. The mean-peak signature is mild in absolute terms relative to the synchronized endpoint (the per-condition CIs at σ = 0.05 and σ = 0.2 overlap, so disjoint-CI confirmation does not hold at the strict-disjoint level), but unambiguous in direction across the full sweep. The dip p = $7.6 \times 10^{-6}$ is the load-bearing signal — the within-window bimodality is what the §4.2 prediction primarily concerns, and the mean-peak corroborates it without single-handedly carrying the verdict.

### 4.3 Methodological asymmetry between the two §4.2 instances

The two confirmed §4.2 instances are not equally clean methodologically. This is the first of the four prose-engagement items the figure review surfaced and is a disclosure that strengthens credibility rather than weakening it.

The **noise σ = 0.2 instance is methodologically clean** on three counts:

1. The bimodality dip test result (p = $7.6 \times 10^{-6}$) is four orders of magnitude stronger than at alignment w_a = 0.6 (p = 0.102).
2. The mean-Φ-peak component is testable because the noise sweep's disordered endpoint (σ = 0.5, Φ = 85.03) is genuinely B&S-random in the Bailey & Schneider sense — high additive velocity noise washes out cross-agent coupling and produces low-MI dynamics, exactly the random regime §4.2 expects to compare against.
3. The σ_u progression across the noise sweep (σ = 0.0: 0.5148 → σ = 0.2: 0.5311 → σ = 0.5: 0.6421) sits the transitional condition cleanly between the synchronized and disordered endpoints.

The **alignment w_a = 0.6 instance can only test the bimodality component** because the alignment sweep's disordered endpoint (`w_a = 0.0`) is *not* B&S-random in this 3D model. At w_a = 0 the swarm still has non-zero cohesion and separation forces, which produce structured pairwise dynamics with high MI even without alignment coupling. The cross-seed Φ at w_a = 0.0 is 361.16 — three times the transitional Φ — which is the *opposite* direction the §4.2 mean-peak prediction would expect. The Tier 1.C audit's high-w_a non-monotonicity check verified that the alignment-sweep coherent endpoint is plateaued (`Φ(w_a = 1.2) = 117.98`, `Φ(w_a = 1.8) = 118.07`, difference +0.089 with bootstrap CI [−28.98, +29.65], Cohen's d = +0.002 — null), so the §4.3 inversion is not visible on the alignment axis at the sampled w_a values either. The alignment sweep's disordered-endpoint complication is intrinsic to the C1 sweep design (the alignment sweep is a *coupling-strength* axis, not a *noise* axis), not a defect; it limits what §4.2 component can be tested but does not invalidate the bimodality finding.

The two-instance verification is therefore strongest as a **bimodality-signature** result across two orthogonal perturbation axes (deterministic coupling + stochastic noise), with the mean-peak component additionally satisfied on the cleaner of the two. The Phase 5 internal report does not flatten this asymmetry: the noise instance is the methodologically cleaner of the two, and that is the point — the convergence of evidence comes from two independent perturbation axes producing the same within-window bimodal signature, with one of them additionally satisfying the more stringent mean-peak criterion.

### 4.4 Surrogate corroboration

Tier 2.B's circular-shift surrogate test was originally run on seven primary scenarios + `none` baseline; alignment w_a = 1.8 (the coherent endpoint) was included but alignment w_a = 0.6 was not. A targeted follow-up session (commit `f8f7ea5`) added the alignment w_a = 0.6 surrogate test post-Tier-1.C audit. Both confirmed §4.2 instances now have surrogate corroboration at near-identical z-scores. **Note on aggregation**: the surrogate test operates on simulation seed 0 per D1 (single-seed protocol pre-committed for reproducibility); the cross-seed Φ values cited elsewhere in §4 (e.g., Φ = 144.63 for noise σ = 0.2 in §4.2) come from 10-seed pooling on per-window steady-state means. The two are not directly comparable as observed-Φ values; the surrogate result corroborates the §4.2 verdict at the *single-seed* level, which is the standard surrogate-analysis protocol but is a narrower claim than the cross-seed bimodality result.

| Instance               | Observed Φ (seed 0) | Surrogate mean ± 95% CI     | z    |
|---|---|---|---|
| `alignment w_a = 0.6` (§4.2)  | 166.15    | 116.08 [114.04, 118.53] | **32.91** |
| `noise σ = 0.2` (§4.2)        | 150.12    | 109.94 [108.63, 111.53] | **32.92** |

These are the strongest above-null z-scores in the entire eight-scenario surrogate set. The near-identical z values are a coincidence of the single-seed (seed 0 per D1 protocol) computation, but their order-of-magnitude agreement with the Tier 1.C bimodality finding is consistent: both instances exhibit strong within-window heterogeneity that circular-shift destroys, and the resulting observed-Φ excess over null is large because the per-window high-Φ wobble episodes contribute disproportionately. Both z-scores exceed the boundary-synchrony floor (z = 3.12) by an order of magnitude. Figure 6 (`fig6_surrogate_null_comparison.png`) renders both instances side by side; the two §4.2 bars are visually indistinguishable from one another at this resolution.

The surrogate corroboration also strengthens the *framing-(b)* reading per D14 §139: even when the mean-over-windows Φ is bimodal (mixing high and low windows), the per-window dynamical structure is detectable *against* the temporal-independence null, which means Φ_spectral measures genuine within-window informational dependence rather than a mean-level artefact.

### 4.5 §4.2 verdict

The §4.2 transitional Φ peak prediction is **confirmed across two orthogonal perturbation axes**, with the noise instance being methodologically cleaner. The bimodality-signature component is satisfied at both instances; the mean-peak component is satisfied at noise σ = 0.2 and is not testable at alignment w_a = 0.6 because the alignment sweep's disordered endpoint is not B&S-random. The two-instance count exceeds the Phase 5 pre-registration's single-instance expectation. The strongest single-pieces of empirical evidence are dip p = $7.6 \times 10^{-6}$ at noise σ = 0.2 (Tier 1.C) and surrogate z = 32.92 at the same condition (Tier 2.B). Mechanistically, both instances are consistent with §4.2's prediction that the disorder-to-order transitional regime alternates window-by-window between high-σ_u turning episodes and low-σ_u steady-flight episodes, producing bimodal per-window Φ. The figure references are: `fig1_three_mechanism_panel.png` (Row 1, Columns 1–2 for the per-window distributions; Columns 3–4 for cross-condition Φ ordering across the noise and alignment sweeps), `fig6_surrogate_null_comparison.png` (both instances visible at z ≈ 32.9), and the supplementary `fig3_sensitivity_alignment_sweep.png` and `fig3_sensitivity_noise_sweep.png` for per-sweep η² rankings.

---

## §5 — Results: §4.3 compressibility-Φ-inversion

The §4.3 prediction is operationally distinct from §4.2: rather than a within-window bimodality at the regime transition, §4.3 predicts a **mean-Φ-inversion** at a moderately disordered regime that prevents the coherent regime's compressibility. The signature is fourfold (per the A2 jamming reference, commit `cc23aa9`): σ_u floor-locked at moderate elevation above the coherent baseline; phi_norm cross-seed σ strongly reduced (jamming regularizes Φ across seeds); per-window Φ unimodal-narrow (no flipping between high-MI wobble windows and low-MI steady-flight windows); and **mean Φ inverted above the same sweep's coherent baseline**. This is the headline §4.3 prediction: a coherent regime registers lower Φ than a moderately disordered regime via compressibility.

### 5.1 Mean-Φ-inversion at jamming α = 0.2

The canonical §4.3 verification is the inversion comparison:

| Condition                              | Cross-seed Φ mean | 95% CI                   |
|---|---|---|
| `jamming α = 0.2` (§4.3 instance)             | **187.23** | [181.61, 193.74]     |
| `jamming α = 1.0` (= vanilla baseline †) | 135.05 | [115.95, 155.30]   |
| Inversion magnitude                    | **+38.6%**         | CIs disjoint   |

Φ at jamming α = 0.2 is 187.23 ± 6 (cross-seed bootstrap CI), substantially above the same-sweep coherent baseline of 135.05. The Tier 2.C aggregation table (`scenario_summary.csv` row 5) reports the same numbers; the Tier 2.C inversion comparison is therefore a baseline-alias verification of the A2 finding using the canonical vanilla-baseline collapse rather than an independent re-derivation. The per-condition CIs do not overlap: the inversion is robust at the n = 10 seed level. Mechanistically, the A2 diagnostic established that under α = 0.2 the MI matrix is *uniformly elevated* (MI mean = 0.491, ρ(MI, −distance) = +0.10, near-chance) — every pair has substantial MI because every agent is forced to continually wobble at moderate within-window σ_u. Under α = 1.0 (coherent), the MI matrix is low-magnitude (MI mean = 0.099) and *spatially patterned* (ρ(MI, −distance) = +0.40), with the coherent flock spending substantial time in low-entropy steady-flight windows where pairwise MI collapses. The mean-over-windows Φ inverts.

### 5.2 σ_u floor-locked moderate at α = 0.2

The proximate driver of the inversion is **within-window dynamic amplitude** (σ_u). At α = 0.2, σ_u = 0.5925 — floor-locked above the coherent baseline's σ_u = 0.5183, because the 80% alignment loss forces agents to continually wobble (they cannot lock onto a mean direction). The per-channel raw within-agent directional std at α = 0.2 ranges 0.17–0.26 across seeds and windows (A2 §3); at α = 1.0 it ranges 0.10–0.28 with a heavy distribution toward the low end where steady-flight windows dominate. The σ_u definition used in the cross-sweep audit is the per-agent L2 norm of per-channel velocity-direction stds (~√3 times the per-channel value for direction-isotropic motion), so quantitative comparison to A2's per-channel numbers requires the conversion factor; values within the audit are mutually consistent and the relative ordering (jamming α = 0.2 > jamming α = 1.0) holds in either definition.

The σ_u observable is the load-bearing operational discriminator for §4.3. A condition that prevents compressibility *must* keep σ_u floor-locked above the coherent baseline; any condition where σ_u is at or below the baseline is (by definition) not preventing compressibility. The leadership Outcome 4 verdict (§6 below) leans on this: at λ = 2.4, σ_u is 0.6030 — only slightly above the coherent baseline (0.5183) and not floor-locked at the mechanism level — and the Φ collapse there is therefore not via compressibility.

### 5.3 phi_norm cross-seed σ compressed at α = 0.2

The secondary §4.3 signature is **phi_norm cross-seed σ reduction**. The per-edge MI normalization (phi_norm = Φ_spectral / cross_edges) removes the cut-size component and isolates per-edge MI magnitude; under jamming, the across-seed variance of phi_norm drops because every seed produces the same uniformly-wobbly dynamics (the system cannot collapse into a steady-flight low). The Tier 1.C audit reports phi_norm cross-seed σ = 0.0268 at α = 0.2 vs 0.0911 at α = 1.0 (a factor of 3.4 reduction). The Tier 2.C table records phi_norm σ = 0.027 at α = 0.2 (slightly different rounding); both numbers describe the same effect. This is the "jamming regularizes Φ while coherence bimodalizes it" signature: the coherent baseline's phi_norm σ is high because seeds split between wobbly turning windows (high phi_norm) and steady-flight windows (low phi_norm); the jammed condition's phi_norm σ is low because every seed lives in the wobbly transitional regime.

### 5.4 Surrogate corroboration

Tier 2.B's circular-shift null at jamming α = 0.2 (seed 0) produced observed Φ = 179.87, surrogate mean = 165.64 (95% CI [164.72, 167.06]), z = +16.17 — observed substantially above null. This confirms that the elevated Φ at α = 0.2 reflects real cross-agent integration rather than a confound, and is fully consistent with the §4.3 prediction.

A subtle interpretive point: the mean-over-windows surrogate test does not directly test §4.3 (which is defined as inversion *relative to the same sweep's coherent baseline*). It tests whether per-window Φ at α = 0.2 contains real cross-agent temporal structure beyond what temporal independence would produce. The two questions are separate: §4.3 is the inversion comparison (positive); the surrogate test is whether the per-window structure is real (also positive). The two findings are consistent and complementary — per-window structure is real (surrogate test, z = 16.17) AND the mean-Φ ordering is inverted relative to the coherent baseline (the canonical §4.3 verification, +38.6%). The earlier Tier 2.B README note "this is the opposite direction from the §4.3 compressibility prediction — flag for investigation" reflects an incomplete reading: the surrogate test addresses a different question than the inversion comparison, and the §4.3 finding is the inversion, which goes in the predicted direction.

### 5.5 Redundancy-saturation alternative reading and the σ_u discriminator

The mean-Φ-inversion finding at jamming α = 0.2 is, in principle, consistent with two readings: (a) the **§4.3 compressibility prediction** per Bailey & Schneider 2025 — coherent regimes spend time in low-entropy steady-flight windows that pull mean Φ down, and conditions that prevent steady-flight (by floor-locking σ_u) invert the mean; or (b) **redundancy saturation** per Luppi et al. (2024), in which pairwise-MI-based integration measures are disproportionately sensitive to redundant rather than synergistic information, so that a regime which produces broadly redundant pairwise dependence (every agent wobbling against every other) registers high Φ even without a compressibility mechanism in the §4.3 sense. ResearchContext.md L1 names this as a structural limit of the second-order approach.

The two readings predict different empirical signatures. Compressibility specifically predicts **σ_u floor-locked above the coherent baseline** as the proximate driver of the inversion: the mechanism *is* preventing the steady-flight low. Redundancy saturation does not require σ_u floor-locking; it would predict elevated Φ wherever pairwise dependence is broadly distributed, regardless of within-window dynamic amplitude. The Phase 5 jamming data show σ_u = 0.5925 at α = 0.2 vs σ_u = 0.5183 at the coherent baseline — floor-locked above the baseline, with the difference robust at the 10-seed CI level. The σ_u progression across the jamming sweep tracks the Φ progression in the predicted direction (σ_u declines monotonically from α = 0.2 → α = 0.5 → α = 1.0; Φ does the same). The §4.3 reading is therefore the empirically supported one for the jamming finding: the σ_u observable is the discriminator, and it favors compressibility specifically over redundancy saturation.

This does not eliminate L1 as a structural limit on the framework. The pairwise-MI redundancy-weighting concern remains in force for any Φ_spectral interpretation that requires distinguishing redundant from synergistic integration; ΦID-grade analysis (per Luppi et al. and as flagged in ResearchContext.md §4.1) would address L1 directly. What the Phase 5 jamming result establishes is that *for this specific instance*, the available evidence (σ_u floor-lock co-located with the inversion) is the §4.3 mechanism and not the redundancy alternative — but the discrimination rests on σ_u rather than on Φ_spectral alone, which is itself a Phase 5 methodological observation worth recording.

### 5.6 §4.3 verdict — jamming-specific despite testing across five mechanism families

The §4.3 compressibility-Φ-inversion is **confirmed at jamming α = 0.2** as the only condition in the cross-sweep set that satisfies all four load-bearing §4.3 descriptors (σ_u floor-locked above coherent baseline, phi_norm cross-seed σ reduced, per-window Φ unimodal-narrow, mean Φ inverted above coherent baseline). The cross-sweep audit's §4.3 sub-table (Tier 1.C) tested every plausible candidate; only `jamming α = 0.5` is partially present (σ_u = 0.5331, phi_norm σ = 0.0441, +4% Φ vs α = 1.0 — an intermediate compressibility regime, not a confirmed instance). The remaining four mechanism families each fail with a mechanistically defensible reason:

- `alignment w_a = 0.0`: σ_u = 0.7941 sits in the disordered-random regime rather than floor-locked moderate; the structure at this condition is "no alignment force, cohesion+separation produce pairwise structure," not compressibility prevention.
- `leader λ = 1.6` and `λ = 2.4`: Φ inverts in the *opposite* direction (collapse below baseline, not above) via the leader-block partition mechanism documented in §6 — a structurally distinct phenomenon, not §4.3.
- `noise σ = 0.5`: Φ drops at the random endpoint as the §4.2 prediction expects of a B&S-random regime; the noise sweep tests the transitional-peak prediction, not the compressibility-inversion prediction.
- `split_merge`: observed Φ falls *below* the coherent baseline rather than above, the wrong direction for §4.3; the surrogate-level z = −5.08 is mechanistically a flock-dissolution finding rather than a compressibility-prevention finding (see §8.3).

The empirical verdict is therefore not "we only tested one sweep where it worked" but **"§4.3 is jamming-specific despite testing across five orthogonal mechanism families, with each non-confirmation accounted for mechanistically."** This is methodologically honest scope-narrowing and is the empirically stronger framing: the original Phase 5 pre-registration anticipated a multi-sweep §4.3 generalization, and the framework's empirical reach is narrower than that hope but is established by direct testing rather than by absence of evidence. The Phase 5 result is stronger, not weaker, for shipping a tested-and-disconfirmed leadership extension alongside the confirmed primary claim: ambiguity in either direction would have been a less defensible posture.

The figure references are: `fig1_three_mechanism_panel.png` (Row 2: Columns 1–2 for the per-window Φ distributions at α = 0.2 and α = 1.0; Column 3 for the +38.6% inversion across the jamming sweep; Column 4 for the σ_u and phi_norm σ twin-axis showing the mechanism-level signature), `fig5_deltas_jamming.png` for the matched-control deltas during the [200, 400] jam interval, and the supplementary `outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md` for the canonical mechanism-level reference (MI matrix structure, eigenvalue gap, ρ(MI, distance)).

---

## §6 — Results: leadership Outcome 4 and the leader-block partition mechanism

The Phase 5 pre-registered prediction was that the leadership sweep at high λ would produce a third compressibility instance via leader-group compactness compressing within-window σ_u and pulling mean Φ down despite visible structural organization (Phase5.md Tier 1.A). The Tier 1.A analysis (commit `9ad6a5a`, Opus 4.7 max effort) tested this prediction across all 10 seeds at λ $\in$ {0.0, 0.8, 1.6, 2.4} with explicit MI-matrix mechanism diagnostics. The verdict is **Outcome 4**: Φ does collapse at high λ, but the mechanism is **leader-vs-follower block structure** rather than uniform-MI compressibility. The Φ collapse is real but it is a different mechanism from §4.3. This section documents what was found, what makes it mechanistically distinct from §4.3, and how Phase 5 reports the result honestly as scope-narrowing.

### 6.1 Φ collapse at λ $\geq$ 1.6 confirmed directionally

Per-condition cross-seed means (Tier 1.A `aggregates.json`, n = 10 seeds per condition):

| Condition | Φ_spectral (95% CI) | σ_u (95% CI) | leader compactness (95% CI) | polarization | phi_norm cross-seed σ |
|---|---|---|---|---|---|
| `λ = 0.0` (= vanilla †) | 135.05 [115.95, 155.30] | 0.518 [0.498, 0.538] | 19.94 [10.98, 25.51] | 0.725 | 0.0911 |
| `λ = 0.8`               | 113.35 [68.96, 158.64]  | 0.701 [0.642, 0.761] | 1.61 [1.45, 1.74]   | 0.663 | 0.2084 |
| `λ = 1.6`               | **6.94** [5.41, 8.45]  | 0.619 [0.602, 0.635] | 0.141 [0.133, 0.154] | 0.605 | **0.0097** |
| `λ = 2.4`               | **8.73** [4.03, 15.19] | 0.603 [0.588, 0.618] | 0.226 [0.150, 0.337] | 0.579 | 0.0328 |

Φ drops dramatically at high λ: from 135.05 at λ = 0.0 to 8.73 at λ = 2.4 (Cohen's d = +5.0, CIs disjoint). Φ at λ = 1.6 vs λ = 2.4 is statistically indistinguishable (d = −0.25, bootstrap CI on the difference brackets zero, per-condition CIs overlap). Leader compactness collapses across the same axis (19.94 → 1.61 → 0.141 → 0.226), confirming that the high-λ regime produces a tight leader cluster as the prediction anticipated.

But the proximate compressibility driver — within-window σ_u — is **not compressed**. σ_u at λ = 2.4 is 0.603, slightly *higher* than at λ = 0.0 (0.518) and well below the peak at λ = 0.8 (0.701). The original prediction was that σ_u would be compressed at high λ as the proximate cause of the Φ collapse; the data falsify that proximate claim directly.

### 6.2 The mechanism: leader-vs-follower block structure

The Tier 1.A mechanism diagnostic — explicit MI matrix inspection at representative steady-state windows — discriminates Outcome 1 from Outcome 4. For each of λ = 0.0 and λ = 2.4, a representative seed (whose per-seed steady-state Φ is closest to the cross-seed median) and window (whose Φ is closest to that seed's mean) was selected, and the MI matrix recomputed via the canonical pipeline (`extract_features` → `standardize_window` → `mi_matrix_ksg`). The recomputed Φ matches the published parquet bit-for-bit.

The descriptor comparison against the A2 reference shows three of four compressibility descriptors fail at λ = 2.4:

| Descriptor                            | A2 α = 0.2 (compressibility) | A2 α = 1.0 (coherent) | λ = 0.0 (this study) | **λ = 2.4 (this study)** |
|---|---|---|---|---|
| MI mean                               | 0.491 | 0.099 | 0.414 | **0.188** |
| Spearman ρ(MI, −distance)             | +0.10 | +0.40 | +0.32 | **+0.30** |
| Fiedler $\leftrightarrow$ kmeans-2 pair agreement     | 0.50 (chance) | 0.78 | 0.90 | **0.49** |
| MI top-eig gap (top1 − top2)          | 18.7  | 1.77  | 15.6  | **7.4**   |

At λ = 2.4: MI mean is **low** (0.19, closer to coherent's 0.10 than to compressibility's 0.49); spatial dependence ρ(MI, −distance) is **moderate-strong** (+0.30, not compressibility's near-zero $\lesssim$ 0.15); the eigenvalue gap is **intermediate** (7.4, well below compressibility's rank-1-dominated 18.7); and Fiedler $\leftrightarrow$ kmeans-2 agreement is at chance (0.49).

But Fiedler agreement at chance is for a different reason than under jamming. Direct inspection of the partition shows that at λ = 2.4 the **Fiedler bipartition splits leaders from followers perfectly**: 8 leaders in one part, 32 followers in the other; Fiedler-vs-leader-membership pair agreement = **1.000** (perfect). The kmeans-2 spatial bipartition gives a different cut — it splits the swarm geometrically, ignoring functional role (kmeans-2-vs-leader-membership pair agreement = 0.49). The two methods disagree because the MI matrix is **block-structured around the leader cluster**, not uniform: the 8 leaders share high MI with each other (tight group, common waypoint pull), and the bulk follower-follower MI is low. The spatial bipartition cuts the geometric extent of the swarm; the Fiedler cut isolates the dense leader block. Φ_spectral collapses because the cross-cut sum is composed of the low leader-to-follower MI edges that connect the dense leader block to the sparse follower bulk.

This is the **block-structured pattern** the Outcome 4 framing explicitly warned about ("any pattern distinct from uniform elevation"), produced by a different mechanism than A2 compressibility. Compressibility produces *uniform MI* because it floor-locks every agent into wobbly dynamics; leader-block partition produces *block-structured MI* because high λ creates two functionally distinct populations with very different dynamic profiles. The two mechanisms are structurally distinct.

### 6.3 Distinction from §4.3 — addressing prose-engagement item 2

The figure-set primary panel (`fig1_three_mechanism_panel.png` Row 3, Column 4) renders the MI matrix at λ = 2.4 with leaders ordered first and a white-dashed separator marking the leader/follower partition; the 8 \times 8 high-MI block in the upper-left and the sparse 32$\times$32 follower bulk are visible in the heatmap. The standalone diagnostic figure (`outputs/tier1_compressibility/mi_matrix_diagnostic.png`, commit `9ad6a5a`) shows the same matrix in side-by-side λ = 0 vs λ = 2.4 contrast — at λ = 0 the MI matrix is uniformly high-MI in a coherent flock; at λ = 2.4 the matrix is block-structured with the leader cluster visually distinct from the follower bulk. The side-by-side rendering makes the structural distinction unambiguous in a way the single-panel rendering cannot.

This report references **both** figures: the integrated three-mechanism panel (`fig1` Row 3 Col 4) for the headline narrative position alongside §4.2 and §4.3, and the standalone diagnostic for the comprehensive side-by-side mechanism contrast. This is the second prose-engagement item from the figure review: the standalone diagnostic should be staged into `outputs/figures/composition/supplementary/` for a self-contained figure set (a planning-level recommendation in §10 below; this report does not take that action).

The mechanistic distinction matters operationally. The cross-sweep `(σ_u, phi_norm σ)` coordinate space places leadership λ $\geq$ 1.6 in the bottom-left quadrant, looking superficially similar to the A2 jamming reference (both have σ_u in the 0.6 range and phi_norm σ in the 0.01–0.03 range). A naive reading on those two coordinates alone would classify leadership-high-λ as a §4.3 instance. But Φ at high λ is **far below** the leadership coherent baseline (8 vs 135), the *opposite* direction of §4.3's coherent-baseline-inversion. The cross-sweep verdict therefore requires the Φ-direction-of-inversion AND the per-window Φ shape AND the MI matrix structure diagnostic together. The (σ_u, phi_norm σ) coordinate alone does not classify a condition as §4.3.

### 6.4 Outcome 4 verdict

Leadership Φ collapse is a real empirical phenomenon at λ $\geq$ 1.6 but it is **not a §4.3 instance**. The original D14 generalization claim (compressibility as a general mechanism across multiple sweeps) is disconfirmed for the leadership axis. The framework's empirical reach is jamming for §4.3, not jamming + leadership.

The leader-block partition mechanism is a separate empirical contribution. It was not pre-registered as a finding (the pre-registration anticipated a third compressibility instance, not a structurally distinct mechanism). It emerges from running the explicit mechanism diagnostic that Outcome 4 was designed to surface. The diagnostic's perfect Fiedler $\leftrightarrow$ leader-membership agreement (= 1.000) is a single load-bearing fact that the cross-sweep picture cannot produce on its own; it requires direct MI matrix inspection at a representative window. This is one place where the Phase 5 design's "interpretation-first" Tier 1 ordering pays off methodologically: had the cross-sweep aggregation been run first without the per-window MI matrix mechanism diagnostic, the leadership high-λ result might have been classified as a §4.3 instance on the (σ_u, phi_norm σ) coordinate alone.

The figure references are: `fig1_three_mechanism_panel.png` Row 3 (per-window Φ distribution at λ = 2.4 vs λ = 0.0; cross-condition Φ ordering across the leadership sweep; MI matrix at λ = 2.4 showing the leader-block structure), `outputs/tier1_compressibility/leadership_panel.png` for the four-panel integrated leadership view, `outputs/tier1_compressibility/mi_matrix_diagnostic.png` for the side-by-side λ = 0 vs λ = 2.4 contrast, and the supplementary `fig8_scenario_snapshots_3d.png` showing the 3D leader-block geometry visually.

---

## §7 — Cross-sweep agreement: spectral vs topological

The Bailey 2026 core hypothesis frames the comparison of spectral and topological methods as a question of when they agree and when they diverge. The Tier 2.C agreement matrix (`outputs/comparison/cross_sweep/scenario_agreement_spearman.csv`, 38 scenarios  \times  18 TDA metrics) captures this: each cell is the Spearman ρ of that scenario's per-window TDA metric series against per-window Φ_spectral. Strong positive correlation means the spectral and topological summaries respond to the same window-level dynamic structure; near-zero or negative correlation means they capture different aspects of the dynamics. Figure 4 (`fig4_agreement_divergence_heatmap.png`) renders this matrix as a heatmap with hierarchical clustering on the 18-column row vectors (Ward linkage) determining the row order.

### 7.1 H2 columns are uniformly weaker than H0/H1

H2 persistent homology is the 3D-specific addition (B4) — H2 captures enclosed voids, a signal meaningful only in dimensions $\geq$ 3. Across the 38-scenario  \times  18-metric matrix, the H2 columns (snap_TP_2, snap_MP_2, snap_B_base_2, traj_TP_2, traj_MP_2, traj_B_base_2) show systematically weaker correlation with Φ_spectral than the H0/H1 columns. This is consistent with D9's Phase 3 finding that H2 at N = 40 on a spherical milling shell falls below Rips filtration resolution (shell-thickness-to-radius ratio puts enclosed voids below detection), and with the demotion of trajectory-cloud TDA in D10. The H2 columns are reported and rendered (Figure 4 caption explicitly emphasizes the H2 column block as the 3D-specific addition) but are not load-bearing for the spectral-topological agreement story at this N.

This is empirical content worth preserving. It is *not* a defect of the H2 implementation — Ripser's `maxdim = 2` runs cleanly and the H2 columns populate without errors. The H2 metric weakness is a finding about the geometric resolution of N = 40 in 3D: a swarm with 40 agents on a spherical shell at R ≈ 11 produces shell thickness ~0.7 and nearest-neighbour spacing ~0.17, which means the void scale (the radius of the enclosed sphere) is at the edge of what Rips filtration can resolve before over-triangulation kicks in. At N = 160 the ratio improves only to 1.55 — still below where H2 detection becomes routine without methodology deviations. The H2 weakness is a *scale finding*, not a *method finding*, and is reported as such.

### 7.2 Hierarchical clustering separates the §4.2 instances — addressing prose-engagement item 4

The figure 4 hierarchical clustering on the 18-column row vectors does *not* group the two confirmed §4.2 instances (alignment w_a = 0.6 and noise σ = 0.2) adjacent. They appear in different parts of the heatmap because their TDA-correlation patterns differ across the 18 metrics. This is the fourth prose-engagement item from the figure review and is substantive content for the cross-sweep comparison.

The two §4.2 instances share the same theoretical mechanism (within-window-bimodality at the disorder-to-order regime boundary) but produce different agreement profiles with topological metrics. Either:

- **(a) This is real empirical content about how the §4.2 mechanism manifests differently under different perturbation types.** Alignment-coupling perturbation introduces structure via the Vicsek mean-velocity rule; noise perturbation introduces it via additive velocity disruption. The within-window dynamics that produce the bimodal Φ are mechanistically the same in both cases (alternation between turning and steady-flight), but the *spatial* configurations during turning and steady-flight differ between the two perturbation types. Topological metrics (especially H1 cluster persistence and H0 connected-component lifetimes) are sensitive to spatial configuration in ways that Φ_spectral is not, so the two §4.2 instances can have similar within-window-Φ statistics but different per-window TDA-vs-Φ correlations. If real, this is an interesting Bailey 2026 hypothesis content: the spectral measure captures the temporal-dependence aspect of transitional regime dynamics; topological measures capture the spatial-configuration aspect; the two aspects can be uncorrelated even when both are responding to the same underlying mechanism.

- **(b) This is noise from the limited n = 10 seeds.** The Spearman correlations are computed per scenario per metric across windows, with seed contributing only via the per-seed parquet aggregation. Sampling noise in the TDA metrics at the per-seed level could produce different correlation profiles between two scenarios that mechanistically should produce similar profiles. Without a finer-grained seed analysis (e.g., per-seed Spearman with bootstrap CIs on the row vector), this possibility is not directly excludable.

The Phase 5 internal report cannot adjudicate (a) vs (b) without additional analysis. The honest treatment is to flag this as a substantive open question worth investigating in Phase 6 (recommendation in §10): a finer-grained seed-level decomposition of the agreement matrix at the two §4.2 instances would test whether the divergent profiles persist beyond sampling noise. If they do, the substantive finding is that **the §4.2 mechanism produces different spatial-configuration signatures under different perturbation types even when the within-window-Φ signatures are mechanistically the same**, which is content for the Bailey 2026 hypothesis. If they do not, the divergence is sampling noise and the Phase 5 report should not foreground it.

For this draft, the report engages explicitly: the figure 4 separation of the two §4.2 instances is reported as a substantive empirical observation worth investigating, not glossed. The two instances are confirmed §4.2 cases on the within-window-Φ-bimodality criterion regardless of how their TDA-correlation profiles compare; the Figure 4 separation is a *secondary* observation that does not affect the §4.2 verdict but does affect the spectral-vs-topological-comparison narrative.

### 7.3 §4.3 agreement profile

The §4.3 instance (jamming α = 0.2) shows strong positive correlations with H0 and H1 metrics. From `monitoring_roc.csv`'s top-AUC entries at jamming α = 0.2: `traj_TP_0` AUC = 0.92, `snap_MP_0` = 0.92, `local_density` = 0.90, `LCC_fraction` = 0.88, `snap_TP_0` = 0.87, `snap_TP_1` = 0.86, `traj_TP_1` = 0.85, `snap_MP_1` = 0.83, `traj_TP_2` = 0.81. This is the strongest cross-method-family agreement in the entire 11-sweep matrix: jamming produces a regime where spectral integration (Φ_spectral) and multiple TDA persistence measures (H0 connected-component lifetimes, H1 cluster persistence, H2 void detection) all elevate together during the [200, 400] jam interval. Mechanistically, this is consistent with §4.3 producing structurally rich within-window dependence that both spectral and topological measures capture: the wobbly transitional regime has high pairwise MI (spectral) and detectable persistent topological features (the jammed flock is geometrically less coherent than the synchronized one, which produces longer-lived H0 components and richer H1 cluster structure). Note the H2 metric (`traj_TP_2`) appears in this top-AUC list at AUC = 0.81 — H2 is not load-bearing for spectral-topological agreement in general, but at the jamming regime where the dynamics are spatially structured enough to admit detectable enclosed-void persistence, H2 contributes meaningfully.

### 7.4 Leader-block partition agreement profile

The leadership Outcome 4 conditions (λ = 0.8, 1.6, 2.4) cluster together in figure 4, which makes empirical sense: the leader-vs-follower structure is detectable to topological methods. The 8-leader cluster produces persistent H1 cycles (the closed loop of the leader cluster's spatial extent), and the leader-vs-follower partition produces detectable H0 component-lifetime asymmetry. Topological metrics that track cluster structure (snap_MP_1 mostly, also snap_TP_1) correlate moderately with Φ_spectral at these conditions because both measures are responding to the partition geometry. This is content for the Bailey 2026 hypothesis: spectral and topological methods agree on regimes where the underlying structure is *spatial cluster-block* (leadership high-λ); they agree on regimes where the underlying structure is *uniform-MI within-window dynamic* (jamming α = 0.2); they may diverge when the underlying structure is *temporal bimodal alternation* (the §4.2 transitional regimes). The §4.2 separation in figure 4 is consistent with this hypothesis if the (a) reading above holds.

### 7.5 Cross-sweep summary

Figure 4 is a primary figure for the spectral-vs-topological comparison story, but its narrative weight is secondary to the three-mechanism-family finding in figure 1. The agreement-divergence pattern across the 38 scenarios is empirically rich and supports the Bailey 2026 hypothesis on its own terms (spectral and topological measures agree on some regimes, diverge on others, with the divergence concentrated where the underlying structure is temporal rather than spatial). The within-method weakness of H2 in 3D at N = 40 is a finding about scale rather than a finding about method, and is documented honestly. The cross-method agreement at jamming is the strongest single block in the matrix and is consistent with §4.3 producing structurally rich within-window dependence detectable to both method families.

---

## §8 — Surrogate analysis

Tier 2.B's circular-shift surrogate analysis (D1) serves three purposes in Phase 5: method validation, §4.2 corroboration, and one exploratory finding worth flagging. The full per-scenario summary table is in `outputs/surrogates/README_summary.md`. This section addresses each role and engages with the third prose-engagement item from the figure review (the noise σ = 0.5 reclassification in figure 6).

### 8.1 Method validation

Tier 2.B's method-validation history (documented in §3.5 above) went through three positive-control attempts before settling: Attempt 1 (noise σ = 0.5) failed because the scenario retained real cross-agent structure; Attempt 2 (disabled-interaction simulator) failed at z = 3.12 due to boundary synchrony; Attempt 3 (synthetic AR(1) i.i.d. control) passed at z = −0.53 within the surrogate 95% CI. The synthetic i.i.d. control is the canonical method-validation entry. The boundary-synchrony floor at z = 3.12 is preserved as a model-level effect, not a method bias.

This is documentation honesty rather than a methodology failure. The surrogate protocol (D1 circular shift, 10 shuffles, marginal distributions preserved per agent) is sound; what failed was the pre-registered choice of noise σ = 0.5 as a control. The reclassification of noise σ = 0.5 as a science scenario rather than a method-validation entry is the correct interpretive move once the empirical evidence (z = 17.58, observed polarization = 0.46 at σ = 0.5) is in.

### 8.2 §4.2 corroboration

Both confirmed §4.2 instances show observed Φ vastly above the surrogate null:

| Instance | Observed Φ | Surrogate 95% CI | z |
|---|---|---|---|
| `alignment w_a = 0.6` | 166.15 | [114.04, 118.53] | **+32.91** |
| `noise σ = 0.2`        | 150.12 | [108.63, 111.53] | **+32.92** |

The two z-scores are the strongest above-null results in the eight-scenario set, and both exceed the boundary-synchrony floor (z = 3.12) by an order of magnitude. The near-identical magnitude is a **single-seed coincidence** rather than evidence of inherent symmetry between the two instances — the surrogate test runs on simulation seed 0 per D1, and the value at any other seed would differ. What the data corroborate is that *both instances independently produce among the strongest above-null z-scores in the surrogate set*; the corroboration is the joint above-null result, not the near-identity. Both instances exhibit strong within-window heterogeneity (the bimodal Φ shape) that circular-shift destroys; the resulting observed-Φ excess is large because the per-window high-Φ wobble episodes contribute disproportionately to the mean. The framing-(b) reading from D14 §139 — that Φ_spectral measures genuine within-window dependence rather than a mean-level artefact — is supported here: even when the mean-over-windows Φ is bimodal, the per-window dynamical structure is detectable against temporal independence.

### 8.3 Exploratory split_merge finding — addressing prose-engagement item 3

The Tier 2.B run for `split_merge_sweep/split_merge` (seed 0) produced a result worth flagging: observed Φ = 129.86, surrogate mean = 139.75, surrogate 95% CI = [136.98, 142.61], **z = −5.08**. Observed *below* surrogate. This is the only scenario in the eight-scenario set with observed-below-null direction.

The direction is consistent with §4.3 compressibility (reduced cross-agent temporal integration relative to the shuffled null), and one could naively classify split_merge as a third §4.3 candidate. But three considerations argue against this classification:

1. **Mean Φ is below the coherent baseline, not above.** Φ at split_merge is 105.41 (cross-seed), versus vanilla baseline 135.05. The §4.3 prediction is *inversion above* the coherent baseline, not below. The split_merge observation goes the wrong direction for a §4.3 instance on the canonical inversion criterion.
2. **σ_u was not computed for split_merge.** The audit's §4.3 sub-table (Tier 1.C) requires σ_u floor-locked above the coherent baseline; without σ_u, the canonical descriptor cannot be evaluated. The Tier 1.C note "(n/a)" is honest about this gap.
3. **Single-seed result.** The Tier 2.B protocol uses seed 0 per the D1 specification (pre-committed for reproducibility); the z = −5.08 is a single-seed observation. A multi-seed surrogate run would test whether the below-null result is robust.

The mechanistically plausible interpretation is that the during-event phase of split_merge dissolves flocking structure as agents pursue separate waypoints — this may produce feature time series that are *simpler* than the circular-shift null (lower cross-agent temporal correlation, because the dissolving flock's trajectories become nearly independent). This is a different mechanism from the §4.3 compressibility-prevention (which is a coherence-blocking mechanism, not flock-dissolution). The Phase 5 report flags split_merge as an **exploratory §4.3 candidate**, not a confirmed instance, with the recommended verification work documented in §10 (multi-seed surrogate, σ_u computation, within-event vs outside-event window decomposition).

### 8.4 Noise σ = 0.5 reclassification — also addressing prose-engagement item 3

Phase5.md §141 pre-registered noise σ = 0.5 as the surrogate-method positive control on the assumption that boids at high noise would produce near-random telemetry. Tier 2.B's actual run produced observed Φ = 82.07 vs surrogate 70.86 (95% CI [70.26, 72.11]), z = +17.58 — observed substantially above null. The Tier 2.B README documents this as a "sanity-check fail" — but the failure is of the *assumption*, not the method.

What the data actually establish is that boids at σ = 0.5 with `w_a = 1.0` and `vision_radius = 10.0` retain real cross-agent temporal structure. Observed polarization at this condition is 0.46 (still substantially coordinated), and the σ_u value (Tier 1.C, 0.6421) is in the moderate range. The σ = 0.5 condition is the alignment-sweep's analogue of a "moderately disordered but still partially coherent" regime — exactly what Bailey & Schneider §4.2 describes for a transitional regime, but in the noise sweep this condition sits *past* the bimodal peak (which is at σ = 0.2) toward the disordered end. The science finding is that cross-agent integration persists at moderate noise levels in this 3D model, which is interesting and consistent with the §4.2 framework but is not the surrogate-method validation that was pre-registered.

Figure 6 (`fig6_surrogate_null_comparison.png`) currently renders noise σ = 0.5 as a science scenario without explicit acknowledgment of the reclassification. The Phase 5 report's Methods section (§3.5) documents the reclassification honestly; the Results sections (§4 and this section) reference figure 6 with awareness that noise σ = 0.5's bar represents a science finding emerging from a failed methodological assumption — a small but real contribution to the Phase 5 record.

### 8.5 Boundary-synchrony floor

The disabled-interaction control (Attempt 2) yielded z = 3.12 — the boundary-synchrony floor. This z value is preserved as a model-level effect: reflective box walls at L = 50 produce velocity reversals that are correlated across agents sharing similar regions of the box. Circular-shift cannot decorrelate them because they arise from real per-agent autocorrelation. This is *not* a surrogate-method bias; it is a finite-size finding about the simulator (D7 acknowledges the high boundary-volume fraction at L = 50 with r_v = 10: ≈ 78% of the cube's volume is within r_v of a wall).

All eight science scenarios produce z-scores well above the 3.12 floor (smallest positive: leadership λ = 1.6 at z = 8.38; the split_merge z = −5.08 is a signed below-null result, not an ambiguous-vs-floor result). The boundary-synchrony floor does not affect the interpretability of any science-scenario z-score in the Phase 5 dataset.

### 8.6 Surrogate analysis summary

The circular-shift surrogate protocol is method-validated (synthetic AR(1) control, z = −0.53). The boundary-synchrony floor (z = 3.12) is documented as a model-level effect. Both confirmed §4.2 instances show observed Φ at z ≈ 32.9, the strongest above-null results in the set. The §4.3 jamming instance shows z = +16.17, consistent with real per-window cross-agent integration. The split_merge below-null finding (z = −5.08) is flagged as exploratory; not confirmed. The noise σ = 0.5 reclassification from method-validation entry to science scenario is documented honestly. Figure 6 renders the eight science-scenario bars plus the two method-validation control bars with the boundary-synchrony floor annotated.

---

## §9 — Discussion

This section synthesizes what Phase 5 establishes, what it narrows, what it unexpectedly contributes, what it leaves open, and how it relates to the 2D Phase 4 work. The goal is interpretive honesty: the data tell a richer story than the Phase 5 pre-registration anticipated, and the narrative shift from "compressibility as a general mechanism across multiple sweeps" to "the §4.2/§4.3 framework operating mechanism-specifically across three orthogonal axes" is the empirical finding rather than a deviation to be apologized for.

### 9.1 What Phase 5 establishes

The **Bailey & Schneider §4.2/§4.3 framework is empirically grounded in the 3D Vicsek/Bailey extension** across three orthogonal perturbation axes. The §4.2 transitional Φ peak prediction is confirmed at two instances (alignment w_a = 0.6 and noise σ = 0.2) with bimodality dip-test signatures and surrogate corroboration at z ≈ 32.9. The §4.3 compressibility-Φ-inversion prediction is confirmed at jamming α = 0.2 with a +38.6% mean-Φ inversion above the coherent baseline, σ_u floor-locked, phi_norm cross-seed σ reduced, per-window Φ unimodal-narrow, and surrogate z = 16.17 confirming real cross-agent integration. The mechanism described in D14 — that Φ_spectral measures within-window informational dependence; coherent low-dynamics regimes show low MI in steady-flight windows and pull the mean down; transitional regimes show window-to-window bimodality; jammed regimes lock σ_u above the steady-flight low and invert mean Φ relative to the coherent baseline — is consistent with every confirmed instance and is the canonical methodological framing for the report.

The framework operates **mechanism-specifically rather than sweep-agnostically**. Different perturbation axes can excite different sub-predictions of the §4.2/§4.3 family: alignment coupling and additive noise both excite §4.2 (transitional bimodality); jamming severity excites §4.3 (compressibility-Φ-inversion); leadership coupling excites neither sub-prediction and instead produces a structurally distinct leader-block partition mechanism. The empirical reach of the framework is therefore broader than one sweep but narrower than universal — a more interesting, more specific, and more defensible claim than the original pre-registration's universal-mechanism framing would have produced.

### 9.2 What Phase 5 narrows

The original D14 framing of compressibility as a general mechanism across multiple sweeps is **narrowed empirically**. §4.3 is a jamming-specific finding within the existing sweep set. The pre-registered leadership extension was tested in Tier 1.A and explicitly disconfirmed (Outcome 4); the cross-sweep audit's §4.3 sub-table verified that no other sweep-condition outside jamming matches the §4.3 signature on all four load-bearing descriptors (σ_u floor-locked, phi_norm σ reduced, per-window Φ unimodal-narrow, mean Φ inverted above coherent baseline).

This is methodologically honest scope-narrowing. The Phase 5 result is empirically stronger for shipping a **tested-and-disconfirmed extension claim** alongside two confirmed instances of the parent prediction: ambiguity in either direction would have been a less defensible posture. The leadership disconfirmation is a *result*, not a caveat. The pre-registration's four-outcome framework explicitly anticipated Outcome 4 as a possible finding distinct from compressibility; the data fall on Outcome 4, and the Phase 5 plan's contingent Tier 1.B/1.C scoping for non-Outcome-1 verdicts (narrower atlas, jamming-specific reframing) was followed cleanly.

### 9.3 What Phase 5 unexpectedly contributes

The **leader-block partition mechanism** is a structurally distinct route to Φ collapse that Phase 4 / pre-Tier 1 framing did not anticipate. Phase 4 framed the leadership-sweep follow-up as "compressibility extension"; Tier 1.A's mechanism diagnostic revealed the real story: at high λ, the MI matrix is *block-structured* around an 8-leader cluster (Fiedler $\leftrightarrow$ leader-membership pair agreement = 1.000, perfect), with the dense leader block sharing high MI internally and the sparse follower bulk sharing low MI internally. The Φ_spectral collapse at high λ is via the cross-cut of low leader-to-follower MI edges, not via uniform-MI compressibility.

This is new empirical content. It is also a **methodological vindication of the explicit MI-matrix mechanism diagnostic** that Phase 5 specified before any code was written. Without the per-window matrix inspection at representative λ = 0 and λ = 2.4 windows, the leadership high-λ result would have looked superficially like a §4.3 instance on the (σ_u, phi_norm σ) coordinate alone. The diagnostic discriminates Outcome 1 from Outcome 4 directly, and is the load-bearing pre-registered protocol that turns "Φ drops at high λ" into a meaningful structural claim about *which* mechanism is responsible.

The unexpectedness of this contribution is itself worth reflecting on. The Phase 5 plan was written to test compressibility-as-general-mechanism; the empirical reality is mechanism-family-specificity, which the plan's outcome-discrimination scheme accommodates because the plan was designed around what the data could plausibly show, not around what it was hoped to show. This is a Phase 5-specific instance of the broader project methodology that Bailey 2026 anchors: pre-registered alternatives are tested against pre-registered diagnostics; the verdict is whatever the data say; the writeup follows the data rather than pre-existing narrative commitment.

### 9.4 What Phase 5 leaves open

Several genuinely open items emerge from this Phase:

- **The split_merge §4.3 candidate flag.** Single-seed surrogate result at z = −5.08 (observed below null), not pre-registered as a §4.3 candidate, mean Φ wrong direction for §4.3 (below baseline rather than above). Mechanistically a flock-dissolution finding rather than a compressibility-prevention finding. Worth verification (multi-seed surrogate, σ_u computation for the split_merge sweep, within-event vs outside-event window decomposition) before any classification claim is made.
- **The compressibility vs redundancy-saturation interpretation (L1 in ResearchContext.md).** §5.5 establishes that the σ_u floor-lock at jamming α = 0.2 favors compressibility specifically over redundancy saturation for that finding, but the underlying limit on Φ_spectral's redundancy/synergy decomposition (Luppi et al. 2024) remains structural. ΦID-grade analysis on the same Phase 5 data (per ResearchContext.md §4.1) would test whether Phase 5's mechanism-specific findings hold under a redundancy/synergy decomposition or whether the framework's verdicts shift when the redundancy-weighting limit is addressed directly.
- **The methodological asymmetry between the two §4.2 instances.** Alignment can only test bimodality; noise tests bimodality + mean-peak. The Phase 5 verdict is that the two instances corroborate each other across orthogonal axes, but the empirical evidence is asymmetric in strength. A finer alignment-sweep grid around w_a = 0.6 (`{0.3, 0.45, 0.6, 0.75, 0.9}`) would map the transitional regime's onset and offset, and a finer noise-sweep grid (`{0.15, 0.2, 0.25, 0.3, 0.35}`) would do the same on the noise axis.
- **The figure 4 hierarchical-clustering separation of the two §4.2 instances.** Substantive finding (different spatial-configuration signatures under different perturbation types) or sampling noise at n = 10 seeds. A finer-grained per-seed bootstrap on the agreement matrix would discriminate, and the result is a Phase 6 hook for the Bailey 2026 hypothesis content (whether spectral and topological methods diverge specifically in temporally-bimodal regimes).
- **The H2 metric weakness in 3D.** A scale finding rather than a method finding; H2 detection at N = 40 on a spherical milling shell falls below Rips filtration resolution. Whether this weakness is intrinsic to 3D persistence at the relevant length scales or is an N-dependent finite-size effect is empirically open. N-scaling toward N = 160 in earlier Phase 4 sensitivity sweeps did not fully resolve the question; an explicit N-scaling at jamming α = 0.2 (where H2 signatures appear in the monitoring AUC matrix at AUC = 0.81 for `traj_TP_2`) would test whether H2 strengthens with N.

These open items are pointers, not commitments. They do not affect the Phase 5 verdicts as currently stated; they refine those verdicts by characterizing where additional empirical work would harden the empirical reach.

### 9.5 Comparison with the 2D Phase 4 work

The 2D proof of concept (`github.com/StevenFAU/Spectral_Swarm`, frozen at tag `v0.1-2d-poc`) established the spectral/topological framework on a 2D Vicsek/Bailey swarm but with two methodology deviations relative to Bailey 2026: a Gaussian closed-form MI estimator (instead of the methodology-specified KSG estimator) and a sum alignment rule (instead of the methodology-specified mean alignment rule). The 2D internal report focused on the primary pass/fail (milling monotonicity, snap_TP_1 jamming separation) and the spectral-vs-topological agreement comparison, and did not have the perturbation-axis breadth that Phase 5 provides — the 2D scope did not test whether the §4.2/§4.3 framework operates mechanism-specifically across multiple orthogonal axes. Notably, the 2D alignment-sweep work observed Φ_spectral *decreasing* with increasing alignment coupling — the same direction the §4.3 compressibility prediction would forecast — but the 2D writeup did not have the §4.2/§4.3 vocabulary yet to articulate this as a mechanism-level finding. Phase 5's mechanism-specific verification across three orthogonal axes can be read in part as completing the interpretive scaffolding the 2D Phase 4 work began.

Phase 5 in 3D adds that breadth with the two methodology restorations (KSG estimator, mean alignment) and with mechanism-specific verification across the three perturbation axes. The two confirmed §4.2 instances on orthogonal axes (alignment + noise) are a 3D-specific result that the 2D scope did not test directly. The §4.3 jamming inversion is the same mechanism the 2D A2 diagnostic established but with the 3D-specific σ_u definition and 3D MI-matrix mechanism diagnostic. The leader-block partition Outcome 4 is a 3D-specific finding (the 2D code's leadership sweep was less well-instrumented for the per-window MI matrix mechanism diagnostic that distinguishes Outcome 1 from Outcome 4). The H2 persistent homology addition is intrinsic to 3D and produces the H2 weakness finding (a scale issue rather than a method issue, documented in §7.1).

The Phase 5 internal report follows the 2D template structurally (per-section Methods → Results → Discussion → Future Work) but reorganizes the Results around the three-mechanism-family finding rather than the 2D's two-result (milling, jamming) structure. This is a deliberate Phase 5 design choice anchored in the Tier 1.A Outcome 4 verdict and the Tier 1.C two-instance §4.2 finding. A future external manuscript distilled from this internal report could foreground the three-mechanism-family finding as the headline contribution; the internal version preserves the comprehensive empirical record.

### 9.6 Methodology limits per ResearchContext.md (L1–L8)

The Phase 5 verdicts are stated within a methodology whose structural limits are articulated in `ResearchContext.md`. Five of those limits bear specifically on how the Phase 5 findings should be read; they are listed here for completeness, with cross-references to where each is relevant.

**L1 — Pairwise-MI is redundancy-weighted (Luppi et al. 2024).** The §4.3 jamming inversion at α = 0.2 is consistent in principle with both compressibility (Bailey & Schneider 2025 §4.3) and redundancy saturation (Luppi et al. 2024). §5.5 above identifies σ_u floor-lock as the empirical discriminator and shows the Phase 5 jamming data favor the compressibility reading specifically. L1 nevertheless remains a structural limit on Φ_spectral's ability to distinguish redundant from synergistic integration in general; ΦID-grade analysis (ResearchContext.md §4.1) addresses this directly and is the load-bearing follow-up if the framework's redundancy/synergy decomposition is to be sharpened.

**L4 — Φ_spectral is two relaxations removed from the IIT MIP.** The Fiedler bipartition relaxes the normalized minimum cut; the normalized minimum cut relaxes the MIP search. Each relaxation is principled, but Phase 5's Φ_spectral verdicts inherit the bound-not-equality status that Bailey & Schneider 2025 §2.5 acknowledges. PyPhi validation on small subsystems (ResearchContext.md §4.3) is the relevant follow-up where a tractable comparison is possible.

**L5 — Synchronic vs diachronic components are entangled in Φ_spectral(t).** The sliding-window construction produces a per-window time series, but it does not separately estimate the synchronic (constitutive-at-instant) and diachronic (non-traceable-across-time) components that Bailey & Schneider 2025 §7 distinguishes theoretically. The §4.2 transitional bimodality finding in particular reflects window-to-window alternation, which is *between-window* dynamics; the §4.3 compressibility inversion reflects within-window dynamic amplitude. Phase 5's mechanism-specific framing is partially organized around this distinction in practice, but the formal separation remains a methodology gap (ResearchContext.md §4.9).

**L7 — Finite-size effects at N = 40.** A 40-agent system is small relative to real swarms ($10^{3}$–$10^{6}$ agents). The Fiedler partition has meaningful statistical structure at N = 40 — the leader-block partition finding at λ = 2.4 demonstrates this concretely — but scaling claims to large swarms require either demonstration at larger N or explicit caveats. The N-scaling at jamming α = 0.2 recommended in §10.1 directly addresses L7 for the §4.3 finding; analogous tests for the §4.2 instances would do the same.

**L8 — Simulation-only validation.** Phase 5's findings are entirely in an idealized simulator where physics, noise, and observability are controlled. Real-world applicability is argued from mechanism, not demonstrated from telemetry. The real-world validation step (ResearchContext.md §4.7) is outside Phase 5's scope but bounds the claims Phase 5 can defend. No verdict in this report should be read as a claim about field-deployable swarm sensing; the verdicts apply to the simulator-substrate methodology and to the framework's coherence, not to deployment readiness.

L2 (symmetric MI misses directionality), L3 (Φ_spectral is causally blind), and L6 (within-window autocorrelation inflates apparent sample size) are also in force but are less specific to Phase 5's particular findings — they apply uniformly across the project. ResearchContext.md treats all eight in their full form; this section names only the five that bear most directly on the Phase 5 verdicts.

The asymmetry between this section and §9.4 (Phase 5 operational open items) is intentional. §9.4 names what additional empirical work would refine the Phase 5 verdicts. §9.6 names what methodological limits bound those verdicts even if every §9.4 follow-up were completed. Both are honest about scope; together they articulate where Phase 5 establishes claims and where those claims are bounded.

### 9.7 What would falsify the framework

The mechanism-specific framing in §9.1–§9.3 has an absorptive property worth naming: any new disconfirmation of a particular sweep can in principle be re-described as "the framework is mechanism-specific; this sweep excites a different mechanism." The leadership Outcome 4 finding is the project's exhibit A that this isn't pure rescue — leader-block partition is a real, distinct, named mechanism evidenced by direct MI-matrix inspection (Fiedler $\leftrightarrow$ leader-membership = 1.000) rather than a label assigned post-hoc to absorb a problematic result. But the absorptive property is structural, and a methodologically honest report should articulate what observation, if it occurred, would compel abandonment of the §4.2/§4.3 framework rather than further mechanism-specific narrowing.

The framework's predicted causal chain (per §4.3) is: a perturbation that **floor-locks within-window σ_u above the coherent baseline** produces **uniformly elevated MI** in the per-window matrix, which produces **mean Φ inversion above the same sweep's coherent baseline**. The chain has three observable links. A finding that disrupts any link while leaving the others intact would constitute framework-level falsification rather than mechanism-specific narrowing:

- **σ_u floor-locked above baseline AND Φ inverted above baseline AND MI matrix uniformly elevated AND the inversion does NOT track the σ_u floor-lock across conditions in a sweep.** This would mean the predicted causal chain is broken — σ_u is not the proximate driver of Φ inversion — and the §4.3 mechanism's operational definition would need substantive revision. Phase 5's jamming sweep tracks the chain in the predicted direction (σ_u and Φ co-vary across α), so this falsification path is not currently active.
- **A condition with σ_u in the compressibility range but per-window Φ persistently bimodal.** §4.3 predicts unimodal-narrow per-window Φ at compressibility regimes (the wobbly transitional regime is uniformly wobbly; there is no steady-flight low to alternate to). A bimodal-Φ compressibility regime would mean the unimodal-narrow component of the §4.3 signature is dispensable, weakening the mechanism distinction between §4.2 and §4.3.
- **A confirmed §4.2 instance whose per-window Φ is unimodal-narrow rather than bimodal.** §4.2 predicts within-window bimodality at the disorder-to-order regime boundary; a transitional condition that produced a peak in mean Φ without bimodality would contradict the bimodality-as-mechanism reading. Both confirmed §4.2 instances in Phase 5 (alignment w_a = 0.6 dip p = 0.102; noise σ = 0.2 dip p = $7.6 \times 10^{-6}$) carry the bimodality signature, so this falsification path is not currently active.

These are not hypothetical edge cases; they are concrete observations whose absence in Phase 5 supports the framework but whose presence in Phase 6 or in another substrate would require the framework to be revised rather than narrowed further. Articulating them converts the framework from "absorptive" to "characterizable" and is what distinguishes a falsifiable mechanism-specific framework from one that accommodates any data by reassignment.

---

## §10 — Future work and Phase 6 hooks

These are pointers for Phase 6 or for an external manuscript distilled from this internal report, not commitments within Phase 5. They are organized by which Phase 5 finding each one would strengthen.

### 10.1 Tightening the §4.3 verdict

**N-scaling at jamming α = 0.2** to confirm the inversion magnitude scales appropriately. The cross-sweep n_sensitivity_N80 and N160 data are at default w_a sweeping the alignment axis only; an analogous N-scaling at jamming α = 0.2 would test whether the σ_u floor-locked regime persists, weakens, or strengthens with N. This is the clearest single follow-up that would harden the §4.3 verdict at the empirical-reach dimension. Expected behaviour: the +38.6% inversion magnitude should persist or strengthen with N, because the compressibility mechanism scales with the ratio of high-σ_u wobble window contributions to low-σ_u steady-flight contributions in the mean — which is set by the per-agent dynamics rather than by N.

### 10.2 Tightening the §4.2 verdict

**Finer alignment-sweep grid around w_a = 0.6** (`{0.3, 0.45, 0.6, 0.75, 0.9}`) to characterize the transitional regime's width on the coupling axis. The current grid (Δw_a = 0.6) is too coarse to establish how narrow the bimodal regime is. A finer grid would map the bimodality's onset and offset, allowing direct comparison to the corresponding onset/offset on the noise axis and testing whether the two §4.2 instances span similar fractions of their respective control axes.

**Finer noise-sweep grid around σ = 0.2** (`{0.15, 0.2, 0.25, 0.3, 0.35}`) for the analogous question on the noise axis. The current grid jumps from σ = 0.1 (modes = 3, dip p = 0.45) to σ = 0.2 (bimodal, dip p = $7.6 \times 10^{-6}$) to σ = 0.5 (random unimodal). The dip p = $7.6 \times 10^{-6}$ at σ = 0.2 is the strongest bimodal signature in the audit and is worth characterizing precisely.

### 10.3 The figure 4 §4.2-instance separation

**Per-seed bootstrap on the agreement matrix at the two §4.2 instances** to discriminate substantive finding from sampling noise at n = 10 seeds. If the two instances' TDA-correlation profiles persist beyond bootstrap noise, this is substantive Bailey 2026 hypothesis content (the §4.2 mechanism produces different spatial-configuration signatures under different perturbation types even when the within-window-Φ signatures are mechanistically the same). If they do not, the divergence is sampling noise and should not be foregrounded. Phase 5 cannot adjudicate this without additional analysis; the §10.3 work is the load-bearing follow-up for the spectral-vs-topological story in figure 4.

### 10.4 The split_merge §4.3 candidate flag

**Multi-seed surrogate test** with seeds beyond seed 0; if the z = −5.08 below-null direction persists across multiple seeds, the result is robust at the seed-aggregate level. **σ_u computation** for the split_merge sweep (canonical descriptor for §4.3 — currently "n/a" in the Tier 1.C audit table). **Within-event vs outside-event window decomposition** — the dissolution interval [200, 300] is mechanistically different from the merge interval [300, 400] and the pre/post-event intervals, and the surrogate test conducted on per-window data pooled across all intervals may dilute or amplify the signal depending on which interval drives the below-null result. **MI matrix descriptors** at a representative seed/window during the split interval would determine whether the below-null Φ reflects a compressibility-style uniform-MI elevation or a flock-dissolution-style fragmentation pattern. This work could resolve split_merge as a third confirmed §4.3 instance, as a flock-dissolution-mechanism finding (mechanistically distinct from §4.3), or as a single-seed artefact.

### 10.5 The H2 metric weakness

**Investigation of why H2 contributes less to spectral-topological agreement in 3D** — possibly a scale issue (N = 40 on a spherical shell at R = 11 puts enclosed voids below Rips filtration resolution per D9), possibly substantive (3D persistence at H2 is genuinely sparser than the analogous 2D H1 because the geometric resolution requirement is more demanding). N-scaling at jamming α = 0.2 (where H2 signatures appear at AUC = 0.81 for `traj_TP_2` per §7.3) would test whether H2 detection improves at N = 80, 160. Alpha-complex substitution (instead of Rips) would address the over-triangulation issue at fine scales but introduces a new TDA dependency and a methodology deviation; not recommended for Phase 6 unless the N-scaling test inconclusive.

### 10.6 Standalone MI matrix diagnostic figure staging

The standalone diagnostic `outputs/tier1_compressibility/mi_matrix_diagnostic.png` (commit `9ad6a5a`) shows the side-by-side λ = 0 vs λ = 2.4 contrast that makes the leader-block partition unambiguous. Phase 5 references both this standalone figure and the integrated three-mechanism panel (`fig1` Row 3 Col 4) for comprehensive visual evidence. The recommendation is to copy or symlink the standalone diagnostic into `outputs/figures/composition/supplementary/` so the figure set is self-contained for any reader picking up the supplementary materials. This is a planning-level recommendation, not an action this report takes.

### 10.7 Surrogate at noise σ = 0.2 — already done

The Tier 1.C audit recommendation #5 — adding noise σ = 0.2 to the Tier 2.B surrogate set — was implemented post-Tier-1.C (commit `f8f7ea5`). The result (z = +32.92) corroborates the §4.2 verdict at the surrogate level. This item is **resolved** and is documented for completeness.

### 10.8 Phase 6 directions per ResearchContext

Three Phase 6 directions are flagged in `ResearchContext.md` and remain pointers for follow-on work: §4.8 N-scaling (across all sweeps, not just the existing N80/N160 data on the alignment axis), §4.9 synchronic/diachronic separation estimator (theoretical refinement of the within-window vs across-window decomposition that Φ_spectral implements), §4.10 cross-substrate comparison (whether the 3D Vicsek/Bailey framework generalizes to other agent-based collective-motion substrates). These are commitments at the ResearchContext level rather than Phase 5 hooks; they are mentioned here for completeness in case the Phase 5 verdicts inform Phase 6's specific scope.

---

## §11 — References, methodology citations, code/data availability

### 11.1 Primary methodology references

- Bailey, M. M. (2026). *Spectral and Topological Methods Comparison in Swarms.* Methodology paper specifying the full 2D simulation and analysis pipeline; the 3D extension restores the methodology's KSG MI estimator (B6) and mean alignment rule (A6).
- Bailey, M. M., & Schneider, S. L. (2025). *When Wholes Resist Decomposition: A Spectral Measure of Epistemic Emergence.* Introduces Φ_spectral and validates its behaviour across random, transitional, synchronized, and CTLN systems. §4.2 (transitional Φ peak) and §4.3 (compressibility-Φ-inversion) are the two predictions Phase 5 tests.
- Bailey, M. M. (2026). *Quotient Geometry and Persistence-Stable Metrics for Swarm Configurations.* arXiv:2603.18041. Supporting reference for the persistence-stable distance choice.

### 11.2 Supporting references (by decision)

- ter Hoeven, E., et al. (2025). *Mesa 3: Agent-based modeling with Python in 2025.* JOSS 10(107), 7668. — Mesa 3 substrate per A1.
- Reynolds, C. W. (1987). *Flocks, Herds, and Schools: A Distributed Behavioral Model.* ACM SIGGRAPH. — boids model lineage.
- Vicsek, T., et al. (1995). *Novel Type of Phase Transition in a System of Self-Driven Particles.* Phys. Rev. Lett. 75(6), 1226. — Vicsek model and synchronous-update convention.
- Kraskov, A., Stögbauer, H., & Grassberger, P. (2004). *Estimating Mutual Information.* Phys. Rev. E 69, 066138. — KSG estimator per B6.
- Fiedler, M. (1973). *Algebraic Connectivity of Graphs.* Czech. Math. J. — Fiedler-bipartition foundation.
- von Luxburg, U. (2007). *A Tutorial on Spectral Clustering.* Stat. Comput. 17(4), 395.
- Edelsbrunner, H., Letscher, D., & Zomorodian, A. (2002). *Topological Persistence and Simplification.* DCG.
- Zomorodian, A., & Carlsson, G. (2005). *Computing Persistent Homology.* DCG. — H2 persistent homology per B4.
- Carlsson, G. (2009). *Topology and Data.* Bull. AMS.
- Cohen-Steiner, D., Edelsbrunner, H., & Harer, J. (2007). *Stability of Persistence Diagrams.* DCG. — bottleneck-distance stability per D8.
- Tralie, C., Saul, N., & Bar-On, R. (2018). *Ripser.py: A Lean Persistent Homology Library for Python.* JOSS 3(29), 925.
- Perea, J. A., & Harer, J. (2015). *Sliding Windows and Persistence.* FoCM 15(3), 799. — trajectory-cloud TDA foundation per D10.
- Topaz, C. M., Ziegelmeier, L., & Halverson, T. (2015). *Topological Data Analysis of Biological Aggregation Models.* PLOS ONE 10(5), e0126383.
- Bhaskar, D., et al. (2019). *Analyzing Collective Motion with Machine Learning and Topology.* Chaos 29, 123125.
- Barrett, A. B., & Seth, A. K. (2011). *Practical Measures of Integrated Information for Time-Series Data.* PLOS Comput. Biol. 7(1), e1001052.
- Mediano, P. A. M., Seth, A. K., & Barrett, A. B. (2019). *Measuring Integrated Information: Comparison of Candidate Measures in Theory and Simulation.* Entropy 21(1), 17.

### 11.3 Internal Phase 5 references

The empirical evidence in this report draws from the following project artefacts (commit SHA at the time of report drafting in parentheses):

- `Phase5.md` (HEAD `c623642`) — Phase 5 working plan; supersedes the Phase 5 section in `SpectralSwarm3DPhases.md`.
- `SpectralSwarm3DPhases.md` D14 (commit `6d0a165`) — canonical D14 framework framing as it stands at the time of report drafting.
- `outputs/tier1_compressibility/leadership_prediction_verdict.md` (commit `9ad6a5a`) — Tier 1.A leadership Outcome 4 verdict; load-bearing for §6.
- `outputs/tier1_compressibility/distributions/bimodality_audit.md` (commit `4f821ae`) — Tier 1.B per-window distribution atlas; load-bearing for §4.1 and the steady-state-only pooling convention in §3.3.
- `outputs/tier1_compressibility/cross_sweep_audit.md` (commit `fec6079`) — Tier 1.C two-part verdict; load-bearing for §4.2, §4.3, §5, and §6.
- `outputs/comparison/cross_sweep/findings_summary.md` (commit `f0ad4aa`) — Tier 2.C narrative anchor; load-bearing for §5 and §8.
- `outputs/surrogates/README_summary.md` (commit `f8f7ea5`, with prior commits `5d1d5c0` and `2603b83`) — Tier 2.B surrogate analysis and method-validation history; load-bearing for §3.5 and §8.
- `outputs/figures/composition_plan.md` (commit `b981317`) — Tier 3.A figure composition plan.
- `outputs/figures/composition/primary/_captions.md`, `outputs/figures/composition/_render_notes.md` (commit `5974061`) — rendered figure captions and renderer's documented decisions.
- `outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md` (commit `cc23aa9`) — canonical A2 §4.3 reference; mechanism-level descriptors used in §6's mechanism diagnostic.
- `outputs/comparison/cross_sweep/scenario_summary.csv` (commit `f0ad4aa`) — 38-row canonical cross-sweep fact sheet.
- `outputs/comparison/cross_sweep/scenario_agreement_spearman.csv` (commit `f0ad4aa`) — 38  \times  18 Spearman agreement matrix; load-bearing for §7.
- `outputs/comparison/cross_sweep/monitoring_roc.csv` (commit `f0ad4aa`) — per-metric AUC table for event detection.

### 11.4 Code and data availability

- **Repository:** `github.com/StevenFAU/Spectral_Swarm_3D` (private). Code at HEAD `c623642`.
- **Predecessor:** `github.com/StevenFAU/Spectral_Swarm` at tag `v0.1-2d-poc` (frozen 2D proof of concept).
- **Reproducibility metadata:** Each sweep run's `metadata.json` records git commit hash, Python version, and package versions per D6. All randomness is via explicit seeds; under D6 deterministic seeding, runs reproduce bit-identical trajectories for the same seed (verified for the eight vanilla-baseline byte-identical conditions in Tier 1.C).
- **Dependency pinning:** `pyproject.toml` pins exact versions; `requirements-lock.txt` captures the full transitive dependency closure per D5.
- **Data storage:** Per-run telemetry and per-window aggregates are stored in Parquet format under `outputs/<sweep>/<condition>/seed*/*.parquet`; cross-seed summaries under `outputs/<sweep>/cross_seed_summary.csv`; cross-sweep aggregates under `outputs/comparison/cross_sweep/`.
- **Figures:** Tier 3.A primary and supplementary figures under `outputs/figures/composition/primary/` and `outputs/figures/composition/supplementary/`; legacy 2D-mirror per-sweep figures under `outputs/figures/<sweep>/`.

---

## Notes on plan deviations and prose-engagement items

The following items emerged during Phase 5 execution and are flagged here for the project's record. They do not affect the verdicts; they document where the empirical reality required adjustments to the plan or where reasonable analysis chose between defensible alternatives.

1. **Phase5.md figure 1 specification is empirically obsolete.** The original 3$\times$4 grid with rows = perturbation axes (alignment, jamming, leadership) and columns = (coherent-Φ-dist, disordered-Φ-dist, σ_u, phi_norm σ) was written for Outcome 1. Post-Outcome-4 plus the cross-sweep audit's two-§4.2-instances finding, the row-by-perturbation-axis logic does not fit the empirical structure. The Tier 3.A composition session chose a mechanism-organized 3-row layout (Option II in the composition plan): rows = §4.2 transitional bimodality, §4.3 compressibility-Φ-inversion, leader-block partition. This is the figure that ships in the Phase 5 report. The Phase5.md figure 1 spec is superseded by the rendered figure; if a planning-level update is desired in a separate session, the recommendation is to record the supersession.

2. **Phase5.md figure 1 spec did not anticipate the noise sweep's role.** The cross-sweep audit elevated `noise σ = 0.2` to a confirmed §4.2 instance; Phase5.md figure 1's row structure does not include noise. The mechanism-organized Option II layout addresses this by placing both confirmed §4.2 instances in Row 1.

3. **Phase5.md figure 8 spec lists 5 scenarios; the rendered figure includes 6.** The composition session added `leadership λ = 2.4` as a sixth scenario for the leader-block partition visualization; this is the visual primer for the Outcome 4 mechanism. The deviation is documented in the composition plan §10 Appendix item 5.

4. **Tier 2.B noise σ = 0.5 reclassification.** Pre-registered as the surrogate-method positive control; reclassified post-hoc as a science scenario after Tier 2.B revealed observed > surrogate at z = 17.58 due to retained cross-agent structure. The synthetic AR(1) i.i.d. control (Attempt 3) is the canonical method-validation entry. Documented in §3.5 and §8.4 above.

5. **Standalone MI matrix diagnostic is not staged in the figure composition supplementary.** The standalone `outputs/tier1_compressibility/mi_matrix_diagnostic.png` is referenced in §6.3 alongside the integrated three-mechanism panel. The recommendation in §10.6 is to copy or symlink it into the supplementary figure set; this report does not take that action.

6. **The Phase5.md prerequisite path for the A2 diagnostic was incorrect.** The Tier 3.C prompt's prerequisite check listed `outputs/tier1_compressibility/A2_PHI_INVERSION_DIAGNOSTIC.md`; the actual location is `outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md`. This is a documentation typo, not a missing artefact; the file exists and is the canonical §4.3 reference.

These items are documentation, not decisions to be re-litigated in this report. They are listed for the record so that a future revision pass or external manuscript distillation can address them as needed.

---

*End of Phase 5 internal report. The four prose-engagement items from the Tier 3.A figure review are addressed in §4.3 (asymmetric §4.2 evidence), §6.3 (standalone MI matrix diagnostic), §8.4 (noise σ = 0.5 reclassification), and §7.2 (figure 4 hierarchical-clustering separation of §4.2 instances). The substantive defensibility additions from review feedback are addressed in §5.5 (compressibility vs redundancy-saturation discriminator), §5.6 (jamming-specific verdict tightened to reflect testing across five mechanism families), §8.2 (single-seed-coincidence framing for the §4.2 z-score near-identity), §9.6 (methodology-limit cross-references to ResearchContext.md L1, L4, L5, L7, L8), and §9.7 (framework-level falsifiability articulated as three concrete observations whose absence supports the framework). Subsequent passes will polish prose, refine figure captions, and adjudicate any framing decisions that remain open after this revision pass settles.*
