# Decision D9 — H2 sampling density

**Status:** Open (pending diagnostic sweep).
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

[To be filled in when the diagnostic completes.]

## References

- Cohen-Steiner et al. 2007 — Lipschitz stability of bottleneck distance (D8 connection).
- Bailey 2026 §3.5 — augmented snapshot embedding (Option B methodology basis).
- Zomorodian & Carlsson 2005 — Rips complexes and persistence foundations (sampling-density requirement folklore).
- `SpectralSwarm3DPhases.md` — Cluster B3 (augmented embedding), B4 (H2 extension), Phase 4 milling-sweep criterion.
