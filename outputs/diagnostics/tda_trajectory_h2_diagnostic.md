# TDA Trajectory-Cloud H2 Diagnostic (D9 Option 1)

**Date:** 2026-04-21  
**Git commit:** `683bb3150c4e4eb5f2630c1498a5cf5632e06482`

Diagnostic for D9 (docs/decisions/D9_h2_sampling_density.md) Option 1:
trajectory-cloud H2 at methodology-spec N=40. Fixed: seed=0, T=500,
kinematic features, unaugmented, D3 standardization applied.
Window widths W ∈ {40, 80}. Final window (T-W:T) used.

## Results

| scenario | W | ambient_dim | TP_0 | MP_0 | TP_1 | MP_1 | TP_2 | MP_2 | wall_time_sec |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| none | 40 | 160 | 227.4905 | 15.4391 | 3.7201 | 1.3663 | 0.0000 | 0.0000 | 0.0000 |
| milling | 40 | 160 | 163.3073 | 21.6944 | 1.3327 | 0.8688 | 0.0000 | 0.0000 | 0.0000 |
| none | 80 | 320 | 421.5685 | 23.1641 | 0.0073 | 0.0073 | 0.0000 | 0.0000 | 0.0000 |
| milling | 80 | 320 | 331.4331 | 30.4233 | 1.1607 | 0.5056 | 0.0000 | 0.0000 | 0.0000 |

## Summary

### W=40 (ambient dim 160)

**H2:** milling MP_2=0.0000, TP_2=0.0000; baseline MP_2=0.0000, TP_2=0.0000. milling MP_2 / baseline MP_2 = NaN < 2.0 — NOT achieved.

**H1:** milling MP_1=0.8688, TP_1=1.3327; baseline MP_1=1.3663, TP_1=3.7201. milling MP_1 / baseline MP_1 = 0.64.

### W=80 (ambient dim 320)

**H2:** milling MP_2=0.0000, TP_2=0.0000; baseline MP_2=0.0000, TP_2=0.0000. milling MP_2 / baseline MP_2 = NaN < 2.0 — NOT achieved.

**H1:** milling MP_1=0.5056, TP_1=1.1607; baseline MP_1=0.0073, TP_1=0.0073. milling MP_1 / baseline MP_1 = 69.50.

### Overall H2 verdict

milling MP_2 / baseline MP_2 ≥ 2.0 not achieved at either W=40 or W=80.
