"""Scenario perturbation logic for the 3D swarm simulation.

Each public function returns per-agent force contributions of shape ``(N, 3)``
(or effective scalar parameters in the case of the jamming accessor). The
model calls these each step and integrates them into the synchronous boids
update. Plan anchors: A2 (scaling), A3 (velocity-projected milling tangent),
A5 (3D waypoints), A6 (alignment rule is passed through via config and is
not scenario-dependent).
"""

from __future__ import annotations

import numpy as np


def effective_boids_params(
    step: int,
    vision_radius: float,
    w_c: float,
    w_a: float,
    w_s: float,
    jam_alpha: float,
    jam_t_on: int,
    jam_t_off: int,
) -> tuple[float, float, float, float]:
    """Return ``(r_v, w_c, w_a, w_s)`` scaled by ``jam_alpha`` during the jam window.

    Implements the jamming perturbation: during ``[jam_t_on, jam_t_off)``
    the vision radius and all three boids weights are multiplied by
    ``jam_alpha`` (< 1 simulates communication degradation).
    """
    if jam_t_on <= step < jam_t_off:
        return (
            vision_radius * jam_alpha,
            w_c * jam_alpha,
            w_a * jam_alpha,
            w_s * jam_alpha,
        )
    return vision_radius, w_c, w_a, w_s


def leader_waypoint(
    step: int,
    leader_groups: np.ndarray,
    positions: np.ndarray,
    default_waypoint: np.ndarray,
    split_waypoints: tuple[np.ndarray, np.ndarray],
    leader_strength: float,
    split_t_on: int | None = None,
    split_t_off: int | None = None,
) -> np.ndarray:
    """Compute leader steering force for each agent in 3D (``N×3``).

    Implements A5: 3D default waypoint ``(0.8L, 0.8L, 0.8L)`` and
    diagonal-opposite split waypoints. Force for a leader i is
    ``leader_strength * normalize(g_i − x_i)``; zero for followers.
    """
    N = positions.shape[0]
    forces = np.zeros((N, 3))

    in_split = (
        split_t_on is not None
        and split_t_off is not None
        and split_t_on <= step < split_t_off
    )

    for i in np.where(leader_groups >= 0)[0]:
        if in_split:
            target = split_waypoints[int(leader_groups[i]) % 2]
        else:
            target = default_waypoint
        diff = target - positions[i]
        norm = float(np.linalg.norm(diff))
        if norm > 1e-12:
            forces[i] = leader_strength * diff / norm

    return forces


def milling_force(
    positions: np.ndarray,
    velocities: np.ndarray,
    mu: float,
    R: float,
    kappa: float,
    L: float,
    eps: float = 1e-6,
) -> np.ndarray:
    """Velocity-projected milling force in 3D (A3).

    Produces a dimension-agnostic tangent that reduces to the 2D
    ``τ_i = (−r̂_y, r̂_x)`` prescription in the planar limit:

    .. math::
        r_i     &= x_i - x_c,\\qquad x_c = (L/2, L/2, L/2) \\\\
        \\hat r_i &= r_i / \\|r_i\\| \\\\
        v_{tan,i} &= v_i - (v_i \\cdot \\hat r_i) \\hat r_i \\\\
        \\hat\\tau_i &= v_{tan,i}/\\|v_{tan,i}\\| \\quad(\\text{fallback on } <\\varepsilon) \\\\
        m_i     &= \\mu (\\hat\\tau_i + \\kappa (R - r_i) \\hat r_i)

    The Gram-Schmidt fallback constructs a unit vector orthogonal to
    ``r̂_i`` when the current velocity is parallel to the radial direction
    (``||v_tan,i|| < eps``), so orbiting starts in a deterministic plane.
    """
    center = 0.5 * L * np.ones(3)
    delta = positions - center                     # (N, 3)
    r = np.linalg.norm(delta, axis=1)               # (N,)
    r_safe = np.where(r < 1e-12, 1e-12, r)
    r_hat = delta / r_safe[:, np.newaxis]           # (N, 3)

    # Tangent component of current velocity
    v_dot_r = np.einsum("ij,ij->i", velocities, r_hat)  # (N,)
    v_tan = velocities - v_dot_r[:, np.newaxis] * r_hat  # (N, 3)
    v_tan_norm = np.linalg.norm(v_tan, axis=1)           # (N,)

    tau_hat = np.zeros_like(r_hat)
    good = v_tan_norm >= eps
    tau_hat[good] = v_tan[good] / v_tan_norm[good, np.newaxis]

    # Gram-Schmidt fallback for near-radial agents: pick a reference axis
    # least parallel to r̂ to guarantee a non-degenerate cross product.
    if (~good).any():
        idx = np.where(~good)[0]
        ref = np.zeros((idx.size, 3))
        # For each fallback agent, choose the standard axis that is
        # least aligned with its r̂ (smallest |component|).
        comp = np.abs(r_hat[idx])
        axis_pick = np.argmin(comp, axis=1)  # 0, 1, or 2
        ref[np.arange(idx.size), axis_pick] = 1.0
        # Orthogonalize: t = ref - (ref·r̂) r̂
        dots = np.einsum("ij,ij->i", ref, r_hat[idx])
        t = ref - dots[:, np.newaxis] * r_hat[idx]
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        tau_hat[idx] = t

    radial = kappa * (R - r)[:, np.newaxis] * r_hat  # (N, 3)
    return mu * (tau_hat + radial)
