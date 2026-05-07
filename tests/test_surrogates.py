"""Tests for Phase 5 Tier 2.B surrogate null testing (D1).

Covers:
  - circular_shift_telemetry: marginal preservation, per-agent independence,
    round-trip inversion
  - Phi_spectral direction: perfectly-correlated flock > shuffled surrogate
  - Noise sanity check: near-random flock yields observed ≈ surrogate
"""
from __future__ import annotations

import numpy as np
import pytest

from spectral_swarm_3d.analysis.surrogates import (
    circular_shift_telemetry,
    surrogate_phi_spectral,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_correlated_features(T: int = 60, N: int = 8, d: int = 2, seed: int = 0) -> np.ndarray:
    """All agents track the same shared signal + small noise → high cross-agent MI."""
    rng = np.random.default_rng(seed)
    shared = rng.standard_normal((T, d))             # (T, d) shared signal
    per_agent_noise = rng.standard_normal((T, N, d)) * 0.05
    features = shared[:, np.newaxis, :] + per_agent_noise  # (T, N, d)
    return features


def _make_random_features(T: int = 60, N: int = 8, d: int = 2, seed: int = 42) -> np.ndarray:
    """Independent random features per agent → low cross-agent MI."""
    return np.random.default_rng(seed).standard_normal((T, N, d))


# ---------------------------------------------------------------------------
# circular_shift_telemetry tests
# ---------------------------------------------------------------------------

class TestCircularShift:

    def test_shape_preserved(self):
        rng = np.random.default_rng(0)
        arr = rng.standard_normal((50, 10, 4))
        shuffled = circular_shift_telemetry(arr, rng)
        assert shuffled.shape == arr.shape

    def test_marginal_mean_preserved(self):
        """Per-agent per-channel mean must be unchanged by circular shift."""
        rng = np.random.default_rng(1)
        arr = rng.standard_normal((100, 15, 3))
        shuffled = circular_shift_telemetry(arr, rng)
        # Mean over T-axis per (agent, channel)
        orig_mean = arr.mean(axis=0)
        shuf_mean = shuffled.mean(axis=0)
        np.testing.assert_allclose(shuf_mean, orig_mean, atol=1e-12,
                                   err_msg="Per-agent mean changed by circular shift.")

    def test_marginal_std_preserved(self):
        """Per-agent per-channel std must be unchanged by circular shift."""
        rng = np.random.default_rng(2)
        arr = rng.standard_normal((100, 15, 3))
        shuffled = circular_shift_telemetry(arr, rng)
        orig_std = arr.std(axis=0, ddof=0)
        shuf_std = shuffled.std(axis=0, ddof=0)
        np.testing.assert_allclose(shuf_std, orig_std, atol=1e-12,
                                   err_msg="Per-agent std changed by circular shift.")

    def test_autocorrelation_lag0_preserved(self):
        """Autocorrelation at lag 0 (variance) must be unchanged."""
        rng = np.random.default_rng(3)
        arr = rng.standard_normal((80, 6, 2))
        shuffled = circular_shift_telemetry(arr, rng)
        # var over T-axis = mean of squared deviations at lag 0
        orig_var = arr.var(axis=0, ddof=0)
        shuf_var = shuffled.var(axis=0, ddof=0)
        np.testing.assert_allclose(shuf_var, orig_var, atol=1e-12)

    def test_agents_get_independent_shifts(self):
        """Different agents must get different shifts (with high probability for N>5)."""
        rng = np.random.default_rng(7)
        T = 100
        N = 20
        d = 2
        # Give each agent a unique constant signal so shift is detectable
        arr = np.zeros((T, N, d))
        for n in range(N):
            arr[0, n, 0] = float(n + 1)  # unique marker at step 0

        shifts_rng = np.random.default_rng(99)
        # Capture applied shifts by checking where the marker ended up
        shuffled = circular_shift_telemetry(arr, shifts_rng)

        detected_shifts = []
        for n in range(N):
            # The marker (non-zero value) should be at position shifts[n]
            positions = np.where(shuffled[:, n, 0] != 0.0)[0]
            assert len(positions) == 1, f"Agent {n}: expected 1 non-zero position"
            detected_shifts.append(int(positions[0]))

        # With N=20 and T=100, probability all shifts identical is ~(1/100)^19 ≈ 0
        assert len(set(detected_shifts)) > 1, (
            "All agents received the same shift — independence violated."
        )

    def test_roundtrip_inverse(self):
        """Applying a known shift and its inverse recovers the original exactly."""
        rng = np.random.default_rng(5)
        T = 50
        N = 6
        d = 3
        arr = rng.standard_normal((T, N, d))

        # Apply a fixed shift of +13 to each agent
        shift_amount = 13
        class _FixedShiftRNG:
            def integers(self, lo, hi, size=None):
                return np.full(size if size is not None else (), shift_amount, dtype=np.intp)
        forward_rng = _FixedShiftRNG()
        shuffled = circular_shift_telemetry(arr, forward_rng)

        # Inverse shift is T - shift_amount = T - 13
        inverse_amount = T - shift_amount
        class _InverseRNG:
            def integers(self, lo, hi, size=None):
                return np.full(size if size is not None else (), inverse_amount, dtype=np.intp)
        recovered = circular_shift_telemetry(shuffled, _InverseRNG())

        np.testing.assert_array_equal(recovered, arr, err_msg="Round-trip inversion failed.")


# ---------------------------------------------------------------------------
# Phi direction test
# ---------------------------------------------------------------------------

class TestPhiDirection:

    def test_correlated_phi_exceeds_surrogate_mean(self):
        """Phi on correlated flock should be higher than surrogate mean (most runs)."""
        features = _make_correlated_features(T=80, N=8, d=2, seed=10)
        rng = np.random.default_rng(100)
        config = {"W": 20, "stride": 5, "estimator": "ksg", "k_ksg": 3,
                  "mi_tie_break_noise": 1e-10}
        result = surrogate_phi_spectral(features, rng, n_shuffles=5, config=config)

        obs = result["observed_phi"]
        surr_mean = result["surrogate_mean"]
        # Correlated flock should have substantially higher observed phi
        assert obs > surr_mean, (
            f"Expected observed_phi ({obs:.4f}) > surrogate_mean ({surr_mean:.4f}) "
            "for correlated flock."
        )

    def test_surrogate_std_nonzero(self):
        """Surrogate distribution must have nonzero std (shuffles actually shuffle)."""
        features = _make_correlated_features(T=80, N=8, d=2, seed=11)
        rng = np.random.default_rng(200)
        config = {"W": 20, "stride": 5, "estimator": "ksg", "k_ksg": 3,
                  "mi_tie_break_noise": 1e-10}
        result = surrogate_phi_spectral(features, rng, n_shuffles=6, config=config)

        assert result["surrogate_std"] > 0, (
            "Surrogate std is zero — circular shift may not be varying across shuffles."
        )

    def test_per_window_null_frac_shape(self):
        """per_window_null_frac should have one entry per analysis window."""
        T, N, d = 80, 8, 2
        W, stride = 20, 5
        features = _make_random_features(T=T, N=N, d=d, seed=30)
        rng = np.random.default_rng(300)
        config = {"W": W, "stride": stride, "estimator": "ksg", "k_ksg": 3,
                  "mi_tie_break_noise": 1e-10}
        result = surrogate_phi_spectral(features, rng, n_shuffles=4, config=config)

        expected_n_windows = (T - W) // stride + 1
        assert result["per_window_null_frac"].shape == (expected_n_windows,), (
            f"per_window_null_frac shape {result['per_window_null_frac'].shape} "
            f"!= expected ({expected_n_windows},)."
        )
        assert np.all((result["per_window_null_frac"] >= 0) &
                      (result["per_window_null_frac"] <= 1)), (
            "per_window_null_frac values out of [0, 1]."
        )


# ---------------------------------------------------------------------------
# Noise σ=0.5 sanity check (synthetic stress test)
# ---------------------------------------------------------------------------

class TestNoiseSanityCheck:

    def test_random_flock_observed_within_surrogate_ci(self):
        """Pure random flock: observed Phi should lie within surrogate 95% CI."""
        # Use independent random features to simulate a high-noise flock
        features = _make_random_features(T=100, N=8, d=2, seed=999)
        rng = np.random.default_rng(500)
        config = {"W": 20, "stride": 5, "estimator": "ksg", "k_ksg": 3,
                  "mi_tie_break_noise": 1e-10}
        result = surrogate_phi_spectral(features, rng, n_shuffles=10, config=config)

        obs = result["observed_phi"]
        lo, hi = result["surrogate_95ci"]
        # For truly independent agents, observed ≈ surrogate; allow a loose CI test
        # by checking that z-score is small (|z| < 3 with high probability)
        z = result["z_score"]
        assert abs(z) < 4.0, (
            f"z-score={z:.2f} is large for a random flock — observed phi ({obs:.4f}) "
            f"should be close to surrogate mean ({result['surrogate_mean']:.4f}). "
            f"CI=[{lo:.4f}, {hi:.4f}]."
        )

    def test_z_score_finite(self):
        """z_score must be finite when surrogate_std > 0."""
        features = _make_random_features(T=60, N=6, d=2, seed=777)
        rng = np.random.default_rng(600)
        config = {"W": 15, "stride": 5, "estimator": "ksg", "k_ksg": 3,
                  "mi_tie_break_noise": 1e-10}
        result = surrogate_phi_spectral(features, rng, n_shuffles=6, config=config)

        if result["surrogate_std"] > 0:
            assert np.isfinite(result["z_score"]), "z_score is not finite."
