"""Phase 3 TDA pipeline tests.

Synthetic positive controls for each homology dimension, structural invariants
of the summary metrics, and the D8 bottleneck-stability linearity check.
End-to-end integration on Phase 1 telemetry lives in ``test_phase3_integration.py``.
"""

from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d.analysis.tda import (
    compute_persistence,
    persistence_summaries,
    snapshot_cloud,
    trajectory_cloud,
)


# ---------------------------------------------------------------------------
# Task 1 — snapshot_cloud
# ---------------------------------------------------------------------------


def test_snapshot_cloud_not_augmented_returns_positions():
    rng = np.random.default_rng(0)
    positions = rng.normal(size=(40, 3))
    out = snapshot_cloud(positions, augmented=False)
    assert out.shape == (40, 3)
    np.testing.assert_array_equal(out, positions)


def test_snapshot_cloud_augmented_concatenates_beta_velocities():
    rng = np.random.default_rng(1)
    positions = rng.normal(size=(30, 3))
    velocities = rng.normal(size=(30, 3))
    out = snapshot_cloud(positions, augmented=True, velocities=velocities, beta=0.35)
    assert out.shape == (30, 6)
    np.testing.assert_array_equal(out[:, :3], positions)
    np.testing.assert_allclose(out[:, 3:], 0.35 * velocities)


def test_snapshot_cloud_augmented_without_velocities_raises():
    positions = np.zeros((5, 3))
    with pytest.raises(ValueError, match="velocities"):
        snapshot_cloud(positions, augmented=True, velocities=None)


# ---------------------------------------------------------------------------
# Task 2 — trajectory_cloud
# ---------------------------------------------------------------------------


def test_trajectory_cloud_shape():
    rng = np.random.default_rng(2)
    W, N, d = 40, 12, 4
    window = rng.normal(size=(W, N, d))
    out = trajectory_cloud(window)
    assert out.shape == (N, W * d)


def test_trajectory_cloud_flatten_consistency():
    rng = np.random.default_rng(3)
    W, N, d = 10, 7, 4
    window = rng.normal(size=(W, N, d))
    out = trajectory_cloud(window)
    for i in range(N):
        np.testing.assert_array_equal(out[i, :], window[:, i, :].reshape(-1))


def test_trajectory_cloud_phase2_defaults_ambient_dim_160():
    """Phase 2 defaults: d=4, W=40 -> ambient dim 160."""
    window = np.zeros((40, 40, 4))
    out = trajectory_cloud(window)
    assert out.shape[1] == 160


# ---------------------------------------------------------------------------
# Task 3 — compute_persistence (synthetic positive controls)
# ---------------------------------------------------------------------------


def _summaries(X: np.ndarray, maxdim: int = 2) -> dict[str, float]:
    return persistence_summaries(compute_persistence(X, maxdim=maxdim), maxdim=maxdim)


def test_persistence_tight_cluster_has_near_zero_totals():
    rng = np.random.default_rng(10)
    X = rng.normal(scale=1e-3, size=(30, 3))
    s = _summaries(X)
    # All persistences scale with noise (~1e-3); sum over ~30 bars stays small.
    assert s["TP_0"] < 0.1
    assert s["TP_1"] < 0.1
    assert s["TP_2"] < 0.1


def test_persistence_two_separated_clusters_have_positive_tp0():
    rng = np.random.default_rng(11)
    cluster_a = rng.normal(scale=0.05, size=(6, 3))
    cluster_b = rng.normal(scale=0.05, size=(6, 3)) + np.array([10.0, 0.0, 0.0])
    X = np.vstack([cluster_a, cluster_b])
    s = _summaries(X)
    assert s["TP_0"] > 1.0
    assert s["TP_1"] < 1e-2
    assert s["TP_2"] < 1e-2


def test_persistence_planar_ring_has_positive_h1_no_h2():
    rng = np.random.default_rng(12)
    n = 60
    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    R = 2.0
    X = np.stack(
        [R * np.cos(theta), R * np.sin(theta), np.zeros(n)], axis=1
    )
    X = X + rng.normal(scale=1e-2, size=X.shape)
    s = _summaries(X)
    # Ring's H1 bar (the circle loop) is the dominant feature; any H2 bars
    # from the Vietoris-Rips filtration are far smaller.
    assert s["MP_1"] > 0.5
    assert s["MP_1"] > 3.0 * s["MP_2"]


def _fibonacci_sphere(
    n: int, R: float, rng: np.random.Generator, noise: float = 1e-2
) -> np.ndarray:
    """Uniform-ish sphere sampling via the Fibonacci lattice."""
    i = np.arange(n)
    phi_golden = np.pi * (3.0 - np.sqrt(5.0))
    y = 1.0 - 2.0 * i / (n - 1)
    radius = np.sqrt(1.0 - y * y)
    theta = phi_golden * i
    X = R * np.stack([radius * np.cos(theta), y, radius * np.sin(theta)], axis=1)
    return X + rng.normal(scale=noise, size=X.shape)


def test_persistence_spherical_shell_has_dominant_h2():
    rng = np.random.default_rng(13)
    X = _fibonacci_sphere(n=80, R=1.0, rng=rng)
    s = _summaries(X)
    assert s["MP_2"] > 0.5
    # Sphere's H2 void is the canonical positive control: MP_2 dominates MP_1.
    assert s["MP_2"] > 2.0 * s["MP_1"]


# ---------------------------------------------------------------------------
# Task 4 — persistence_summaries (structural invariants)
# ---------------------------------------------------------------------------


def _small_cloud(seed: int = 0, n: int = 25) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, 3))


def test_summaries_tp_mp_non_negative_and_mp_le_tp():
    dgms = compute_persistence(_small_cloud(seed=20), maxdim=2)
    s = persistence_summaries(dgms, maxdim=2)
    for k in range(3):
        assert s[f"TP_{k}"] >= 0.0
        assert s[f"MP_{k}"] >= 0.0
        assert s[f"MP_{k}"] <= s[f"TP_{k}"] + 1e-12


def test_summaries_bottleneck_to_self_is_zero():
    """D8 stability sanity: bottleneck(dgm, dgm) == 0 (Cohen-Steiner et al. 2007)."""
    dgms = compute_persistence(_small_cloud(seed=21), maxdim=2)
    s = persistence_summaries(dgms, baseline_dgms=dgms, prev_dgms=dgms, maxdim=2)
    for k in range(3):
        assert s[f"B_base_{k}"] == pytest.approx(0.0, abs=1e-10)
        assert s[f"B_prev_{k}"] == pytest.approx(0.0, abs=1e-10)


def test_summaries_missing_baseline_yields_nan_not_zero():
    dgms = compute_persistence(_small_cloud(seed=22), maxdim=2)
    s = persistence_summaries(dgms, baseline_dgms=None, prev_dgms=None, maxdim=2)
    for k in range(3):
        assert np.isnan(s[f"B_base_{k}"])
        assert np.isnan(s[f"B_prev_{k}"])


def test_summaries_keys_cover_full_range():
    dgms = compute_persistence(_small_cloud(seed=23), maxdim=2)
    s = persistence_summaries(dgms, maxdim=2)
    for k in range(3):
        for prefix in ("TP_", "MP_", "B_base_", "B_prev_"):
            assert f"{prefix}{k}" in s


def test_summaries_spherical_shell_mp2_dominates_mp1():
    """Sphere's H2 bar is the dominant feature; MP_2 > MP_1."""
    rng = np.random.default_rng(24)
    X = _fibonacci_sphere(n=80, R=1.0, rng=rng)
    dgms = compute_persistence(X, maxdim=2)
    s = persistence_summaries(dgms, maxdim=2)
    assert s["MP_2"] > s["MP_1"]


# ---------------------------------------------------------------------------
# Task 5 — D8 bottleneck stability linearity
# ---------------------------------------------------------------------------


def test_bottleneck_stability_linear_in_noise():
    """Perturbing a fixed cloud by Gaussian noise of sigma produces bottleneck
    distances that grow monotonically and roughly linearly in sigma — the
    Cohen-Steiner stability theorem (D8) in empirical form."""
    rng = np.random.default_rng(42)

    # Base cloud: 40 points on the corners of nested cubes (clean H0/H1 signal).
    base = rng.normal(size=(40, 3)) * 2.0
    base_dgms = compute_persistence(base, maxdim=1)

    sigmas = [0.0, 0.05, 0.1, 0.2]
    distances: list[float] = []
    for sigma in sigmas:
        perturbed = base + rng.normal(scale=sigma, size=base.shape)
        pert_dgms = compute_persistence(perturbed, maxdim=1)
        s = persistence_summaries(pert_dgms, baseline_dgms=base_dgms, maxdim=1)
        # Use H1 for the stability check — H0 bottleneck is dominated by the
        # single infinite-death bar, which persim's default handling normalizes
        # in a way that's less informative here.
        distances.append(s["B_base_1"])

    # sigma=0 reproduces the baseline exactly; bottleneck must be 0.
    assert distances[0] == pytest.approx(0.0, abs=1e-10)

    # Monotone non-decreasing in sigma.
    assert distances[1] <= distances[2] + 1e-10
    assert distances[2] <= distances[3] + 1e-10

    # Loose linear-growth bound: b(0.2) / b(0.05) < 10 (linear gives ~4).
    assert distances[1] > 0.0, "noise=0.05 should produce non-zero bottleneck"
    assert distances[3] / distances[1] < 10.0
