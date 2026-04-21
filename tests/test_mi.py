"""Phase 2 validation tests for MI estimators (B6, D3).

These are the most important tests in Phase 2: bugs in MI estimation silently
propagate through every downstream Φ_spectral result.
"""

from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d.analysis.mi import (
    mi_matrix_gaussian,
    mi_matrix_histogram,
    mi_matrix_ksg,
    standardize_window,
)


# --------------------------------------------------------------------------
# Standardization (D3)
# --------------------------------------------------------------------------


def test_standardize_window_zero_mean_unit_std():
    rng = np.random.default_rng(0)
    X = rng.normal(loc=3.0, scale=2.0, size=(50, 6, 3))
    Xs = standardize_window(X)
    np.testing.assert_allclose(Xs.mean(axis=0), 0.0, atol=1e-10)
    np.testing.assert_allclose(Xs.std(axis=0, ddof=0), 1.0, atol=1e-10)


def test_standardize_window_constant_channel_zero():
    X = np.ones((20, 3, 2))
    X[:, :, 0] = 5.0
    X[:, :, 1] = np.arange(20).reshape(20, 1)
    Xs = standardize_window(X)
    np.testing.assert_allclose(Xs[:, :, 0], 0.0)
    np.testing.assert_allclose(Xs[:, :, 1].mean(axis=0), 0.0, atol=1e-10)
    np.testing.assert_allclose(Xs[:, :, 1].std(axis=0), 1.0, atol=1e-10)


# --------------------------------------------------------------------------
# Independent Gaussians — MI should be ~0 (within estimator bias tolerances)
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def independent_window():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(100, 10, 4))
    return standardize_window(X)


def test_ksg_independent_near_zero(independent_window):
    M = mi_matrix_ksg(independent_window, k=5)
    off_diag = M[~np.eye(10, dtype=bool)]
    assert abs(off_diag.mean()) < 0.15
    assert off_diag.max() < 0.35


def test_histogram_independent_bounded(independent_window):
    M = mi_matrix_histogram(independent_window, n_bins=8)
    off_diag = M[~np.eye(10, dtype=bool)]
    assert np.all(np.isfinite(off_diag))
    assert off_diag.mean() < 5.0


def test_gaussian_independent_near_zero(independent_window):
    M = mi_matrix_gaussian(independent_window)
    off_diag = M[~np.eye(10, dtype=bool)]
    assert abs(off_diag.mean()) < 0.2
    assert off_diag.max() < 0.6


# --------------------------------------------------------------------------
# Perfectly correlated agents — MI much larger than in independent case
# --------------------------------------------------------------------------


def test_all_estimators_correlated_gt_independent():
    rng = np.random.default_rng(0)
    base = rng.normal(size=(100, 4))
    X = np.broadcast_to(base[:, None, :], (100, 6, 4)).copy()
    Xs = standardize_window(X)

    ksg_corr = mi_matrix_ksg(Xs, k=5)
    hist_corr = mi_matrix_histogram(Xs, n_bins=8)
    gauss_corr = mi_matrix_gaussian(Xs)

    for M in (ksg_corr, hist_corr, gauss_corr):
        off_diag = M[~np.eye(6, dtype=bool)]
        assert off_diag.min() > 0.3


# --------------------------------------------------------------------------
# Known-correlation bivariate Gaussian — analytic reference
# --------------------------------------------------------------------------


@pytest.mark.parametrize("rho", [0.3, 0.6, 0.9])
def test_gaussian_matches_analytic_mi(rho):
    rng = np.random.default_rng(7)
    W = 500
    cov = np.array([[1.0, rho], [rho, 1.0]])
    samples = rng.multivariate_normal([0.0, 0.0], cov, size=W)
    X = np.stack([samples[:, 0:1], samples[:, 1:2]], axis=1)
    Xs = standardize_window(X)
    analytic = -0.5 * np.log(1.0 - rho * rho)

    M_gauss = mi_matrix_gaussian(Xs)
    assert abs(M_gauss[0, 1] - analytic) < 0.05


@pytest.mark.parametrize("rho", [0.3, 0.6, 0.9])
def test_ksg_matches_analytic_mi(rho):
    rng = np.random.default_rng(13)
    W = 500
    cov = np.array([[1.0, rho], [rho, 1.0]])
    samples = rng.multivariate_normal([0.0, 0.0], cov, size=W)
    X = np.stack([samples[:, 0:1], samples[:, 1:2]], axis=1)
    Xs = standardize_window(X)
    analytic = -0.5 * np.log(1.0 - rho * rho)

    M_ksg = mi_matrix_ksg(Xs, k=5)
    assert abs(M_ksg[0, 1] - analytic) < 0.15


# --------------------------------------------------------------------------
# Structural invariants
# --------------------------------------------------------------------------


@pytest.fixture
def small_window():
    rng = np.random.default_rng(1)
    return standardize_window(rng.normal(size=(60, 5, 3)))


def test_symmetry_all_estimators(small_window):
    for fn in (mi_matrix_ksg, mi_matrix_histogram, mi_matrix_gaussian):
        M = fn(small_window)
        np.testing.assert_allclose(M, M.T, atol=1e-12)


def test_diagonal_is_zero(small_window):
    for fn in (mi_matrix_ksg, mi_matrix_histogram, mi_matrix_gaussian):
        M = fn(small_window)
        np.testing.assert_array_equal(np.diag(M), 0.0)


def test_nonnegativity(small_window):
    for fn in (mi_matrix_ksg, mi_matrix_histogram, mi_matrix_gaussian):
        M = fn(small_window)
        assert M.min() >= -1e-10


# --------------------------------------------------------------------------
# Scale invariance (KSG & Gaussian are scale-invariant on paper)
# --------------------------------------------------------------------------


def test_ksg_scale_invariance():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(80, 4, 2))
    Xs = standardize_window(X)
    M1 = mi_matrix_ksg(Xs, k=5)
    M2 = mi_matrix_ksg(10.0 * Xs, k=5)
    np.testing.assert_allclose(M1, M2, atol=1e-8)


def test_gaussian_scale_invariance():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(80, 4, 2))
    Xs = standardize_window(X)
    M1 = mi_matrix_gaussian(Xs)
    M2 = mi_matrix_gaussian(10.0 * Xs)
    np.testing.assert_allclose(M1, M2, atol=1e-6)
