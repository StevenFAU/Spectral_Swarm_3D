"""Run aggregation and sweep result aggregation for 3D swarm analysis.

Phase 4 implementation target. See SpectralSwarm3DPhases.md §Phase 4 and D2.

Implements:
  - analyze_run: full per-step analysis for one telemetry CSV.
  - aggregate_steady_state: summarize the final third of windows per §3.8.
    Includes optional bootstrap CI computation (D2).
  - aggregate_event_phases: pre/during/post window aggregation for event scenarios.
  - time_to_coordination: steps to first sustained polarization >= 0.65 threshold.
  - aggregate_across_seeds: combine per-seed summaries into sweep-level stats.

Column schema includes all 2D columns plus 3D extensions:
  H2 TDA columns (snap_TP_2, snap_MP_2, snap_B_base_2, snap_B_prev_2,
                   traj_TP_2, traj_MP_2, traj_B_base_2, traj_B_prev_2)
  angular_momentum_norm (B5)
"""


def analyze_run(telemetry_path: str, config: dict):
    """Run full per-window analysis on one telemetry CSV. Phase 4.

    Parameters
    ----------
    telemetry_path : str
        Path to telemetry CSV.
    config : dict
        Analysis configuration (estimator, W, stride, feature_set, etc.).

    Returns
    -------
    pd.DataFrame
        One row per analysis window with all spectral, TDA, and classical metrics.
    """
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md")


def aggregate_steady_state(
    run_results,
    config: dict,
    bootstrap: bool = False,
    n_bootstrap: int = 1000,
) -> dict:
    """Aggregate steady-state (final third of windows) metrics. Phase 4.

    Parameters
    ----------
    run_results : pd.DataFrame
        Output of analyze_run.
    config : dict
    bootstrap : bool
        If True, compute 95% bootstrap CIs (D2).
    n_bootstrap : int
        Number of bootstrap resamples.

    Returns
    -------
    dict
        Mean (and optionally CI lo/hi) for each metric column.
    """
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md D2")


def aggregate_event_phases(run_results, config: dict) -> dict:
    """Aggregate pre/during/post event-phase windows (strict containment per §3.8). Phase 4."""
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md")


def time_to_coordination(
    run_results, threshold: float = 0.65, n_consecutive: int = 2
) -> int:
    """Steps to first sustained polarization >= threshold for n_consecutive windows. Phase 4."""
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md")


def aggregate_across_seeds(seed_summaries: list, config: dict):
    """Combine per-seed steady-state summaries into sweep-level stats. Phase 4."""
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md")
