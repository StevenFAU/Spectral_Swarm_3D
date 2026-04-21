"""Visualization functions for 3D swarm analysis output.

Phase 5 implementation target. See SpectralSwarm3DPhases.md §Phase 5 and C4.

Functions:
  - configure_style: set Matplotlib rcParams for publication figures.
  - plot_time_series: per-metric time series overlay (extended to H2 columns).
  - plot_snapshot_3d: static 3D scatter with optional Fiedler partition coloring (NEW).
  - animate_trajectory_3d: FuncAnimation MP4 output via ffmpeg writer (NEW).
  - plot_agreement_heatmap: Spearman correlation heatmap including H2 columns in _TDA_COMPARE.

Follows visual conventions of Topaz et al. (2015) and Bhaskar et al. (2019).
No print() in library code — functions return Figure/Axes or write to output_path.
"""


def configure_style() -> None:
    """Set Matplotlib rcParams for publication-quality figures. Phase 5."""
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C4")


def plot_time_series(
    run_results,
    metrics: list,
    output_path: str | None = None,
):
    """Plot metric time series for one run. Phase 5.

    Parameters
    ----------
    run_results : pd.DataFrame
        Output of analyze_run.
    metrics : list of str
        Column names to plot (supports H2 TDA columns).
    output_path : str or None
        If provided, save figure to this path.

    Returns
    -------
    matplotlib.figure.Figure
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C4")


def plot_snapshot_3d(
    positions,
    velocities=None,
    fiedler_partition=None,
    ax=None,
):
    """Render a 3D scatter of agent positions at one timestep (C4). Phase 5.

    Parameters
    ----------
    positions : np.ndarray, shape (N, 3)
    velocities : np.ndarray, shape (N, 3) or None
        If provided, draw velocity quivers.
    fiedler_partition : np.ndarray, shape (N,) or None
        Binary partition vector; if provided, color agents by partition.
    ax : mpl_toolkits.mplot3d.Axes3D or None
        Existing axes to plot into; creates new figure if None.

    Returns
    -------
    mpl_toolkits.mplot3d.Axes3D
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C4")


def animate_trajectory_3d(
    telemetry_csv: str,
    output_path: str,
    step_range: tuple | None = None,
    fps: int = 30,
) -> None:
    """Animate a 3D swarm trajectory as an MP4 (C4). Phase 5.

    Parameters
    ----------
    telemetry_csv : str
        Path to telemetry CSV.
    output_path : str
        Path for MP4 output (ffmpeg writer).
    step_range : (int, int) or None
        (start, end) step indices to render; None = full run.
    fps : int
        Frames per second (default 30).
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C4")


def plot_agreement_heatmap(
    comparison_df,
    output_path: str | None = None,
):
    """Plot Spearman correlation heatmap for spectral vs. TDA metrics. Phase 5.

    Returns
    -------
    matplotlib.figure.Figure
    """
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C4")
