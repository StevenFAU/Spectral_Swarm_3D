"""Run all sweep conditions for a given sweep family (alignment, leadership, etc.).

Phase 4 implementation target. See SpectralSwarm3DPhases.md §Phase 4 and C3.

Sweep families: alignment, leadership, jamming, split_merge, milling, noise,
sensitivity (9 estimator x feature combos), n_sensitivity, w_sensitivity,
alignment_rule_sensitivity.

Usage:
    python 3d/scripts/run_sweep.py --sweep alignment --config 3d/configs/default.yaml
"""


def main() -> None:
    raise NotImplementedError("Phase 4 — see SpectralSwarm3DPhases.md")


if __name__ == "__main__":
    main()
