"""Persistent homology TDA pipeline for 3D swarm analysis.

Phase 3 implementation. See SpectralSwarm3DPhases.md §Phase 3, B3, B4, D8.

Extends 2D pipeline to maxdim=2 for H2 void detection (B4). Adds augmented
snapshot embedding option (B3: methodology §3.5). Snapshot H2 is the primary
3D contribution; trajectory H2 on W*d-dimensional ambient space is exploratory.

Stability note (D8): bottleneck distances are Lipschitz-stable per Cohen-Steiner
et al. (2007). Total persistence and max persistence are not stability-guaranteed
and should be interpreted as more noise-sensitive summaries. Where they disagree
with bottleneck results, the bottleneck result is treated as more reliable.

References:
    Tralie et al. 2018 (Ripser.py)
    Perea & Harer 2015 (trajectory cloud theoretical foundation)
    Zomorodian & Carlsson 2005 (H2 in TDA)
    Cohen-Steiner, Edelsbrunner & Harer 2007 (bottleneck stability)
"""

from __future__ import annotations

import numpy as np
from persim import bottleneck
from ripser import ripser


def snapshot_cloud(
    positions: np.ndarray,
    augmented: bool = False,
    velocities: np.ndarray | None = None,
    beta: float = 0.35,
) -> np.ndarray:
    """Build a snapshot point cloud for Ripser input. Implements B3.

    Parameters
    ----------
    positions : np.ndarray
        Shape (N, 3) agent positions at a single timestep.
    augmented : bool
        If True, concatenate beta-scaled velocities per Bailey (2026) §3.5:
        ``y_i = (x_i, y_i, z_i, beta * vx_i, beta * vy_i, beta * vz_i)``.
    velocities : np.ndarray or None
        Shape (N, 3). Required when ``augmented=True``.
    beta : float
        Velocity scaling factor (default 0.35 per methodology §3.5).

    Returns
    -------
    np.ndarray
        Shape (N, 3) if not augmented; (N, 6) if augmented.
    """
    positions = np.asarray(positions, dtype=np.float64)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError(
            f"positions must be shape (N, 3); got {positions.shape}."
        )
    if not augmented:
        return positions.copy()

    if velocities is None:
        raise ValueError(
            "snapshot_cloud(augmented=True) requires `velocities` of shape (N, 3); got None."
        )
    velocities = np.asarray(velocities, dtype=np.float64)
    if velocities.shape != positions.shape:
        raise ValueError(
            f"velocities shape {velocities.shape} does not match positions {positions.shape}."
        )
    return np.concatenate([positions, beta * velocities], axis=1)


def trajectory_cloud(features_window: np.ndarray) -> np.ndarray:
    """Build a trajectory (sliding-window) point cloud. Implements B4 / Perea & Harer (2015).

    Each agent's W time steps of d-dimensional features are flattened into a
    single W*d-dimensional point.

    Standardization is an upstream responsibility. The spectral pipeline already
    standardizes in ``phi_spectral_over_windows``; re-standardizing here would
    couple the two branches in a way that is hard to debug.

    Parameters
    ----------
    features_window : np.ndarray
        Shape (W, N, d). Assumed already standardized upstream (D3).

    Returns
    -------
    np.ndarray
        Shape (N, W*d). ``out[i, :]`` equals ``features_window[:, i, :].reshape(-1)``.
    """
    features_window = np.asarray(features_window, dtype=np.float64)
    if features_window.ndim != 3:
        raise ValueError(
            f"features_window must be shape (W, N, d); got {features_window.shape}."
        )
    W, N, d = features_window.shape
    out = np.empty((N, W * d), dtype=np.float64)
    for i in range(N):
        out[i, :] = features_window[:, i, :].reshape(-1)
    return out


def compute_persistence(X: np.ndarray, maxdim: int = 2) -> list[np.ndarray]:
    """Compute persistent homology through ``maxdim`` via Ripser. Implements B4.

    Parameters
    ----------
    X : np.ndarray
        Shape (n_points, ambient_dim) point cloud.
    maxdim : int
        Maximum homology dimension (default 2: H0, H1, H2 per Bailey (2026) §3.5
        extension for 3D — H2 detects enclosed voids).

    Returns
    -------
    list of np.ndarray
        ``[dgm_H0, dgm_H1, ..., dgm_H{maxdim}]``. Each dgm has shape
        ``(n_features, 2)`` with (birth, death). Infinite-death features use
        ``np.inf`` and are filtered by the summary functions.
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError(f"X must be 2D (n_points, ambient_dim); got {X.shape}.")
    result = ripser(X, maxdim=maxdim)
    return list(result["dgms"])


def _finite_persistences(dgm: np.ndarray) -> np.ndarray:
    """Return (death - birth) for finite-death bars only.

    H0 always contains exactly one infinite-death bar (the persistent connected
    component at threshold infinity). Dropping it keeps TP_0 finite and
    meaningful.
    """
    if dgm.size == 0:
        return np.array([], dtype=np.float64)
    finite_mask = np.isfinite(dgm[:, 1])
    if not finite_mask.any():
        return np.array([], dtype=np.float64)
    bars = dgm[finite_mask]
    return bars[:, 1] - bars[:, 0]


def persistence_summaries(
    dgms: list[np.ndarray],
    baseline_dgms: list[np.ndarray] | None = None,
    prev_dgms: list[np.ndarray] | None = None,
    maxdim: int = 2,
) -> dict[str, float]:
    """Compute scalar summaries of persistence diagrams. Implements B4.

    For each dimension ``k`` in ``0..maxdim``:
      - ``TP_k``: total persistence (sum of death-birth over finite bars).
      - ``MP_k``: max persistence (max death-birth over finite bars).
      - ``B_base_k``: bottleneck distance to ``baseline_dgms[k]`` if provided, else NaN.
      - ``B_prev_k``: bottleneck distance to ``prev_dgms[k]`` if provided, else NaN.

    H0's single infinite-death bar is dropped from TP_0 and MP_0 (otherwise
    both would always be infinite). Bottleneck distances are computed via
    ``persim.bottleneck`` which handles infinite-death features internally.

    Parameters
    ----------
    dgms : list of np.ndarray
        ``[dgm_H0, dgm_H1, ..., dgm_H{maxdim}]`` from ``compute_persistence``.
    baseline_dgms : list of np.ndarray or None
        Reference diagrams (typically first-window). None skips B_base.
    prev_dgms : list of np.ndarray or None
        Previous-window diagrams. None skips B_prev.
    maxdim : int
        Highest homology dimension to summarize. Must satisfy
        ``len(dgms) >= maxdim + 1``.

    Returns
    -------
    dict[str, float]
        Keys: ``TP_k``, ``MP_k``, ``B_base_k``, ``B_prev_k`` for each
        ``k in 0..maxdim``. Missing bottleneck entries are NaN (not 0, not absent).
    """
    if len(dgms) < maxdim + 1:
        raise ValueError(
            f"dgms has {len(dgms)} diagrams but maxdim={maxdim} requires at least {maxdim + 1}."
        )

    out: dict[str, float] = {}
    for k in range(maxdim + 1):
        pers = _finite_persistences(dgms[k])
        out[f"TP_{k}"] = float(pers.sum()) if pers.size else 0.0
        out[f"MP_{k}"] = float(pers.max()) if pers.size else 0.0

        if baseline_dgms is not None and k < len(baseline_dgms):
            out[f"B_base_{k}"] = float(bottleneck(dgms[k], baseline_dgms[k]))
        else:
            out[f"B_base_{k}"] = float("nan")

        if prev_dgms is not None and k < len(prev_dgms):
            out[f"B_prev_{k}"] = float(bottleneck(dgms[k], prev_dgms[k]))
        else:
            out[f"B_prev_{k}"] = float("nan")

    return out
