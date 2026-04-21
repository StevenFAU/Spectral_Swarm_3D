"""Scenario configuration helpers for the 3D swarm simulation.

Phase 1 implementation target. See SpectralSwarm3DPhases.md §Phase 1 and Cluster A.

Provides effective parameter overrides for each scenario:
  - none: baseline (no perturbation)
  - leader: leader waypoints per A5 (default (0.8L, 0.8L, 0.8L))
  - jamming: periodic MI jamming alpha per A2-scaled thresholds
  - split_merge: diagonal-opposite 3D waypoints per A5
  - milling: velocity-projected tangent force per A3

A6: alignment_rule config flag ('mean' | 'sum') is passed through here.
"""


def effective_boids_params(scenario: str, config: dict) -> dict:
    """Return config dict with scenario-specific parameter overrides. Phase 1."""
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md")


def leader_waypoint(scenario: str, group: int, config: dict) -> list:
    """Return 3D waypoint [x, y, z] for leader group in the given scenario. Phase 1."""
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md")


def milling_force(positions, velocities, config: dict):
    """Compute per-agent milling force using velocity-projected tangent (A3). Phase 1."""
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md")
