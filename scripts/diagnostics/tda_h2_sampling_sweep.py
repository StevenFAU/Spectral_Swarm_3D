"""TDA H2 sampling-density diagnostic sweep across (N, embedding, scenario).

D9 investigation (docs/decisions/D9_h2_sampling_density.md): empirically
determine which (N, embedding) combinations produce milling MP_2 / baseline
MP_2 >= 2.0, to inform resolution of the Phase 3 H2 positive-control failure.

Sweep: N ∈ {40, 80, 120, 160} × embedding ∈ {unaugmented, augmented} ×
scenario ∈ {none, milling} at seed=0, T=500, step=499.

No production code is modified. Does not alter xfail in test_phase3_integration.py.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.tda import (  # noqa: E402
    compute_persistence,
    persistence_summaries,
    snapshot_cloud,
)
from spectral_swarm_3d.model import BoidSwarmModel3D  # noqa: E402


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(REPO_ROOT),
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _nn_spacing(cloud: np.ndarray) -> float:
    """Mean nearest-neighbor Euclidean distance in the given point cloud."""
    tree = cKDTree(cloud)
    dists, _ = tree.query(cloud, k=2)  # k=2: first hit is self (distance 0)
    return float(dists[:, 1].mean())


def run_sweep() -> pd.DataFrame:
    """Execute the full (N, scenario, embedding) sweep and return results."""
    config_path = REPO_ROOT / "configs" / "default.yaml"
    with config_path.open() as f:
        base_cfg = yaml.safe_load(f)

    N_values = [40, 80, 120, 160]
    scenarios = ["none", "milling"]
    embeddings = ["unaugmented", "augmented"]
    beta = float(base_cfg["snapshot_beta"])
    L = float(base_cfg["L"])
    center = np.array([L / 2.0, L / 2.0, L / 2.0])

    rows = []
    for N in N_values:
        cfg = dict(base_cfg)
        cfg["N"] = N
        print(f"N={N}: running simulations ...", flush=True)

        sim_data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for scenario in scenarios:
            model = BoidSwarmModel3D(cfg, scenario_name=scenario, seed=0)
            model.run(T=500)
            positions = model._positions()
            velocities = model._velocities()
            sim_data[scenario] = (positions, velocities)
            print(f"  scenario={scenario!r} done", flush=True)

        for scenario in scenarios:
            positions, velocities = sim_data[scenario]
            radial = np.linalg.norm(positions - center, axis=1)
            mean_radial = float(radial.mean())
            shell_thickness = float(radial.std())

            for emb in embeddings:
                if emb == "unaugmented":
                    cloud = snapshot_cloud(positions, augmented=False)
                else:
                    cloud = snapshot_cloud(
                        positions,
                        augmented=True,
                        velocities=velocities,
                        beta=beta,
                    )

                nn_spacing = _nn_spacing(cloud)
                dgms = compute_persistence(cloud, maxdim=2)
                summaries = persistence_summaries(dgms, maxdim=2)

                rows.append(
                    {
                        "N": N,
                        "scenario": scenario,
                        "embedding": emb,
                        "snap_TP_2": round(summaries["TP_2"], 6),
                        "snap_MP_2": round(summaries["MP_2"], 6),
                        "mean_radial_distance": round(mean_radial, 4),
                        "nearest_neighbor_spacing": round(nn_spacing, 4),
                        "shell_thickness": round(shell_thickness, 4),
                    }
                )

    return pd.DataFrame(rows)


def _df_to_md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a plain GitHub-flavoured markdown table."""
    cols = df.columns.tolist()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                cells.append(f"{val:.4f}")
            else:
                cells.append(str(val))
        body_rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + body_rows)


def write_markdown(df: pd.DataFrame, sha: str, out_path: Path) -> None:
    today = datetime.date.today().isoformat()
    threshold = 2.0

    # Collect qualifying (N, embedding) pairs.
    qualifying: list[tuple[int, str, float, float, float]] = []
    for N in sorted(df["N"].unique()):
        for emb in ["unaugmented", "augmented"]:
            base_row = df[
                (df["N"] == N) & (df["scenario"] == "none") & (df["embedding"] == emb)
            ]
            mill_row = df[
                (df["N"] == N) & (df["scenario"] == "milling") & (df["embedding"] == emb)
            ]
            if base_row.empty or mill_row.empty:
                continue
            base_mp2 = float(base_row["snap_MP_2"].iloc[0])
            mill_mp2 = float(mill_row["snap_MP_2"].iloc[0])
            if base_mp2 > 0.0:
                ratio = mill_mp2 / base_mp2
            elif mill_mp2 > 0.0:
                ratio = float("inf")
            else:
                ratio = float("nan")
            if ratio >= threshold:
                qualifying.append((N, emb, mill_mp2, base_mp2, ratio))

    lines: list[str] = [
        "# TDA H2 Sampling Density Sweep",
        "",
        f"**Date:** {today}  ",
        f"**Git commit:** `{sha}`",
        "",
        "Diagnostic sweep for D9 (H2 sampling density decision). Covers",
        "N ∈ {40, 80, 120, 160} × embedding ∈ {unaugmented, augmented} ×",
        "scenario ∈ {none, milling} at seed=0, T=500, step=499.",
        "Geometry fixed at defaults: L=50, milling_R=11, speed=1.0, vision_radius=10.",
        "",
        "## Results",
        "",
        _df_to_md_table(df),
        "",
        "## Summary",
        "",
    ]

    if qualifying:
        lines.append(
            f"The following (N, embedding) combinations produce "
            f"milling MP_2 / baseline MP_2 ≥ {threshold:.1f}:"
        )
        lines.append("")
        for N, emb, mill_mp2, base_mp2, ratio in qualifying:
            ratio_str = f"{ratio:.2f}" if np.isfinite(ratio) else "∞"
            lines.append(
                f"- N={N}, {emb}: milling MP_2={mill_mp2:.4f}, "
                f"baseline MP_2={base_mp2:.4f}, ratio={ratio_str}"
            )
    else:
        lines.append(
            f"No (N, embedding) combination produces milling MP_2 / baseline MP_2 ≥ {threshold:.1f}. "
            "H2 void detection remains unreliable at all tested sampling densities with both "
            "unaugmented and augmented embeddings at methodology-spec geometry "
            "(L=50, milling_R=11, speed=1.0, vision_radius=10)."
        )

    lines.append("")
    out_path.write_text("\n".join(lines))


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    sha = _git_sha()
    df = run_sweep()

    csv_path = out_dir / "tda_h2_sampling_sweep.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nCSV written to {csv_path}", flush=True)

    md_path = out_dir / "tda_h2_sampling_sweep.md"
    write_markdown(df, sha, md_path)
    print(f"Markdown written to {md_path}", flush=True)

    print("\n--- Final DataFrame ---")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
