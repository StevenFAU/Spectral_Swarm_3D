# TDA H2 Sampling Density Sweep

**Date:** 2026-04-21  
**Git commit:** `79f3bbe1d19c748005db093ce848ccca06af4dd8`

Diagnostic sweep for D9 (H2 sampling density decision). Covers
N ∈ {40, 80, 120, 160} × embedding ∈ {unaugmented, augmented} ×
scenario ∈ {none, milling} at seed=0, T=500, step=499.
Geometry fixed at defaults: L=50, milling_R=11, speed=1.0, vision_radius=10.

## Results

| N | scenario | embedding | snap_TP_2 | snap_MP_2 | mean_radial_distance | nearest_neighbor_spacing | shell_thickness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40 | none | unaugmented | 0.5376 | 0.4311 | 14.2385 | 0.7817 | 4.7321 |
| 40 | none | augmented | 0.5376 | 0.4310 | 14.2385 | 0.7821 | 4.7321 |
| 40 | milling | unaugmented | 0.0000 | 0.0000 | 13.2527 | 0.1675 | 0.6432 |
| 40 | milling | augmented | 0.0000 | 0.0000 | 13.2527 | 0.1694 | 0.6432 |
| 80 | none | unaugmented | 0.6089 | 0.2962 | 22.7501 | 0.6936 | 1.5548 |
| 80 | none | augmented | 0.6093 | 0.2963 | 22.7501 | 0.6942 | 1.5548 |
| 80 | milling | unaugmented | 0.3863 | 0.3360 | 13.2721 | 0.1721 | 0.6930 |
| 80 | milling | augmented | 0.3861 | 0.3359 | 13.2721 | 0.1737 | 0.6930 |
| 120 | none | unaugmented | 0.6772 | 0.3129 | 29.1765 | 0.4641 | 6.4493 |
| 120 | none | augmented | 0.6822 | 0.3130 | 29.1765 | 0.4688 | 6.4493 |
| 120 | milling | unaugmented | 0.1937 | 0.1113 | 13.2860 | 0.0908 | 0.8939 |
| 120 | milling | augmented | 0.1942 | 0.1115 | 13.2860 | 0.0944 | 0.8939 |
| 160 | none | unaugmented | 1.6013 | 0.3379 | 22.6768 | 0.4838 | 6.2201 |
| 160 | none | augmented | 1.6007 | 0.3378 | 22.6768 | 0.4884 | 6.2201 |
| 160 | milling | unaugmented | 0.5675 | 0.5239 | 13.2979 | 0.0768 | 0.9376 |
| 160 | milling | augmented | 0.5677 | 0.5239 | 13.2979 | 0.0802 | 0.9376 |

## Summary

No (N, embedding) combination produces milling MP_2 / baseline MP_2 ≥ 2.0. H2 void detection remains unreliable at all tested sampling densities with both unaugmented and augmented embeddings at methodology-spec geometry (L=50, milling_R=11, speed=1.0, vision_radius=10).
