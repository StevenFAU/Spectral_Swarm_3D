# Spectral Swarm 3D Phases

## Project Overview

This repository contains the 3D extension of the spectral-topological swarm analysis pipeline. It is developed independently of the 2D proof of concept (preserved at `github.com/StevenFAU/Spectral_Swarm`, tag `v0.1-2d-poc`) to keep both codebases clean, independently citable, and free from cross-coupling. Three goals drive the 3D work:

1. **Methodological fidelity.** Restore the methodology-specified KSG mutual-information estimator and mean alignment rule (Bailey 2026 §3.1, §3.4), and implement the augmented snapshot embedding (§3.5). The 2D proof of concept substituted a Gaussian closed-form MI estimator for pipeline-budget reasons and used a sum alignment variant for practical flocking; the 3D implementation removes both deviations.
2. **Dimension-specific analytical reach.** Add H2 persistent homology to detect enclosed voids (Zomorodian & Carlsson 2005) and define a dimension-agnostic milling tangent that produces spherical-shell configurations rather than a planar ring embedded in 3D space.
3. **Reproducibility and robustness.** Explicit per-run metadata, dependency pinning, surrogate null testing, and bootstrap confidence intervals sit alongside the core pipeline. Measurement choices are aligned with standard practice in applied information theory (Kraskov et al. 2004; Cohen-Steiner et al. 2007; Perea & Harer 2015).

**Repository:** `github.com/StevenFAU/Spectral_Swarm_3D` (private)
**Predecessor:** `github.com/StevenFAU/Spectral_Swarm` at tag `v0.1-2d-poc` (frozen 2D proof of concept)

## Key References

Two primary papers define the methodology; additional references anchor specific implementation choices.

- **Bailey, M. M. (2026).** *Spectral and Topological Methods Comparison in Swarms.* — methodology paper specifying the full 2D simulation and analysis pipeline.
- **Bailey, M. M., & Schneider, S. L. (2025).** *When Wholes Resist Decomposition: A Spectral Measure of Epistemic Emergence.* — introduces Φ_spectral and validates its behavior across random, transitional, synchronized, and CTLN systems.

Supporting references, grouped by the decision they anchor:

**Simulation substrate.**
- ter Hoeven, E., et al. (2025). *Mesa 3: Agent-based modeling with Python in 2025.* JOSS 10(107), 7668.
- Reynolds, C. W. (1987). *Flocks, Herds, and Schools: A Distributed Behavioral Model.* ACM SIGGRAPH.
- Vicsek, T., et al. (1995). *Novel Type of Phase Transition in a System of Self-Driven Particles.* Phys. Rev. Lett. 75(6), 1226.

**Mutual information estimation.**
- Kraskov, A., Stögbauer, H., & Grassberger, P. (2004). *Estimating Mutual Information.* Phys. Rev. E 69, 066138. — KSG estimator; methodology §3.4 primary specification.
- Barrett, A. B., & Seth, A. K. (2011). *Practical Measures of Integrated Information for Time-Series Data.* PLOS Comput. Biol. 7(1), e1001052. — lineage of practical MI-based integration measurement.
- Mediano, P. A. M., Seth, A. K., & Barrett, A. B. (2019). *Measuring Integrated Information: Comparison of Candidate Measures in Theory and Simulation.* Entropy 21(1), 17.

**Spectral analysis.**
- Fiedler, M. (1973). *Algebraic Connectivity of Graphs.* Czech. Math. J.
- von Luxburg, U. (2007). *A Tutorial on Spectral Clustering.* Stat. Comput. 17(4), 395.

**Persistent homology.**
- Edelsbrunner, H., Letscher, D., & Zomorodian, A. (2002). *Topological Persistence and Simplification.* DCG.
- Zomorodian, A., & Carlsson, G. (2005). *Computing Persistent Homology.* DCG.
- Carlsson, G. (2009). *Topology and Data.* Bull. AMS.
- Cohen-Steiner, D., Edelsbrunner, H., & Harer, J. (2007). *Stability of Persistence Diagrams.* DCG. — bottleneck-distance stability guarantees.
- Tralie, C., Saul, N., & Bar-On, R. (2018). *Ripser.py: A Lean Persistent Homology Library for Python.* JOSS 3(29), 925.
- Perea, J. A., & Harer, J. (2015). *Sliding Windows and Persistence.* FoCM 15(3), 799. — theoretical backbone of the trajectory cloud.

**TDA of collective motion.**
- Topaz, C. M., Ziegelmeier, L., & Halverson, T. (2015). *Topological Data Analysis of Biological Aggregation Models.* PLOS ONE 10(5), e0126383.
- Bhaskar, D., et al. (2019). *Analyzing Collective Motion with Machine Learning and Topology.* Chaos 29, 123125.
- Bailey, M. M. (2026). *Quotient Geometry and Persistence-Stable Metrics for Swarm Configurations.* arXiv:2603.18041.

---

## Design Decisions

Each decision is classified by its relationship to the methodology paper: **methodology restoration** (addressing a 2D deviation), **methodology-consistent extension** (2D→3D generalization faithful to the methodology's intent), **novel formulation** (new in 3D where the methodology is silent), or **preserved 2D choice** (continuation from 2D with documented justification).

### Cluster A — Simulator Foundation

**A1. Mesa 3 continuous space in 3D.** *(Methodology-consistent extension.)* Bailey (2026) §3.1 prescribes Mesa 3. The `mesa.experimental.continuous_space.ContinuousSpace` class accepts n-dimensional domains via a `dimensions` parameter of shape `(D, 2)` (ter Hoeven et al. 2025). The 2D code's `np.array([[0, L], [0, L]])` becomes `np.array([[0, L], [0, L], [0, L]])`. No Mesa API change, no fallback logic needed.

**A2. Domain size and length scaling.** *(Project-specific choice.)* Set `L = 50`, keeping `N=40`, `r_v=10`, `speed=1.0`. Rationale: preserves the expected uniform neighbor count from 2D — in 3D, `(N−1)·(4π/3)·r_v³/L³ ≈ 1.31`, matching 2D's `(N−1)·π·r_v²/L_2D² ≈ 1.22`. Milling radius scales with L: `milling_R = 11` (from 2D's 22 at L=100). Split waypoints scale to `(12.5, 37.5, 12.5)` and `(37.5, 12.5, 37.5)`. Fixed LCC threshold in classical baselines scales from 12.0 (2D, r/L=0.12) to 6.0 (3D, same ratio).

**A3. Milling force — velocity-projected tangent formulation.** *(Novel formulation; dimension-agnostic extension.)* Bailey (2026) §3.2 specifies milling only in 2D, with fixed CCW tangent `τ_i = (−r̂_y, r̂_x)`. In 3D we use a dimension-agnostic formulation that reduces to the 2D prescription when motion is planar:

```
r_i     = x_i − x_c,                  x_c = (L/2, L/2, L/2)
r̂_i     = r_i / ||r_i||
v_tan,i = v_i − (v_i · r̂_i) r̂_i
τ̂_i     = v_tan,i / ||v_tan,i||       (fallback: Gram-Schmidt unit tangent if ||v_tan,i|| < ε)
m_i     = μ · (τ̂_i + κ · (R − r_i) · r̂_i)
```

Under planar motion `τ̂_i = (−r̂_y, r̂_x)` exactly (up to sign determined by initial velocity direction), so 2D behavior is recovered as a limiting case. The velocity-projected formulation allows agents to orbit in their own initial planes, producing a shell configuration suitable for H2 detection, rather than the equatorial ring that a fixed-axis `τ_i = ẑ × r̂_i` would produce (the latter has vanishing tangent force at the poles).

**A4. Initial velocity distribution.** *(Methodology-consistent extension.)* Uniform on S² via inverse-CDF sampling:
```
z ∼ U(−1, 1),  φ ∼ U(0, 2π)
u = (√(1 − z²) cos φ,  √(1 − z²) sin φ,  z)
v_i(0) = speed · u
```
Direct 3D analog of the 2D uniform-angle initialization.

**A5. Leader waypoints in 3D.** *(Methodology-consistent extension with intentional design choice.)* Default waypoint `(0.8L, 0.8L, 0.8L) = (40, 40, 40)`, matching Bailey (2026) §3.2's diagonal convention. Split-merge waypoints at opposite cube corners: group 0 → `(0.25L, 0.75L, 0.25L)`, group 1 → `(0.75L, 0.25L, 0.75L)`. Diagonal-opposite placement ensures the split probes genuine 3D reorganization rather than collapsing to a 2D scenario with a trivial z-coordinate.

**A6. Alignment rule — mean alignment restored.** *(Methodology restoration.)* Implement:
```
a_i(t) = (1/|N_i(t)|) · Σ_{j ∈ N_i(t)} v_j(t)
```
per Bailey (2026) §3.1. The 2D sum variant is preserved as an optional config flag (`alignment_rule: "mean" | "sum"`, default `"mean"`) for sensitivity analysis. Baseline w_a is recalibrated to satisfy the Phase 1 polarization criterion under mean alignment; the alignment sweep values themselves remain at methodology-specified `{0.0, 0.6, 1.2, 1.8}`.

**A7. Activation / update order.** *(Preserved 2D choice, made explicit.)* Bailey (2026) §3.1 wording ("agents activated in randomized order at each time step using Mesa's agent-set activation interface") is compatible with sequential random-order updating. The 2D code uses synchronous vectorized numpy updates: `agent.step()` is a no-op; the model reads the full position/velocity state once, computes all forces, and writes all updates simultaneously. This is standard in flocking literature (Reynolds 1987; Vicsek et al. 1995) because it eliminates order-of-update artifacts. We preserve the synchronous approach in 3D for consistency with 2D results and standard practice.

### Cluster B — Analysis

**B1. Primary feature set.** *(Methodology-consistent extension.)* Use `(speed, u_x, u_y, u_z)` at d=4, where `(u_x, u_y, u_z) = v_i/||v_i||` is the unit velocity vector. This is the direct 3D analog of Bailey (2026) §3.3's `(speed, sin θ, cos θ)` at d=3. The unit-vector encoding avoids the singularities of (azimuth, elevation) at the poles, paralleling the methodology's motivation for (sin θ, cos θ) over raw angle. Secondary sets: `vxvyvz` at d=3, `full = (x,y,z,vx,vy,vz)` at d=6 (direct extension of the methodology's `(x, y, vx, vy)` supplementary set).

The constraint `u_x² + u_y² + u_z² = 1` makes the 3×3 velocity sub-covariance rank-2; the existing ridge ε=1e-8 in `mi.py` handles this identically to 2D's rank-1 sin²+cos²=1 case, which has been empirically validated in the 2D test suite.

**B2. Window length.** *(Project-specific choice.)* Primary W=40 for d=4. W=50 for d=6 full feature set (joint covariance 12×12 needs comfortable sample-to-parameter ratio). Stride=1 default, stride=5 for sweep orchestration.

For calibration: Bailey & Schneider (2025) §3.5 used W=10 with b=3 bins on N=50 oscillator systems. Our W=40 at N=40 is substantially more conservative in sample density per window, reflecting the methodology paper's migration from histogram MI (appropriate for W=10) to KSG (requires larger W for acceptable bias; Kraskov et al. 2004).

**B3. Augmented snapshot embedding.** *(Methodology restoration.)* Bailey (2026) §3.5 specifies, "in selected robustness analyses and the custom leadership sweep," an augmented snapshot `y_i = (x_i, y_i, β·vx_i, β·vy_i)` with β=0.35. The 2D code never implemented this. In 3D, implement as config flag `snapshot_augmented: bool`, default `false`. When true: `y_i = (x_i, y_i, z_i, β·vx_i, β·vy_i, β·vz_i)` with β=0.35.

**B4. H2 persistent homology.** *(Methodology-consistent extension.)* Bailey (2026) §3.5 specifies Ripser with maxdim=1 (H0, H1). For 3D point clouds, H2 captures enclosed voids — a signal meaningful only in dimensions ≥ 3. Extension to maxdim=2 is standard in TDA (Zomorodian & Carlsson 2005; Carlsson 2009) and supported by Ripser's interface (Tralie et al. 2018). Add 8 new columns: `snap_TP_2, snap_MP_2, snap_B_base_2, snap_B_prev_2, traj_TP_2, traj_MP_2, traj_B_base_2, traj_B_prev_2`. Extend `persistence_summaries` loop to `for k in range(3)`. Snapshot H2 is the primary interpretation target; trajectory H2 (ambient dimension W·d = 160 at d=4, W=40) is exploratory — the sliding-windows-and-persistence foundation (Perea & Harer 2015) proves that trajectory embeddings carry persistence-detectable structure, but H2 on such high-ambient-dimension data is less established in the swarm literature than H0 and H1.

**B5. Milling score baseline.** *(Methodology-consistent extension.)* Bailey (2026) §3.6 defines 2D milling as `M(t) = (1/N) Σ |r̂_i × v̂_i|` with the 2D scalar cross product. Two dimension-agnostic forms:

- **Primary:** `mean |r̂_i × v̂_i|` using the 3D vector cross product magnitude. Reduces to the 2D methodology definition in the planar limit, since `|r̂ × v̂|` equals the absolute value of the 2D scalar cross in xy-plane motion.
- **Secondary:** Angular momentum norm, `||(1/N) Σ r_i × v_i||`, normalized by max over simulation. Measures *global* rotational coherence; complementary to the per-agent mean and more informative for genuine 3D swirling.

**B6. MI estimator — KSG as primary.** *(Methodology restoration.)* Bailey (2026) §3.4 specifies the Kraskov-Stögbauer-Grassberger k-nearest-neighbor estimator (Kraskov et al. 2004) as primary, with histogram MI as sensitivity check. The 2D code used a Gaussian closed-form estimator as primary for pipeline-budget reasons; the 3D production code restores KSG.

**KSG implementation requirements:**
- Each agent's window features are standardized per-channel before MI estimation: `z_k = (f_k − μ_{k,i}) / σ_{k,i}` where μ and σ are computed across the W time steps for agent i and channel k independently. This is Bailey (2026) §3.4's explicit "per-agent standardization of each feature channel within the window."
- MI is estimated for each ordered pair `(i, j)` on the joint 2d-dimensional space, following Kraskov et al. 2004 equation (8) with k=5 (methodology default) and Chebyshev (L∞) metric.
- Implementation uses `scipy.spatial.cKDTree` for k-NN queries rather than adding a dependency on a dedicated MI package; this keeps the dependency surface minimal and has been validated in the 2D test suite's `test_gaussian_mi_known_correlation` pattern.
- Small noise `~ U(−ε, ε)` with ε=1e-10 added to continuous features before k-NN estimation to break ties (standard practice; sklearn's `mutual_info_regression` does the same internally).

**Estimator lineup in 3D code:** `mi_matrix_ksg` (primary), `mi_matrix_histogram` (sensitivity check per §3.4), `mi_matrix_gaussian` (retained for 2D-to-3D direct comparability). Config flag `estimator: "ksg" | "histogram" | "gaussian"`, default `"ksg"`.

**Epistemic note (methodology §3.4 verbatim):** "Because the W observations come from consecutive time points, serial autocorrelation inside a window is retained rather than explicitly removed. For that reason, we interpret Φ_spectral as an operational windowed dependence score rather than an unbiased population estimate of a static MI graph." This caveat applies to all three estimators and is inherited from the methodology.

### Cluster C — Downstream

**C1. No pre-committed alignment xfail.** *(Methodology-grounded choice.)* Bailey & Schneider (2025) §4.2–§4.3 makes a specific prediction about Φ_spectral across coordination regimes: moderate coupling (§4.2 transitional regime) peaks Φ; perfect coherence (§4.3 synchronized regime) collapses Φ due to compressibility. Under mean alignment (A6) and KSG (B6), the 3D alignment sweep `w_a ∈ {0.0, 0.6, 1.2, 1.8}` directly tests this prediction: low w_a ≈ random (moderate Φ), intermediate w_a ≈ transitional (peak Φ), high w_a ≈ synchronized (low Φ). Monotonicity is not assumed in advance; tests are written to match observed behavior after the sweep runs.

**C2. Column schema changes.** *(Mechanical, tracked for completeness.)* Spectral metrics unchanged. TDA metrics gain 8 H2 entries. Classical metrics gain `angular_momentum_norm` from B5. `_TDA_COMPARE` in `comparison.py` extended with H2 columns. Test fixtures in `test_aggregation.py` and `test_comparison.py` updated.

**C3. Sweep conditions.** *(Methodology-specified values where available; project choice for extensions.)*

- **Alignment:** `w_a ∈ {0.0, 0.6, 1.2, 1.8}` per §3.7. Methodology values used directly now that mean alignment is restored.
- **Leadership:** `λ ∈ {0.0, 0.8, 1.6, 2.4}`, leader fraction fixed at 0.20 per §3.7.
- **Jamming:** `α_jam ∈ {1.0, 0.5, 0.2}` per §3.7.
- **Split-merge:** 3D diagonal waypoints per A5.
- **Milling:** `μ ∈ {0.0, 0.4, 0.8, 1.2}` per §3.7, R=11 (scaled), velocity-projected tangent (A3).
- **Noise:** `σ ∈ {0.0, 0.05, 0.1, 0.2, 0.5}` per §3.7.
- **Sensitivity:** 3 estimators × 3 feature sets = **9 combinations**: `{kinematic, vxvyvz, full} × {ksg, histogram, gaussian}`. Methodology §3.7 specified 6 (2 estimators × 3 features); we extend to 9 to include the Gaussian estimator, enabling a direct 2D–3D comparison bridge and quantifying estimator-choice robustness.
- **N-sensitivity:** `N ∈ {40, 80, 160}` — project-specific robustness check. 2D used {20, 40, 80}; N=20 is too sparse in 3D at L=50.
- **W-sensitivity:** `W ∈ {30, 40, 50, 60}` — project-specific check.
- **Alignment-rule sensitivity:** `mean` vs `sum` at matched-flocking w_a, baseline scenario, 5 seeds each. Supports A6 restoration.

**Seeds per condition:** 10 for primary sweeps (alignment, leadership, jamming, split-merge, milling, noise), 5 for sensitivity and robustness sweeps. Mirrors 2D design and methodology §3.8 replication convention.

**C4. Visualization.** *(Methodology-consistent extension; standard academic practice.)* Matplotlib `Axes3D` with `FuncAnimation`, MP4 output via ffmpeg writer. Mirrors the visual conventions of Topaz et al. (2015) and Bhaskar et al. (2019). Two new functions in `plotting.py`: `plot_snapshot_3d` (static 3D scatter, optionally colored by Fiedler partition) and `animate_trajectory_3d` (full-run animation). One new script `render_scenario_videos.py` producing per-scenario MP4s.

### Cluster D — Robustness and Reproducibility

**D1. Surrogate null testing.** *(Methodology-consistent extension.)* For each scenario, compute Φ_spectral and top TDA summaries on **trajectory-shuffled surrogates** — telemetry where per-agent time series are independently circularly shifted, destroying cross-agent temporal dependence while preserving marginal distributions. If observed Φ_spectral is substantially higher than the surrogate distribution's Φ_spectral, the measured integration is real rather than an artifact of the estimator or of finite-sample fluctuation. Standard practice in time-series MI analysis. Implemented as an optional analysis in Phase 5, run on one representative seed per scenario (10-shuffle null distribution).

**D2. Bootstrap confidence intervals within run.** *(Standard practice.)* The 2D `comparison.py` already provides bootstrap CIs across seeds for η². Add within-run bootstrap: for each run, resample analysis windows with replacement to produce CIs on steady-state means of Φ_spectral and key TDA summaries. This complements across-seed variance with within-run uncertainty and is essential for reporting error bars on single-seed figures.

**D3. Feature standardization made explicit.** *(Methodology compliance.)* Per B6, KSG requires per-agent per-channel standardization within each window before MI estimation. This is made an explicit step in `mi.py` (not buried inside the estimator), with a dedicated test verifying: after standardization, each agent's window features have mean 0 and std 1 along the W-axis (or std = 0 for constant channels, with the channel zeroed).

**D4. Multiple-comparisons discipline.** *(Reporting stance.)* With 11 sweeps × ~30 metrics, ~330 η² estimates are computed. Rather than applying a single-test significance threshold with post-hoc correction, the reporting convention throughout is **effect size (η²) with bootstrap CIs**, not p-value significance. This matches the 2D code's existing reporting style and is the standard practice in complex-systems and swarm literature. Where significance claims are made (e.g., for the cross-scenario agreement/divergence Spearman correlations), they are flagged explicitly and interpreted in context.

**D5. Dependency pinning.** *(Reproducibility.)* The repo's `pyproject.toml` pins exact versions of `mesa`, `ripser`, `persim`, `scipy`, `numpy`, and `scikit-learn` using `==` rather than `>=` for known-good versions, with lower bounds for anything not yet tested. A `requirements-lock.txt` is generated via `pip freeze` and committed, capturing the full transitive dependency closure.

**D6. Reproducibility metadata.** *(Provenance.)* Each sweep run's metadata JSON records, in addition to config and seed: (a) git commit hash of the code at run time; (b) Python version; (c) versions of `mesa`, `ripser`, `numpy`, `scipy` at run time; (d) hostname and timestamp. This enables precise post-hoc identification of which code produced which outputs, and surfaces environmental drift that could compromise cross-run comparability.

**D7. Boundary-effect diagnostic.** *(Finite-size awareness.)* The reflective cubic domain at L=50 with r_v=10 means a non-trivial volume fraction is within r_v of a boundary: `(L³ − (L−2r_v)³)/L³ ≈ 78%`. Before Phase 4 results are trusted, verify in Phase 1 that boundary-reflected agents do not disproportionately contribute to any metric: compute Φ_spectral and key TDA summaries conditional on (a) fraction of agents reflected in the last window and (b) mean distance from centroid to nearest boundary. If these conditional metrics differ substantially from unconditioned, flag for investigation. This is a sanity check, not a primary result.

**D8. Bottleneck-vs-total-persistence distinction.** *(Methodological honesty.)* Cohen-Steiner et al. (2007) proves that **bottleneck distances** between persistence diagrams are Lipschitz-stable in the Hausdorff distance of the underlying point clouds. **Total persistence** has no comparable stability guarantee — it is a coarser, more noise-sensitive summary. Accordingly: where the two metrics agree on a trend, both are reported. Where they disagree, the bottleneck-distance result is treated as more reliable, and the disagreement is flagged as a finding about metric sensitivity rather than a contradiction. This is already implicit in the 2D code (which reports both); the 3D plan makes the ranking explicit.

**D9. H2 persistence at N=40 does not work as a primary observable.**
(Finding from Phase 3 diagnostics.) H2 on spatial snapshots of N=40 agents
on a spherical shell at R=11 with shell thickness ~0.7 puts enclosed voids
below Rips filtration resolution (shell-thickness-to-radius ratio produces
over-triangulation before the void's scale is reached; nearest-neighbor
spacing ~0.17 on a shell of radius ~13). H2 on trajectory clouds at 40
points in 160–320D ambient space is below coverage threshold for H2
detection. Neither condition is correctable within reasonable N (even at
N=160 the ratio is only 1.55) and without methodology deviations (alpha
complex substitution, which would add a new dependency and a deviation
from Ripser). H2 is retained as an exploratory observable in Phase 4,
reported but not used as pass/fail. Classical milling measures (B5) serve
as the milling-sweep primary positive controls instead.

**D10. Trajectory-cloud TDA is systemically noisy at N=40; spatial-snapshot
TDA is the working alternative.** (Finding from Phase 3.5 probe; 3 seeds ×
3 scenarios on `none`, `split_merge`, `jamming` at default parameters.)

*Negative finding — trajectory clouds.* `traj_TP_1` did not reliably
separate either scenario from baseline. Split-merge was consistently below
baseline (ratio ~0.67 on 3/3 seeds — wrong direction for a topological-
event detector). Jamming overlapped baseline entirely. Working mechanistic
hypothesis: coherent flocking at calibrated w_a=1.0 produces rich
trajectory-cloud H1 structure from parallel-curve geometry, which the
tested perturbations modify without disrupting. The probe did not test
other trajectory-cloud metrics (`traj_TP_0`, `traj_MP_k`, trajectory
bottleneck distances) directly; extending the demotion to these metrics
is the consistent stance at N=40 and avoids asymmetric promotion of
observables whose underlying measurement approach has been shown
problematic.

*Positive finding — spatial snapshots.* `snap_TP_1` separates jamming from
baseline cleanly: per-seed non-overlapping (jamming 1.663–2.071, baseline
1.322–1.457), 1.14–1.57× ratios. `snap_TP_0` separates split-merge from
baseline cleanly: 3/3 seeds below baseline (split-merge 72.02–94.10,
baseline 99.30–118.64). Split-merge H0 direction is counter-intuitive;
mechanism (possibly fast H0 collapse from tight leader-group compactness)
requires investigation with 10-seed Phase 4 data.

*Decision.* Phase 4 demotes trajectory-cloud TDA to exploratory. Phase 4
promotes `snap_TP_0` and `snap_TP_1` to primary candidate TDA observables;
D2 bootstrap CIs on 10 seeds formally characterize robustness. The probe
established signs, not distributions; promotion is to "primary candidate,"
not "validated primary," until Phase 4's larger-N statistics resolve
whether the probe patterns hold. Reported as a scientific finding about
embedding choice (snapshot vs. trajectory) at N=40, not as a pipeline
defect.

**D11. Histogram MI estimator saturates at W=40, d=4, n_bins=8; KSG and
Gaussian agree strongly.** (Finding from Phase 4 B2b sensitivity sweep,
5 seeds × 9 estimator×feature combinations, diagnosed by Opus 4.7
max-effort session.) The histogram estimator's joint symbol space
(8⁴ = 4096 cells) vastly exceeds W=40 samples, driving plug-in MI to
its log(W) ≈ 3.69 ceiling regardless of coupling. Observed Φ_spectral
≈ log(W) × Fiedler-cut-size matches prediction to 3%; histogram
per-run CV of 0.03 confirms saturation. KSG ↔ Gaussian Spearman ρ =
1.00 across seeds (window-level 0.75) provides strong cross-estimator
robustness evidence between the two non-saturated estimators, which
have independent bias mechanisms (k-NN nonparametric vs. closed-form
parametric).

*Decision.* KSG retained as primary per B6. Histogram results in
Phase 4 are reported but interpreted only on sign-of-across-
condition-differences, not within-condition rank or magnitude. A
saturation diagnostic (`phi_norm / log(W)`) is added to
`analyze_sweep.py` to surface per-condition saturation empirically.
The methodology paper's own statement at line 100 of the phases
document ("migration from histogram MI appropriate for W=10 to KSG")
anticipated this exact finding.

---

## Repository Organization

This repository is a standalone Python package. The 2D predecessor work lives in a separate repository and is not duplicated here.

```
Spectral_Swarm_3D/
├── pyproject.toml                  # spectral_swarm_3d package, pinned deps (D5)
├── requirements-lock.txt           # pip freeze of transitive deps
├── conftest.py                     # pytest config, loads configs/default.yaml
├── README.md                       # project landing page
├── CLAUDE.md                       # Claude Code conventions for this repo
├── LICENSE                         # MIT (matching 2D predecessor)
├── SpectralSwarm3DPhases.md        # this plan
├── Phase0.md                       # scaffolding record, for provenance
├── ResearchContext.md              # research positioning, companion doc
│
├── src/spectral_swarm_3d/
│   ├── __init__.py
│   ├── model.py                    # Phase 1: BoidSwarmModel3D
│   ├── agent.py                    # Phase 1: SwarmAgent3D
│   ├── scenarios.py                # Phase 1: waypoints, milling force
│   ├── telemetry.py                # Phase 1 + D6: CSV logger, env metadata
│   └── analysis/
│       ├── __init__.py
│       ├── features.py             # Phase 2: kinematic, vxvyvz, full
│       ├── mi.py                   # Phase 2 + B6: ksg, histogram, gaussian
│       ├── spectral.py             # Phase 2: Laplacian, Fiedler, Φ_spectral
│       ├── tda.py                  # Phase 3 + B3 + B4: H2 persistence
│       ├── classical.py            # Phase 2 + B5: polarization, milling, L-norm
│       ├── aggregation.py          # Phase 4 + D2: bootstrap CIs
│       ├── comparison.py           # Phase 5 + C2: extended column lists
│       ├── surrogates.py           # Phase 5 + D1: null testing
│       └── plotting.py             # Phase 5 + C4: 3D plots, FuncAnimation
│
├── tests/
│   ├── __init__.py
│   ├── test_scaffolding.py         # Phase 0 real tests
│   ├── test_boids.py               # Phase 1 stub
│   ├── test_scenarios.py           # Phase 1 stub
│   ├── test_telemetry.py           # Phase 1 stub
│   ├── test_features.py            # Phase 2 stub
│   ├── test_mi.py                  # Phase 2 stub
│   ├── test_spectral.py            # Phase 2 stub
│   ├── test_classical.py           # Phase 2 stub
│   ├── test_tda.py                 # Phase 3 stub
│   ├── test_aggregation.py         # Phase 4 stub
│   └── test_comparison.py          # Phase 5 stub
│
├── configs/
│   └── default.yaml                # all 3D parameters
│
├── scripts/
│   ├── run_single.py
│   ├── run_sweep.py
│   ├── analyze_sweep.py
│   ├── run_comparison.py
│   ├── run_surrogates.py           # Phase 5, D1
│   └── render_scenario_videos.py   # Phase 5, C4
│
├── notebooks/                      # exploration, not canonical
│   └── .gitkeep
│
├── outputs/                        # Parquet, figures, MP4
│   └── .gitkeep
│
└── docs/
    ├── Swarm_Methodology2.pdf
    ├── when_wholes_resist_decomposition.pdf
    └── (other supporting PDFs as needed)
```

Install: `pip install -e .` from repository root.
Run tests: `pytest tests/ -v` from repository root.

---

## Phase Structure

Complete each phase fully before moving on. Each phase has explicit pass/fail criteria. Claude model recommendations apply to Claude Code sessions.

---

### PHASE 0 — Scaffolding and Migration

**Scope.** Initialize this repository with the scaffolding first prototyped in the 2D predecessor repo, flattened from the `3d/` subdirectory into a standalone top-level Python project. Populate `pyproject.toml` (with pins per D5), `default.yaml` with all 3D parameters, module and test stubs, and reproducibility metadata infrastructure.

**Claude model:** Sonnet 4.6. Pure file creation and verification, no novel reasoning.

**Estimated effort:** 1 day (migration and verification), previously scaffolded in predecessor repo.

**Pass/Fail.**
- [ ] `pip install -e .` from repository root succeeds.
- [ ] `pytest tests/ -v` runs; `test_scaffolding.py` passes; other test files are skipped with the Phase stub reason.
- [ ] `configs/default.yaml` loads with PyYAML; includes all 3D parameters (`L=50`, `milling_R=11`, `alignment_rule`, `snapshot_augmented`, `fixed_cc_threshold=6.0`, `estimator="ksg"`, `k_ksg=5`).
- [ ] `pyproject.toml` declares `spectral_swarm_3d`, Python ≥3.12, Mesa ≥3.4.
- [ ] `requirements-lock.txt` exists and is non-empty.
- [ ] `CLAUDE.md`, `README.md`, `SpectralSwarm3DPhases.md`, `Phase0.md`, `ResearchContext.md` all present at repo root.
- [ ] Repository structure matches the layout in "Repository Organization."
- [ ] Initial commit pushed to `main` on `github.com/StevenFAU/Spectral_Swarm_3D`.

---

### PHASE 1 — 3D Boids Simulator + Telemetry

**Scope.** Port the simulator with all Cluster A decisions applied. Produce reproducible 500-step 3D telemetry for all five scenarios (none, leader, jamming, split_merge, milling). Wire up reproducibility metadata (D6) and boundary-effect diagnostics (D7).

**Architecture addition.**
```
src/spectral_swarm_3d/
    ├── model.py          # BoidSwarmModel3D (Mesa 3 experimental ContinuousSpace, 3D)
    ├── agent.py          # SwarmAgent3D
    ├── scenarios.py      # effective_boids_params, leader_waypoint, milling_force
    └── telemetry.py      # CSV logger with z, vz, u_x, u_y, u_z columns
tests/
    ├── test_boids.py
    ├── test_scenarios.py
    └── test_telemetry.py
```

**Key implementation notes.**
- Mesa 3 space: `ContinuousSpace(dimensions=np.array([[0, L], [0, L], [0, L]]), torus=False, n_agents=N, random=_stdlib_random.Random(seed))`.
- Agent velocities initialized via uniform-on-S² (A4).
- Synchronous numpy update in `model.step()` (A7); reflective BC loop `for dim in range(3)`.
- Alignment: mean (A6). Config flag `alignment_rule` allows sum for sensitivity.
- Milling force: velocity-projected tangent (A3 equations above).
- Telemetry columns: `step, agent_id, x, y, z, vx, vy, vz, speed, u_x, u_y, u_z, is_leader, leader_group, neighbor_count, local_density, scenario_label, near_boundary`. The `near_boundary` flag is 1 if agent is within r_v of any boundary this step (D7).
- **w_a calibration.** Iterative. Start w_a=1.0 with mean alignment, run 10-seed polarization check, adjust until ≥8/10 seeds reach polarization > 0.6 within 200 steps. This calibration sets the baseline w_a for non-alignment sweeps.
- Metadata JSON includes all D6 fields.

**Claude model:** Opus 4.7 for A3 milling implementation and A6 baseline w_a calibration (iterative reasoning about simulator behavior, physically-informed parameter search). Sonnet 4.6 for the remaining mechanical 2D→3D port once formulations are locked.

**Estimated effort:** 4–6 days including calibration.

**Pass/Fail.**
- [ ] 40 agents survive 500 steps without NaN positions or velocities (all five scenarios).
- [ ] All agents stay within `[0, L]³` at every step.
- [ ] Speed invariant: every agent has magnitude exactly `config['speed']` at every step (mirrors 2D `test_speed_constant_throughout_simulation`).
- [ ] Reflective BC test: agent at `[49.5, 25, 25]` with velocity `[1, 0, 0]` has x-velocity flipped after one step and position reflected into domain.
- [ ] With calibrated baseline w_a and mean alignment, polarization > 0.6 within 200 steps for ≥8/10 seeds.
- [ ] Milling scenario: mean radial distance converges to `R=11` by step 500 (within ±7.5 tolerance).
- [ ] Milling spherical-shell diagnostic: std(z-component of agent positions) > 3.0 by step 300 (distinguishes shell from equatorial ring).
- [ ] Split-merge: during split phase, leader group centroids separate by more than `√3 · 0.25L ≈ 21.6` units.
- [ ] Telemetry CSV: `N·T` rows, no missing values, `u_x² + u_y² + u_z² = 1` for every row within floating-point tolerance.
- [ ] Metadata JSON round-trips including `alignment_rule`, `snapshot_augmented`, all 3D parameters, git commit hash, Python version, and pinned package versions (D6).
- [ ] Deterministic reproducibility: same seed produces bit-identical trajectories across two independent runs.
- [ ] Boundary-effect diagnostic (D7): `near_boundary` column logged for every row; mean fraction of near-boundary agents over the full run is computable from telemetry.

---

### PHASE 2 — Φ_spectral Pipeline

**Scope.** Port feature extraction and Laplacian/Fiedler spectral pipeline. Implement three MI estimators (KSG primary, histogram sensitivity, Gaussian retained for 2D bridge). Apply per-channel per-agent standardization (D3).

**Architecture addition.**
```
src/spectral_swarm_3d/analysis/
    ├── features.py       # kinematic (d=4), vxvyvz (d=3), full (d=6)
    ├── mi.py             # mi_matrix_ksg, mi_matrix_histogram, mi_matrix_gaussian
    ├── spectral.py       # Normalized Laplacian, Fiedler, Φ_spectral (dimension-agnostic)
    └── classical.py      # Polarization, milling score (magnitude), angular momentum norm
tests/
    ├── test_features.py
    ├── test_mi.py
    ├── test_spectral.py
    └── test_classical.py
```

**Key implementation notes.**
- `features.py` kinematic set reads `u_x, u_y, u_z` columns directly from telemetry; no reconstruction needed.
- `mi.py` KSG implementation: per-agent per-channel z-score standardization (D3), then Kraskov et al. 2004 equation (8) with k=5, Chebyshev metric, `scipy.spatial.cKDTree` for k-NN queries. Small uniform noise `±1e-10` added to break ties. Returns `(N, N)` symmetric matrix, zero diagonal, non-negative clipped at 0.
- `mi.py` histogram: quantile-binned joint histograms per §3.4; 8 bins per channel with the existing bin-cap mechanism to bound joint symbol space.
- `mi.py` Gaussian: retained from 2D (joint covariance, slogdet, ridge ε=1e-8). Used only in sensitivity sweep and 2D-comparison contexts.
- `spectral.py` structurally identical to 2D — fully dimension-agnostic per Fiedler (1973), von Luxburg (2007), and Bailey & Schneider (2025) §2.3.
- `classical.py` `milling_score = mean |r̂ × v̂|` uses 3D vector cross magnitude. Adds `angular_momentum_norm`.

**Claude model:** Opus 4.7 for KSG implementation correctness verification (implementation must match Kraskov et al. 2004 equation 8, validated against known analytic cases and against sklearn's 1D `mutual_info_regression` for single-feature inputs). Sonnet 4.6 for the remaining mechanical ports.

**Estimated effort:** 3–4 days (KSG implementation is the main time cost).

**Pass/Fail.**
- [ ] **KSG correctness (critical).** For two 1D Gaussians with Pearson r=0.8, W=1000, KSG with k=5 recovers `I = −½log(1 − r²) ≈ 0.5108` within 10% tolerance. Mirrors 2D `test_gaussian_mi_known_correlation`.
- [ ] **KSG agreement with sklearn.** For the same input (2 agents, d=1, W=500), `mi_matrix_ksg` agrees with `sklearn.feature_selection.mutual_info_regression` within 5% (validates basic implementation correctness against an established reference).
- [ ] **KSG multivariate.** For two 2D Gaussians with known joint covariance, KSG recovers the analytic MI within 15% (KSG multivariate has higher variance; tolerance relaxed).
- [ ] **Cross-feature MI test.** Cross-channel dependency (agent i feat-0 predicts agent j feat-1) produces higher pairwise MI than independent case under KSG. Same test as 2D's `test_mi_captures_cross_feature_dependence`.
- [ ] **Standardization explicit test (D3).** A window where agent-0 has features scaled 100× produces the same MI matrix after per-agent standardization as the unscaled version.
- [ ] **Unit-vector rank.** A d=4 window where `(u_x, u_y, u_z)` lies on the unit sphere produces finite, non-NaN MI matrix for all three estimators.
- [ ] **Redundancy-low-Φ check.** A perfectly constant window produces `total_mi ≈ 0` and `Φ_spectral ≈ 0` under all three estimators (validates Bailey & Schneider 2025 §4.3 prediction).
- [ ] **Coordinated-higher-than-random.** `Φ_spectral_coordinated > Φ_spectral_random` under all three estimators.
- [ ] **MI matrix structural properties.** Symmetric, zero diagonal, non-negative for all three estimators.
- [ ] **Fiedler partition non-degenerate.** Two non-empty groups for all windows across a test sweep.
- [ ] **Estimator ordering agreement.** KSG, histogram, and Gaussian agree on the sign of Φ differences across coordinated-vs-random test conditions (sensitivity check per §3.4).
- [ ] **Full pipeline runtime.** 500-step telemetry at stride=5 completes in < 180 seconds under KSG (relaxed from 2D's 60s Gaussian budget; KSG is more expensive per pair but feasible on desktop).

---

### PHASE 3 — TDA Pipeline with H2

**Scope.** Extend persistent homology to `maxdim=2`. Add augmented snapshot option (B3). Extend summary dict to include H2 columns. Flag bottleneck-distance results as the stability-guaranteed summaries per D8.

**Architecture addition.**
```
src/spectral_swarm_3d/analysis/
    └── tda.py            # snapshot_cloud (augmented flag), compute_persistence(maxdim=2)
tests/
    └── test_tda.py
```

**Key implementation notes.**
- `snapshot_cloud(positions, augmented=False, beta=0.35, velocities=None)`: when augmented, returns `(N, 6)` concatenation of positions and `beta * velocities`; else `(N, 3)` pass-through. Implements Bailey (2026) §3.5 augmented embedding.
- `compute_persistence(X, maxdim=2)`: returns `[dgm_H0, dgm_H1, dgm_H2]` via Ripser (Tralie et al. 2018).
- `persistence_summaries` extended: `for k in range(3)` instead of `range(2)`; returns TP_k, MP_k for k∈{0,1,2} always, and conditional bottleneck metrics B_base_k, B_prev_k.
- Baseline/prev caching extended to 3 diagrams each.
- Trajectory cloud construction follows Bailey (2026) §3.5 and Perea & Harer (2015): flattened window features with per-dimension standardization across agents.

**Claude model:** Sonnet 4.6 for the mechanical extension. One targeted Opus 4.7 query to sanity-check H2 interpretation on the 160-dimensional trajectory cloud.

**Estimated effort:** 2–3 days.

**Pass/Fail.**
- [ ] Synthetic spherical shell (N=60 points on radius-R sphere with small noise): `TP_2 > 0`, `MP_2` large relative to H1 (positive control for H2 void detection).
- [ ] Synthetic planar ring (N=60 points on circle embedded in 3D, small noise): `TP_2 ≈ 0`, `TP_1 > 0` (verifies H2 does not false-positive on rings).
- [ ] Synthetic tight cluster: `TP_0, TP_1, TP_2 ≈ 0`.
- [ ] Synthetic two separated clusters: `TP_0 > tight`, `TP_2 ≈ 0`.
- [ ] Augmented snapshot option produces `(N, 6)` when enabled and `(N, 3)` when disabled.
- [ ] Bottleneck-to-self is 0 for all three homology dimensions (stability per Cohen-Steiner et al. 2007).
- [ ] Pipeline handles 500-window 3D telemetry in < 300 seconds.
- [ ] End-to-end integration: simulated milling scenario produces higher `snap_TP_2` than no-milling baseline.
- [ ] Bottleneck-distance stability check (D8): on a synthetic point cloud perturbed by Gaussian noise with σ=0.1, bottleneck distance to the unperturbed diagram scales approximately linearly with σ for small σ (sanity check on the stability theorem's applicability).

---

### PHASE 4 — Experimental Sweeps

Phase 3 closed with decision D9 dropping H2 as a primary observable due to
finite-size geometric limits at N=40 (Cluster D). Phase 3.5 probed H1-on-
trajectory-clouds scenario-specificity across `none`, `split_merge`, and
`jamming` at 3 seeds each; its findings restructure the TDA observable
hierarchy. Trajectory-cloud TDA metrics (`traj_TP_k`, `traj_MP_k`, trajectory
bottleneck distances) are demoted to exploratory observables due to
systemic finite-size noise at N=40; reported but not used as pass/fail.
Spatial-snapshot TDA metrics (`snap_TP_0`, `snap_TP_1`) are promoted to
primary candidate observables based on per-seed non-overlapping separation
on the probe scenarios; Phase 4's 10-seed bootstrap CIs will formally
characterize their robustness. Primary quantitative observables in Phase 4
are therefore Φ_spectral (all sweeps), classical measures (polarization,
milling_score, angular_momentum_norm, local_density, LCC fraction), and
spatial-snapshot TDA (`snap_TP_0`, `snap_TP_1`). TDA noise floors across
the remaining metrics are characterized through D2 within-run bootstrap
CIs as part of the sweep output rather than pre-measured.

**Scope.** Port aggregation pipeline and sweep orchestration. Apply C3 sweep parameter changes. Run all 11 sweep families. Add bootstrap CI (D2) within `aggregate_steady_state`.

**Architecture addition.**
```
src/spectral_swarm_3d/analysis/
    └── aggregation.py    # analyze_run, aggregate_steady_state (with bootstrap CI),
                          # aggregate_event_phases, time_to_coordination, aggregate_across_seeds
scripts/
    ├── run_single.py
    ├── run_sweep.py
    └── analyze_sweep.py
outputs/
    ├── alignment_sweep/, leadership_sweep/, jamming_sweep/, split_merge/,
    ├── milling_sweep/, noise_sweep/, sensitivity/,
    ├── n_sensitivity_N80/, n_sensitivity_N160/, w_sensitivity/,
    └── alignment_rule_sensitivity/
```

**Key implementation notes.**
- `analyze_run` extended with H2 columns and `angular_momentum_norm`. Per §3.8: steady-state = final third of windows; event phases = fully-contained pre/during/post; time-to-coordination at polarization ≥ 0.65 for two consecutive windows.
- `aggregate_steady_state` extended with optional bootstrap CI computation (D2): resample windows with replacement B=1000 times, report 95% CI on each column's mean.
- `run_sweep.py` condition list built per C3, with the 9-condition sensitivity matrix.
- Parquet outputs preserve 2D schema plus new columns. Condition directory names follow 2D conventions for tooling reuse.
- Each Parquet file has a companion `metadata.json` including all D6 reproducibility fields.
- Alignment-rule sensitivity: baseline scenario at calibrated w_a, once with `alignment_rule=mean` and once with `alignment_rule=sum`, 5 seeds each.

**Claude model:** Sonnet 4.6 for orchestration code. Opus 4.7 for result interpretation — especially C1, whether mean alignment + KSG produces the Bailey & Schneider (2025) §4 transitional-regime peak.

**Estimated effort:** 2–3 days development + 1 week runtime (desktop) or shorter on HPC.

**Pass/Fail.**
- [ ] All sweep conditions complete without errors.
- [ ] Results saved as Parquet under `outputs/<sweep>/<condition>/seed<n>.parquet` with companion `metadata.json`.
- [ ] All sweep metadata includes D6 reproducibility fields (git hash, Python version, pinned packages, timestamp).
- [ ] Alignment-rule sensitivity sweep produces both `mean` and `sum` branches cleanly.
- [ ] 9-condition sensitivity sweep produces all 3 estimator × 3 feature set combinations.
- [ ] Milling sweep (primary): milling_score (mean |r̂ × v̂|) increases
      monotonically with μ from μ=0 to μ=1.2. Primary classical positive
      control.
- [ ] Milling sweep (secondary): angular_momentum_norm increases
      monotonically with μ over the same range. Secondary classical
      positive control; global rotational coherence.
- [ ] Milling sweep (exploratory): snap_TP_2, traj_TP_k, and traj_MP_k
      reported. Not pass/fail per D9 (H2 geometric limits) and D10
      (trajectory-cloud noise). Interpretation in Phase 5.
- [ ] Jamming (primary Φ_spectral): Φ_spectral during jam window < pre-jam
      for α=0.2.
- [ ] Jamming (primary TDA candidate): snap_TP_1 at jam condition >
      snap_TP_1 at control for α=0.2, with non-overlapping 95% bootstrap
      CIs across 10 seeds. Phase 3.5 showed 1.14–1.57× per-seed separation
      on 3 seeds; Phase 4 validates whether this holds at larger sample.
- [ ] Split-merge (primary): at least one of Φ_spectral, phi_norm, or
      milling_score shows η² > 0.5 between split and control conditions.
- [ ] Split-merge (primary TDA candidate): snap_TP_0 during split condition
      differs from control with η² > 0.3 and 95% bootstrap CIs not
      overlapping. Phase 3.5 showed consistent below-baseline direction on
      3 seeds; direction is counter-intuitive (splitting swarm produces
      *lower* H0 persistence than coherent baseline) and mechanism requires
      investigation in Phase 4. Pass/fail is separation magnitude, not a
      pre-committed direction.
- [ ] Non-milling sweeps (leadership, noise, alignment): Φ_spectral and
      classical measures treated as primary observables. snap_TP_0,
      snap_TP_1 reported as primary TDA candidates and characterized
      through D2 bootstrap CIs. Trajectory-cloud metrics reported as
      exploratory.
- [ ] Bootstrap CIs (D2) computed and stored for each run's steady-state
      summary, and for all TDA metrics across conditions. These CIs
      characterize the TDA noise floor empirically for Phase 5
      interpretation.
- [ ] Bootstrap CIs (D2) computed and stored for each run's steady-state summary.

---

### PHASE 5 — Comparison Analysis, Surrogates, and 3D Visualization

**Scope.** Port comparison pipeline with H2 column additions. Implement surrogate null testing (D1). Add matplotlib 3D visualization functions. Render per-scenario animations. Produce all figures and tables.

**Architecture addition.**
```
src/spectral_swarm_3d/analysis/
    ├── comparison.py     # SPECTRAL/TDA/CLASSICAL/_TDA_COMPARE column lists extended
    ├── surrogates.py     # D1: trajectory-shuffled null distributions
    └── plotting.py       # configure_style, plot_time_series (extended to H2),
                          # plot_agreement_heatmap (H2 in _TDA_COMPARE),
                          # plot_snapshot_3d (NEW), animate_trajectory_3d (NEW)
scripts/
    ├── run_comparison.py
    ├── run_surrogates.py      # NEW: D1 surrogate analysis
    └── render_scenario_videos.py
notebooks/
    └── exploration_3d.ipynb
```

**Key implementation notes.**
- `_TDA_COMPARE` extended with H2 entries: `snap_TP_2, snap_MP_2, snap_B_base_2, traj_TP_2, traj_MP_2, traj_B_base_2`.
- `surrogates.py` implements circular-shift shuffling per-agent per-channel; runs one representative seed per scenario with 10 shuffle iterations, computes observed-vs-null Φ_spectral and top TDA summaries.
- `plot_snapshot_3d(positions, velocities, fiedler_partition=None, ax=None)`: matplotlib 3D scatter with optional Fiedler partition coloring and velocity quivers.
- `animate_trajectory_3d(telemetry_csv, output_path, step_range=None, fps=30)`: `FuncAnimation` over 3D scatter, MP4 output via ffmpeg writer.
- `render_scenario_videos.py`: loops over five scenarios, runs one seed each, produces one MP4 per scenario.

**Claude model:** Sonnet 4.6 for plotting and surrogate code. Opus 4.7 for figure composition and result interpretation.

**Estimated effort:** 5–6 days.

**Pass/Fail.**
- [ ] All comparison functions run on full sweep data without errors.
- [ ] η² sensitivity tables generated for all 11 sweeps with bootstrap CIs.
- [ ] Agreement/divergence heatmaps include H2 columns.
- [ ] At least one sweep shows spectral-topological divergence (core hypothesis of Bailey 2026).
- [ ] Surrogate null testing (D1): observed Φ_spectral substantially exceeds surrogate distribution for coordinated scenarios (leader, milling) but not for random baseline at w_a=0.
- [ ] `plot_snapshot_3d` renders cleanly for each of the 5 scenarios at step 250.
- [ ] `animate_trajectory_3d` produces five MP4 files, each < 30 MB, playable in standard video viewers.
- [ ] All numerical results reproducible from saved telemetry and analysis code, using the metadata stored in D6.
- [ ] Figure set identified: time-series overlays per scenario, sensitivity bar charts per sweep, agreement heatmaps combining sweeps, matched-control deltas, monitoring ROC, surrogate null comparisons.

---

## Global Rules

- Python 3.12+ (aligned with Mesa 3.4+ requirement).
- Mesa 3 with `mesa.experimental.continuous_space` (n-dimensional support via ter Hoeven et al. 2025).
- Neighbor queries via `scipy.spatial.cKDTree` rebuilt each step (same pattern as 2D; Mesa's ContinuousSpace not used for neighbor lookup).
- All randomness via explicit `np.random.default_rng(seed)` and `random.Random(seed)` for Mesa's internal RNG. Seed is propagated through all stochastic operations including MI tie-breaking noise (B6) and bootstrap resampling (D2).
- Telemetry as CSV (one file per run); analysis as Parquet (one per run per sweep condition). Each output has a companion metadata JSON with D6 reproducibility fields.
- Configuration via YAML, loaded with PyYAML.
- Type hints everywhere; docstrings on all public functions.
- `pytest` for tests; `ruff` for linting (line length 100, `select = ["E", "F", "W"]`).
- Version-pin core dependencies in `pyproject.toml` per D5; regenerate `requirements-lock.txt` when dependencies change and commit both.
- Reporting convention: effect sizes (η² with bootstrap CIs) rather than p-values throughout (D4). Significance claims, when made, are flagged explicitly.
- No phase advances until the previous phase's pass/fail criteria are all met.
- Methodology conformance (Bailey 2026, Bailey & Schneider 2025) is the default; deviations are explicit, justified, and documented in the decision clusters above.

---

## Dependencies

```
mesa>=3.4
numpy>=2.0
scipy>=1.13
scikit-learn>=1.5
ripser>=0.6.8
persim>=0.3.5
pandas>=2.2
pyarrow>=17.0
pyyaml>=6.0
matplotlib>=3.9
networkx>=3.3
ffmpeg-python>=0.2    # for MP4 rendering via FuncAnimation
```

Exact versions in `requirements-lock.txt` per D5. Dev extras: `ruff`, `pytest`.

---

## Methodology Conformance Notes

Implementation choices classified by their relationship to Bailey (2026):

**Methodology restorations** (addressing 2D-code deviations):
- Mean alignment (A6) restores §3.1 specification verbatim.
- KSG mutual information estimator (B6) restores §3.4 primary estimator; the 2D code's Gaussian closed-form is retained as one of three estimator choices in the 9-condition sensitivity sweep.
- Augmented snapshot embedding (B3) implements §3.5 "selected robustness analyses" never realized in 2D.
- Per-agent per-channel feature standardization (D3) is explicit in the pipeline, per §3.4.

**Methodology-consistent extensions** (2D→3D generalizations faithful to the methodology's intent):
- 3D `ContinuousSpace` (A1) extends §3.1 Mesa 3 substrate; n-dimensional support is a property of the experimental module.
- Uniform-on-S² initialization (A4) is the natural 3D analog of 2D uniform-angle sampling.
- Diagonal-opposite 3D split waypoints (A5) generalize §3.2 split semantics.
- `(speed, u_x, u_y, u_z)` feature set (B1) generalizes §3.3 `(speed, sin θ, cos θ)`; unit-vector encoding avoids angle-representation singularities, paralleling the methodology's motivation for (sin θ, cos θ).
- H2 persistent homology (B4) extends §3.5 Ripser usage to `maxdim=2`; standard in TDA literature for 3D data (Zomorodian & Carlsson 2005). Trajectory cloud analysis rests on Perea & Harer (2015) sliding-windows-and-persistence theoretical foundation.
- Angular momentum norm (B5) generalizes §3.6 milling score to dimension-agnostic form.
- Surrogate null testing (D1) is standard in applied MI analysis and complements the methodology's event-contrast design.

**Novel formulations** (3D-specific where the methodology is silent):
- Velocity-projected milling tangent (A3) — the methodology defines milling only in 2D; our formulation reduces to §3.2's fixed-CCW tangent in the planar limit.

**Preserved 2D choices** (continuations from the 2D implementation, with documented justification):
- Synchronous vectorized update order (A7) is standard in flocking literature (Reynolds 1987; Vicsek et al. 1995) and eliminates order-of-update artifacts that randomized activation can introduce.
- Strict event-window containment in phase aggregation follows the §3.8 full-containment prescription verbatim.

**Epistemic caveats inherited from the methodology** (explicit in the paper; carried forward in 3D code comments and documentation):
- Within-window autocorrelation is retained rather than removed (§3.4). Φ_spectral is interpreted as an operational windowed dependence score, not an unbiased population MI estimate. All three estimators (KSG, histogram, Gaussian) share this caveat.
- Spectral bipartition is an approximation to the combinatorial minimum information partition, not an exact solution (Bailey & Schneider 2025 §2.5; the Fiedler partition is an approximation to normalized minimum cut per von Luxburg 2007, itself an approximation to the MIP of IIT).
- Persistence summaries differ in their stability guarantees: bottleneck distances are Lipschitz-stable per Cohen-Steiner et al. (2007); total persistence and max persistence are not, and should be interpreted as more noise-sensitive (D8).
