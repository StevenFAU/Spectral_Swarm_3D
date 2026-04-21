"""Classical swarm order parameters for 3D telemetry.

Phase 2 implementation target. See SpectralSwarm3DPhases.md §Phase 2 and B5.

Implements:
  - polarization: mean normalized velocity alignment (scalar in [0, 1]).
  - milling_score: mean |r_hat x v_hat| using 3D vector cross product magnitude.
    Reduces to 2D methodology definition (Bailey 2026 §3.6) in the planar limit.
  - angular_momentum_norm: ||(1/N) sum r_i x v_i|| normalized by run maximum.
    Captures global rotational coherence; complements milling_score (B5).
"""
import numpy as np


def polarization(velocities: np.ndarray) -> float:
    """Compute swarm polarization (mean heading alignment). Phase 2.

    Parameters
    ----------
    velocities : np.ndarray, shape (N, 3)
        Agent velocity vectors at a single timestep.

    Returns
    -------
    float
        Polarization in [0, 1].
    """
    raise NotImplementedError("Phase 2 — see SpectralSwarm3DPhases.md B5")


def milling_score(positions: np.ndarray, velocities: np.ndarray, center: np.ndarray) -> float:
    """Compute milling score via 3D cross-product magnitude (B5). Phase 2.

    M(t) = (1/N) sum_i |r_hat_i x v_hat_i|

    Reduces to Bailey (2026) §3.6 scalar 2D definition in the planar limit.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
    velocities : np.ndarray, shape (N, 3)
    center : np.ndarray, shape (3,)
        Domain center (typically (L/2, L/2, L/2)).

    Returns
    -------
    float
        Milling score in [0, 1].
    """
    raise NotImplementedError("Phase 2 — see SpectralSwarm3DPhases.md B5")


def angular_momentum_norm(
    positions: np.ndarray, velocities: np.ndarray, center: np.ndarray
) -> float:
    """Compute normalized angular momentum magnitude (B5). Phase 2.

    L = ||(1/N) sum_i r_i x v_i|| / max_over_run

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
    velocities : np.ndarray, shape (N, 3)
    center : np.ndarray, shape (3,)

    Returns
    -------
    float
        Raw angular momentum magnitude (normalization applied in aggregation).
    """
    raise NotImplementedError("Phase 2 — see SpectralSwarm3DPhases.md B5")
