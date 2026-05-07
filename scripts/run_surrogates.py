"""Run Phase 5 Tier 2.B circular-shift surrogate nulls for 8 scenarios (D1).

Iterates over the eight pre-registered scenarios (7 primary per Phase5.md plus
noise σ=0.2 added per Tier 1.C audit recommendation #5), runs circular-shift
surrogate null testing for each, and writes:

  outputs/surrogates/<scenario>_null.csv   -- per-scenario null distribution
  outputs/surrogates/README_summary.md     -- sanity-check verdict + summary table

The noise σ=0.5 scenario is the surrogate-method positive control. If its
sanity check fails (observed Phi outside the surrogate 95% CI), the script
flags the method as broken and does NOT interpret other scenarios.

Usage:
    python scripts/run_surrogates.py
    python scripts/run_surrogates.py --n-shuffles 10 --rng-seed 0
    python scripts/run_surrogates.py --scenarios none,noise_sigma_0.5
    python scripts/run_surrogates.py --outputs-dir outputs/surrogates
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from spectral_swarm_3d.analysis.surrogates import run_surrogate_test  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scenario registry: 7 primary (Phase5.md) + 1 per Tier 1.C audit rec. #5
# ---------------------------------------------------------------------------

_OUTPUTS_ROOT = REPO_ROOT / "outputs"

# Each entry: (scenario_label, sweep_subdir, condition)
# Config and scenario_name are loaded from the seed's metadata JSON (D6).
_SCENARIO_REGISTRY: list[tuple[str, str, str]] = [
    # none baseline — using jamming_sweep/alpha_1.0 (byte-identical vanilla boids;
    # D6 shared-baseline finding: 8 conditions are byte-identical, commit fec6079).
    ("none",               "jamming_sweep",      "alpha_1.0"),
    # 7 primary scenarios
    ("alignment_wa_1.8",   "alignment_sweep",    "wa_1.8"),
    ("leadership_lam_1.6", "leadership_sweep",   "lambda_1.6"),
    ("jamming_alpha_0.2",  "jamming_sweep",      "alpha_0.2"),
    ("split_merge",        "split_merge_sweep",  "split_merge"),
    ("milling_mu_0.8",     "milling_sweep",      "mu_0.8"),
    ("noise_sigma_0.5",    "noise_sweep",        "sigma_0.5"),
    # +1 per Tier 1.C audit recommendation #5 (noise σ=0.2 second §4.2 instance)
    ("noise_sigma_0.2",    "noise_sweep",        "sigma_0.2"),
]

_SANITY_CHECK_SCENARIO = "noise_sigma_0.5"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 5 Tier 2.B surrogate null testing.")
    p.add_argument("--n-shuffles", type=int, default=10, metavar="N",
                   help="Number of circular-shift surrogates per scenario (default: 10).")
    p.add_argument("--rng-seed", type=int, default=0, metavar="S",
                   help="RNG seed for surrogate shifts (default: 0).")
    p.add_argument("--seed", type=int, default=0, metavar="SEED",
                   help="Simulation seed to analyse (default: 0, pre-committed).")
    p.add_argument("--scenarios", type=str, default="",
                   help="Comma-separated scenario labels to run (default: all 8).")
    p.add_argument("--outputs-dir", type=str, default=str(REPO_ROOT / "outputs" / "surrogates"),
                   help="Directory for null CSVs and README_summary.md.")
    return p.parse_args()


def _observed_above_surrogate(row: dict[str, Any]) -> bool:
    return float(row["observed_phi"]) > float(row["surrogate_95ci_hi"])


def _sanity_pass(row: dict[str, Any]) -> bool:
    lo = float(row["surrogate_95ci_lo"])
    hi = float(row["surrogate_95ci_hi"])
    obs = float(row["observed_phi"])
    return lo <= obs <= hi


def _interpret(label: str, row: dict[str, Any], sanity_scenario: str) -> str:
    if label == sanity_scenario:
        return "sanity-check pass" if _sanity_pass(row) else "sanity-check fail"
    obs = float(row["observed_phi"])
    lo = float(row["surrogate_95ci_lo"])
    hi = float(row["surrogate_95ci_hi"])
    if obs > hi:
        return "real integration detected"
    if obs < lo:
        return "compressibility flag"
    return "near-baseline"


def _write_readme(
    summary_rows: list[dict[str, Any]],
    sanity_verdict: str,
    outputs_dir: Path,
    n_shuffles: int,
    rng_seed: int,
) -> None:
    """Write outputs/surrogates/README_summary.md per Phase5.md §141 spec."""
    lines: list[str] = []
    lines.append("# Tier 2.B Surrogate Null Summary\n")
    lines.append("Phase 5 — circular-shift surrogate null distributions (D1)\n")
    lines.append(f"n_shuffles={n_shuffles}, rng_seed={rng_seed}, simulation_seed=0\n\n")

    # --- Section 1: Sanity-check verdict (Phase5.md §141 first section) ---
    lines.append("## Sanity-Check Verdict (noise σ=0.5)\n\n")
    sanity_row = next((r for r in summary_rows if r["scenario"] == _SANITY_CHECK_SCENARIO), None)
    if sanity_row is None:
        lines.append("**SKIP** — noise σ=0.5 scenario was not run in this session.\n\n")
    else:
        obs = sanity_row["observed_phi"]
        lo = sanity_row["surrogate_95ci_lo"]
        hi = sanity_row["surrogate_95ci_hi"]
        z = sanity_row["z_score"]
        lines.append(f"**{sanity_verdict}**\n\n")
        lines.append(
            f"Observed Φ = {obs:.3f}. Surrogate 95% CI = [{lo:.3f}, {hi:.3f}]. "
            f"z = {z:.2f}.\n\n"
        )
        if sanity_verdict == "PASS":
            lines.append(
                "The noise σ=0.5 observed Φ falls within the surrogate distribution's 95% CI. "
                "The circular-shift protocol is correctly destroying cross-agent temporal "
                "dependence without introducing spurious structure. Results for other "
                "scenarios are interpretable.\n\n"
            )
        else:
            lines.append(
                "**FAIL: The noise σ=0.5 observed Φ falls OUTSIDE the surrogate 95% CI.** "
                "The circular-shift protocol may not be working correctly. "
                "Scenario-level results below are reported for completeness but "
                "should NOT be interpreted as scientific findings until the method is "
                "debugged. See Anomalies section.\n\n"
            )

    # --- Section 2: Per-scenario summary table ---
    lines.append("## Per-Scenario Summary Table\n\n")
    lines.append("| scenario | observed_phi | surrogate_mean | "
                 "surrogate_95ci_lo | surrogate_95ci_hi | z_score | "
                 "observed_above_surrogate | interpretation |\n")
    lines.append("|---|---|---|---|---|---|---|---|\n")
    for row in summary_rows:
        above = _observed_above_surrogate(row)
        interp = _interpret(row["scenario"], row, _SANITY_CHECK_SCENARIO)
        lines.append(
            f"| {row['scenario']} "
            f"| {row['observed_phi']:.3f} "
            f"| {row['surrogate_mean']:.3f} "
            f"| {row['surrogate_95ci_lo']:.3f} "
            f"| {row['surrogate_95ci_hi']:.3f} "
            f"| {row['z_score']:.2f} "
            f"| {above} "
            f"| {interp} |\n"
        )
    lines.append("\n")

    # --- Section 3: Compressibility cross-reference (§4.3, jamming α=0.2) ---
    lines.append("## Compressibility Cross-Reference — Jamming α=0.2 (§4.3)\n\n")
    jam_row = next((r for r in summary_rows if r["scenario"] == "jamming_alpha_0.2"), None)
    if jam_row is None:
        lines.append("jamming_alpha_0.2 was not run in this session.\n\n")
    else:
        obs = jam_row["observed_phi"]
        lo = jam_row["surrogate_95ci_lo"]
        hi = jam_row["surrogate_95ci_hi"]
        z = jam_row["z_score"]
        if obs < lo:
            direction = "observed < surrogate (compressibility flag)"
            interp_text = (
                "The observed Φ at jamming α=0.2 falls **below** the surrogate null "
                "distribution. This is the §4.3 compressibility mechanism at the single-seed "
                "level: fragmentation suppresses within-window informational structure to "
                f"below what cross-agent temporal independence alone would produce. "
                f"Observed={obs:.3f}, surrogate 95% CI=[{lo:.3f}, {hi:.3f}], z={z:.2f}. "
                "Corroborates Tier 1.A §4.3 finding at surrogate level."
            )
        elif obs > hi:
            direction = "observed > surrogate (above null)"
            interp_text = (
                "The observed Φ at jamming α=0.2 falls **above** the surrogate null "
                "distribution. This means the jamming condition retains detectable "
                "cross-agent temporal structure beyond what temporal independence would "
                f"produce. Observed={obs:.3f}, surrogate 95% CI=[{lo:.3f}, {hi:.3f}], "
                f"z={z:.2f}. This is the opposite direction from the §4.3 compressibility "
                "prediction — flag for investigation."
            )
        else:
            direction = "observed ≈ surrogate (near-baseline)"
            interp_text = (
                "The observed Φ at jamming α=0.2 falls within the surrogate null "
                f"distribution. Observed={obs:.3f}, surrogate 95% CI=[{lo:.3f}, {hi:.3f}], "
                f"z={z:.2f}. No strong signal in either direction at single-seed level."
            )
        lines.append(f"**Direction: {direction}**\n\n")
        lines.append(interp_text + "\n\n")

    # --- Section 4: §4.2 candidate cross-reference (noise σ=0.2) ---
    lines.append("## §4.2 Candidate Cross-Reference — Noise σ=0.2\n\n")
    lines.append(
        "Added per Tier 1.C audit recommendation #5 (commit fec6079). "
        "Tests whether the second §4.2 instance (noise σ=0.2 bimodality, confirmed "
        "in cross-sweep audit with dip p=7.6e-6) shows observed Φ exceeding surrogate, "
        "indicating real per-window structure beyond cross-agent temporal independence.\n\n"
    )
    n02_row = next((r for r in summary_rows if r["scenario"] == "noise_sigma_0.2"), None)
    if n02_row is None:
        lines.append("noise_sigma_0.2 was not run in this session.\n\n")
    else:
        obs = n02_row["observed_phi"]
        lo = n02_row["surrogate_95ci_lo"]
        hi = n02_row["surrogate_95ci_hi"]
        z = n02_row["z_score"]
        if obs > hi:
            lines.append(
                f"**Observed > surrogate (§4.2 signature supported).** "
                f"Observed Φ={obs:.3f} exceeds surrogate 95% CI upper bound {hi:.3f} "
                f"(z={z:.2f}). The noise σ=0.2 regime shows per-window temporal structure "
                "beyond what cross-agent independence would produce, corroborating the "
                "Tier 1.C audit's §4.2 bimodality finding at the surrogate level. "
                "The §4.2 candidate's empirical support is strengthened.\n\n"
            )
        elif lo <= obs <= hi:
            lines.append(
                f"**Observed ≈ surrogate (§4.2 candidate weakened).** "
                f"Observed Φ={obs:.3f} falls within the surrogate 95% CI [{lo:.3f}, {hi:.3f}] "
                f"(z={z:.2f}). The surrogate test does not detect per-window structure beyond "
                "temporal independence at noise σ=0.2 for this seed. The Tier 1.C §4.2 "
                "bimodality finding may be a single-seed artifact at seed 0, or the "
                "per-window structure exists but is not detectable with n_shuffles=10 "
                "at this granularity.\n\n"
            )
        else:
            lines.append(
                f"**Observed < surrogate.** "
                f"Observed Φ={obs:.3f} falls below surrogate 95% CI lower bound {lo:.3f} "
                f"(z={z:.2f}). Unexpected direction — flag for investigation.\n\n"
            )

    # --- Section 5: Framing-(b) note (D14 §139) ---
    lines.append("## Framing-(b) Note — Per-Window Structure (D14 §139)\n\n")
    lines.append(
        "For each coordinated scenario, reports whether observed Φ > surrogate "
        "at the per-window level. Even when the mean-over-windows Φ is compressed "
        "(coherent regimes suppress MI), the surrogate comparison can detect whether "
        "the per-window dynamical structure is real against the null. A positive result "
        "strengthens the framing-(b) reading (D14): Φ_spectral measures genuine "
        "within-window informational dependence, not just a mean-level artefact.\n\n"
    )
    coordinated_scenarios = [
        "alignment_wa_1.8", "leadership_lam_1.6", "milling_mu_0.8", "jamming_alpha_0.2"
    ]
    for sc in coordinated_scenarios:
        sc_row = next((r for r in summary_rows if r["scenario"] == sc), None)
        if sc_row is None:
            lines.append(f"- **{sc}**: not run.\n")
            continue
        obs = sc_row["observed_phi"]
        hi = sc_row["surrogate_95ci_hi"]
        lo = sc_row["surrogate_95ci_lo"]
        z = sc_row["z_score"]
        above = obs > hi
        lines.append(
            f"- **{sc}**: observed={obs:.3f}, surrogate 95% CI=[{lo:.3f}, {hi:.3f}], "
            f"z={z:.2f} → "
            f"{'observed > surrogate (framing-b supported)' if above else 'observed ≤ surrogate 95%CI upper (framing-b not confirmed at this threshold)'}\n"
        )
    lines.append("\n")

    # --- Section 6: Anomalies ---
    lines.append("## Anomalies\n\n")
    anomalies: list[str] = []
    for row in summary_rows:
        sc = row["scenario"]
        std = row["surrogate_std"]
        obs = row["observed_phi"]
        lo = row["surrogate_95ci_lo"]
        hi = row["surrogate_95ci_hi"]
        z = row["z_score"]

        if std == 0.0 or (std < 1e-6 and row.get("n_shuffles_actual", 10) > 1):
            anomalies.append(
                f"**{sc}**: surrogate_std≈0 — shuffle may not have shuffled. "
                "Check for axis bug in np.roll."
            )
        if not (lo <= obs <= hi) and abs(z) > 100:
            anomalies.append(
                f"**{sc}**: |z|={abs(z):.1f} — extreme z-score suggests scale mismatch "
                "between observed and surrogate pipelines."
            )
        match = row.get("parquet_match")
        if match is False:
            parquet_phi = row.get("parquet_phi_mean", float("nan"))
            anomalies.append(
                f"**{sc}**: parquet_match=False — re-run observed_phi={obs:.3f} vs "
                f"parquet_phi={parquet_phi:.3f}. Methodology consistency issue."
            )
        # Sanity check CI width: if CI contains zero and extends to 3× the observed value,
        # the null is too permissive
        ci_width = hi - lo
        if lo <= obs <= hi and ci_width > 3 * abs(obs) and obs > 0:
            anomalies.append(
                f"**{sc}**: surrogate 95% CI width={ci_width:.2f} is more than 3× the "
                f"observed value ({obs:.3f}) — null may be too permissive (sanity check "
                "would pass for any observed value)."
            )

    if anomalies:
        for a in anomalies:
            lines.append(f"- {a}\n")
    else:
        lines.append("No anomalies detected in any scenario's null distribution.\n")
    lines.append("\n")

    # --- Methodology note ---
    lines.append("## Methodology Note\n\n")
    lines.append(
        "**None baseline source**: jamming_sweep/alpha_1.0/seed0.parquet. "
        "This is byte-identical to the vanilla boids run (jam_alpha=1.0 → no "
        "scaling effect; confirmed by D6 shared-baseline finding, audit commit "
        "fec6079, VANILLA_BASELINE_CONDITIONS in comparison.py).\n\n"
    )
    lines.append(
        "**Surrogate protocol**: D1 circular shift. Each agent's (T, d) feature "
        "time series independently shifted by a uniform random offset over [0, T). "
        "Marginal distributions per agent are preserved exactly; cross-agent "
        "temporal dependence is destroyed. 10 shuffles per scenario, rng_seed=0.\n\n"
    )
    lines.append(
        "**Observed Phi source**: deterministic re-run from seed-0 telemetry "
        "(config loaded from metadata JSON per D6). Cross-checked against canonical "
        "parquet phi_spectral — see parquet_match column in null CSVs.\n\n"
    )

    readme_path = outputs_dir / "README_summary.md"
    readme_path.write_text("".join(lines))
    _log.info("Wrote %s", readme_path)


def main() -> None:
    args = _parse_args()
    outputs_dir = Path(args.outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Filter scenarios
    if args.scenarios:
        requested = set(args.scenarios.split(","))
        registry = [(lbl, sw, cond) for lbl, sw, cond in _SCENARIO_REGISTRY if lbl in requested]
        missing = requested - {lbl for lbl, _, _ in registry}
        if missing:
            _log.warning("Unknown scenario labels: %s", missing)
    else:
        registry = list(_SCENARIO_REGISTRY)

    scenario_labels = [lbl for lbl, _, _ in registry]
    _log.info(
        "Running %d scenarios with n_shuffles=%d rng_seed=%d simulation_seed=%d",
        len(registry), args.n_shuffles, args.rng_seed, args.seed,
    )

    all_results: dict[str, dict[str, Any]] = {}

    for scenario_label, sweep_subdir, condition in registry:
        sweep_dir = _OUTPUTS_ROOT / sweep_subdir
        _log.info("=== Scenario: %s (%s / %s) ===", scenario_label, sweep_subdir, condition)

        df = run_surrogate_test(
            scenario_label=scenario_label,
            sweep_dir=sweep_dir,
            condition=condition,
            seed=args.seed,
            rng_seed=args.rng_seed,
            n_shuffles=args.n_shuffles,
        )

        # Write per-scenario null CSV
        csv_path = outputs_dir / f"{scenario_label}_null.csv"
        df.to_csv(csv_path, index=False)
        _log.info("Wrote %s", csv_path)

        # Extract summary stats for README
        obs_row = df[df["kind"] == "observed"].iloc[0]
        all_results[scenario_label] = {
            "scenario": scenario_label,
            "observed_phi": float(obs_row["phi_spectral_mean"]),
            "surrogate_mean": float(obs_row["surrogate_mean"]),
            "surrogate_95ci_lo": float(obs_row["surrogate_95ci_lo"]),
            "surrogate_95ci_hi": float(obs_row["surrogate_95ci_hi"]),
            "z_score": float(obs_row["z_score"]),
            "surrogate_std": float(obs_row["surrogate_std"]),
            "parquet_phi_mean": float(obs_row["parquet_phi_mean"]),
            "parquet_match": obs_row["parquet_match"],
        }

    # Sanity-check verdict (gating result)
    sanity_verdict = "SKIP"
    if _SANITY_CHECK_SCENARIO in all_results:
        sanity_row = all_results[_SANITY_CHECK_SCENARIO]
        lo = sanity_row["surrogate_95ci_lo"]
        hi = sanity_row["surrogate_95ci_hi"]
        obs = sanity_row["observed_phi"]
        sanity_verdict = "PASS" if lo <= obs <= hi else "FAIL"

    _log.info("=== SANITY-CHECK VERDICT (noise σ=0.5): %s ===", sanity_verdict)

    if sanity_verdict == "FAIL":
        _log.warning(
            "Noise σ=0.5 sanity check FAILED. Observed Phi is outside the surrogate "
            "95%% CI. Do not interpret other scenarios' results until the method is "
            "debugged. See README_summary.md Anomalies section."
        )

    # Print per-scenario one-liners
    print(f"\n{'Scenario':<25} {'Obs Φ':>8} {'Surr μ':>8} {'95CI lo':>8} "
          f"{'95CI hi':>8} {'z':>6} {'Above?':>7} {'Match?':>7}")
    print("-" * 80)
    for lbl in scenario_labels:
        if lbl not in all_results:
            continue
        r = all_results[lbl]
        above = r["observed_phi"] > r["surrogate_95ci_hi"]
        print(
            f"{lbl:<25} {r['observed_phi']:>8.3f} {r['surrogate_mean']:>8.3f} "
            f"{r['surrogate_95ci_lo']:>8.3f} {r['surrogate_95ci_hi']:>8.3f} "
            f"{r['z_score']:>6.2f} {str(above):>7} {str(r['parquet_match']):>7}"
        )
    print()

    # Write README summary
    summary_rows = [all_results[lbl] for lbl in scenario_labels if lbl in all_results]
    _write_readme(
        summary_rows=summary_rows,
        sanity_verdict=sanity_verdict,
        outputs_dir=outputs_dir,
        n_shuffles=args.n_shuffles,
        rng_seed=args.rng_seed,
    )

    print(f"\nSANITY-CHECK VERDICT (noise σ=0.5): {sanity_verdict}")
    if sanity_verdict == "FAIL":
        print("WARNING: method validation failed — scenario results are provisional.")
    print(f"Outputs written to: {outputs_dir}")


if __name__ == "__main__":
    main()
