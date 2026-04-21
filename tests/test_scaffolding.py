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
    three_d = REPO_ROOT
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
        path = three_d / rel
        assert path.exists(), f"Missing: {path}"
