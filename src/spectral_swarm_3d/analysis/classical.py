"""Classical swarm order parameters (B5) — polarization, milling magnitude,
angular-momentum norm. All functions operate on a single timestep.

Reduces to Bailey (2026) §3.6 2D definitions in the planar limit (agents
confined to z=0 with vz=0).
"""

from __future__ import annotations

import numpy as np


def _unit(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Row-wise unit vectors. Zero-length rows return the zero vector."""
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    safe = np.where(norm > eps, norm, 1.0)
    out = v / safe
    return np.where(norm > eps, out, 0.0)


def polarization(velocities: np.ndarray) -> float:
    """Mean-heading alignment ``||mean(v_hat)||``; scalar in ``[0, 1]``.

    Parameters
    ----------
    velocities : np.ndarray
        Shape ``(N, d)`` (typically ``d=3``).
    """
    v = np.asarray(velocities, dtype=np.float64)
    u = _unit(v)
    return float(np.linalg.norm(u.mean(axis=0)))


def milling_score_magnitude(
    positions: np.ndarray,
    velocities: np.ndarray,
    center: np.ndarray,
) -> float:
    """Mean ``|r_hat × v_hat|`` (3D cross-product magnitude). Reduces to the
    2D scalar ``|cross|`` value in the planar limit.
    """
    p = np.asarray(positions, dtype=np.float64)
    v = np.asarray(velocities, dtype=np.float64)
    c = np.asarray(center, dtype=np.float64)
    r = p - c
    r_hat = _unit(r)
    v_hat = _unit(v)
    crosses = np.cross(r_hat, v_hat)
    return float(np.linalg.norm(crosses, axis=-1).mean())


def angular_momentum_norm(
    positions: np.ndarray,
    velocities: np.ndarray,
    center: np.ndarray,
) -> float:
    """``||(1/N) Σ r_i × v_i||``. Global rotational coherence (B5 secondary)."""
    p = np.asarray(positions, dtype=np.float64)
    v = np.asarray(velocities, dtype=np.float64)
    c = np.asarray(center, dtype=np.float64)
    r = p - c
    L = np.cross(r, v).mean(axis=0)
    return float(np.linalg.norm(L))
