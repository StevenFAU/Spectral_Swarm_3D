# Claude Code Conventions — Spectral Swarm 3D

## Authoritative documents

- `SpectralSwarm3DPhases.md` (repo root) — full project plan. Read before starting any phase.
- `Phase0.md` — scaffolding record. Historical reference.
- `ResearchContext.md` — research positioning. Useful for result interpretation and related-work framing.

## Repository

This is a standalone Python package. The 2D predecessor work lives in a separate repository (`github.com/StevenFAU/Spectral_Swarm`, tag `v0.1-2d-poc`) and is not imported here. If you need to consult the 2D code, clone that repository separately and read it as reference material — do not copy code across without deliberate porting.

## Package

- Name: `spectral_swarm_3d`
- Install locally: `pip install -e .` from repository root.
- Python 3.12+; Mesa 3.4+.

## Methodology fidelity

Every design decision has an anchor in `SpectralSwarm3DPhases.md` clusters A–D. When in doubt:

1. Check the plan's cluster that covers the decision (A for simulator, B for analysis, C for downstream, D for robustness).
2. If ambiguous, check Bailey (2026) §§3.1–3.8 and Bailey & Schneider (2025).
3. Deviations must be discussed with the user before committing.

## Testing

- `pytest tests/ -v` from repository root.
- Every phase has an explicit pass/fail checklist in the plan. Do not advance phases until all checks pass.
- Prefer pinning expected behavior with unit tests over ad-hoc verification.

## Style

- Type hints on all public functions.
- Docstrings referencing the plan section (e.g., "Implements A3 velocity-projected milling tangent.").
- `ruff` for linting; line length 100; `select = ["E", "F", "W"]`.
- No `print()` in library code; use logging or explicit returns.

## Reproducibility

- **D6** — every run records git hash, Python version, package versions, timestamp in its metadata JSON.
- **D5** — `requirements-lock.txt` regenerated whenever dependencies change.
- All randomness via explicit seeds. Bit-identical trajectories required for same seed in Phase 1 onwards.

## Commits

- Small, atomic commits per sub-task.
- Conventional prefix: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Reference the plan cluster and phase in commit messages where relevant
  (example: `feat(Phase 1, A3): velocity-projected milling tangent`).

## Phase discipline

- Do not advance phases within a single Claude Code session. Each phase starts fresh with the plan reloaded into context.
- Phase N cannot begin until Phase N−1's pass/fail checklist is entirely green.
- If the user asks to skip or combine phases, stop and confirm — the phase structure is a deliberate scope-management tool.

## Common gotchas

- Mesa 3's `ContinuousSpace` is n-dimensional via the `dimensions` parameter (ter Hoeven et al. 2025). Do not look for a separate "3D" class.
- Ripser's `maxdim=2` produces H2 persistence; make sure test fixtures account for the third diagram in the list.
- KSG MI estimation requires per-agent per-channel feature standardization as a separate step (D3); it is not a property of the estimator itself.
- The 2D code's `alignment_rule` was implicit sum; in this repo the default is explicit mean (A6 methodology restoration).
