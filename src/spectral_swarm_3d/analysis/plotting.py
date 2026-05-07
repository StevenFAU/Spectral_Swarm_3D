"""Phase 5 — Publication-quality figures for spectral vs topological comparison.

Ported from 2D Spectral_Swarm v0.1-2d-poc with H2 column extensions.

All plotting functions accept pre-computed DataFrames/Series from comparison.py
and save figures to a specified output directory in both PDF and PNG formats.
call configure_style() once before any plotting.

Functions implemented here (Tier 2.A scope):
  configure_style      -- set rcParams for publication figures
  plot_time_series     -- per-scenario time-series overlay (spectral/TDA/classical)
  plot_sensitivity_bars -- eta-squared bar chart per sweep
  plot_agreement_heatmap -- Spearman rho heatmap (H2 columns included)
  plot_control_deltas  -- matched-control delta grouped bar chart
  plot_monitoring_auc  -- ROC AUC bar chart for event detection

Phase 5 NEW functions (Tier 3.B/3.C — stubs until those sessions):
  plot_snapshot_3d          -- static 3D scatter with Fiedler partition colour
  animate_trajectory_3d     -- MP4 via ffmpeg writer
  plot_phi_distribution     -- per-window Phi distribution panel (D14)
  plot_compressibility_panel -- cross-sweep compressibility panel figure
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spectral_swarm_3d.analysis.comparison import (
    CLASSICAL_METRICS,
    SPECTRAL_METRICS,
    TDA_METRICS,
    _TDA_COMPARE,
)


# ---------------------------------------------------------------------------
# Consistent style
# ---------------------------------------------------------------------------

def configure_style() -> None:
    """Set matplotlib rcParams for publication-quality figures."""
    matplotlib.rcParams.update({
        "font.size": 12,
        "figure.figsize": (7, 4.5),
        "lines.linewidth": 1.5,
        "axes.grid": False,
        "axes.linewidth": 0.8,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
    })


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    """Save figure as both PDF and PNG."""
    name = name.replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.pdf")
    fig.savefig(out_dir / f"{name}.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Time-series overlay (per scenario)
# ---------------------------------------------------------------------------

def plot_time_series(
    mean_ts: pd.DataFrame,
    condition_label: str,
    out_dir: Path,
) -> None:
    """Three-panel time series: spectral, TDA (including H2), classical.

    Args:
        mean_ts: seed-averaged DataFrame indexed by window_idx.
        condition_label: used in title and filename.
        out_dir: output directory for figures.
    """
    fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True)

    steps = mean_ts.index.values

    ax = axes[0]
    for m in SPECTRAL_METRICS:
        if m in mean_ts.columns:
            ax.plot(steps, mean_ts[m], label=m)
    ax.set_ylabel("Spectral metrics")
    ax.set_title(f"Time series: {condition_label}")
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[1]
    # Show H0, H1, H2 TP for both snap and traj
    tda_plot = [
        "snap_TP_0", "snap_TP_1", "snap_TP_2",
        "traj_TP_0", "traj_TP_1", "traj_TP_2",
    ]
    for m in tda_plot:
        if m in mean_ts.columns:
            ax.plot(steps, mean_ts[m], label=m)
    ax.set_ylabel("TDA total persistence")
    ax.legend(loc="upper right", fontsize=8)

    ax = axes[2]
    for m in ["polarization", "milling_score", "angular_momentum_norm"]:
        if m in mean_ts.columns:
            ax.plot(steps, mean_ts[m], label=m)
    ax.set_ylabel("Classical baselines")
    ax.set_xlabel("Window index")
    ax.legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    _save(fig, out_dir, f"timeseries_{condition_label}")


# ---------------------------------------------------------------------------
# 2. Cross-condition sensitivity bar chart
# ---------------------------------------------------------------------------

def plot_sensitivity_bars(
    eta2: pd.Series,
    sweep_name: str,
    out_dir: Path,
    top_n: int = 15,
) -> None:
    """Horizontal bar chart of eta-squared values (top N metrics).

    Args:
        eta2: Series indexed by metric, values are eta-squared.
        sweep_name: sweep label for title/filename.
        out_dir: output directory.
        top_n: number of top metrics to show.
    """
    eta2_clean = eta2.dropna().head(top_n)
    if eta2_clean.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 0.4 * len(eta2_clean) + 1.5))
    y_pos = np.arange(len(eta2_clean))
    ax.barh(y_pos, eta2_clean.values, height=0.6, color="#4878CF")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(eta2_clean.index, fontsize=9)
    ax.set_xlabel(r"$\eta^2$ (variance explained)")
    ax.set_title(f"Cross-condition sensitivity: {sweep_name}")
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    fig.tight_layout()
    _save(fig, out_dir, f"sensitivity_{sweep_name}")


# ---------------------------------------------------------------------------
# 3. Agreement / divergence heatmap
# ---------------------------------------------------------------------------

def plot_agreement_heatmap(
    ad_matrix: pd.DataFrame,
    sweep_name: str,
    out_dir: Path,
) -> None:
    """Heatmap of Spearman rho between phi_spectral and TDA metrics (H2 included).

    Args:
        ad_matrix: DataFrame from agreement_divergence_matrix().
        sweep_name: for title/filename.
        out_dir: output directory.
    """
    tda_cols = [c for c in _TDA_COMPARE if c in ad_matrix.columns]
    if not tda_cols or ad_matrix.empty:
        return

    mat = ad_matrix.set_index("condition")[tda_cols].astype(float)

    fig, ax = plt.subplots(
        figsize=(max(7, 0.8 * len(tda_cols)), 0.5 * len(mat) + 2)
    )
    im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(tda_cols)))
    ax.set_xticklabels(
        [c.replace("snap_", "s.").replace("traj_", "t.") for c in tda_cols],
        rotation=45, ha="right", fontsize=8,
    )
    ax.set_yticks(range(len(mat)))
    ax.set_yticklabels(mat.index, fontsize=9)
    ax.set_title(
        f"Agreement/Divergence: {sweep_name}\n"
        f"(Spearman rho: phi_spectral vs TDA, H0–H2)"
    )
    fig.colorbar(im, ax=ax, shrink=0.8, label="Spearman rho")
    fig.tight_layout()
    _save(fig, out_dir, f"agreement_{sweep_name}")


# ---------------------------------------------------------------------------
# 4. Matched-control delta chart
# ---------------------------------------------------------------------------

def plot_control_deltas(
    deltas_df: pd.DataFrame,
    sweep_name: str,
    out_dir: Path,
    metrics: list[str] | None = None,
) -> None:
    """Grouped bar chart of perturbation-minus-control deltas.

    Args:
        deltas_df: DataFrame from matched_control_deltas().
        sweep_name: for title/filename.
        out_dir: output directory.
        metrics: subset of metrics to plot. Defaults to a curated 3D selection.
    """
    if deltas_df.empty:
        return

    if metrics is None:
        metrics = [
            "phi_spectral", "phi_norm",
            "snap_TP_0", "snap_TP_1", "snap_TP_2",
            "traj_TP_0", "traj_TP_1", "traj_TP_2",
            "polarization", "angular_momentum_norm",
        ]
    metrics = [m for m in metrics if m in deltas_df.columns]
    if not metrics:
        return

    conditions = deltas_df["condition"].values
    n_cond = len(conditions)
    n_met = len(metrics)
    x = np.arange(n_met)
    width = 0.8 / n_cond

    fig, ax = plt.subplots(figsize=(max(7, 0.7 * n_met + 1), 5))
    for i, cond in enumerate(conditions):
        row = deltas_df[deltas_df["condition"] == cond]
        vals = [float(row[m].iloc[0]) if m in row.columns else 0.0 for m in metrics]
        ax.bar(x + i * width, vals, width=width, label=cond)

    ax.set_xticks(x + width * (n_cond - 1) / 2)
    ax.set_xticklabels(metrics, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Delta (condition - control)")
    ax.set_title(f"Matched-control deltas: {sweep_name}")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save(fig, out_dir, f"deltas_{sweep_name}")


# ---------------------------------------------------------------------------
# 5. Monitoring ROC AUC bar chart
# ---------------------------------------------------------------------------

def plot_monitoring_auc(
    aucs: pd.Series,
    condition_label: str,
    out_dir: Path,
    top_n: int = 15,
) -> None:
    """Horizontal bar chart of ROC AUC for event detection.

    Args:
        aucs: Series from monitoring_roc().
        condition_label: for title/filename.
        out_dir: output directory.
        top_n: number of top metrics to show.
    """
    aucs_clean = aucs.dropna().head(top_n)
    if aucs_clean.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 0.4 * len(aucs_clean) + 1.5))
    y_pos = np.arange(len(aucs_clean))
    colors = [
        "#E24A33" if v >= 0.8 else "#348ABD" if v >= 0.65 else "#988ED5"
        for v in aucs_clean.values
    ]
    ax.barh(y_pos, aucs_clean.values, height=0.6, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(aucs_clean.index, fontsize=9)
    ax.set_xlabel("ROC AUC")
    ax.set_title(f"Monitoring benchmark: {condition_label}")
    ax.set_xlim(0.4, 1.0)
    ax.axvline(0.5, color="gray", linewidth=0.5, linestyle="--")
    ax.invert_yaxis()
    fig.tight_layout()
    _save(fig, out_dir, f"monitoring_{condition_label}")


# ---------------------------------------------------------------------------
# Phase 5 NEW functions — stubs for Tier 3.B / Tier 3.C sessions
# ---------------------------------------------------------------------------

def plot_snapshot_3d(
    positions: np.ndarray,
    velocities: np.ndarray | None = None,
    fiedler_partition: np.ndarray | None = None,
    ax=None,
):
    """Static 3D scatter of agent positions with optional Fiedler partition colour.

    Tier 3.B implementation target. See Phase5.md §Tier 3.A figure 8.
    """
    raise NotImplementedError("Phase 5 Tier 3.B — plot_snapshot_3d not yet implemented")


def animate_trajectory_3d(
    telemetry_csv: str,
    output_path: str,
    step_range: tuple | None = None,
    fps: int = 30,
) -> None:
    """Animate a 3D swarm trajectory as an MP4 (ffmpeg writer).

    Tier 3.B implementation target. See Phase5.md §Tier 3.B.
    """
    raise NotImplementedError("Phase 5 Tier 3.B — animate_trajectory_3d not yet implemented")


def plot_phi_distribution(
    phi_vals: np.ndarray,
    diag: dict,
    condition_label: str,
    out_dir: Path,
) -> None:
    """Per-window Phi distribution panel with bimodality annotation.

    Tier 3.A implementation target. See Phase5.md §Tier 3.A figure 1.
    """
    raise NotImplementedError("Phase 5 Tier 3.A — plot_phi_distribution not yet implemented")


def plot_compressibility_panel(
    results: dict,
    out_dir: Path,
) -> None:
    """Cross-sweep compressibility panel (primary publication figure).

    Tier 3.A implementation target. See Phase5.md §Tier 3.A figure 1.
    """
    raise NotImplementedError("Phase 5 Tier 3.A — plot_compressibility_panel not yet implemented")
