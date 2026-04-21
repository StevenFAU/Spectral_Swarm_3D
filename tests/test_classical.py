"""Phase 2 tests for classical order parameters (B5)."""

from __future__ import annotations

import numpy as np

from spectral_swarm_3d.analysis.classical import (
    angular_momentum_norm,
    milling_score_magnitude,
    polarization,
)


def test_polarization_aligned_is_one():
    v = np.tile(np.array([1.0, 0.0, 0.0]), (20, 1))
    assert polarization(v) == 1.0


def test_polarization_isotropic_near_zero():
    rng = np.random.default_rng(0)
    z = rng.uniform(-1, 1, 10_000)
    phi = rng.uniform(0, 2 * np.pi, 10_000)
    r = np.sqrt(1 - z * z)
    v = np.column_stack([r * np.cos(phi), r * np.sin(phi), z])
    assert polarization(v) < 0.05


def test_milling_perfect_planar_orbit_is_one():
    N = 40
    theta = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    center = np.array([0.0, 0.0, 0.0])
    radius = 5.0
    positions = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), np.zeros(N)])
    velocities = np.column_stack([-np.sin(theta), np.cos(theta), np.zeros(N)])
    assert milling_score_magnitude(positions, velocities, center) == 1.0


def test_angular_momentum_planar_orbit_high():
    N = 40
    theta = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    center = np.zeros(3)
    radius = 5.0
    positions = np.column_stack([radius * np.cos(theta), radius * np.sin(theta), np.zeros(N)])
    velocities = np.column_stack([-np.sin(theta), np.cos(theta), np.zeros(N)])
    L = angular_momentum_norm(positions, velocities, center)
    assert L == 5.0


def test_angular_momentum_random_velocities_near_zero():
    rng = np.random.default_rng(3)
    N = 2000
    positions = rng.uniform(-5, 5, size=(N, 3))
    velocities = rng.normal(size=(N, 3))
    center = np.zeros(3)
    L = angular_momentum_norm(positions, velocities, center)
    assert L < 0.5


def test_milling_reduces_to_2d_planar_limit():
    rng = np.random.default_rng(11)
    N = 50
    center = np.zeros(3)
    xy = rng.uniform(-5, 5, size=(N, 2))
    vxy = rng.normal(size=(N, 2))
    positions = np.column_stack([xy, np.zeros(N)])
    velocities = np.column_stack([vxy, np.zeros(N)])

    r = xy
    r_norm = np.linalg.norm(r, axis=1, keepdims=True)
    r_hat = np.where(r_norm > 1e-12, r / np.where(r_norm > 0, r_norm, 1.0), 0.0)
    v = vxy
    v_norm = np.linalg.norm(v, axis=1, keepdims=True)
    v_hat = np.where(v_norm > 1e-12, v / np.where(v_norm > 0, v_norm, 1.0), 0.0)
    cross_2d = r_hat[:, 0] * v_hat[:, 1] - r_hat[:, 1] * v_hat[:, 0]
    expected = np.mean(np.abs(cross_2d))

    got = milling_score_magnitude(positions, velocities, center)
    assert abs(got - expected) < 1e-12
