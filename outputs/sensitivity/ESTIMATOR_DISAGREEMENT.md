# Estimator Disagreement — B2b Finding

**Date:** 2026-04-21  
**Sweep:** sensitivity (9-combo, kinematic/vxvyvz/full × ksg/histogram/gaussian)  
**Conditions examined here:** ksg_kinematic vs histogram_kinematic, seeds 0–4  
**Git commit at time of finding:** 9450515 (analyze_sweep.py)

---

## 5-seed steady-state Φ_spectral (final third of windows, W=40, stride=5, T=500)

| seed | KSG | Histogram | ratio (hist/ksg) |
|------|-----|-----------|------------------|
| 0 | 125.12 | 1144.98 | 9.15× |
| 1 | 158.23 | 1167.81 | 7.38× |
| 2 | 113.15 | 1194.04 | 10.55× |
| 3 | 103.71 | 1200.58 | 11.58× |
| 4 | 131.86 | 1213.38 | 9.20× |

KSG top seed: 1 (158.23). Histogram top seed: 4 (1213.38). Different.

---

## Correlation statistics

| level | Pearson r | Spearman ρ | p (Spearman) |
|-------|-----------|------------|--------------|
| window-level (93 windows, seed 0) | 0.317 | 0.096 | 0.361 |
| seed-level (5 steady-state means) | — | −0.200 | 0.747 |

---

## Ratio instability

The histogram/KSG magnitude ratio is not a stable scale factor:

- Minimum ratio: 7.38× (seed 1)  
- Maximum ratio: 11.58× (seed 3)  
- Range: 4.20× across 5 seeds  

---

## Status

This is a methodology finding requiring investigation in a dedicated Opus session before Phase 4 Part C is run. Part C (full sweep, ~280 runs) is on hold pending that diagnostic.
