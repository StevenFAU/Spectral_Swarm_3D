"""3D Boids swarm agent.

Phase 1 implementation target. See SpectralSwarm3DPhases.md §Phase 1 and Cluster A.

Implements SwarmAgent3D for use within BoidSwarmModel3D. Agents carry 3D
position and velocity; synchronous update means agent.step() is a no-op
and all force calculations are performed in model.step() (A7).
"""


def build_agent(agent_id: int, model, config: dict):
    """Construct a SwarmAgent3D. Phase 1."""
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md")
