"""Pairwise mutual-information estimators for the 3D swarm analysis pipeline.

Implements B6 and D3 (Phase 2):

  - :func:`standardize_window` — per-agent per-channel z-score within a single
    window. Explicit pipeline step (D3); not buried inside the estimator.
  - :func:`mi_matrix_ksg` — KSG k-NN estimator (Kraskov et al. 2004 eq. 8),
    Chebyshev metric, tie-break noise. Primary estimator (methodology §3.4).
  - :func:`mi_matrix_histogram` — quantile-binned joint histogram estimator
    (sensitivity check).
  - :func:`mi_matrix_gaussian` — closed-form Gaussian MI; retained for
    2D-to-3D comparability.

All estimators accept a window ``X`` of shape ``(W, N, d)`` and return an
``(N, N)`` symmetric non-negative MI matrix with zero diagonal.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy.spatial import cKDTree
from scipy.special import digamma


def standardize_window(X: np.ndarray) -> np.ndarray:
    """Per-agent per-channel z-score within a single window (D3).

    Parameters
    ----------
    X : np.ndarray
        Shape ``(W, N, d)``.

    Returns
    -------
    np.ndarray
        Same shape. Each ``(agent, channel)`` column is zero-mean and
        unit-std; columns that are exactly constant become zero.
    """
    if X.ndim != 3:
        raise ValueError(f"standardize_window expects (W, N, d); got shape {X.shape}")
    X = np.asarray(X, dtype=np.float64)
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, ddof=0, keepdims=True)
    out = X - mean
    mask = std > 0.0
    safe_std = np.where(mask, std, 1.0)
    out = np.where(mask, out / safe_std, 0.0)
    return out


def _add_tie_noise(X: np.ndarray, noise_eps: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Scale noise by per-channel std so the estimator remains scale-invariant
    # in practice: a fixed-absolute eps would couple noise-dominated regions
    # to input magnitude and break scale-invariance on x10 scaling.
    scale = X.std(axis=0, keepdims=True)
    scale = np.where(scale > 0.0, scale, 1.0)
    return X + rng.uniform(-noise_eps, noise_eps, size=X.shape) * scale


def _pair_mi_ksg(xi: np.ndarray, xj: np.ndarray, k: int) -> float:
    """KSG estimator (first variant, Kraskov 2004 eq. 8) for a single pair.

    Parameters
    ----------
    xi, xj : np.ndarray
        Shape ``(W, d)`` each; already noise-perturbed.
    """
    W = xi.shape[0]
    Z = np.hstack([xi, xj])

    tree_joint = cKDTree(Z)
    # (k+1)-th neighbour because the nearest neighbour is the point itself.
    dists, _ = tree_joint.query(Z, k=k + 1, p=np.inf)
    eps = dists[:, -1]

    tree_x = cKDTree(xi)
    tree_y = cKDTree(xj)
    r_eps = eps * (1.0 - 1e-12)
    nx = np.array(
        [len(tree_x.query_ball_point(xi[n], r=r_eps[n], p=np.inf)) - 1 for n in range(W)]
    )
    ny = np.array(
        [len(tree_y.query_ball_point(xj[n], r=r_eps[n], p=np.inf)) - 1 for n in range(W)]
    )
    nx = np.clip(nx, 0, None)
    ny = np.clip(ny, 0, None)

    mi = digamma(k) - np.mean(digamma(nx + 1) + digamma(ny + 1)) + digamma(W)
    return float(max(mi, 0.0))


def mi_matrix_ksg(
    X: np.ndarray, k: int = 5, noise_eps: float = 1e-10, seed: int = 0
) -> np.ndarray:
    """Pairwise KSG MI matrix (Kraskov et al. 2004 eq. 8).

    Parameters
    ----------
    X : np.ndarray
        Shape ``(W, N, d)``. Should be standardized (D3) beforehand.
    k : int
        Number of nearest neighbours (methodology default 5).
    noise_eps : float
        Amplitude of uniform tie-break noise added before k-NN queries.
    seed : int
        RNG seed for the tie-break noise (deterministic reruns).

    Returns
    -------
    np.ndarray
        Shape ``(N, N)``, symmetric, zero diagonal, non-negative.
    """
    X = np.asarray(X, dtype=np.float64)
    W, N, _d = X.shape
    if W <= k + 1:
        raise ValueError(f"W={W} too small for k={k} (need W > k+1).")

    X_noisy = _add_tie_noise(X, noise_eps, seed=seed)
    M = np.zeros((N, N), dtype=np.float64)
    for i in range(N):
        for j in range(i + 1, N):
            mi = _pair_mi_ksg(X_noisy[:, i, :], X_noisy[:, j, :], k=k)
            M[i, j] = mi
            M[j, i] = mi
    return M


def _quantile_bin(x: np.ndarray, n_bins: int) -> np.ndarray:
    """Map each column of ``x`` (shape (W, d)) to equal-frequency integer bins.

    Constant columns collapse to a single bin (all zeros).
    """
    W, d = x.shape
    out = np.zeros((W, d), dtype=np.int64)
    qs = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
    for c in range(d):
        col = x[:, c]
        if np.ptp(col) == 0:
            continue
        edges = np.quantile(col, qs)
        out[:, c] = np.digitize(col, edges, right=False)
    return out


def _mi_from_samples(samples_x: np.ndarray, samples_y: np.ndarray) -> float:
    W = samples_x.shape[0]
    tx = [tuple(row) for row in samples_x]
    ty = [tuple(row) for row in samples_y]
    tj = [(a, b) for a, b in zip(tx, ty)]
    px = Counter(tx)
    py = Counter(ty)
    pj = Counter(tj)
    mi = 0.0
    for (a, b), nij in pj.items():
        p_ij = nij / W
        p_a = px[a] / W
        p_b = py[b] / W
        mi += p_ij * np.log(p_ij / (p_a * p_b))
    return float(max(mi, 0.0))


def mi_matrix_histogram(X: np.ndarray, n_bins: int = 8) -> np.ndarray:
    """Pairwise MI matrix via quantile-binned joint histograms.

    Parameters
    ----------
    X : np.ndarray
        Shape ``(W, N, d)``. Should be standardized (D3) beforehand.
    n_bins : int
        Number of bins per channel (methodology §3.4 default 8).

    Returns
    -------
    np.ndarray
        Shape ``(N, N)``, symmetric, zero diagonal, non-negative.
    """
    X = np.asarray(X, dtype=np.float64)
    _W, N, _d = X.shape
    binned = np.stack([_quantile_bin(X[:, i, :], n_bins) for i in range(N)], axis=1)

    M = np.zeros((N, N), dtype=np.float64)
    for i in range(N):
        for j in range(i + 1, N):
            mi = _mi_from_samples(binned[:, i, :], binned[:, j, :])
            M[i, j] = mi
            M[j, i] = mi
    return M


def mi_matrix_gaussian(X: np.ndarray, ridge: float = 1e-8) -> np.ndarray:
    """Gaussian closed-form MI: 0.5 * log(|Σ_x| |Σ_y| / |Σ_xy|).

    Parameters
    ----------
    X : np.ndarray
        Shape ``(W, N, d)``. Should be standardized (D3) beforehand.
    ridge : float
        Added to diagonal of covariance matrices for numerical stability.

    Returns
    -------
    np.ndarray
        Shape ``(N, N)``, symmetric, zero diagonal, non-negative.
    """
    X = np.asarray(X, dtype=np.float64)
    W, N, d = X.shape
    I_d = np.eye(d) * ridge
    I_2d = np.eye(2 * d) * ridge

    covs = np.zeros((N, d, d))
    logdets = np.zeros(N)
    for i in range(N):
        c = np.cov(X[:, i, :], rowvar=False, ddof=0).reshape(d, d) + I_d
        covs[i] = c
        sign, ld = np.linalg.slogdet(c)
        logdets[i] = ld if sign > 0 else -np.inf

    M = np.zeros((N, N), dtype=np.float64)
    for i in range(N):
        for j in range(i + 1, N):
            joint = np.hstack([X[:, i, :], X[:, j, :]])
            cj = np.cov(joint, rowvar=False, ddof=0).reshape(2 * d, 2 * d) + I_2d
            sign, ld = np.linalg.slogdet(cj)
            if sign <= 0:
                mi = 0.0
            else:
                mi = 0.5 * (logdets[i] + logdets[j] - ld)
            mi = float(max(mi, 0.0))
            M[i, j] = mi
            M[j, i] = mi
    _ = W  # silence unused
    return M
