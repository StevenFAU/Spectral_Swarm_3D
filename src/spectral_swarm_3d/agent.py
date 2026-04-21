"""3D Boids swarm agent.

Implements SwarmAgent3D for use within BoidSwarmModel3D. Agents carry 3D
position and velocity; synchronous update (A7) means ``step()`` is a no-op
and all force calculations are performed in ``model.step()``.
"""

from __future__ import annotations

import numpy as np
from mesa.experimental.continuous_space import ContinuousSpaceAgent


class SwarmAgent3D(ContinuousSpaceAgent):
    """A single boid agent in the 3D continuous space.

    Parameters
    ----------
    space:
        The Mesa ``ContinuousSpace`` (3D) this agent inhabits.
    model:
        The owning ``BoidSwarmModel3D``.
    velocity:
        Initial velocity vector, shape ``(3,)``.
    is_leader:
        True if this agent is a designated leader.
    leader_group:
        0 or 1 for leaders (half/half split); -1 for followers.
    """

    def __init__(
        self,
        space,
        model,
        velocity: np.ndarray,
        is_leader: bool,
        leader_group: int,
    ) -> None:
        super().__init__(space, model)
        self.velocity: np.ndarray = velocity.astype(float).copy()
        self.is_leader: bool = bool(is_leader)
        self.leader_group: int = int(leader_group)

    def step(self) -> None:
        """No-op: model handles synchronous boids update (A7)."""
        return None
