"""Data quality checks. Fail fast on bad data instead of training on it."""

import pandas as pd

from proto_star.config import DataConfig


class DataValidationError(ValueError):
    pass


def validate(df: pd.DataFrame, cfg: DataConfig, *, has_target: bool = True) -> None:
    """Raise DataValidationError listing every problem found."""
    problems: list[str] = []

    required = [c for c in (cfg.id_column, cfg.time_column) if c]
    if has_target:
        required.append(cfg.target)
    if cfg.features:
        required.extend(cfg.features)
    missing = [c for c in required if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")

    if df.empty:
        problems.append("dataframe is empty")

    if has_target and cfg.target in df.columns:
        if df[cfg.target].isna().all():
            problems.append(f"target {cfg.target!r} is entirely null")
        elif not pd.api.types.is_numeric_dtype(df[cfg.target]):
            problems.append(f"target {cfg.target!r} is not numeric")

    if cfg.id_column and cfg.id_column in df.columns and df[cfg.id_column].duplicated().any():
        n = int(df[cfg.id_column].duplicated().sum())
        problems.append(f"{n} duplicate values in id column {cfg.id_column!r}")

    if (
        cfg.time_column
        and cfg.time_column in df.columns
        and not pd.api.types.is_datetime64_any_dtype(df[cfg.time_column])
    ):
        problems.append(f"time column {cfg.time_column!r} is not a datetime")

    if problems:
        raise DataValidationError("Data validation failed:\n  - " + "\n  - ".join(problems))
