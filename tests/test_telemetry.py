"""Phase 1 tests for telemetry CSV and D6 metadata JSON."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from spectral_swarm_3d.model import BoidSwarmModel3D
from spectral_swarm_3d.telemetry import load_metadata


def _run(cfg: dict, tmp_path: Path, scenario: str = "none", seed: int = 0, T: int = 20):
    csv_path = tmp_path / f"{scenario}_{seed}.csv"
    m = BoidSwarmModel3D(cfg, scenario_name=scenario, seed=seed,
                         telemetry_path=csv_path)
    m.run(T=T)
    meta_path = tmp_path / f"{scenario}_{seed}.json"
    m.save_metadata(meta_path, repo_root=Path(__file__).parent.parent)
    return csv_path, meta_path, m


def test_telemetry_csv_rows_and_columns(config, tmp_path):
    T = 10
    csv_path, _meta, _m = _run(config, tmp_path, scenario="none", seed=0, T=T)
    df = pd.read_csv(csv_path)
    assert len(df) == int(config["N"]) * T
    required = {
        "step", "agent_id", "x", "y", "z", "vx", "vy", "vz", "speed",
        "u_x", "u_y", "u_z", "is_leader", "leader_group",
        "neighbor_count", "local_density", "scenario_label", "near_boundary",
    }
    assert required.issubset(df.columns)
    assert not df.isna().any().any()


def test_telemetry_unit_vector_invariant(config, tmp_path):
    csv_path, _m, _ = _run(config, tmp_path, scenario="leader", seed=1, T=20)
    df = pd.read_csv(csv_path)
    norms = df["u_x"] ** 2 + df["u_y"] ** 2 + df["u_z"] ** 2
    assert np.allclose(norms, 1.0, atol=1e-9)


def test_near_boundary_column_logged(config, tmp_path):
    csv_path, _m, _ = _run(config, tmp_path, scenario="none", seed=0, T=30)
    df = pd.read_csv(csv_path)
    assert df["near_boundary"].isin([0, 1]).all()
    # Fraction is computable from the full run.
    frac = df["near_boundary"].mean()
    assert 0.0 <= frac <= 1.0


def test_metadata_json_has_d6_fields(config, tmp_path):
    _csv, meta_path, _m = _run(config, tmp_path, scenario="milling", seed=3, T=5)
    payload = load_metadata(meta_path)
    assert "environment" in payload
    env = payload["environment"]
    for key in ("git_commit", "python_version", "package_versions",
                "hostname", "timestamp"):
        assert key in env
    assert "mesa" in env["package_versions"]
    assert payload["config"]["alignment_rule"] == "mean"
    assert payload["config"]["snapshot_augmented"] is False
    assert payload["scenario"] == "milling"
    assert payload["seed"] == 3


def test_metadata_roundtrip(config, tmp_path):
    _csv, meta_path, _m = _run(config, tmp_path, scenario="none", seed=7, T=5)
    # File must be valid JSON that survives a roundtrip.
    with open(meta_path) as f:
        raw = json.load(f)
    out = tmp_path / "roundtrip.json"
    with open(out, "w") as f:
        json.dump(raw, f)
    with open(out) as f:
        again = json.load(f)
    assert again == raw
