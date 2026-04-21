# Phase 0 — Scaffolding and Migration

This document records the Phase 0 work for the 3D extension of the Spectral Swarm project. It serves two purposes:

1. **Provenance.** The scaffolding was first prototyped inside the 2D predecessor repository (`Spectral_Swarm`) under a `3d/` subdirectory. It was then migrated to this standalone repository (`Spectral_Swarm_3D`) by flattening the `3d/` subdirectory into the repo root. This document records what was migrated and verifies the migration succeeded.

2. **Reference.** Future Claude Code sessions or human collaborators can use this document to verify Phase 0 invariants after environment changes (new machine, updated dependencies, etc.) and to understand the intended structure of the repository.

**Scope of Phase 0.** Repository initialization with Python package (`spectral_swarm_3d`), pinned dependencies, `default.yaml` with all 3D parameters, module and test stubs, reproducibility metadata infrastructure, and Claude Code conventions file. No simulator logic; no analysis logic. Every module under `src/` contains either a docstring-only stub or a signature that `raises NotImplementedError` pointing to the phase that will implement it.

**Out of scope.** Any substantive implementation. Phase 1 onwards is a separate session with an empty context.

---

## Target Repository State at End of Phase 0

```
Spectral_Swarm_3D/
├── pyproject.toml
├── requirements-lock.txt
├── conftest.py
├── README.md
├── LICENSE                                 (copied from 2D predecessor)
├── CLAUDE.md
├── SpectralSwarm3DPhases.md
├── Phase0.md                               (this document)
├── ResearchContext.md
│
├── src/
│   └── spectral_swarm_3d/
│       ├── __init__.py
│       ├── model.py
│       ├── agent.py
│       ├── scenarios.py
│       ├── telemetry.py
│       └── analysis/
│           ├── __init__.py
│           ├── features.py
│           ├── mi.py
│           ├── spectral.py
│           ├── tda.py
│           ├── classical.py
│           ├── aggregation.py
│           ├── comparison.py
│           ├── surrogates.py
│           └── plotting.py
│
├── tests/
│   ├── __init__.py
│   ├── test_scaffolding.py                 (real assertions)
│   ├── test_boids.py                       (stub, skipped)
│   ├── test_scenarios.py                   (stub)
│   ├── test_telemetry.py                   (stub)
│   ├── test_features.py                    (stub)
│   ├── test_mi.py                          (stub)
│   ├── test_spectral.py                    (stub)
│   ├── test_tda.py                         (stub)
│   ├── test_classical.py                   (stub)
│   ├── test_aggregation.py                 (stub)
│   └── test_comparison.py                  (stub)
│
├── configs/
│   └── default.yaml
│
├── scripts/
│   ├── run_single.py
│   ├── run_sweep.py
│   ├── analyze_sweep.py
│   ├── run_comparison.py
│   ├── run_surrogates.py
│   └── render_scenario_videos.py
│
├── notebooks/
│   └── .gitkeep
│
├── outputs/
│   └── .gitkeep
│
└── docs/
    ├── Swarm_Methodology2.pdf              (Bailey 2026 methodology paper)
    └── when_wholes_resist_decomposition.pdf (Bailey & Schneider 2025)
```

---

## File Specifications

The following content specifications are authoritative. Anything already present from the predecessor repository's `3d/` subdirectory should match these specifications; if it does not, update to match.

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "spectral_swarm_3d"
version = "0.1.0"
requires-python = ">=3.12"
description = "3D extension of the Spectral Swarm spectral-topological pipeline."
dependencies = [
    "mesa>=3.4",
    "numpy>=2.0",
    "scipy>=1.13",
    "scikit-learn>=1.5",
    "ripser>=0.6.8",
    "persim>=0.3.5",
    "pandas>=2.2",
    "pyarrow>=17.0",
    "pyyaml>=6.0",
    "matplotlib>=3.9",
    "networkx>=3.3",
    "ffmpeg-python>=0.2",
]

[project.optional-dependencies]
dev = ["ruff>=0.6", "pytest>=8.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W"]
```

**Rationale.** `>=` lower bounds in the manifest ensure the package installs on current environments. Exact pinning for reproducibility (D5) is captured separately in `requirements-lock.txt` via `pip freeze`, which reflects the actual resolved versions.

### `configs/default.yaml`

```yaml
# Default 3D simulation parameters (Bailey 2026 + 3D adaptations per SpectralSwarm3DPhases.md)
# Values marked TBD will be calibrated in Phase 1.

# Swarm
N: 40
L: 50.0                   # A2: scaled from 2D L=100 to preserve neighbor count in 3D
speed: 1.0
vision_radius: 10.0
separation_radius: 2.0

# Boids weights (B6, A6: mean alignment restored; w_a recalibrated in Phase 1)
w_c: 0.03
w_a: 1.0                  # TBD — calibrated in Phase 1 under mean alignment
w_s: 0.015
alignment_rule: "mean"    # A6: methodology-spec. Alternative: "sum" for sensitivity sweep

# Noise
noise_sigma: 0.05

# Leadership (A5 3D waypoints)
leader_fraction: 0.20
leader_strength: 0.8
leader_waypoint: [40.0, 40.0, 40.0]      # 0.8L diagonal
split_waypoint_group0: [12.5, 37.5, 12.5]   # 3D diagonal-opposite cube corners
split_waypoint_group1: [37.5, 12.5, 37.5]

# Jamming (A2 scaled)
jam_alpha: 0.5
jam_t_on: 200
jam_t_off: 400
fixed_cc_threshold: 6.0   # A2: 12.0 in 2D at L=100 -> 6.0 in 3D at L=50 (r/L=0.12)

# Split-merge
split_t_on: 200
split_t_off: 400

# Milling (A3 velocity-projected tangent; A2 R scaled; methodology μ values in sweeps)
milling_mu: 0.8
milling_R: 11.0           # A2: scaled from 2D R=22 at L=100
milling_kappa: 0.1

# Run
T: 500
seeds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Phase 2 — analysis
W: 40                     # B2: primary window length at d=4 (d=6 uses W=50)
stride: 1
feature_set: "kinematic"  # B1: (speed, u_x, u_y, u_z) at d=4

# Phase 2 — MI estimator (B6: KSG primary per methodology §3.4)
estimator: "ksg"          # Options: "ksg" | "histogram" | "gaussian"
k_ksg: 5
n_bins_hist: 8
mi_tie_break_noise: 1.0e-10

# Phase 3 — TDA (B4: maxdim=2 for H2 void detection)
tda_maxdim: 2
snapshot_augmented: false # B3: methodology §3.5 augmented embedding. Flip to true for robustness runs
snapshot_beta: 0.35
```

### `conftest.py`

```python
"""Pytest configuration for the spectral_swarm_3d package."""
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def config():
    """Load the default 3D config from configs/default.yaml."""
    config_path = Path(__file__).parent / "configs" / "default.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)
```

### `src/spectral_swarm_3d/__init__.py`

```python
"""Spectral Swarm 3D — 3D extension of the spectral-topological swarm pipeline.

See `SpectralSwarm3DPhases.md` at the repository root for the full project plan.
"""

__version__ = "0.1.0"
```

### Module stubs in `src/spectral_swarm_3d/`

Every `.py` file (except `__init__.py` files) contains a module docstring referencing the phase that will implement it plus a placeholder. Example:

```python
"""3D Boids swarm model.

Phase 1 implementation target. See SpectralSwarm3DPhases.md §Phase 1 and Cluster A.

Implements BoidSwarmModel3D using Mesa 3's experimental ContinuousSpace with
dimensions=np.array([[0, L], [0, L], [0, L]]). Synchronous vectorized numpy
update (A7). Mean alignment (A6). Velocity-projected milling tangent (A3).
Uniform-on-S^2 initial velocities (A4).
"""


def build_model(config):
    """Construct a BoidSwarmModel3D from a config dict. Phase 1."""
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md")
```

Apply the same pattern to all modules: `agent.py` (Phase 1), `scenarios.py` (Phase 1), `telemetry.py` (Phase 1 + D6), `analysis/features.py` (Phase 2), `analysis/mi.py` (Phase 2 + B6), `analysis/spectral.py` (Phase 2), `analysis/classical.py` (Phase 2 + B5), `analysis/tda.py` (Phase 3 + B3 + B4), `analysis/aggregation.py` (Phase 4 + D2), `analysis/comparison.py` (Phase 5 + C2), `analysis/surrogates.py` (Phase 5 + D1), `analysis/plotting.py` (Phase 5 + C4).

### Reproducibility metadata helper stub (in `telemetry.py`)

```python
def record_environment() -> dict:
    """Record git commit hash, Python version, pinned package versions, timestamp.

    Per D6 of SpectralSwarm3DPhases.md. Returned dict is attached to every
    run's metadata JSON. Implementation target: Phase 1.

    Returns
    -------
    dict
        Keys: git_commit, python_version, package_versions (dict), hostname, timestamp.
    """
    raise NotImplementedError("Phase 1 — see SpectralSwarm3DPhases.md D6")
```

### Scripts in `scripts/`

Each script is a stub with a module docstring and a `main()` that raises `NotImplementedError`.

### `tests/test_scaffolding.py` (the one test with real assertions)

```python
"""Phase 0 scaffolding tests — structural correctness only."""
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def test_package_imports():
    """The 3D package and all submodules import without errors."""
    import spectral_swarm_3d  # noqa: F401
    import spectral_swarm_3d.model  # noqa: F401
    import spectral_swarm_3d.agent  # noqa: F401
    import spectral_swarm_3d.scenarios  # noqa: F401
    import spectral_swarm_3d.telemetry  # noqa: F401
    import spectral_swarm_3d.analysis  # noqa: F401
    import spectral_swarm_3d.analysis.features  # noqa: F401
    import spectral_swarm_3d.analysis.mi  # noqa: F401
    import spectral_swarm_3d.analysis.spectral  # noqa: F401
    import spectral_swarm_3d.analysis.tda  # noqa: F401
    import spectral_swarm_3d.analysis.classical  # noqa: F401
    import spectral_swarm_3d.analysis.aggregation  # noqa: F401
    import spectral_swarm_3d.analysis.comparison  # noqa: F401
    import spectral_swarm_3d.analysis.surrogates  # noqa: F401
    import spectral_swarm_3d.analysis.plotting  # noqa: F401


def test_default_config_loads(config):
    """The default 3D config loads and has all required keys."""
    required_keys = {
        "N", "L", "speed", "vision_radius", "separation_radius",
        "w_c", "w_a", "w_s", "alignment_rule",
        "noise_sigma",
        "leader_fraction", "leader_strength", "leader_waypoint",
        "split_waypoint_group0", "split_waypoint_group1",
        "jam_alpha", "jam_t_on", "jam_t_off", "fixed_cc_threshold",
        "split_t_on", "split_t_off",
        "milling_mu", "milling_R", "milling_kappa",
        "T", "seeds",
        "W", "stride", "feature_set",
        "estimator", "k_ksg", "n_bins_hist", "mi_tie_break_noise",
        "tda_maxdim", "snapshot_augmented", "snapshot_beta",
    }
    missing = required_keys - set(config.keys())
    assert not missing, f"Missing config keys: {missing}"


def test_3d_parameters_have_3d_values(config):
    """Core 3D parameters are correctly scaled per the plan."""
    assert config["L"] == 50.0, "L should be 50.0 in 3D (A2)"
    assert config["milling_R"] == 11.0, "milling_R should be 11.0 in 3D (A2)"
    assert config["fixed_cc_threshold"] == 6.0, "fixed_cc_threshold should be 6.0 (A2)"
    assert len(config["leader_waypoint"]) == 3, "leader_waypoint must be 3D"
    assert len(config["split_waypoint_group0"]) == 3, "split waypoints must be 3D"
    assert len(config["split_waypoint_group1"]) == 3, "split waypoints must be 3D"


def test_methodology_restorations_in_config(config):
    """Config defaults reflect methodology restorations (A6 mean, B6 KSG)."""
    assert config["alignment_rule"] == "mean", \
        "A6: methodology specifies mean alignment; sum is opt-in"
    assert config["estimator"] == "ksg", \
        "B6: methodology §3.4 specifies KSG as primary estimator"
    assert config["tda_maxdim"] == 2, "B4: H2 persistence in 3D"


def test_snapshot_augmented_default_false(config):
    """B3 augmented snapshot defaults to false; used in robustness sweeps."""
    assert config["snapshot_augmented"] is False


def test_directory_structure_present():
    """All Phase 0 directories and key files exist."""
    expected = [
        "pyproject.toml",
        "CLAUDE.md",
        "README.md",
        "conftest.py",
        "configs/default.yaml",
        "src/spectral_swarm_3d/__init__.py",
        "src/spectral_swarm_3d/analysis/__init__.py",
        "scripts/run_single.py",
    ]
    for rel in expected:
        path = REPO_ROOT / rel
        assert path.exists(), f"Missing: {path}"
```

### Other test files in `tests/`

All non-scaffolding test files are stubs:

```python
"""Phase <N> test target. Stub for Phase 0; implemented in Phase <N>."""
import pytest

pytestmark = pytest.mark.skip(reason="Phase 0 stub; implemented in Phase <N>.")
```

Phase numbers: `test_boids.py` → 1; `test_scenarios.py` → 1; `test_telemetry.py` → 1; `test_features.py` → 2; `test_mi.py` → 2; `test_spectral.py` → 2; `test_classical.py` → 2; `test_tda.py` → 3; `test_aggregation.py` → 4; `test_comparison.py` → 5.

### `CLAUDE.md`

Content specified in the separate `CLAUDE.md` deliverable.

### `README.md`

Content specified in the separate `README.md` deliverable.

### `requirements-lock.txt`

Generated via `pip freeze > requirements-lock.txt` after `pip install -e .`.

---

## Pass/Fail Verification

Run every one of these checks before considering Phase 0 complete:

- [ ] `pip install -e .` from repo root succeeds with no errors.
- [ ] `pytest tests/ -v` runs. `test_scaffolding.py` passes. All other test files are collected and marked skipped with the phase stub reason.
- [ ] `configs/default.yaml` loads with PyYAML and contains all keys listed in `test_default_config_loads`.
- [ ] `pyproject.toml` declares `spectral_swarm_3d`, requires-python `>=3.12`, mesa `>=3.4`.
- [ ] `requirements-lock.txt` exists and is non-empty.
- [ ] All four top-level documentation files exist at repo root: `README.md`, `CLAUDE.md`, `SpectralSwarm3DPhases.md`, `ResearchContext.md`, `Phase0.md`.
- [ ] `LICENSE` exists and matches the 2D predecessor's license.
- [ ] `ruff check .` passes (no lint errors) or surfaces only issues that are explicitly intended for future phases.
- [ ] `git log --oneline -n 5` shows the initial scaffolding commit(s) on `main`.
- [ ] `git remote -v` shows the `Spectral_Swarm_3D` repository as `origin`.

---

## Relationship to the 2D Predecessor

The 2D work is preserved at `github.com/StevenFAU/Spectral_Swarm`, tag `v0.1-2d-poc`. That repository is read-only reference material for this project; no development happens there, and there is no cross-repository code dependency.

Earlier drafts of the Phase 0 scaffolding were developed inside the 2D repository under a `3d/` subdirectory. That work was migrated to this standalone repository and then removed from the 2D repository to restore it to the clean state described by its README (2D-only study). The scaffolding specifications in this document reflect the flattened, standalone form used here.

---

## What Future Claude Code Sessions Should Do

- **Phase 1 onwards:** open a fresh Claude Code session; read `SpectralSwarm3DPhases.md` and `CLAUDE.md`; execute the relevant phase; do not advance phases in the same session.
- **Re-verification after environment changes:** run the Pass/Fail checklist above. If any check fails, diagnose before proceeding.
- **Documentation updates:** any changes to scaffolding specifications must be reflected both in this document and in the actual files on disk.
