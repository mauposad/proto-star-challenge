"""Feature engineering.

Rule: a feature function must only use information available at prediction
time for that row. Anything that looks at future rows (e.g. a centered rolling
mean, or statistics over the whole dataset) leaks the answer.
"""

import numpy as np
import pandas as pd

from proto_star.config import DataConfig


def add_calendar_features(df: pd.DataFrame, time_column: str) -> pd.DataFrame:
    """Cyclical encodings of seasonality, so Dec 31 and Jan 1 are close together."""
    t = df[time_column]
    day = t.dt.day_of_year
    out = df.copy()
    out["doy_sin"] = np.sin(2 * np.pi * day / 365.25)
    out["doy_cos"] = np.cos(2 * np.pi * day / 365.25)
    out["month"] = t.dt.month
    out["year"] = t.dt.year
    return out


def build_features(df: pd.DataFrame, cfg: DataConfig) -> pd.DataFrame:
    """Return the model input matrix X. Deterministic and identical for train and test."""
    if cfg.calendar_features and cfg.time_column:
        df = add_calendar_features(df, cfg.time_column)

    if cfg.features is not None:
        cols = list(cfg.features)
        if cfg.calendar_features and cfg.time_column:
            cols += ["doy_sin", "doy_cos", "month", "year"]
    else:
        excluded = {cfg.target, cfg.id_column, cfg.time_column}
        cols = [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
    return df[cols]
