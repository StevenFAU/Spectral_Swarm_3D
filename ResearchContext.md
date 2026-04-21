# Spectral Swarm: Research Context and Future Directions

Companion document to `SpectralSwarm3DPhases.md`. Where the phases document specifies *what* is being built, this document maps *where the work sits* in the landscape of information-theoretic integration measurement, and *what remains open* for further research.

---

## 1. The Landscape of Integration Measures

The question "how integrated is this system?" has generated a spectrum of formalizations over the past two decades. They differ along four orthogonal axes that are useful to separate before placing any specific measure.

**Axis 1: Causal vs. observational.** Does the measure require access to the system's intervention-grounded causal structure (transition probabilities under counterfactuals), or can it be estimated from passively-observed time series? IIT in all versions is causal: exact Φ is defined over cause-effect repertoires evaluated by interventionally marginalizing elements. MI-based measures, transfer entropy, and Φ_spectral are observational: they work on whatever joint distribution the system happens to produce.

**Axis 2: Pairwise vs. higher-order.** Does the measure decompose information dependence into pairwise terms only, or does it capture genuinely n-way structure — synergy, redundancy, emergent coupling that cannot be recovered from any subset of the parts? Pairwise mutual information, by construction, is at the floor of this axis. Partial Information Decomposition (PID) and Integrated Information Decomposition (ΦID) sit at the top, decomposing information into synergistic, redundant, and unique atoms that pairwise measures collapse together.

**Axis 3: Synchronic vs. diachronic.** Does the measure describe the *state* of the system at an instant (constitutive integration) or the *process* of integration unfolding over time (etiological integration)? Bailey & Schneider (2025) §7 explicitly notes that Φ_spectral, as a sliding-window measure, gives a diachronic trajectory but does not separately estimate either the synchronic or diachronic components — it entangles them.

**Axis 4: Tractable vs. intractable.** Does the measure scale to real systems (N=40, N=1000, N=10⁶) or is it confined to toy systems? IIT 4.0 exact Φ is intractable beyond ~10–15 elements even with modern optimizations. PID for n≥4 sources has no unique decomposition and becomes combinatorially fraught. Pairwise-MI measures scale as O(N² · MI_cost) and are routinely run on systems with hundreds to thousands of nodes.

Every integration measure is a point in this four-dimensional tradeoff space. No measure dominates on all axes; each is a deliberate choice of what to privilege.

---

## 2. Situating Φ_spectral

Against these axes, Φ_spectral is: **observational, pairwise, dynamical (diachronic-trajectory over sliding windows), tractable.** It is scalable, works on real time series, and requires no causal model. It pays for this by missing higher-order synergistic structure and by conflating synchronic constitution with diachronic process.

This is a deliberate position. The 2025 paper frames it explicitly: Φ_spectral is presented as a "practical proxy for epistemic emergence" — accessible to "a statistical observer limited to second-order dependencies" (Bailey & Schneider 2025 §2.1). The measure is calibrated to what an external observer can compute from time-series data, which is exactly the regime in which drones, birds, neurons, and AI systems produce their telemetry.

### 2.1 Adjacent measures and what they capture differently

**IIT 4.0 (Albantakis et al. 2023).** The canonical causal formulation of integrated information. Computes cause-effect structures over subsets of a system, identifies the Minimum Information Partition (MIP), and measures φ_s as the irreducibility of the system under partition. Requires the full transition probability matrix, which for a system of N binary elements is a 2^N × 2^N object. PyPhi (Mayner et al. 2018, extended for 4.0) is the reference implementation. Recent work — GeoMIP (Lyu et al. 2025) — achieves 165–326× speedups over PyPhi via hypercube-symmetry exploitation but remains bounded at ~25 variables. The IIT 4.0 authors themselves (Albantakis et al. 2023) describe their theory as "canonically non-computational, non-algorithmic." Exact Φ is a theoretical target, not a practical measurement instrument for a 40-agent swarm.

**Partial Information Decomposition (Williams & Beer 2010).** Given two sources X₁, X₂ and a target Y, PID decomposes I(X₁, X₂; Y) into four atoms: unique information from X₁, unique from X₂, redundant information shared by both, and synergistic information present only in the joint. Multiple formalizations exist (I_min, I_ccs, Blackwell redundancy, δ-PID for Gaussians), and the field is still unifying — Gutknecht, Makkeh, & Wibral (2025) recently proposed "From Babel to Boole," a logical framework attempting to unify the fragmented PID proposals. For n≥4 sources, PID lacks a unique decomposition and becomes combinatorially ill-posed (Matthias et al. 2025).

**Integrated Information Decomposition (Mediano et al. 2021; Luppi et al. 2024).** Extends PID to the dynamical setting: decomposes the information past-states carry about future-states into synergistic, redundant, and unique components across a temporal partition. Critical recent finding: Luppi et al. (2024), applying ΦID to human fMRI, demonstrated that "functional connectivity predominantly reflects redundant interactions" — that is, measures based on pairwise correlational dependence (of which Φ_spectral is a spectral-partition aggregation) systematically weight redundancy over synergy. This is a methodological caveat that propagates directly to Φ_spectral and should be acknowledged in the discussion of what the measure captures.

**Transfer Entropy (Schreiber 2000) and Granger-causal variants.** Directional information-theoretic measures: quantifies how much knowing the past of X reduces uncertainty about the future of Y beyond what Y's own past provides. Solves the symmetry limitation of pairwise MI (Φ_spectral's MI matrix is symmetric by construction). The graph-Laplacian spectral approach would need modification to handle directed graphs (non-self-adjoint Laplacian; different spectral partitioning theory). Luppi et al. (2023, 2024) have decomposed transfer entropy through ΦID, showing this combined directional + synergy-aware approach is tractable in principle.

**Causal Emergence (Hoel, Albantakis, & Tononi 2013).** A different framing of integration: macro-level coarse-grainings of a system can have *higher* effective information than the underlying micro-level, meaning the macro description is more informative about its own dynamics. Directly applicable to swarms — the question "does the swarm-as-a-whole have more effective information than the sum of agent-level descriptions?" maps onto causal emergence computations. But requires the same transition probability apparatus IIT does, inheriting the tractability problem.

**Information Geometry (Amari 2001; Oizumi, Tsuchiya, & Amari 2016).** A distinct formalization in which integration is defined via the Kullback-Leibler divergence between the full system's joint distribution and a factorized approximation. Elegant and principled but again computationally demanding for large systems.

**Classical swarm order parameters (polarization, milling score, nearest-neighbor distance).** The baselines the methodology paper uses. These are not integration measures — they are motif detectors. They do one thing well each (polarization detects heading alignment, milling detects rotational coordination, NN distance detects spatial dispersal), but they don't attempt to capture system-level irreducibility.

**Topological Data Analysis of collective motion (Topaz et al. 2015; Bhaskar et al. 2019).** The topological branch of the methodology paper. Complementary, not competing: TDA describes geometric shape of configurations and trajectories; it says nothing directly about information integration. The Bailey 2026 methodology's innovation is to run both in parallel and ask where they agree and diverge.

### 2.2 What corner does Spectral Swarm 3D occupy

The project sits at the intersection of several under-populated corners:

1. **IIT-inspired integration measurement applied to swarms.** Swarm robotics as a field (Dorigo 2021; Couzin lab) has largely developed in parallel to integration theory, with very little cross-pollination. Bailey 2026 is one of the first methodology papers to explicitly bring Φ-like measurement to swarm telemetry. This 3D extension is the first practical realization of that methodology in three dimensions.

2. **Parallel spectral + topological pipelines on identical telemetry.** The head-to-head comparison on matched sliding windows (methodology §2.4) is a genuine methodological contribution. Most work does one or the other; running both on the same data and asking "where do they agree, where do they diverge" is novel even within the TDA-of-swarms literature.

3. **Dimension-specific extensions.** The spherical-shell milling scenario + H2 persistent homology combination tests whether adding a spatial dimension adds *analytical reach* — whether H2 captures a coordination signal that H1 and Φ_spectral cannot. This is a genuinely 3D-specific contribution.

4. **Reproducible, open methodology.** Dependency pinning, reproducibility metadata, surrogate null testing, bootstrap CIs, explicit deviation documentation. The 2025 and 2026 papers describe results but do not ship computational infrastructure at the reproducibility level the 3D plan commits to.

---

## 3. What This Work Does Not Address

Honesty about scope is itself a scientific virtue. The following are *inherited limitations* of the methodology, not project-specific shortcomings, but they should be named so that downstream claims do not overreach.

**L1 — Pairwise-MI is redundancy-weighted.** Per Luppi et al. (2024), pairwise-dependence-based integration measures are disproportionately sensitive to redundant information and undercount synergistic integration. When Φ_spectral declines as w_a increases (the predicted synchronized-oscillator regime), this could be *either* genuine low integration *or* redundancy saturation hiding synergy. The measure cannot distinguish. This is a hard limit of the second-order approach.

**L2 — Symmetric MI misses directionality.** The MI graph `M_ij = I(Z_i; Z_j) = I(Z_j; Z_i)` is symmetric by the symmetry of Shannon mutual information. Real swarms have directional influence — leaders drive followers, not vice versa. Φ_spectral cannot detect this; the Fiedler partition is blind to who is driving whom.

**L3 — Φ_spectral is causally blind.** Because the measure is observational, it cannot distinguish integration from confounding. Two agents whose velocities covary because both are responding to the same environmental gradient produce the same MI as two agents where one is directly influencing the other. For a controlled simulator this is fine — we know the ground-truth coupling. For real swarms in real environments, this is a substantive limitation.

**L4 — The spectral bipartition is an approximation of an approximation.** The Fiedler vector provides a relaxation of the normalized minimum cut (itself NP-hard). The normalized minimum cut is a relaxation of the MIP search IIT specifies. Each relaxation is principled, but Φ_spectral is two steps removed from the theoretical quantity it approximates. Bailey & Schneider (2025) §2.5 states this explicitly as a bound, not an equality.

**L5 — Synchronic vs. diachronic are entangled.** The sliding-window construction produces Φ_spectral(t), a trajectory. But this trajectory does not separately estimate the synchronic (constitutive-at-instant-t) and diachronic (non-traceable-across-time) components of emergence, despite the 2025 paper's theoretical discussion of both. Bailey & Schneider (2025) §7 explicitly acknowledges this gap.

**L6 — Within-window autocorrelation inflates apparent sample size.** Methodology §3.4 notes this verbatim: consecutive time points within a window are not independent. The effective sample size is less than W, which biases MI estimators. Reported Φ_spectral values are "operational windowed dependence scores" rather than unbiased population estimates.

**L7 — Finite-size effects at N=40.** A 40-agent system is small by swarm-robotics standards (real-world aerial swarms exceed 1000; fish schools reach 10⁴; starling murmurations 10⁵–10⁶). The Fiedler partition has meaningful statistical structure at N=40, but scaling claims to large swarms require either demonstration at larger N or explicit caveats.

**L8 — Simulation-only validation.** Neither the 2025 paper, the 2026 methodology, nor this 3D extension touches real-world telemetry. All results are in an idealized simulator where physics, noise, and observability are controlled. Real-world applicability is argued, not demonstrated.

---

## 4. Research Directions Implied by the Limitations

Each limitation in §3 implies a specific research direction. For each, this section identifies what immediate next work would address the limitation and how that work connects to active programs in the landscape of §2. These are not speculative; they are direct consequences of the scope boundaries drawn above, and each has identifiable literature and tooling already in place.

### 4.1 ΦID upgrade of the spectral branch (addresses L1)

**Direction.** Replace `M_ij = I(Z_i; Z_j)` with a decomposition into redundant, unique, and synergistic atoms via MMI-PID (Mediano, Seth, Barrett 2019) for the Gaussian regime or ΦID (Mediano et al. 2021) for full dynamical decomposition. Build the Laplacian on synergy-weighted edges rather than raw MI, and re-run the Fiedler analysis. The result is a "synergistic Φ_spectral" that captures coordination structure pairwise MI systematically undercounts.

**Landscape connection.** This is a direct response to Luppi et al. (2024), who demonstrated on human fMRI that pairwise-dependence measures are redundancy-weighted. Their result generalizes in principle to any pairwise-MI-based integration score, including Φ_spectral. The MMI-PID restriction is specifically tractable for near-Gaussian data (Mediano, Seth, Barrett 2019 demonstrate most PID decompositions converge for continuous Gaussian variables), which matches our feature distribution after per-agent standardization. Primary feasibility question: does ΦID scale to N=40 agents over W=40 windows at d=4 features? Current ΦID implementations are validated at n~10 nodes; scaling is the main risk.

**Comparative value.** Distinguishes our work from the redundancy-heavy end of pairwise integration measures without requiring the IIT 4.0 computational budget.

### 4.2 Transfer-entropy extension (addresses L2)

**Direction.** Replace the symmetric MI matrix with a pairwise transfer entropy matrix (Schreiber 2000), producing a directed dependence graph. Use a directed-graph Laplacian formulation (Chung 2005 for random-walk Laplacian; Li & Zhang 2012 for signed) to compute a directional analog of Φ_spectral. The Fiedler cut becomes asymmetric, and partitions can be ranked by "who is driving whom."

**Landscape connection.** Transfer entropy is the standard directional extension of MI in applied information theory. Luppi et al. (2023, 2024) have already decomposed transfer entropy through ΦID, demonstrating that directional + synergy-aware measurement is tractable. Our leader scenarios (with ground-truth directional coupling) are a natural validation target — a correct directional Φ_spectral analog should identify leaders as information sources.

**Comparative value.** Closes the gap between Φ_spectral and the broader time-series-integration literature, where directionality is standard rather than optional.

### 4.3 PyPhi validation on small subsystems (addresses L4)

**Direction.** For subsets of 5–8 agents identified as "cores" by Fiedler centrality or by physical criteria (tightest cluster, most-coupled leader group), compute exact IIT 4.0 Φ via PyPhi. Compare to Φ_spectral evaluated on the same subsystem. High correlation validates the spectral approximation; low correlation is itself a publishable finding about where spectral methods diverge from the causal ground truth.

**Landscape connection.** PyPhi (Mayner et al. 2018; extended for 4.0) and its recent optimizations (GeoMIP; Lyu et al. 2025) make exact Φ computation feasible for ~15–25 variables. The 5–8 agent range is well within this envelope. No prior work has validated spectral-integration approximations against exact IIT 4.0 on physically-grounded subsystems.

**Comparative value.** Turns the "spectral approximation" framing of Bailey & Schneider (2025) from a theoretical claim into an empirically-grounded one.

### 4.4 Causal emergence variants (addresses L3)

**Direction.** Apply Hoel's causal emergence framework (Hoel, Albantakis, Tononi 2013) to coarse-grainings of the swarm — cluster agents into macro-groups (via Fiedler partition, spatial clustering, or leader/follower classes) and ask whether the macro-level description has higher effective information than the micro-level. The methodology's existing infrastructure (window-level partitions, information quantities per window) supports this directly.

**Landscape connection.** Causal emergence is the principled framing of "what is the right level of description for this system at this time?" Hoel et al. 2013 demonstrated this for small abstract networks; swarms are a natural applied target that has not been systematically explored. Requires intervention-grounded transition probabilities, which the simulator provides (the simulator *is* the causal model) but real-world data does not — hence this direction is most tractable for the simulator phase of this research program.

**Comparative value.** Provides a causally-grounded companion metric to the observational Φ_spectral, and addresses L3 directly rather than deferring it.

### 4.5 Effective-sample-size correction and block resampling (addresses L6)

**Direction.** The within-window autocorrelation problem has a standard toolkit. Effective sample size estimation via integrated autocorrelation time τ_int gives a corrected "effective W" per window. Block bootstrap (Künsch 1989) handles autocorrelated resampling without assuming independence. Both can be added to the existing sweep pipeline with minor modifications.

**Landscape connection.** These are standard techniques in time-series econometrics and neuroscience. The methodology paper's acknowledgment (§3.4 verbatim) that Φ_spectral is an "operational windowed dependence score" rather than an unbiased population estimate is honest framing of an addressable limitation, not an unresolvable one. Applying the correction tightens the interpretation.

**Comparative value.** Brings the measurement discipline of Φ_spectral in line with standard practice in applied time-series analysis, which is more mature than the time-series integration-measurement literature.

### 4.6 Quotient-geometric TDA upgrade

**Direction.** Bailey (2026, arXiv:2603.18041) develops quotient geometry for swarm configurations modulo relabeling and rigid motions, with persistence-stable metrics on the resulting configuration space. Replacing the Euclidean pairwise-distance input to Ripser with a quotient-geometric distance gives the topological branch the formation-invariance that swarms conceptually require — two identical flocks at different positions or rotations should produce identical persistence diagrams.

**Landscape connection.** This is a direct integration with work by the methodology paper's author. The theoretical infrastructure is already published. Natural companion to the current 3D work, not a separate research program.

**Comparative value.** Strengthens the stability properties of the topological branch and demonstrates that the two Bailey 2026 papers (spectral-topological comparison; quotient geometry) compose cleanly.

### 4.7 Real-world telemetry validation (addresses L8)

**Direction.** Apply the pipeline to published datasets: starling murmurations (STARFLAG, Cavagna lab), fish schools (Couzin lab), drone swarm robotics datasets. Requires handling partial observability (not every agent tracked every frame), measurement noise, heterogeneous sampling rates. A sensible first step is a robustness study on the simulator: introduce agent dropout, observation noise, and sampling jitter, and measure how Φ_spectral and the TDA summaries degrade.

**Landscape connection.** The 2025 paper validates on random/transitional/synchronized oscillators and CTLNs — abstract dynamical systems. The 2026 methodology and this 3D extension validate on a simulated swarm — still idealized. None of the published Φ_spectral work touches real telemetry. This is the obvious next applied step.

**Comparative value.** Transforms the methodology from an in-silico proof of concept into an empirical tool.

### 4.8 Scalability to larger swarms (addresses L7)

**Direction.** At N=1000+, the pipeline has two bottlenecks. Ripser H2 memory scales as O(N³); this is addressed by approximate persistence methods (sparse Vietoris-Rips, Delaunay-based filtrations via GUDHI). The MI matrix scales as O(N²) in number of pairs; KSG computation per pair is O(W log W). Total MI compute at N=1000 is approximately (10⁶/2) pairs × 40 log 40 ≈ 10⁸ operations per window, still feasible but requires parallelization. The spectral side (normalized Laplacian, Fiedler) scales comfortably via sparse iterative eigensolvers (Lanczos, LOBPCG) since the MI graph is sparse when most agent pairs have near-zero MI.

**Landscape connection.** GUDHI and Ripser have active development on approximate persistence for large point clouds. Sparse spectral methods are mature in the graph-learning literature. The methodology does not require custom algorithm development at scale — it requires engineering integration with existing tools.

**Comparative value.** Validates (or invalidates) scaling claims that are currently unsupported. A negative finding — that Φ_spectral dynamics qualitatively change between N=40 and N=1000 — would itself be important.

### 4.9 Synchronic/diachronic separation (addresses L5)

**Direction.** Bailey & Schneider (2025) §7 explicitly calls for a two-channel estimator: one computing time-slice constitutive structure (synchronic), the other measuring etiological non-traceability across time (diachronic). The standard move is to compare windowed Φ_spectral against a surrogate in which the temporal order within windows is shuffled — the shuffle preserves the *synchronic* covariance structure but destroys *diachronic* information flow. The gap between observed and shuffled Φ_spectral is a diachronic-specific signal; what remains after shuffle-collapse is synchronic.

**Landscape connection.** This is explicitly flagged by the 2025 paper's authors as an open problem they want solved. Implementing it pragmatically addresses Bailey & Schneider (2025) §7 directly.

**Comparative value.** Converts a theoretical gap in the framing of Φ_spectral into a concrete estimator, produces a richer measurement, and directly advances a program the original authors have publicly identified as open.

### 4.10 Cross-substrate comparison

**Direction.** Φ_spectral is proposed in Bailey & Schneider (2025) as substrate-general — applicable to swarms, neural systems, AI. The swarm work is one substrate. A direct cross-substrate study would apply the same spectral-topological pipeline to: swarm telemetry (this work); neural time series (fMRI, EEG, or electrophysiology); AI internal states (transformer attention, RNN hidden states). If the measure tracks a general property of integration rather than substrate-specific coordination, qualitative patterns — redundancy-weighting, synchronized-collapse, transitional-peak — should replicate across substrates.

**Landscape connection.** Luppi et al. (2024) have already applied ΦID to human fMRI. Comparing swarm Φ_spectral behavior to their fMRI Φ_spectral behavior would be a direct substrate-comparison test that also addresses L1 (by running side-by-side with ΦID-grade analysis).

**Comparative value.** Strengthens (or falsifies) the "substrate-general marker of integration" framing on which the applied applications of Φ_spectral ultimately depend.

### 4.11 Quantum-information extensions (theoretical open direction)

**Direction.** The framework's co-authors have developed the Prototime Interpretation (Schneider & Bailey 2025, in Rickles et al. *Quantum Gravity and Computation*) and Superpsychism (Schneider & Bailey 2025, J. Consciousness Studies) as related theoretical programs. A quantum-information analog of Φ_spectral — defined on reduced density matrices and quantum mutual information rather than classical Shannon MI — is implicit in this program. Concrete formalism would include: replacing classical MI with quantum mutual information `I(A:B) = S(ρ_A) + S(ρ_B) − S(ρ_AB)` on the bipartite reduced state, building a quantum Laplacian on the resulting dependence graph, and evaluating spectral partitions on entangled subsystems.

**Landscape connection.** This is an explicitly theoretical direction flagged by the co-authors themselves, not a timeline projection. It is not part of the current 3D project's scope but is named here because it is the natural theoretical extension of the framework into the quantum regime, and because any future work on AI-consciousness markers (which the 2025 paper discusses at length) intersects with this program.

**Comparative value.** Acknowledges that the classical Φ_spectral is one reduction of a broader theoretical program; any future classical results are interpretable within this larger setting.

---

## 5. Why This Corner Is Worth Tackling

A fair question at this point is: given the limitations, why invest in this particular formulation at all?

**Because it's the tractable one.** IIT 4.0 is not a realistic measurement instrument for 40-agent swarms; it was never designed to be. PID/ΦID is powerful but still maturing as a framework and has not been applied at scale to swarm telemetry. Φ_spectral is the only formulation in the IIT-adjacent family that runs on real telemetry, scales to hundreds of agents, and produces a time-resolved trajectory. This alone is worth something.

**Because the dual pipeline is novel.** Running spectral and topological descriptors on the *same* sliding windows and asking where they agree/diverge is a methodological contribution independent of either branch. No other work does this for swarms. The agreement/divergence findings are genuine scientific results — they tell us something about what different notions of "emergence" pick up in the same physical data.

**Because the 2D-3D progression is principled.** The 2D work established the framework is usable and produces interpretable results. The 3D extension tests whether adding a spatial dimension adds analytical reach (H2 voids, spherical-shell milling) or just more numbers. Either answer is informative.

**Because the field lacks a measurement baseline.** Swarm robotics has decades of work on control algorithms and emergent behavior, but very few quantitative measures of "how integrated is this swarm right now" that go beyond motif-specific order parameters. Whatever Φ_spectral's limitations, it is a step toward a shared measurement language across swarm research, applied information theory, and integration-theoretic consciousness science.

**Because the limitations are themselves directions.** Each limitation named in §3 maps to a direction in §4. PID/ΦID extension, transfer-entropy variants, PyPhi validation, quotient-geometric TDA, real-world telemetry, causal emergence — this is a substantial research program, not a single study. The 3D work is one foundational piece of a larger trajectory, with each direction addressing a specific, named limitation using tools already present in the literature.

---

## 6. Honest Self-Assessment

What the 3D Spectral Swarm work is not:

- It is not a measurement of consciousness. Bailey & Schneider (2025) are careful to frame Φ_spectral as a marker warranting further investigation, not a sufficient condition for phenomenal experience. Our work inherits this framing.

- It is not a test of IIT 4.0. We do not compute exact Φ; we compute a spectral approximation inspired by IIT's irreducibility principle. Comparisons to IIT 4.0 would require PyPhi validation on small subsystems (§4.3).

- It is not a solution to the pairwise limitation. We acknowledge that Φ_spectral undercounts synergy (Luppi et al. 2024). Addressing this requires moving to PID/ΦID (§4.1).

- It is not a swarm-robotics control algorithm. The pipeline is for measurement and analysis, not decision-making.

What the work *is*:

- A scalable, reproducible, dual spectral-topological measurement pipeline for 3D swarm telemetry.
- An empirical test of the 2025 paper's predictions (synchronized → low Φ; transitional → peak Φ) in a regime broader than the oscillator systems the paper originally validated.
- A concrete realization of a 3D methodology that the 2026 paper specifies only in 2D.
- A foundation for the research directions in §4.

The goal of the 3D extension is to establish that the methodology is sound, reproducible, and extensible — and to surface whatever unexpected findings emerge from pushing it into 3D. The larger program (PID/ΦID, transfer entropy, real-world validation, causal emergence, quotient-geometric TDA, quantum extensions) follows from this foundation; it does not precede it.

---

## Cited References (Beyond the Phases Document)

New references introduced in this document, grouped by cluster. The phases document's reference list remains canonical for implementation-level citations.

**IIT 4.0 and computational IIT:**
- Albantakis, L., Barbosa, L., Findlay, G., et al. (2023). *Integrated Information Theory (IIT) 4.0: Formulating the Properties of Phenomenal Existence in Physical Terms.* PLOS Comp. Biol. 19(10), e1011465.
- Mayner, W. G. P., Marshall, W., Albantakis, L., et al. (2018). *PyPhi: A toolbox for integrated information theory.* PLOS Comp. Biol. 14(7), e1006343.
- Tononi, G. (2004). *An Information Integration Theory of Consciousness.* BMC Neurosci. 5, 42.
- Oizumi, M., Albantakis, L., & Tononi, G. (2014). *From the Phenomenology to the Mechanisms of Consciousness: IIT 3.0.* PLOS Comp. Biol. 10(5), e1003588.

**Partial Information Decomposition and ΦID:**
- Williams, P. L., & Beer, R. D. (2010). *Nonnegative decomposition of multivariate information.* arXiv:1004.2515.
- Mediano, P. A. M., Rosas, F. E., Luppi, A. I., et al. (2021). *Towards an Extended Taxonomy of Information Dynamics via Integrated Information Decomposition.* arXiv:2109.13186.
- Luppi, A. I., Mediano, P. A. M., Rosas, F. E., et al. (2024). *A synergistic workspace for human consciousness revealed by Integrated Information Decomposition.* eLife 12, RP88173.
- Gutknecht, A. J., Makkeh, A., & Wibral, M. (2025). *From Babel to Boole: the logical organization of information decompositions.* Proc. Royal Soc. A 481(2310), 20240174.

**Transfer Entropy and directional measures:**
- Schreiber, T. (2000). *Measuring Information Transfer.* Phys. Rev. Lett. 85(2), 461.
- Chung, F. (2005). *Laplacians and the Cheeger Inequality for Directed Graphs.* Ann. Combinatorics 9(1), 1–19.

**Causal Emergence:**
- Hoel, E. P., Albantakis, L., & Tononi, G. (2013). *Quantifying causal emergence shows that macro can beat micro.* PNAS 110(49), 19790.

**Information Geometry:**
- Amari, S. (2001). *Information geometry on hierarchy of probability distributions.* IEEE Trans. Inf. Theory 47(5), 1701.
- Oizumi, M., Tsuchiya, N., & Amari, S. (2016). *Unified framework for information integration based on information geometry.* PNAS 113(51), 14817.

**Block bootstrap and autocorrelated resampling:**
- Künsch, H. R. (1989). *The Jackknife and the Bootstrap for General Stationary Observations.* Annals of Statistics 17(3), 1217.

**Quantum extensions (theoretical framework by co-authors):**
- Schneider, S., & Bailey, M. (2025). *Superpsychism.* Journal of Consciousness Studies.
- Schneider, S., & Bailey, M. (2025). *The Prototime Interpretation of Quantum Mechanics.* Forthcoming in Rickles, D., Arsiwalla, X. D., & Elshatlawy, H. (eds.), *Quantum Gravity and Computation: Information, Pregeometry, and Digital Physics.*
