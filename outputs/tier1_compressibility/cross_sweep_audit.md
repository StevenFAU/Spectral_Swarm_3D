# Phase 5 Tier 1.C — Cross-Sweep Compressibility Audit

**Date:** 2026-05-06.
**Pipeline:** `outputs/tier1_compressibility/_make_audit.py`
(`audit_aggregates.json`, `cross_sweep_panel.png`).
**Code at HEAD:** `6baae1a` (Phase 5 post-audit consistency pass; Phase 4
analysis modules unchanged since `1dcb009`).

---

## Verdict

**§4.3 compressibility — jamming-specific.** The §4.3 signature
(σ_u floor-locked above the coherent baseline, phi_norm cross-seed σ
strongly reduced, per-window Φ unimodal narrow, mean Φ inverted above
the coherent baseline) is cleanly confirmed at `jamming α=0.2` (the A2
reference), partially present at `jamming α=0.5`, and at no other
sweep-condition in this audit. The leadership extension was tested in
Tier 1.A and disconfirmed (Outcome 4 — Φ collapse via leader-block
partition rather than uniform-elevation compressibility). The original
D14 generalization claim is empirically narrowed to "jamming as the
unique non-leadership §4.3 instance available in the existing
sweep set."

**§4.2 transitional peak — supported with two confirmed instances.**
Alignment `w_a=0.6` (Tier 1.B confirmed) and `noise σ=0.2` (newly
identified by this audit) are both steady-state per-window bimodal with
σ_u in the moderate "between coherent and disordered" range. The noise
σ=0.2 instance is more empirically clean than the alignment one on three
counts: it satisfies the mean-Φ peak criterion (Φ=144.63 above both
σ=0.0 and σ=0.5 endpoints), the dip test is stronger
(`dip p ≈ 7.6 × 10⁻⁶` vs `0.102`, four orders of magnitude), and σ_u sits between the synchronized
endpoint (0.515 at σ=0.0) and the disordered endpoint (0.642 at σ=0.5)
without the disordered-random complication of `alignment w_a=0.0`. The
high-w_a non-monotonicity check is **null** (`d ≈ 0.002`, CIs heavily
overlap), so the alignment §4.2 instance is the bimodality-signature
case at the transitional w_a=0.6 condition rather than a clean mean-peak
inversion.

**Joint judgment — D14's framework confirmed in two complementary
instances per prediction, across three orthogonal perturbation axes,
with the leadership axis explicitly disconfirmed.** The Bailey &
Schneider §4.2/§4.3 mechanism is empirically grounded in this 3D swarm:
§4.2 transitional bimodality occurs in alignment-coupling and additive-
noise sweeps; §4.3 compressibility-Φ-inversion occurs in the jamming
sweep. The framework is mechanism-specific rather than sweep-specific
— different perturbation axes can excite different sub-predictions of
the §4.2/§4.3 family, and not every axis excites a §4.2/§4.3 mode (the
leadership axis produces a structurally distinct leader-block-partition
mechanism). The Phase 5 internal report's Discussion section should
lead with this two-instance-per-prediction framing rather than the
original "compressibility as general mechanism" framing.

---

## Cross-sweep aggregation table

Columns: cross-seed Φ mean and 95% CI (1000-resample bootstrap on
per-seed steady-state means); σ_u steady-state cross-seed mean (computed
for the three §4.2/§4.3-load-bearing sweeps + noise sweep after the
σ=0.2 candidate emerged); phi_norm cross-seed σ; bimodality on pooled
steady-state per-window Φ (`window_idx ≥ quantile(2/3)` per seed,
≈310 windows pooled per condition) — `dip p` and KDE mode count.
**Bimodal classification:** `dip p < 0.20` AND `modes ≥ 2` (Tier 1.B
convention). The "✦" tag in the right-most column marks bimodal
classifications. The "†" tag marks conditions whose seed parquets are
byte-identical to the vanilla-boids baseline (see §vanilla-baseline
below).

| sweep | condition | n_seeds | Φ mean | Φ 95% CI | σ_u | phi_norm σ | dip p | modes | bimodal? |
|---|---|---|---|---|---|---|---|---|---|
| alignment_sweep | wa_0.0 | 10 | 361.16 | [357.70, 364.45] | **0.7941** | 0.0147 | 0.861 | 1 |  |
| alignment_sweep | wa_0.6 | 10 | 138.73 | [116.55, 160.50] | **0.5201** | 0.0937 | 0.102 | 2 | ✦ §4.2 |
| alignment_sweep | wa_1.2 | 10 | 117.98 | [97.87, 139.33] | **0.5061** | 0.0997 | 0.992 | 1 |  |
| alignment_sweep | wa_1.8 | 10 | 118.07 | [96.60, 138.41] | **0.5070** | 0.0974 | 0.962 | 1 |  |
| jamming_sweep | alpha_0.2 | 10 | 187.23 | [181.61, 193.74] | **0.5925** | 0.0268 | 0.984 | 1 | (§4.3 ref) |
| jamming_sweep | alpha_0.5 | 10 | 140.17 | [130.01, 151.02] | **0.5331** | 0.0441 | 0.720 | 1 |  |
| jamming_sweep | alpha_1.0 † | 10 | 135.05 | [115.95, 155.30] | **0.5183** | 0.0911 | 0.914 | 1 |  |
| leadership_sweep | lambda_0.0 † | 10 | 135.05 | [115.95, 155.30] | **0.5183** | 0.0911 | 0.914 | 1 |  |
| leadership_sweep | lambda_0.8 | 10 | 113.35 | [68.96, 158.64] | **0.7009** | 0.2084 | 0.907 | 1 |  |
| leadership_sweep | lambda_1.6 | 10 | 6.94 | [5.41, 8.45] | **0.6188** | 0.0097 | 0.992 | 1 |  |
| leadership_sweep | lambda_2.4 | 10 | 8.73 | [4.03, 15.19] | **0.6030** | 0.0328 | 0.953 | 2 |  |
| milling_sweep | mu_0.0 † | 10 | 135.05 | [115.95, 155.30] | (vanilla) | 0.0911 | 0.914 | 1 |  |
| milling_sweep | mu_0.4 | 10 | 573.56 | [553.08, 594.67] | n/a | 0.0534 | 0.726 | 1 |  |
| milling_sweep | mu_0.8 | 10 | 565.36 | [505.44, 620.21] | n/a | 0.1980 | 0.259 | 2 |  |
| milling_sweep | mu_1.2 | 10 | 593.57 | [539.38, 645.41] | n/a | 0.0538 | 0.664 | 2 |  |
| split_merge_sweep | none † | 10 | 135.05 | [115.95, 155.30] | (vanilla) | 0.0911 | 0.914 | 1 |  |
| split_merge_sweep | split_merge | 10 | 105.41 | [86.16, 127.48] | n/a | 0.1023 | 0.791 | 1 |  |
| noise_sweep | sigma_0.0 | 10 | 129.65 | [121.32, 137.91] | **0.5148** | 0.0496 | 0.717 | 1 |  |
| noise_sweep | sigma_0.05 † | 10 | 135.05 | [115.95, 155.30] | **0.5183** | 0.0911 | 0.914 | 1 |  |
| noise_sweep | sigma_0.1 | 10 | 128.50 | [110.91, 147.00] | **0.5111** | 0.0666 | 0.446 | 3 |  |
| noise_sweep | sigma_0.2 | 10 | 144.63 | [125.58, 163.49] | **0.5311** | 0.0799 | 7.6e-6 | 2 | ✦ §4.2 |
| noise_sweep | sigma_0.5 | 10 | 85.03 | [77.33, 92.92] | **0.6421** | 0.0334 | 0.993 | 1 |  |
| n_sensitivity_N80 | wa_0.0 | 5 | 1553.37 | [1539.50, 1570.26] | n/a | 0.0121 | 0.658 | 1 |  |
| n_sensitivity_N80 | wa_0.6 | 5 | 564.56 | [492.31, 668.90] | n/a | 0.0859 | 0.789 | 1 |  |
| n_sensitivity_N80 | wa_1.2 | 5 | 426.91 | [323.79, 557.12] | n/a | 0.0887 | 0.982 | 2 |  |
| n_sensitivity_N80 | wa_1.8 | 5 | 596.93 | [457.21, 736.10] | n/a | 0.1113 | 0.310 | 1 |  |
| n_sensitivity_N160 | wa_0.0 | 5 | 6504.59 | [6439.25, 6595.73] | n/a | 0.0161 | 0.953 | 1 |  |
| n_sensitivity_N160 | wa_0.6 | 5 | 1735.22 | [1190.37, 2285.84] | n/a | 0.1327 | 0.922 | 1 |  |
| n_sensitivity_N160 | wa_1.2 | 5 | 2163.25 | [1849.21, 2507.29] | n/a | 0.0655 | 0.947 | 1 |  |
| n_sensitivity_N160 | wa_1.8 | 5 | 2088.87 | [1481.67, 2722.44] | n/a | 0.1364 | 0.124 | 1 |  |
| w_sensitivity | W30 | 5 | 95.39 | [82.78, 108.18] | n/a | 0.0550 | 0.583 | 2 |  |
| w_sensitivity | W40 ‡ | 5 | 126.41 | [111.77, 142.59] | n/a | 0.0755 | 0.438 | 2 |  |
| w_sensitivity | W50 | 5 | 155.25 | [141.69, 171.00] | n/a | 0.0857 | 0.311 | 2 |  |
| w_sensitivity | W60 | 5 | 183.51 | [172.61, 197.74] | n/a | 0.0916 | 0.707 | 1 |  |
| alignment_rule_sensitivity | mean ‡ | 5 | 126.41 | [111.77, 142.59] | n/a | 0.0755 | 0.438 | 2 |  |
| alignment_rule_sensitivity | sum | 5 | 79.48 | [61.72, 94.72] | n/a | 0.0641 | 0.993 | 2 |  |
| sensitivity | ksg_kinematic ‡ | 5 | 126.41 | [111.77, 142.59] | n/a | 0.0755 | 0.438 | 2 |  |
| sensitivity | ksg_vxvyvz | 5 | 128.85 | [113.04, 146.73] | n/a | 0.0821 | 0.809 | 2 |  |
| sensitivity | ksg_full | 5 | 472.51 | [440.13, 499.36] | n/a | 0.0851 | 0.889 | 1 |  |
| sensitivity | histogram_kinematic | 5 | 1184.16 | [1163.92, 1204.27] | n/a | 0.0092 | 0.990 | 1 |  |
| sensitivity | histogram_vxvyvz | 5 | 1178.52 | [1159.24, 1196.59] | n/a | 0.0116 | 0.515 | 1 |  |
| sensitivity | histogram_full | 5 | 1358.55 | [1334.06, 1380.08] | n/a | 0.0175 | 0.875 | 1 |  |
| sensitivity | gaussian_kinematic | 5 | 380.06 | [299.06, 465.88] | n/a | 0.3171 | 0.634 | 2 |  |
| sensitivity | gaussian_vxvyvz | 5 | 334.93 | [257.20, 416.51] | n/a | 0.3183 | 0.334 | 3 |  |
| sensitivity | gaussian_full | 5 | 2832.25 | [2595.86, 2985.84] | n/a | 0.6459 | 0.981 | 1 |  |

Footnotes.

- **σ_u definition** is the per-agent L2 norm of per-channel velocity-direction
  stds, averaged across agents over each W=40 window — Tier 1.A's
  `windowed_sigma_u_per_window` (commit `9ad6a5a`). This is **not the same**
  as A2 §2's per-channel "raw within-agent directional std" (which reports
  ranges of 0.17–0.26 at α=0.2). The L2-of-3-channels definition multiplies
  the per-channel value by ~√3 for direction-isotropic motion, so quantitative
  comparison between this audit's σ_u and A2's σ_u must use the same definition;
  values within the audit are mutually consistent (the leadership-sweep σ_u
  reused from Tier 1.A matches the jamming-sweep σ_u recomputed for `alpha_1.0`
  to 4 decimals at 0.5183, exactly as expected from the byte-identical vanilla
  parquet — see §vanilla-baseline).
- **σ_u "n/a"** marks sweeps where σ_u is not load-bearing for the §4.2/§4.3
  verdicts (out of audit scope; computable on request from the existing
  scenarios.py / model.py via deterministic D6 re-runs).
- **"vanilla" σ_u entries** for the † conditions point to the recomputed
  jamming `α=1.0` row above — all five n=10 † conditions share byte-identical
  parquets and therefore identical σ_u, phi_norm σ, and bimodality. They are
  reported as separate rows for completeness but quantitatively duplicate.
- **† marker** flags the n=10 vanilla-boids cluster: `jamming α=1.0`,
  `leader λ=0.0`, `milling μ=0.0`, `noise σ=0.05`, `split_merge none`. Tier
  1.B's audit verified three of these byte-identical at commit `7a5b58e`;
  this audit's hash check (`audit_aggregates.json::vanilla_baseline_equivalence`)
  extends the verification to all five.
- **‡ marker** flags an analogous n=5 sensitivity-default cluster:
  `w_sensitivity W40`, `alignment_rule_sensitivity mean`, `sensitivity
  ksg_kinematic`. Their seed 0 parquet matches the n=10 cluster's hash —
  these are 5-seed subsets of the same vanilla-boids run set.
- **Φ 95% CI** is the 1000-resample percentile bootstrap CI on the cross-seed
  mean, computed from `per_seed_summary.csv::phi_spectral_mean` per the D2
  protocol. The Φ mean and per-seed std reproduce
  `cross_seed_summary.csv::phi_spectral_mean` and `phi_spectral_std`.

---

## §4.3 compressibility analysis

The signature pattern from the A2 jamming reference at `α=0.2`
(`outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md`):

1. σ_u floor-locked at moderate elevation above the coherent baseline
   ("the 80% alignment loss forces agents to continually wobble"; per-window
   σ_u never falls into the steady-flight low regime that drags Φ down).
2. phi_norm cross-seed σ strongly reduced (jamming regularizes Φ across
   seeds; A2 reference: 0.025 vs 0.086 at α=1.0).
3. Per-window Φ unimodal narrow (no flipping between high-MI wobble
   windows and low-MI steady-flight windows).
4. Mean Φ inverted above the same sweep's coherent baseline (the headline
   §4.3 prediction: a coherent regime registers lower Φ than a moderately
   disordered regime via compressibility).

**Note on signature wording.** Some prior text (including parts of the
Phase5.md scoping document) describes the §4.3 signature as "low σ_u"
following the literal reading of B&S §4.3 (the synchronized regime is
"compressible" = low intrinsic entropy = low within-window dynamic
amplitude). In our swarm the operationalization is inverted: the
*coherent baseline* (α=1.0, w_a=1.2, w_a=1.8) is the regime that is
*sometimes* compressed (low-σ_u steady-flight windows interleaved with
high-σ_u turn windows), so its mean σ_u sits in the middle and its
phi_norm cross-seed σ is high; the *jammed* condition (α=0.2) is the
regime that *prevents* compressibility (σ_u floor-locked above the
steady-flight low), so its phi_norm cross-seed σ is low. The audit table
above describes "§4.3 instance" using the empirical operational
signature (σ_u elevated above the same sweep's coherent baseline, phi_norm
σ below it, unimodal narrow Φ, mean Φ inverted) rather than the literal
B&S "low σ_u" reading. Both descriptions agree on which condition is
the §4.3 instance (jamming α=0.2); they differ only in which side of
the σ_u comparison is phrased as "the compressibility side."

### Sub-table — descriptors at each candidate vs the A2 reference

| condition | σ_u | phi_norm σ | dip p | modes | std/IQR | mean Φ vs same-sweep coherent | §4.3 match? |
|---|---|---|---|---|---|---|---|
| **A2 reference** `jamming α=0.2` | 0.5925 | **0.0268** | **0.984** | 1 | **0.857** | **+39%** vs α=1.0 (135.05) | **YES — confirmed §4.3 instance** |
| `jamming α=0.5` | 0.5331 | 0.0441 | 0.720 | 1 | 0.595 | +4% vs α=1.0 | partial (intermediate compressibility) |
| `alignment w_a=0.0` | 0.7941 | 0.0147 | 0.861 | 1 | 0.695 | +206% vs w_a=1.2 (117.98) | **no** — σ_u in disordered-random regime, not floor-locked moderate; mechanism is "no alignment, cohesion+separation produce structure," not compressibility-prevention |
| `leader λ=1.6` | 0.6188 | 0.0097 | 0.992 | 1 | 0.919 | **−94%** vs λ=0.0 (135.05) | **no** — Φ INVERTED OPPOSITE direction (collapse below coherent baseline); Outcome 4 leader-block partition |
| `leader λ=2.4` | 0.6030 | 0.0328 | 0.953 | 2 | 2.616 | **−94%** vs λ=0.0 | **no** — same Outcome 4 mechanism; modes=2 from heavy-tailed dispersion (std/IQR=2.6) not bimodality (dip p=0.95) |
| `noise σ=0.5` | 0.6421 | 0.0334 | 0.993 | 1 | 0.646 | **−37%** vs σ=0.05 (135.05) | **no** — Φ DROPS at random regime (B&S random endpoint), not the §4.3 inversion direction |

**Reading.** Only `jamming α=0.2` cleanly matches the §4.3 signature in
all four descriptor columns; `jamming α=0.5` is a partial intermediate
case. The other low-phi_norm-σ candidates (`alignment w_a=0.0`,
`leader λ=1.6` and `λ=2.4`, `noise σ=0.5`) fail on at least one
load-bearing descriptor — most decisively on the Φ-inversion direction.
The `alignment w_a=0.0` row in particular shows that low phi_norm σ
alone is not sufficient to indicate compressibility: at w_a=0 the
phi_norm regularization is driven by the disordered-random regime
giving very consistent (high) Φ across seeds, not by the §4.3 mechanism.

This confirms the §4.3 verdict above: jamming is the unique
non-leadership §4.3 instance available in the existing sweep set.

---

## §4.2 transitional peak analysis

The signature pattern (Tier 1.B audit at `alignment w_a=0.6` plus the
§4.2 mechanism description in B&S 2025):

1. Per-window Φ steady-state distribution **bimodal** (the within-
   window-distribution signature of a regime that flips between
   high-Φ turning/wobble and low-Φ steady-flight modes).
2. σ_u in the moderate "between disordered and coherent" range
   (window-by-window σ_u is bimodal; the cross-window mean sits
   close to the coherent endpoint because the low-σ "steady" windows
   pull the average down).
3. Mean Φ peaks at the transitional condition relative to both endpoints
   (the mean-Φ-peak signature; satisfied where the disordered endpoint
   is genuinely random / B&S-style independence, less satisfied where
   the disordered endpoint has its own MI-elevating dynamics).

### Sub-table — bimodal candidates across all 11 sweeps

A condition is bimodal under the Tier 1.B criterion (`dip p < 0.20` AND
KDE modes ≥ 2). Conditions with `modes ≥ 2` but `dip p ≥ 0.20` are
heavy-tailed unimodal-with-shoulder, not statistically bimodal at this
n; they are listed for transparency but excluded from the §4.2
candidate set.

| sweep | condition | dip p | modes | std/IQR | σ_u | Φ vs both endpoints | §4.2 instance? |
|---|---|---|---|---|---|---|---|
| `alignment w_a=0.6` | (Tier 1.B confirmed) | **0.102** | **2** | 0.551 | **0.5201** (moderate; w_a=0 → 0.794, w_a=1.2 → 0.506) | Φ=138.7 — *below* w_a=0 (361) but above w_a=1.2 (118) | **YES** — bimodality + σ_u-in-range; mean-peak partial (peaks above coherent endpoint only) |
| `noise σ=0.2` | **(this audit, new)** | **7.6e-6** | **2** | 0.544 | **0.5311** (moderate; σ=0.0 → 0.515, σ=0.5 → 0.642) | Φ=144.6 — **above** σ=0 (130) AND σ=0.5 (85) | **YES — second confirmed §4.2 instance** — full signature, including mean-peak above both endpoints |
| `noise σ=0.1` | (sub-threshold) | 0.446 | 3 | 0.568 | 0.5111 | Φ=128.5 — between σ=0.05 (135) and σ=0.2 (145) | **no** — modes=3 with dip p=0.45 indicates secondary structure but not statistical bimodality at this n |
| `milling μ=0.8` | (sub-threshold) | 0.259 | 2 | 0.775 | n/a | Φ=565 vs μ=0 (135) and μ=1.2 (594) — within the high-Φ milling regime | **no** — dip p slightly above 0.20 threshold; unrelated to §4.2 disorder-to-order transition |
| `n_sensitivity_N80 wa_1.2` | (sub-threshold) | 0.982 | 2 | 0.692 | n/a | Φ=427 between disordered (1553) and most-coherent (597) | **no** — dip p=0.98 strongly unimodal; modes=2 likely KDE wiggle on heavy tail at n=5 |
| `n_sensitivity_N160 wa_1.8` | (sub-threshold) | 0.124 | 1 | 0.673 | n/a | Φ=2089 — N=160 high-Φ regime | **no** — dip p < 0.20 but modes=1; not bimodal under joint criterion |
| `w_sensitivity W30..W50` | (sub-threshold) | 0.31–0.58 | 2 | ≈0.62 | n/a | smooth W-dependence in Φ | **no** — modes=2 in n=5 with default-bandwidth KDE on a wide-tailed distribution; dip p shows no statistical bimodality |
| `alignment_rule_sensitivity / sensitivity *_kinematic ‡` | (n=5 sensitivity-default cluster) | 0.438 | 2 | 0.621 | n/a | Same row (vanilla baseline 5-seed subset) | **no** — same modes=2 as W40 ‡ from the same byte-identical parquets; not a distinct candidate |
| `sensitivity gaussian_*` | (estimator-substitution) | 0.33–0.98 | 1–3 | 0.69–0.84 | n/a | Different estimator entirely (closed-form Gaussian); D11 sign-only territory | **no** — within-estimator multi-modality not interpretable as §4.2 mechanism without histogram + KSG concurrence |

**Mean-peak verification at `alignment w_a=0.6`.** The §4.2 mean-Φ-peak
prediction requires Φ at the transitional condition to exceed both
disordered and coherent endpoints. In the alignment sweep:

- Φ(w_a=0.0) = 361.16 (disordered — but Φ HIGH, not low)
- Φ(w_a=0.6) = 138.73 (transitional — bimodal)
- Φ(w_a=1.2) = 117.98 (coherent)
- Φ(w_a=1.8) = 118.07 (most coherent)

The peak is at the disordered endpoint, not the transitional condition.
The "alignment w_a=0.0" condition does **not** correspond to B&S §4.2's
"random regime" because at w_a=0 the swarm still has non-zero cohesion
and separation forces, which produce structured pairwise dynamics with
high MI and high Φ even without alignment coupling. The §4.2 prediction's
mean-peak component therefore cannot be cleanly tested in this sweep.
The bimodality-signature component IS satisfied at the transitional
condition (`w_a=0.6` is the only bimodal alignment condition), so the
audit reports this as a §4.2 instance under the within-window
distribution signature, with the explicit caveat that the mean-peak
requires a sweep whose disordered endpoint is genuinely
B&S-random — which is `noise σ=0.5` in our sweep set (Φ=85 < every
synchronized condition), and which is what makes `noise σ=0.2` a
particularly clean §4.2 confirmation.

**Mean-peak verification at `noise σ=0.2` (the new instance).**

- Φ(σ=0.0) = 129.65 (synchronized — no noise)
- Φ(σ=0.05) = 135.05 (vanilla baseline)
- Φ(σ=0.1) = 128.50 (mild perturbation)
- Φ(σ=0.2) = **144.63** (transitional — bimodal)
- Φ(σ=0.5) = 85.03 (random — high noise)

The peak at `σ=0.2` exceeds every neighbouring noise condition AND both
endpoints. The mean-Φ peak is mild in absolute terms (≈+7% over
baseline) but unambiguous in direction (CIs do not strictly disjoint
with σ=0.05's CI, but the bimodal per-window signature at `σ=0.2` is
the load-bearing signal — `dip p ≈ 7.6 × 10⁻⁶` is the strongest
dip-test result in the entire 11-sweep audit). The mechanism is consistent with
B&S §4.2: at moderate noise, the synchronized flock alternates window
by window between turning/realignment events (high σ_u and high MI)
and steady-flight windows (low σ_u and low MI), producing the bimodal
per-window Φ that the §4.2 prediction expects at the transitional
regime.

**Why noise σ=0.2 was missed in pre-registered Tier 1.B atlas.**
Tier 1.B's atlas scope (per Session 1 Outcome 4 verdict §6) deliberately
excluded the noise sweep — it was not pre-registered as a §4.2 candidate
because the noise perturbation acts on an axis (additive velocity noise)
distinct from the coupling axis (`w_a`) that originally framed §4.2 in
C1. The cross-sweep audit's purpose is exactly to surface this kind of
non-pre-registered candidate; finding one is a substantive cross-sweep
result, not noise. The σ=0.2 instance is an additive-noise analog of
the alignment w_a=0.6 instance — both occupy the *transitional* regime
of their respective control axes, and both express the bimodal-per-
window-Φ signature.

---

## High-w_a non-monotonicity check

Per the Tier 1.B observation that `alignment_sweep` mean Φ may be
slightly higher at `w_a=1.8` than at `w_a=1.2` (visible by inspection of
`alignment_sweep_distributions.png`):

| quantity | w_a=1.2 | w_a=1.8 |
|---|---|---|
| cross-seed Φ mean (per-seed steady-state) | 117.98 | 118.07 |
| 95% bootstrap CI on cross-seed mean | [97.87, 139.33] | [96.60, 138.41] |
| difference (w_a=1.8 − w_a=1.2) | — | **+0.089** |
| 95% bootstrap CI on the difference | — | **[−28.98, +29.65]** |
| Cohen's d (per-seed values) | — | **+0.002** |
| CI overlap | — | **yes (heavy)** |

**Verdict — null.** The visual ordering from the Tier 1.B distribution
figure is within noise. Φ at `w_a=1.8` and `w_a=1.2` are statistically
indistinguishable: the difference of +0.089 (in absolute Φ units) sits
on a per-seed std of ~35; Cohen's d is essentially zero; the bootstrap
CI on the difference brackets zero with a width of ≈59; the per-condition
CIs overlap by 96.6%. The §4.2 transitional-peak prediction's "post-peak
decline" reading is therefore **monotonically non-strict**: in the
alignment sweep, mean Φ saturates at the coherent end (w_a=1.2 ≈ w_a=1.8)
with no further descent as coupling strengthens. There is no
high-w_a non-monotonicity to fold into the §4.2 verdict.

**Implication for the §4.2 prediction's post-peak shape.** The plateau
at high w_a is consistent with the swarm reaching a "maximally coherent"
steady-state where further increases in w_a do not further suppress
σ_u or further compress Φ — the σ_u re-runs confirm this (σ_u(w_a=1.2)
= 0.5061 vs σ_u(w_a=1.8) = 0.5070, indistinguishable). This argues
against extrapolating the alignment sweep further to look for an even
deeper §4.3 compressibility instance: w_a=1.8 is already at the σ_u
floor of the coherent-flock regime in this 3D model (with default
cohesion+separation+noise active), and the coherent baseline Φ is
≈118. The §4.3 inversion is not visible on the alignment axis at the
sampled w_a values.

---

## Leadership Outcome 4 placement in the cross-sweep picture

Tier 1.A (`outputs/tier1_compressibility/leadership_prediction_verdict.md`,
commit `9ad6a5a`) established that the Φ collapse at high λ is real (Φ at
λ=2.4 ≈ 8.7 vs Φ at λ=0.0 ≈ 135, d=+5.0, CIs disjoint) but the
mechanism is structurally distinct from the §4.3 compressibility
mechanism diagnosed at jamming. The Outcome 4 mechanism diagnostic
shows three of four A2-reference compressibility descriptors fail at
λ=2.4: MI mean is low (0.19 vs 0.49 at α=0.2), spatial coupling
ρ(MI, −d) is moderate-strong (+0.30 vs +0.10), eigenvalue gap is
intermediate (7.4 vs 18.7). The Fiedler partition at λ=2.4 perfectly
separates leaders from followers (`Fiedler ⟷ leader-membership = 1.000`)
— a leader-block partition pattern, not the uniformly elevated MI
matrix that defines compressibility per A2.

In the cross-sweep panel, this places leadership `λ=1.6` and `λ=2.4`
in the bottom-left quadrant of `(σ_u, phi_norm σ)` space — looking
superficially like the A2 reference because both have σ_u in the
0.6 range and phi_norm σ in the 0.01–0.03 range. But Φ is **far below**
the leadership coherent baseline (≈8 vs 135), the OPPOSITE direction
of §4.3's coherent-baseline-inversion. The cross-sweep picture
*reaffirms* Outcome 4 by showing that the (σ_u, phi_norm σ) coordinate
alone does not classify a condition as §4.3 — the Φ-direction-of-
inversion AND the per-window Φ shape AND the MI matrix structure
diagnostic together are needed. Tier 1.A's Outcome-4 verdict is
unchanged by the cross-sweep audit; it is corroborated by the absence
of any other sweep showing the leadership-style Φ-collapse pattern.

The leader-block-partition mechanism is structurally distinct from
both §4.2 and §4.3, and from any other condition surfaced in this
audit. It is the leadership sweep's own phenomenon and should be
reported under its own mechanism description in the Phase 5 internal
report — neither as a "third compressibility instance" (the original
pre-registered prediction; falsified) nor as a §4.2 transitional
instance (no bimodality at λ=2.4 under steady-state-only pooling).

---

## Cross-references

- **A2 diagnostic** (commit `cc23aa9`,
  `outputs/jamming_sweep/A2_PHI_INVERSION_DIAGNOSTIC.md`) — canonical
  §4.3 reference for the descriptors used in this audit.
- **Tier 1.A leadership prediction verdict** (commit `9ad6a5a`,
  `outputs/tier1_compressibility/leadership_prediction_verdict.md`) —
  Outcome 4 finding for leadership; this audit reuses the leadership
  σ_u values from `aggregates.json` without re-running.
- **Tier 1.B per-window distribution atlas + bimodality audit**
  (commits `4f821ae` and `7a5b58e`,
  `outputs/tier1_compressibility/distributions/bimodality_audit.md`) —
  steady-state pooling convention adopted here; vanilla-baseline three-
  condition equivalence verified at `7a5b58e` and extended in this
  audit to five at n=10 plus three at n=5 (`vanilla_baseline_equivalence`
  in `audit_aggregates.json`).
- **D14 sharpening** (commits `7c96730` and `6baae1a`,
  `SpectralSwarm3DPhases.md` D14) — current canonical statement of the
  §4.2/§4.3 framework as two complementary predictions; this audit
  updates the empirical-instance count to **two §4.2 instances** (alignment
  w_a=0.6 + noise σ=0.2) **and one §4.3 instance** (jamming α=0.2),
  with the leadership extension explicitly disconfirmed.

---

## Recommendations for Phase 5 writeup

The Tier 3.C internal report's Discussion section should lean on the
following synthesis:

1. **Headline framing.** The Bailey & Schneider (2025) §4.2/§4.3
   compressibility mechanism is empirically grounded in this 3D swarm
   across **three orthogonal perturbation axes** — alignment coupling
   (§4.2 transitional bimodality at `w_a=0.6`), additive noise
   (§4.2 transitional peak at `σ=0.2`), and jamming severity
   (§4.3 compressibility-Φ-inversion at `α=0.2`). The mechanism is
   axis-specific in expression: not every perturbation axis excites a
   §4.2 or §4.3 mode (the leadership-coupling axis produces a
   structurally distinct leader-block-partition Φ collapse, tested
   in Tier 1.A and disconfirmed as a third compressibility instance).

2. **Two §4.2 instances, not one.** The Tier 1.B atlas was correctly
   cautious about scope; the cross-sweep audit's job was to surface
   non-pre-registered candidates, and the noise σ=0.2 result is one.
   The audit's evidence for `noise σ=0.2` as a §4.2 instance is at
   least as strong as the evidence for `alignment w_a=0.6` (dip test
   stronger; mean-peak signature satisfied; σ_u verified moderate).
   The Phase 5 report should report both instances, with `noise σ=0.2`
   framed as an additional empirical confirmation rather than a
   surprise — additive velocity noise is a plausible §4.2 axis and its
   transitional regime expressing the bimodal-Φ signature is exactly
   what B&S §4.2 predicts.

3. **One §4.3 instance.** The Phase 5 report should state plainly that
   §4.3 compressibility is a jamming-specific finding within this
   sweep set. The leadership prediction was a load-bearing
   pre-registered test of generality; its disconfirmation
   (Tier 1.A Outcome 4) is a *result*, not a caveat — Phase 5 ships
   a tested-and-disconfirmed extension claim alongside two confirmed
   instances of the parent prediction. This is a stronger empirical
   posture than ambiguity in either direction would have produced.

4. **Mechanism description preserved.** D14's mechanism description
   (Φ_spectral measures within-window informational dependence;
   coherent-low-dynamics regimes show low MI in steady-flight windows,
   pulling the mean down; transitional regimes show window-to-window
   bimodality; jammed regimes lock σ_u above the steady-flight low and
   invert the mean Φ ordering relative to the coherent baseline) is
   confirmed by every dataset in this audit and should be the
   methodological framing in the report's Methods section.

5. **Vanilla-baseline footnote.** The eight identified byte-identical
   conditions (five at n=10, three at n=5 sensitivity-default subset)
   should be reported once in the report's Tables section with explicit
   recognition that these rows duplicate identical underlying
   simulations under D6 deterministic seeding, so cross-scenario
   correlations and η² aggregations in Tier 2.C must collapse them to
   a single "vanilla baseline" entry. This audit's
   `audit_aggregates.json::vanilla_baseline_equivalence` is the canonical
   list (extends Tier 1.B's three-condition record).

6. **High-w_a plateau.** The high-w_a non-monotonicity check is null;
   the alignment-sweep coherent endpoint plateau at `w_a ≥ 1.2` should
   be reported as a property of the sweep design rather than an
   anomaly. No further sub-condition analysis is warranted at the
   sampled w_a values.

---

## Future work hooks

These are pointers for ResearchContext.md §4.8 (N-scaling) and §4.9
(synchronic/diachronic separation), not commitments within Phase 5:

1. **N-scaling at jamming α=0.2** to confirm §4.3 compressibility's
   N-dependence. The cross-sweep table shows the existing
   `n_sensitivity_N80` and `_N160` data are at default w_a sweeping
   the alignment axis only; an analogous N-scaling at jamming α=0.2
   would test whether the σ_u floor-locked regime persists, weakens, or
   strengthens with N. This is the clearest single follow-up that
   would harden the §4.3 verdict.

2. **Finer alignment_sweep grid around w_a=0.6** to characterize the
   §4.2 transitional regime's width on the coupling axis. Bimodality at
   w_a=0.6 is the only steady-state bimodal condition in the alignment
   sweep, but the grid width (Δw_a = 0.6) is too coarse to establish
   how narrow the transitional regime is. A grid at
   w_a ∈ {0.3, 0.45, 0.6, 0.75, 0.9} would map the transitional
   bimodality's onset and offset on the alignment axis.

3. **Finer noise_sweep grid around σ=0.2** for the analogous question
   on the noise axis. The current grid jumps from σ=0.1 (modes=3,
   dip p=0.45) to σ=0.2 (bimodal) to σ=0.5 (random unimodal); a
   finer grid (σ ∈ {0.15, 0.2, 0.25, 0.3, 0.35}) would map the
   transitional regime's width on the noise axis. The dip p=0.000 at
   σ=0.2 is the strongest bimodal signature in the audit and is worth
   characterizing precisely.

4. **Leader-only σ_u at high λ**, deferred from Tier 1.A §9. If
   leader-subset σ_u dropped sharply at λ=2.4 even while global σ_u
   did not, this would refine the description of the leader-block
   mechanism but would not change the Outcome 4 verdict (the MI matrix
   structure diagnostic already differentiates from §4.3 compressibility
   independent of σ_u).

5. **Surrogate null at noise σ=0.2** in Tier 2.B. The pre-registered
   Tier 2.B surrogate set includes seven primary scenarios with seed 0;
   `noise σ=0.5` is the surrogate-method positive control. Adding
   `noise σ=0.2` to that set would test whether observed Φ exceeds
   surrogate Φ at the newly-identified §4.2 instance — a cheap
   additional sanity check on the candidate's signature.

---

## Confidence note

**Strong confidence on the §4.3 verdict.** Two independent lines of
evidence converge:

1. The MI matrix mechanism diagnostic from A2 (commit `cc23aa9`)
   established `jamming α=0.2` as the unique uniform-MI compressibility
   regime in the existing data. The cross-sweep audit's σ_u + phi_norm σ
   table corroborates: only `jamming α=0.2` (and partially `α=0.5`)
   matches the floor-locked-σ_u + low-phi_norm-σ + Φ-inversion-above-
   baseline pattern.
2. The leadership extension was tested in Tier 1.A across 10 seeds with
   the explicit MI matrix mechanism diagnostic, and the leader-block-
   partition signature decisively differentiates Outcome 4 from §4.3
   compressibility. The cross-sweep view confirms no other sweep-condition
   matches the §4.3 signature.

**Strong confidence on the §4.2 verdict's two-instance count.** The
bimodality criterion (`dip p < 0.20` AND modes ≥ 2 at steady-state
pooled per-window Φ) classifies exactly two conditions in the entire
45-row table as bimodal: `alignment w_a=0.6` (Tier 1.B confirmed,
`dip p=0.102`) and `noise σ=0.2` (this audit, `dip p ≈ 7.6 × 10⁻⁶`).
The noise σ=0.2 instance has stronger statistical evidence (`dip p`
four orders of magnitude smaller) and additionally satisfies the mean-Φ
peak criterion (which alignment w_a=0.6 cannot due to the disordered-
endpoint complication).

**Borderline elements where reasonable analysis could differ.**

- **`noise σ=0.2`'s mean-peak magnitude is mild.** Φ(σ=0.2) = 144.63
  vs Φ(σ=0.05) = 135.05 is ≈+7% over baseline; the per-condition CIs
  overlap (no disjoint-CI confirmation of a peak at the strict-disjoint
  level). The bimodality signature (`dip p=0.000`) is the load-bearing
  signal; the mean-peak is corroborating but not by itself decisive.
  An argument for reporting `noise σ=0.2` as "ambiguous" rather than
  "confirmed second §4.2 instance" could rest on the mean-peak
  weakness; the audit chose "confirmed" because the bimodality is
  unambiguous and the σ_u + endpoint structure both fit. A finer noise
  grid (future-work item 3) would settle the mean-peak's robustness
  at higher resolution.

- **`alignment w_a=0.6`'s mean-peak failure.** The alignment §4.2
  instance was confirmed by Tier 1.B on the bimodality signature
  alone, with the explicit recognition that the mean-peak component
  is not testable in this sweep because the disordered endpoint
  (`w_a=0.0`) is not B&S-random in our model. A reasonable analysis
  could choose to flag `alignment w_a=0.6` as "partial §4.2" rather
  than "confirmed §4.2"; the audit follows Tier 1.B's classification
  for continuity and cites the disordered-endpoint complication
  explicitly above. The two-instance count (alignment + noise) is
  robust to either reading.

- **σ_u definition asymmetry with A2.** The audit's σ_u (per-agent
  L2 norm of per-channel velocity-direction stds) is ≈√3 times A2's
  per-channel "raw within-agent directional std." The audit's σ_u
  values are mutually consistent across the four σ_u-computed sweeps
  but cannot be directly compared to A2 §2's numerical references
  (e.g., A2 reports σ_u ≈ 0.17–0.26 at α=0.2; this audit's L2
  definition gives 0.59 at α=0.2). The relative ordering is preserved
  (jamming α=0.2 > jamming α=1.0 in both definitions) and the
  relative-to-coherent-baseline structure is the relevant comparison
  for the verdict, so this definition asymmetry is documented and
  does not affect the verdict but is a clarity item for any reader
  cross-referencing A2 numbers in the Phase 5 report.

- **Unknown σ_u for 7 of 11 sweeps.** The audit deliberately restricts
  σ_u re-runs to the four sweeps that load on the §4.2/§4.3 verdicts
  (alignment, jamming, leadership, noise). The remaining seven sweeps
  (milling, split_merge, the four sensitivity sweeps) could in principle
  surface another §4.2 or §4.3 candidate that the bimodality-only
  table missed. The bimodality scan flagged none above the criterion,
  which is the audit's strongest argument that no further candidate is
  hiding. A future sweep-wide σ_u re-run is a cheap add (~30 minutes
  of compute) and would close this gap.

- **n=5 sensitivity sweeps are underpowered for bimodality.** Several
  n=5 sensitivity-sweep conditions show modes=2 with dip p in the
  0.3–0.6 range (e.g., `w_sensitivity W30..W50`, `gaussian_*`); these
  are sub-threshold under the audit criterion and likely reflect
  default-bandwidth-KDE wiggle on a heavy-tailed distribution at
  ~155 windows pooled. None of the n=5 conditions cross the
  `dip p < 0.20 AND modes ≥ 2` threshold, so the bimodality-detection
  power is sufficient to distinguish them from the two confirmed
  cases (alignment w_a=0.6 dip p=0.102; noise σ=0.2 dip p=0.000). A
  larger-n re-run of the sensitivity sweeps would resolve the
  sub-threshold cases definitively but is not load-bearing for the
  verdict.

**No revision to `Phase5.md` or `SpectralSwarm3DPhases.md` is recommended
from this analysis.** D14's framing is empirically supported and the
sub-prediction count is now: §4.2 → 2 instances, §4.3 → 1 instance,
leadership extension → disconfirmed (Outcome 4). If a planning-level
revision is desired in a separate session, the only candidate edit is
to add `noise σ=0.2` to D14's "complementary empirical instances"
list alongside `alignment w_a=0.6`. This is a single-line addition;
the rest of D14 (mechanism description, jamming-confirms-§4.3,
leadership-disconfirms-extension) is unchanged.
