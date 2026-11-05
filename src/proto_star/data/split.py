"""Train/validation splitting.

For forecasting, default to a time-based split: validate on the most recent
period, train on everything before it. A random split lets the model peek at
neighbouring days and gives over-optimistic scores that won't hold on the
leaderboard.
"""

import pandas as pd

from proto_star.config import SplitConfig


def split(
    df: pd.DataFrame, cfg: SplitConfig, *, time_column: str | None, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if cfg.strategy == "time":
        if time_column is None:
            raise ValueError("time split requires a time column")
        return time_split(df, time_column, cfg.valid_fraction)
    return random_split(df, cfg.valid_fraction, seed)


def time_split(
    df: pd.DataFrame, time_column: str, valid_fraction: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All validation timestamps are strictly later than all training timestamps."""
    cutoff = df[time_column].quantile(1 - valid_fraction)
    train = df[df[time_column] < cutoff]
    valid = df[df[time_column] >= cutoff]
    return train, valid


def random_split(
    df: pd.DataFrame, valid_fraction: float, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = df.sample(frac=valid_fraction, random_state=seed)
    return df.drop(valid.index), valid
