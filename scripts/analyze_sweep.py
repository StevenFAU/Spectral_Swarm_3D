"""Analyze completed sweep outputs: load Parquet files, compute summary tables.

Phase 4 implementation. See SpectralSwarm3DPhases.md §Phase 4, D2, D3.

For each sweep family, loads all per-seed Parquet files, calls
:func:`aggregate_steady_state` (with D2 bootstrap CIs), and writes:

* ``outputs/<sweep>/per_seed_summary.csv`` — one row per (condition, seed) with
  metric_mean / metric_ci_lo / metric_ci_hi columns plus git_commit / timestamp
  from the companion metadata.json.
* ``outputs/<sweep>/cross_seed_summary.csv`` — one row per condition; mean-of-means
  and std-of-means across seeds. Per-seed CIs are within-run uncertainty; std is
  cross-run variability. They are kept separate and not pooled (D2).

Special outputs:

* ``outputs/alignment_rule_sensitivity/README_summary.md`` (B2a)
* ``outputs/sensitivity/README_summary.md`` (B2b — 3×3 estimator × feature_set table)

Usage::

    python scripts/analyze_sweep.py [--sweep SWEEP] [--outputs DIR]

Omitting ``--sweep`` processes all known sweep families.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.aggregation import aggregate_steady_state  # noqa: E402

_log = logging.getLogger(__name__)

_STEADY_STATE_SWEEPS = [
    "alignment_sweep",
    "leadership_sweep",
    "jamming_sweep",
    "split_merge_sweep",
    "milling_sweep",
    "noise_sweep",
    "sensitivity",
    "n_sensitivity_N80",
    "n_sensitivity_N160",
    "w_sensitivity",
    "alignment_rule_sensitivity",
]


def _load_parquet_with_meta(
    parquet_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load a Parquet file and its companion metadata.json."""
    df = pd.read_parquet(parquet_path)
    meta_path = parquet_path.with_suffix(".metadata.json")
    if meta_path.exists():
        with meta_path.open() as f:
            meta = json.load(f)
    else:
        meta = {}
    return df, meta


def _aggregate_sweep(
    sweep: str,
    outputs_dir: Path,
    base_config: dict,
    bootstrap_ci: bool = True,
    n_bootstrap: int = 1000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate all Parquet files in a sweep directory.

    Returns
    -------
    per_seed_df
        One row per (condition, seed). Columns: sweep, condition, seed,
        {metric}_mean, {metric}_ci_lo, {metric}_ci_hi, git_commit, timestamp.
    cross_seed_df
        One row per condition. Columns: sweep, condition, n_seeds,
        {metric}_mean, {metric}_std.
    """
    sweep_dir = outputs_dir / sweep
    if not sweep_dir.exists():
        _log.warning("Sweep directory not found: %s", sweep_dir)
        return pd.DataFrame(), pd.DataFrame()

    per_seed_rows: list[dict[str, Any]] = []

    for cond_dir in sorted(sweep_dir.iterdir()):
        if not cond_dir.is_dir():
            continue
        condition = cond_dir.name
        parquet_files = sorted(cond_dir.glob("seed*.parquet"))
        if not parquet_files:
            _log.debug("No parquet files in %s", cond_dir)
            continue

        for pq_path in parquet_files:
            seed_str = pq_path.stem  # "seed0"
            try:
                seed = int(seed_str.replace("seed", ""))
            except ValueError:
                continue

            try:
                run_df, meta = _load_parquet_with_meta(pq_path)
            except Exception as exc:
                _log.error("Failed to load %s: %s", pq_path, exc)
                continue

            cfg = meta.get("config", base_config)
            ss = aggregate_steady_state(
                run_df, cfg, bootstrap_ci=bootstrap_ci, n_bootstrap=n_bootstrap
            )

            row: dict[str, Any] = {
                "sweep": sweep,
                "condition": condition,
                "seed": seed,
                "git_commit": meta.get("environment", {}).get("git_commit", ""),
                "timestamp": meta.get("environment", {}).get("timestamp", ""),
            }

            if bootstrap_ci and "mean" in ss:
                for col, val in ss["mean"].items():
                    row[f"{col}_mean"] = val
                for col, val in ss["ci_lo"].items():
                    row[f"{col}_ci_lo"] = val
                for col, val in ss["ci_hi"].items():
                    row[f"{col}_ci_hi"] = val
            else:
                for col, val in ss.items():
                    row[f"{col}_mean"] = val

            # Saturation diagnostic per D11: phi_saturation_ratio = phi_norm / log(W).
            W_run = int(cfg.get("W", 40))
            phi_norm_val = row.get("phi_norm_mean")
            if phi_norm_val is not None and np.isfinite(float(phi_norm_val)):
                row["phi_saturation_ratio"] = float(phi_norm_val) / np.log(W_run)
            else:
                row["phi_saturation_ratio"] = float("nan")

            per_seed_rows.append(row)

    if not per_seed_rows:
        return pd.DataFrame(), pd.DataFrame()

    per_seed_df = pd.DataFrame(per_seed_rows)

    # Cross-seed aggregation: mean-of-means and std-of-means.
    mean_cols = [c for c in per_seed_df.columns if c.endswith("_mean")]
    cross_seed_rows: list[dict[str, Any]] = []
    for condition, grp in per_seed_df.groupby("condition"):
        row_cs: dict[str, Any] = {
            "sweep": sweep,
            "condition": condition,
            "n_seeds": len(grp),
        }
        for mc in mean_cols:
            metric = mc[: -len("_mean")]
            vals = grp[mc].dropna().to_numpy(dtype=np.float64)
            row_cs[f"{metric}_mean"] = float(np.nanmean(vals)) if vals.size else float("nan")
            row_cs[f"{metric}_std"] = float(np.nanstd(vals)) if vals.size else float("nan")
        cross_seed_rows.append(row_cs)

    cross_seed_df = pd.DataFrame(cross_seed_rows)
    return per_seed_df, cross_seed_df


def _write_alignment_rule_summary(
    per_seed_df: pd.DataFrame,
    cross_seed_df: pd.DataFrame,
    outputs_dir: Path,
) -> None:
    """Write B2a summary: alignment_rule_sensitivity README."""
    out_path = outputs_dir / "alignment_rule_sensitivity" / "README_summary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# B2a — Alignment-Rule Sensitivity Summary",
        "",
        "Compares `mean` vs `sum` alignment rule at calibrated w_a=1.0, baseline "
        "scenario, 5 seeds each. Tests robustness of the A6 mean-alignment restoration.",
        "",
        "## Per-seed Φ_spectral at steady state",
        "",
    ]

    if "phi_spectral_mean" in per_seed_df.columns:
        lines.append(
            "| rule | seed | phi_spectral_mean | phi_spectral_ci_lo | phi_spectral_ci_hi |"
        )
        lines.append(
            "|------|------|-------------------|--------------------|--------------------|"
        )
        for _, row in per_seed_df.sort_values(["condition", "seed"]).iterrows():
            ci_lo = row.get("phi_spectral_ci_lo", float("nan"))
            ci_hi = row.get("phi_spectral_ci_hi", float("nan"))
            lines.append(
                f"| {row['condition']} | {row['seed']} "
                f"| {row['phi_spectral_mean']:.4f} "
                f"| {ci_lo:.4f} "
                f"| {ci_hi:.4f} |"
            )
        lines.append("")

        # Interpretation
        mean_vals: dict[str, list[float]] = {}
        for _, row in per_seed_df.iterrows():
            rule = row["condition"]
            mean_vals.setdefault(rule, []).append(row["phi_spectral_mean"])
        summary_means = {r: float(np.mean(v)) for r, v in mean_vals.items()}
        mean_rule = summary_means.get("mean", float("nan"))
        sum_rule = summary_means.get("sum", float("nan"))
        direction = "similar to" if abs(mean_rule - sum_rule) / (sum_rule + 1e-9) < 0.15 else (
            "higher than" if mean_rule > sum_rule else "lower than"
        )
        lines.append(
            f"**Interpretation:** Mean Φ_spectral at steady state: "
            f"`mean` rule = {mean_rule:.2f}, `sum` rule = {sum_rule:.2f}. "
            f"The `mean`-alignment restoration (A6) produces Φ_spectral behavior "
            f"qualitatively {direction} the `sum` variant."
        )
    else:
        lines.append("*phi_spectral data not available in this run.*")

    out_path.write_text("\n".join(lines) + "\n")
    _log.info("Wrote B2a summary: %s", out_path)


def _write_sensitivity_summary(
    per_seed_df: pd.DataFrame,
    cross_seed_df: pd.DataFrame,
    outputs_dir: Path,
) -> None:
    """Write B2b summary: 3×3 estimator × feature_set table of Φ_spectral."""
    out_path = outputs_dir / "sensitivity" / "README_summary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    estimators = ["ksg", "histogram", "gaussian"]
    feature_sets = ["kinematic", "vxvyvz", "full"]

    lines = [
        "# B2b — Estimator × Feature-Set Sensitivity Summary",
        "",
        "9-condition matrix: `{ksg, histogram, gaussian} × {kinematic, vxvyvz, full}`. "
        "Baseline scenario (none), w_a=1.0, 5 seeds each. Primary metric: Φ_spectral "
        "at steady state (mean across seeds).",
        "",
        "## 3×3 Φ_spectral table (mean across seeds)",
        "",
    ]

    # Build lookup: condition → cross-seed mean Φ_spectral
    phi_table: dict[str, dict[str, float]] = {e: {} for e in estimators}
    if not cross_seed_df.empty and "phi_spectral_mean" in cross_seed_df.columns:
        for _, row in cross_seed_df.iterrows():
            cond = str(row["condition"])  # e.g. "ksg_kinematic"
            parts = cond.split("_", 1)
            if len(parts) == 2:
                est, feat = parts[0], parts[1]
                if est in estimators and feat in feature_sets:
                    phi_table[est][feat] = float(row["phi_spectral_mean"])

    # Header row
    header = "| estimator | " + " | ".join(feature_sets) + " |"
    sep = "|-----------|" + "|".join(["------"] * len(feature_sets)) + "|"
    lines += [header, sep]
    for est in estimators:
        vals = [f"{phi_table[est].get(feat, float('nan')):.2f}" for feat in feature_sets]
        lines.append("| " + est + " | " + " | ".join(vals) + " |")
    lines.append("")

    # Interpretation paragraph
    ksg_vals = list(phi_table.get("ksg", {}).values())
    hist_vals = list(phi_table.get("histogram", {}).values())
    gauss_vals = list(phi_table.get("gaussian", {}).values())

    ksg_mean = float(np.mean(ksg_vals)) if ksg_vals else float("nan")
    hist_mean = float(np.mean(hist_vals)) if hist_vals else float("nan")
    gauss_mean = float(np.mean(gauss_vals)) if gauss_vals else float("nan")

    if np.isfinite(ksg_mean) and np.isfinite(hist_mean):
        ratio = abs(ksg_mean - hist_mean) / (max(ksg_mean, hist_mean) + 1e-9)
        ksg_hist_agree = ratio < 0.20
    else:
        ksg_hist_agree = None

    lines.append(
        "**Interpretation:** "
        f"KSG mean Φ_spectral = {ksg_mean:.2f}, histogram = {hist_mean:.2f}, "
        f"Gaussian = {gauss_mean:.2f}. "
    )
    if ksg_hist_agree is True:
        lines[-1] += (
            "KSG and histogram are in the same ballpark (< 20% difference), "
            "supporting KSG as the primary estimator. "
        )
    elif ksg_hist_agree is False:
        lines[-1] += (
            "KSG and histogram show > 20% difference — flag for methodology review. "
        )
    if np.isfinite(gauss_mean) and np.isfinite(ksg_mean):
        if gauss_mean <= ksg_mean:
            lines[-1] += "Gaussian is at or below KSG as expected (closed-form lower bound). "
        else:
            lines[-1] += "Gaussian exceeds KSG — unexpected; may indicate finite-sample bias. "

    out_path.write_text("\n".join(lines) + "\n")
    _log.info("Wrote B2b summary: %s", out_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Analyze Phase 4 sweep outputs.")
    parser.add_argument(
        "--sweep",
        default=None,
        help="Sweep family to analyze (default: all known sweeps).",
    )
    parser.add_argument(
        "--outputs",
        default=str(REPO_ROOT / "outputs"),
        help="Root outputs directory (default: outputs/).",
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "default.yaml"),
        help="Path to YAML config.",
    )
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Skip bootstrap CI computation (faster; for quick inspections).",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        base_config = yaml.safe_load(f)

    outputs_dir = Path(args.outputs)
    sweeps = [args.sweep] if args.sweep else _STEADY_STATE_SWEEPS
    bootstrap_ci = not args.no_bootstrap

    for sweep in sweeps:
        _log.info("Analyzing sweep: %s", sweep)
        per_seed_df, cross_seed_df = _aggregate_sweep(
            sweep, outputs_dir, base_config, bootstrap_ci=bootstrap_ci
        )

        if per_seed_df.empty:
            _log.warning("No data found for sweep %s; skipping.", sweep)
            continue

        sweep_dir = outputs_dir / sweep
        sweep_dir.mkdir(parents=True, exist_ok=True)

        per_seed_path = sweep_dir / "per_seed_summary.csv"
        cross_path = sweep_dir / "cross_seed_summary.csv"
        per_seed_df.to_csv(per_seed_path, index=False)
        cross_seed_df.to_csv(cross_path, index=False)
        _log.info("  Wrote %s", per_seed_path)
        _log.info("  Wrote %s", cross_path)

        # Special summary documents.
        if sweep == "alignment_rule_sensitivity":
            _write_alignment_rule_summary(per_seed_df, cross_seed_df, outputs_dir)
        elif sweep == "sensitivity":
            _write_sensitivity_summary(per_seed_df, cross_seed_df, outputs_dir)

    # Part D pass/fail evaluation — estimator-agreement interpretation note (D11).
    # Per D11 (ESTIMATOR_DISAGREEMENT_VERDICT.md): histogram MI at W=40, n_bins=8, d≥4
    # operates at its log(W) saturation ceiling and has no within-condition signal content.
    # For the estimator ordering-agreement pass/fail criterion (phases.md line 426),
    # histogram results are evaluated ONLY on the sign of Φ differences across conditions
    # (e.g., Φ(condition_A) − Φ(condition_B) > 0 under histogram iff > 0 under KSG).
    # Within-condition rank correlations and magnitude comparisons between histogram and
    # KSG/Gaussian are NOT meaningful at this (W, d, n_bins) operating point and must NOT
    # be used as pass/fail evidence. See ESTIMATOR_DISAGREEMENT_VERDICT.md §Recommendation.
    print(
        "\n[Part D — estimator-agreement note]\n"
        "Histogram MI results interpreted on sign-of-across-condition-differences only "
        "(D11 / ESTIMATOR_DISAGREEMENT_VERDICT.md). Within-condition histogram ranks "
        "and magnitudes are saturated artefacts and are excluded from pass/fail evaluation."
    )

    print("analyze_sweep.py complete.")


if __name__ == "__main__":
    main()
