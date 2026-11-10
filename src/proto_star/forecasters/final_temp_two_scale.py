"""PstarAlu's two-scale departure decay for temperature, re-implemented (final round, T3).

Source: Nibedita Biswal (@nbiswal-star), "PstarAlu: climate forecasts for 210 U.S. cities",
Hugging Face dataset ``nbiswal-star/protostar-climate-submission`` (CC BY 4.0), README at
commit ``9e51c3ef5d3178ca194f28e2c4134201c1bf9675``, sections "Method / Average temperature"
and "Validation". Only the README text was read; no code was copied or downloaded. The
README does not define the area weights or the bias correction; our choices (fixed before
running) are in ``docs/trials/final_temp.md``.

Kind ``final_temp_two_scale``:

1. Base: the pooled-trend temperature (levels 10/15, non-negative pooled 40-year slope).
2. Anomaly ``a`` = value - city mean of the 30 years ending at the cut-off. National pattern
   ``n(t)`` = area-weighted median of ``a`` over cities. Departure ``d = a - n``.
3. Area weights: inverse local density, ``w_c = 1 / #cities within radius_km`` (city
   included), normalized. Regional part ``R`` = area-weighted mean of ``d`` over the cities
   within ``radius_km`` (city included); local part ``L = d - R``.
4. Each part's persistence: pooled lag-1 OLS of the city-demeaned part over the 30-year
   window, bias-corrected (Kendall 1954: ``phi + (1 + 3 phi) / n``), clipped to [0, 0.99].
5. The part's value in the city's last valid year ``T``, minus its mean over the years the
   base level uses, decays as ``phi^(year - T)`` and is added to the base.

Produces ``annual_avg_temp`` rows only; use it through ``swap_metric``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._final_temp_common import (
    coordinates,
    pooled_trend_temperature,
    temperature_panel,
    to_long,
    window_columns,
)
from proto_star.neighbors import distance_matrix_km, neighbor_mean, own_anomalies

MAX_PERSISTENCE = 0.99


class TwoScaleSpec(ForecasterSpec):
    """T3 settings. Defaults are the pre-registered ones."""

    anomaly_window: int = Field(default=30, ge=10)
    min_years: int = Field(default=10, ge=3)
    radius_km: float = Field(default=300.0, gt=0.0)
    level_years: list[int] = Field(default=[10, 15], min_length=1)
    trend_window: int = Field(default=40, ge=10)

    def describe(self) -> str:
        return (
            f"PstarAlu two-scale: pooled-trend temperature (levels {self.level_years}, "
            f"{self.trend_window}-year slope) + regional (within {self.radius_km:g} km) and "
            "local recent departures from the area-weighted national median, each decaying "
            "by its own pooled bias-corrected AR(1)"
        )


def area_weights(coords: pd.DataFrame, radius_km: float) -> pd.Series:
    """Declustering weights: 1 / number of cities within ``radius_km`` (self included)."""
    within = distance_matrix_km(coords) <= radius_km
    weights = 1.0 / within.sum(axis=1).astype(float)
    return weights / weights.sum()


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Smallest value whose cumulative weight reaches half the total (finite values only)."""
    keep = np.isfinite(values) & (weights > 0)
    if not keep.any():
        return float("nan")
    order = np.argsort(values[keep], kind="mergesort")
    sorted_values = values[keep][order]
    cumulative = np.cumsum(weights[keep][order])
    return float(sorted_values[np.searchsorted(cumulative, 0.5 * cumulative[-1])])


def bias_corrected_ar1(part: pd.DataFrame) -> float:
    """Pooled lag-1 persistence of city-demeaned series, with Kendall's bias correction."""
    demeaned = part.sub(part.mean(axis=1), axis=0).to_numpy(dtype=float)
    lagged, current = demeaned[:, :-1], demeaned[:, 1:]
    pairs = np.isfinite(lagged) & np.isfinite(current)
    denominator = float(np.where(pairs, lagged**2, 0.0).sum())
    if denominator == 0.0:
        return 0.0
    raw = float(np.where(pairs, lagged * current, 0.0).sum()) / denominator
    counts = np.isfinite(demeaned).sum(axis=1)
    n = float(counts[counts > 1].mean()) if (counts > 1).any() else 0.0
    if n <= 0.0:
        return 0.0
    return float(np.clip(raw + (1.0 + 3.0 * raw) / n, 0.0, MAX_PERSISTENCE))


def recent_excess(part: pd.DataFrame, level_years: list[int]) -> pd.DataFrame:
    """Per city: last valid year ``T`` and the part's value then minus its level-window mean."""
    rows = {}
    for city, series in part.iterrows():
        valid = series.dropna()
        if valid.empty:
            rows[city] = (np.nan, np.nan)
            continue
        level_mean = float(np.mean([valid.tail(n).mean() for n in level_years]))
        rows[city] = (float(valid.index[-1]), float(valid.iloc[-1]) - level_mean)
    return pd.DataFrame.from_dict(rows, orient="index", columns=["last_year", "excess"])


def two_scale_parts(
    train: pd.DataFrame, cutoff_year: int, spec: TwoScaleSpec
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Regional and local departure parts (city x year over the anomaly window)."""
    panel = temperature_panel(train, cutoff_year)
    window = window_columns(panel, cutoff_year - spec.anomaly_window + 1, cutoff_year)
    anomalies = own_anomalies(
        window, cutoff_year, window=spec.anomaly_window, min_years=spec.min_years
    )
    coords = coordinates(train).reindex(anomalies.index)
    weights = area_weights(coords, spec.radius_km)
    w = weights.to_numpy()
    national = pd.Series(
        [weighted_median(anomalies[year].to_numpy(dtype=float), w) for year in anomalies.columns],
        index=anomalies.columns,
    )
    departure = anomalies.sub(national, axis=1)
    within = (distance_matrix_km(coords) <= spec.radius_km).astype(float)
    regional_weights = within.mul(weights, axis=1)
    regional = neighbor_mean(departure, regional_weights).where(departure.notna())
    return regional, departure - regional


def build_two_scale(spec: TwoScaleSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = pooled_trend_temperature(
            train,
            cutoff_year,
            forecast_years,
            level_years=spec.level_years,
            trend_window=spec.trend_window,
        )
        years = np.asarray(forecast_years, dtype=float)
        total = base.copy()
        for part in two_scale_parts(train, cutoff_year, spec):
            phi = bias_corrected_ar1(part)
            excess = recent_excess(part, spec.level_years).reindex(base.index)
            lead = years[None, :] - excess["last_year"].to_numpy()[:, None]
            term = excess["excess"].to_numpy()[:, None] * phi**lead
            total += np.nan_to_num(term, nan=0.0)
        return to_long(total)

    return forecast


register_kind("final_temp_two_scale", TwoScaleSpec, build_two_scale)
