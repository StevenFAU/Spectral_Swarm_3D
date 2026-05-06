# Phase 5 Tier 1.A — Leadership Compressibility Prediction Verdict

**Date:** 2026-05-06.
**Pipeline:** `outputs/tier1_compressibility/_make_aggregates.py`
(`aggregates.json`, `mechanism_diagnostic.npz`, `per_window_timeseries.npz`)
+ `_make_figures.py` (`leadership_panel.png`, `mi_matrix_diagnostic.png`).
**Code at HEAD:** `839172a` (Phase 5 plan added; Phase 4 analysis modules
unchanged since `1dcb009` — the leadership-sweep parquets reproduce
bit-identically).

## Verdict

**Outcome 4 — Φ ordering observed but mechanism is not compressibility.**
Φ_spectral at λ=2.4 is dramatically lower than at λ=0.0 and λ=0.8 (large
effect, CIs disjoint), but the MI matrix at λ=2.4 fails three of four
A2-reference compressibility descriptors (low MI mean, moderate-strong
spatial dependence, intermediate eigenvalue gap), and σ_u — the proximate
compressibility driver — is **not compressed at high λ**; it is in fact
slightly higher at λ=2.4 (0.60) than at λ=0.0 (0.52). The Φ drop is real
but compressibility is the wrong name for it: the MI matrix is
*block-structured around the leader cluster*, not uniformly elevated as
under jamming.

## 1. Numeric support — pairwise comparisons

Per-seed steady-state means (final third of windows, n=10 seeds per
condition). Bootstrap 95% CIs use B=1000 resamples of seeds with
replacement (D2 protocol). Cohen's d uses pooled std (ddof=1).

| Comparison | mean other | mean λ=2.4 | diff (other − 2.4) | 95% CI on diff | Cohen's d | CIs disjoint? |
|---|---|---|---|---|---|---|
| **Φ(λ=0.0) vs Φ(λ=2.4)** | 135.05 | 8.73 | **+126.32** | [+106.18, +146.52] | **+5.00** | yes |
| **Φ(λ=0.8) vs Φ(λ=2.4)** | 113.35 | 8.73 | **+104.62** | [+59.88, +150.81] | **+1.88** | yes |
| **Φ(λ=1.6) vs Φ(λ=2.4)** | 6.94 | 8.73 | **−1.79** | [−8.47, +3.24] | **−0.25** | **no** |

**Reading.** Φ at λ=2.4 is unambiguously lower than at λ=0.0 and λ=0.8
(large effect, no CI overlap). Φ at λ=1.6 vs λ=2.4 is statistically
indistinguishable — d=−0.25, the bootstrap CI on the difference brackets
zero, and the per-condition CIs overlap. The "Φ non-monotone with peak at
moderate λ" reading required by Outcome 1's strict criterion is therefore
not supported: the peak is at λ=0.0, not at moderate λ, and the tail is
flat from λ=1.6 onward rather than dipping further at λ=2.4.

## 2. Numeric support — per-condition aggregates

Per-seed steady-state values aggregated across n=10 seeds. CIs are
percentile bootstrap on the cross-seed mean.

| Condition | Φ_spectral (mean, 95% CI) | σ_u (mean, 95% CI) | leader compactness (mean, 95% CI) | polarization | phi_norm cross-seed σ |
|---|---|---|---|---|---|
| λ=0.0 | **135.05** [115.95, 155.30] | **0.518** [0.498, 0.538] | **19.94** [10.98, 25.51] | 0.725 | 0.0911 |
| λ=0.8 | **113.35** [68.96, 158.64] | **0.701** [0.642, 0.761] | **1.61** [1.45, 1.74] | 0.663 | 0.2084 |
| λ=1.6 | **6.94** [5.41, 8.45] | **0.619** [0.602, 0.635] | **0.141** [0.133, 0.154] | 0.605 | **0.0097** |
| λ=2.4 | **8.73** [4.03, 15.19] | **0.603** [0.588, 0.618] | **0.226** [0.150, 0.337] | 0.579 | **0.0328** |

**A2 reference for context** (jamming sweep, 10-seed):
phi_norm cross-seed σ = 0.025 at α=0.2 (compressibility) vs 0.086 at α=1.0
(coherent baseline).

### Bimodality diagnostics (per-window Φ, steady-state windows only, n≈310 each)

| Condition | Hartigan dip p | KDE mode count | std/IQR |
|---|---|---|---|
| λ=0.0 | 0.914 | 1 | 0.611 |
| λ=0.8 | 0.907 | 1 | 0.661 |
| λ=1.6 | 0.992 | 1 | 0.919 |
| λ=2.4 | 0.953 | 1 | 2.616 |

> Bimodality diagnostics revised to steady-state-only pooling per the Tier 1.B audit's
> methodological clarification (commit `4f821ae`). The original Tier 1.A all-windows
> pooling produced different numbers for λ=0.8 (dip p=0.129, modes=2, classified bimodal);
> this was a transient-mixing artifact, documented in the audit's cross-reference section.
> The verdict's overall classification (Outcome 4) is unchanged — bimodality at λ=0.8 was
> not load-bearing for the Outcome 4 finding.

**Reading.** All four conditions are unimodal under steady-state-only pooling. λ=2.4
remains heavy-tailed (std/IQR=2.616), reflecting occasional high-Φ excursions; λ=1.6
is narrower (std/IQR=0.919). The original Tier 1.A finding that λ=0.8 appeared bimodal
(modes=2) does not replicate under steady-state restriction — it was a transient-mixing
artifact. D14's secondary prediction that high-λ distributions become "more tightly
unimodal than at λ=0 or λ=0.8" is not supported; all conditions are unimodal and the
high-λ tails are heavier, not tighter.

### What does and does not fit the compressibility prediction

| D14 / A2 prediction at high λ | Result | Match? |
|---|---|---|
| Φ at λ=2.4 lower than at moderate λ | Lower than λ=0.0 and λ=0.8; **indistinguishable from λ=1.6** | partial |
| σ_u monotonically compressed at high λ | σ_u **highest at λ=0.8 (0.70)**, lowest at λ=0.0 (0.52); λ=2.4 (0.60) > λ=0.0 | **fails** |
| Leader compactness collapses at high λ | 19.9 → 1.6 → 0.14 → 0.23 (dramatic collapse 0.0 → 0.8 → 1.6) | yes |
| Per-window Φ "more tightly unimodal" at high λ | Mode count 1 at λ=1.6 and λ=2.4 (vs 2 at λ=0.8); but std/IQR is heavy-tailed | partial |
| phi_norm cross-seed σ near 0.025 (jamming) at high λ | 0.0097 (λ=1.6) and 0.0328 (λ=2.4) — both at or below the jamming reference | yes |

The proximate driver A2 identified — within-window σ_u compression — is
**absent** in the leadership sweep. phi_norm regularization across seeds
**is** present at high λ. A subset of compressibility's correlates appears
without the mechanism that produces them under jamming.

## 3. Mechanism diagnostic — MI matrix at the representative window

For each of λ=0.0 and λ=2.4 we picked the seed whose per-seed
steady-state Φ is closest to the cross-seed median, then the
steady-state window whose Φ is closest to that seed's mean. Features
and MI matrix are recomputed via the canonical `extract_features` →
`standardize_window` → `mi_matrix_ksg(k=5, noise_eps=1e-10)` path; the
recomputed Φ_spectral matches the published parquet bit-for-bit (a
sanity check on reproducibility).

- **λ=0.0 representative:** seed 4, window 85 (steps 425–464); per-seed
  steady-state mean Φ = 131.86, this window's Φ = 130.96.
- **λ=2.4 representative:** seed 0, window 89 (steps 445–484); per-seed
  steady-state mean Φ = 6.02, this window's Φ = 7.36.

| Descriptor | A2 α=0.2 (compressibility) | A2 α=1.0 (coherent) | **λ=0.0 (this study)** | **λ=2.4 (this study)** |
|---|---|---|---|---|
| MI mean | **0.491** | 0.099 | 0.414 | **0.188** |
| MI std | 0.209 | 0.100 | 0.108 | 0.158 |
| MI Q25 / Q50 / Q75 | 0.33 / 0.48 / 0.63 | 0.03 / 0.08 / 0.14 | 0.34 / 0.43 / 0.49 | 0.04 / 0.17 / 0.30 |
| Spearman ρ(MI, −d) | **+0.10** (p=0.005) | +0.40 (p<1e-4) | +0.32 (p<1e-19) | **+0.30** (p<1e-17) |
| Fiedler ⟷ kmeans-2 pair agreement | **0.50** (chance) | 0.78 | 0.90 | **0.49** |
| Fiedler λ_2 (normalized Laplacian) | **0.926** | 0.463 | 0.932 | **0.347** |
| MI top-eig gap (top1 − top2) | **18.7** | 1.77 | 15.6 | **7.4** |
| phi_norm cross-seed σ (10-seed) | 0.025 | 0.086 | 0.0911 | **0.0328** |

**Interpretation.**

The λ=0.0 representative is closest to the **A2 α=0.2 column** on three of
five MI descriptors (MI mean, Fiedler λ_2, top-eig gap), but with much
stronger spatial dependence (ρ = +0.32 vs +0.10) and high agreement with
spatial kmeans (0.90 vs 0.50). It is qualitatively a coherent flock with
high uniform MI, similar to A2 jamming in Φ magnitude but with spatial
ordering visible in the partition geometry.

The λ=2.4 representative **does not match either A2 column cleanly**.
Three of four discriminating descriptors fail the compressibility
signature:

- MI mean is **low** (0.19) — closer to α=1.0 (0.10) than to α=0.2 (0.49).
  Compressibility predicts MI ≳ 0.4.
- Spatial dependence ρ(MI, −d) is **moderate-strong** (+0.30), not the
  near-zero ρ that compressibility predicts (≲ 0.15).
- The MI eigenvalue gap is **intermediate** (7.4) — well below
  compressibility's rank-1-dominated 18.7 and above coherent's 1.77.
- Fiedler ⟷ kmeans-2 agreement at chance (0.49) is the **only**
  descriptor matching compressibility — but for a different reason than
  in jamming (see below).

**Why agreement is at chance for a non-compressibility reason.** Direct
inspection of the partition shows that at λ=2.4 the **Fiedler bipartition
splits leaders from followers perfectly** (8 leaders in one part, 32
followers in the other; Fiedler-vs-leader-membership pair agreement =
1.000). The kmeans-2 spatial bipartition gives a different cut — it
splits the swarm geometrically, ignoring functional role
(kmeans-2-vs-leader-membership pair agreement = 0.49). The two methods
disagree because the MI matrix is **block-structured around the leader
cluster**, not uniform: leaders share high MI with each other (tight
group, common waypoint pull), and the bulk follower-follower MI is low.
The spatial bipartition cuts the larger geometric extent of the swarm;
the Fiedler cut isolates the dense leader block. Φ_spectral falls
because the cross-cut sum is composed of low leader-to-follower MI edges.

This is the **block-structured pattern** Outcome 4 explicitly warns about
("any pattern distinct from uniform elevation"), produced by a different
mechanism than A2 compressibility.

For comparison, at λ=0.0 the Fiedler partition is **not** aligned with
the leader/follower axis (4 leaders in each Fiedler part — leaders are
dynamically indistinguishable from followers when leader_strength = 0),
and Fiedler agrees strongly with spatial kmeans (0.90). The qualitative
mechanism producing Φ at λ=0.0 is uniform high MI in a coherent flock —
the closest leadership-sweep analogue to A2 jamming, at the *opposite*
end of the λ axis.

## 4. Per-seed breakdown

Per-seed steady-state values across all (condition, seed) combinations.
Outlier flag uses Tukey 1.5·IQR within each condition's Φ distribution.

| λ | seed | Φ_ss | σ_u_ss | compactness | polarization | outlier? |
|---|------|------|--------|-------------|--------------|----------|
| 0.0 | 0 | 125.12 | 0.5369 | 21.43 | 0.614 |  |
| 0.0 | 1 | 158.23 | 0.5463 | 26.98 | 0.805 |  |
| 0.0 | 2 | 113.15 | 0.5266 | 28.32 | 0.637 |  |
| 0.0 | 3 | 103.71 | 0.5123 | 27.71 | 0.625 |  |
| 0.0 | 4 | 131.86 | 0.5023 | 22.43 | 0.625 |  |
| 0.0 | 5 |  87.79 | 0.4949 | 29.64 | 0.602 |  |
| 0.0 | 6 | 173.41 | 0.5490 |  2.93 | 0.873 |  |
| 0.0 | 7 | 189.26 | 0.5579 |  3.73 | 0.944 |  |
| 0.0 | 8 | 164.89 | 0.4412 | 11.92 | 0.918 |  |
| 0.0 | 9 | 103.06 | 0.5157 | 24.35 | 0.607 |  |
| 0.8 | 0 | 205.23 | 0.8461 |  1.88 | 0.663 |  |
| 0.8 | 1 | 162.81 | 0.7748 |  1.85 | 0.554 |  |
| 0.8 | 2 |  51.85 | 0.6314 |  1.34 | 0.666 |  |
| 0.8 | 3 | 152.38 | 0.6929 |  1.60 | 0.689 |  |
| 0.8 | 4 |  47.26 | 0.6429 |  1.74 | 0.689 |  |
| 0.8 | 5 |  25.13 | 0.6693 |  1.21 | 0.738 |  |
| 0.8 | 6 | 244.87 | 0.8688 |  1.76 | 0.718 |  |
| 0.8 | 7 | 143.81 | 0.7227 |  1.64 | 0.550 |  |
| 0.8 | 8 |  62.18 | 0.5703 |  1.61 | 0.813 |  |
| 0.8 | 9 |  37.93 | 0.5901 |  1.49 | 0.547 |  |
| 1.6 | 0 |   7.01 | 0.6510 |  0.13 | 0.620 |  |
| 1.6 | 1 |   5.84 | 0.5970 |  0.13 | 0.528 |  |
| 1.6 | 2 |   2.75 | 0.6285 |  0.14 | 0.490 |  |
| 1.6 | 3 |   4.33 | 0.6252 |  0.12 | 0.786 |  |
| 1.6 | 4 |  10.59 | 0.6231 |  0.19 | 0.671 |  |
| 1.6 | 5 |   8.29 | 0.5800 |  0.14 | 0.530 |  |
| 1.6 | 6 |  10.25 | 0.6132 |  0.15 | 0.565 |  |
| 1.6 | 7 |   8.55 | 0.5784 |  0.15 | 0.744 |  |
| 1.6 | 8 |   8.04 | 0.6647 |  0.13 | 0.559 |  |
| 1.6 | 9 |   3.75 | 0.6268 |  0.13 | 0.556 |  |
| 2.4 | 0 |   6.02 | 0.6208 |  0.24 | 0.550 |  |
| 2.4 | 1 |   0.74 | 0.6301 |  0.09 | 0.405 |  |
| 2.4 | 2 |   2.20 | 0.5789 |  0.08 | 0.696 |  |
| 2.4 | 3 |   8.61 | 0.6095 |  0.20 | 0.646 |  |
| 2.4 | 4 |   6.56 | 0.5835 |  0.32 | 0.657 |  |
| 2.4 | 5 |   5.14 | 0.5764 |  0.20 | 0.555 |  |
| 2.4 | 6 |  16.32 | 0.5801 |  0.38 | 0.683 | ★ |
| 2.4 | 7 |   7.27 | 0.5943 |  0.09 | 0.605 |  |
| 2.4 | 8 |  33.19 | 0.6501 |  0.58 | 0.382 | ★ |
| 2.4 | 9 |   1.24 | 0.6064 |  0.08 | 0.609 |  |

Two seeds at λ=2.4 fail Tukey 1.5·IQR — seed 6 (Φ=16.3, ~2× the next
group) and seed 8 (Φ=33.2, ~2× seed 6).

Two further notes:

- **λ=0.8 has order-of-magnitude within-condition spread** (Φ from 25.1
  at seed 5 to 244.9 at seed 6). This is the regime with both the highest
  σ_u (0.87 at seed 6) and the most across-window Φ variance, and is why
  the Φ(λ=0.8) cross-seed CI is wide (±45). Bimodality diagnostics on the
  pooled per-window Φ at λ=0.8 detect 2 KDE modes (dip p = 0.13).
- **At λ=0.0**, seeds 6 and 7 have anomalously low compactness (2.9 and
  3.7) compared to the other 8 seeds (12–30). These are the seeds where
  the random initial leader placement happened to start clustered;
  without leader force they remain locally close. The cross-seed mean
  for compactness at λ=0.0 is therefore wide-CI (10.98 to 25.51) and is
  not a load-bearing signal at this condition.

## 5. Outlier sensitivity at λ=2.4

| Quantity | with seed 8 (n=10) | without seed 8 (n=9) |
|---|---|---|
| Φ cross-seed mean | 8.73 | **6.01** |
| Φ 95% bootstrap CI | [4.03, 15.19] | **[3.46, 8.95]** |
| diff Φ(λ=0.0) − Φ(λ=2.4) | +126.32 (d=+5.00) | +129.04 (d=+5.25) |
| diff Φ(λ=0.8) − Φ(λ=2.4) | +104.62 (d=+1.88) | +107.34 (d=+1.94) |
| diff Φ(λ=1.6) − Φ(λ=2.4) | −1.79 (d=−0.25) | **+0.93 (d=+0.24)** |

**Headline number kept as the with-seed-8 result (Φ=8.73)** because (a)
the analysis pre-registered seed 8 as part of the n=10 set in the
existing parquets and dropping it post-hoc is selection on the outcome
without an a priori physical justification, and (b) including it does
not change the verdict on any pairwise comparison — the directions of
all three comparisons against λ=2.4 are preserved (CIs disjoint at
0.0 and 0.8, overlapping at 1.6).

The n=9 sensitivity check is informative for one secondary purpose:
without seed 8, λ=2.4 (Φ=6.01) is even closer to λ=1.6 (Φ=6.94), and
the comparison flips sign while staying inside the bootstrap CI. So the
"λ=2.4 < λ=1.6" reading required by strict Outcome 1 also fails on the
without-seed-8 sensitivity — λ=2.4 is at most equal to λ=1.6, and on the
robust mean it is slightly higher.

Seed 8 is also the seed at λ=2.4 with the highest leader compactness
(0.58 vs 0.08–0.32 across the other 9 seeds) and the lowest
polarization (0.382 vs 0.40–0.70). Mechanistically it is consistent with
a less-tight leader cluster producing more inter-pair dynamic
information — i.e., the same direction of effect compactness has on Φ
within the high-λ regime.

## 6. Tier 1.B scoping recommendation

**Narrower focused atlas** (per Phase5.md guidance for Outcomes 2, 3, or
4). The full atlas is not the right deliverable since compressibility is
not now a general claim across all sweeps — it is a finding under
jamming whose generalization to leadership has been disconfirmed.

Atlas scope:
- **jamming_sweep** (confirmed compressibility instance — required).
- **alignment_sweep** (where C1 originally predicted the
  transitional-regime peak; the second pre-registered compressibility
  axis, distinct from leadership).
- **leadership_sweep at λ=0.8** — flagged here as the suspected-bimodality
  condition (KDE mode count = 2, dip p = 0.13). This is the most
  bimodal condition in the entire leadership_sweep and worth its own
  per-window distribution figure for the writeup. Other leadership
  conditions are not high-priority for the atlas.
- **milling_sweep at μ=0** if D14 also flagged it, plus any condition
  Sonnet's session 2 determines is plausibly bimodal during a quick
  scan of the existing parquets.

Other sweeps (split_merge, noise, sensitivity families, n_sensitivity,
w_sensitivity, alignment_rule_sensitivity) are out of atlas scope unless
something specific is requested.

## 7. Report-structure recommendation

**2D-mirror with compressibility positioned as a jamming-specific
finding, not as the headline.** Per Phase5.md's open-question 2, this
follows from any non-Outcome-1 verdict.

Concrete consequences for the Tier 3 internal report draft:

- **Headline section** is the primary pass/fail (milling monotonicity,
  snap_TP_1 jamming separation), as in the 2D report.
- **Compressibility section** stays — but framed as: "the jamming sweep
  produces a Bailey & Schneider §4.2–§4.3 compressibility instance; the
  pre-registered prediction that the leadership sweep would produce a
  second instance was tested (Phase 5 Tier 1.A) and **not confirmed** —
  the Φ drop at high λ is real but the MI matrix structure is
  block-structured around the leader cluster, not uniformly elevated,
  and σ_u is not compressed at high λ." This is a substantive scientific
  finding worth reporting honestly; the leadership Φ collapse becomes a
  "different mechanism" subsection rather than a corroborating
  compressibility instance.
- **Spectral-vs-topological comparison** (Tier 2 output) becomes the
  main co-headline rather than being upstaged by a compressibility-lead
  framing.
- **Methodological-note-up-front** from A2 §7 still belongs at the front
  of Methods — Φ_spectral being a within-window dependence score whose
  sensitivity to dynamic amplitude can produce coherent-regime
  inversions remains the right framing for reading any of the sweeps,
  including the ones where the inversion does not occur.

## 8. Confidence note

**Strong confidence on the verdict's negative direction.** Three
independent lines of evidence converge:

1. The mechanism diagnostic — the explicit Tier 1.A pass/fail — fails
   compressibility on 3 of 4 A2 descriptors (MI mean, ρ, gap), with the
   chance-level Fiedler/kmeans agreement explained by leader-cluster
   block structure rather than uniform elevation. The Fiedler partition
   at λ=2.4 perfectly separates leaders from followers (agreement =
   1.000), confirming the block-structured interpretation directly.
2. σ_u — the proximate mechanism in A2 — is **not compressed** at high
   λ. λ=2.4 has σ_u = 0.60, slightly higher than λ=0.0's 0.52. The
   maximum is at λ=0.8 (σ_u = 0.70). This contradicts the prediction
   directly.
3. The Φ ordering's strict reading also fails: Φ(λ=1.6) and Φ(λ=2.4)
   are statistically indistinguishable (CIs overlap, d = −0.25), and
   under the seed-8 sensitivity λ=2.4 becomes slightly higher than
   λ=1.6. Outcome 1's "non-monotone with peak at moderate λ, dip at
   extreme" requires λ=2.4 to be lower than at least one moderate λ; it
   is lower than 0.0 and 0.8, but the only "moderate" λ in the
   pre-registered ordering of {0.0, 0.8, 1.6, 2.4} where λ=2.4 sits
   below would be the two low conditions, undermining the
   "transitional-peak" reading. The pre-registered prediction was
   specifically that high-λ Φ would dip below moderate-λ Φ; the data
   show the regime transition happens between λ=0.8 and λ=1.6 (where
   leader compactness collapses from 1.6 to 0.14), with a flat tail
   thereafter.

**Borderline elements where reasonable analysis could differ.**

- **phi_norm cross-seed σ**: at λ=2.4 it is 0.033, near A2's 0.025
  compressibility reference. λ=1.6 is even tighter at 0.010. The
  "regularization across seeds" component of compressibility is
  partially present at high λ. However, this signal alone — without
  σ_u compression and without uniform MI — is insufficient to support
  a compressibility verdict; it is more parsimoniously explained by
  the leader cluster suppressing inter-seed variation in the late-run
  geometry (all seeds end up with leaders pulled to the same waypoint).
- **The MI matrix at λ=2.4 falls between A2 columns** on several
  descriptors (MI mean 0.19 between 0.10 and 0.49; ρ 0.30 between
  0.10 and 0.40). An "Ambiguous" label could be defended on these
  intermediate values alone. It was not chosen because the qualitative
  picture — block structure aligned with the functional leader/follower
  axis, low overall MI magnitude in the follower bulk — is mechanistically
  distinct from compressibility's uniformly-high MI signature, even where
  individual descriptors are in between numerically.
- **Polarization at λ=2.4 (0.58)** is lower than at λ=0.0 (0.72) and
  λ=0.8 (0.66), and is also low at the seed-8 outlier (0.38). The
  high-λ regime is not as polarized as the low-λ regimes, which
  tightens the case that Φ at high λ measures something other than
  classical coordination, but does not by itself adjudicate Outcome 1
  vs Outcome 4. This is consistent with A2 §6: Φ_spectral and
  polarization measure different things.
- **n=10 seeds is enough to disjoint-CI the headline pairwise
  comparisons** but is at the edge of statistical resolution for the
  λ=1.6 vs λ=2.4 comparison. A future N>10 follow-up at these two
  conditions would settle whether Φ(λ=2.4) < Φ(λ=1.6) holds at higher
  power — but even if it did, it would not rescue Outcome 1, since the
  *mechanism* diagnostic at λ=2.4 already fails 3/4 compressibility
  descriptors.

**No revision to Phase5.md or SpectralSwarm3DPhases.md is recommended
from this analysis.** The four-outcome framework is well-posed and the
data fall on Outcome 4. The plan's contingent Tier 1.B/1.C scoping for
Outcomes 2/3/4 is appropriate.

## 9. Anomalies and caveats

- The tighter-than-expected reproducibility check surfaced a subtle
  pipeline detail: in the in-process recompute path, computing the
  speed channel directly from numpy velocity arrays (`np.linalg.norm`)
  produces ε-level differences from the canonical CSV→`extract_features`
  path, and `standardize_window` divides by the resulting near-zero std,
  amplifying the difference into a ~2× change in Φ_spectral at the
  representative λ=2.4 window when MI is low. The mechanism diagnostic in
  this verdict goes through the canonical CSV path (matches parquet
  bit-for-bit). This is flagged as a minor reproducibility note, not a
  bug fix request — the Φ values reported in published parquets are
  consistent with the canonical path, and the issue only surfaces when
  bypassing telemetry. Per Phase5.md scope, no changes to Phase 1–4
  modules are within scope of this session.
- λ=0.0 seed 6 and seed 7 have anomalously low leader compactness (2.9
  and 3.7) compared to the rest (12–30), driven by initial-condition
  clustering of the leader sub-set. They also have correspondingly higher
  Φ (173 and 189) and higher polarization (0.87 and 0.94). These are
  legitimate seeds — the simulator is reproducible and the spread reflects
  initial-condition sensitivity, not error — and inflate the cross-seed
  CI on compactness at λ=0.0. The leadership_sweep mean compactness at
  λ=0.0 is therefore reported with wide CI, and is not load-bearing for
  the verdict.
- The λ=2.4 representative window's Φ (7.36) is slightly above the
  per-seed mean (6.02). Window selection picked the steady-state window
  where Φ was closest to the per-seed mean; the 1.3-point gap is the
  smallest available among the 31 steady-state windows for this seed,
  reflecting the heavy-tailed within-run distribution.
- A reasonable follow-up not done in this session: **leader-only σ_u**
  versus **follower-only σ_u** at high λ. The compressibility prediction
  was specifically about within-leader-subset compression; if leader σ_u
  dropped sharply at high λ even while global σ_u did not, the picture
  could shift toward "compressibility within the leader subset, drowned
  out in the global average by follower wobble." This would not change
  the Outcome-4 verdict (the MI-matrix mechanism diagnostic already
  fails three compressibility descriptors regardless), but it would
  refine the description of the mechanism. The aggregate JSON contains
  the per-step velocities; this analysis can be added if Session 2 or
  Tier 1.C wants it.
