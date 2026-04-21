# Decision D9 — H2 sampling density

**Status:** Closed — Option 3 adopted. See Closure section.
**Phase opened:** 3.
**Phase to close by:** 4 planning.
**Related:** SpectralSwarm3DPhases.md clusters B3, B4; Phase 4 milling-sweep pass/fail criterion.

## Problem

Phase 3 end-to-end positive control `MP_2(milling snapshot) > MP_2(baseline snapshot)` fails at methodology-spec N=40. Empirical measurement at T=500, seed=0: baseline MP_2 ≈ 0.18 (noise), milling MP_2 ≈ 0.07.

Root cause: nearest-neighbor spacing on the milling shell of radius ~13 is ~7.3, which exceeds the rule-of-thumb R/3 ≈ 3.7 threshold for reliable Vietoris-Rips H2 void detection. At this sampling density, Rips complexes on the shell do not close the void before noise fills it, and baseline noise produces more spurious H2 than the shell produces real H2.

## Impact

Phase 3: one strict xfail on `test_milling_mp2_exceeds_baseline_mp2` in `tests/test_phase3_integration.py`.

Phase 4: the milling-sweep pass/fail criterion from `SpectralSwarm3DPhases.md` — "`snap_TP_2` increases with μ for μ ≥ 0.4 (positive control for H2 void detection in spherical shell)" — will fail for the same reason unless this decision resolves N or embedding.

Phase 5: the H2 interpretation rests on this signal being resolvable. If H2 isn't working, the "dimension-specific analytical reach" framing in the project overview needs qualification.

## Options

### A. Raise N project-wide

Estimated target: N ≈ 120. This brings nearest-neighbor spacing to ≈ R/3 ≈ 3.7 on the milling shell.

- **Pros:** TDA works as intended across H0/H1/H2. Phase 4 milling-sweep criterion becomes achievable. All downstream interpretation of H2 as a signature of 3D-unique structure remains valid.
- **Cons:** Methodology §3.1 specifies N=40. Deviating is a documented deviation, not catastrophic but significant. KSG MI compute cost scales O(N²), so 3× N is 9× Phase 4 sweep compute. Breaks direct 2D-to-3D N matching.

### B. Flip `snapshot_augmented` default to true for H2-dependent analysis

Use `(x, y, z, 0.35*vx, 0.35*vy, 0.35*vz)` as the snapshot for H2 computation. Augmented embedding exploits the velocity coherence of milling agents to add topological structure the spatial positions alone can't resolve at N=40.

- **Pros:** No change to N. This is the methodology-specified robustness analysis (§3.5), already implemented. Keeps compute budget.
- **Cons:** The H2 being detected is in 6D position-velocity space, not 3D spatial space. The interpretive claim shifts: not "H2 detects spatial voids unique to 3D" but "H2 detects higher-dimensional coordination structure." Requires careful framing in Phase 5 writeup.

### C. Other (retained as possibility pending data)

Raise `milling_R` to improve shell curvature-to-density ratio, change Vietoris-Rips parameters, switch to a different filtration, or accept H1-only analysis for production sweeps. Each has tradeoffs; none pursued unless diagnostic data rules out A and B.

## Diagnostic plan

Before choosing, run a sweep over `(N, embedding) ∈ {40, 80, 120, 160} × {unaugmented, augmented}` on baseline and milling, at T=500, seed=0. Record MP_2, TP_2, and shell geometry diagnostics. Script lives at `scripts/diagnostics/tda_h2_sampling_sweep.py`; results at `outputs/diagnostics/tda_h2_sampling_sweep.{csv,md}`.

Decision rule: whichever combination produces `milling MP_2 / baseline MP_2 ≥ 2.0` at the lowest N is preferred. If both A at N=80 and B at N=40 work, B is preferred (lower compute, methodology-supported). If only A at N ≥ 120 works, A is accepted as a deviation with rationale documented.

## Resolution

### Investigation: sampling-density sweep results

A diagnostic sweep (commit 59b5184, script `scripts/diagnostics/tda_h2_sampling_sweep.py`, results at `outputs/diagnostics/tda_h2_sampling_sweep.{csv,md}`) ran both scenarios over `(N, embedding) ∈ {40, 80, 120, 160} × {unaugmented, augmented}` at T=500, seed=0, recording MP_2, shell geometry, and nearest-neighbor spacing. The sweep refutes the undersampling hypothesis in the original Problem section. At N=40, measured nearest-neighbor spacing on the milling shell is ~0.17 — not the predicted ~7.3 that motivated the D9 opening. Neither raising N nor switching to augmented embedding produces a milling/baseline MP_2 ratio ≥ 2.0. At N=160 (16× the methodology-spec agent count), milling MP_2 reaches 0.52 against baseline MP_2 of 0.34, giving a ratio of only 1.55.

| N   | Scenario | Embedding   | MP_2  | NN spacing (milling) | Shell thickness |
|-----|----------|-------------|-------|----------------------|-----------------|
| 40  | baseline | unaugmented | 0.431 | —                    | —               |
| 40  | baseline | augmented   | 0.431 | —                    | —               |
| 40  | milling  | unaugmented | 0.000 | 0.168                | 0.643           |
| 40  | milling  | augmented   | 0.000 | 0.169                | 0.643           |
| 80  | baseline | unaugmented | 0.296 | —                    | —               |
| 80  | milling  | unaugmented | 0.336 | 0.172                | 0.693           |
| 120 | baseline | unaugmented | 0.313 | —                    | —               |
| 120 | milling  | unaugmented | 0.111 | 0.091                | 0.894           |
| 160 | baseline | unaugmented | 0.338 | —                    | —               |
| 160 | milling  | unaugmented | 0.524 | 0.077                | 0.938           |

Augmented embedding columns are omitted from the table; they are numerically indistinguishable from unaugmented (differences confined to the fourth decimal) at every N, confirming Option B provides no leverage on this failure mode.

The reframed root cause is Vietoris-Rips over-triangulation on a thin dense shell, not undersampling. Milling agents pack tightly on a shell of radius ~13.3 and thickness ~0.64–0.94. Because nearest-neighbor spacing (~0.08–0.17) is far smaller than the shell radius, Rips complexes fill the interior of the shell at ε far below the scale needed to detect the void: every agent is already connected to its neighbors on the opposite side of the thin shell before ε approaches the shell's radius. The resulting complex is topologically equivalent to a filled ball, so H2 = 0. This is a known failure mode of Vietoris-Rips on thin structures: the filtration cannot distinguish a thin shell from a solid object when the sampling is dense relative to thickness but sparse relative to radius (Zomorodian & Carlsson 2005, §4 — persistence of Rips complexes on manifolds requires ε to probe the embedding geometry, not merely the local point spacing). Increasing N makes the shell denser and therefore thinner in normalized terms, which only worsens the ratio at intermediate N (N=120 is worse than N=80) before recovering slightly at N=160.

### Refined options

#### Option 1 — Trajectory-cloud H2

Instead of computing H2 on the spatial snapshot cloud at a fixed time T, compute H2 on the trajectory cloud: the set of all agent positions concatenated across W time-steps, giving a cloud of `N×W` points in ℝ³ (or ℝ⁶ if augmented). A milling trajectory traces a closed loop, so its trajectory cloud has strong H1 signal; collectively the N agent trajectories sample a toroidal or spherical surface in trajectory space, potentially producing H2 that baseline random-walk trajectories do not. This approach is methodology-supported: Bailey 2026 §3.5 discusses trajectory-space embeddings as a complement to snapshot embeddings, and Perea & Harer 2015 establish that time-delay and trajectory-based persistence reliably detects periodic and quasi-periodic structure that static snapshots miss.

- **Pros:** No change to N or filtration method. Directly addresses the geometric problem: trajectory clouds for milling agents sample a closed surface in trajectory space rather than a thin shell in position space, so the Rips complex can close a void at ε well below the shell-scale issue. Methodology-grounded. No new dependencies.
- **Cons:** Requires a new diagnostic to confirm the trajectory-cloud H2 signal is empirically distinguishable at N=40. Introduces a W (window width) hyperparameter that affects compute and must be justified. The interpretive claim becomes "H2 detects trajectory-space topology of collective motion" rather than "H2 detects spatial voids," which requires a careful Phase 5 reframing — but this is arguably a stronger 3D-specific claim.

#### Option 2 — Alpha complex filtration

Replace the Vietoris-Rips filtration with an alpha complex filtration (via `gudhi`) for H2 computation. Alpha complexes are sub-complexes of the Delaunay triangulation and use circumradius, not pairwise distance, to define the filtration. On a thin shell, the circumradius of a simplex spanning the shell thickness grows much faster than the pairwise edge lengths, so the alpha complex does not fill the interior of the shell at small ε — it respects the shell's geometric structure. Alpha complexes are provably equivalent to Čech complexes and are the correct filtration for point clouds drawn from manifolds with boundary (Zomorodian & Carlsson 2005, §3).

- **Pros:** Directly fixes the over-triangulation failure mode. Well-understood theoretical guarantees. Does not require changing N, W, or embedding.
- **Cons:** This is a methodology deviation — Bailey 2026 specifies Vietoris-Rips throughout. Requires explicit justification and documentation as a deviation. Adds `gudhi` as a new dependency (currently only `ripser` is used for TDA). The Phase 4 sweep and Phase 5 interpretation must be re-validated under the new filtration. Highest implementation cost of the three options.

#### Option 3 — Accept as null result, rely on H0/H1 and trajectory-cloud H2

Document H2-on-Rips-snapshots as a non-result for milling detection at methodology-spec N. Formally close the strict xfail test as a known limitation; retain H0 and H1 as the primary TDA observables for Phase 4 sweeps. Reserve H2 claims for trajectory-cloud analysis (Option 1) if the follow-up diagnostic validates it, and note in the Phase 5 writeup that the "dimension-specific analytical reach" framing applies to H0/H1 topology and trajectory-space H2, not to snapshot-space H2 void detection.

- **Pros:** Methodologically honest. Avoids introducing deviations (Option 2) or unvalidated hyperparameters (Option 1's W). H0 and H1 are already working well. The Phase 4 milling-sweep criterion can be rewritten to use H1 persistence instead of H2, which is consistent with the milling dynamics (closed loops → H1, not H2, at snapshot scale).
- **Cons:** Weakens the "3D-unique structure" claim that motivated H2 inclusion in Phase 1. If a reviewer or collaborator asks why H2 is in the paper but adds no signal, the answer requires explaining both the geometric pathology and the decision not to fix it. Requires updating Phase 4 pass/fail criteria before the phase begins.

## Next step

A trajectory-cloud H2 diagnostic (Option 1) will be run before D9 is closed. If trajectory-cloud H2 produces a milling/baseline MP_2 ratio ≥ 2.0 at N=40 with a defensible choice of W, Option 1 is accepted and D9 is closed as resolved in its favor. If not, Option 3 is accepted by default with a note that Option 2 is available as a future deviation if H2-void detection becomes essential to a Phase 5 claim. The strict xfail on `test_milling_mp2_exceeds_baseline_mp2` in `tests/test_phase3_integration.py` remains in place with its existing reason string; it is the correct marker for this open decision and will be removed only when D9 closes.

## Closure

A trajectory-cloud H2 diagnostic (commit 23a8d4f, script `scripts/diagnostics/tda_trajectory_h2_diagnostic.py`, outputs at `outputs/diagnostics/tda_trajectory_h2_diagnostic.{csv,md}`) tested whether computing H2 on trajectory clouds — the set of N×W agent positions concatenated across W time-steps — could produce a milling/baseline MP_2 ratio ≥ 2.0 at N=40. The diagnostic ran both scenarios at W=40 and W=80 (unaugmented, seed=0), producing four rows in total. MP_2 is uniformly zero across all four rows. The geometric reason is distinct from the snapshot over-triangulation pathology identified in commit 59b5184: trajectory clouds at W=40 comprise 40×40 = 1600 points embedded in ℝ^(3×40) = ℝ^120 ambient space (or ℝ^(3×80) = ℝ^240 at W=80). At 40 agents, the point cloud is far below the minimum coverage needed for Vietoris-Rips to close an H2 void in ambient spaces of 120–320 dimensions. This is under-coverage in high ambient dimension — a different pathology from snapshot over-triangulation — but produces the same null H2 result.

Option 3 is adopted: snapshot-space H2 on Vietoris-Rips is accepted as a null result for milling detection at methodology-spec N=40, and the project relies on H0 and H1 as the primary TDA observables for Phase 4 sweeps. Options A and B are not adopted: both were empirically ruled out by the sampling-density sweep (commit 59b5184), which showed no combination of N ∈ {40, 80, 120, 160} × {unaugmented, augmented} achieved a milling/baseline MP_2 ratio ≥ 2.0. Option 1 (trajectory-cloud H2) is not adopted: empirically ruled out by commit 23a8d4f. Option 2 (alpha complex filtration) is not adopted at this time but is preserved as a future escape hatch: if Phase 5 claims require H2-void detection in position space, alpha complexes remain available as a deviation with documented justification. The rationale for not needing Option 2 now is the secondary finding described below, which provides a viable H1-based alternative.

**Secondary finding: trajectory H1 at W=80 distinguishes milling cleanly.** At W=80, one seed, the trajectory-cloud H1 signal sharply separates the two scenarios: baseline trajectory MP_1 ≈ 0.007 while milling trajectory MP_1 ≈ 0.506, a ratio of approximately 70×. This is exactly what Perea & Harer 2015 predicts: milling agents trace closed loops in 3D position space, so their trajectory clouds in ℝ^(3×80) sample a toroidal or loop-like surface with strong H1 signal, while baseline agents executing random walks produce no such closed structure. This finding means the project's "dimension-specific analytical reach" claim is intact — it applies to trajectory-cloud H1 as a signature of 3D periodic collective motion rather than snapshot-space H2 void detection. This is a preliminary single-seed observation; a multi-seed variance check is required before Phase 4 relies on it. The variance-check diagnostic will live at `scripts/diagnostics/tda_trajectory_h1_variance.py` and will be run as a separate session before Phase 4 begins.

**Variance check (5 seeds) refutes the single-seed finding.** The 5-seed result (commit 208b135, outputs at `outputs/diagnostics/tda_trajectory_h1_variance.{csv,md}`): only 2/5 seeds showed milling > baseline, with a mean ratio of 14.6× dominated entirely by seed 0's 69.5× outlier; the other four seeds fall in the 0.46–1.15 range. The interpretation: baseline flocking at w_a=1.0 produces coherent collective motion whose trajectory cloud has nontrivial H1 for the same reason milling does — parallel curves in trajectory space produce transient H1 under small fluctuations, not only closed orbits do. Both scenarios generate H1, just via different mechanisms; H1 alone does not distinguish them reliably. The implication: Phase 4's milling-sweep positive control needs to come from classical milling measures (`milling_score_magnitude`, `angular_momentum_norm`, `polarization`) already in `classical.py`, not from trajectory-cloud H1. TDA metrics remain useful as complementary observables for Phase 5 interpretation but are not primary sweep validity checks. The broader question of whether other Phase 4 sweeps should also rebalance classical-vs-TDA as primary-vs-complementary is flagged for Phase 4 planning; no change is made here.

**Implications for Phase 4 and beyond.** The Phase 4 milling-sweep pass/fail criterion from `SpectralSwarm3DPhases.md` — "`snap_TP_2` increases with μ for μ ≥ 0.4 (positive control for H2 void detection in spherical shell)" — needs to be rewritten to target classical milling measures (`milling_score_magnitude`, `angular_momentum_norm`) with the TDA metrics kept as secondary observables. This rewrite is not done in this session; it is a Phase 4 planning task to be completed when Phase 4 begins. The Phase 3 snapshot-H2 infrastructure in `tda.py` — `maxdim=2` Ripser calls, `TP_2`/`MP_2`/`bottleneck_2` in `persistence_summaries` — is preserved as-is: it runs, it produces correct null results, and it remains usable if a future diagnostic reopens the question. No refactor is justified on the basis of a confirmed null result. The `snapshot_augmented` config flag is similarly preserved with its default of `false`: augmented embedding provided no leverage in the sampling-density sweep (differences confined to the fourth decimal at every N), so flipping the default would add compute cost for no gain.

## References

- Cohen-Steiner et al. 2007 — Lipschitz stability of bottleneck distance (D8 connection).
- Bailey 2026 §3.5 — augmented snapshot embedding (Option B methodology basis).
- Zomorodian & Carlsson 2005 — Rips complexes and persistence foundations (sampling-density requirement folklore).
- `SpectralSwarm3DPhases.md` — Cluster B3 (augmented embedding), B4 (H2 extension), Phase 4 milling-sweep criterion.
