"""Feature extraction for 3D swarm telemetry.

Implements B1 (Phase 2). Three feature sets:

  - ``kinematic`` (d=4): (speed, u_x, u_y, u_z) — unit-velocity encoding avoids
    pole singularities (direct 3D analog of 2D's (speed, sin_theta, cos_theta)).
    Uses the already-logged telemetry columns; does not recompute.
  - ``vxvyvz`` (d=3): raw velocity components.
  - ``full`` (d=6): (x, y, z, vx, vy, vz).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_FEATURE_COLUMNS: dict[str, tuple[str, ...]] = {
    "kinematic": ("speed", "u_x", "u_y", "u_z"),
    "vxvyvz": ("vx", "vy", "vz"),
    "full": ("x", "y", "z", "vx", "vy", "vz"),
}


def extract_features(telemetry_df: pd.DataFrame, feature_set: str) -> np.ndarray:
    """Extract a ``(T, N, d)`` feature array from telemetry. Implements B1.

    Parameters
    ----------
    telemetry_df : pd.DataFrame
        Per-step telemetry with columns ``step``, ``agent_id`` plus columns
        required by the selected feature set.
    feature_set : str
        One of ``"kinematic"``, ``"vxvyvz"``, ``"full"``.

    Returns
    -------
    np.ndarray
        Shape ``(T, N, d)`` where ``T`` = number of steps, ``N`` = number of
        agents, ``d`` depends on ``feature_set``.
    """
    if feature_set not in _FEATURE_COLUMNS:
        raise ValueError(
            f"Unknown feature_set {feature_set!r}; "
            f"expected one of {sorted(_FEATURE_COLUMNS)}."
        )
    cols = _FEATURE_COLUMNS[feature_set]

    df = telemetry_df.sort_values(["step", "agent_id"], kind="stable")
    T = df["step"].nunique()
    N = df["agent_id"].nunique()
    d = len(cols)

    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Telemetry missing columns for {feature_set!r}: {missing}")

    arr = df[list(cols)].to_numpy(dtype=np.float64, copy=True)
    if arr.shape[0] != T * N:
        raise ValueError(
            f"Telemetry rows ({arr.shape[0]}) do not match T*N = {T * N}; "
            "expected a complete rectangular (step, agent_id) grid."
        )
    return arr.reshape(T, N, d)
