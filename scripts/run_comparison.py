#!/usr/bin/env python3
"""Phase 5 — Run all cross-method comparisons and generate figures.

Ported from 2D Spectral_Swarm v0.1-2d-poc with H2 column extensions and
--collapse-shared-baseline flag for Tier 2.C cross-scenario aggregation.

Reads sweep outputs from Phase 4 (Parquet files under outputs/) and produces:
  - Time-series overlays per scenario/condition
  - Cross-condition sensitivity (eta-squared) per sweep
  - Agreement/divergence heatmaps (Spearman phi_spectral vs TDA, H0–H2)
  - Matched-control delta charts
  - Monitoring benchmark (ROC AUC) for event sweeps

Gracefully skips any sweep that has no outputs yet.

Usage:
    python scripts/run_comparison.py [--out outputs] [--collapse-shared-baseline]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from spectral_swarm_3d.analysis.comparison import (
    agreement_divergence_with_pvalues,
    agreement_divergence_matrix,
    cross_condition_sensitivity,
    load_sweep_runs,
    matched_control_deltas,
    monitoring_roc,
    time_aligned_seed_mean,
)
from spectral_swarm_3d.analysis.plotting import (
    configure_style,
    plot_agreement_heatmap,
    plot_control_deltas,
    plot_monitoring_auc,
    plot_sensitivity_bars,
    plot_time_series,
)


# Control labels for matched-control analysis (boundary/baseline condition per sweep)
_CONTROL_LABELS: dict[str, str] = {
    "alignment_sweep":            "wa_0.0",
    "leadership_sweep":           "lambda_0.0",
    "milling_sweep":              "mu_0.0",
    "noise_sweep":                "sigma_0.0",
    "jamming_sweep":              "alpha_1.0",
    "split_merge_sweep":          "none",
    "w_sensitivity":              "W40",
    "alignment_rule_sensitivity": "mean",
    "sensitivity":                "ksg_kinematic",
}

# Event sweeps: config keys for (t_on, t_off)
_EVENT_SWEEPS: dict[str, tuple[str, str]] = {
    "jamming_sweep":    ("jam_t_on", "jam_t_off"),
    "split_merge_sweep": ("split_t_on", "split_t_off"),
}

# Sweeps and sub-directories that should not be treated as sweep data
_SKIP_DIRS: frozenset[str] = frozenset(
    ["tables", "figures", "tier1_compressibility", "diagnostics", "phase3_5_probe"]
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 5: comparison analysis + figures.")
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--out", default="outputs")
    p.add_argument(
        "--collapse-shared-baseline",
        action="store_true",
        default=False,
        help=(
            "Collapse the eight vanilla-baseline conditions to a single "
            "'vanilla_baseline' entry when computing eta-squared and Spearman "
            "correlations.  Default off (matches 2D semantics).  Tier 2.C uses "
            "this flag for cross-scenario aggregation."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.config) as f:
        base_config = yaml.safe_load(f)

    out_root = Path(args.out)
    fig_dir = out_root / "figures"
    W = int(base_config.get("W", 40))

    configure_style()

    if not out_root.is_dir():
        print(f"Output directory {out_root} does not exist. Run sweeps first.")
        return

    sweep_names = sorted(
        d.name for d in out_root.iterdir()
        if d.is_dir() and d.name not in _SKIP_DIRS
    )

    if not sweep_names:
        print("No sweep outputs found. Run run_sweep.py first.")
        return

    print(f"Found sweeps: {', '.join(sweep_names)}")

    all_ad_rows: list = []

    for sweep_name in sweep_names:
        sweep_dir = out_root / sweep_name
        sweep_data, is_shared = load_sweep_runs(sweep_dir)
        if not sweep_data:
            print(f"  {sweep_name}: no data, skipping.")
            continue

        n_conds = len(sweep_data)
        n_runs = sum(len(runs) for runs in sweep_data.values())
        n_shared = sum(1 for v in is_shared.values() if v)
        print(f"\n{'=' * 60}")
        print(f"  {sweep_name}  ({n_conds} conditions, {n_runs} runs"
              + (f", {n_shared} shared-baseline" if n_shared else "") + ")")
        print(f"{'=' * 60}")

        sweep_fig_dir = fig_dir / sweep_name

        # --- Time series for each condition ---
        for condition, runs in sweep_data.items():
            mean_ts = time_aligned_seed_mean(runs)
            plot_time_series(mean_ts, f"{sweep_name}/{condition}", sweep_fig_dir)
        print(f"  Time series: {n_conds} conditions plotted.")

        # --- Cross-condition sensitivity (with bootstrap CIs) ---
        eta2_df = cross_condition_sensitivity(
            sweep_data,
            n_bootstrap=1000,
            collapse_shared_baseline=args.collapse_shared_baseline,
        )
        if not eta2_df.empty:
            plot_sensitivity_bars(eta2_df["eta2"], sweep_name, sweep_fig_dir)
            top3 = eta2_df["eta2"].head(3)
            print(f"  Sensitivity (top 3): "
                  f"{', '.join(f'{m}={v:.3f}' for m, v in top3.items())}")
            tables_dir = out_root / "tables"
            tables_dir.mkdir(parents=True, exist_ok=True)
            eta2_df.to_csv(tables_dir / f"sensitivity_{sweep_name}.csv")

        # --- Agreement / divergence (with p-values) ---
        ad, ad_pval = agreement_divergence_with_pvalues(sweep_data, sweep_label=sweep_name)
        if not ad.empty:
            plot_agreement_heatmap(ad, sweep_name, sweep_fig_dir)
            all_ad_rows.append(ad)
            tables_dir = out_root / "tables"
            tables_dir.mkdir(parents=True, exist_ok=True)
            ad_pval.to_csv(
                tables_dir / f"agreement_pvalues_{sweep_name}.csv", index=False
            )
            print(f"  Agreement heatmap: {len(ad)} conditions.")

        # --- Matched-control deltas ---
        control = _CONTROL_LABELS.get(sweep_name)
        if control and control in sweep_data:
            deltas = matched_control_deltas(sweep_data, control)
            if not deltas.empty:
                plot_control_deltas(deltas, sweep_name, sweep_fig_dir)
                print(f"  Control deltas: {len(deltas)} conditions vs {control}.")

        # --- Monitoring benchmark (event sweeps only) ---
        if sweep_name in _EVENT_SWEEPS:
            t_on_key, t_off_key = _EVENT_SWEEPS[sweep_name]
            t_on = int(base_config[t_on_key])
            t_off = int(base_config[t_off_key])
            for condition, runs in sweep_data.items():
                aucs = monitoring_roc(runs, t_on, t_off, W=W)
                if not aucs.empty:
                    plot_monitoring_auc(aucs, f"{sweep_name}/{condition}", sweep_fig_dir)
                    top = aucs.head(1)
                    print(
                        f"  Monitoring {condition}: "
                        f"best={top.index[0]} AUC={top.values[0]:.3f}"
                    )

    # --- Combined agreement heatmap across all sweeps ---
    if all_ad_rows:
        import pandas as pd
        combined_ad = pd.concat(all_ad_rows, ignore_index=True)
        combined_ad["condition"] = (
            combined_ad["sweep"] + "/" + combined_ad["condition"]
        )
        plot_agreement_heatmap(combined_ad, "all_sweeps", fig_dir)
        print(f"\n  Combined agreement heatmap: {len(combined_ad)} rows across all sweeps.")

    print(f"\nFigures saved to {fig_dir}/")


if __name__ == "__main__":
    main()
