# Phase 2 — Φ_spectral Analysis Pipeline

This document specifies the Phase 2 work for the 3D extension of the Spectral Swarm project. It is intended to be executed by Claude Code as a standalone unit of work. The full project plan is in `SpectralSwarm3DPhases.md`; this document narrows that plan to exactly what Phase 2 produces.

**Pre-requisites.**
- Phase 1 is complete and committed on `main`. `pytest tests/ -v` shows 34 passing, zero failing, zero errors.
- `configs/default.yaml` has `w_a: 1.0` marked as calibrated, `alignment_rule: "mean"`, `estimator: "ksg"`, `k_ksg: 5`, `W: 40`, `stride: 1`, `feature_set: "kinematic"`, `n_bins_hist: 8`, `mi_tie_break_noise: 1.0e-10`.
- Before starting, read `SpectralSwarm3DPhases.md` Phase 2 section and Cluster B (analysis decisions). The specifics below override nothing in the main plan; they narrow the scope to what Phase 2 produces.

**Scope of Phase 2.** Implement the Φ_spectral pipeline: feature extraction from telemetry (B1), per-agent per-channel standardization (D3), three MI estimators with KSG as primary (B6), dimension-agnostic normalized Laplacian plus Fiedler bipartition, Φ_spectral time series computation over sliding windows. End-to-end: telemetry CSV → Φ_spectral(t) array. Produce tests that verify each stage against known-answer inputs.

**Out of scope for Phase 2.** No TDA code. No classical baselines beyond what is already in the repo. No sweep orchestration. No comparison pipeline. No plotting. No surrogates.

---

## Target state at end of Phase 2

Four modules populated with real implementations:

- `src/spectral_swarm_3d/analysis/features.py` — feature extraction with three feature sets (B1).
- `src/spectral_swarm_3d/analysis/mi.py` — three estimators plus standardization helper (B6, D3).
- `src/spectral_swarm_3d/analysis/spectral.py` — normalized Laplacian, Fiedler partition, Φ_spectral computation.
- `src/spectral_swarm_3d/analysis/classical.py` — polarization, milling score magnitude, angular momentum norm (B5).

Four test files with real assertions:

- `tests/test_features.py` — feature extraction unit tests.
- `tests/test_mi.py` — MI estimator correctness against analytic cases.
- `tests/test_spectral.py` — Laplacian and Fiedler properties, Φ_spectral end-to-end.
- `tests/test_classical.py` — classical baselines against synthetic inputs.

One integration test that ties the whole pipeline together in `tests/test_phase2_integration.py`.

---

## Task order

**Implement in this order. Do not skip ahead.** Each module's tests pass before the next module begins.

### Task 1 — `features.py`

Per B1, three feature sets:

- `kinematic` at d=4: `(speed, u_x, u_y, u_z)` where `(u_x, u_y, u_z) = v/||v||` is the unit velocity vector.
- `vxvyvz` at d=3: `(vx, vy, vz)` raw velocity components.
- `full` at d=6: `(x, y, z, vx, vy, vz)`.

Public API:

```python
def extract_features(
    telemetry_df: pd.DataFrame,
    feature_set: str,
) -> np.ndarray:
    """Extract features from a telemetry DataFrame.

    Parameters
    ----------
    telemetry_df : pd.DataFrame
        Per-step telemetry CSV loaded into a DataFrame. Must contain columns
        appropriate to the feature set.
    feature_set : str
        One of "kinematic", "vxvyvz", "full".

    Returns
    -------
    np.ndarray
        Shape (T, N, d) where T is number of steps, N is number of agents,
        d is feature dimension determined by feature_set.
    """
```

Implementation notes:
- `kinematic`: use the already-logged `speed, u_x, u_y, u_z` columns directly. Do not recompute.
- Validate the feature_set argument with an explicit error message.
- T is inferred from `telemetry_df["step"].nunique()`, N from `telemetry_df["agent_id"].nunique()`.
- Assume telemetry is sorted; if it is not, sort by `(step, agent_id)` before reshaping.

Tests (`tests/test_features.py`):
- Kinematic: unit vector invariant holds for every (t, i) after extraction.
- All three sets: output shape matches `(T, N, d)` with correct d.
- vxvyvz: matches raw velocity columns (spot-check a few rows).
- Invalid feature_set raises a clear error.

### Task 2 — `mi.py` — standardization and three estimators (B6, D3)

Per D3, feature standardization is an explicit pipeline step, not buried inside the estimator.

```python
def standardize_window(X: np.ndarray) -> np.ndarray:
    """Per-agent per-channel z-score within a single window.

    Parameters
    ----------
    X : np.ndarray
        Shape (W, N, d). W is window length, N agents, d features.

    Returns
    -------
    np.ndarray
        Same shape. For each (agent, channel), subtract the W-mean and divide
        by the W-std. If std == 0 (constant channel), set that channel to 0
        rather than dividing.
    """
```

Test: after standardization, `mean(X_std, axis=0)` is approximately 0 everywhere, `std(X_std, axis=0)` is approximately 1 for non-constant channels and exactly 0 for constant channels.

Three estimators, all operating on a standardized window:

```python
def mi_matrix_ksg(X: np.ndarray, k: int = 5, noise_eps: float = 1e-10) -> np.ndarray:
    """KSG k-NN mutual information estimator (Kraskov et al. 2004 eq. 8).

    Per Bailey (2026) §3.4. Chebyshev (L-infinity) metric.
    Small uniform noise is added before k-NN queries to break ties.
    Uses scipy.spatial.cKDTree for k-NN queries (no external MI library).

    Parameters
    ----------
    X : np.ndarray
        Shape (W, N, d), standardized per D3.

    Returns
    -------
    np.ndarray
        Shape (N, N) symmetric MI matrix with zeros on diagonal.
    """

def mi_matrix_histogram(X: np.ndarray, n_bins: int = 8) -> np.ndarray:
    """Histogram-based MI estimator. Sensitivity check per §3.4."""

def mi_matrix_gaussian(X: np.ndarray, ridge: float = 1e-8) -> np.ndarray:
    """Gaussian closed-form MI estimator. Retained for 2D-to-3D comparability."""
```

Validation tests (`tests/test_mi.py`) — these are the most important tests in Phase 2. Bugs in MI estimation silently propagate through every downstream result.

1. **Independent Gaussians.** Generate X ~ N(0, 1) shape (W=100, N=10, d=4) with all agents drawn independently. All three estimators should return an MI matrix where off-diagonal entries are close to 0 (within reasonable estimator-specific bias tolerances — KSG has more variance at W=100, Gaussian has less).

2. **Perfectly correlated agents.** Set all agents to identical time series. Off-diagonal MI should be large and approximately equal across all pairs. Gaussian will return very large values (approaching infinity as ridge shrinks); KSG and histogram return finite large values. Test: off-diagonal values are substantially larger than in the independent case.

3. **Known-correlation Gaussian pair.** Two agents with d=1 features drawn from a bivariate Gaussian with correlation ρ. Analytic MI is `-0.5 * log(1 - ρ²)`. Test Gaussian estimator returns this to within 0.05 for ρ in {0.3, 0.6, 0.9} at W=500. KSG returns within 0.15 of analytic (KSG is biased; this tolerance matches Kraskov et al. 2004's reported behavior at k=5, W=500).

4. **Symmetry.** MI matrix is symmetric (`M[i,j] == M[j,i]`) for all three estimators.

5. **Diagonal is zero.** `M[i,i] == 0` by convention (MI of a variable with itself is infinite; we zero it).

6. **Non-negativity.** All off-diagonal entries ≥ 0 (up to small numerical noise; allow -1e-10 tolerance).

7. **Standardization independence for KSG and Gaussian.** These estimators are scale-invariant on paper. Run the estimator on raw X and on `10 * X`; results should be identical within numerical tolerance. (Histogram is bin-edge-dependent and will differ; test histogram on pre-standardized input only.)

### Task 3 — `spectral.py`

Normalized Laplacian, Fiedler bipartition, Φ_spectral per Bailey & Schneider (2025) §2 and Bailey (2026) §3.4. This logic is dimension-agnostic — the 2D code's spectral pipeline ports over with no 3D-specific changes.

```python
def normalized_laplacian(mi_matrix: np.ndarray) -> np.ndarray:
    """Symmetric normalized graph Laplacian L = I - D^(-1/2) W D^(-1/2).

    W is the MI matrix with zero diagonal. Degree D is the row sums of W.
    Returns a symmetric positive-semidefinite matrix.
    """

def fiedler_bipartition(L: np.ndarray) -> np.ndarray:
    """Partition nodes into two clusters using sign of the Fiedler vector.

    Returns a (N,) int array with values in {0, 1}. Handles degenerate cases
    where the Fiedler eigenvalue has multiplicity > 1 by breaking ties on
    leading entry sign (documented behavior; matches Bailey & Schneider 2025).
    """

def phi_spectral(mi_matrix: np.ndarray, partition: np.ndarray) -> float:
    """Sum of MI across the minimum spectral cut.

    Φ_spectral = sum over (i, j) where partition[i] != partition[j] of MI[i, j].
    """

def phi_spectral_over_windows(
    features: np.ndarray,
    W: int,
    stride: int,
    estimator: str,
    **estimator_kwargs,
) -> np.ndarray:
    """End-to-end Φ_spectral time series.

    For each window, extract, standardize, compute MI matrix, compute Laplacian,
    Fiedler partition, cross-cut MI sum. Returns array of length
    (T - W) // stride + 1.
    """
```

Tests (`tests/test_spectral.py`):

1. **Laplacian is symmetric and PSD.** Eigenvalues all ≥ -1e-10.
2. **Laplacian of a graph with two disconnected components has exactly 2 zero eigenvalues.** Test with a block-diagonal MI matrix (two groups, zero MI between groups, nonzero within).
3. **Fiedler on two-block MI recovers the true partition.** Construct a block MI with 5 agents in each group, strong MI within each group, zero across. Fiedler partition should perfectly separate the two groups (allowing for label swap: either {0,0,0,0,0,1,1,1,1,1} or the flipped version).
4. **Φ_spectral is zero for a perfectly block-separated MI.** Given the partition above, the cross-cut is empty (or all zeros).
5. **Φ_spectral is maximal when partition matches a fully-connected MI.** Test with uniform MI and the resulting partition.
6. **End-to-end pipeline runs on Phase 1 telemetry.** Load a real telemetry CSV from a short simulation, compute `phi_spectral_over_windows`, check output is finite, non-negative, and has the expected length.

### Task 4 — `classical.py`

Per B5, three classical order parameters computed per window:

```python
def polarization(velocities: np.ndarray) -> float:
    """||mean(v_hat)||. velocities shape (N, 3) or (N, d). Returns scalar in [0, 1]."""

def milling_score_magnitude(positions: np.ndarray, velocities: np.ndarray, center: np.ndarray) -> float:
    """Mean over agents of |r_hat × v_hat| (3D vector cross product magnitude).

    Reduces to 2D cross-product absolute value in the planar limit. Per B5 primary.
    """

def angular_momentum_norm(positions: np.ndarray, velocities: np.ndarray, center: np.ndarray) -> float:
    """||(1/N) sum r_i × v_i||. Global rotational coherence. Per B5 secondary."""
```

Tests (`tests/test_classical.py`):
1. **Polarization = 1 for perfectly aligned velocities, ≈ 0 for isotropic.** Construct both and verify.
2. **Milling score magnitude = 1 for perfect planar orbit (velocity everywhere perpendicular to radial).** Construct, verify.
3. **Angular momentum norm: same planar orbit gives a high value; random velocities give near-zero mean L.**
4. **Milling score reduces to 2D equivalent in the planar limit.** Construct agents entirely in the xy-plane, compare to the 2D scalar cross product value — should match to machine precision.

### Task 5 — Integration test

`tests/test_phase2_integration.py` runs a complete end-to-end pipeline on a real 100-step simulation and checks it produces sensible output:

1. Run a 100-step baseline scenario at seed 0.
2. Load telemetry, extract kinematic features, compute Φ_spectral over windows using KSG estimator at W=40, stride=1.
3. Assert the output is a 1D array of the expected length.
4. Assert no NaN or infinite values.
5. Assert all values are non-negative.
6. Assert standard deviation of Φ_spectral over the time series is > 0 (i.e. the measure varies, it is not a constant).

Keep this test fast — 100 steps, 40 agents, one scenario. Should run in under 30 seconds on a typical laptop. If it takes longer than 60 seconds, profile and see whether KSG is the bottleneck; if so, note it in a comment and leave performance work for later (Phase 4 sweeps will care).

---

## Pass/Fail

- [ ] `pytest tests/ -v` passes. Count should be 34 (Phase 1) + N (Phase 2 new tests) with zero failures.
- [ ] All four modules in `src/spectral_swarm_3d/analysis/` have real implementations (no `NotImplementedError`).
- [ ] KSG, histogram, and Gaussian estimators all exist and are callable. Config flag `estimator: "ksg"` is respected as the default in `phi_spectral_over_windows`.
- [ ] Standardization is an explicit step (D3 compliance) — verifiable by reading the code and seeing `standardize_window` called explicitly before the estimator.
- [ ] `ruff check .` is clean.
- [ ] Integration test runs a full pipeline on real telemetry without errors.

---

## Reminders

**Do not drift into Phase 3.** TDA implementation is Phase 3 work. If you see yourself reaching for Ripser, stop.

**Do not change Phase 1 code to make Phase 2 easier.** If Phase 1's telemetry schema or agent step seems inconvenient, adapt the Phase 2 code to it. If there is a genuine Phase 1 bug, stop and report — do not silently patch.

**Watch for silent KSG bugs.** The two most common ways KSG goes wrong are: forgetting to add tie-breaking noise (look for discrete/integer-valued features that should have been continuous), and using Euclidean instead of Chebyshev metric on the joint space (changes the bias characteristics). Both produce plausible-looking output that is quantitatively wrong. The validation tests in Task 2 are designed to catch both.

**Report any deviation.** If you cannot make a test pass within the tolerances specified, do not relax the tolerance. Report the actual result and let the user decide whether the tolerance was set wrong or the implementation has a problem.

**Do not advance to Phase 3 in this session.** Phase 3 starts fresh with the plan re-loaded.
