"""Phase 2 tests for the spectral pipeline (normalized Laplacian, Fiedler, Φ_spectral)."""

from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d.analysis.spectral import (
    fiedler_bipartition,
    normalized_laplacian,
    phi_spectral,
    phi_spectral_over_windows,
)


def _block_mi(n_per_block: int = 5, intra: float = 1.0, inter: float = 0.0) -> np.ndarray:
    N = 2 * n_per_block
    M = np.full((N, N), inter, dtype=np.float64)
    block = np.full((n_per_block, n_per_block), intra)
    M[:n_per_block, :n_per_block] = block
    M[n_per_block:, n_per_block:] = block
    np.fill_diagonal(M, 0.0)
    return M


def test_laplacian_symmetric_and_psd():
    rng = np.random.default_rng(0)
    W = np.abs(rng.normal(size=(8, 8)))
    W = 0.5 * (W + W.T)
    np.fill_diagonal(W, 0.0)
    L = normalized_laplacian(W)
    np.testing.assert_allclose(L, L.T, atol=1e-12)
    eigvals = np.linalg.eigvalsh(L)
    assert eigvals.min() >= -1e-10


def test_laplacian_two_components_has_two_zero_eigenvalues():
    M = _block_mi(5, intra=1.0, inter=0.0)
    L = normalized_laplacian(M)
    eigvals = np.sort(np.linalg.eigvalsh(L))
    assert abs(eigvals[0]) < 1e-10
    assert abs(eigvals[1]) < 1e-10
    assert eigvals[2] > 1e-6


def test_fiedler_recovers_block_partition():
    M = _block_mi(5, intra=1.0, inter=0.01)  # small cross-MI to make it connected
    L = normalized_laplacian(M)
    part = fiedler_bipartition(L)
    # Either labelling is acceptable.
    first = part[:5]
    second = part[5:]
    assert np.all(first == first[0]) and np.all(second == second[0])
    assert first[0] != second[0]


def test_phi_spectral_zero_for_disconnected_blocks():
    M = _block_mi(5, intra=1.0, inter=0.0)
    part = np.array([0] * 5 + [1] * 5)
    assert phi_spectral(M, part) == 0.0


def test_phi_spectral_maximal_on_uniform_mi():
    N = 8
    M = np.ones((N, N)) - np.eye(N)
    part = np.array([0] * (N // 2) + [1] * (N // 2))
    # Cross edges = 4 * 4 = 16 pairs, each MI=1, counted once.
    assert phi_spectral(M, part) == pytest.approx(16.0)


def test_end_to_end_phi_spectral_over_windows():
    rng = np.random.default_rng(5)
    T, N, d = 60, 6, 3
    features = rng.normal(size=(T, N, d))
    out = phi_spectral_over_windows(features, W=20, stride=1, estimator="gaussian")
    assert out.shape == ((T - 20) // 1 + 1,)
    assert np.all(np.isfinite(out))
    assert np.all(out >= -1e-10)


def test_phi_spectral_over_windows_ksg_small():
    rng = np.random.default_rng(9)
    T, N, d = 50, 5, 2
    features = rng.normal(size=(T, N, d))
    out = phi_spectral_over_windows(features, W=20, stride=2, estimator="ksg", k=3)
    assert out.shape == ((T - 20) // 2 + 1,)
    assert np.all(np.isfinite(out))
