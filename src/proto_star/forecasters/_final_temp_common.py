"""Shared pieces of the final-round temperature components (agent T).

Everything here works on one fold's ``train`` and ignores years after the cut-off. Panels
are city x year tables of valid annual temperature (``proto_star.neighbors.metric_panel``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from proto_star.backtest import pooled_trend_forecaster
from proto_star.neighbors import city_coordinates, metric_panel, neighbor_weights
from proto_star.trend import TEMPERATURE, PooledTrendSpec

_KEY = ["city_id", "year", "metric"]


def temperature_panel(train: pd.DataFrame, cutoff_year: int) -> pd.DataFrame:
    """City x year panel of valid annual temperature up to the cut-off."""
    return metric_panel(train.loc[train["Year"] <= cutoff_year], TEMPERATURE, cutoff_year)


def nearest_with_self(coords: pd.DataFrame, n_cities: int) -> pd.DataFrame:
    """Equal weights over the city itself and its ``n_cities - 1`` nearest other cities."""
    if n_cities < 1:
        raise ValueError(f"n_cities must be at least 1, got {n_cities}")
    k = min(n_cities - 1, len(coords) - 1)
    identity = pd.DataFrame(np.eye(len(coords)), index=coords.index, columns=coords.index)
    if k < 1:
        return identity
    neighbors = neighbor_weights(coords, k=k) * k  # 1 per kept neighbor
    return (neighbors + identity) / (k + 1)


def last_valid_level(panel: pd.DataFrame, years: int) -> pd.DataFrame:
    """Mean of each city's last ``years`` valid values (``level``) and their mean year."""
    rows = {}
    for city, series in panel.iterrows():
        valid = series.dropna().tail(years)
        if valid.empty:
            rows[city] = (np.nan, np.nan)
        else:
            rows[city] = (float(valid.mean()), float(np.mean(valid.index.astype(float))))
    return pd.DataFrame.from_dict(rows, orient="index", columns=["level", "center"])


def window_columns(panel: pd.DataFrame, first_year: int, last_year: int) -> pd.DataFrame:
    """The panel's columns from ``first_year`` to ``last_year`` (inclusive)."""
    return panel[[y for y in panel.columns if first_year <= int(y) <= last_year]]


def ols_slopes(values: pd.DataFrame, x: pd.Series | None = None, *, min_years: int) -> pd.DataFrame:
    """Per-row OLS slope of ``values`` on ``x`` (default: the year), with its standard error.

    Only finite cells count. Rows with fewer than ``min_years`` of them get NaN.
    """
    xs = (
        pd.Series(values.columns.astype(float), index=values.columns)
        if x is None
        else x.reindex(values.columns).astype(float)
    )
    out = {}
    for row, series in values.iterrows():
        mask = series.notna().to_numpy() & xs.notna().to_numpy()
        n = int(mask.sum())
        if n < max(min_years, 3):
            out[row] = (np.nan, np.nan)
            continue
        xv = xs.to_numpy()[mask]
        yv = series.to_numpy(dtype=float)[mask]
        dx = xv - xv.mean()
        sxx = float((dx**2).sum())
        if sxx == 0.0:
            out[row] = (np.nan, np.nan)
            continue
        slope = float((dx * (yv - yv.mean())).sum()) / sxx
        residual = yv - yv.mean() - slope * dx
        se = float(np.sqrt((residual**2).sum() / (n - 2) / sxx))
        out[row] = (slope, se)
    return pd.DataFrame.from_dict(out, orient="index", columns=["slope", "se"])


def pooled_trend_temperature(
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    *,
    level_years: list[int] | None = None,
    trend_window: int = 40,
) -> pd.DataFrame:
    """City x year pooled-trend temperature (the champion's trend member, lead_blend's trend)."""
    spec = PooledTrendSpec(
        level_years=level_years or [10, 15], trend_window=trend_window, cdd_sensitivity=True
    )
    forecast = pooled_trend_forecaster(spec)(train, cutoff_year, forecast_years)
    rows = forecast.loc[forecast["metric"] == TEMPERATURE]
    return rows.pivot_table(index="city_id", columns="year", values="predicted_value")


def to_long(values: pd.DataFrame) -> pd.DataFrame:
    """City x year table to forecast rows ``city_id, year, metric, predicted_value``."""
    frame = values.rename_axis(index="city_id", columns="year").reset_index()
    frame = frame.melt(id_vars="city_id", var_name="year", value_name="predicted_value")
    frame = frame.dropna(subset=["predicted_value"])
    frame["city_id"] = frame["city_id"].astype(str)
    frame["year"] = frame["year"].astype(int)
    frame["metric"] = TEMPERATURE
    return frame[[*_KEY, "predicted_value"]]


def with_fallback(values: pd.DataFrame, fallback: pd.DataFrame) -> pd.DataFrame:
    """Fill cells ``values`` cannot forecast from ``fallback`` (same layout)."""
    aligned = values.reindex(index=fallback.index, columns=fallback.columns)
    return aligned.where(aligned.notna(), fallback)


def coordinates(train: pd.DataFrame) -> pd.DataFrame:
    """City coordinates of the fold (``proto_star.neighbors.city_coordinates``)."""
    return city_coordinates(train)
