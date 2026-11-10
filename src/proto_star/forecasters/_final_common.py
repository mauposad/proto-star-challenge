"""Shared pieces of the final-round precipitation and hottest-day components.

* :func:`thirty_year_rows`: the official 30-year mean (``thirty_year_mean``) for one metric, the
  level every component starts from and falls back to, so a component covers exactly the rows
  of the base forecast it is swapped into.
* :func:`neighbor_nudge`: Tatakae's station-move nudge (each city's mean departure from its
  nearest neighbors over the last years), re-implemented from the README of
  ``ironMan334/protostar-climate-team-tatakae`` (CC BY 4.0), commit
  ``f18c1178c1b97566c75facc94c886184ebaa2a10``, section "Method", "Rain and the hottest day".
  No code of that team was downloaded or copied.
* :func:`kernel_matrix` and :func:`kernel_mean`: Gaussian distance weights and the weighted
  mean of a per-city quantity, as in PstarAlu's 300 km convention.

Everything is computed from one fold's ``train`` (years up to the cut-off).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.climate import annual_to_long, baseline_forecast
from proto_star.forecasters import ForecasterSpec
from proto_star.neighbors import (
    city_coordinates,
    departures,
    distance_matrix_km,
    gaussian_kernel,
    metric_panel,
    neighbor_weights,
    own_anomalies,
)

KEY = ["city_id", "year", "metric"]


def thirty_year_rows(
    train: pd.DataFrame, cutoff_year: int, forecast_years: list[int], metric: str
) -> pd.DataFrame:
    """The official 30-year-mean forecast of ``metric`` (``city_id, year, metric, value``)."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    rows = baseline_forecast(
        history, cutoff_year=cutoff_year, forecast_years=forecast_years, method="thirty_year_mean"
    )
    return rows.loc[rows["metric"] == metric].reset_index(drop=True)


def kernel_matrix(train: pd.DataFrame, bandwidth_km: float, *, include_self: bool) -> pd.DataFrame:
    """City x city raw Gaussian weights ``exp(-0.5 (d / bandwidth)^2)`` (not normalized)."""
    distances = distance_matrix_km(city_coordinates(train))
    weights = gaussian_kernel(distances, bandwidth_km)
    if not include_self:
        np.fill_diagonal(weights, 0.0)
    return pd.DataFrame(weights, index=distances.index, columns=distances.columns)


def kernel_mean(values: pd.Series, weights: pd.DataFrame) -> pd.Series:
    """Per city, the ``weights``-weighted mean of ``values`` over cities where it is finite."""
    x = values.reindex(weights.columns).to_numpy(dtype=float)
    present = np.isfinite(x)
    w = weights.to_numpy(dtype=float)
    numerator = w @ np.where(present, x, 0.0)
    denominator = w @ present.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(denominator > 0, numerator / denominator, np.nan)
    return pd.Series(mean, index=weights.index)


def neighbor_nudge(
    train: pd.DataFrame,
    cutoff_year: int,
    metric: str,
    *,
    k: int,
    recent_years: int,
    window: int,
    min_years: int,
    kind: Literal["difference", "ratio"],
) -> pd.Series:
    """Each city's mean departure from its ``k`` nearest cities over the last ``recent_years``.

    A departure is the city's anomaly minus the equal-weight mean anomaly of its ``k`` nearest
    cities with data that year; each anomaly is against the city's own ``window``-year mean
    (``kind`` "ratio" for precipitation). Cities without an anomaly, or without a departure in
    the recent years, get 0 (no nudge).
    """
    panel = metric_panel(train, metric, cutoff_year)
    anomalies = own_anomalies(panel, cutoff_year, window=window, min_years=min_years, kind=kind)
    weights = neighbor_weights(city_coordinates(train), k=k)
    departure = departures(anomalies, weights)
    recent = [year for year in departure.columns if int(year) > cutoff_year - recent_years]
    return departure[recent].mean(axis=1).fillna(0.0)


class NudgeSpec(ForecasterSpec):
    """Settings of Tatakae's neighbor nudge (defaults are theirs)."""

    k: int = Field(default=31, ge=1)
    recent_years: int = Field(default=10, ge=1)
    fraction: float = Field(default=0.3, ge=0.0, le=1.0)
    window: int = Field(default=30, ge=1)
    min_years: int = Field(default=10, ge=1)

    def describe(self) -> str:
        return (
            f"{self.window}-year mean nudged by {self.fraction:g} x the city's mean departure "
            f"over the last {self.recent_years} years from its {self.k} nearest cities "
            "(Tatakae)"
        )
