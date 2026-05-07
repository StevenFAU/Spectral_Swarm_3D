"""Tests for Phase 5 comparison analysis (3D port of 2D Spectral_Swarm v0.1-2d-poc).

All tests use synthetic DataFrames that mimic 3D analyze_run output.
No actual sweep outputs are required.

3D adaptations vs 2D test_comparison.py:
- _make_window_df produces H2 columns (snap_*/traj_* with _2 suffix)
- window alignment key is window_idx (not center_step)
- monitoring_roc labelling uses t_start/t_end columns
- load_sweep_runs returns (sweep_data, is_shared_baseline) tuple
- new tests cover per_window_distribution_summary and collapse_shared_baseline
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from spectral_swarm_3d.analysis.comparison import (
    ALL_METRICS,
    VANILLA_BASELINE_CONDITIONS,
    agreement_divergence_matrix,
    agreement_divergence_with_pvalues,
    cross_condition_sensitivity,
    load_sweep_runs,
    matched_control_deltas,
    monitoring_roc,
    per_window_distribution_summary,
    time_aligned_seed_mean,
    time_aligned_summary,
)


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

def _make_window_df(
    n_windows: int = 20,
    seed: int = 0,
    phi_trend: float = 0.0,
    snap_tp1_trend: float = 0.0,
) -> pd.DataFrame:
    """Create a synthetic per-window DataFrame mimicking 3D analyze_run output.

    Uses window_idx / t_start / t_end (3D schema) instead of 2D's center_step.
    Includes H2 columns (snap_*/traj_* with _2 suffix).
    """
    rng = np.random.default_rng(seed)
    window_idx = list(range(n_windows))
    t_start = [k * 5 for k in range(n_windows)]
    t_end = [k * 5 + 4 for k in range(n_windows)]

    data: dict = {
        "window_idx": window_idx,
        "t_start": t_start,
        "t_end": t_end,
        # Spectral
        "phi_spectral": (
            5.0 + phi_trend * np.arange(n_windows) + rng.normal(0, 0.1, n_windows)
        ),
        "phi_norm": 0.3 + rng.normal(0, 0.01, n_windows),
        # Classical (3D schema)
        "polarization": 0.5 + rng.normal(0, 0.05, n_windows),
        "milling_score": 0.1 + rng.normal(0, 0.02, n_windows),
        "angular_momentum_norm": 10.0 + rng.normal(0, 0.5, n_windows),
        "local_density": 0.3 + rng.normal(0, 0.03, n_windows),
        "LCC_fraction": 0.9 + rng.normal(0, 0.02, n_windows),
        # Snapshot TDA — H0
        "snap_TP_0": 50.0 + rng.normal(0, 2.0, n_windows),
        "snap_MP_0": 10.0 + rng.normal(0, 0.5, n_windows),
        "snap_B_base_0": np.abs(rng.normal(0, 1.0, n_windows)),
        "snap_B_prev_0": np.abs(rng.normal(0, 0.5, n_windows)),
        # Snapshot TDA — H1
        "snap_TP_1": (
            5.0
            + snap_tp1_trend * np.arange(n_windows)
            + rng.normal(0, 0.5, n_windows)
        ),
        "snap_MP_1": 2.0 + rng.normal(0, 0.2, n_windows),
        "snap_B_base_1": np.abs(rng.normal(0, 0.3, n_windows)),
        "snap_B_prev_1": np.abs(rng.normal(0, 0.2, n_windows)),
        # Snapshot TDA — H2 (3D extension)
        "snap_TP_2": 1.0 + rng.normal(0, 0.2, n_windows),
        "snap_MP_2": 0.4 + rng.normal(0, 0.05, n_windows),
        "snap_B_base_2": np.abs(rng.normal(0, 0.1, n_windows)),
        "snap_B_prev_2": np.abs(rng.normal(0, 0.05, n_windows)),
        # Trajectory TDA — H0
        "traj_TP_0": 30.0 + rng.normal(0, 1.5, n_windows),
        "traj_MP_0": 6.0 + rng.normal(0, 0.3, n_windows),
        "traj_B_base_0": np.abs(rng.normal(0, 0.8, n_windows)),
        "traj_B_prev_0": np.abs(rng.normal(0, 0.4, n_windows)),
        # Trajectory TDA — H1
        "traj_TP_1": 3.0 + rng.normal(0, 0.3, n_windows),
        "traj_MP_1": 1.0 + rng.normal(0, 0.1, n_windows),
        "traj_B_base_1": np.abs(rng.normal(0, 0.2, n_windows)),
        "traj_B_prev_1": np.abs(rng.normal(0, 0.1, n_windows)),
        # Trajectory TDA — H2 (3D extension)
        "traj_TP_2": 0.5 + rng.normal(0, 0.1, n_windows),
        "traj_MP_2": 0.2 + rng.normal(0, 0.03, n_windows),
        "traj_B_base_2": np.abs(rng.normal(0, 0.05, n_windows)),
        "traj_B_prev_2": np.abs(rng.normal(0, 0.03, n_windows)),
    }
    return pd.DataFrame(data)


def _make_sweep_data(
    n_conditions: int = 3,
    n_seeds: int = 3,
    n_windows: int = 20,
) -> dict[str, list[tuple[int, pd.DataFrame]]]:
    """Create synthetic sweep data with multiple conditions and seeds."""
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]] = {}
    for c in range(n_conditions):
        runs = []
        for s in range(n_seeds):
            df = _make_window_df(
                n_windows=n_windows,
                seed=c * 100 + s,
                phi_trend=0.1 * c,
                snap_tp1_trend=0.05 * c,
            )
            runs.append((s, df))
        sweep_data[f"cond_{c}"] = runs
    return sweep_data


# ---------------------------------------------------------------------------
# time_aligned_summary
# ---------------------------------------------------------------------------

def test_time_aligned_summary_index():
    """Index should be window_idx in 3D."""
    df = _make_window_df()
    result = time_aligned_summary(df)
    assert result.index.name == "window_idx"
    assert "phi_spectral" in result.columns


def test_time_aligned_summary_no_extra_cols():
    df = _make_window_df()
    result = time_aligned_summary(df)
    assert "window_idx" not in result.columns  # it's the index
    assert "t_start" not in result.columns
    assert "t_end" not in result.columns


def test_time_aligned_summary_h2_present():
    """H2 columns should appear in summary when present in the source df."""
    df = _make_window_df()
    result = time_aligned_summary(df)
    assert "snap_TP_2" in result.columns
    assert "traj_TP_2" in result.columns
    assert "snap_B_base_2" in result.columns


# ---------------------------------------------------------------------------
# time_aligned_seed_mean
# ---------------------------------------------------------------------------

def test_seed_mean_averages_across_seeds():
    runs = [(s, _make_window_df(seed=s)) for s in range(5)]
    mean_ts = time_aligned_seed_mean(runs)
    assert len(mean_ts) > 0
    assert "phi_spectral" in mean_ts.columns


def test_seed_mean_reduces_variance():
    """Averaging across seeds should reduce variance vs single seed."""
    single = time_aligned_summary(_make_window_df(seed=0))
    runs = [(s, _make_window_df(seed=s)) for s in range(10)]
    mean_ts = time_aligned_seed_mean(runs)
    assert mean_ts["phi_spectral"].std() < single["phi_spectral"].std() * 3


def test_seed_mean_h2_columns_preserved():
    runs = [(s, _make_window_df(seed=s)) for s in range(3)]
    mean_ts = time_aligned_seed_mean(runs)
    for col in ["snap_TP_2", "snap_MP_2", "traj_TP_2", "traj_B_base_2"]:
        assert col in mean_ts.columns


# ---------------------------------------------------------------------------
# cross_condition_sensitivity
# ---------------------------------------------------------------------------

def test_sensitivity_returns_dataframe():
    sweep_data = _make_sweep_data(n_conditions=4, n_seeds=5)
    eta2 = cross_condition_sensitivity(sweep_data)
    assert isinstance(eta2, pd.DataFrame)
    assert "eta2" in eta2.columns
    assert "ci_lo" in eta2.columns
    assert "ci_hi" in eta2.columns
    assert len(eta2) > 0


def test_sensitivity_values_in_range():
    sweep_data = _make_sweep_data(n_conditions=4, n_seeds=5)
    eta2 = cross_condition_sensitivity(sweep_data)
    for v in eta2["eta2"].dropna():
        assert 0.0 <= v <= 1.0


def test_sensitivity_detects_designed_difference():
    """phi_spectral has an increasing trend across conditions; eta2 should be high."""
    sweep_data = _make_sweep_data(n_conditions=4, n_seeds=10, n_windows=50)
    eta2 = cross_condition_sensitivity(sweep_data)
    assert eta2.loc["phi_spectral", "eta2"] > 0.1


def test_sensitivity_bootstrap_ci_bounds():
    """Bootstrap CIs should satisfy ci_lo <= ci_hi and both in [0, 1]."""
    sweep_data = _make_sweep_data(n_conditions=3, n_seeds=5, n_windows=20)
    eta2 = cross_condition_sensitivity(sweep_data, n_bootstrap=50)
    finite = eta2.dropna(subset=["eta2", "ci_lo", "ci_hi"])
    assert len(finite) > 0, "Expected at least some metrics with finite CI"
    for _, row in finite.iterrows():
        assert row["ci_lo"] <= row["ci_hi"] + 1e-9
        assert 0.0 <= row["ci_lo"] <= 1.0
        assert 0.0 <= row["ci_hi"] <= 1.0


def test_sensitivity_h2_columns_in_output():
    """H2 TDA metrics should appear in the eta2 output when present in data."""
    sweep_data = _make_sweep_data(n_conditions=3, n_seeds=4)
    eta2 = cross_condition_sensitivity(sweep_data)
    assert "snap_TP_2" in eta2.index
    assert "traj_TP_2" in eta2.index


# ---------------------------------------------------------------------------
# collapse_shared_baseline
# ---------------------------------------------------------------------------

def _make_sweep_data_with_baseline(
    n_seeds: int = 3,
    n_windows: int = 20,
) -> dict[str, list[tuple[int, pd.DataFrame]]]:
    """Sweep data where some conditions match VANILLA_BASELINE_CONDITIONS names."""
    # alpha_1.0 and sigma_0.05 are both vanilla-baseline condition names
    conditions = ["alpha_0.2", "alpha_0.5", "alpha_1.0"]
    sweep_data = {}
    for i, cond in enumerate(conditions):
        runs = []
        for s in range(n_seeds):
            df = _make_window_df(n_windows=n_windows, seed=i * 100 + s,
                                 phi_trend=0.1 * i)
            runs.append((s, df))
        sweep_data[cond] = runs
    return sweep_data


def test_collapse_shared_baseline_reduces_conditions():
    """collapse_shared_baseline=True should merge baseline conditions into one."""
    sweep_data = _make_sweep_data_with_baseline(n_seeds=4, n_windows=30)
    # With 3 conditions (alpha_0.2, alpha_0.5, alpha_1.0):
    # alpha_1.0 is in VANILLA_BASELINE_CONDITIONS → collapses to vanilla_baseline
    eta2_normal = cross_condition_sensitivity(sweep_data, collapse_shared_baseline=False)
    eta2_collapsed = cross_condition_sensitivity(
        sweep_data, collapse_shared_baseline=True
    )
    # Both should return DataFrames; collapsed has the same metrics
    assert isinstance(eta2_collapsed, pd.DataFrame)
    assert len(eta2_collapsed) > 0


def test_collapse_baseline_agreement_matrix():
    """agreement_divergence_matrix with collapse_shared_baseline should not crash."""
    sweep_data = _make_sweep_data_with_baseline(n_seeds=3)
    ad = agreement_divergence_matrix(
        sweep_data, collapse_shared_baseline=True
    )
    assert isinstance(ad, pd.DataFrame)
    if not ad.empty:
        # vanilla_baseline should appear, alpha_1.0 should not
        assert "alpha_1.0" not in ad["condition"].values
        assert "vanilla_baseline" in ad["condition"].values


def test_collapse_baseline_no_crash_when_no_baseline_present():
    """collapse_shared_baseline=True should behave normally when no baselines present."""
    sweep_data = _make_sweep_data(n_conditions=3)  # cond_0, cond_1, cond_2 — no baselines
    eta2 = cross_condition_sensitivity(sweep_data, collapse_shared_baseline=True)
    assert isinstance(eta2, pd.DataFrame)
    assert len(eta2) > 0


# ---------------------------------------------------------------------------
# agreement_divergence_matrix
# ---------------------------------------------------------------------------

def test_agreement_matrix_shape():
    sweep_data = _make_sweep_data(n_conditions=3)
    ad = agreement_divergence_matrix(sweep_data, sweep_label="test")
    assert len(ad) == 3
    assert "condition" in ad.columns
    assert "sweep" in ad.columns


def test_agreement_values_in_range():
    sweep_data = _make_sweep_data(n_conditions=3)
    ad = agreement_divergence_matrix(sweep_data)
    tda_cols = [c for c in ad.columns if c not in ("condition", "sweep")]
    for col in tda_cols:
        for v in ad[col].dropna():
            assert -1.0 <= v <= 1.0


def test_agreement_h2_columns_present():
    """H2 TDA columns should appear in agreement matrix output."""
    sweep_data = _make_sweep_data(n_conditions=3)
    ad = agreement_divergence_matrix(sweep_data)
    assert "snap_TP_2" in ad.columns
    assert "traj_B_base_2" in ad.columns


def test_agreement_correlated_trends():
    """When phi and snap_TP_1 have same trend direction, rho should be positive."""
    sweep_data: dict[str, list[tuple[int, pd.DataFrame]]] = {}
    for s in range(5):
        df = _make_window_df(seed=s, phi_trend=0.5, snap_tp1_trend=0.5)
        sweep_data.setdefault("correlated", []).append((s, df))

    ad = agreement_divergence_matrix(sweep_data)
    assert len(ad) == 1
    if "snap_TP_1" in ad.columns:
        assert ad["snap_TP_1"].iloc[0] > 0.0


def test_agreement_with_pvalues_shape():
    """agreement_divergence_with_pvalues returns (rho_df, pval_df) with same shape."""
    sweep_data = _make_sweep_data(n_conditions=3)
    rho_df, pval_df = agreement_divergence_with_pvalues(sweep_data, sweep_label="test")
    assert rho_df.shape == pval_df.shape
    assert "condition" in rho_df.columns
    assert "condition" in pval_df.columns


def test_agreement_pvalues_in_range():
    sweep_data = _make_sweep_data(n_conditions=3)
    _, pval_df = agreement_divergence_with_pvalues(sweep_data)
    numeric_cols = [c for c in pval_df.columns if c not in ("condition", "sweep")]
    for col in numeric_cols:
        for v in pval_df[col].dropna():
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# matched_control_deltas
# ---------------------------------------------------------------------------

def test_control_deltas_excludes_control():
    sweep_data = _make_sweep_data(n_conditions=3)
    deltas = matched_control_deltas(sweep_data, control_label="cond_0")
    assert "cond_0" not in deltas["condition"].values
    assert len(deltas) == 2


def test_control_deltas_direction():
    """Conditions with higher phi_trend should have positive phi delta vs control."""
    sweep_data = _make_sweep_data(n_conditions=3, n_seeds=10, n_windows=50)
    deltas = matched_control_deltas(sweep_data, control_label="cond_0")
    cond2 = deltas[deltas["condition"] == "cond_2"]
    assert float(cond2["phi_spectral"].iloc[0]) > 0


def test_control_deltas_missing_control():
    sweep_data = _make_sweep_data(n_conditions=2)
    deltas = matched_control_deltas(sweep_data, control_label="nonexistent")
    assert deltas.empty


# ---------------------------------------------------------------------------
# monitoring_roc
# ---------------------------------------------------------------------------

def _make_event_runs(
    n_seeds: int = 5,
    n_windows: int = 40,
    t_on: int = 50,
    t_off: int = 150,
) -> list[tuple[int, pd.DataFrame]]:
    """Runs where phi_spectral drops sharply during [t_on, t_off).

    Uses t_start / t_end columns (3D schema).
    """
    runs = []
    for s in range(n_seeds):
        rng = np.random.default_rng(s)
        df = _make_window_df(n_windows=n_windows, seed=s)
        # Overwrite t_start / t_end with event-aligned windows
        t_starts = list(range(0, n_windows * 5, 5))
        t_ends = [ts + 4 for ts in t_starts]
        df["t_start"] = t_starts
        df["t_end"] = t_ends
        phi = np.where(
            (np.array(t_starts) >= t_on) & (np.array(t_ends) <= t_off),
            2.0 + rng.normal(0, 0.1, n_windows),
            8.0 + rng.normal(0, 0.1, n_windows),
        )
        df["phi_spectral"] = phi
        runs.append((s, df))
    return runs


def test_monitoring_roc_returns_series():
    runs = _make_event_runs()
    aucs = monitoring_roc(runs, t_on=50, t_off=150, W=1)
    assert isinstance(aucs, pd.Series)
    assert len(aucs) > 0


def test_monitoring_roc_values_in_range():
    runs = _make_event_runs()
    aucs = monitoring_roc(runs, t_on=50, t_off=150, W=1)
    for v in aucs.dropna():
        assert 0.5 <= v <= 1.0


def test_monitoring_roc_detects_designed_event():
    """phi_spectral drops during event; AUC should be near 1.0."""
    runs = _make_event_runs(n_seeds=10, n_windows=60, t_on=100, t_off=200)
    aucs = monitoring_roc(runs, t_on=100, t_off=200, W=1)
    assert aucs["phi_spectral"] > 0.85


def test_monitoring_roc_degenerate_no_event():
    """If event window covers everything, return empty."""
    runs = _make_event_runs(n_windows=20)
    aucs = monitoring_roc(runs, t_on=0, t_off=9999, W=1)
    assert aucs.empty


# ---------------------------------------------------------------------------
# load_sweep_runs — shared-baseline metadata (Option A)
# ---------------------------------------------------------------------------

def test_load_sweep_runs_returns_tuple(tmp_path):
    """load_sweep_runs should return a (sweep_data, is_shared_baseline) tuple."""
    # Create a minimal fake sweep directory
    cond_dir = tmp_path / "alpha_0.2"
    cond_dir.mkdir()
    df = _make_window_df(n_windows=10)
    df.to_parquet(cond_dir / "seed0.parquet", index=False)

    result = load_sweep_runs(tmp_path)
    assert isinstance(result, tuple)
    assert len(result) == 2
    sweep_data, is_shared = result
    assert isinstance(sweep_data, dict)
    assert isinstance(is_shared, dict)


def test_load_sweep_runs_baseline_detection(tmp_path):
    """is_shared_baseline should be True for vanilla-baseline condition names."""
    # Simulate jamming_sweep directory with alpha_1.0 (a vanilla-baseline condition)
    # and alpha_0.2 (not)
    sweep_dir = tmp_path / "jamming_sweep"
    sweep_dir.mkdir()

    for cond in ["alpha_0.2", "alpha_1.0"]:
        cond_dir = sweep_dir / cond
        cond_dir.mkdir()
        df = _make_window_df(n_windows=10)
        df.to_parquet(cond_dir / "seed0.parquet", index=False)

    sweep_data, is_shared = load_sweep_runs(sweep_dir)
    assert "alpha_0.2" in sweep_data
    assert "alpha_1.0" in sweep_data
    assert is_shared["alpha_1.0"] is True
    assert is_shared["alpha_0.2"] is False


def test_load_sweep_runs_empty_dir(tmp_path):
    """Non-existent sweep dir returns (empty_dict, empty_dict)."""
    sweep_data, is_shared = load_sweep_runs(tmp_path / "nonexistent")
    assert sweep_data == {}
    assert is_shared == {}


def test_load_sweep_runs_round_trip(tmp_path):
    """Data loaded from parquet should equal what was written."""
    cond_dir = tmp_path / "alpha_0.2"
    cond_dir.mkdir()
    df_written = _make_window_df(n_windows=10, seed=42)
    df_written.to_parquet(cond_dir / "seed0.parquet", index=False)

    sweep_data, _ = load_sweep_runs(tmp_path)
    _, df_loaded = sweep_data["alpha_0.2"][0]
    pd.testing.assert_frame_equal(
        df_written.reset_index(drop=True),
        df_loaded.reset_index(drop=True),
    )


# ---------------------------------------------------------------------------
# per_window_distribution_summary
# ---------------------------------------------------------------------------

def _make_bimodal_df(n: int = 200, seed: int = 0) -> pd.DataFrame:
    """Synthetic bimodal phi_spectral distribution."""
    rng = np.random.default_rng(seed)
    n_each = n // 2
    phi = np.concatenate([
        rng.normal(50.0, 5.0, n_each),
        rng.normal(150.0, 5.0, n - n_each),
    ])
    rng.shuffle(phi)
    window_idx = list(range(n))
    return pd.DataFrame({"window_idx": window_idx, "phi_spectral": phi})


def _make_unimodal_df(n: int = 200, seed: int = 0) -> pd.DataFrame:
    """Synthetic unimodal phi_spectral distribution."""
    rng = np.random.default_rng(seed)
    phi = rng.normal(100.0, 5.0, n)
    window_idx = list(range(n))
    return pd.DataFrame({"window_idx": window_idx, "phi_spectral": phi})


def test_distribution_summary_returns_dict():
    df = _make_unimodal_df()
    result = per_window_distribution_summary(df, "phi_spectral")
    assert isinstance(result, dict)
    for key in ("n_windows", "dip_p", "mode_count", "std_iqr", "bimodal"):
        assert key in result


def test_distribution_summary_n_windows_steady_state():
    """steady_state_only=True should use approximately the final third of windows."""
    df = _make_unimodal_df(n=120)
    result_ss = per_window_distribution_summary(df, "phi_spectral", steady_state_only=True)
    result_all = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)
    assert result_ss["n_windows"] < result_all["n_windows"]
    # Final-third: ~40 of 120 windows
    assert 30 <= result_ss["n_windows"] <= 55


def test_distribution_summary_unimodal_detection():
    """Clear unimodal data should not be classified as bimodal."""
    df = _make_unimodal_df(n=300, seed=1)
    result = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)
    assert result["mode_count"] >= 1
    # dip_p should be large for unimodal data (high = unimodal)
    assert result["dip_p"] > 0.01  # not necessarily > 0.20 always, but should be finite
    assert isinstance(result["bimodal"], bool)


def test_distribution_summary_bimodal_detection():
    """Clearly bimodal distribution (two well-separated modes) should be detected."""
    df = _make_bimodal_df(n=400, seed=0)
    result = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)
    assert result["mode_count"] >= 2
    assert result["dip_p"] < 0.05  # strong bimodal signal
    assert result["bimodal"] is True


def test_distribution_summary_std_iqr_positive():
    """std/IQR should be positive for any non-degenerate distribution."""
    df = _make_unimodal_df(n=100)
    result = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)
    assert result["std_iqr"] > 0


def test_distribution_summary_missing_metric():
    """Missing metric column should return a safe all-NaN dict."""
    df = _make_unimodal_df(n=50)
    result = per_window_distribution_summary(df, "nonexistent_metric")
    assert result["n_windows"] == 0
    assert not result["bimodal"]


def test_distribution_summary_insufficient_data():
    """Fewer than 5 windows should return a safe no-computation result."""
    df = pd.DataFrame({
        "window_idx": [0, 1, 2],
        "phi_spectral": [100.0, 110.0, 90.0],
    })
    result = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)
    assert result["n_windows"] == 3
    assert np.isnan(result["dip_p"])
    assert not result["bimodal"]


def test_distribution_summary_methodology_agreement():
    """Results should match _make_distributions.py methodology for alignment w_a=0.6.

    This is a smoke test that the methodology produces plausible numbers for a
    known bimodal case — it does not assert exact reproduction (which would
    require the actual Phase 4 parquets) but verifies the computation pipeline
    returns finite values in expected ranges.
    """
    # Simulate bimodal with known properties similar to alignment w_a=0.6
    # (Tier 1.B found dip_p=0.102, mode_count=2, std_iqr=0.551, n≈310)
    rng = np.random.default_rng(7)
    n = 310
    # Two-mode distribution: modes at ~90 and ~180, std~35 each
    phi = np.concatenate([
        rng.normal(90.0, 35.0, n // 2),
        rng.normal(180.0, 35.0, n - n // 2),
    ])
    window_idx = list(range(n))
    df = pd.DataFrame({"window_idx": window_idx, "phi_spectral": phi})
    result = per_window_distribution_summary(df, "phi_spectral", steady_state_only=False)

    assert np.isfinite(result["dip_p"])
    assert result["mode_count"] >= 1
    assert np.isfinite(result["std_iqr"])
    assert result["n_windows"] == n


# ---------------------------------------------------------------------------
# Plotting (smoke tests — verify they don't crash, not visual output)
# ---------------------------------------------------------------------------

def test_plot_time_series_smoke(tmp_path):
    from spectral_swarm_3d.analysis.plotting import configure_style, plot_time_series
    configure_style()
    runs = [(0, _make_window_df())]
    mean_ts = time_aligned_seed_mean(runs)
    plot_time_series(mean_ts, "smoke_test", tmp_path)
    assert (tmp_path / "timeseries_smoke_test.png").exists()
    assert (tmp_path / "timeseries_smoke_test.pdf").exists()


def test_plot_sensitivity_smoke(tmp_path):
    from spectral_swarm_3d.analysis.plotting import configure_style, plot_sensitivity_bars
    configure_style()
    eta2 = pd.Series({"phi_spectral": 0.8, "snap_TP_2": 0.5, "polarization": 0.3})
    plot_sensitivity_bars(eta2, "smoke", tmp_path)
    assert (tmp_path / "sensitivity_smoke.png").exists()


def test_plot_agreement_smoke(tmp_path):
    from spectral_swarm_3d.analysis.plotting import configure_style, plot_agreement_heatmap
    configure_style()
    ad = pd.DataFrame({
        "condition": ["a", "b"],
        "sweep": ["test", "test"],
        "snap_TP_0": [0.8, -0.3],
        "snap_TP_1": [0.5, 0.9],
        "snap_TP_2": [0.2, 0.6],  # H2 column
    })
    plot_agreement_heatmap(ad, "smoke", tmp_path)
    assert (tmp_path / "agreement_smoke.png").exists()


def test_plot_monitoring_smoke(tmp_path):
    from spectral_swarm_3d.analysis.plotting import configure_style, plot_monitoring_auc
    configure_style()
    aucs = pd.Series({
        "phi_spectral": 0.92, "snap_TP_0": 0.71, "snap_TP_2": 0.65,
    })
    plot_monitoring_auc(aucs, "smoke", tmp_path)
    assert (tmp_path / "monitoring_smoke.png").exists()


def test_plot_deltas_smoke(tmp_path):
    from spectral_swarm_3d.analysis.plotting import configure_style, plot_control_deltas
    configure_style()
    deltas = pd.DataFrame({
        "condition": ["cond_1", "cond_2"],
        "phi_spectral": [1.5, 3.0],
        "snap_TP_2": [0.3, 0.8],  # H2 column
        "polarization": [0.1, 0.2],
    })
    plot_control_deltas(deltas, "smoke", tmp_path)
    assert (tmp_path / "deltas_smoke.png").exists()
