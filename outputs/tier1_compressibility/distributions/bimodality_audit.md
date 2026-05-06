# Phase 5 Tier 1.B — Bimodality Audit

**Date:** 2026-05-06
**Script:** `outputs/tier1_compressibility/distributions/_make_distributions.py`
**Scope:** Narrower focused atlas per Session 1 Outcome 4 verdict §6.
**Bimodal criterion:** KDE mode count ≥ 2 AND Hartigan dip p < 0.20
**Steady-state:** window_idx ≥ quantile(2/3) per seed (~31 windows/seed × 10 seeds ≈ 310/condition)
**† symbol** denotes conditions that share the "vanilla boids" baseline (see §shared-baseline below).

---

## Table 1: Atlas-scope conditions (all rendered)

| sweep | condition | n_windows | dip p | KDE modes | std/IQR | classification |
|---|---|---|---|---|---|---|
| jamming_sweep | α=0.2 | 310 | 0.984 | 1 | 0.857 | unimodal |
| jamming_sweep | α=0.5 | 310 | 0.720 | 1 | 0.595 | unimodal |
| jamming_sweep | α=1.0 | 310 | 0.914 | 1 | 0.611 | unimodal † |
| alignment_sweep | w_a=0.0 | 310 | 0.861 | 1 | 0.695 | unimodal |
| alignment_sweep | w_a=0.6 | 310 | 0.102 | 2 | 0.551 | bimodal |
| alignment_sweep | w_a=1.2 | 310 | 0.992 | 1 | 0.641 | unimodal |
| alignment_sweep | w_a=1.8 | 310 | 0.962 | 1 | 0.680 | unimodal |
| leadership_sweep | λ=0.8 | 310 | 0.907 | 1 | 0.661 | unimodal |

---

## Table 2: Pre-suspected bimodality candidates (Phase5.md Tier 1.B)

Phase5.md Tier 1.B pre-registered four candidate conditions for bimodality testing.
Conditions marked † share the vanilla-boids baseline (see §shared-baseline).

| candidate | n_windows | dip p | KDE modes | std/IQR | classification | atlas inclusion |
|---|---|---|---|---|---|---|
| alignment w_a=1.8 | 310 | 0.962 | 1 | 0.680 | unimodal | included (verdict recommendation) |
| jamming α=1.0 † | 310 | 0.914 | 1 | 0.611 | unimodal | included (verdict recommendation) |
| leadership λ=0.0 † | 310 | 0.914 | 1 | 0.611 | unimodal | excluded (unimodal, empirical test) |
| milling μ=0.0 † | 310 | 0.914 | 1 | 0.611 | unimodal | excluded (unimodal, empirical test) |

---

## Narrative — D14 "coherent regimes bimodalize Φ"

D14 asserts that "Phase 5 reports per-window Φ distributions (not just steady-state means)
for all sweeps exhibiting coherent regimes," with an implicit claim that coherent-regime
conditions bimodalize Φ across windows. The empirical results do **not** broadly support
this claim in the steady-state-only window pool.

**Jamming α=1.0** — the A2-confirmed compressibility coherent-baseline condition — shows
unimodal steady-state distributions (dip p=0.914, modes=1).
Note: this condition's parquets are byte-identical to leadership_sweep/lambda_0.0 and
milling_sweep/mu_0.0 — all three reduce to vanilla boids (see §shared-baseline); results
describe the unperturbed coherent-flock baseline and are valid for that interpretation.

**Leadership λ=0.8** — identified as bimodal in Session 1 (dip p=0.129, modes=2 over
all 930 windows) — shows unimodal when restricted to steady-state windows only
(dip p=0.907, modes=1, n=310). The Session 1 bimodality was computed
on all windows pooled (transient + steady-state). Restricting to steady-state reverses the
classification: the apparent bimodality in Session 1 reflects a **transient-to-steady-state
regime transition** (early low-Φ windows and late high-Φ windows create two apparent modes
in the all-window pool) rather than within-steady-state bimodality. This is an important
methodological distinction for D14's reporting requirement.

**Unexpected finding — alignment w_a=0.6**: the transitional-alignment condition
(w_a=0.6, not the high-w_a condition pre-suspected by Phase5.md) shows bimodal
steady-state distributions (dip p=0.102, modes=2).
The fully coherent high-alignment condition (w_a=1.8) is unimodal. This suggests
bimodality concentrates at the disorder-to-order transition, not in the fully coherent regime.

Pre-suspected candidates that failed to bimodalize: alignment w_a=1.8, jamming α=1.0, leadership λ=0.0, milling μ=0.0.
A planning-level discussion is recommended before Tier 3.C to clarify D14's mechanism claim:
"coherent regimes bimodalize" is not empirically supported as a general statement;
the finding is better characterized as "bimodality appears at disorder-to-order transitions
(alignment w_a=0.6) and in mixed-regime pooling artifacts (leadership λ=0.8 all-window pool)."

---

## Cross-reference to Session 1 (Tier 1.A leadership λ=0.8)

Session 1 (Tier 1.A) bimodality diagnostics for leadership λ=0.8 used all 930 per-window
Φ values (93 windows × 10 seeds): dip p=0.129, KDE mode count=2, std/IQR=0.593.
This session uses steady-state windows only (~310 per condition, window_idx ≥ quantile(2/3)).

**Result: classification does NOT reproduce on steady-state-only data.**
Steady-state: dip p=0.907, modes=1 → unimodal.

The discrepancy is mechanistically interpretable: at λ=0.8 the system transitions from a
low-Φ early regime to a higher-Φ (but variable) late regime. Pooling all windows creates
a bimodal appearance from regime mixing, not within-regime bimodality. The Session 1
result was computed on all windows per the Tier 1.A methodology (which was designed to
characterize the full run, not steady-state behavior specifically). This session's
steady-state restriction is more appropriate for D14's "steady-state distribution"
reporting requirement.

Both results come from the same parquets (bit-identical data source); the difference
is the window-subset definition.

---

## Shared-baseline equivalence († conditions)

`jamming_sweep/alpha_1.0`, `leadership_sweep/lambda_0.0`, and `milling_sweep/mu_0.0`
are byte-identical across all 10 seeds. This was initially flagged as a potential
data-integrity concern; post-commit verification confirmed it is **expected behavior**
under D6 deterministic seeding. All three conditions reduce to vanilla boids at their
boundary values:

- **jamming α=1.0** — `effective_boids_params` multiplies all boids weights by `jam_alpha=1.0`.
  In IEEE 754, `x * 1.0 = x` exactly (no floating-point error); the jam-window code path
  is numerically identical to the no-jam path. `leader_forces = np.zeros((N,3))`;
  `mill_forces = np.zeros((N,3))`.
- **leader λ=0.0** — `scenarios.leader_waypoint` computes `0.0 * diff / norm = 0.0`
  for each leader agent. Adding `±0.0` to the non-zero noise term does not change the
  bit representation of `v_tilde` (IEEE 754: `x + (±0.0) = x` for finite non-zero x).
- **milling μ=0.0** — `scenarios.milling_force` returns `0.0 * (tau_hat + radial) = 0.0`
  per agent; same ±0.0 argument applies.

RNG initialization is scenario-independent: the leader-designation draw
(`self.rng.choice(N, size=n_leaders, replace=False)`, `model.py:91`) is unconditional —
it runs for all scenarios regardless of `scenario_name`, based only on `leader_fraction`
from config. All three conditions consume the same RNG draws in the same order in
`__init__`, and the only RNG draw in `step()` is the noise draw (`model.py:197`), also
unconditional. The three scenarios therefore share identical RNG state at every step.

No silent scenario-name override exists in `run_sweep.py`: `condition.scenario` is
passed directly to `BoidSwarmModel3D(scenario_name=condition.scenario, ...)` without
transformation.

**Conclusion:** byte-identical parquets are correct. The bimodality results for the
three † conditions (all unimodal) describe the vanilla-boids unperturbed-flock baseline,
which is the appropriate interpretation for each boundary value. No re-run needed.

---

## Recommend planning-level discussion

Before Tier 3.C (internal report draft):
1. **D14 mechanism claim qualification** — "coherent regimes bimodalize Φ across windows"
   is not empirically supported as a general statement by these steady-state results.
   Recommended revised framing: bimodality appears at disorder-to-order regime transitions
   (alignment w_a=0.6) and as a transient-mixing artifact in all-window pooling.
2. **Shared-baseline note for Tier 1.C cross-sweep audit** — the three † conditions
   represent the same unperturbed dynamics. Their identical Φ distributions (unimodal,
   mean≈135, std≈87) provide a consistent baseline reference for the cross-sweep table.
