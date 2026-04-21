"""Phase 1 tests for the 3D boids simulator (SpectralSwarm3DPhases.md)."""
from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d.model import BoidSwarmModel3D


SCENARIOS = ["none", "leader", "jamming", "split_merge", "milling"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_500_steps_no_nan_in_bounds_constant_speed(config, scenario):
    """40 agents survive 500 steps; positions in [0, L]³; speed constant."""
    m = BoidSwarmModel3D(config, scenario_name=scenario, seed=0)
    L = float(config["L"])
    speed = float(config["speed"])
    for _ in range(500):
        m.step()
        pos = m._positions()
        vel = m._velocities()
        assert not np.isnan(pos).any(), f"{scenario}: NaN in positions"
        assert not np.isnan(vel).any(), f"{scenario}: NaN in velocities"
        assert pos.min() >= 0.0 - 1e-9 and pos.max() <= L + 1e-9, (
            f"{scenario}: positions left [0, L]³"
        )
        speeds = np.linalg.norm(vel, axis=1)
        assert np.allclose(speeds, speed, atol=1e-9), (
            f"{scenario}: speed deviates from {speed}"
        )


def test_reflective_boundary_flips_velocity(config):
    """An agent overshooting x=L is reflected with vx negated."""
    cfg = dict(config)
    cfg["N"] = 1
    cfg["noise_sigma"] = 0.0
    cfg["w_c"] = 0.0
    cfg["w_a"] = 0.0
    cfg["w_s"] = 0.0
    cfg["leader_fraction"] = 0.0
    L = float(cfg["L"])
    m = BoidSwarmModel3D(cfg, scenario_name="none", seed=0)
    # Force deterministic state: single agent near +x wall moving outward.
    ag = m.swarm[0]
    ag.position = np.array([L - 0.5, L / 2, L / 2])
    ag.velocity = np.array([1.0, 0.0, 0.0])
    m.step()
    new_pos = m._positions()[0]
    new_vel = m._velocities()[0]
    assert 0.0 <= new_pos[0] <= L
    assert new_vel[0] < 0.0, "vx should flip after reflection at x=L"
    # Orthogonal components unchanged.
    assert abs(new_vel[1]) < 1e-9 and abs(new_vel[2]) < 1e-9
    # Reflected position: 2L - (L-0.5 + 1) = L - 0.5
    assert new_pos[0] == pytest.approx(L - 0.5, abs=1e-9)


def test_baseline_polarization_calibrated(config):
    """With baseline w_a + mean alignment, ≥8/10 seeds polarize within 200 steps."""
    speed = float(config["speed"])
    n_ok = 0
    for seed in range(10):
        m = BoidSwarmModel3D(config, scenario_name="none", seed=seed)
        reached = False
        for _ in range(200):
            m.step()
            pol = np.linalg.norm(m._velocities().mean(axis=0)) / speed
            if pol > 0.6:
                reached = True
                break
        if reached:
            n_ok += 1
    assert n_ok >= 8, f"only {n_ok}/10 seeds polarized > 0.6 in 200 steps"


def test_milling_radial_convergence(config):
    """Mean radial distance converges to R=11 (±7.5) by step 500."""
    L = float(config["L"])
    R = float(config["milling_R"])
    m = BoidSwarmModel3D(config, scenario_name="milling", seed=0)
    for _ in range(500):
        m.step()
    pos = m._positions()
    center = 0.5 * L * np.ones(3)
    r_mean = np.linalg.norm(pos - center, axis=1).mean()
    assert abs(r_mean - R) < 7.5, f"mean radial {r_mean:.2f} off target {R}"


def test_milling_spherical_shell(config):
    """std(z) of agent positions exceeds 3.0 by step 300 (shell, not ring)."""
    m = BoidSwarmModel3D(config, scenario_name="milling", seed=0)
    for _ in range(300):
        m.step()
    pos = m._positions()
    assert pos[:, 2].std() > 3.0, (
        "milling produced a near-equatorial ring, not a spherical shell"
    )


def test_split_merge_leader_group_separation(config):
    """Leader group centroids separate by > √3 · 0.25L during the split window."""
    L = float(config["L"])
    m = BoidSwarmModel3D(config, scenario_name="split_merge", seed=0)
    # Run through a majority of the split window.
    t_target = int(config["split_t_on"]) + 150
    for _ in range(t_target):
        m.step()
    pos = m._positions()
    groups = np.array([a.leader_group for a in m.swarm])
    c0 = pos[groups == 0].mean(axis=0)
    c1 = pos[groups == 1].mean(axis=0)
    sep = float(np.linalg.norm(c0 - c1))
    threshold = np.sqrt(3) * 0.25 * L
    assert sep > threshold, f"split separation {sep:.2f} ≤ {threshold:.2f}"


def test_deterministic_reproducibility(config):
    """Same seed → bit-identical trajectories across two independent runs."""
    m1 = BoidSwarmModel3D(config, scenario_name="leader", seed=42)
    m2 = BoidSwarmModel3D(config, scenario_name="leader", seed=42)
    for _ in range(50):
        m1.step()
        m2.step()
    p1 = m1._positions()
    p2 = m2._positions()
    v1 = m1._velocities()
    v2 = m2._velocities()
    assert np.array_equal(p1, p2), "positions diverge under identical seed"
    assert np.array_equal(v1, v2), "velocities diverge under identical seed"
