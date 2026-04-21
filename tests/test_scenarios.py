"""Phase 1 tests for scenario helpers (A3, A5, jamming)."""
from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d import scenarios


def test_effective_boids_params_within_jam_window():
    r_v, w_c, w_a, w_s = scenarios.effective_boids_params(
        step=250, vision_radius=10.0, w_c=0.03, w_a=1.0, w_s=0.015,
        jam_alpha=0.5, jam_t_on=200, jam_t_off=400,
    )
    assert r_v == pytest.approx(5.0)
    assert w_a == pytest.approx(0.5)


def test_effective_boids_params_outside_jam_window_unchanged():
    base = (10.0, 0.03, 1.0, 0.015)
    out = scenarios.effective_boids_params(
        step=10, vision_radius=base[0], w_c=base[1], w_a=base[2], w_s=base[3],
        jam_alpha=0.2, jam_t_on=200, jam_t_off=400,
    )
    assert out == base


def test_leader_waypoint_default_zero_for_followers():
    groups = np.array([-1, -1, 0, 1])
    pos = np.array([[0, 0, 0], [1, 1, 1], [10, 10, 10], [5, 5, 5]], dtype=float)
    dwp = np.array([40.0, 40.0, 40.0])
    swps = (np.array([12.5, 37.5, 12.5]), np.array([37.5, 12.5, 37.5]))
    f = scenarios.leader_waypoint(
        step=10, leader_groups=groups, positions=pos,
        default_waypoint=dwp, split_waypoints=swps, leader_strength=0.8,
    )
    assert np.allclose(f[:2], 0)
    # Leaders: force magnitude equals leader_strength.
    assert np.linalg.norm(f[2]) == pytest.approx(0.8)
    assert np.linalg.norm(f[3]) == pytest.approx(0.8)


def test_leader_waypoint_splits_to_opposite_corners_during_window():
    groups = np.array([0, 1])
    pos = np.array([[25, 25, 25], [25, 25, 25]], dtype=float)
    dwp = np.array([40.0, 40.0, 40.0])
    swps = (np.array([12.5, 37.5, 12.5]), np.array([37.5, 12.5, 37.5]))
    # Inside split window
    f_in = scenarios.leader_waypoint(
        step=250, leader_groups=groups, positions=pos,
        default_waypoint=dwp, split_waypoints=swps, leader_strength=1.0,
        split_t_on=200, split_t_off=400,
    )
    # Outside split window
    f_out = scenarios.leader_waypoint(
        step=10, leader_groups=groups, positions=pos,
        default_waypoint=dwp, split_waypoints=swps, leader_strength=1.0,
        split_t_on=200, split_t_off=400,
    )
    # Inside: groups aim at opposite corners → unit vectors point in opposite
    # half-spaces. Outside: both aim at the same default waypoint.
    assert np.dot(f_in[0], f_in[1]) < 0.0
    assert np.allclose(f_out[0], f_out[1])


def test_milling_tangent_orthogonal_to_radial_in_planar_limit():
    """A3: velocity-projected tangent matches the 2D CCW prescription in-plane."""
    L = 50.0
    # Two agents symmetric about center in the xy-plane, with tangential velocity.
    pos = np.array([[35.0, 25.0, 25.0], [15.0, 25.0, 25.0]])
    # Both moving in +y and -y (tangential in xy-plane)
    vel = np.array([[0.0, 1.0, 0.0], [0.0, -1.0, 0.0]])
    f = scenarios.milling_force(
        positions=pos, velocities=vel, mu=1.0, R=10.0, kappa=0.0, L=L,
    )
    # With kappa=0, force = mu * tau_hat. tau_hat should match the velocity direction
    # (already tangential, unit-norm).
    assert np.allclose(f[0], [0.0, 1.0, 0.0], atol=1e-9)
    assert np.allclose(f[1], [0.0, -1.0, 0.0], atol=1e-9)


def test_milling_fallback_when_velocity_is_radial():
    """If v is parallel to r̂ the Gram-Schmidt fallback produces a unit tangent."""
    L = 50.0
    pos = np.array([[35.0, 25.0, 25.0]])           # r̂ = +x
    vel = np.array([[1.0, 0.0, 0.0]])               # v ∥ r̂ → v_tan = 0
    f = scenarios.milling_force(
        positions=pos, velocities=vel, mu=1.0, R=10.0, kappa=0.0, L=L,
    )
    # Force magnitude equals mu * |tau_hat| = 1 and is orthogonal to r̂.
    r_hat = np.array([1.0, 0.0, 0.0])
    assert np.linalg.norm(f[0]) == pytest.approx(1.0, abs=1e-9)
    assert abs(np.dot(f[0], r_hat)) < 1e-9


def test_milling_radial_correction_sign():
    """κ term pulls inward when r > R and pushes outward when r < R."""
    L = 50.0
    # Agent at +x direction, distance 20 from centre (r > R=10).
    pos_out = np.array([[45.0, 25.0, 25.0]])
    vel = np.array([[0.0, 1.0, 0.0]])  # tangential
    f_out = scenarios.milling_force(
        positions=pos_out, velocities=vel, mu=1.0, R=10.0, kappa=1.0, L=L,
    )
    # x-component of force should be negative (pulling toward centre).
    assert f_out[0, 0] < 0.0

    pos_in = np.array([[30.0, 25.0, 25.0]])  # r=5, r < R=10
    f_in = scenarios.milling_force(
        positions=pos_in, velocities=vel, mu=1.0, R=10.0, kappa=1.0, L=L,
    )
    assert f_in[0, 0] > 0.0
