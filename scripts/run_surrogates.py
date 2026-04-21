"""Run surrogate null testing (D1) for all scenarios.

Phase 5 implementation target. See SpectralSwarm3DPhases.md §Phase 5 and D1.

Generates trajectory-shuffled null distributions (10 surrogates per scenario)
and compares observed Phi_spectral and TDA summaries against the null.

Usage:
    python 3d/scripts/run_surrogates.py --outputs 3d/outputs/ --config 3d/configs/default.yaml
"""


def main() -> None:
    raise NotImplementedError("Phase 5 — see SpectralSwarm3DPhases.md D1")


if __name__ == "__main__":
    main()
