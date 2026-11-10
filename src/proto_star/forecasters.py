"""Forecasters defined in a trial config's ``custom`` block, built from registered kinds.

A trial config can define a forecaster without new trial code::

    custom:
      trend_damped:
        kind: blend
        params: {members: [trend_level10_15_sensitivity, current_best]}

Each kind is a factory ``(params, resolve) -> Forecaster``.  ``resolve`` looks up any other
forecaster the same config can name (baselines, ``current_best``, ensembles, pooled trends and
other custom forecasters), so a kind can combine them.  Every kind keeps the backtest contract:
compute everything from ``train`` (see :mod:`proto_star.backtest`).  Hyperparameters live in
``params``, not here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from proto_star.adjust import (
    CddFromTemperatureSpec,
    PersistenceSpec,
    SkewShiftSpec,
    cdd_from_temperature_forecast,
    persistence_forecast,
    skew_shift_forecast,
)
from proto_star.anomaly import (
    AnomalyCorrectionSpec,
    RelativeTrendSpec,
    TrendScaleSpec,
    anomaly_correction_forecast,
    relative_trend_forecast,
    trend_scale_forecast,
)
from proto_star.backtest import Forecaster
from proto_star.climate import METRICS, ClimateDataError, annual_to_long, baseline_forecast
from proto_star.direct import DirectSpec, direct_forecast
from proto_star.hottest import HottestSummerSpec, hottest_summer_forecast
from proto_star.levels import LevelAdjustSpec, level_adjust_forecast
from proto_star.neighbours import NeighbourSpec, neighbour_forecast

Resolver = Callable[[str], Forecaster]
KindFactory = Callable[[Mapping[str, Any], Resolver], Forecaster]
_KEY = ["city_id", "year", "metric"]


class CustomSpec(BaseModel):
    """One config-defined forecaster: a registered ``kind`` and its parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    params: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None  # one line for trial notes; a default is built otherwise


_KINDS: dict[str, tuple[KindFactory, str]] = {}


def register_kind(name: str, summary: str) -> Callable[[KindFactory], KindFactory]:
    """Register a forecaster kind under ``name``; ``summary`` is used in trial notes."""

    def deco(factory: KindFactory) -> KindFactory:
        if name in _KINDS:
            raise ValueError(f"forecaster kind {name!r} already registered")
        _KINDS[name] = (factory, summary)
        return factory

    return deco


def available_kinds() -> list[str]:
    return sorted(_KINDS)


def build_custom(spec: CustomSpec, resolve: Resolver) -> Forecaster:
    """Build the forecaster a :class:`CustomSpec` describes."""
    if spec.kind not in _KINDS:
        raise ValueError(f"unknown forecaster kind {spec.kind!r}; available: {available_kinds()}")
    factory, _ = _KINDS[spec.kind]
    return factory(spec.params, resolve)


def describe_custom(spec: CustomSpec) -> str:
    """One line describing a custom forecaster, for trial notes."""
    if spec.description:
        return spec.description
    _, summary = _KINDS[spec.kind]
    params = ", ".join(f"{key}={value}" for key, value in spec.params.items())
    return f"{summary} ({params})" if params else summary


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(_KEY)["predicted_value"]


@register_kind("blend", "Weighted mean of other forecasters, row by row")
def _blend(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    members = [str(name) for name in params["members"]]
    weights = np.asarray(params.get("weights") or [1.0] * len(members), dtype=float)
    if len(members) < 2 or len(weights) != len(members):
        raise ValueError("blend needs at least two members and one weight per member")
    if np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("blend weights must be non-negative and not all zero")
    unknown = sorted(set(params) - {"members", "weights"})
    if unknown:
        raise ValueError(f"blend got unknown params {unknown}")
    forecasters = [resolve(name) for name in members]

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        columns = [_indexed(fn(train, cutoff_year, forecast_years)) for fn in forecasters]
        joined = pd.concat(columns, axis=1, join="inner")
        if len(joined) < max(len(column) for column in columns):
            raise ClimateDataError("blend members do not forecast the same rows")
        values = joined.to_numpy() @ (weights / weights.sum())
        return pd.DataFrame(
            {**{k: joined.index.get_level_values(k) for k in _KEY}, "predicted_value": values}
        )

    return forecast


@register_kind("per_metric", "A different forecaster per metric")
def _per_metric(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    if set(params) != set(METRICS):
        raise ValueError(f"per_metric must map exactly {list(METRICS)}")
    chosen = {metric: resolve(str(params[metric])) for metric in METRICS}

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        frames = []
        for metric, fn in chosen.items():
            rows = fn(train, cutoff_year, forecast_years)
            frames.append(rows.loc[rows["metric"] == metric])
        return pd.concat(frames, ignore_index=True)

    return forecast


def _fill_missing(
    forecast: pd.DataFrame, history: pd.DataFrame, cutoff_year: int, forecast_years: list[int]
) -> pd.DataFrame:
    """Give every city/metric the 30-year mean where a model produced no row."""
    backup = baseline_forecast(
        history, cutoff_year=cutoff_year, forecast_years=forecast_years, method="thirty_year_mean"
    )
    extra = backup.merge(forecast[_KEY], on=_KEY, how="left", indicator=True)
    extra = extra.loc[extra["_merge"] == "left_only"].drop(columns="_merge")
    return pd.concat([forecast, extra], ignore_index=True)


@register_kind("direct", "Pooled direct multi-horizon median model on 30-year-mean anomalies")
def _direct(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = DirectSpec.model_validate(dict(params))

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        rows = direct_forecast(train, history, cutoff_year, forecast_years, spec)
        return _fill_missing(rows, history, cutoff_year, forecast_years)

    return forecast


@register_kind("persistence", "Base forecast plus an in-fold fraction of last year's error")
def _persistence(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = PersistenceSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return persistence_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("skew_shift", "Base forecast times 1 - q * CV^2, q fitted in-fold by MAE")
def _skew_shift(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = SkewShiftSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return skew_shift_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("cdd_from_temp", "CDD 30-year mean plus CDD per degree x temperature departure")
def _cdd_from_temp(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = CddFromTemperatureSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return cdd_from_temperature_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("level_adjust", "Base forecast with H4 common-residual and/or H11 shrunk levels")
def _level_adjust(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = LevelAdjustSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return level_adjust_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("hottest_summer", "Hottest day = 30-year mean + a June-August-based shift")
def _hottest_summer(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = HottestSummerSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return hottest_summer_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("neighbours", "Level moved toward a neighbour-anchored value by a pooled weight")
def _neighbours(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = NeighbourSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return neighbour_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("anomaly_correction", "Base forecast plus in-fold multiples of the recent anomaly")
def _anomaly_correction(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = AnomalyCorrectionSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return anomaly_correction_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("trend_scale", "Pooled-trend forecast with an in-fold trend multiplier kappa")
def _trend_scale(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = TrendScaleSpec.model_validate(dict(params))

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return trend_scale_forecast(train, cutoff_year, forecast_years, spec)

    return forecast


@register_kind("relative_trend", "Metric = 30-year mean x (1 + pooled relative slope x years)")
def _relative_trend(params: Mapping[str, Any], resolve: Resolver) -> Forecaster:
    spec = RelativeTrendSpec.model_validate(dict(params))
    base = resolve(spec.base)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        return relative_trend_forecast(base, train, cutoff_year, forecast_years, spec)

    return forecast
