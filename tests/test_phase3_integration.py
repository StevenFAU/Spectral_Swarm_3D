"""Phase 3 end-to-end integration: run Phase 1 simulator, compute TDA summaries.

Bridges Phase 1's 3D boids telemetry to Phase 3's persistent-homology output.
Positive control: a milling scenario produces a velocity-projected toroidal/
spherical-shell structure (A3) whose H2 signature dominates the baseline's.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from spectral_swarm_3d.analysis.tda import (
    compute_persistence,
    persistence_summaries,
    snapshot_cloud,
)
from spectral_swarm_3d.model import BoidSwarmModel3D


def _run_and_extract_snapshot(
    cfg: dict, scenario_name: str, telemetry_path: Path, step: int, T: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """Run a simulation and return (positions, velocities) at the target step."""
    model = BoidSwarmModel3D(
        cfg, scenario_name=scenario_name, seed=0, telemetry_path=telemetry_path
    )
    model.run(T=T)
    df = pd.read_csv(telemetry_path)
    snap = df[df["step"] == step].sort_values("agent_id", kind="stable")
    positions = snap[["x", "y", "z"]].to_numpy(dtype=np.float64)
    velocities = snap[["vx", "vy", "vz"]].to_numpy(dtype=np.float64)
    return positions, velocities


def test_phase3_baseline_snapshot_produces_finite_summaries(config, tmp_path: Path):
    positions, _ = _run_and_extract_snapshot(
        config, "none", tmp_path / "baseline.csv", step=50, T=100
    )
    X = snapshot_cloud(positions, augmented=False)
    assert X.shape == (int(config["N"]), 3)

    dgms = compute_persistence(X, maxdim=int(config["tda_maxdim"]))
    assert len(dgms) == int(config["tda_maxdim"]) + 1

    summaries = persistence_summaries(dgms, maxdim=int(config["tda_maxdim"]))
    for k in range(int(config["tda_maxdim"]) + 1):
        assert np.isfinite(summaries[f"TP_{k}"])
        assert np.isfinite(summaries[f"MP_{k}"])
        # No baseline/prev provided -> bottleneck entries are NaN, not zero/error.
        assert np.isnan(summaries[f"B_base_{k}"])
        assert np.isnan(summaries[f"B_prev_{k}"])


def test_phase3_augmented_snapshot_has_six_dim_ambient(config, tmp_path: Path):
    positions, velocities = _run_and_extract_snapshot(
        config, "none", tmp_path / "baseline_aug.csv", step=50, T=100
    )
    X = snapshot_cloud(
        positions,
        augmented=True,
        velocities=velocities,
        beta=float(config["snapshot_beta"]),
    )
    assert X.shape == (int(config["N"]), 6)
    dgms = compute_persistence(X, maxdim=int(config["tda_maxdim"]))
    s = persistence_summaries(dgms, maxdim=int(config["tda_maxdim"]))
    assert np.isfinite(s["MP_2"])


@pytest.mark.xfail(
    reason=(
        "H2 milling-shell positive control requires denser sampling than "
        "methodology-spec N=40 at R=11. Neighbor spacing ~7.3 exceeds the "
        "R/3 ~3.7 threshold typically needed for reliable H2 void detection. "
        "Empirical at T=500, seed=0: baseline MP_2 ~0.18 (noise), milling "
        "MP_2 ~0.07. Diagnostic sweep over (N, embedding) pending — see "
        "docs/decisions/D9_h2_sampling_density.md. Resolution will pick one "
        "of: raise N project-wide, flip snapshot_augmented default to true "
        "for H2-dependent sweeps, or other. Do not relax this assertion "
        "until the decision is made and documented."
    ),
    strict=True,
)
def test_phase3_milling_mp2_exceeds_baseline_mp2(config, tmp_path: Path):
    """End-to-end positive control: milling's velocity-projected tangent (A3)
    yields a spherical-shell-like geometry whose H2 is stronger than the
    baseline's at the same step."""
    baseline_positions, _ = _run_and_extract_snapshot(
        config, "none", tmp_path / "base.csv", step=50, T=100
    )
    baseline_X = snapshot_cloud(baseline_positions)
    baseline_dgms = compute_persistence(baseline_X, maxdim=2)
    baseline_mp2 = persistence_summaries(baseline_dgms, maxdim=2)["MP_2"]

    milling_cfg = dict(config)
    milling_cfg["milling_mu"] = 0.8
    milling_positions, _ = _run_and_extract_snapshot(
        milling_cfg, "milling", tmp_path / "mill.csv", step=50, T=100
    )
    milling_X = snapshot_cloud(milling_positions)
    milling_dgms = compute_persistence(milling_X, maxdim=2)
    milling_mp2 = persistence_summaries(milling_dgms, maxdim=2)["MP_2"]

    assert milling_mp2 > baseline_mp2, (
        f"Expected milling MP_2 ({milling_mp2:.4f}) > baseline MP_2 "
        f"({baseline_mp2:.4f}) — 3D milling tangent should produce stronger H2."
    )


@pytest.mark.slow
def test_phase3_pipeline_under_300s_at_T500(config, tmp_path: Path):
    """Phase 3 pass/fail (SpectralSwarm3DPhases.md): a 500-step 3D milling run
    with per-step snapshot TDA completes in under 300 seconds."""
    milling_cfg = dict(config)
    milling_cfg["milling_mu"] = 0.8
    telemetry_path = tmp_path / "mill_long.csv"

    t0 = time.perf_counter()
    model = BoidSwarmModel3D(
        milling_cfg, scenario_name="milling", seed=0, telemetry_path=telemetry_path
    )
    model.run(T=500)
    df = pd.read_csv(telemetry_path)

    maxdim = int(milling_cfg["tda_maxdim"])
    for step in sorted(df["step"].unique()):
        snap = df[df["step"] == step].sort_values("agent_id", kind="stable")
        X = snapshot_cloud(snap[["x", "y", "z"]].to_numpy(dtype=np.float64))
        dgms = compute_persistence(X, maxdim=maxdim)
        persistence_summaries(dgms, maxdim=maxdim)

    elapsed = time.perf_counter() - t0
    assert elapsed < 300.0, f"Phase 3 pipeline took {elapsed:.1f}s (> 300s budget)."
