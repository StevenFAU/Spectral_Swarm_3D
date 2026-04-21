"""Phase 1 integrity regression tests.

These guard invariants established at the end of Phase 1 so future phases
cannot silently break them. They are intentionally short and focused.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from spectral_swarm_3d.model import BoidSwarmModel3D
from spectral_swarm_3d.telemetry import record_environment


REPO_ROOT = Path(__file__).parent.parent

_CORE_PACKAGES = (
    "mesa", "numpy", "scipy", "scikit-learn", "ripser", "persim",
    "pandas", "pyarrow", "pyyaml", "matplotlib", "networkx",
)

_SCENARIOS = ["none", "leader", "jamming", "split_merge", "milling"]


def test_config_wa_is_calibrated_value():
    """w_a and alignment_rule must match the Phase 1 calibrated baseline."""
    cfg_path = REPO_ROOT / "configs" / "default.yaml"
    with cfg_path.open() as f:
        cfg = yaml.safe_load(f)
    assert cfg["w_a"] == 1.0, "w_a drifted from the Phase 1 calibrated value"
    assert cfg["alignment_rule"] == "mean", "alignment_rule must stay 'mean' (A6)"


def _git_available(repo_root: Path) -> bool:
    try:
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def test_metadata_git_commit_resolves_to_real_sha():
    """D6: git_commit must be a real 40-char SHA, not the 'unknown' fallback."""
    if not _git_available(REPO_ROOT):
        pytest.skip("not inside a git repo; SHA capture not applicable")
    env = record_environment(REPO_ROOT)
    assert re.fullmatch(r"[0-9a-f]{40}", env["git_commit"]), (
        f"git_commit not a 40-char hex SHA: {env['git_commit']!r}"
    )


def test_metadata_package_versions_covers_core_deps():
    """record_environment must report a version for every core runtime dep."""
    env = record_environment(REPO_ROOT)
    pkgs = env["package_versions"]
    missing = [p for p in _CORE_PACKAGES if p not in pkgs]
    assert not missing, f"metadata missing package entries: {missing}"


@pytest.mark.parametrize("scenario", _SCENARIOS)
def test_reproducibility_across_scenarios(config, scenario):
    """Same seed → bit-identical positions after 50 steps for every scenario."""
    m1 = BoidSwarmModel3D(config, scenario_name=scenario, seed=0)
    m2 = BoidSwarmModel3D(config, scenario_name=scenario, seed=0)
    for _ in range(50):
        m1.step()
        m2.step()
    assert np.array_equal(m1._positions(), m2._positions()), (
        f"{scenario}: positions diverge under identical seed"
    )


def test_near_boundary_flag_plausible_fraction(config, tmp_path):
    """D7: near_boundary must vary — not be hardcoded to a constant."""
    csv_path = tmp_path / "near_boundary_sanity.csv"
    m = BoidSwarmModel3D(config, scenario_name="none", seed=0,
                         telemetry_path=csv_path)
    m.run(T=100)
    df = pd.read_csv(csv_path)
    frac = float(df["near_boundary"].mean())
    assert 0.1 <= frac <= 0.95, (
        f"near_boundary fraction {frac:.3f} outside plausible range; "
        "flag may be constant rather than computed"
    )
