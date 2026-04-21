"""Phase 2 tests for feature extraction (B1)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from spectral_swarm_3d.analysis.features import extract_features


def _make_telemetry(T: int = 5, N: int = 4, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for t in range(T):
        for i in range(N):
            vx, vy, vz = rng.normal(size=3)
            speed = float(np.sqrt(vx * vx + vy * vy + vz * vz))
            ux, uy, uz = (vx / speed, vy / speed, vz / speed) if speed > 0 else (0.0, 0.0, 0.0)
            rows.append(
                {
                    "step": t,
                    "agent_id": i,
                    "x": float(rng.uniform(0, 50)),
                    "y": float(rng.uniform(0, 50)),
                    "z": float(rng.uniform(0, 50)),
                    "vx": float(vx),
                    "vy": float(vy),
                    "vz": float(vz),
                    "speed": speed,
                    "u_x": ux,
                    "u_y": uy,
                    "u_z": uz,
                }
            )
    return pd.DataFrame(rows)


def test_kinematic_shape_and_unit_vector_invariant():
    T, N = 5, 4
    df = _make_telemetry(T=T, N=N)
    X = extract_features(df, "kinematic")
    assert X.shape == (T, N, 4)
    norms = np.linalg.norm(X[..., 1:4], axis=-1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-10)


def test_vxvyvz_shape_and_values_match_raw_columns():
    T, N = 5, 4
    df = _make_telemetry(T=T, N=N)
    X = extract_features(df, "vxvyvz")
    assert X.shape == (T, N, 3)
    for _ in range(5):
        t = int(np.random.default_rng(1).integers(T))
        i = int(np.random.default_rng(2).integers(N))
        row = df[(df["step"] == t) & (df["agent_id"] == i)].iloc[0]
        np.testing.assert_allclose(X[t, i], [row.vx, row.vy, row.vz])


def test_full_shape():
    T, N = 3, 6
    df = _make_telemetry(T=T, N=N)
    X = extract_features(df, "full")
    assert X.shape == (T, N, 6)


def test_invalid_feature_set_raises():
    df = _make_telemetry(T=2, N=2)
    with pytest.raises(ValueError, match="Unknown feature_set"):
        extract_features(df, "banana")


def test_unsorted_input_is_handled():
    df = _make_telemetry(T=4, N=3)
    shuffled = df.sample(frac=1.0, random_state=0).reset_index(drop=True)
    X_sorted = extract_features(df, "vxvyvz")
    X_shuffled = extract_features(shuffled, "vxvyvz")
    np.testing.assert_allclose(X_sorted, X_shuffled)
