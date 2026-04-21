# Spectral Swarm 3D

3D extension of the spectral and topological measures of emergence in boids-like swarms, building on the 2D proof of concept at [`StevenFAU/Spectral_Swarm`](https://github.com/StevenFAU/Spectral_Swarm) (tag `v0.1-2d-poc`).

This repository implements:

- 3D boids simulation on Mesa 3's n-dimensional continuous space, with a velocity-projected milling tangent that produces genuine spherical-shell configurations rather than a planar ring embedded in 3D.
- The Φ_spectral integrated-information proxy (Bailey & Schneider 2025) with KSG, histogram, and Gaussian mutual-information estimators for sensitivity analysis.
- Persistent homology through H2 for detection of enclosed voids unique to ≥3 spatial dimensions, alongside the H0/H1 persistence from the 2D methodology.
- Classical swarm order parameters (polarization, 3D milling score, angular momentum norm) as baselines.
- Full reproducibility infrastructure: dependency pinning, per-run metadata (git hash, Python version, package versions, timestamp), surrogate null testing, and bootstrap confidence intervals.

## References

- Bailey, M. M. (2026). *Spectral and Topological Methods Comparison in Swarms.* Methodology paper.
- Bailey, M. M., & Schneider, S. L. (2025). *When Wholes Resist Decomposition: A Spectral Measure of Epistemic Emergence.* Theoretical foundation.

See `SpectralSwarm3DPhases.md` for the full reference list and design decision rationale.

## Install

```bash
pip install -e .
```

Python 3.12+ required. See `pyproject.toml` for dependency specifications and `requirements-lock.txt` for exact versions of the validated environment.

## Run tests

```bash
pytest tests/ -v
```

## Project structure

```
src/spectral_swarm_3d/        # package source
├── model.py, agent.py        # simulator
├── scenarios.py              # waypoint and milling logic
├── telemetry.py              # CSV logger + reproducibility metadata
└── analysis/                 # spectral, TDA, classical, comparison modules

tests/                        # pytest suite; one-to-one with source modules
configs/default.yaml          # all simulation and analysis parameters
scripts/                      # CLI entry points for runs, sweeps, comparison, rendering
notebooks/                    # exploration; not canonical results
outputs/                      # sweep outputs (Parquet, figures, MP4)
docs/                         # supporting PDFs
```

## Project plan

Full phase structure, design decisions, pass/fail criteria, and methodology conformance notes are in [`SpectralSwarm3DPhases.md`](./SpectralSwarm3DPhases.md). Research positioning relative to IIT 4.0, PID/ΦID, transfer entropy, causal emergence, and information geometry is documented in [`ResearchContext.md`](./ResearchContext.md).

## Claude Code conventions

Guidelines for Claude Code sessions working on this repository are in [`CLAUDE.md`](./CLAUDE.md).

## License

MIT, matching the 2D predecessor repository.
