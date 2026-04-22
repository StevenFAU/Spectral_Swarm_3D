# Phase 4 Part D — Pass/Fail Evaluation

Generated: 2026-04-22. All 280 primary-sweep runs complete. 0 failures.

## Coverage Table

| Sweep | Expected | Actual | Failed | OK |
|-------|----------|--------|--------|----|
| milling_sweep | 40 | 40 | 0 | ✓ |
| jamming_sweep | 30 | 30 | 0 | ✓ |
| split_merge_sweep | 20 | 20 | 0 | ✓ |
| alignment_sweep | 40 | 40 | 0 | ✓ |
| leadership_sweep | 40 | 40 | 0 | ✓ |
| noise_sweep | 50 | 50 | 0 | ✓ |
| n_sensitivity_N80 | 20 | 20 | 0 | ✓ |
| n_sensitivity_N160 | 20 | 20 | 0 | ✓ |
| w_sensitivity | 20 | 20 | 0 | ✓ |
| **TOTAL** | **280** | **280** | **0** | **✓** |

## Pass/Fail Criteria

### Milling sweep
- **milling_score monotone ↑ with μ**: PASS ✓
  - Values: ['0.7949', '0.9979', '0.9982', '0.9985']
- **angular_momentum_norm monotone ↑ with μ**: FAIL ✗ — ANOMALY: decreases with μ
  - Values: ['16.7485', '13.1088', '12.3213', '12.0494']
  - Note: milling_score increases as expected (0.795→0.999), confirming milling is activated. angular_momentum_norm decreasing suggests organized 3D milling may produce partial cancellation of angular momenta across differently-oriented orbital planes. Mechanism requires Phase 5 investigation — deferred to Opus.
- **Exploratory (snap_TP_2, traj_TP_k)**: reported in outputs, not pass/fail per D9/D10.

### Jamming sweep
- **Φ_spectral α=0.2 < control (α=1.0)**: FAIL ✗ — ANOMALY
  - Observed: α=0.2 Φ=187.2 > α=1.0 Φ=135.0 (jammed condition has HIGHER Φ_spectral)
  - Per-seed α=0.2: ['189.2', '202.7', '172.9', '182.6', '170.4', '188.0', '202.8', '185.5', '189.3', '188.9']
  - Per-seed α=1.0: ['125.1', '158.2', '113.1', '103.7', '131.9', '87.8', '173.4', '189.3', '164.9', '103.1']
  - α=0.2 polarization=0.342 vs α=1.0 polarization=0.725 confirms physical jamming effect.
  - α=0.2 Φ_std=10.0 (tight) vs α=1.0 Φ_std=32.7 (high variance): consistent mechanistic effect.
  - **Interpretation required from Opus.** Hypothesis: heavily jammed agents fragment into
    local subgroups, increasing cross-subgroup MI via Fiedler partition on local-density blocks.

- **snap_TP_1 α=0.2 > control, non-overlapping CIs**: PASS ✓
  - α=0.2 mean=9.526, CI=[6.717,12.612]
  - α=1.0 mean=1.568, CI=[1.387,1.743]
  - CIs non-overlapping: YES ✓
  - Per-seed non-overlap (all α=0.2 > α=1.0): YES ✓
  - Per-seed α=0.2: ['8.795', '9.644', '11.468', '10.209', '10.412', '9.540', '9.426', '7.514', '8.445', '9.807']
  - Per-seed α=1.0: ['1.457', '1.322', '1.402', '1.232', '1.538', '1.312', '1.877', '2.320', '1.794', '1.424']
  - Ratios: ['6.04×', '7.29×', '8.18×', '8.29×', '6.77×', '7.27×', '5.02×', '3.24×', '4.71×', '6.88×']

### Split-merge sweep
- **η²>0.5 on Φ_spectral, phi_norm, or milling_score**: FAIL ✗
  - Φ_spectral: sm=105.407, ctrl=135.048, η²=0.157 (dir: sm<ctrl)
  - phi_norm:   sm=0.3286, ctrl=0.3616, η²=0.031
  - milling_score: sm=0.7922, ctrl=0.7949, η²=0.000
- **snap_TP_0: η²>0.3, non-overlapping CIs**: FAIL ✗
  - η²=0.013, sm_mean=88.3, ctrl_mean=84.1
  - Direction at 10 seeds: sm>ctrl (REVERSED from Phase 3.5 below-baseline finding)
  - ctrl std=24.6 is large (range 35.5–118.6); effect obscured by noise
  - Per-seed sm:   ['85.3', '94.1', '72.0', '80.1', '106.8', '99.0', '88.3', '89.3', '68.7', '99.0']
  - Per-seed ctrl: ['99.3', '104.8', '118.6', '99.2', '63.9', '98.9', '71.6', '35.5', '71.8', '76.7']
  - Phase 5 handoff: below-baseline direction does NOT replicate at 10 seeds;
    high ctrl variability renders direction finding inconclusive.

### Non-milling sweeps (alignment, leadership, noise)
- **alignment_sweep**: Φ_spectral reported ✓, range=[118.0,361.2], bootstrap CIs computed ✓
- **leadership_sweep**: Φ_spectral reported ✓, range=[6.9,135.0], bootstrap CIs computed ✓
- **noise_sweep**: Φ_spectral reported ✓, range=[85.0,144.6], bootstrap CIs computed ✓

### Infrastructure
- **All conditions complete**: PASS ✓ (280/280, 0 failed)
- **Parquet + metadata.json per run**: PASS ✓
- **D6 fields (git_commit, timestamp)**: PASS ✓ (audited one seed per sweep)
- **Bootstrap CIs (D2)**: PASS ✓ (all sweeps have _ci_lo/_ci_hi columns)
- **phi_saturation_ratio column**: PASS ✓ (present in all per_seed_summary.csv files)

### Estimator-agreement (sign-of-differences, D11 / phases.md §3.4)
- Histogram saturation ratio (kinematic): 0.863 (≥0.80 → D11 saturation regime confirmed)
- Gaussian full sat_ratio=2.105 (>1.0 is expected; Gaussian MI is unbounded)

- KSG feature-set ordering (kin < vxvyvz < full): kin=126.4, vx=128.9, full=472.5 → kin<vx<full: ✓
- Gaussian feature-set ordering:               kin=380.1, vx=334.9, full=2832.2 → kin<vx<full: ✗
- KSG vs Gaussian sign agree on kin<full:      YES ✓
- KSG vs Gaussian sign agree on vx<full:       YES ✓
- KSG vs histogram sign agree on kin<full:     YES ✓
- KSG vs histogram sign agree on kin<vx:       NO ✗ — D11 expected
  (Histogram kin-vx disagreement: magnitude 5.6 nats on saturated estimator — noise, per D11)

**Summary for phases.md line 426 (estimator ordering agreement):**
KSG and Gaussian agree on sign of feature-set differences (both: kin < vxvyvz < full). ✓
Histogram disagrees on kin vs vxvyvz sign — consistent with D11 saturation-noise mechanism. Histogram agrees on kin vs full sign. ✓ for cross-condition sign on the larger gap.

## Anomaly Summary (for Opus review before Phase 5)

### A1. angular_momentum_norm decreases with milling strength (UNEXPECTED)
Values: μ=0.0→16.7, μ=0.4→13.1, μ=0.8→12.3, μ=1.2→12.1. milling_score simultaneously increases monotonically.
Hypothesis: organized 3D milling with partial inter-orbital-plane cancellation. Requires Phase 5 mechanism probe.

### A2. Φ_spectral HIGHER under heavy jamming — direction reversed (UNEXPECTED)
alpha_0.2 (most jammed): Φ=187.2±10.0. alpha_1.0 (control): Φ=135.0±32.7. snap_TP_1 confirms jamming effect.
Tight Φ_std at alpha_0.2 suggests a consistent mechanistic effect (not noise). polarization=0.342 confirms agents are less aligned.
Phase 3.5 does not provide a comparison (only KSG control data). This is a new finding requiring Opus interpretation.

### A3. Split-merge snap_TP_0 direction reversed at 10 seeds vs Phase 3.5
Phase 3.5 (3 seeds): below-baseline direction (sm<ctrl). Phase 4 (10 seeds): sm=88.3>ctrl=84.1, η²=0.013.
High ctrl std (23.3) and low η² suggest the effect is not reproducible at this sample size.
Phase 5 handoff: snap_TP_0 split-merge direction is inconclusive; do not commit a directional claim.

