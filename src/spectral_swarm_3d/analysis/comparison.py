"""Cross-scenario and cross-metric comparison analysis for 3D swarm sweeps.

Phase 5 implementation target. See SpectralSwarm3DPhases.md §Phase 5, C2.

Extends 2D comparison.py with H2 TDA columns in _TDA_COMPARE and
angular_momentum_norm in _CLASSICAL column list.

Column schema additions (C2):
  _TDA_COMPARE gains: snap_TP_2, snap_MP_2, snap_B_base_2, traj_TP_2, traj_MP_2, traj_B_base_2
"""

# Spectral columns (unchanged from 2D)
_SPECTRAL = [
    "phi_spectral",
    "phi_norm",
    "fiedler_gap",
    "total_mi",
]

# TDA columns — 3D extends to H2 (C2)
_TDA = [
    "snap_TP_0", "snap_TP_1", "snap_TP_2",
    "snap_MP_0", "snap_MP_1", "snap_MP_2",
    "traj_TP_0", "traj_TP_1", "traj_TP_2",
    "traj_MP_0", "traj_MP_1", "traj_MP_2",
]

# TDA columns used in agreement/divergence heatmaps (C2 extended)
_TDA_COMPARE = [
    "snap_TP_0", "snap_TP_1", "snap_TP_2",
    "snap_MP_0", "snap_MP_1", "snap_MP_2",
    "snap_B_base_0", "snap_B_base_1", "snap_B_base_2",
    "traj_TP_0", "traj_TP_1", "traj_TP_2",
    "traj_MP_0", "traj_MP_1", "traj_MP_2",
    "traj_B_base_0", "traj_B_base_1", "traj_B_base_2",
]

# Classical columns — 3D adds angular_momentum_norm (B5)
_CLASSICAL = [
    "polarization",
    "milling_score",
    "angular_momentum_norm",
    "mean_nn_dist",
    "flock_radius",
]


def eta_squared_table(sweep_results, columns: list):
    """Compute eta^2 effect sizes for each metric column across sweep conditions. Phase 5."""
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C2")


def agreement_heatmap_data(sweep_results):
    """Compute pairwise Spearman correlation between spectral and TDA metric rankings. Phase 5."""
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C2")


def run_comparison(sweep_dir: str, config: dict):
    """Load all sweep Parquet files and produce the full comparison table. Phase 5."""
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md C2")
