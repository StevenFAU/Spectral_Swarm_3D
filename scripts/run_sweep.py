"""Run all sweep conditions for a given sweep family.

Phase 4 implementation. See SpectralSwarm3DPhases.md §Phase 4, C3.

Usage
-----
Dry-run (print condition list, do not simulate)::

    python scripts/run_sweep.py --sweep alignment_sweep --dry-run

Run one seed for smoke-testing::

    python scripts/run_sweep.py --sweep alignment_sweep --seeds 0

Full sweep (default seeds from condition list)::

    python scripts/run_sweep.py --sweep alignment_sweep

Available sweep families
------------------------
alignment_sweep, leadership_sweep, jamming_sweep, split_merge_sweep,
milling_sweep, noise_sweep, sensitivity, n_sensitivity_N80,
n_sensitivity_N160, w_sensitivity, alignment_rule_sensitivity
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, NamedTuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.aggregation import analyze_run  # noqa: E402
from spectral_swarm_3d.model import BoidSwarmModel3D  # noqa: E402
from spectral_swarm_3d.telemetry import record_environment  # noqa: E402

_log = logging.getLogger(__name__)

# Applied on top of base config for every sweep run (B2 §3.7 orchestration defaults).
# stride=5 per B2 ("stride=5 for sweep orchestration").
_SWEEP_DEFAULTS: dict[str, Any] = {
    "stride": 5,
}

# Seeds for primary sweeps (10) and sensitivity/robustness sweeps (5).
_PRIMARY_SEEDS = list(range(10))
_SENSITIVITY_SEEDS = list(range(5))


class Condition(NamedTuple):
    """A single (sweep, condition, seeds) triple with its config overrides."""

    sweep: str
    name: str
    scenario: str
    config_overrides: dict[str, Any]
    seeds: list[int]


def _build_conditions(sweep: str, outputs_dir: Path) -> list[Condition]:
    """Return the ordered list of Condition objects for *sweep*."""
    conditions: list[Condition] = []

    if sweep == "alignment_sweep":
        for wa in [0.0, 0.6, 1.2, 1.8]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"wa_{wa}",
                scenario="none",
                config_overrides={"w_a": wa},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "leadership_sweep":
        for lam in [0.0, 0.8, 1.6, 2.4]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"lambda_{lam}",
                scenario="leader",
                config_overrides={"leader_strength": lam},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "jamming_sweep":
        for alpha in [1.0, 0.5, 0.2]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"alpha_{alpha}",
                scenario="jamming",
                config_overrides={"jam_alpha": alpha},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "split_merge_sweep":
        for scenario_name, cond_name in [("none", "none"), ("split_merge", "split_merge")]:
            conditions.append(Condition(
                sweep=sweep,
                name=cond_name,
                scenario=scenario_name,
                config_overrides={},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "milling_sweep":
        for mu in [0.0, 0.4, 0.8, 1.2]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"mu_{mu}",
                scenario="milling",
                config_overrides={"milling_mu": mu},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "noise_sweep":
        for sigma in [0.0, 0.05, 0.1, 0.2, 0.5]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"sigma_{sigma}",
                scenario="none",
                config_overrides={"noise_sigma": sigma},
                seeds=_PRIMARY_SEEDS,
            ))

    elif sweep == "sensitivity":
        # 9-combination matrix: {ksg, histogram, gaussian} × {kinematic, vxvyvz, full} (C3).
        for est in ["ksg", "histogram", "gaussian"]:
            for feat in ["kinematic", "vxvyvz", "full"]:
                # W=50 for d=6 full feature set per B2.
                w_override = 50 if feat == "full" else 40
                conditions.append(Condition(
                    sweep=sweep,
                    name=f"{est}_{feat}",
                    scenario="none",
                    config_overrides={"estimator": est, "feature_set": feat, "W": w_override},
                    seeds=_SENSITIVITY_SEEDS,
                ))

    elif sweep == "n_sensitivity_N80":
        for wa in [0.0, 0.6, 1.2, 1.8]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"wa_{wa}",
                scenario="none",
                config_overrides={"N": 80, "w_a": wa},
                seeds=_SENSITIVITY_SEEDS,
            ))

    elif sweep == "n_sensitivity_N160":
        for wa in [0.0, 0.6, 1.2, 1.8]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"wa_{wa}",
                scenario="none",
                config_overrides={"N": 160, "w_a": wa},
                seeds=_SENSITIVITY_SEEDS,
            ))

    elif sweep == "w_sensitivity":
        for W_val in [30, 40, 50, 60]:
            conditions.append(Condition(
                sweep=sweep,
                name=f"W{W_val}",
                scenario="none",
                config_overrides={"W": W_val},
                seeds=_SENSITIVITY_SEEDS,
            ))

    elif sweep == "alignment_rule_sensitivity":
        # B2a: mean vs sum alignment at calibrated w_a=1.0, baseline scenario (A6).
        for rule in ["mean", "sum"]:
            conditions.append(Condition(
                sweep=sweep,
                name=rule,
                scenario="none",
                config_overrides={"alignment_rule": rule, "w_a": 1.0},
                seeds=_SENSITIVITY_SEEDS,
            ))

    else:
        raise ValueError(
            f"Unknown sweep {sweep!r}. Available: alignment_sweep, leadership_sweep, "
            "jamming_sweep, split_merge_sweep, milling_sweep, noise_sweep, sensitivity, "
            "n_sensitivity_N80, n_sensitivity_N160, w_sensitivity, alignment_rule_sensitivity"
        )

    return conditions


def _effective_config(base_config: dict, condition: Condition) -> dict:
    """Merge base config with sweep defaults and condition-specific overrides."""
    cfg = {**base_config, **_SWEEP_DEFAULTS, **condition.config_overrides}
    # Inject scenario into config for downstream event-phase detection.
    cfg["scenario"] = condition.scenario
    return cfg


def _write_metadata(
    meta_path: Path,
    cfg: dict,
    seed: int,
    condition: Condition,
    repo_root: Path,
) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "seed": seed,
        "scenario": condition.scenario,
        "sweep": condition.sweep,
        "condition": condition.name,
        "feature_set": str(cfg.get("feature_set", "kinematic")),
        "estimator": str(cfg.get("estimator", "ksg")),
        "config": cfg,
        "environment": record_environment(repo_root),
    }
    with meta_path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)


def _run_one(
    condition: Condition,
    seed: int,
    base_config: dict,
    outputs_dir: Path,
    repo_root: Path,
    dry_run: bool = False,
) -> str:
    """Execute one (condition, seed) run. Returns a status string."""
    out_dir = outputs_dir / condition.sweep / condition.name
    parquet_path = out_dir / f"seed{seed}.parquet"
    meta_path = out_dir / f"seed{seed}.metadata.json"

    if parquet_path.exists() and meta_path.exists():
        return "skipped"

    cfg = _effective_config(base_config, condition)

    if parquet_path.exists() and not meta_path.exists():
        # Orphan from pre-metadata run: regenerate metadata without re-simulating.
        _write_metadata(meta_path, cfg, seed, condition, repo_root)
        return "metadata_regenerated"

    if dry_run:
        return "dry_run"

    out_dir.mkdir(parents=True, exist_ok=True)

    # Write telemetry to a temp file, analyze in-process, then delete.
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, dir=out_dir) as tmp_f:
        tel_path = Path(tmp_f.name)

    try:
        model = BoidSwarmModel3D(
            cfg, scenario_name=condition.scenario, seed=seed, telemetry_path=tel_path
        )
        model.run(T=int(cfg.get("T", 500)))

        run_df = analyze_run(str(tel_path), cfg)
        run_df.to_parquet(parquet_path, index=False)

        _write_metadata(meta_path, cfg, seed, condition, repo_root)
    finally:
        tel_path.unlink(missing_ok=True)

    return "completed"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Run a Phase 4 sweep family.")
    parser.add_argument(
        "--sweep",
        required=True,
        help="Sweep family name (e.g. alignment_sweep, sensitivity, …).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=None,
        metavar="N",
        help="Override seed list for all conditions (e.g. --seeds 0 for smoke test).",
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "default.yaml"),
        help="Path to YAML config (default: configs/default.yaml).",
    )
    parser.add_argument(
        "--outputs",
        default=str(REPO_ROOT / "outputs"),
        help="Root outputs directory (default: outputs/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print condition list and exit without simulating.",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        base_config = yaml.safe_load(f)

    outputs_dir = Path(args.outputs)
    conditions = _build_conditions(args.sweep, outputs_dir)

    if args.seeds is not None:
        conditions = [Condition(c.sweep, c.name, c.scenario, c.config_overrides, args.seeds)
                      for c in conditions]

    # Dry-run: list conditions and exit.
    if args.dry_run:
        total = sum(len(c.seeds) for c in conditions)
        print(f"Sweep: {args.sweep}  ({len(conditions)} conditions, {total} total runs)")
        for cond in conditions:
            cfg_preview = {**_SWEEP_DEFAULTS, **cond.config_overrides}
            print(f"  {cond.name:30s}  scenario={cond.scenario:12s}  "
                  f"seeds={cond.seeds}  overrides={cfg_preview}")
        return

    n_completed = 0
    n_skipped = 0
    n_meta_regen = 0
    n_failed = 0
    total = sum(len(c.seeds) for c in conditions)
    run_count = 0

    for cond in conditions:
        for seed in cond.seeds:
            run_count += 1
            out_dir = outputs_dir / cond.sweep / cond.name
            error_path = out_dir / f"seed{seed}.ERROR.txt"
            label = f"[{run_count}/{total}] {cond.sweep}/{cond.name}/seed{seed}"
            try:
                status = _run_one(cond, seed, base_config, outputs_dir, REPO_ROOT)
                if status == "completed":
                    n_completed += 1
                    _log.info("%s  → completed", label)
                elif status == "skipped":
                    n_skipped += 1
                    _log.info("%s  → skipped (already complete)", label)
                elif status == "metadata_regenerated":
                    n_meta_regen += 1
                    _log.info("%s  → metadata regenerated (orphan parquet)", label)
            except Exception:
                n_failed += 1
                tb = traceback.format_exc()
                out_dir.mkdir(parents=True, exist_ok=True)
                error_path.write_text(
                    f"Config: {_effective_config(base_config, cond)}\n\n{tb}"
                )
                _log.error("%s  → FAILED (see %s)", label, error_path)

    print(
        f"\nSweep {args.sweep} complete: "
        f"{n_completed} completed, {n_skipped} skipped, "
        f"{n_meta_regen} metadata-regenerated, {n_failed} failed."
    )
    if n_failed > 0:
        print(f"  {n_failed} run(s) failed — see ERROR.txt files in outputs/.")
        sys.exit(1)


if __name__ == "__main__":
    main()
