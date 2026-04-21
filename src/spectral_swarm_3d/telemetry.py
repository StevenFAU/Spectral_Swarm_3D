"""Telemetry CSV logger and reproducibility metadata for 3D swarm runs.

Plan anchors: Phase 1 scope, D6 (reproducibility metadata), D7 (boundary
diagnostic). Telemetry columns (one row per agent per step)::

    step, agent_id, x, y, z, vx, vy, vz, speed,
    u_x, u_y, u_z, is_leader, leader_group,
    neighbor_count, local_density, scenario_label, near_boundary
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import socket
import subprocess
import sys
from importlib import metadata as _metadata
from pathlib import Path
from typing import Any

import numpy as np


_CSV_FIELDS = [
    "step",
    "agent_id",
    "x", "y", "z",
    "vx", "vy", "vz",
    "speed",
    "u_x", "u_y", "u_z",
    "is_leader",
    "leader_group",
    "neighbor_count",
    "local_density",
    "scenario_label",
    "near_boundary",
]

_PACKAGES_TO_RECORD = (
    "mesa",
    "numpy",
    "scipy",
    "scikit-learn",
    "ripser",
    "persim",
    "pandas",
    "pyarrow",
    "pyyaml",
    "matplotlib",
    "networkx",
)


def _git_commit(repo_root: Path | None = None) -> str:
    """Return the current git commit hash, or ``"unknown"`` if unavailable."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root) if repo_root else None,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def record_environment(repo_root: Path | None = None) -> dict[str, Any]:
    """Capture reproducibility metadata (D6).

    Returns a dict with ``git_commit``, ``python_version``, ``package_versions``
    (dict mapping package name to pinned version string), ``hostname``, and
    ``timestamp`` (ISO-8601, UTC).
    """
    pkg_versions: dict[str, str] = {}
    for name in _PACKAGES_TO_RECORD:
        try:
            pkg_versions[name] = _metadata.version(name)
        except _metadata.PackageNotFoundError:
            pkg_versions[name] = "not-installed"
    return {
        "git_commit": _git_commit(repo_root),
        "python_version": sys.version.split()[0],
        "package_versions": pkg_versions,
        "hostname": socket.gethostname(),
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }


class TelemetryLogger:
    """CSV writer for 3D swarm telemetry."""

    def __init__(self, csv_path: Path) -> None:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._path = csv_path
        self._file = csv_path.open("w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=_CSV_FIELDS)
        self._writer.writeheader()

    def log_step(
        self,
        step: int,
        agents: list,
        positions: np.ndarray,
        velocities: np.ndarray,
        neighbor_counts: np.ndarray,
        local_density: np.ndarray,
        scenario_label: str,
        near_boundary: np.ndarray,
    ) -> None:
        """Append one row per agent for the given step."""
        rows = []
        for i, ag in enumerate(agents):
            vx, vy, vz = (float(velocities[i, 0]),
                          float(velocities[i, 1]),
                          float(velocities[i, 2]))
            speed = float(np.sqrt(vx * vx + vy * vy + vz * vz))
            if speed > 1e-12:
                ux, uy, uz = vx / speed, vy / speed, vz / speed
            else:
                ux = uy = uz = 0.0
            rows.append({
                "step": int(step),
                "agent_id": int(ag.unique_id),
                "x": float(positions[i, 0]),
                "y": float(positions[i, 1]),
                "z": float(positions[i, 2]),
                "vx": vx, "vy": vy, "vz": vz,
                "speed": speed,
                "u_x": ux, "u_y": uy, "u_z": uz,
                "is_leader": int(ag.is_leader),
                "leader_group": int(ag.leader_group),
                "neighbor_count": int(neighbor_counts[i]),
                "local_density": float(local_density[i]),
                "scenario_label": str(scenario_label),
                "near_boundary": int(near_boundary[i]),
            })
        self._writer.writerows(rows)

    def close(self) -> None:
        self._file.flush()
        self._file.close()


def save_metadata(
    config: dict[str, Any],
    seed: int,
    scenario: str,
    path: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Write the companion metadata JSON with D6 reproducibility fields.

    Returns the payload dict that was written (useful for tests).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "seed": int(seed),
        "scenario": str(scenario),
        "config": dict(config),
        "environment": record_environment(repo_root),
    }
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)
    return payload


def load_metadata(path: Path) -> dict[str, Any]:
    with Path(path).open() as f:
        return json.load(f)
