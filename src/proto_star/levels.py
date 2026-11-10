"""Level adjustments for hypotheses H4 and H11 in ``hypotheses.md``, applied to any base forecast.

Both act on the recent level that the pooled-trend candidate carries forward:

* H4 (``common_residual``): subtract, from each city's level, the national mean residual from the
  pooled trend line averaged over that city's level-window years. The premise is that shared
  multi-year anomalies around the trend do not persist.  For CDD the residual is temperature's,
  scaled by the city's CDD per degree.
* H11 (``shrink="region"``): shrink each city's recent anomaly (level minus 30-year mean) toward
  the leave-one-out mean anomaly of its region, by a pooled James-Stein-type factor ``B`` fitted
  in-fold.  ``shrink="zero"`` is the methodologist's control: the same ``B``, toward zero.

Each adjustment is a constant per city and metric, so it moves the base forecast's level and
keeps its slope.  Every quantity is computed from the fold's training rows.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.climate import BASELINE_WINDOW_YEARS, annual_to_long
from proto_star.trend import PooledTrendSpec, cdd_per_degree, pooled_slope
from proto_star.utils.logging import get_logger

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
TEMPERATURE = "annual_avg_temp"
CDD = "cdd"
log = get_logger(__name__)


class LevelAdjustSpec(BaseModel):
    """Settings of an H4/H11 level adjustment, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    common_residual: bool = False  # H4
    shrink: Literal["none", "region", "zero"] = "none"  # H11 and its control
    metrics: list[str] = Field(default_factory=lambda: [TEMPERATURE, CDD])
    level_years: list[int] = Field(default_factory=lambda: [10, 15], min_length=1)
    trend_window: int = Field(default=40, ge=10)
    min_city_years: int = Field(default=10, ge=3)

    @model_validator(mode="after")
    def _check_metrics(self) -> LevelAdjustSpec:
        if not self.metrics or not set(self.metrics) <= {TEMPERATURE, CDD}:
            raise ValueError(f"metrics must be a non-empty subset of {[TEMPERATURE, CDD]}")
        return self


def _recent(rows: pd.DataFrame, years: int) -> pd.DataFrame:
    return rows.sort_values("year").groupby("city_id").tail(years)


def _level(rows: pd.DataFrame, level_years: list[int]) -> pd.Series:
    """The candidate's level: the mean over windows of each city's last-N valid values."""
    return pd.concat(
        [_recent(rows, n).groupby("city_id")["actual_value"].mean() for n in level_years], axis=1
    ).mean(axis=1)


def _common_residual(
    rows: pd.DataFrame, cutoff_year: int, spec: LevelAdjustSpec, slope: float
) -> pd.Series:
    """National mean residual per year from the pooled trend, within the trend window."""
    first = cutoff_year - spec.trend_window + 1
    window = rows.loc[rows["year"].between(first, cutoff_year)]
    window = window.loc[window.groupby("city_id")["year"].transform("size") >= spec.min_city_years]
    by_city = window.groupby("city_id")
    residual = (window["actual_value"] - by_city["actual_value"].transform("mean")) - slope * (
        window["year"] - by_city["year"].transform("mean")
    )
    return residual.groupby(window["year"]).mean()


def _window_mean_of(series: pd.Series, rows: pd.DataFrame, level_years: list[int]) -> pd.Series:
    """Per city, the mean of a per-year ``series`` over its level-window years."""
    parts = []
    for n in level_years:
        recent = _recent(rows, n)
        parts.append(recent.assign(r=recent["year"].map(series)).groupby("city_id")["r"].mean())
    return pd.concat(parts, axis=1).mean(axis=1)


def _noise_factor(level_years: list[int]) -> float:
    """Var(level - 30-year mean) / Var(one year) for iid years, with nested windows."""
    weights = np.zeros(BASELINE_WINDOW_YEARS)
    for n in level_years:
        weights[-n:] += 1.0 / (n * len(level_years))
    return float(((weights - 1.0 / BASELINE_WINDOW_YEARS) ** 2).sum())


def level_adjust_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: LevelAdjustSpec,
) -> pd.DataFrame:
    """The base forecast with H4 and/or H11 level adjustments for ``spec.metrics``."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    trend_spec = PooledTrendSpec(
        level_years=spec.level_years,
        trend_window=spec.trend_window,
        min_city_years=spec.min_city_years,
    )
    temp_rows = history.loc[history["metric"] == TEMPERATURE]
    temp_slope = pooled_slope(history, TEMPERATURE, cutoff_year, trend_spec)
    common = _common_residual(temp_rows, cutoff_year, spec, temp_slope)
    sensitivity = cdd_per_degree(history, cutoff_year, trend_spec)
    region = train.assign(city_id=train["ID"].astype(str)).groupby("city_id")["region"].first()
    factor = _noise_factor(spec.level_years)

    forecast = base(train, cutoff_year, forecast_years).copy()
    for metric in spec.metrics:
        rows = history.loc[history["metric"] == metric]
        level = _level(rows, spec.level_years)
        delta = pd.Series(0.0, index=level.index)
        if spec.common_residual:
            shift = _window_mean_of(common, rows, spec.level_years).fillna(0.0)
            if metric == CDD:
                shift = shift * sensitivity.reindex(shift.index).fillna(0.0)
            delta += shift
        if spec.shrink != "none":
            window = rows.loc[rows["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
            m30 = window.groupby("city_id")["actual_value"].mean()
            detrended = window["actual_value"] - temp_slope * window["year"] * (
                metric == TEMPERATURE
            )
            variance = detrended.groupby(window["city_id"]).var()
            anomaly = (level - delta - m30).dropna()
            groups = region.reindex(anomaly.index)
            total = anomaly.groupby(groups).transform("sum")
            count = anomaly.groupby(groups).transform("size")
            loo = ((total - anomaly) / (count - 1)).where(count > 1, 0.0)
            target = loo if spec.shrink == "region" else pd.Series(0.0, index=anomaly.index)
            noise = float((variance.reindex(anomaly.index) * factor).mean())
            spread = float(((anomaly - loo) ** 2).mean())
            weight = float(np.clip(1.0 - noise / spread, 0.0, 1.0)) if spread > 0 else 1.0
            log.info(
                "level shrink %s %s at cutoff %d: B=%.3f", spec.shrink, metric, cutoff_year, weight
            )
            delta = delta.add((1.0 - weight) * (anomaly - target), fill_value=0.0)
        if spec.common_residual:
            log.info(
                "common residual %s at cutoff %d: mean shift %.3f",
                metric,
                cutoff_year,
                float(delta.mean()),
            )
        is_metric = forecast["metric"] == metric
        cities = forecast.loc[is_metric, "city_id"]
        offset = delta.reindex(cities).fillna(0.0).to_numpy()
        forecast.loc[is_metric, "predicted_value"] = (
            forecast.loc[is_metric, "predicted_value"].to_numpy() - offset
        )
    return forecast
