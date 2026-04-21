# Trajectory-Cloud H1 Variance Check (W=80, 5 seeds)

**Date:** 2026-04-21  
**Git commit:** `17a95195a23fb2b7021bdb8198970010111c7cb9`

Follow-up to D9 closure. Checks whether the single-seed observation (seed=0,
commit 23a8d4f) that trajectory-cloud MP_1 at W=80 distinguishes milling from
baseline holds across seeds [0, 1, 2, 3, 4].

Fixed: W=80, N=40, T=500, kinematic features, D3 standardization, maxdim=1.

## Raw results

| seed | scenario | W | MP_1 | TP_1 | wall_time_sec |
| --- | --- | --- | --- | --- | --- |
| 0 | none | 80 | 0.0073 | 0.0073 | 0.6600 |
| 0 | milling | 80 | 0.5056 | 1.1607 | 0.6400 |
| 1 | none | 80 | 0.3716 | 0.3716 | 0.6100 |
| 1 | milling | 80 | 0.4265 | 1.0622 | 0.6700 |
| 2 | none | 80 | 1.5400 | 2.4470 | 0.6100 |
| 2 | milling | 80 | 1.2812 | 2.0257 | 0.6500 |
| 3 | none | 80 | 0.7434 | 1.7822 | 0.6300 |
| 3 | milling | 80 | 0.6168 | 0.9372 | 0.6400 |
| 4 | none | 80 | 1.5023 | 2.3175 | 0.6300 |
| 4 | milling | 80 | 0.6866 | 1.2204 | 0.6400 |

## Per-scenario summary (MP_1)

**milling:** mean=0.7033, std=0.3025, min=0.4265, max=1.2812

**none (baseline):** mean=0.8329, std=0.6084, min=0.0073, max=1.5400

## Per-seed ratios (milling MP_1 / baseline MP_1)

seed=0: 69.497, seed=1: 1.148, seed=2: 0.832, seed=3: 0.830, seed=4: 0.457

Mean ratio: 14.553  
Range: [0.457, 69.497]  
Seeds with milling > baseline: 2/5

## Suitability judgment

The milling > baseline direction holds for 2/5 seeds, with per-seed ratios ranging from 0.457 to 69.497. At this variance profile, traj_MP_1 at W=80 is **not suitable as primary control; requires follow-up analysis** as a Phase 4 milling-sweep positive control.