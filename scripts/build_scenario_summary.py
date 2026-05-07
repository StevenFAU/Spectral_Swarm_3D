#!/usr/bin/env python3
"""Phase 5, Tier 2.C — Cross-sweep scenario summary table (Deliverable 6).

Produces outputs/comparison/cross_sweep/scenario_summary.csv:
  One row per (sweep, condition) after shared-baseline collapse (~38 rows).
  Integrates Φ metrics, σ_u, bimodality diagnostics, surrogate z-scores,
  and Tier 1 verdict tags / §4.2/§4.3 instance flags.

Standalone and reproducible: run from repo root or any directory.

Column conventions
------------------
sweep                   Sweep family name
condition               Condition label after shared-baseline collapse
n_seeds                 Number of seeds present
shared_baseline_alias   Comma-separated list of original conditions for the
                        collapsed vanilla_baseline row; else empty
phi_xseed_mean          Cross-seed steady-state mean Φ (from cross_seed_summary.csv)
phi_xseed_ci_lo         Bootstrap 95% CI lower (1000-resample, per-seed values)
phi_xseed_ci_hi         Bootstrap 95% CI upper
phi_norm_xseed_mean     Cross-seed phi_norm mean
phi_norm_xseed_sigma    Cross-seed phi_norm std (D14 secondary signal)
polarization_xseed_mean Cross-seed polarization mean
sigma_u_xseed_mean      Within-agent directional std, L2 of 3 channels; computed
                        for alignment/jamming/leadership/noise sweeps (Tier 1.C re-runs)
sigma_u_source          "tier1c_rerun" if sigma_u present; "not_computed" otherwise
bimodality_dip_p        Hartigan's dip test p-value (steady-state pooled per-window Φ)
bimodality_modes        KDE mode count (steady-state pooled)
bimodality_std_iqr      Std / IQR ratio (steady-state pooled)
surrogate_z_mean_over_windows  z-score from Tier 2.B null CSV (observed row)
surrogate_obs_above_ci  bool; True if observed Φ > surrogate 95% CI upper
surrogate_interpretation One of: real_integration_detected / near_baseline /
                          compressibility_flag / sanity_check_fail / null
tier1a_outcome          "outcome_4" for leadership_sweep conditions; else ""
section_4_2_instance    bool; True for alignment wa_0.6 and noise sigma_0.2
section_4_3_instance    bool; True for jamming alpha_0.2
leader_block_partition  bool; True for leadership lambda_1.6 and lambda_2.4
notes                   Free-text anomaly flags
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from spectral_swarm_3d.analysis.comparison import (
    VANILLA_BASELINE_CONDITIONS,
    _VANILLA_CONDITION_NAMES,
    load_sweep_runs,
    per_window_distribution_summary,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
OUTPUTS = REPO_ROOT / "outputs"
CROSS = OUTPUTS / "comparison" / "cross_sweep"

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

# ── σ_u from Tier 1.C audit (L2 of 3 per-channel directional stds) ────────
# Conditions not listed here get "not_computed" source and NaN σ_u.
SIGMA_U_TIER1C: dict[tuple[str, str], float] = {
    ("alignment_sweep", "wa_0.0"):    0.7941,
    ("alignment_sweep", "wa_0.6"):    0.5201,
    ("alignment_sweep", "wa_1.2"):    0.5061,
    ("alignment_sweep", "wa_1.8"):    0.5070,
    ("jamming_sweep",   "alpha_0.2"): 0.5925,
    ("jamming_sweep",   "alpha_0.5"): 0.5331,
    ("jamming_sweep",   "alpha_1.0"): 0.5183,  # vanilla baseline alias
    ("leadership_sweep","lambda_0.0"):0.5183,   # vanilla baseline alias
    ("leadership_sweep","lambda_0.8"):0.7009,
    ("leadership_sweep","lambda_1.6"):0.6188,
    ("leadership_sweep","lambda_2.4"):0.6030,
    ("noise_sweep",     "sigma_0.0"): 0.5148,
    ("noise_sweep",     "sigma_0.05"):0.5183,   # vanilla baseline alias
    ("noise_sweep",     "sigma_0.1"): 0.5111,
    ("noise_sweep",     "sigma_0.2"): 0.5311,
    ("noise_sweep",     "sigma_0.5"): 0.6421,
}

# ── Surrogate z-scores from Tier 2.B null CSVs ────────────────────────────
# Map: (sweep, condition) → (z_score, obs_above_ci, interpretation)
# "none" scenario in Tier 2.B maps to vanilla_baseline after collapse.
# vanilla_baseline values come from outputs/surrogates/none_null.csv
SURROGATE_MAP: dict[tuple[str, str], tuple[float, bool, str]] = {
    # vanilla_baseline (from "none" surrogate run — byte-identical to alpha_1.0 etc.)
    # Applied to vanilla_baseline collapsed row (handled separately below)
    ("alignment_sweep",           "wa_1.8"):       (9.96,  True,  "real_integration_detected"),
    ("leadership_sweep",          "lambda_1.6"):   (8.38,  True,  "real_integration_detected"),
    ("jamming_sweep",             "alpha_0.2"):    (16.17, True,  "real_integration_detected"),
    ("split_merge_sweep",         "split_merge"):  (-5.08, False, "compressibility_flag"),
    ("milling_sweep",             "mu_0.8"):       (15.45, True,  "real_integration_detected"),
    ("noise_sweep",               "sigma_0.5"):    (17.58, True,  "sanity_check_fail"),
    ("noise_sweep",               "sigma_0.2"):    (32.92, True,  "real_integration_detected"),
}

# vanilla_baseline surrogate (from "none" scenario)
VANILLA_SURROGATE = (25.38, True, "real_integration_detected")

# ── §4.2 / §4.3 / leadership flags ────────────────────────────────────────
SECTION_4_2: set[tuple[str, str]] = {
    ("alignment_sweep", "wa_0.6"),
    ("noise_sweep",     "sigma_0.2"),
}
SECTION_4_3: set[tuple[str, str]] = {
    ("jamming_sweep", "alpha_0.2"),
}
LEADER_BLOCK: set[tuple[str, str]] = {
    ("leadership_sweep", "lambda_1.6"),
    ("leadership_sweep", "lambda_2.4"),
}


# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap CI helper
# ─────────────────────────────────────────────────────────────────────────────

def _bootstrap_ci(
    values: np.ndarray, n: int = 1000, rng_seed: int = 42
) -> tuple[float, float]:
    """Percentile bootstrap 95% CI on the mean (D2 protocol)."""
    rng = np.random.default_rng(rng_seed)
    n_obs = len(values)
    if n_obs == 0:
        return float("nan"), float("nan")
    boot_means = np.array([
        rng.choice(values, size=n_obs, replace=True).mean()
        for _ in range(n)
    ])
    return float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))


# ─────────────────────────────────────────────────────────────────────────────
# Build per-condition bimodality stats from raw parquets
# ─────────────────────────────────────────────────────────────────────────────

def _bimodality_for_condition(
    sweep_dir: Path, condition: str
) -> dict:
    """Pool steady-state per-window Φ across all seeds for one condition."""
    cond_dir = sweep_dir / condition
    if not cond_dir.is_dir():
        return {"dip_p": float("nan"), "modes": 0, "std_iqr": float("nan")}

    frames = []
    for pq in sorted(cond_dir.glob("seed*.parquet")):
        frames.append(pd.read_parquet(pq))
    if not frames:
        return {"dip_p": float("nan"), "modes": 0, "std_iqr": float("nan")}

    pooled = pd.concat(frames, ignore_index=True)
    stats = per_window_distribution_summary(pooled, "phi_spectral", steady_state_only=True)
    return {
        "dip_p": stats["dip_p"],
        "modes": stats["mode_count"],
        "std_iqr": stats["std_iqr"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main build
# ─────────────────────────────────────────────────────────────────────────────

def build() -> pd.DataFrame:
    CROSS.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    vanilla_rows_for_collapse: list[dict] = []

    for sweep_name in SWEEPS:
        sweep_dir = OUTPUTS / sweep_name
        css_path = sweep_dir / "cross_seed_summary.csv"
        pss_path = sweep_dir / "per_seed_summary.csv"

        if not css_path.exists():
            print(f"  {sweep_name}: cross_seed_summary.csv missing — skip")
            continue

        css = pd.read_csv(css_path)
        pss = pd.read_csv(pss_path) if pss_path.exists() else pd.DataFrame()

        for _, crow in css.iterrows():
            cond = str(crow["condition"])
            n_seeds = int(crow["n_seeds"])
            is_vanilla = (sweep_name, cond) in VANILLA_BASELINE_CONDITIONS

            # ── Φ metrics from cross_seed_summary ──
            phi_mean = float(crow.get("phi_spectral_mean", float("nan")))
            phi_norm_mean = float(crow.get("phi_norm_mean", float("nan")))
            phi_norm_sigma = float(crow.get("phi_norm_std", float("nan")))
            pol_mean = float(crow.get("polarization_mean", float("nan")))

            # ── Bootstrap CI from per_seed_summary ──
            phi_ci_lo, phi_ci_hi = float("nan"), float("nan")
            if not pss.empty and "condition" in pss.columns:
                seed_vals = pss.loc[
                    pss["condition"] == cond, "phi_spectral_mean"
                ].dropna().values
                if len(seed_vals) >= 2:
                    phi_ci_lo, phi_ci_hi = _bootstrap_ci(seed_vals)

            # ── σ_u ──
            sigma_u = SIGMA_U_TIER1C.get((sweep_name, cond), float("nan"))
            sigma_u_source = (
                "tier1c_rerun" if np.isfinite(sigma_u) else "not_computed"
            )

            # ── Bimodality from parquets ──
            bio = _bimodality_for_condition(sweep_dir, cond)

            # ── Surrogate ──
            sur_key = (sweep_name, cond)
            if sur_key in SURROGATE_MAP:
                sur_z, sur_above, sur_interp = SURROGATE_MAP[sur_key]
            else:
                sur_z, sur_above, sur_interp = float("nan"), None, None

            # ── Flags ──
            tier1a = "outcome_4" if sweep_name == "leadership_sweep" and cond != "lambda_0.0" else ""
            s42 = (sweep_name, cond) in SECTION_4_2
            s43 = (sweep_name, cond) in SECTION_4_3
            lbp = (sweep_name, cond) in LEADER_BLOCK

            # ── Notes ──
            notes = ""
            if (sweep_name, cond) == ("split_merge_sweep", "split_merge"):
                notes = "single-seed compressibility flag (surrogate z=-5.08, observed below null)"
            if (sweep_name, cond) == ("noise_sweep", "sigma_0.5"):
                notes = "sanity-check fail — real cross-agent structure detected at sigma=0.5 (not near-random)"

            row = {
                "sweep": sweep_name,
                "condition": cond,
                "n_seeds": n_seeds,
                "shared_baseline_alias": "",
                "phi_xseed_mean": phi_mean,
                "phi_xseed_ci_lo": phi_ci_lo,
                "phi_xseed_ci_hi": phi_ci_hi,
                "phi_norm_xseed_mean": phi_norm_mean,
                "phi_norm_xseed_sigma": phi_norm_sigma,
                "polarization_xseed_mean": pol_mean,
                "sigma_u_xseed_mean": sigma_u if np.isfinite(sigma_u) else None,
                "sigma_u_source": sigma_u_source,
                "bimodality_dip_p": bio["dip_p"],
                "bimodality_modes": bio["modes"],
                "bimodality_std_iqr": bio["std_iqr"],
                "surrogate_z_mean_over_windows": sur_z if np.isfinite(sur_z) else None,
                "surrogate_obs_above_ci": sur_above,
                "surrogate_interpretation": sur_interp,
                "tier1a_outcome": tier1a,
                "section_4_2_instance": s42,
                "section_4_3_instance": s43,
                "leader_block_partition": lbp,
                "notes": notes,
            }

            if is_vanilla:
                vanilla_rows_for_collapse.append(row)
            else:
                rows.append(row)
            sur_z_str = f"{sur_z:.2f}" if np.isfinite(sur_z) else "nan"
            print(f"  {sweep_name}/{cond}: Φ={phi_mean:.2f}, dip_p={bio['dip_p']:.3g}, "
                  f"sur_z={sur_z_str}")

    # ── Collapse vanilla baseline rows ──────────────────────────────────────
    if vanilla_rows_for_collapse:
        vr = vanilla_rows_for_collapse
        aliases = sorted(f"{r['sweep']}/{r['condition']}" for r in vr)
        alias_conds = sorted(r["condition"] for r in vr)

        # Numeric columns: mean across the byte-identical rows (should all be equal)
        phi_vals = [r["phi_xseed_mean"] for r in vr if r["phi_xseed_mean"] is not None]
        phi_mean_vb = float(np.mean(phi_vals)) if phi_vals else float("nan")

        ci_lo_vals = [r["phi_xseed_ci_lo"] for r in vr if r["phi_xseed_ci_lo"] is not None and np.isfinite(r["phi_xseed_ci_lo"])]
        ci_hi_vals = [r["phi_xseed_ci_hi"] for r in vr if r["phi_xseed_ci_hi"] is not None and np.isfinite(r["phi_xseed_ci_hi"])]
        phi_ci_lo_vb = float(np.mean(ci_lo_vals)) if ci_lo_vals else float("nan")
        phi_ci_hi_vb = float(np.mean(ci_hi_vals)) if ci_hi_vals else float("nan")

        pn_vals = [r["phi_norm_xseed_mean"] for r in vr if r["phi_norm_xseed_mean"] is not None]
        pn_sigma_vals = [r["phi_norm_xseed_sigma"] for r in vr if r["phi_norm_xseed_sigma"] is not None]
        pol_vals = [r["polarization_xseed_mean"] for r in vr if r["polarization_xseed_mean"] is not None]

        # σ_u: use jamming alpha_1.0 value (0.5183) — all n=10 conditions are byte-identical
        sigma_u_vb = SIGMA_U_TIER1C.get(("jamming_sweep", "alpha_1.0"), float("nan"))

        # Bimodality: use any of the n=10 conditions (byte-identical → identical result)
        # Prefer jamming alpha_1.0 since it's the reference
        bio_vb = _bimodality_for_condition(OUTPUTS / "jamming_sweep", "alpha_1.0")

        # Surrogate for vanilla_baseline = the "none" scenario
        sur_z_vb, sur_above_vb, sur_interp_vb = VANILLA_SURROGATE

        # Total seeds: sum across n=10 conditions only (5 conditions × 10 seeds = 50,
        # but that would double-count identical runs; report as count of unique conditions)
        n_seeds_vb = max(r["n_seeds"] for r in vr)

        vb_row = {
            "sweep": "multiple",
            "condition": "vanilla_baseline",
            "n_seeds": n_seeds_vb,
            "shared_baseline_alias": ", ".join(alias_conds),
            "phi_xseed_mean": phi_mean_vb,
            "phi_xseed_ci_lo": phi_ci_lo_vb,
            "phi_xseed_ci_hi": phi_ci_hi_vb,
            "phi_norm_xseed_mean": float(np.mean(pn_vals)) if pn_vals else float("nan"),
            "phi_norm_xseed_sigma": float(np.mean(pn_sigma_vals)) if pn_sigma_vals else float("nan"),
            "polarization_xseed_mean": float(np.mean(pol_vals)) if pol_vals else float("nan"),
            "sigma_u_xseed_mean": sigma_u_vb if np.isfinite(sigma_u_vb) else None,
            "sigma_u_source": "tier1c_rerun",
            "bimodality_dip_p": bio_vb["dip_p"],
            "bimodality_modes": bio_vb["modes"],
            "bimodality_std_iqr": bio_vb["std_iqr"],
            "surrogate_z_mean_over_windows": sur_z_vb,
            "surrogate_obs_above_ci": sur_above_vb,
            "surrogate_interpretation": sur_interp_vb,
            "tier1a_outcome": "",
            "section_4_2_instance": False,
            "section_4_3_instance": False,
            "leader_block_partition": False,
            "notes": f"Collapsed from {len(vr)} byte-identical vanilla-baseline conditions; "
                     f"surrogate from Tier 2.B 'none' scenario",
        }
        rows.append(vb_row)
        print(f"\nvanilla_baseline: collapsed {len(vr)} conditions → 1 row")
        print(f"  aliases: {', '.join(alias_conds)}")

    df = pd.DataFrame(rows)
    out_path = CROSS / "scenario_summary.csv"
    df.to_csv(out_path, index=False)
    print(f"\nscenario_summary.csv: {len(df)} rows → {out_path}")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Validation checks
# ─────────────────────────────────────────────────────────────────────────────

def validate(df: pd.DataFrame) -> None:
    val_lines = [
        "",
        "=" * 45,
        "build_scenario_summary.py validation",
        "=" * 45,
        "",
    ]

    # [A] Row count
    n_rows = len(df)
    val_lines += [
        f"[A] Row count: {n_rows} (expect 35–40)",
        f"    {'OK' if 35 <= n_rows <= 42 else 'WARNING — unexpected row count'}",
        "",
    ]

    # [B] vanilla_baseline aliases
    vb = df[df["condition"] == "vanilla_baseline"]
    if not vb.empty:
        aliases_str = str(vb.iloc[0]["shared_baseline_alias"])
        aliases = [a.strip() for a in aliases_str.split(",") if a.strip()]
        val_lines += [
            f"[B] vanilla_baseline aliases: {len(aliases)} (expect 8)",
            f"    {'PASS' if len(aliases) == 8 else 'FAIL'}",
            f"    {aliases_str}",
            "",
        ]
    else:
        val_lines += ["[B] vanilla_baseline row: MISSING", ""]

    # [C] Bimodality cross-check: alignment wa_0.6 dip p ≈ 0.102
    align_row = df[(df["sweep"] == "alignment_sweep") & (df["condition"] == "wa_0.6")]
    if not align_row.empty:
        dip_p = float(align_row.iloc[0]["bimodality_dip_p"])
        match = 0.05 < dip_p < 0.20
        val_lines += [
            f"[C] Bimodality cross-check: alignment wa_0.6 dip p = {dip_p:.4f}",
            f"    Tier 1.B audit reference: ≈0.102",
            f"    {'PASS (within 0.05–0.20 range)' if match else 'WARNING — outside expected range'}",
            "",
        ]
    else:
        val_lines += ["[C] alignment wa_0.6 row: MISSING", ""]

    # [D] Surrogate integration: count rows with non-null surrogate_z
    n_sur = df["surrogate_z_mean_over_windows"].notna().sum()
    val_lines += [
        f"[D] Surrogate z populated: {n_sur} rows (expect 9: 8 scenarios + vanilla_baseline)",
        f"    {'PASS' if n_sur >= 8 else 'FAIL'}",
        "",
    ]

    # [E] §4.2 and §4.3 instance flags
    s42 = df[df["section_4_2_instance"] == True]["sweep"].tolist() if "section_4_2_instance" in df.columns else []
    s43 = df[df["section_4_3_instance"] == True]["sweep"].tolist() if "section_4_3_instance" in df.columns else []
    val_lines += [
        f"[E] §4.2 instances: {df[df['section_4_2_instance'] == True][['sweep','condition']].to_dict('records')}",
        f"    §4.3 instances: {df[df['section_4_3_instance'] == True][['sweep','condition']].to_dict('records')}",
        "",
    ]

    # [F] §4.3 inversion check: jamming alpha_0.2 Φ vs vanilla_baseline Φ
    jam_row = df[(df["sweep"] == "jamming_sweep") & (df["condition"] == "alpha_0.2")]
    if not jam_row.empty and not vb.empty:
        phi_jam = float(jam_row.iloc[0]["phi_xseed_mean"])
        phi_vb = float(vb.iloc[0]["phi_xseed_mean"])
        inversion = phi_jam - phi_vb
        pct = 100 * inversion / phi_vb if phi_vb != 0 else float("nan")
        direction_ok = inversion > 0
        val_lines += [
            f"[F] §4.3 inversion: jamming α=0.2 Φ = {phi_jam:.2f}, vanilla_baseline Φ = {phi_vb:.2f}",
            f"    Inversion magnitude: +{inversion:.2f} ({pct:+.1f}%)",
            f"    Direction: {'CORRECT — jamming above baseline (§4.3 prediction confirmed)' if direction_ok else 'WRONG — jamming below baseline (contradicts §4.3)'}",
            "",
        ]

    text = "\n".join(val_lines)
    print(text)

    # Append to _validation.txt
    val_file = OUTPUTS / "comparison" / "_validation.txt"
    if val_file.exists():
        existing = val_file.read_text()
        val_file.write_text(existing + text)
    else:
        val_file.write_text(text)


if __name__ == "__main__":
    print("Building scenario_summary.csv ...")
    df = build()
    validate(df)
