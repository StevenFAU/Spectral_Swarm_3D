"""Spectral integration analysis: normalized Laplacian, Fiedler, Φ_spectral.

Phase 2. Dimension-agnostic since the MI matrix is ``(N, N)`` regardless of
feature dimensionality. Implements Bailey & Schneider (2025) §2 and Bailey
(2026) §3.4.

Epistemic note (methodology §3.4): ``Φ_spectral`` is an operational windowed
dependence score, not an unbiased population MI estimate. The spectral
bipartition is a relaxation of normalized minimum cut (itself NP-hard), which
is a relaxation of the MIP.
"""

from __future__ import annotations

import numpy as np

from spectral_swarm_3d.analysis.mi import (
    mi_matrix_gaussian,
    mi_matrix_histogram,
    mi_matrix_ksg,
    standardize_window,
)


_ESTIMATORS = {
    "ksg": mi_matrix_ksg,
    "histogram": mi_matrix_histogram,
    "gaussian": mi_matrix_gaussian,
}


def normalized_laplacian(mi_matrix: np.ndarray) -> np.ndarray:
    """Symmetric normalized Laplacian ``L = I - D^{-1/2} W D^{-1/2}``.

    Isolated nodes (row-sum zero) are handled by setting the corresponding
    ``D^{-1/2}`` entry to zero — these nodes become disconnected components.
    """
    W = np.asarray(mi_matrix, dtype=np.float64)
    if W.shape[0] != W.shape[1]:
        raise ValueError(f"mi_matrix must be square; got {W.shape}")
    np.fill_diagonal(W, 0.0)
    deg = W.sum(axis=1)
    with np.errstate(divide="ignore"):
        inv_sqrt = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
    D_inv_sqrt = np.diag(inv_sqrt)
    L = np.eye(W.shape[0]) - D_inv_sqrt @ W @ D_inv_sqrt
    L = 0.5 * (L + L.T)
    return L


def fiedler_vector(laplacian: np.ndarray) -> np.ndarray:
    """Second-smallest-eigenvalue eigenvector of the Laplacian."""
    L = 0.5 * (laplacian + laplacian.T)
    eigvals, eigvecs = np.linalg.eigh(L)
    order = np.argsort(eigvals)
    return eigvecs[:, order[1]]


def fiedler_bipartition(laplacian: np.ndarray) -> np.ndarray:
    """Partition nodes into ``{0, 1}`` by sign of the Fiedler vector.

    Ties at zero (Fiedler entry exactly 0) are resolved by the leading-entry
    sign convention: if the first non-zero component is negative, the output
    is flipped so label 0 corresponds to the positive-sign side. This gives
    deterministic output under degenerate multiplicity > 1 cases.
    """
    f = fiedler_vector(laplacian)
    nonzero = np.flatnonzero(np.abs(f) > 1e-12)
    if nonzero.size and f[nonzero[0]] < 0:
        f = -f
    return (f >= 0).astype(np.int64)


def phi_spectral(mi_matrix: np.ndarray, partition: np.ndarray) -> float:
    """Sum of MI edges that cross the ``partition`` bipartition.

    ``Φ_spectral = Σ_{i<j, part[i] != part[j]} MI[i, j]``.
    """
    W = np.asarray(mi_matrix, dtype=np.float64)
    p = np.asarray(partition).astype(np.int64)
    cross = p[:, None] != p[None, :]
    upper = np.triu(cross, k=1)
    return float(W[upper].sum())


def phi_spectral_over_windows(
    features: np.ndarray,
    W: int,
    stride: int,
    estimator: str = "ksg",
    **estimator_kwargs,
) -> np.ndarray:
    """End-to-end Φ_spectral time series over sliding windows.

    For each window ``(t : t+W)``:
      1. Slice ``features`` → ``(W, N, d)``.
      2. Standardize per D3.
      3. Compute MI matrix with the selected estimator.
      4. Normalized Laplacian → Fiedler bipartition.
      5. Accumulate MI across the cut.

    Parameters
    ----------
    features : np.ndarray
        Shape ``(T, N, d)`` telemetry-derived feature array.
    W : int
        Window length.
    stride : int
        Step between successive window starts.
    estimator : str
        One of ``"ksg"``, ``"histogram"``, ``"gaussian"``.
    **estimator_kwargs :
        Forwarded to the selected estimator.

    Returns
    -------
    np.ndarray
        1-D array of length ``(T - W) // stride + 1``.
    """
    if estimator not in _ESTIMATORS:
        raise ValueError(
            f"Unknown estimator {estimator!r}; expected one of {sorted(_ESTIMATORS)}."
        )
    features = np.asarray(features, dtype=np.float64)
    if features.ndim != 3:
        raise ValueError(f"features must be (T, N, d); got shape {features.shape}")
    T = features.shape[0]
    if W > T:
        raise ValueError(f"W={W} exceeds T={T}.")
    if stride < 1:
        raise ValueError(f"stride must be >= 1; got {stride}")

    fn = _ESTIMATORS[estimator]
    n_windows = (T - W) // stride + 1
    out = np.zeros(n_windows, dtype=np.float64)
    for k in range(n_windows):
        t0 = k * stride
        window = features[t0 : t0 + W]
        Xs = standardize_window(window)
        M = fn(Xs, **estimator_kwargs)
        L = normalized_laplacian(M)
        part = fiedler_bipartition(L)
        out[k] = phi_spectral(M, part)
    return out
