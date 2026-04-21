"""3D Boids swarm model (Phase 1).

Implements :class:`BoidSwarmModel3D` on Mesa 3's experimental
``ContinuousSpace`` with ``dimensions=((0, L), (0, L), (0, L))``. All physics
are computed synchronously in :meth:`step` using numpy vectorisation and
``scipy.spatial.cKDTree`` for neighbour queries (A7; Mesa's own neighbour
methods are not used). Key plan anchors:

* A1 — 3D ContinuousSpace via the ``dimensions`` parameter.
* A2 — Domain and length scaling via config (L=50 default).
* A3 — Velocity-projected milling tangent (see :mod:`scenarios`).
* A4 — Uniform-on-S² initial velocities.
* A5 — 3D leader waypoints from config.
* A6 — Mean alignment by default; ``alignment_rule=='sum'`` opt-in for sensitivity.
* A7 — Synchronous vectorised update; ``agent.step()`` is a no-op.
"""

from __future__ import annotations

import random as _stdlib_random
from pathlib import Path
from typing import Any

import mesa
import numpy as np
from mesa.experimental.continuous_space import ContinuousSpace
from scipy.spatial import cKDTree

from spectral_swarm_3d import scenarios
from spectral_swarm_3d.agent import SwarmAgent3D
from spectral_swarm_3d.telemetry import TelemetryLogger, save_metadata


def _uniform_on_sphere(rng: np.random.Generator, n: int) -> np.ndarray:
    """Sample ``n`` unit vectors uniformly on S² (A4, inverse-CDF)."""
    z = rng.uniform(-1.0, 1.0, size=n)
    phi = rng.uniform(0.0, 2.0 * np.pi, size=n)
    r = np.sqrt(1.0 - z * z)
    return np.column_stack([r * np.cos(phi), r * np.sin(phi), z])


class BoidSwarmModel3D(mesa.Model):
    """3D boids swarm model with optional scenario perturbations.

    Parameters
    ----------
    config:
        Parameter dictionary; see ``configs/default.yaml``.
    scenario_name:
        One of ``"none"``, ``"leader"``, ``"jamming"``, ``"split_merge"``,
        ``"milling"``.
    seed:
        Integer RNG seed; propagated to numpy, Mesa, and the space.
    telemetry_path:
        If given, write per-step CSV telemetry here.
    """

    def __init__(
        self,
        config: dict[str, Any],
        scenario_name: str = "none",
        seed: int = 0,
        telemetry_path: Path | None = None,
    ) -> None:
        super().__init__(rng=seed)

        self.cfg = config
        self.scenario_name = str(scenario_name)
        self._seed = int(seed)
        self._step_count: int = 0

        N: int = int(config["N"])
        L: float = float(config["L"])

        self.space = ContinuousSpace(
            dimensions=np.array([[0.0, L], [0.0, L], [0.0, L]]),
            torus=False,
            n_agents=N,
            random=_stdlib_random.Random(seed),
        )

        # Initial positions: uniform in the cube; velocities: uniform on S².
        positions = self.rng.uniform(0.0, L, size=(N, 3))
        speed = float(config["speed"])
        velocities = speed * _uniform_on_sphere(self.rng, N)

        # Designate leaders and split them evenly into two groups.
        n_leaders = round(N * float(config["leader_fraction"]))
        leader_groups = np.full(N, -1, dtype=int)
        if n_leaders > 0:
            leader_idx = self.rng.choice(N, size=n_leaders, replace=False)
            half = n_leaders // 2
            leader_groups[leader_idx[:half]] = 0
            leader_groups[leader_idx[half:]] = 1

        self.swarm: list[SwarmAgent3D] = []
        for i in range(N):
            ag = SwarmAgent3D(
                space=self.space,
                model=self,
                velocity=velocities[i],
                is_leader=bool(leader_groups[i] >= 0),
                leader_group=int(leader_groups[i]),
            )
            ag.position = positions[i].copy()
            self.swarm.append(ag)

        self._telemetry: TelemetryLogger | None = None
        if telemetry_path is not None:
            self._telemetry = TelemetryLogger(Path(telemetry_path))

    # ------------------------------------------------------------------
    # Internal snapshots
    # ------------------------------------------------------------------

    def _positions(self) -> np.ndarray:
        return np.array([ag.position for ag in self.swarm], dtype=float)

    def _velocities(self) -> np.ndarray:
        return np.array([ag.velocity for ag in self.swarm], dtype=float)

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> None:  # type: ignore[override]
        cfg = self.cfg
        t = self._step_count
        N: int = int(cfg["N"])
        L: float = float(cfg["L"])
        speed: float = float(cfg["speed"])
        r_s: float = float(cfg["separation_radius"])
        alignment_rule: str = str(cfg.get("alignment_rule", "mean"))

        pos = self._positions()
        vel = self._velocities()

        # --- Effective boids parameters (jamming scales during its window) ---
        if self.scenario_name == "jamming":
            jam_t_on = int(cfg.get("jam_t_on", 99999))
            jam_t_off = int(cfg.get("jam_t_off", 99999))
            jam_alpha = float(cfg.get("jam_alpha", 0.5))
        else:
            jam_t_on = jam_t_off = 99999
            jam_alpha = 1.0

        r_v, w_c, w_a, w_s = scenarios.effective_boids_params(
            step=t,
            vision_radius=float(cfg["vision_radius"]),
            w_c=float(cfg["w_c"]),
            w_a=float(cfg["w_a"]),
            w_s=float(cfg["w_s"]),
            jam_alpha=jam_alpha,
            jam_t_on=jam_t_on,
            jam_t_off=jam_t_off,
        )

        # --- Neighbour queries via cKDTree -------------------------------
        tree = cKDTree(pos)
        nbrs_v = tree.query_ball_point(pos, r=r_v)
        nbrs_s = tree.query_ball_point(pos, r=r_s)

        # --- Scenario forces ---------------------------------------------
        leader_groups = np.array([ag.leader_group for ag in self.swarm])
        default_wp = np.array(cfg["leader_waypoint"], dtype=float)
        split_wps = (
            np.array(cfg["split_waypoint_group0"], dtype=float),
            np.array(cfg["split_waypoint_group1"], dtype=float),
        )
        if self.scenario_name in ("leader", "split_merge"):
            is_split = self.scenario_name == "split_merge"
            leader_forces = scenarios.leader_waypoint(
                step=t,
                leader_groups=leader_groups,
                positions=pos,
                default_waypoint=default_wp,
                split_waypoints=split_wps,
                leader_strength=float(cfg["leader_strength"]),
                split_t_on=int(cfg["split_t_on"]) if is_split else None,
                split_t_off=int(cfg["split_t_off"]) if is_split else None,
            )
        else:
            leader_forces = np.zeros((N, 3))

        if self.scenario_name == "milling":
            mill_forces = scenarios.milling_force(
                positions=pos,
                velocities=vel,
                mu=float(cfg["milling_mu"]),
                R=float(cfg["milling_R"]),
                kappa=float(cfg["milling_kappa"]),
                L=L,
            )
        else:
            mill_forces = np.zeros((N, 3))

        noise = self.rng.normal(0.0, float(cfg["noise_sigma"]), size=(N, 3))

        # --- Velocity update (mean/sum alignment; A6) --------------------
        new_vel = np.empty((N, 3))
        neighbor_counts = np.zeros(N, dtype=int)

        for i in range(N):
            nv = [j for j in nbrs_v[i] if j != i]
            ns = [j for j in nbrs_s[i] if j != i]
            neighbor_counts[i] = len(nv)

            if nv:
                c_i = np.mean(pos[nv] - pos[i], axis=0)
                if alignment_rule == "mean":
                    a_i = np.mean(vel[nv], axis=0)
                else:  # "sum"
                    a_i = np.sum(vel[nv], axis=0)
            else:
                c_i = np.zeros(3)
                a_i = np.zeros(3)

            s_i = -np.sum(pos[ns] - pos[i], axis=0) if ns else np.zeros(3)

            v_tilde = (
                vel[i]
                + w_c * c_i
                + w_a * a_i
                + w_s * s_i
                + leader_forces[i]
                + mill_forces[i]
                + noise[i]
            )
            norm = float(np.linalg.norm(v_tilde))
            if norm > 1e-12:
                new_vel[i] = speed * v_tilde / norm
            else:
                old_norm = float(np.linalg.norm(vel[i]))
                if old_norm > 1e-12:
                    new_vel[i] = speed * vel[i] / old_norm
                else:
                    new_vel[i] = np.array([speed, 0.0, 0.0])

        new_pos = pos + new_vel

        # --- Reflective boundary conditions in 3D ------------------------
        for dim in range(3):
            lo = new_pos[:, dim] < 0.0
            new_pos[lo, dim] = -new_pos[lo, dim]
            new_vel[lo, dim] = -new_vel[lo, dim]

            hi = new_pos[:, dim] > L
            new_pos[hi, dim] = 2.0 * L - new_pos[hi, dim]
            new_vel[hi, dim] = -new_vel[hi, dim]

            new_pos[:, dim] = np.clip(new_pos[:, dim], 0.0, L)

        # --- Commit state ------------------------------------------------
        for i, ag in enumerate(self.swarm):
            ag.position = new_pos[i]
            ag.velocity = new_vel[i]

        # --- Telemetry ---------------------------------------------------
        if self._telemetry is not None:
            # Local density: neighbour count over the 3-ball volume.
            ball_vol = (4.0 / 3.0) * np.pi * r_v ** 3
            local_density = neighbor_counts / ball_vol
            # D7: agent within r_v of any boundary after the update.
            near_boundary = (
                (new_pos.min(axis=1) < r_v) | (new_pos.max(axis=1) > L - r_v)
            ).astype(int)
            self._telemetry.log_step(
                step=t,
                agents=self.swarm,
                positions=new_pos,
                velocities=new_vel,
                neighbor_counts=neighbor_counts,
                local_density=local_density,
                scenario_label=self.scenario_name,
                near_boundary=near_boundary,
            )

        self._step_count += 1

    # ------------------------------------------------------------------
    # Convenience API
    # ------------------------------------------------------------------

    def run(self, T: int | None = None) -> None:
        """Run for ``T`` steps, closing the telemetry file on exit."""
        n_steps = T if T is not None else int(self.cfg["T"])
        for _ in range(n_steps):
            self.step()
        if self._telemetry is not None:
            self._telemetry.close()

    def save_metadata(self, path: Path, repo_root: Path | None = None) -> dict:
        """Write the companion metadata JSON (D6)."""
        return save_metadata(
            config=self.cfg,
            seed=self._seed,
            scenario=self.scenario_name,
            path=Path(path),
            repo_root=repo_root,
        )


def build_model(config: dict, **kwargs: Any) -> BoidSwarmModel3D:
    """Construct a :class:`BoidSwarmModel3D` (kept for Phase-0 API parity)."""
    return BoidSwarmModel3D(config=config, **kwargs)
