# B2a — Alignment-Rule Sensitivity Summary

Compares `mean` vs `sum` alignment rule at calibrated w_a=1.0, baseline scenario, 5 seeds each. Tests robustness of the A6 mean-alignment restoration.

## Per-seed Φ_spectral at steady state

| rule | seed | phi_spectral_mean | phi_spectral_ci_lo | phi_spectral_ci_hi |
|------|------|-------------------|--------------------|--------------------|
| mean | 0 | 125.1158 | 96.7775 | 155.4376 |
| mean | 1 | 158.2288 | 131.6684 | 184.1254 |
| mean | 2 | 113.1493 | 91.3570 | 135.2653 |
| mean | 3 | 103.7149 | 83.8803 | 124.1526 |
| mean | 4 | 131.8600 | 100.6710 | 162.2210 |
| sum | 0 | 51.0103 | 40.4956 | 62.2167 |
| sum | 1 | 91.7055 | 69.3303 | 115.7695 |
| sum | 2 | 91.8200 | 71.4725 | 114.1496 |
| sum | 3 | 63.7375 | 51.6271 | 76.7274 |
| sum | 4 | 99.1330 | 74.1673 | 123.3568 |

**Interpretation:** Mean Φ_spectral at steady state: `mean` rule = 126.41, `sum` rule = 79.48. The `mean`-alignment restoration (A6) produces Φ_spectral behavior qualitatively higher than the `sum` variant.
