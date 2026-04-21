"""Trajectory-cloud H2 diagnostic for D9 Option 1.

Tests whether trajectory-cloud H2 at N=40 (methodology-spec) distinguishes
milling from baseline, addressing the snapshot H2 over-triangulation gap
identified by the sampling-density sweep (59b5184).

Fixed: N=40, seed=0, T=500, kinematic features, unaugmented trajectory cloud.
Window widths W ∈ {40, 80}. D3 standardization applied before trajectory_cloud.

No production code modified. xfail on test_phase3_integration.py preserved.
D9 Resolution section unchanged.
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

WALL_TIME_BUDGET_SEC = 300.0  # 5 minutes per row


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


def _run_scenario(cfg: dict, scenario: str) -> pd.DataFrame:
    """Run simulation for one scenario and return telemetry DataFrame."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        csv_path = Path(f.name)
    model = BoidSwarmModel3D(cfg, scenario_name=scenario, seed=0, telemetry_path=csv_path)
    model.run(T=500)
    df = pd.read_csv(csv_path)
    csv_path.unlink(missing_ok=True)
    return df


def _df_to_md_table(df: pd.DataFrame) -> str:
    cols = df.columns.tolist()
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body_rows = []
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
        body_rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + body_rows)


def run_diagnostic() -> pd.DataFrame:
    config_path = REPO_ROOT / "configs" / "default.yaml"
    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    scenarios = ["none", "milling"]
    window_widths = [40, 80]
    T = 500

    # Pre-run both simulations (independent of window width).
    print("Running simulations ...", flush=True)
    telemetry: dict[str, pd.DataFrame] = {}
    for scenario in scenarios:
        print(f"  scenario={scenario!r} ...", flush=True)
        telemetry[scenario] = _run_scenario(cfg, scenario)
        print(f"  scenario={scenario!r} done", flush=True)

    # Extract features once per scenario; slice per window width.
    features_by_scenario: dict[str, np.ndarray] = {}
    for scenario in scenarios:
        features_by_scenario[scenario] = extract_features(
            telemetry[scenario], feature_set="kinematic"
        )  # shape (T=500, N=40, d=4)

    rows: list[dict] = []
    w40_wall_time: float | None = None

    for W in window_widths:
        # Skip guard: estimate W=80 cost from W=40 time. Ambient dim doubles
        # (160 → 320); assume at most 2x wall-time; skip if projected > budget.
        if W == 80 and w40_wall_time is not None:
            projected = w40_wall_time * 2.0
            if projected > WALL_TIME_BUDGET_SEC:
                print(
                    f"  W=80 skipped: projected wall time {projected:.0f}s "
                    f"exceeds budget {WALL_TIME_BUDGET_SEC:.0f}s",
                    flush=True,
                )
                for scenario in scenarios:
                    rows.append(
                        {
                            "scenario": scenario,
                            "W": W,
                            "ambient_dim": float("nan"),
                            "TP_0": float("nan"),
                            "MP_0": float("nan"),
                            "TP_1": float("nan"),
                            "MP_1": float("nan"),
                            "TP_2": float("nan"),
                            "MP_2": float("nan"),
                            "wall_time_sec": float("nan"),
                        }
                    )
                continue

        for scenario in scenarios:
            print(f"  W={W}, scenario={scenario!r} ...", flush=True)
            t0 = time.perf_counter()

            features = features_by_scenario[scenario]  # (500, 40, 4)
            window = features[T - W : T]               # (W, 40, 4)
            standardized = standardize_window(window)  # (W, 40, 4) — D3
            cloud = trajectory_cloud(standardized)     # (40, W*4)
            ambient_dim = cloud.shape[1]               # W*d = W*4

            dgms = compute_persistence(cloud, maxdim=2)
            summaries = persistence_summaries(dgms, maxdim=2)

            wall_time = time.perf_counter() - t0
            if W == 40:
                # Track per-scenario; use max as conservative estimate.
                if w40_wall_time is None:
                    w40_wall_time = wall_time
                else:
                    w40_wall_time = max(w40_wall_time, wall_time)

            rows.append(
                {
                    "scenario": scenario,
                    "W": W,
                    "ambient_dim": ambient_dim,
                    "TP_0": round(summaries["TP_0"], 6),
                    "MP_0": round(summaries["MP_0"], 6),
                    "TP_1": round(summaries["TP_1"], 6),
                    "MP_1": round(summaries["MP_1"], 6),
                    "TP_2": round(summaries["TP_2"], 6),
                    "MP_2": round(summaries["MP_2"], 6),
                    "wall_time_sec": round(wall_time, 2),
                }
            )
            print(
                f"  W={W}, scenario={scenario!r}: "
                f"MP_2={summaries['MP_2']:.4f}, TP_2={summaries['TP_2']:.4f}, "
                f"MP_1={summaries['MP_1']:.4f}, TP_1={summaries['TP_1']:.4f}, "
                f"wall={wall_time:.1f}s",
                flush=True,
            )

    return pd.DataFrame(rows)


def write_markdown(df: pd.DataFrame, sha: str, out_path: Path) -> None:
    today = datetime.date.today().isoformat()
    threshold = 2.0

    lines: list[str] = [
        "# TDA Trajectory-Cloud H2 Diagnostic (D9 Option 1)",
        "",
        f"**Date:** {today}  ",
        f"**Git commit:** `{sha}`",
        "",
        "Diagnostic for D9 (docs/decisions/D9_h2_sampling_density.md) Option 1:",
        "trajectory-cloud H2 at methodology-spec N=40. Fixed: seed=0, T=500,",
        "kinematic features, unaugmented, D3 standardization applied.",
        "Window widths W ∈ {40, 80}. Final window (T-W:T) used.",
        "",
        "## Results",
        "",
        _df_to_md_table(df),
        "",
        "## Summary",
        "",
    ]

    skipped_ws: list[int] = []
    for W in [40, 80]:
        w_rows = df[df["W"] == W]
        if not w_rows.empty and w_rows["wall_time_sec"].isna().all():
            skipped_ws.append(W)

    if skipped_ws:
        lines.append(
            f"W={skipped_ws} rows were skipped: projected wall time exceeded the "
            f"{int(WALL_TIME_BUDGET_SEC // 60)}-minute compute budget (estimated from W=40 timing)."
        )
        lines.append("")

    # Analyse H2 and H1 at each non-skipped W.
    for W in [40, 80]:
        w_rows = df[df["W"] == W]
        if w_rows.empty or w_rows["wall_time_sec"].isna().all():
            continue

        base_row = w_rows[w_rows["scenario"] == "none"]
        mill_row = w_rows[w_rows["scenario"] == "milling"]
        if base_row.empty or mill_row.empty:
            continue

        base_mp2 = float(base_row["MP_2"].iloc[0])
        mill_mp2 = float(mill_row["MP_2"].iloc[0])
        base_tp2 = float(base_row["TP_2"].iloc[0])
        mill_tp2 = float(mill_row["TP_2"].iloc[0])
        base_mp1 = float(base_row["MP_1"].iloc[0])
        mill_mp1 = float(mill_row["MP_1"].iloc[0])
        base_tp1 = float(base_row["TP_1"].iloc[0])
        mill_tp1 = float(mill_row["TP_1"].iloc[0])

        if base_mp2 > 0.0:
            h2_ratio = mill_mp2 / base_mp2
            ratio_str = f"{h2_ratio:.2f}"
        elif mill_mp2 > 0.0:
            h2_ratio = float("inf")
            ratio_str = "∞"
        else:
            h2_ratio = float("nan")
            ratio_str = "NaN"

        if base_mp1 > 0.0:
            h1_ratio = mill_mp1 / base_mp1
            h1_ratio_str = f"{h1_ratio:.2f}"
        elif mill_mp1 > 0.0:
            h1_ratio = float("inf")
            h1_ratio_str = "∞"
        else:
            h1_ratio = float("nan")
            h1_ratio_str = "NaN"

        h2_verdict = (
            f"milling MP_2 / baseline MP_2 = {ratio_str} "
            + ("≥" if np.isfinite(h2_ratio) and h2_ratio >= threshold else "<")
            + f" {threshold:.1f} — "
            + ("ACHIEVED" if np.isfinite(h2_ratio) and h2_ratio >= threshold else "NOT achieved")
        )

        lines += [
            f"### W={W} (ambient dim {W * 4})",
            "",
            f"**H2:** milling MP_2={mill_mp2:.4f}, TP_2={mill_tp2:.4f}; "
            f"baseline MP_2={base_mp2:.4f}, TP_2={base_tp2:.4f}. "
            f"{h2_verdict}.",
            "",
            f"**H1:** milling MP_1={mill_mp1:.4f}, TP_1={mill_tp1:.4f}; "
            f"baseline MP_1={base_mp1:.4f}, TP_1={base_tp1:.4f}. "
            f"milling MP_1 / baseline MP_1 = {h1_ratio_str}.",
            "",
        ]

    # Cross-W H2 verdict.
    w40_achieved = False
    w80_achieved = False
    w80_skipped = False

    w40_rows = df[df["W"] == 40]
    if not w40_rows.empty and not w40_rows["wall_time_sec"].isna().all():
        base_mp2_40 = float(w40_rows[w40_rows["scenario"] == "none"]["MP_2"].iloc[0])
        mill_mp2_40 = float(w40_rows[w40_rows["scenario"] == "milling"]["MP_2"].iloc[0])
        if base_mp2_40 > 0.0:
            w40_achieved = (mill_mp2_40 / base_mp2_40) >= threshold
        elif mill_mp2_40 > 0.0:
            w40_achieved = True

    w80_rows = df[df["W"] == 80]
    if not w80_rows.empty and w80_rows["wall_time_sec"].isna().all():
        w80_skipped = True
    elif not w80_rows.empty:
        base_mp2_80 = float(w80_rows[w80_rows["scenario"] == "none"]["MP_2"].iloc[0])
        mill_mp2_80 = float(w80_rows[w80_rows["scenario"] == "milling"]["MP_2"].iloc[0])
        if base_mp2_80 > 0.0:
            w80_achieved = (mill_mp2_80 / base_mp2_80) >= threshold
        elif mill_mp2_80 > 0.0:
            w80_achieved = True

    lines.append("### Overall H2 verdict")
    lines.append("")
    if w40_achieved and (w80_achieved or w80_skipped):
        lines.append(
            f"milling MP_2 / baseline MP_2 ≥ {threshold:.1f} achieved at W=40"
            + (" (W=80 skipped)." if w80_skipped else " and W=80.")
        )
    elif not w40_achieved and w80_achieved:
        lines.append(
            f"milling MP_2 / baseline MP_2 ≥ {threshold:.1f} achieved at W=80 only, not at W=40."
        )
    elif w80_skipped and not w40_achieved:
        lines.append(
            f"milling MP_2 / baseline MP_2 ≥ {threshold:.1f} not achieved at W=40. "
            "W=80 was skipped due to compute budget."
        )
    else:
        lines.append(
            f"milling MP_2 / baseline MP_2 ≥ {threshold:.1f} not achieved at "
            + ("either W=40 or W=80." if not w80_skipped else "W=40 (W=80 skipped).")
        )

    lines.append("")
    out_path.write_text("\n".join(lines))


def main() -> None:
    out_dir = REPO_ROOT / "outputs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    sha = _git_sha()
    df = run_diagnostic()

    csv_path = out_dir / "tda_trajectory_h2_diagnostic.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nCSV written to {csv_path}", flush=True)

    md_path = out_dir / "tda_trajectory_h2_diagnostic.md"
    write_markdown(df, sha, md_path)
    print(f"Markdown written to {md_path}", flush=True)

    print("\n--- Final DataFrame ---")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
