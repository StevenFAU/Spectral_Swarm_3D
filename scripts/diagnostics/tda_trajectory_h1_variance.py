"""Trajectory H1 variance check at W=80 across 5 seeds.

Follow-up to D9 closure (commit 17a9519). Confirms or denies the single-seed
observation (commit 23a8d4f, seed=0) that trajectory-cloud MP_1 at W=80
distinguishes milling from baseline — the basis on which Phase 4 may rewrite
the milling-sweep positive control from snap_TP_2 to traj_MP_1 or traj_TP_1.

Fixed: W=80, N=40, T=500, kinematic features, D3 standardization. maxdim=1 (H1
only). Seeds [0, 1, 2, 3, 4].

No production code modified. No test changes. No config changes. No D9 changes.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.features import extract_features  # noqa: E402
from spectral_swarm_3d.analysis.mi import standardize_window  # noqa: E402
from spectral_swarm_3d.analysis.tda import (  # noqa: E402
    compute_persistence,
    persistence_summaries,
    trajectory_cloud,
)
from spectral_swarm_3d.model import BoidSwarmModel3D  # noqa: E402

WALL_TIME_BUDGET_SEC = 600.0  # 10 minutes total
W = 80
T = 500
SEEDS = [0, 1, 2, 3, 4]
SCENARIOS = ["none", "milling"]


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


def _run_scenario(cfg: dict, scenario: str, seed: int) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        csv_path = Path(f.name)
    model = BoidSwarmModel3D(cfg, scenario_name=scenario, seed=seed, telemetry_path=csv_path)
    model.run(T=T)
    df = pd.read_csv(csv_path)
    csv_path.unlink(missing_ok=True)
    return df


def _df_to_md_table(df: pd.DataFrame) -> str:
    cols = df.columns.tolist()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in cols:
            val = row[col]
            if pd.isna(val):
                cells.append("NaN")
            elif isinstance(val, float):
                cells.append(f"{val:.4f}")
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)


def run_variance_check() -> pd.DataFrame:
    config_path = REPO_ROOT / "configs" / "default.yaml"
    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    global_t0 = time.perf_counter()
    rows: list[dict] = []

    for seed in SEEDS:
        for scenario in SCENARIOS:
            elapsed = time.perf_counter() - global_t0
            if elapsed >= WALL_TIME_BUDGET_SEC:
                print(
                    f"Budget exceeded at seed={seed}, scenario={scenario!r}; "
                    f"elapsed={elapsed:.1f}s >= {WALL_TIME_BUDGET_SEC:.0f}s — stopping.",
                    flush=True,
                )
                return pd.DataFrame(rows)

            print(f"  seed={seed}, scenario={scenario!r} ...", flush=True)
            t0 = time.perf_counter()

            telemetry = _run_scenario(cfg, scenario, seed)
            features = extract_features(telemetry, feature_set="kinematic")  # (T, N, d)
            window = features[T - W : T]               # (W, N, d)
            standardized = standardize_window(window)  # (W, N, d) — D3
            cloud = trajectory_cloud(standardized)     # (N, W*d)

            dgms = compute_persistence(cloud, maxdim=1)
            summaries = persistence_summaries(dgms, maxdim=1)

            wall_time = time.perf_counter() - t0
            rows.append(
                {
                    "seed": seed,
                    "scenario": scenario,
                    "W": W,
                    "MP_1": round(summaries["MP_1"], 6),
                    "TP_1": round(summaries["TP_1"], 6),
                    "wall_time_sec": round(wall_time, 2),
                }
            )
            print(
                f"  seed={seed}, scenario={scenario!r}: "
                f"MP_1={summaries['MP_1']:.4f}, TP_1={summaries['TP_1']:.4f}, "
                f"wall={wall_time:.1f}s",
                flush=True,
            )

    return pd.DataFrame(rows)


def _suitability_judgment(ratios: list[float], n_milling_gt_baseline: int) -> str:
    n = len(SEEDS)
    if n_milling_gt_baseline < n:
        return "not suitable as primary control; requires follow-up analysis"
    # All 5 seeds: milling > baseline
    if all(r >= 2.0 for r in ratios):
        return "suitable"
    return "provisionally suitable, monitor in Phase 4"


def write_markdown(df: pd.DataFrame, sha: str, out_path: Path) -> None:
    today = datetime.date.today().isoformat()

    mill = df[df["scenario"] == "milling"].set_index("seed")
    base = df[df["scenario"] == "none"].set_index("seed")

    seeds_present = sorted(set(mill.index) & set(base.index))
    ratios: list[float] = []
    n_milling_gt = 0
    for seed in seeds_present:
        m = float(mill.loc[seed, "MP_1"])
        b = float(base.loc[seed, "MP_1"])
        if b > 0.0:
            r = m / b
        elif m > 0.0:
            r = float("inf")
        else:
            r = float("nan")
        ratios.append(r)
        if m > b:
            n_milling_gt += 1

    finite_ratios = [r for r in ratios if np.isfinite(r)]
    ratio_min = min(finite_ratios) if finite_ratios else float("nan")
    ratio_max = max(finite_ratios) if finite_ratios else float("nan")
    ratio_mean = float(np.mean(finite_ratios)) if finite_ratios else float("nan")

    mill_mp1 = [float(mill.loc[s, "MP_1"]) for s in seeds_present]
    base_mp1 = [float(base.loc[s, "MP_1"]) for s in seeds_present]

    judgment = _suitability_judgment(
        [r for r in ratios if not np.isnan(r)], n_milling_gt
    )
    n_total = len(seeds_present)

    lines: list[str] = [
        "# Trajectory-Cloud H1 Variance Check (W=80, 5 seeds)",
        "",
        f"**Date:** {today}  ",
        f"**Git commit:** `{sha}`",
        "",
        "Follow-up to D9 closure. Checks whether the single-seed observation (seed=0,",
        "commit 23a8d4f) that trajectory-cloud MP_1 at W=80 distinguishes milling from",
        "baseline holds across seeds [0, 1, 2, 3, 4].",
        "",
        f"Fixed: W={W}, N=40, T={T}, kinematic features, D3 standardization, maxdim=1.",
        "",
        "## Raw results",
        "",
        _df_to_md_table(df),
        "",
        "## Per-scenario summary (MP_1)",
        "",
    ]

    for scenario, vals in [("milling", mill_mp1), ("none (baseline)", base_mp1)]:
        arr = np.array(vals)
        lines.append(
            f"**{scenario}:** mean={arr.mean():.4f}, std={arr.std():.4f}, "
            f"min={arr.min():.4f}, max={arr.max():.4f}"
        )
        lines.append("")

    ratio_strs = []
    for seed, r in zip(seeds_present, ratios):
        ratio_strs.append(f"seed={seed}: {r:.3f}" if np.isfinite(r) else f"seed={seed}: ∞")

    lines += [
        "## Per-seed ratios (milling MP_1 / baseline MP_1)",
        "",
        ", ".join(ratio_strs),
        "",
        f"Mean ratio: {ratio_mean:.3f}  ",
        f"Range: [{ratio_min:.3f}, {ratio_max:.3f}]  ",
        f"Seeds with milling > baseline: {n_milling_gt}/{n_total}",
        "",
        "## Suitability judgment",
        "",
        f"The milling > baseline direction holds for {n_milling_gt}/{n_total} seeds, "
        f"with per-seed ratios ranging from {ratio_min:.3f} to {ratio_max:.3f}. "
        f"At this variance profile, traj_MP_1 at W=80 is **{judgment}** as a "
        "Phase 4 milling-sweep positive control.",
    ]

    out_path.write_text("\n".join(lines))


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    sha = _git_sha()

    print(f"Running trajectory H1 variance check: W={W}, seeds={SEEDS}", flush=True)
    df = run_variance_check()

    csv_path = out_dir / "tda_trajectory_h1_variance.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nCSV written to {csv_path}", flush=True)

    md_path = out_dir / "tda_trajectory_h1_variance.md"
    write_markdown(df, sha, md_path)
    print(f"Markdown written to {md_path}", flush=True)

    print("\n--- Final DataFrame ---")
    print(df.to_string(index=False))

    # Print summary stats.
    mill = df[df["scenario"] == "milling"].set_index("seed")
    base = df[df["scenario"] == "none"].set_index("seed")
    seeds_present = sorted(set(mill.index) & set(base.index))

    print("\n--- MP_1 summary ---")
    mill_vals = np.array([float(mill.loc[s, "MP_1"]) for s in seeds_present])
    base_vals = np.array([float(base.loc[s, "MP_1"]) for s in seeds_present])
    print(
        f"milling : mean={mill_vals.mean():.4f} std={mill_vals.std():.4f} "
        f"min={mill_vals.min():.4f} max={mill_vals.max():.4f}"
    )
    print(
        f"baseline: mean={base_vals.mean():.4f} std={base_vals.std():.4f} "
        f"min={base_vals.min():.4f} max={base_vals.max():.4f}"
    )

    ratios = []
    n_milling_gt = 0
    for s in seeds_present:
        m = float(mill.loc[s, "MP_1"])
        b = float(base.loc[s, "MP_1"])
        r = m / b if b > 0.0 else (float("inf") if m > 0.0 else float("nan"))
        ratios.append(r)
        if m > b:
            n_milling_gt += 1

    print("\n--- Per-seed ratios (milling/baseline MP_1) ---")
    for s, r in zip(seeds_present, ratios):
        print(f"  seed={s}: {r:.4f}" if np.isfinite(r) else f"  seed={s}: inf")

    finite = [r for r in ratios if np.isfinite(r)]
    judgment = _suitability_judgment([r for r in ratios if not np.isnan(r)], n_milling_gt)
    print(
        f"\nmilling > baseline: {n_milling_gt}/{len(seeds_present)} seeds"
    )
    if finite:
        print(f"ratio mean={np.mean(finite):.4f}, range=[{min(finite):.4f}, {max(finite):.4f}]")
    print(f"\nSuitability judgment: {judgment}")


if __name__ == "__main__":
    main()
