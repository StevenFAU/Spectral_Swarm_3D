# Phase 3 — TDA Pipeline

This document specifies the Phase 3 work for the 3D extension of the Spectral Swarm project. It is intended to be executed by Claude Code as a standalone unit of work. The full project plan is in `SpectralSwarm3DPhases.md`; this document narrows that plan to exactly what Phase 3 produces.

**Pre-requisites.**
- Phase 2 is complete and committed on `main`. `pytest tests/ -v` shows 74 passing, zero failing, zero errors.
- `configs/default.yaml` has `tda_maxdim: 2`, `snapshot_augmented: false`, `snapshot_beta: 0.35`.
- Before starting, read `SpectralSwarm3DPhases.md` Phase 3 section and Cluster B items B3 (augmented snapshot embedding) and B4 (H2 persistent homology). Also read D8 on bottleneck-vs-total-persistence distinction.

**Scope of Phase 3.** Implement `analysis/tda.py`: snapshot cloud and trajectory cloud construction, persistent homology computation through H2 via Ripser, and persistence diagram summary metrics. Extend the test suite with `tests/test_tda.py` covering H0/H1/H2 correctness on synthetic positive-control inputs and end-to-end verification on Phase 1 telemetry.

**Out of scope for Phase 3.** No sweep orchestration, no aggregation pipeline, no plotting, no comparison against Φ_spectral, no surrogate null testing. The TDA branch computes persistence summaries per window; connecting those to sweep-level aggregates is Phase 4 work.

---

## Target state at end of Phase 3

One module populated:

- `src/spectral_swarm_3d/analysis/tda.py` — snapshot/trajectory clouds, `compute_persistence(maxdim=2)`, `persistence_summaries` returning TP_k, MP_k, B_base_k, B_prev_k for k ∈ {0, 1, 2}.

One test file with real assertions:

- `tests/test_tda.py` — synthetic positive controls for each homology dimension, structural invariants (symmetry, stability sanity check per D8), and end-to-end verification on Phase 1 telemetry.

---

## Task order

### Task 1 — Snapshot cloud construction (B3)

```python
def snapshot_cloud(
    positions: np.ndarray,
    augmented: bool = False,
    velocities: np.ndarray | None = None,
    beta: float = 0.35,
) -> np.ndarray:
    """Build a point cloud from a single timestep's agent positions.

    Parameters
    ----------
    positions : np.ndarray
        Shape (N, 3) agent positions in 3D.
    augmented : bool
        If True, concatenate velocities scaled by beta per Bailey (2026) §3.5:
        y_i = (x_i, y_i, z_i, beta * vx_i, beta * vy_i, beta * vz_i).
        If False, return positions as-is.
    velocities : np.ndarray or None
        Shape (N, 3). Required if augmented=True.
    beta : float
        Velocity scaling factor. Default 0.35 per methodology §3.5.

    Returns
    -------
    np.ndarray
        Shape (N, 3) when augmented=False, (N, 6) when augmented=True.
    """
```

**Tests:**
- `augmented=False`: output shape is `(N, 3)` and equal to input positions.
- `augmented=True` with default beta: output shape is `(N, 6)`; first 3 columns match positions, last 3 match `0.35 * velocities`.
- `augmented=True` but `velocities=None`: raises `ValueError` with a clear message.

### Task 2 — Trajectory cloud construction

```python
def trajectory_cloud(features_window: np.ndarray) -> np.ndarray:
    """Build a trajectory cloud from a flattened window of per-agent features.

    Per Bailey (2026) §3.5 and Perea & Harer (2015), sliding-windows-and-
    persistence theory. Each agent's W time steps of d-dimensional features
    are flattened into a single W*d-dimensional point.

    Parameters
    ----------
    features_window : np.ndarray
        Shape (W, N, d). Must be standardized (D3) upstream of this call;
        this function does not re-standardize.

    Returns
    -------
    np.ndarray
        Shape (N, W*d).
    """
```

Standardization is an upstream responsibility here — the spectral pipeline already standardizes in `phi_spectral_over_windows`; if `trajectory_cloud` re-standardized, it would couple in a way that's hard to debug. Document this in the docstring.

**Tests:**
- Output shape is `(N, W*d)`.
- Flattening is consistent: `out[i, :]` equals `features_window[:, i, :].reshape(-1)`.
- At d=4, W=40 (Phase 2 defaults), ambient dimension is 160. Verify.

### Task 3 — Persistence computation

```python
def compute_persistence(X: np.ndarray, maxdim: int = 2) -> list[np.ndarray]:
    """Compute persistent homology through dimension maxdim via Ripser.

    Parameters
    ----------
    X : np.ndarray
        Shape (n_points, ambient_dim) point cloud.
    maxdim : int
        Maximum homology dimension. Default 2 per Bailey (2026) §3.5 extension
        for 3D; H2 detects enclosed voids.

    Returns
    -------
    list of np.ndarray
        [dgm_H0, dgm_H1, dgm_H2] at maxdim=2. Each dgm is shape (n_features, 2)
        with birth/death times. Infinite death features are represented with
        np.inf and handled by summary functions.
    """
```

Use `ripser.ripser(X, maxdim=maxdim)['dgms']` — this returns a list indexed by homology dimension. Default `thresh` (maximum edge weight) is fine; do not set it explicitly unless a later phase needs it.

**Tests:**
- Tight cluster (all points near origin, small noise): `TP_0 ≈ 0` (only one connected component persists), `TP_1 ≈ 0`, `TP_2 ≈ 0`.
- Two separated clusters (6 points each, two groups 10 units apart): `TP_0 > 0` (the second component's birth/death is a visible bar), `TP_1 ≈ 0`, `TP_2 ≈ 0`.
- Planar ring (60 points on a circle embedded in 3D, small noise): `TP_1 > 0`, `TP_2 ≈ 0`. Verifies H2 does not false-positive on rings (the 2D ring is a circle, which has H1 but no H2).
- Spherical shell (60 points on radius-R sphere, small noise): `TP_2 > 0`, and specifically `MP_2` is large relative to `MP_1`. The sphere is the canonical H2 positive control.

### Task 4 — Persistence diagram summaries

```python
def persistence_summaries(
    dgms: list[np.ndarray],
    baseline_dgms: list[np.ndarray] | None = None,
    prev_dgms: list[np.ndarray] | None = None,
    maxdim: int = 2,
) -> dict[str, float]:
    """Compute scalar summaries of persistence diagrams.

    For each dimension k in 0..maxdim, returns:
      - TP_k: total persistence (sum of death-birth over finite features)
      - MP_k: max persistence (max death-birth over finite features)
      - B_base_k: bottleneck distance to baseline_dgms[k] if provided, else NaN
      - B_prev_k: bottleneck distance to prev_dgms[k] if provided, else NaN

    Parameters
    ----------
    dgms : list of np.ndarray
        [dgm_H0, dgm_H1, dgm_H2] from compute_persistence.
    baseline_dgms : list of np.ndarray or None
        Reference persistence diagrams for bottleneck comparison. Typically the
        first-window diagrams. None skips B_base computation.
    prev_dgms : list of np.ndarray or None
        Previous-window diagrams for sliding comparison. None skips B_prev.
    maxdim : int
        Highest homology dimension to summarize. Must match len(dgms) - 1.

    Returns
    -------
    dict[str, float]
        Keys: TP_0, TP_1, TP_2, MP_0, MP_1, MP_2, B_base_0, B_base_1, B_base_2,
        B_prev_0, B_prev_1, B_prev_2. Missing bottleneck entries are NaN.
    """
```

Use `persim.bottleneck` for bottleneck distances. Handle infinite-death features: for TP and MP, drop infinite-death bars from the sum/max (a common convention). For bottleneck, persim handles them — pass through.

**Tests:**
- TP and MP are non-negative.
- Bottleneck-to-self is exactly 0 (stability sanity check per D8 — Cohen-Steiner et al. 2007).
- MP ≤ TP for each k (max is at most the sum).
- Missing baseline_dgms / prev_dgms yields NaN for the corresponding bottleneck fields (not 0, not error).
- On the spherical shell synthetic: `MP_2` is substantially larger than `MP_1` (sphere's H2 is the dominant signal).

### Task 5 — Bottleneck stability sanity check (D8)

One dedicated test verifying the Cohen-Steiner stability theorem is empirically in effect:

```python
def test_bottleneck_stability_linear_in_noise():
    """Perturbing a point cloud by Gaussian noise of sigma produces a
    bottleneck distance that scales approximately linearly in sigma for small
    sigma. Sanity check that the stability theorem's applicability isn't
    broken by some upstream bug."""
```

Construct a base cloud (say, 40 points on a small cube's corners or a simple shape with clean H0/H1), compute its persistence. Then perturb with `sigma ∈ {0.0, 0.05, 0.1, 0.2}`, compute persistence of each perturbed version, compute bottleneck distance to the baseline diagram for each sigma. Assert the bottleneck distance grows monotonically with sigma, and that the ratio `bottleneck(sigma=0.2) / bottleneck(sigma=0.05) < 10` (loose upper bound — linear growth would give ratio ~4). Use fixed seed for reproducibility.

This is the D8 pass/fail criterion from `SpectralSwarm3DPhases.md`. If it fails, either Ripser is misconfigured or persim's bottleneck implementation has changed behavior — both worth catching.

### Task 6 — End-to-end integration test on Phase 1 telemetry

`tests/test_phase3_integration.py`:

1. Run a 100-step baseline simulation at seed 0 (same pattern as `test_phase2_integration.py`).
2. At a single representative step (say step 50), extract positions (and velocities if testing augmented=True).
3. Build snapshot cloud, compute persistence through H2, compute summaries.
4. Assert all fields are present and finite (except NaN bottleneck fields when baseline/prev not provided).
5. Run the same on a milling scenario (load config with `milling_mu: 0.8`) — assert `MP_2` on the milling snapshot is larger than on the baseline snapshot at the same step. This is the end-to-end positive control: the spherical shell produced by the 3D velocity-projected milling tangent (A3) should show up in H2.

This test is the bridge between Phase 1's simulator output and Phase 3's TDA output. If it passes, the TDA branch is hooked up correctly to the same pipeline the spectral branch uses.

---

## Pass/Fail

- [ ] `pytest tests/ -v` passes. Count should be 74 (Phase 1 + 2) + N (Phase 3 new tests) with zero failures.
- [ ] `tda.py` exists with all five functions (`snapshot_cloud`, `trajectory_cloud`, `compute_persistence`, `persistence_summaries`) and each has real implementation (no `NotImplementedError`).
- [ ] All four synthetic positive controls pass (tight cluster, two clusters, planar ring, spherical shell).
- [ ] Bottleneck-to-self is 0 (stability sanity).
- [ ] D8 bottleneck stability linearity test passes.
- [ ] End-to-end test on Phase 1 milling telemetry produces `MP_2` > baseline's `MP_2`.
- [ ] `ruff check .` is clean.
- [ ] Pipeline handles a 500-step 3D telemetry in < 300 seconds — time the integration test at full T=500 milling run and note the wall time in the commit message. (This is Phase 3 pass/fail criterion from `SpectralSwarm3DPhases.md`.)

---

## Reminders

**Do not change Phase 1 or Phase 2 code.** If a Phase 2 module needs a minor extension (e.g., features.py exposing a helper for trajectory cloud construction), stop and report — don't silently restructure.

**Ripser API surface.** `ripser.ripser(X, maxdim=K)` returns a dict; the `'dgms'` key holds the list of diagrams. Do not use the lower-level `ripser.Rips` class unless there's a specific reason — the plain function is simpler and sufficient.

**Infinite-death convention.** H0 always has exactly one infinite-death feature (the single connected component at threshold infinity). Drop it from TP and MP sums — otherwise TP_0 is always infinity and meaningless. Document this in the docstring.

**Do not conflate snapshot and trajectory clouds.** They're different inputs to the same `compute_persistence` function. Snapshot is `(N, 3)` or `(N, 6)`. Trajectory is `(N, W*d)`. Both produce valid persistence diagrams but the geometric interpretation differs significantly. Test both paths.

**Performance watch.** Ripser's runtime at maxdim=2 grows fast with point count. N=40 at 3 ambient dimensions should be fine. Trajectory clouds at 160 ambient dimensions will be slow — if the `test_phase3_integration.py` test at T=500 exceeds 300 seconds, profile before tuning; don't preemptively reduce scope.

**Do not advance to Phase 4 in this session.** Phase 4 starts fresh with the plan re-loaded.
