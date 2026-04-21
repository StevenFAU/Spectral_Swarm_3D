"""Feature extraction for 3D swarm telemetry.

Phase 2 implementation target. See SpectralSwarm3DPhases.md §Phase 2 and B1.

Feature sets:
  - kinematic (d=4): (speed, u_x, u_y, u_z) — unit-velocity encoding avoids
    pole singularities (direct 3D analog of 2D's (speed, sin_theta, cos_theta)).
  - vxvyvz (d=3): raw velocity components.
  - full (d=6): (x, y, z, vx, vy, vz) — extension of 2D's (x, y, vx, vy) set.

B2: primary W=40 at d=4; W=50 recommended for d=6 (larger joint covariance).
"""


def extract_features(telemetry, feature_set: str, W: int, stride: int = 1):
    """Extract sliding windows of agent features from telemetry. Phase 2.

    Parameters
    ----------
    telemetry : pd.DataFrame
        Telemetry CSV loaded as a DataFrame.
    feature_set : str
        One of 'kinematic', 'vxvyvz', 'full'.
    W : int
        Window length in timesteps.
    stride : int
        Stride between successive windows.

    Returns
    -------
    list of np.ndarray
        Each element is shape (N, W, d) for one window.
    """
    raise NotImplementedError("Phase 2 — see SpectralSwarm3DPhases.md B1")
