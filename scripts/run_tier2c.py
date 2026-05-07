#!/usr/bin/env python3
"""Phase 5, Tier 2.C — Aggregated comparison runs.

Deliverables 1–5 (Phase5.md canonical) + cross-sweep provenance/validation.

Usage:
    python scripts/run_tier2c.py

Outputs:
  Per-sweep (all 11 sweeps):
    outputs/comparison/<sweep>/eta_squared.csv
    outputs/comparison/<sweep>/agreement_heatmap.csv
    outputs/comparison/<sweep>/agreement_heatmap.png
    outputs/comparison/<sweep>/matched_control_deltas.csv  (event sweeps only)
  Cross-sweep:
    outputs/comparison/cross_sweep/scenario_agreement_spearman.csv
    outputs/comparison/cross_sweep/scenario_agreement_spearman.png
    outputs/comparison/cross_sweep/monitoring_roc.csv
    outputs/comparison/cross_sweep/monitoring_roc.png
  Provenance:
    outputs/comparison/_run_metadata.json
    outputs/comparison/_validation.txt
"""
from __future__ import annotations

import hashlib
import importlib.metadata as _imp_meta
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spectral_swarm_3d.analysis.comparison import (
    VANILLA_BASELINE_CONDITIONS,
    _VANILLA_CONDITION_NAMES,
    agreement_divergence_with_pvalues,
    cross_condition_sensitivity,
    load_sweep_runs,
    matched_control_deltas,
    monitoring_roc,
)
from spectral_swarm_3d.analysis.plotting import (
    configure_style,
    plot_agreement_heatmap,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
OUTPUTS = REPO_ROOT / "outputs"
COMP = OUTPUTS / "comparison"
CROSS = COMP / "cross_sweep"

SWEEPS = [
    "alignment_sweep",
    "jamming_sweep",
    "leadership_sweep",
    "split_merge_sweep",
    "milling_sweep",
    "noise_sweep",
    "n_sensitivity_N80",
    "n_sensitivity_N160",
    "w_sensitivity",
    "alignment_rule_sensitivity",
    "sensitivity",
]

# Event sweeps: (control_condition, t_on, t_off) — from configs/default.yaml
EVENT_SWEEPS: dict[str, tuple[str, int, int]] = {
    "jamming_sweep": ("alpha_1.0", 200, 400),
    "split_merge_sweep": ("none", 200, 400),
}

# sensitivity sweep contains histogram estimator conditions → flag all rows sign-only
HISTOGRAM_SWEEPS: frozenset[str] = frozenset(["sensitivity"])

W = 40  # from configs/default.yaml

# TDA columns used in cross-sweep Spearman matrix (from comparison.py _TDA_COMPARE)
_TDA_COMPARE = [
    "snap_TP_0", "snap_TP_1", "snap_TP_2",
    "snap_MP_0", "snap_MP_1", "snap_MP_2",
    "snap_B_base_0", "snap_B_base_1", "snap_B_base_2",
    "traj_TP_0", "traj_TP_1", "traj_TP_2",
    "traj_MP_0", "traj_MP_1", "traj_MP_2",
    "traj_B_base_0", "traj_B_base_1", "traj_B_base_2",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _save_png(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _plot_spearman_heatmap(
    mat_df: pd.DataFrame,
    tda_cols: list[str],
    title: str,
    out_path: Path,
    vanilla_row_aliases: list[str] | None = None,
) -> None:
    """Generic Spearman rho heatmap; rows=conditions, cols=TDA metrics."""
    tda_present = [c for c in tda_cols if c in mat_df.columns]
    if not tda_present or mat_df.empty:
        return

    data = mat_df[tda_present].astype(float)
    short_cols = [
        c.replace("snap_", "s.").replace("traj_", "t.")
        for c in tda_present
    ]

    fig, ax = plt.subplots(
        figsize=(max(8, 0.8 * len(tda_present)), max(5, 0.4 * len(data) + 1.5))
    )
    im = ax.imshow(data.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(tda_present)))
    ax.set_xticklabels(short_cols, rotation=45, ha="right", fontsize=7)
    ax.set_yticks(range(len(data)))
    ylabels = list(data.index)
    if vanilla_row_aliases and "vanilla_baseline" in ylabels:
        i = ylabels.index("vanilla_baseline")
        ylabels[i] = f"vanilla_baseline (×{len(vanilla_row_aliases)})"
    ax.set_yticklabels(ylabels, fontsize=7)
    ax.set_title(title, fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Spearman rho")
    fig.tight_layout()
    _save_png(fig, out_path)


def _plot_roc_heatmap(roc_df: pd.DataFrame, out_path: Path) -> None:
    """Heatmap: rows = sweep/condition, cols = top metrics, values = AUC."""
    roc_df = roc_df.copy()
    roc_df["label"] = roc_df["sweep"] + "/" + roc_df["condition"]
    pivot = roc_df.pivot_table(
        index="label", columns="metric", values="auc", aggfunc="mean"
    )
    top_metrics = pivot.mean(skipna=True).sort_values(ascending=False).head(15).index
    pivot = pivot[top_metrics]

    fig, ax = plt.subplots(
        figsize=(max(7, 0.8 * len(pivot.columns)), max(4, 0.4 * len(pivot) + 1.5))
    )
    im = ax.imshow(pivot.values, cmap="YlOrRd", vmin=0.5, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    ax.set_title("Monitoring ROC AUC: event sweep conditions × metrics", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="AUC")
    fig.tight_layout()
    _save_png(fig, out_path)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> dict:
    COMP.mkdir(parents=True, exist_ok=True)
    CROSS.mkdir(parents=True, exist_ok=True)
    configure_style()

    validation: dict = {}
    input_files: list[dict] = []
    all_ad_rows: list[pd.DataFrame] = []
    event_roc_rows: list[dict] = []

    for sweep_name in SWEEPS:
        sweep_dir = OUTPUTS / sweep_name
        sweep_data, is_shared = load_sweep_runs(sweep_dir)
        if not sweep_data:
            print(f"  {sweep_name}: no data — skipping")
            validation.setdefault("missing_sweeps", []).append(sweep_name)
            continue

        out_dir = COMP / sweep_name
        out_dir.mkdir(parents=True, exist_ok=True)

        n_conds = len(sweep_data)
        n_seeds_min = min(len(runs) for runs in sweep_data.values())
        is_hist = sweep_name in HISTOGRAM_SWEEPS

        print(f"\n{'='*60}")
        print(f"  {sweep_name}  ({n_conds} conditions, ≥{n_seeds_min} seeds)")
        print(f"{'='*60}")

        # Track input files for provenance (sample: one file per condition)
        for cond, runs in sweep_data.items():
            for seed, _ in runs:
                pq = sweep_dir / cond / f"seed{seed}.parquet"
                if pq.exists():
                    input_files.append({
                        "path": str(pq.relative_to(REPO_ROOT)),
                        "size": pq.stat().st_size,
                        "sha256": _sha256(pq),
                    })

        # ── Deliverable 1: eta_squared.csv ───────────────────────────────────
        eta2_df = cross_condition_sensitivity(
            sweep_data, n_bootstrap=1000, collapse_shared_baseline=False
        )
        if not eta2_df.empty:
            out_eta = eta2_df.reset_index().rename(columns={"index": "metric"})
            out_eta["n_conditions"] = n_conds
            out_eta["n_seeds_per_condition"] = n_seeds_min
            out_eta["histogram_sign_only"] = is_hist
            out_eta.to_csv(out_dir / "eta_squared.csv", index=False)

            oob = out_eta["eta2"].dropna()
            oob = oob[(oob < -1e-9) | (oob > 1 + 1e-9)]
            if not oob.empty:
                validation.setdefault("eta2_out_of_range", {})[sweep_name] = oob.to_dict()
                print(f"  WARNING η² out of range: {oob.to_dict()}")
            top3 = out_eta.set_index("metric")["eta2"].dropna().head(3)
            print(f"  η² top-3: {', '.join(f'{m}={v:.3f}' for m, v in top3.items())}")
        print(f"  eta_squared.csv: {len(eta2_df)} metrics")

        # ── Deliverable 2: agreement_heatmap.csv + .png ───────────────────────
        ad_df, _ = agreement_divergence_with_pvalues(
            sweep_data, sweep_label=sweep_name
        )
        if not ad_df.empty:
            ad_df.to_csv(out_dir / "agreement_heatmap.csv", index=False)

            # Plot using existing function which saves to out_dir/agreement_{name}.png
            plot_agreement_heatmap(ad_df, sweep_name, out_dir)
            src = out_dir / f"agreement_{sweep_name}.png"
            dst = out_dir / "agreement_heatmap.png"
            if src.exists():
                src.replace(dst)
            # Also clean up PDF if created
            pdf = out_dir / f"agreement_{sweep_name}.pdf"
            if pdf.exists():
                pdf.unlink()

            print(f"  agreement_heatmap: {len(ad_df)} conditions")

            # Collect for cross-sweep: qualify condition names with sweep prefix
            ad_cross = ad_df.copy()
            ad_cross["condition_orig"] = ad_cross["condition"]
            ad_cross["condition"] = sweep_name + "/" + ad_cross["condition"]
            all_ad_rows.append(ad_cross)

        # ── Deliverable 3: matched_control_deltas.csv (event sweeps only) ─────
        if sweep_name in EVENT_SWEEPS:
            ctrl_label, t_on, t_off = EVENT_SWEEPS[sweep_name]
            deltas = matched_control_deltas(sweep_data, ctrl_label)
            if not deltas.empty:
                deltas.to_csv(out_dir / "matched_control_deltas.csv", index=False)
                print(f"  matched_control_deltas: {len(deltas)} rows vs '{ctrl_label}'")

            # Collect monitoring ROC for deliverable 5
            for cond, runs in sweep_data.items():
                aucs = monitoring_roc(runs, t_on, t_off, W=W)
                for metric, auc in aucs.items():
                    event_roc_rows.append({
                        "sweep": sweep_name, "condition": cond,
                        "metric": metric, "auc": float(auc),
                    })

        validation.setdefault("sweeps_loaded", []).append(sweep_name)
        validation.setdefault("conditions_per_sweep", {})[sweep_name] = n_conds

    # ── Deliverable 4: Cross-scenario Spearman matrix ─────────────────────────
    if all_ad_rows:
        combined = pd.concat(all_ad_rows, ignore_index=True)

        # Identify vanilla baseline rows
        vanilla_mask = combined["condition_orig"].isin(_VANILLA_CONDITION_NAMES)
        vanilla_rows = combined[vanilla_mask]
        non_vanilla = combined[~vanilla_mask].copy()

        n_before = len(combined)
        vanilla_aliases = sorted(combined.loc[vanilla_mask, "condition_orig"].unique())

        # Collapse vanilla rows: average Spearman rho values
        tda_present = [c for c in _TDA_COMPARE if c in combined.columns]
        if vanilla_rows.empty:
            vb_row: dict = {}
        else:
            vb_row = vanilla_rows[tda_present].mean().to_dict()
        vb_row["condition"] = "vanilla_baseline"
        vb_row["condition_orig"] = ", ".join(vanilla_aliases)
        vb_row["sweep"] = "multiple"

        final_ad = pd.concat(
            [non_vanilla, pd.DataFrame([vb_row])], ignore_index=True
        )
        n_after = len(final_ad)
        collapse_delta = n_before - n_after

        validation["shared_baseline_collapse"] = {
            "n_before": n_before,
            "n_after": n_after,
            "delta": collapse_delta,
            "expected_delta": 7,
            "pass": collapse_delta == 7,
            "vanilla_aliases_count": len(vanilla_aliases),
            "vanilla_aliases": vanilla_aliases,
        }

        print(f"\nCross-sweep Spearman: {n_before} rows → {n_after} after collapse "
              f"(delta={collapse_delta}, expected=7, "
              f"{'PASS' if collapse_delta == 7 else 'FAIL'})")

        out_cols = ["condition", "sweep"] + [c for c in tda_present if c in final_ad.columns]
        final_ad[out_cols].to_csv(CROSS / "scenario_agreement_spearman.csv", index=False)

        mat_df = final_ad.set_index("condition")
        _plot_spearman_heatmap(
            mat_df, tda_present,
            "Cross-sweep scenario agreement (Spearman rho: phi_spectral vs TDA, H0–H2)\n"
            "vanilla_baseline row = 8 byte-identical conditions collapsed",
            CROSS / "scenario_agreement_spearman.png",
            vanilla_row_aliases=vanilla_aliases,
        )
        print(f"  scenario_agreement_spearman.csv + .png written")

    # ── Deliverable 5: Monitoring ROC cross-sweep ─────────────────────────────
    if event_roc_rows:
        roc_df = pd.DataFrame(event_roc_rows)
        roc_df.to_csv(CROSS / "monitoring_roc.csv", index=False)
        _plot_roc_heatmap(roc_df, CROSS / "monitoring_roc.png")
        print(f"\nMonitoring ROC: {len(roc_df)} metric×condition rows written")

    # ── Deliverable 8a: _run_metadata.json ───────────────────────────────────
    deps: dict[str, str] = {}
    for pkg in ["numpy", "pandas", "scipy", "matplotlib", "scikit-learn", "diptest"]:
        try:
            deps[pkg] = _imp_meta.version(pkg)
        except Exception:
            deps[pkg] = "unknown"

    meta = {
        "head_sha": _head_sha(),
        "python_version": sys.version.split()[0],
        "dependencies": deps,
        "n_input_files": len(input_files),
        "conditions_per_sweep": validation.get("conditions_per_sweep", {}),
        "shared_baseline_collapse": validation.get("shared_baseline_collapse", {}),
    }
    with open(COMP / "_run_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\n_run_metadata.json written")

    return validation


# ─────────────────────────────────────────────────────────────────────────────
# Validation report
# ─────────────────────────────────────────────────────────────────────────────

def write_validation(validation: dict) -> None:
    lines = [
        "Phase 5 Tier 2.C — Validation Checks",
        "=" * 45,
        "",
    ]

    # [1] Sweeps loaded
    loaded = validation.get("sweeps_loaded", [])
    missing = [s for s in SWEEPS if s not in loaded]
    status = "PASS" if not missing else f"FAIL — missing: {missing}"
    lines += [f"[1] Sweeps loaded: {len(loaded)}/11  {status}", ""]

    # [2] Shared-baseline collapse
    sb = validation.get("shared_baseline_collapse", {})
    n_b = sb.get("n_before", "?")
    n_a = sb.get("n_after", "?")
    delta = sb.get("delta", "?")
    ok = sb.get("pass", False)
    aliases = sb.get("vanilla_aliases", [])
    lines += [
        f"[2] Shared-baseline collapse: {n_b} rows → {n_a} (delta={delta}, expected=7)",
        f"    {'PASS' if ok else 'FAIL'}",
        f"    vanilla_baseline aliases ({len(aliases)}): " + ", ".join(aliases),
        "",
    ]

    # [3] η² range
    oob = validation.get("eta2_out_of_range", {})
    if not oob:
        lines += ["[3] η² range: PASS — all values in [0, 1]", ""]
    else:
        lines += [f"[3] η² range: FAIL — out-of-range in: {list(oob.keys())}", ""]

    # [4] Surrogate integration + bimodality: performed by build_scenario_summary.py
    lines += [
        "[4] Surrogate integration (8 scenarios populated) and",
        "    bimodality cross-check (alignment w_a=0.6 dip p ≈ 0.102):",
        "    Run build_scenario_summary.py — validation appended to this file.",
        "",
    ]

    # [5] Conditions per sweep
    cps = validation.get("conditions_per_sweep", {})
    lines += ["[5] Conditions per sweep:"]
    for sw in SWEEPS:
        nc = cps.get(sw, "MISSING")
        lines.append(f"    {sw}: {nc}")
    lines.append("")

    text = "\n".join(lines)
    (COMP / "_validation.txt").write_text(text)
    print(f"\n_validation.txt written")
    print("\n" + text)


if __name__ == "__main__":
    validation = main()
    write_validation(validation)
