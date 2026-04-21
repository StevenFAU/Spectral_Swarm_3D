"""Phase 3.5 H1 scenario-specificity probe.

Answers the open question from D9: is the H1-on-trajectory-clouds variance
issue observed on milling-vs-baseline *milling-specific*, or does it generalise
to other coordination contrasts?

Runs 9 simulations (3 scenarios × 3 seeds), computes per-window metrics
through the existing Phase 1–3 modules, writes Parquet + companion metadata
JSON (D6) for each run, then builds a summary CSV over steady-state windows
(final third, per §3.8) and prints it to stdout.

Note on stride: `default.yaml` sets stride=1 for single-run use. KSG on N=40
at stride=1 yields 461 windows; at the per-window cost of ~0.1–0.2 s the
probe would exceed its 20-minute budget. stride=5 (used here) is the
sweep-orchestration value from B2 and gives 93 windows — representative
coverage of steady-state at acceptable wall-clock cost.

Usage:
    python scripts/run_phase3_5_probe.py

Deliverables (outputs/phase3_5_probe/):
    <scenario>/seed<n>.parquet          — full per-window metrics
    <scenario>/seed<n>_telemetry.csv    — raw per-agent-per-step telemetry
    <scenario>/seed<n>_metadata.json    — D6 reproducibility metadata
    summary.csv                         — 9-row steady-state means table
    VERDICT.md                          — written manually after reviewing results
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.classical import (  # noqa: E402
    angular_momentum_norm,
    milling_score_magnitude,
    polarization,
)
from spectral_swarm_3d.analysis.features import extract_features  # noqa: E402
from spectral_swarm_3d.analysis.mi import mi_matrix_ksg, standardize_window  # noqa: E402
from spectral_swarm_3d.analysis.spectral import (  # noqa: E402
    fiedler_bipartition,
    normalized_laplacian,
    phi_spectral,
)
from spectral_swarm_3d.analysis.tda import (  # noqa: E402
    compute_persistence,
    persistence_summaries,
    snapshot_cloud,
    trajectory_cloud,
)
from spectral_swarm_3d.model import BoidSwarmModel3D  # noqa: E402

SCENARIOS = ["none", "split_merge", "jamming"]
SEEDS = [0, 1, 2]
T_STEPS = 500
STRIDE = 5  # B2 sweep-orchestration value; stride=1 is too slow for KSG at N=40


def _analyze_run(telemetry_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Per-window analysis for one simulation run.

    Computes Phi_spectral, snapshot TDA (H0/H1), trajectory TDA (H0/H1),
    and classical metrics for every window of width W at step STRIDE.

    Parameters
    ----------
    telemetry_df:
        Per-agent-per-step telemetry from the simulation.
    config:
        Full config dict (used for W, k_ksg, mi_tie_break_noise, L).

    Returns
    -------
    DataFrame with one row per window.
    """
    W: int = int(config["W"])
    k_ksg: int = int(config.get("k_ksg", 5))
    noise_eps: float = float(config.get("mi_tie_break_noise", 1e-10))
    L: float = float(config["L"])
    center = np.array([L / 2, L / 2, L / 2])

    features = extract_features(telemetry_df, "kinematic")  # (T, N, d)
    T_len = features.shape[0]

    n_windows = (T_len - W) // STRIDE + 1

    baseline_snap_dgms: list | None = None
    baseline_traj_dgms: list | None = None
    prev_snap_dgms: list | None = None
    prev_traj_dgms: list | None = None

    rows: list[dict] = []

    for k in range(n_windows):
        t0 = k * STRIDE
        t1 = t0 + W
        window = features[t0:t1]  # (W, N, d)

        # D3 — per-agent per-channel standardisation before MI
        Xs = standardize_window(window)

        # Phi_spectral
        M = mi_matrix_ksg(Xs, k=k_ksg, noise_eps=noise_eps)
        L_mat = normalized_laplacian(M)
        part = fiedler_bipartition(L_mat)
        phi_val = phi_spectral(M, part)

        # Classical metrics: last step of the window
        t_snap = t1 - 1
        step_df = telemetry_df[telemetry_df["step"] == t_snap].sort_values("agent_id")
        pos = step_df[["x", "y", "z"]].to_numpy(dtype=float)
        vel = step_df[["vx", "vy", "vz"]].to_numpy(dtype=float)

        pol_val = polarization(vel)
        mill_val = milling_score_magnitude(pos, vel, center)
        amn_val = angular_momentum_norm(pos, vel, center)

        # Snapshot TDA (H0, H1) on 3D position cloud
        snap_pts = snapshot_cloud(pos)  # (N, 3)
        snap_dgms = compute_persistence(snap_pts, maxdim=1)
        if baseline_snap_dgms is None:
            baseline_snap_dgms = snap_dgms
        snap_sums = persistence_summaries(
            snap_dgms,
            baseline_dgms=baseline_snap_dgms,
            prev_dgms=prev_snap_dgms,
            maxdim=1,
        )
        prev_snap_dgms = snap_dgms

        # Trajectory TDA (H0, H1) on N × W*d cloud
        traj_pts = trajectory_cloud(Xs)  # (N, W*d)
        traj_dgms = compute_persistence(traj_pts, maxdim=1)
        if baseline_traj_dgms is None:
            baseline_traj_dgms = traj_dgms
        traj_sums = persistence_summaries(
            traj_dgms,
            baseline_dgms=baseline_traj_dgms,
            prev_dgms=prev_traj_dgms,
            maxdim=1,
        )
        prev_traj_dgms = traj_dgms

        row: dict = {
            "window_idx": k,
            "step_start": t0,
            "step_end": t_snap,
            "phi_spectral": phi_val,
            "polarization": pol_val,
            "milling_score": mill_val,
            "angular_momentum_norm": amn_val,
        }
        for key, val in snap_sums.items():
            row[f"snap_{key}"] = val
        for key, val in traj_sums.items():
            row[f"traj_{key}"] = val

        rows.append(row)

    return pd.DataFrame(rows)


def _steady_state_means(run_df: pd.DataFrame) -> dict[str, float]:
    """Mean of probe columns over the final third of windows (§3.8)."""
    n = len(run_df)
    ss = run_df.iloc[n * 2 // 3 :]
    cols = [
        "phi_spectral",
        "polarization",
        "milling_score",
        "angular_momentum_norm",
        "traj_TP_1",
        "traj_MP_1",
        "snap_TP_0",
        "snap_TP_1",
    ]
    return {c: float(ss[c].mean()) for c in cols}


def main() -> None:
    config_path = REPO_ROOT / "configs" / "default.yaml"
    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    out_root = REPO_ROOT / "outputs" / "phase3_5_probe"
    out_root.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict] = []
    global_t0 = time.perf_counter()

    for scenario in SCENARIOS:
        sc_dir = out_root / scenario
        sc_dir.mkdir(parents=True, exist_ok=True)

        for seed in SEEDS:
            print(f"\n=== scenario={scenario!r}  seed={seed} ===", flush=True)
            run_t0 = time.perf_counter()

            telem_path = sc_dir / f"seed{seed}_telemetry.csv"
            meta_path = sc_dir / f"seed{seed}_metadata.json"
            parquet_path = sc_dir / f"seed{seed}.parquet"

            # --- Simulation ---
            print("  Simulating ...", flush=True)
            model = BoidSwarmModel3D(
                cfg,
                scenario_name=scenario,
                seed=seed,
                telemetry_path=telem_path,
            )
            model.run(T=T_STEPS)
            model.save_metadata(meta_path, repo_root=REPO_ROOT)
            sim_t = time.perf_counter() - run_t0
            print(f"  Simulation done in {sim_t:.1f}s", flush=True)

            # --- Analysis ---
            print("  Analysing windows ...", flush=True)
            telem_df = pd.read_csv(telem_path)
            run_df = _analyze_run(telem_df, cfg)
            analysis_t = time.perf_counter() - run_t0 - sim_t
            print(f"  Analysis done in {analysis_t:.1f}s ({len(run_df)} windows)", flush=True)

            # --- Save Parquet ---
            run_df.to_parquet(parquet_path, index=False)

            # --- Steady-state summary ---
            ss = _steady_state_means(run_df)
            n = len(run_df)
            n_ss = n - n * 2 // 3
            print(
                f"  Steady-state ({n_ss} windows): "
                f"phi={ss['phi_spectral']:.4f}  pol={ss['polarization']:.4f}  "
                f"traj_TP_1={ss['traj_TP_1']:.4f}  snap_TP_1={ss['snap_TP_1']:.4f}",
                flush=True,
            )

            row = {"scenario": scenario, "seed": seed}
            row.update(ss)
            summary_rows.append(row)

    # --- Summary CSV ---
    summary_df = pd.DataFrame(summary_rows)
    col_order = [
        "scenario",
        "seed",
        "phi_spectral",
        "polarization",
        "milling_score",
        "angular_momentum_norm",
        "traj_TP_1",
        "traj_MP_1",
        "snap_TP_0",
        "snap_TP_1",
    ]
    summary_df = summary_df[col_order]
    summary_path = out_root / "summary.csv"
    summary_df.to_csv(summary_path, index=False, float_format="%.6f")

    elapsed = time.perf_counter() - global_t0
    print(f"\n\nAll 9 runs completed in {elapsed:.1f}s ({elapsed / 60:.1f} min).", flush=True)
    print(f"Summary CSV written to: {summary_path}", flush=True)

    print("\n--- Summary Table ---\n")
    # Format for readability
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", 12)
    pd.set_option("display.width", 140)
    print(summary_df.to_string(index=False))

    verdict_path = out_root / "VERDICT.md"
    print(f"\nNext: write {verdict_path} after reviewing the table above.")


if __name__ == "__main__":
    main()
