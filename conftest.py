"""Pytest configuration for the 3D package."""
import pytest
import yaml
from pathlib import Path


@pytest.fixture
def config():
    """Load the 3D default config."""
    config_path = Path(__file__).parent / "configs" / "default.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)
