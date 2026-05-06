# Phase 5 — Comparison Analysis, Surrogates, and Interpretation

## Supersedes

This document supersedes the Phase 5 section in `SpectralSwarm3DPhases.md`. The prior Phase 5 scope was drafted before Phase 4 executed and did not anticipate the A2 diagnostic (commit cc23aa9), which reframed the interpretive task substantially. Decisions D11, D12, D13, and D14 in Cluster D are the load-bearing context for this revised Phase 5. This file is the working plan; when Phase 5 completes, the Phase 5 section in `SpectralSwarm3DPhases.md` should be updated to match what was actually done.

## What changed between the old Phase 5 scope and this one

The old scope treated Phase 5 as (a) porting the 2D comparison pipeline with H2 column additions, (b) implementing surrogate nulls, (c) producing figures and animations. That work is still in scope, but it is now subordinate to a primary interpretive task that the old scope did not know about: Phase 4 surfaced Φ_spectral inversion under jamming as a direct empirical instance of Bailey & Schneider (2025) §4.2–§4.3 compressibility, and Opus's A2 diagnostic predicts a second instance in the leadership sweep at high λ. Whether that prediction is confirmed organizes the entire Phase 5 writeup.

The revised phasing puts the prediction test first. If the leadership sweep exhibits the predicted compressibility inversion, Phase 5 has three convergent empirical instances of the mechanism (alignment, jamming, leadership) from orthogonal perturbation axes and the writeup leads with mechanism. If the prediction fails, the writeup leads with "compressibility under jamming is a finding; generalization across perturbation axes is tested and does not hold," which is a weaker but still interesting result. Both outcomes are publishable; they tell different stories.

## Scope

Phase 5 has three tiers, executed in order.

**Tier 1 — Interpretation-first analysis on existing Phase 4 data.** No new simulation. The compressibility prediction for leadership, the per-window Φ distribution analysis per D14, and the across-sweep compressibility audit are all reanalyses of the 280 runs already on disk. This tier answers the "what story does Phase 4 tell?" question before any code gets written.

**Tier 2 — Comparison pipeline port plus surrogate nulls.** The 2D comparison pipeline ported with H2 column additions and D14-required per-window distribution reporting. Surrogate null testing (D1) on one representative seed per scenario. Bootstrap CIs on η² and across-seed metrics. This is the mechanical bulk of the work and produces the aggregated tables and heatmaps.

**Tier 3 — Figures, animations, and writeup.** Publication-quality figures composed around the Tier 1 interpretation. 3D scenario animations. Internal report draft.

Tier 1 is Opus-first; Tiers 2 and 3 are Sonnet-first with Opus for figure composition and final interpretation passes.

**Tradeoff acknowledgment.** Running Tier 1 before Tier 2 means interpretive calls are made on data that has not yet been through the full comparison pipeline. If Tier 2's aggregated tables surface something that contradicts the Tier 1 interpretation (e.g., histogram-estimator results on jamming tell a different story than KSG does), Tier 1 may need revisiting. This is judged an acceptable risk given D11 already framed histogram as sign-only and the compressibility finding rests on KSG+Gaussian agreement. But if Tier 2 surfaces genuine contradiction, the correct response is to pause Tier 3 and re-examine Tier 1, not to paper over the contradiction in the writeup.

## Architecture addition

```
src/spectral_swarm_3d/analysis/
    ├── comparison.py     # SPECTRAL/TDA/CLASSICAL/_TDA_COMPARE column lists extended;
                          # per-window distribution reporting per D14
    ├── surrogates.py     # D1: trajectory-shuffled null distributions
    └── plotting.py       # configure_style, plot_time_series (extended to H2),
                          # plot_agreement_heatmap (H2 in _TDA_COMPARE),
                          # plot_snapshot_3d (NEW), animate_trajectory_3d (NEW),
                          # plot_phi_distribution (NEW, per D14),
                          # plot_compressibility_panel (NEW)
scripts/
    ├── run_comparison.py
    ├── run_surrogates.py              # NEW: D1 surrogate analysis
    ├── render_scenario_videos.py
    └── analyze_compressibility.py     # NEW: Tier 1 compressibility audit
outputs/
    ├── tier1_compressibility/         # Per-sweep per-window distribution analysis,
                                        # leadership prediction verdict, cross-sweep audit
    ├── comparison/                    # η² tables, agreement heatmaps, matched-control deltas
    ├── surrogates/                    # Observed vs null Φ_spectral per scenario
    ├── figures/                       # Publication figures
    └── videos/                        # Per-scenario MP4s
```

## Tier 1 — Interpretation-first analysis

### Tier 1.A — Leadership sweep compressibility test (the load-bearing result)

**What to compute.** For each leadership_sweep condition (λ ∈ {0.0, 0.8, 1.6, 2.4}), across all 10 seeds:

1. Steady-state mean Φ_spectral per seed. Aggregate to cross-seed mean + bootstrap CI per condition.
2. Per-window Φ distributions per seed. Aggregate to per-condition histograms (pooled across seeds) and per-condition bimodality diagnostics: KDE mode count, Hartigan's dip test, ratio of standard deviation to interquartile range.
3. Per-window within-agent directional σ (σ_u) — the same within-window dynamic amplitude signal that drove the jamming finding. Aggregate per-condition.
4. Leader-group compactness — mean pairwise distance among leader agents per window, aggregated per-condition. (This is what A4 was originally going to instrument in Phase 4 and was deferred.)

**What to look for.** Opus's A2 prediction: Φ at λ=2.4 is *lower* than Φ at moderate λ (0.8 or 1.6), because high λ forces leader compactness, leader compactness compresses within-window σ_u for the leader subset, and this pulls the global Φ mean down even though structural organization is visible in polarization and leader-following metrics. Secondary prediction: per-window Φ at λ=2.4 is more tightly unimodal (lower bimodality diagnostics) than at λ=0.0 or λ=0.8.

**Mechanism diagnostic.** Φ ordering alone is not sufficient to confirm compressibility — Φ could drop at high λ for reasons other than within-window σ_u compression (e.g., heterogeneous leader dynamics that break the Fiedler cut's bipartition assumption would pull Φ down via a partition-quality failure, not compressibility). To discriminate, extract the MI matrix at a representative steady-state window for one seed at λ=2.4 and one seed at λ=0.0. Compare the structure to the A2 jamming result: the compressibility signature is a **uniformly elevated** MI matrix with low spatial correlation. A block-structured or pathologically asymmetric MI matrix at λ=2.4 is a **different** mechanism producing a superficially similar Φ drop and should not be reported as compressibility confirmation.

**Possible outcomes.**

- *Outcome 1 — Prediction confirmed with compressibility mechanism.* Φ non-monotone in λ, σ_u compressed at high λ, MI matrix uniformly elevated at λ=2.4. Best outcome. Organizes Phase 5 around compressibility-as-general-mechanism. Cross-sweep audit (1.C) reports three convergent instances.
- *Outcome 2 — Prediction directionally confirmed but weak.* Φ monotone but σ_u and compactness behave as predicted. Mixed result needing careful framing: compressibility is present as a signature but is not dominant enough to flip the Φ ordering. Writeup is honest about the limit and positions jamming as the clearest instance.
- *Outcome 3 — Prediction disconfirmed.* Φ monotone and σ_u behaves differently. Substantive negative result. The jamming compressibility is then a sweep-specific finding. Phase 5 writeup leads with "compressibility under jamming; scope of the mechanism is narrower than predicted."
- *Outcome 4 — Φ ordering confirmed but mechanism differs.* Φ is non-monotone in λ, but the MI matrix diagnostic shows a different structural signature than jamming (block-structured, pathologically asymmetric, or any pattern distinct from uniform elevation). The Φ drop at high λ is real but is not compressibility. Phase 5 writeup reports the Φ drop as its own finding under a different mechanism name (to be determined by follow-up analysis) and does **not** claim compressibility generalization. This is the outcome most at risk of being misread as Outcome 1 if the mechanism diagnostic is skipped.

**Output.** `outputs/tier1_compressibility/leadership_prediction_verdict.md` stating which outcome obtained, with numbers supporting the verdict. Also per-condition panel figure showing (Φ cross-seed, σ_u cross-seed, leader compactness cross-seed, per-window Φ distribution) as a 2×2 grid.

### Tier 1.B — Per-window Φ distribution analysis per D14

**Scope is contingent on Tier 1.A outcome.**

- *If Outcome 1 (confirmed):* full atlas. Every sweep × condition gets a per-window distribution figure, because compressibility is now a general claim and the atlas is the empirical foundation supporting it.
- *If Outcomes 2, 3, or 4:* narrower atlas. Focus on jamming (confirmed compressibility instance), alignment sweep (where C1 originally predicted the transitional-regime peak), and suspected-bimodality scenarios (milling at μ=0, any condition from Tier 1.A that showed bimodality). Other sweeps are skipped or rendered only on user request. Rationale: if compressibility is not general, producing ~50 distribution figures adds no narrative value.

The contingent scoping is decided at the Tier 1.A verdict pause and documented in the Tier 1.A verdict document so the Tier 1.B scope is explicit before rendering begins.

**What to compute.** For each in-scope sweep × condition, produce a per-window Φ distribution figure. Pooled across seeds per condition. Annotate with bimodality diagnostics per 1.A. Sweeps exhibiting bimodality in the coherent regime (suspected: alignment at high w_a, jamming at α=1.0, leadership at λ=0, milling at μ=0) are flagged for the writeup.

**What to look for.** D14 asserts that coherent regimes bimodalize Φ across windows. This tier validates that claim empirically in the scope set by 1.A. If bimodality does not appear in regimes where compressibility theory says it should, D14's mechanism claim needs revision.

**Output.** Per-sweep distribution atlas in `outputs/tier1_compressibility/distributions/`, one figure per in-scope sweep. Summary `outputs/tier1_compressibility/distributions/bimodality_audit.md` listing per-condition bimodality test results and noting which sweeps were scoped out and why.

### Tier 1.C — Cross-sweep compressibility audit

**What to compute.** Aggregate the Tier 1.A and 1.B results into a single cross-sweep table. Columns: sweep, condition, Φ cross-seed mean, σ_u cross-seed mean, within-window Φ bimodality index, phi_norm cross-seed σ (the secondary confirmation signal Opus identified). Rows: every condition from every primary sweep.

**What to look for.** The compressibility signature is: low σ_u (coherent within-window dynamics) correlates with high bimodality AND with low phi_norm cross-seed σ (jamming regularization signal inverted). If this triple-correlation holds across conditions from multiple sweeps, compressibility is a general mechanism. If it holds only in jamming, compressibility is sweep-specific.

**Output.** `outputs/tier1_compressibility/cross_sweep_audit.md` with the table, a one-paragraph interpretation, and a verdict on whether D14's "general mechanism" framing is empirically supported.

### Tier 1 model guidance

Opus 4.7 at max effort for 1.A (the interpretive call on whether the prediction was confirmed) and 1.C (the cross-sweep synthesis). Sonnet 4.6 is adequate for 1.B (mechanical per-sweep distribution plotting once the analysis function is written). The Opus session runs before any comparison-pipeline code is touched.

## Tier 2 — Comparison pipeline and surrogates

### Tier 2.A — `comparison.py` port with H2 and D14 extensions

Port the 2D `comparison.py` with these extensions:

- `_SPECTRAL`, `_TDA`, `_CLASSICAL`, `_TDA_COMPARE` column lists updated per C2: H2 entries (`snap_TP_2`, `snap_MP_2`, `snap_B_base_2`, `traj_TP_2`, `traj_MP_2`, `traj_B_base_2`) added. `angular_momentum_norm` and the saturation diagnostic column `phi_saturation_ratio` added to classical.
- Per D14, the primary comparison output table for each sweep reports both the steady-state mean AND three distribution summary statistics per condition: median, interquartile range, bimodality index. Steady-state mean alone is not sufficient for sweeps exhibiting bimodality.
- η² computations use bootstrap CIs per D2. Bootstrap is on per-seed values (not per-window), B=1000, resampling seeds with replacement.
- Histogram estimator results are reported under the D11 sign-only interpretation: only the sign of condition-level differences is inferred; magnitudes and within-condition rankings are flagged as unreliable.

Tests: port 2D `test_comparison.py` with 3D column schema updates. Add tests for the new distribution-summary output columns.

### Tier 2.B — `surrogates.py` — trajectory-shuffled nulls (D1)

For each of seven primary scenarios, run D1 surrogate null testing on **seed 0** (pre-committed for reproducibility; the choice is methodological rather than data-driven, so any seed works and seed 0 is the simplest):

- none (baseline)
- alignment at w_a=1.8 (coherent alignment)
- leadership at λ=1.6 (structured coordination)
- jamming at α=0.2 (fragmented — compressibility instance)
- split_merge
- milling at μ=0.8 (rotational coherence)
- **noise at σ=0.5 (surrogate-method sanity check)**

The noise scenario is the surrogate-method positive control: near-random telemetry should produce observed Φ ≈ surrogate Φ. If the shuffling protocol is working correctly, this case should *not* show observed > surrogate. If it does, either the shuffle is not destroying the right temporal dependence or the noise scenario is less random than assumed. Without this sanity check, if all coordinated scenarios show observed > surrogate we cannot distinguish between "real integration detected" and "subtle shuffling bug."

**Protocol per scenario.**

- Generate 10 circular-shift shuffles per run. Each agent's telemetry is independently shifted by a per-agent random offset; cross-agent temporal dependence is destroyed, marginal distributions preserved.
- Compute Φ_spectral and top TDA summaries on each shuffled telemetry.
- Report: observed Φ_spectral, surrogate Φ_spectral distribution (mean, 95% CI across 10 shuffles), z-score of observed relative to null.

**What to look for.** Observed Φ_spectral should substantially exceed surrogate distribution for coordinated scenarios (leadership, milling, coherent alignment). Observed should be close to surrogate for random baseline (w_a=0, no perturbation) **and for noise at σ=0.5** — those two are the method's sanity checks. If an observed Φ_spectral is *below* its surrogate, this is a compressibility finding at the single-seed level and should be flagged for Tier 1 cross-reference.

The surrogate analysis has an additional interpretive role given D14: if observed > surrogate in coherent regimes despite the mean-over-windows compressibility drop, this means the per-window dynamical structure is detectable *against* compressibility artifact, which strengthens the framing-(b) case that Φ_spectral is measuring real structure.

**Output.** `outputs/surrogates/<scenario>_null.csv` and a summary document `outputs/surrogates/README_summary.md`. The summary document's first section is the sanity-check verdict: does the noise scenario show observed ≈ surrogate? If yes, the method is validated and other scenario results can be interpreted. If no, the method itself is flagged for investigation before any scientific claim is drawn from it.

### Tier 2.C — Aggregated comparison tables and heatmaps

Run `scripts/run_comparison.py` on all 11 sweep families. Produce:

- Per-sweep η² sensitivity tables with bootstrap CIs (as in 2D).
- Agreement/divergence heatmaps across metric families (spectral vs classical vs TDA), including H2 columns.
- Matched-control delta tables (perturbation minus baseline per metric) for event sweeps (jamming, split-merge).
- Cross-scenario agreement Spearman matrices.
- Monitoring ROC analysis (as in 2D): per-metric AUC for detecting perturbation onset.

All η² reported with histogram-estimator columns flagged for sign-only interpretation per D11.

**Output.** `outputs/comparison/` with per-sweep subdirectories mirroring 2D structure.

### Tier 2 model guidance

Sonnet 4.6 for the entire tier — this is mechanical porting plus orchestration, well-suited to Sonnet's strengths and cost profile. Opus only needed if the comparison tables surface a result that seems to contradict Tier 1's interpretation, which would warrant a diagnostic session.

## Tier 3 — Figures, videos, and writeup

### Tier 3.A — Publication figure composition

Figure set, each composed with the Tier 1 interpretation as the organizing frame:

1. **Compressibility-across-sweeps panel** (primary figure). 3×4 grid: rows are alignment, jamming, leadership; columns are (per-window Φ distribution at coherent condition, per-window Φ distribution at disordered condition, σ_u across conditions, cross-seed phi_norm σ across conditions). Demonstrates the compressibility signature holds across perturbation axes (or does not, depending on Tier 1.A verdict).
2. **Time-series overlays per scenario.** Φ_spectral(t), polarization(t), snap_TP_1(t), snap_TP_0(t) on shared time axis. Annotated event windows (jam on/off, split on/off).
3. **Sensitivity bar charts per sweep.** η² with bootstrap CIs. KSG primary; Gaussian as cross-estimator validation. Histogram not plotted (sign-only interpretation does not render well in bar charts).
4. **Agreement/divergence heatmap.** Spearman correlations between metric families across all sweeps. H2 columns included. The "when do spectral and topological agree vs diverge" figure.
5. **Matched-control deltas.** Event-driven perturbation response per metric, pre/during/post bars.
6. **Surrogate null comparison.** Observed vs surrogate Φ_spectral per scenario, with z-scores.
7. **Monitoring ROC.** Per-metric AUC for detecting perturbation onset, combined across event sweeps.
8. **3D scenario snapshots.** `plot_snapshot_3d` output for each of the 5 scenarios at a representative step, Fiedler-partition colored.

### Tier 3.B — Scenario animations

`animate_trajectory_3d` for each of the 5 scenarios (none, alignment at transitional w_a, jamming, split-merge, milling). One seed each. MP4 output via ffmpeg writer. File size under 30 MB each.

`render_scenario_videos.py` orchestrates. Per-scenario parameters chosen to visually exhibit the relevant dynamical regime: jamming video should span the full jam on/off interval; split_merge video should span the split/merge transitions; milling video should show the rotational steady state.

### Tier 3.C — Internal report draft

A 3D analog of `Internal_Report_2D_Swarm.odt`. Approximately 15–20 pages. Structure:

1. **Introduction** — 3D extension of Bailey (2026), methodology restorations from Cluster A, decisions D11–D14 as methodological context.
2. **Methods** — 3D simulator, observables, sweep design, estimator choices, compressibility mechanism as pre-registered interpretive frame.
3. **Results — Primary pass/fail** — milling monotonicity, snap_TP_1 jamming separation. Brief, since these are confirmed.
4. **Results — Compressibility mechanism** — the main empirical contribution. Tier 1 findings. Whether leadership prediction confirmed. Per-window distribution evidence.
5. **Results — Spectral vs topological comparison** — Tier 2 aggregated tables, agreement/divergence heatmap, the "when do they diverge" finding from core Bailey 2026 hypothesis.
6. **Surrogate null validation** — Tier 2.B.
7. **Anomalies** — A1 (angular_momentum_norm 3D geometry), A3 (split-merge non-replication). Brief.
8. **Limitations** — N=40 finite-size, histogram saturation (D11), trajectory-cloud exploratory-only (D10).
9. **Next directions** — N-scaling, synchronic/diachronic separation (ResearchContext.md §4.9), cross-substrate (§4.10).

Writeup posture: compressibility is the primary empirical contribution; primary pass/fail is confirmed and reported compactly; the 2D→3D methodological extensions are reported in Methods and referenced in Cluster A.

### Tier 3 model guidance

Sonnet 4.6 for figure generation code and animation rendering. Opus 4.7 at xhigh or max for figure composition decisions (which panels go in the primary figure, how to frame ambiguous results) and for the internal report draft — this is the interpretive writing where Opus's reasoning depth matters most.

## Estimated effort

- Tier 1: 1–2 days. Mostly Opus reasoning time plus Sonnet running the aggregation scripts. No new simulation.
- Tier 2: 4–5 days. Code port (2 days — comparison.py extension including the new per-window distribution summary columns, which aggregate from per-window values already in the Phase 4 parquets, not from raw telemetry), surrogates (1 day), aggregation runs (1 day — the comparison pipeline operating on existing Phase 4 parquets, no re-analysis of telemetry required since `phi_saturation_ratio`, H2 columns, and `angular_momentum_norm` are all already in Phase 4 output), verification (1 day).
- Tier 3: 4–6 days. Figures (2 days), animations (1 day), internal report draft (2–3 days).

Total: roughly 10–13 days of focused work. Can be split across multiple Claude Code sessions at natural boundaries (after Tier 1, after Tier 2).

## Pass/Fail

**Tier 1 pass/fail.**
- [ ] Leadership prediction verdict document produced with numeric support for the chosen outcome (one of the four outcomes in Tier 1.A).
- [ ] MI matrix mechanism diagnostic run on at least one λ=2.4 seed and one λ=0.0 seed; structure compared to A2 jamming signature. Outcome 1 vs Outcome 4 explicitly discriminated.
- [ ] Tier 1.B scope determined based on Tier 1.A outcome (full atlas vs narrower focused atlas) and documented before rendering begins.
- [ ] Per-window distribution atlas produced in the scope set by 1.A.
- [ ] Cross-sweep compressibility audit table produced with per-condition triple-correlation values.
- [ ] Tier 1 interpretation committed before Tier 2 code work begins (natural session boundary).

**Tier 2 pass/fail.**
- [ ] All 11 sweeps processed by `run_comparison.py` without errors.
- [ ] η² tables include bootstrap CIs per D2.
- [ ] Histogram-estimator columns flagged for sign-only interpretation per D11.
- [ ] Agreement/divergence heatmaps include H2 columns.
- [ ] Surrogate nulls completed for all 6 primary scenarios; observed-vs-null summary document produced.
- [ ] At least one sweep shows spectral-topological divergence (core Bailey 2026 hypothesis).

**Tier 3 pass/fail.**
- [ ] Compressibility-across-sweeps panel figure produced (primary figure).
- [ ] All 7 supporting figures produced at publication quality.
- [ ] 5 scenario MP4s produced, each under 30 MB.
- [ ] Internal report draft completed at approximately 15–20 pages.
- [ ] All figures and tables reproducible from saved telemetry and analysis code per D6 metadata.

## What is explicitly out of scope for Phase 5

- N-scaling runs (ResearchContext.md §4.8). Mentioned in Next Directions; not executed.
- Synchronic/diachronic separation estimator (§4.9). Future work.
- Cross-substrate comparison (§4.10). Future work.
- Any change to Phase 1–4 code modules (`model.py`, `agent.py`, `scenarios.py`, `telemetry.py`, `features.py`, `mi.py`, `spectral.py`, `tda.py`, `aggregation.py`). If a bug is surfaced, flag to the user for a separate maintenance session rather than patching inside Phase 5.
- Phase 4.5 mechanism probe for split-merge (deferred indefinitely per D13).
- Any revision to Cluster D decisions or the Phase 4 pass/fail criteria. If Tier 1 findings suggest a decision needs revision, that's a planning-level conversation, not a Phase 5 edit.

## Session structure

A clean way to execute Phase 5 across Claude Code sessions:

1. **Session 1 (Opus max).** Tier 1.A leadership prediction analysis. Produces verdict document. Pauses for user review.
2. **Session 2 (Sonnet).** Tier 1.B distribution atlas. Mechanical. Runs while user is reviewing Session 1 output.
3. **Session 3 (Opus max).** Tier 1.C cross-sweep compressibility audit. Produces the organizing verdict for Phase 5 writeup.
4. **Session 4 (Sonnet).** Tier 2.A comparison pipeline port. Long agentic session.
5. **Session 5 (Sonnet).** Tier 2.B surrogate nulls.
6. **Session 6 (Sonnet).** Tier 2.C aggregated comparison runs.
7. **Session 7 (Opus xhigh).** Tier 3.A figure composition — which panels, what the primary figure looks like, how to frame ambiguous outcomes.
8. **Session 8 (Sonnet).** Tier 3.A figure generation code + Tier 3.B animation rendering.
9. **Session 9 (Opus max).** Tier 3.C internal report draft.

Each session ends with commit + push. Multi-session recovery is the same pattern as Phase 4 Part C.

## Open questions for planning-level discussion before Phase 5 starts

None blocking, but worth flagging:

1. Does the internal report target a specific journal or conference, or is it an internal deliverable only? This affects figure formatting and reference style. *Recommended resolution: defer. Draft as internal deliverable first, decide venue after results are visible.*
2. Is the 2D internal report's structure the intended template, or should the 3D report restructure around the compressibility finding as the lead result? *Genuinely outcome-dependent. Decided at the end of Session 1: if Tier 1.A yields Outcome 1, compressibility is the headline and leads; if Outcomes 2–4, mirror the 2D report's structure more closely and position jamming as a standalone finding. The choice and rationale are documented in the Tier 1.A verdict file.* **Resolved (Tier 1.A verdict, commit `9ad6a5a`):** 2D-mirror with compressibility positioned as a jamming-specific finding. Outcome 4 in Tier 1.A means the compressibility-lead structure is not warranted. The 3D internal report follows the 2D template structurally, with a dedicated subsection for compressibility (jamming) and separate subsections for transitional bimodality (alignment) and the leader-block-partition finding (leadership Outcome 4).

(The representative-seed question from earlier drafts has been resolved: seed 0 uniformly for surrogates, pre-committed for reproducibility.)
