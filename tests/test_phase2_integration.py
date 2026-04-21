"""Phase 2 end-to-end integration: run a short baseline, compute Φ_spectral.

Runs a 100-step baseline scenario at seed 0 using the Phase 1 simulator,
loads telemetry, extracts kinematic features, and computes Φ_spectral over
sliding windows with the KSG estimator per methodology defaults.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from spectral_swarm_3d.analysis.features import extract_features
from spectral_swarm_3d.analysis.spectral import phi_spectral_over_windows
from spectral_swarm_3d.model import BoidSwarmModel3D


def test_phase2_integration_baseline(config, tmp_path: Path):
    telemetry_path = tmp_path / "telemetry.csv"
    m = BoidSwarmModel3D(
        config, scenario_name="none", seed=0, telemetry_path=telemetry_path
    )
    m.run(T=100)

    df = pd.read_csv(telemetry_path)
    features = extract_features(df, feature_set="kinematic")
    assert features.shape == (100, int(config["N"]), 4)

    phi = phi_spectral_over_windows(
        features,
        W=int(config["W"]),
        stride=int(config["stride"]),
        estimator="ksg",
        k=int(config["k_ksg"]),
        noise_eps=float(config["mi_tie_break_noise"]),
    )

    expected_len = (100 - int(config["W"])) // int(config["stride"]) + 1
    assert phi.shape == (expected_len,)
    assert np.all(np.isfinite(phi))
    assert np.all(phi >= -1e-10)
    assert phi.std() > 0.0
    assert (phi == 0).sum() == 0, (
        "Fiedler partition produced a zero-MI cut; indicates a degenerate window"
    )
