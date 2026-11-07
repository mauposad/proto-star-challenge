"""Pooled-trend forecast: each city's recent level plus one warming trend shared by all cities.

A trend fitted to one city is mostly year-to-year noise, and the backtests punish it. Pooling
keeps the signal: one within-city slope estimated across every city, added to each city's own
recent level. Temperature and CDD get this treatment. Precipitation and hottest day keep the
30-year mean, because no trend or other window beat it reliably in backtests.

Two choices are specific to this model:

* The pooled slope cannot go negative. Mid-century cooling makes the 40-year slope negative at
  the 1980 and 1985 cut-offs, and extrapolating it lost skill. This floor was added after seeing
  that failure, so the README discloses it. It does not change the 2019-2025 forecast, where
  the slope is positive.
* CDD uses a per-city trend: the pooled temperature trend times that city's own CDD gained per
  degree. A warm city gains far more CDD from one degree than a cool one does.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from proto_star.climate import baseline_forecast, validate_climate_history

TEMPERATURE = "annual_avg_temp"
CDD = "cdd"
FLAT_METHOD = "thirty_year_mean"


class PooledTrendSpec(BaseModel):
    """Settings of one pooled-trend forecaster, set in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    level_years: list[int] = Field(min_length=1)  # one level per window, then averaged
    trend_window: int = Field(ge=10)  # calendar years used to fit the pooled slope
    min_city_years: int = Field(default=10, ge=3)  # valid years a city needs to enter a fit
    cdd_sensitivity: bool = True  # False: CDD uses its own pooled slope, the same for all cities


def _window_anomalies(
    history: pd.DataFrame, metric: str, cutoff_year: int, spec: PooledTrendSpec
) -> pd.DataFrame:
    """Each city's year and value, as distances from its own mean over the trend window."""
    first_year = cutoff_year - spec.trend_window + 1
    window = history.loc[
        (history["metric"] == metric) & history["year"].between(first_year, cutoff_year)
    ]
    by_city = window.groupby("city_id")
    window = window.loc[by_city["year"].transform("size") >= spec.min_city_years]
    by_city = window.groupby("city_id")
    return pd.DataFrame(
        {
            "city_id": window["city_id"],
            "year": window["year"],
            "x": window["year"] - by_city["year"].transform("mean"),
            "y": window["actual_value"] - by_city["actual_value"].transform("mean"),
        }
    )


def pooled_slope(
    history: pd.DataFrame, metric: str, cutoff_year: int, spec: PooledTrendSpec
) -> float:
    """Within-city least-squares slope per year across all cities, floored at zero."""
    anomalies = _window_anomalies(history, metric, cutoff_year, spec)
    spread = float((anomalies["x"] ** 2).sum())
    if spread == 0.0:
        return 0.0
    return max(0.0, float((anomalies["x"] * anomalies["y"]).sum()) / spread)


def cdd_per_degree(history: pd.DataFrame, cutoff_year: int, spec: PooledTrendSpec) -> pd.Series:
    """Each city's CDD gained per degree of annual temperature, from its own trend window."""
    first_year = cutoff_year - spec.trend_window + 1
    window = history.loc[
        history["metric"].isin([TEMPERATURE, CDD])
        & history["year"].between(first_year, cutoff_year)
    ]
    paired = window.pivot_table(
        index=["city_id", "year"], columns="metric", values="actual_value"
    ).reindex(columns=[TEMPERATURE, CDD])
    paired = paired.dropna()
    by_city = paired.groupby(level="city_id")
    paired = paired.loc[by_city[CDD].transform("size") >= spec.min_city_years]
    by_city = paired.groupby(level="city_id")
    temperature = paired[TEMPERATURE] - by_city[TEMPERATURE].transform("mean")
    cdd = paired[CDD] - by_city[CDD].transform("mean")
    spread = (temperature**2).groupby(level="city_id").sum()
    covariance = (temperature * cdd).groupby(level="city_id").sum()
    return (covariance / spread.where(spread > 0)).dropna().clip(lower=0.0)


def _levels(history: pd.DataFrame, metric: str, cutoff_year: int, years: int) -> pd.DataFrame:
    """Mean of each city's last ``years`` valid values, and the mean year they sit at."""
    rows = history.loc[(history["metric"] == metric) & (history["year"] <= cutoff_year)]
    recent = rows.sort_values("year").groupby("city_id").tail(years)
    return recent.groupby("city_id").agg(level=("actual_value", "mean"), center=("year", "mean"))


def _city_slopes(
    history: pd.DataFrame, metric: str, cutoff_year: int, spec: PooledTrendSpec, cities: pd.Index
) -> pd.Series:
    own_slope = pooled_slope(history, metric, cutoff_year, spec)
    if metric != CDD or not spec.cdd_sensitivity:
        return pd.Series(own_slope, index=cities)
    warming = pooled_slope(history, TEMPERATURE, cutoff_year, spec)
    # Cities too sparse to estimate their own sensitivity fall back to the pooled CDD slope.
    return (cdd_per_degree(history, cutoff_year, spec) * warming).reindex(cities).fillna(own_slope)


def _trend_rows(
    history: pd.DataFrame,
    metric: str,
    cutoff_year: int,
    years: np.ndarray,
    spec: PooledTrendSpec,
) -> pd.DataFrame:
    """Forecast one metric: the mean over level windows of level + slope x years from level."""
    windows = [_levels(history, metric, cutoff_year, n) for n in spec.level_years]
    cities = windows[0].index
    slopes = _city_slopes(history, metric, cutoff_year, spec, cities).to_numpy()
    frames = []
    for year in years:
        paths = [
            levels["level"].to_numpy() + slopes * (year - levels["center"].to_numpy())
            for levels in windows
        ]
        frames.append(
            pd.DataFrame(
                {
                    "city_id": cities.astype(str),
                    "year": int(year),
                    "metric": metric,
                    "predicted_value": np.mean(paths, axis=0),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def pooled_trend_forecast(
    history: pd.DataFrame,
    *,
    cutoff_year: int,
    forecast_years: Iterable[int],
    spec: PooledTrendSpec,
) -> pd.DataFrame:
    """Forecast all four metrics for every known city, using only years up to the cut-off."""
    validate_climate_history(history)
    years = np.asarray(list(forecast_years), dtype=int)
    train = history.loc[history["year"] <= cutoff_year]
    flat = baseline_forecast(
        train, cutoff_year=cutoff_year, forecast_years=years, method=FLAT_METHOD
    )
    trends = [_trend_rows(train, metric, cutoff_year, years, spec) for metric in (TEMPERATURE, CDD)]
    kept = flat.loc[~flat["metric"].isin([TEMPERATURE, CDD])]
    return pd.concat([kept, *trends], ignore_index=True)
