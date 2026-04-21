"""Phase 4 tests for analysis/aggregation.py.

Covers:
- analyze_run: column schema (C2), H2 columns, angular_momentum_norm
- aggregate_steady_state: bootstrap CI structure, degenerate case
- aggregate_event_phases: phase window assignment (strict containment)
- time_to_coordination: scan logic
- aggregate_across_seeds: cross-seed mean/std
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from spectral_swarm_3d.analysis.aggregation import (
    aggregate_across_seeds,
    aggregate_event_phases,
    aggregate_steady_state,
    analyze_run,
    time_to_coordination,
)
from spectral_swarm_3d.model import BoidSwarmModel3D


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def small_cfg(config):
    """Minimal config for fast test runs: short T, small W, coarse stride."""
    cfg = dict(config)
    cfg["W"] = 10
    cfg["stride"] = 10
    cfg["tda_maxdim"] = 2
    cfg["estimator"] = "ksg"
    cfg["feature_set"] = "kinematic"
    return cfg


@pytest.fixture
def run_results_df(small_cfg, tmp_path: Path):
    """Produce a real analyze_run output on a short baseline simulation."""
    tel_path = tmp_path / "tel.csv"
    model = BoidSwarmModel3D(small_cfg, scenario_name="none", seed=0, telemetry_path=tel_path)
    model.run(T=80)
    return analyze_run(str(tel_path), small_cfg)


@pytest.fixture
def synthetic_df():
    """Purely synthetic run_results DataFrame for fast aggregation tests."""
    rng = np.random.default_rng(42)
    n = 30
    return pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n) * 5,
            "t_end": np.arange(n) * 5 + 9,
            "phi_spectral": rng.uniform(50.0, 200.0, n),
            "phi_norm": rng.uniform(0.1, 0.5, n),
            "polarization": rng.uniform(0.3, 0.9, n),
            "milling_score": rng.uniform(0.4, 0.9, n),
            "angular_momentum_norm": rng.uniform(5.0, 25.0, n),
            "local_density": rng.uniform(0.01, 0.1, n),
            "LCC_fraction": rng.uniform(0.5, 1.0, n),
            "snap_TP_0": rng.uniform(80.0, 130.0, n),
            "snap_MP_0": rng.uniform(5.0, 15.0, n),
            "snap_B_base_0": rng.uniform(0.0, 20.0, n),
            "snap_B_prev_0": rng.uniform(0.0, 5.0, n),
            "snap_TP_1": rng.uniform(0.5, 3.0, n),
            "snap_MP_1": rng.uniform(0.1, 1.0, n),
            "snap_B_base_1": rng.uniform(0.0, 1.0, n),
            "snap_B_prev_1": rng.uniform(0.0, 0.5, n),
            "snap_TP_2": rng.uniform(0.0, 1.0, n),
            "snap_MP_2": rng.uniform(0.0, 0.5, n),
            "snap_B_base_2": rng.uniform(0.0, 0.5, n),
            "snap_B_prev_2": rng.uniform(0.0, 0.2, n),
            "traj_TP_0": rng.uniform(0.0, 50.0, n),
            "traj_MP_0": rng.uniform(0.0, 5.0, n),
            "traj_B_base_0": rng.uniform(0.0, 10.0, n),
            "traj_B_prev_0": rng.uniform(0.0, 3.0, n),
            "traj_TP_1": rng.uniform(0.5, 4.0, n),
            "traj_MP_1": rng.uniform(0.1, 1.5, n),
            "traj_B_base_1": rng.uniform(0.0, 1.0, n),
            "traj_B_prev_1": rng.uniform(0.0, 0.5, n),
            "traj_TP_2": rng.uniform(0.0, 1.0, n),
            "traj_MP_2": rng.uniform(0.0, 0.5, n),
            "traj_B_base_2": rng.uniform(0.0, 0.3, n),
            "traj_B_prev_2": rng.uniform(0.0, 0.2, n),
        }
    )


# ---------------------------------------------------------------------------
# analyze_run — column schema and shapes
# ---------------------------------------------------------------------------


_EXPECTED_METRIC_COLS = [
    "phi_spectral", "phi_norm",
    "polarization", "milling_score", "angular_momentum_norm",
    "local_density", "LCC_fraction",
    # snapshot TDA k=0,1,2
    "snap_TP_0", "snap_MP_0", "snap_B_base_0", "snap_B_prev_0",
    "snap_TP_1", "snap_MP_1", "snap_B_base_1", "snap_B_prev_1",
    "snap_TP_2", "snap_MP_2", "snap_B_base_2", "snap_B_prev_2",
    # trajectory TDA k=0,1,2
    "traj_TP_0", "traj_MP_0", "traj_B_base_0", "traj_B_prev_0",
    "traj_TP_1", "traj_MP_1", "traj_B_base_1", "traj_B_prev_1",
    "traj_TP_2", "traj_MP_2", "traj_B_base_2", "traj_B_prev_2",
]


def test_analyze_run_window_count(run_results_df, small_cfg):
    T, W, S = 80, small_cfg["W"], small_cfg["stride"]
    expected = (T - W) // S + 1
    assert len(run_results_df) == expected


def test_analyze_run_required_columns_present(run_results_df):
    for col in _EXPECTED_METRIC_COLS + ["window_idx", "t_start", "t_end"]:
        assert col in run_results_df.columns, f"Missing column: {col}"


def test_analyze_run_h2_columns_present(run_results_df):
    """H2 columns (snap_TP_2, traj_TP_2, …) are in the schema per C2."""
    for prefix in ("snap", "traj"):
        for suffix in ("TP_2", "MP_2", "B_base_2", "B_prev_2"):
            assert f"{prefix}_{suffix}" in run_results_df.columns


def test_analyze_run_angular_momentum_norm_finite(run_results_df):
    """angular_momentum_norm is present and finite in every row."""
    assert "angular_momentum_norm" in run_results_df.columns
    assert np.all(np.isfinite(run_results_df["angular_momentum_norm"].to_numpy()))


def test_analyze_run_spectral_cols_finite_nonneg(run_results_df):
    assert np.all(np.isfinite(run_results_df["phi_spectral"]))
    assert np.all(run_results_df["phi_spectral"] >= -1e-10)
    assert np.all(np.isfinite(run_results_df["phi_norm"]))
    assert np.all(run_results_df["phi_norm"] >= -1e-10)


def test_analyze_run_classical_cols_in_range(run_results_df):
    assert run_results_df["polarization"].between(0.0, 1.0 + 1e-9).all()
    assert run_results_df["milling_score"].between(0.0, 1.0 + 1e-9).all()
    assert (run_results_df["LCC_fraction"] > 0.0).all()
    assert (run_results_df["LCC_fraction"] <= 1.0 + 1e-9).all()


def test_analyze_run_t_start_monotone(run_results_df):
    t_starts = run_results_df["t_start"].to_numpy()
    assert np.all(t_starts[1:] >= t_starts[:-1])


def test_analyze_run_snap_b_base_nan_for_first_window(run_results_df):
    """First window has no baseline reference → B_base is NaN."""
    first_row = run_results_df.iloc[0]
    for k in range(3):
        assert np.isnan(first_row[f"snap_B_base_{k}"]), f"snap_B_base_{k} should be NaN at row 0"
        assert np.isnan(first_row[f"traj_B_base_{k}"]), f"traj_B_base_{k} should be NaN at row 0"


def test_analyze_run_snap_b_base_finite_after_first(run_results_df):
    """Later windows have finite B_base (baseline diagram is set)."""
    if len(run_results_df) < 2:
        pytest.skip("Need at least 2 windows")
    row1 = run_results_df.iloc[1]
    for k in range(3):
        assert np.isfinite(row1[f"snap_B_base_{k}"]) or np.isnan(row1[f"snap_B_base_{k}"])


def test_analyze_run_snap_tp_nonneg(run_results_df):
    for k in range(3):
        col = f"snap_TP_{k}"
        assert (run_results_df[col] >= -1e-9).all(), f"{col} has negative values"


# ---------------------------------------------------------------------------
# aggregate_steady_state — bootstrap CI structure
# ---------------------------------------------------------------------------


def test_aggregate_steady_state_bootstrap_keys(synthetic_df, small_cfg):
    result = aggregate_steady_state(synthetic_df, small_cfg, bootstrap_ci=True, n_bootstrap=100)
    assert set(result.keys()) == {"mean", "ci_lo", "ci_hi"}
    assert "phi_spectral" in result["mean"]
    assert "phi_spectral" in result["ci_lo"]
    assert "phi_spectral" in result["ci_hi"]


def test_aggregate_steady_state_ci_ordering(synthetic_df, small_cfg):
    """ci_lo ≤ mean ≤ ci_hi for every metric column."""
    result = aggregate_steady_state(synthetic_df, small_cfg, bootstrap_ci=True, n_bootstrap=200)
    for col in result["mean"]:
        lo = result["ci_lo"][col]
        mu = result["mean"][col]
        hi = result["ci_hi"][col]
        assert lo <= mu + 1e-10, f"{col}: ci_lo ({lo}) > mean ({mu})"
        assert mu <= hi + 1e-10, f"{col}: mean ({mu}) > ci_hi ({hi})"


def test_aggregate_steady_state_degenerate_bootstrap(small_cfg):
    """Degenerate windows (all identical values) → ci_lo == ci_hi == mean."""
    n = 30
    df = pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n),
            "t_end": np.arange(n) + 9,
            "phi_spectral": np.full(n, 42.0),
            "polarization": np.full(n, 0.75),
        }
    )
    result = aggregate_steady_state(df, small_cfg, bootstrap_ci=True, n_bootstrap=200)
    for col in ("phi_spectral", "polarization"):
        assert abs(result["ci_lo"][col] - 42.0) < 1e-9 or col == "polarization"
        assert abs(result["mean"][col] - result["ci_lo"][col]) < 1e-9
        assert abs(result["mean"][col] - result["ci_hi"][col]) < 1e-9


def test_aggregate_steady_state_no_bootstrap_backward_compat(synthetic_df, small_cfg):
    """bootstrap_ci=False returns flat {col: val} dict, not nested."""
    result = aggregate_steady_state(synthetic_df, small_cfg, bootstrap_ci=False)
    assert "mean" not in result
    assert "phi_spectral" in result
    assert isinstance(result["phi_spectral"], float)


def test_aggregate_steady_state_uses_final_third(small_cfg):
    """Steady-state mean is drawn from the final third, not all windows."""
    n = 30
    early_val, late_val = 10.0, 100.0
    df = pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n),
            "t_end": np.arange(n) + 9,
            "phi_spectral": np.array([early_val] * 20 + [late_val] * 10),
        }
    )
    result = aggregate_steady_state(df, small_cfg, bootstrap_ci=False)
    # Final third is last 10 rows → mean should be late_val
    assert abs(result["phi_spectral"] - late_val) < 1e-9


# ---------------------------------------------------------------------------
# aggregate_event_phases
# ---------------------------------------------------------------------------


def _make_phase_df(n: int = 60):
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n) * 5,
            "t_end": np.arange(n) * 5 + 9,
            "phi_spectral": rng.uniform(50.0, 200.0, n),
            "polarization": rng.uniform(0.3, 0.9, n),
        }
    )


def test_event_phases_jamming_non_none(small_cfg):
    cfg = {**small_cfg, "scenario": "jamming", "jam_t_on": 100, "jam_t_off": 200}
    df = _make_phase_df()
    phases = aggregate_event_phases(df, cfg, bootstrap_ci=False)
    assert "pre" in phases and "during" in phases and "post" in phases
    assert phases["pre"] is not None
    assert phases["during"] is not None


def test_event_phases_no_event_scenario(small_cfg):
    cfg = {**small_cfg, "scenario": "none"}
    df = _make_phase_df()
    phases = aggregate_event_phases(df, cfg, bootstrap_ci=False)
    assert phases["pre"] is None
    assert phases["during"] is None
    assert phases["post"] is None


def test_event_phases_strict_containment(small_cfg):
    """Windows that straddle a phase boundary are excluded."""
    # t_start=0..295 (step=5*k), t_end = t_start+9
    # jam_t_on=50: pre windows have t_end < 50 → t_end = 5k+9 < 50 → k < 8.2 → k ≤ 8
    # during: t_start >= 50 and t_end <= 100 → 5k >= 50 and 5k+9 <= 100 → k∈{10..18}
    cfg = {**small_cfg, "scenario": "jamming", "jam_t_on": 50, "jam_t_off": 100}
    df = _make_phase_df(n=60)
    phases = aggregate_event_phases(df, cfg, bootstrap_ci=False)

    # Verify pre phase ends before t_on
    if phases["pre"] is not None:
        pre_rows = df[df["t_end"] < 50]
        assert len(pre_rows) > 0

    # Verify during phase is fully within [50, 100]
    during_rows = df[(df["t_start"] >= 50) & (df["t_end"] <= 100)]
    if len(during_rows) == 0:
        assert phases["during"] is None
    else:
        assert phases["during"] is not None


def test_event_phases_bootstrap_ci_structure(small_cfg):
    cfg = {**small_cfg, "scenario": "jamming", "jam_t_on": 30, "jam_t_off": 120}
    df = _make_phase_df()
    phases = aggregate_event_phases(df, cfg, bootstrap_ci=True, n_bootstrap=50)
    for phase_name in ("pre", "during", "post"):
        p = phases[phase_name]
        if p is not None:
            assert set(p.keys()) == {"mean", "ci_lo", "ci_hi"}


# ---------------------------------------------------------------------------
# time_to_coordination
# ---------------------------------------------------------------------------


def test_ttc_found(small_cfg):
    n = 20
    pol = [0.3] * 5 + [0.7, 0.8, 0.75] + [0.5] * 12
    df = pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n) * 5,
            "t_end": np.arange(n) * 5 + 4,
            "polarization": pol,
        }
    )
    result = time_to_coordination(df, threshold=0.65, n_consecutive=2)
    assert result == 25  # first window with sustained pol >= 0.65 starts at t=5*5=25


def test_ttc_not_found():
    n = 10
    df = pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n) * 5,
            "t_end": np.arange(n) * 5 + 4,
            "polarization": np.full(n, 0.5),
        }
    )
    assert time_to_coordination(df, threshold=0.65, n_consecutive=2) == -1


def test_ttc_requires_consecutive():
    """A single above-threshold window followed by a dip does not qualify."""
    n = 10
    pol = [0.3, 0.3, 0.7, 0.3, 0.7, 0.7, 0.3, 0.3, 0.3, 0.3]
    df = pd.DataFrame(
        {
            "window_idx": np.arange(n),
            "t_start": np.arange(n) * 5,
            "t_end": np.arange(n) * 5 + 4,
            "polarization": pol,
        }
    )
    # n_consecutive=2: first valid pair is indices 4+5 → t_start = 4*5 = 20
    assert time_to_coordination(df, threshold=0.65, n_consecutive=2) == 20


# ---------------------------------------------------------------------------
# aggregate_across_seeds
# ---------------------------------------------------------------------------


def test_aggregate_across_seeds_mean_std(small_cfg):
    summaries = [
        {"phi_spectral": 100.0, "polarization": 0.7},
        {"phi_spectral": 120.0, "polarization": 0.8},
        {"phi_spectral": 110.0, "polarization": 0.75},
    ]
    result = aggregate_across_seeds(summaries, small_cfg)
    assert abs(result["phi_spectral"]["mean"] - 110.0) < 1e-9
    assert abs(result["polarization"]["mean"] - 0.75) < 1e-9
    assert result["phi_spectral"]["n"] == 3


def test_aggregate_across_seeds_bootstrap_format(small_cfg, synthetic_df):
    """aggregate_across_seeds handles bootstrap-format summaries."""
    s1 = aggregate_steady_state(synthetic_df, small_cfg, bootstrap_ci=True, n_bootstrap=50)
    s2 = aggregate_steady_state(synthetic_df, small_cfg, bootstrap_ci=True, n_bootstrap=50)
    result = aggregate_across_seeds([s1, s2], small_cfg)
    assert "phi_spectral" in result
    assert result["phi_spectral"]["n"] == 2


def test_aggregate_across_seeds_single_seed(small_cfg):
    summaries = [{"phi_spectral": 99.0}]
    result = aggregate_across_seeds(summaries, small_cfg)
    assert result["phi_spectral"]["mean"] == 99.0
    assert result["phi_spectral"]["n"] == 1
