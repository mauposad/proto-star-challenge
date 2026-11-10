"""Team Tatakae's temperature views, re-implemented from their README (final round, T1 and T2).

Source: Mashrafi Mahmud Rafi (@ironMan334), "Team Tatakae: Protostar Climate Challenge
Submission", Hugging Face dataset ``ironMan334/protostar-climate-team-tatakae`` (CC BY 4.0),
README at commit ``f18c1178c1b97566c75facc94c886184ebaa2a10``, section "Method". Only the
README text was read; no code was copied or downloaded. Our reading of the text, with every
fixed parameter, is in ``docs/trials/final_temp.md``.

* ``final_temp_recent_normal`` (T1, "recent normal + regional warming"): the city's mean of
  its last 15 valid years, plus the regional warming rate times (year - mid-year of those
  years). Regional rate = mean 40-year OLS temperature slope of the 32 nearest cities (the
  city and its 31 nearest others).
* ``final_temp_region_departure`` (T2, "region + departure"): region anomaly (mean of the 32
  nearest cities' anomalies, each against its own 30-year mean) carried forward by its
  30-year trend line, plus the city's mean departure from the region over its last 5 valid
  years, on top of the city's 30-year mean. Final = 0.75 x this view + 0.25 x T1.

Both produce ``annual_avg_temp`` rows only; use them through ``swap_metric``. Cities a view
cannot forecast fall back to the pooled-trend temperature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._final_temp_common import (
    coordinates,
    last_valid_level,
    nearest_with_self,
    ols_slopes,
    pooled_trend_temperature,
    temperature_panel,
    to_long,
    window_columns,
    with_fallback,
)
from proto_star.neighbors import neighbor_mean, own_anomalies


class RecentNormalSpec(ForecasterSpec):
    """T1 settings (defaults = Tatakae's README)."""

    level_years: int = Field(default=15, ge=1)
    rate_window: int = Field(default=40, ge=10)
    n_cities: int = Field(default=32, ge=1)
    min_years: int = Field(default=10, ge=3)

    def describe(self) -> str:
        return (
            f"Tatakae recent normal: last-{self.level_years}-valid-year mean + regional "
            f"warming rate (mean {self.rate_window}-year slope of the {self.n_cities} nearest "
            "cities, self included) x years from the window mid-year"
        )


class RegionDepartureSpec(RecentNormalSpec):
    """T2 settings (defaults = Tatakae's README)."""

    normal_window: int = Field(default=30, ge=10)
    departure_years: int = Field(default=5, ge=1)
    view_weight: float = Field(default=0.75, ge=0.0, le=1.0)

    def describe(self) -> str:
        return (
            f"Tatakae region + departure: {self.view_weight:g} x [city {self.normal_window}-"
            f"year mean + {self.n_cities}-city region anomaly on its {self.normal_window}-year "
            f"line + last-{self.departure_years}-year departure] + {1 - self.view_weight:g} x "
            "recent normal"
        )


def recent_normal_table(
    train: pd.DataFrame, cutoff_year: int, forecast_years: list[int], spec: RecentNormalSpec
) -> pd.DataFrame:
    """T1 as a city x year table (NaN where a city has no level or rate)."""
    panel = temperature_panel(train, cutoff_year)
    level = last_valid_level(panel, spec.level_years)
    window = window_columns(panel, cutoff_year - spec.rate_window + 1, cutoff_year)
    slopes = ols_slopes(window, min_years=spec.min_years)["slope"]
    weights = nearest_with_self(coordinates(train), spec.n_cities)
    rate = neighbor_mean(slopes.to_frame("rate"), weights)["rate"].reindex(level.index)
    years = np.asarray(forecast_years, dtype=float)
    values = level["level"].to_numpy()[:, None] + rate.to_numpy()[:, None] * (
        years[None, :] - level["center"].to_numpy()[:, None]
    )
    return pd.DataFrame(values, index=level.index, columns=list(forecast_years))


def region_departure_view(
    train: pd.DataFrame, cutoff_year: int, forecast_years: list[int], spec: RegionDepartureSpec
) -> pd.DataFrame:
    """The "region + departure" view alone, as a city x year table."""
    panel = temperature_panel(train, cutoff_year)
    first = cutoff_year - spec.normal_window + 1
    window = window_columns(panel, first, cutoff_year)
    anomalies = own_anomalies(
        window, cutoff_year, window=spec.normal_window, min_years=spec.min_years
    )
    normal = window.mean(axis=1).where(window.notna().sum(axis=1) >= spec.min_years)
    weights = nearest_with_self(coordinates(train), spec.n_cities)
    region = neighbor_mean(anomalies, weights)
    line = ols_slopes(region, min_years=spec.min_years)
    region_mean = region.mean(axis=1)
    region_year = (
        region.notna().mul(region.columns.astype(float), axis=1).where(region.notna()).mean(axis=1)
    )
    departure = (anomalies - region).apply(
        lambda row: row.dropna().tail(spec.departure_years).mean(), axis=1
    )
    years = np.asarray(forecast_years, dtype=float)
    region_forecast = region_mean.to_numpy()[:, None] + line["slope"].reindex(
        region.index
    ).to_numpy()[:, None] * (years[None, :] - region_year.to_numpy()[:, None])
    values = (normal + departure).to_numpy()[:, None] + region_forecast
    return pd.DataFrame(values, index=panel.index, columns=list(forecast_years))


def build_recent_normal(spec: RecentNormalSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        fallback = pooled_trend_temperature(train, cutoff_year, forecast_years)
        table = recent_normal_table(train, cutoff_year, forecast_years, spec)
        return to_long(with_fallback(table, fallback))

    return forecast


def build_region_departure(spec: RegionDepartureSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        fallback = pooled_trend_temperature(train, cutoff_year, forecast_years)
        recent = with_fallback(
            recent_normal_table(train, cutoff_year, forecast_years, spec), fallback
        )
        view = with_fallback(
            region_departure_view(train, cutoff_year, forecast_years, spec), recent
        )
        return to_long(spec.view_weight * view + (1.0 - spec.view_weight) * recent)

    return forecast


register_kind("final_temp_recent_normal", RecentNormalSpec, build_recent_normal)
register_kind("final_temp_region_departure", RegionDepartureSpec, build_region_departure)
