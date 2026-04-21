# B2b — Estimator × Feature-Set Sensitivity Summary

9-condition matrix: `{ksg, histogram, gaussian} × {kinematic, vxvyvz, full}`. Baseline scenario (none), w_a=1.0, 5 seeds each. Primary metric: Φ_spectral at steady state (mean across seeds).

## 3×3 Φ_spectral table (mean across seeds)

| estimator | kinematic | vxvyvz | full |
|-----------|------|------|------|
| ksg | 126.41 | 128.85 | 472.51 |
| histogram | 1184.16 | 1178.52 | 1358.55 |
| gaussian | 380.06 | 334.93 | 2832.25 |

**Interpretation:** KSG mean Φ_spectral = 242.59, histogram = 1240.41, Gaussian = 1182.41. KSG and histogram show > 20% difference — flag for methodology review. Gaussian exceeds KSG — unexpected; may indicate finite-sample bias. 
