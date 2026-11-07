"""Per-series normalized lag features for pooled (global) forecasters (papers P09, P14).

Everything here is a pure function of one fold's ``train`` frame.  A city x year panel is
built from the quality-screened history, and every feature at origin year ``t`` uses
calendar years ``<= t`` only: lags are ``shift(k)`` with ``k >= 0`` and windows are pandas
``rolling`` with the default right alignment.  Training targets are ``y[t + lead]`` with
``t + lead <= cutoff``, so they also come from ``train``.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from proto_star.climate import BASELINE_WINDOW_YEARS, annual_to_long

LEVEL_MIN_YEARS = 10  # valid years needed in the 30-year window for a level and scale
MEAN_MIN_YEARS = 3  # valid years needed in a shorter trailing window
STATIC_NUMERIC = ("lat", "lon")
STATIC_CATEGORICAL = ("region",)


def wide_panels(train: pd.DataFrame, cutoff_year: int) -> dict[str, pd.DataFrame]:
    """City x calendar-year panels per metric, NaN where a year is missing or invalid."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    first = int(history["year"].min())
    years = pd.RangeIndex(first, cutoff_year + 1, name="year")
    cities = sorted(train["ID"].astype(str).unique())
    panels: dict[str, pd.DataFrame] = {}
    for metric, rows in history.groupby("metric"):
        # Keys are unique (validated by annual_to_long), so "first" never aggregates.
        wide = rows.pivot_table(
            index="city_id", columns="year", values="actual_value", aggfunc="first"
        )
        panels[str(metric)] = wide.reindex(index=cities, columns=years)
    return panels


def city_static(train: pd.DataFrame) -> pd.DataFrame:
    """Lat, Lon and region per city, from the fold's own rows."""
    static = (
        train.assign(city_id=train["ID"].astype(str))
        .groupby("city_id")
        .agg(lat=("Lat", "first"), lon=("Lon", "first"), region=("region", "first"))
    )
    static["region"] = static["region"].astype(str)
    return static


def _to_long(by_year: pd.DataFrame, year_name: str, value_name: str) -> pd.DataFrame:
    """Year-by-city frame to rows of ``year_name, city_id, value_name`` (NaN kept)."""
    frame = by_year.rename_axis(index=year_name, columns="city_id").reset_index()
    return frame.melt(id_vars=year_name, var_name="city_id", value_name=value_name)


def lag_names(n_lags: int) -> list[str]:
    return [f"lag_{k}" for k in range(n_lags)]


def mean_names(windows: Sequence[int]) -> list[str]:
    return [f"mean_{w}" for w in windows]


def origin_features(wide: pd.DataFrame, *, n_lags: int, windows: Sequence[int]) -> pd.DataFrame:
    """Normalized features for every (city, origin year) in ``wide``.

    ``level`` and ``scale`` are the mean and standard deviation of the valid years in the 30
    calendar years ending at the origin (the reference forecast's window).  Lags and shorter
    trailing means are reported as ``(value - level) / scale``.
    """
    by_year = wide.T  # rows: years ascending, columns: cities
    level = by_year.rolling(BASELINE_WINDOW_YEARS, min_periods=LEVEL_MIN_YEARS).mean()
    scale = by_year.rolling(BASELINE_WINDOW_YEARS, min_periods=LEVEL_MIN_YEARS).std()
    scale = scale.where(scale > 0)
    columns: dict[str, pd.DataFrame] = {"level": level, "scale": scale}
    for k, name in enumerate(lag_names(n_lags)):
        columns[name] = (by_year.shift(k) - level) / scale
    for window, name in zip(windows, mean_names(windows), strict=True):
        trailing = by_year.rolling(window, min_periods=min(window, MEAN_MIN_YEARS)).mean()
        columns[name] = (trailing - level) / scale
    long = {name: _to_long(frame, "origin", name) for name, frame in columns.items()}
    features = long["level"][["origin", "city_id"]].copy()
    for name, frame in long.items():
        features[name] = frame[name].to_numpy()
    return features


def training_examples(
    wide: pd.DataFrame,
    features: pd.DataFrame,
    *,
    cutoff_year: int,
    leads: Sequence[int],
    train_years: int | None,
    origin_stride: int,
) -> pd.DataFrame:
    """Direct multi-horizon examples: features at origin ``t``, target ``y[t + lead]``.

    Only targets inside ``train`` (``t + lead <= cutoff_year``) are kept, and only the last
    ``train_years`` target years when set.  ``origin_stride`` thins origins deterministically
    (every k-th year counted back from the cutoff) to bound fitting time.
    """
    usable = features.dropna(subset=["level", "scale"])
    usable = usable.loc[(cutoff_year - usable["origin"]) % origin_stride == 0]
    long_target = _to_long(wide.T, "target_year", "target_value").dropna(subset=["target_value"])
    frames = []
    for lead in leads:
        part = usable.assign(lead=lead, target_year=usable["origin"] + lead)
        part = part.loc[part["target_year"] <= cutoff_year]
        if train_years is not None:
            part = part.loc[part["target_year"] > cutoff_year - train_years]
        frames.append(part.merge(long_target, on=["city_id", "target_year"], how="inner"))
    examples = pd.concat(frames, ignore_index=True)
    examples["target"] = (examples["target_value"] - examples["level"]) / examples["scale"]
    return examples


def add_static(frame: pd.DataFrame, static: pd.DataFrame) -> pd.DataFrame:
    return frame.merge(static, left_on="city_id", right_index=True, how="left")


def finite(values: np.ndarray) -> bool:
    return bool(np.isfinite(values).all())
