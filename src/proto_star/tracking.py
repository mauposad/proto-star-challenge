"""Lightweight local experiment tracking.

Each run gets `runs/<timestamp>_<name>/` containing:
    config.yaml   exact config used
    meta.json     git commit, dirty flag, timestamp, feature columns
    metrics.json  validation metrics
    model.joblib  fitted model

Paste the metrics line into docs/experiments.md when a run is worth sharing.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from proto_star.config import ExperimentConfig
from proto_star.paths import PROJECT_ROOT


def git_info() -> dict[str, Any]:
    def run(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {
        "commit": run("rev-parse", "--short", "HEAD") or None,
        "dirty": bool(run("status", "--porcelain")),
    }


def create_run_dir(cfg: ExperimentConfig, runs_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / f"{stamp}_{cfg.name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    with (run_dir / "config.yaml").open("w") as f:
        yaml.safe_dump(cfg.model_dump(), f, sort_keys=False)
    return run_dir


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())
