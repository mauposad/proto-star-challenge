"""Canonical project paths. Import these instead of hard-coding strings."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"  # immutable source data, exactly as downloaded
INTERIM_DIR = DATA_DIR / "interim"  # intermediate cleaned/joined data
PROCESSED_DIR = DATA_DIR / "processed"  # final model-ready tables
EXTERNAL_DIR = DATA_DIR / "external"  # third-party reference data

CONFIGS_DIR = PROJECT_ROOT / "configs"
RUNS_DIR = PROJECT_ROOT / "runs"  # one folder per training run
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"


def resolve(path: str | Path) -> Path:
    """Resolve a path relative to the project root (absolute paths pass through)."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p
