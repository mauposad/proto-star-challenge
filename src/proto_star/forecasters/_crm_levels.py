"""Flat levels for precipitation and hottest day in the Coupled Regional Model (plan 5.5).

Both start from the organizers' 30-calendar-year window and change it only for some cities:

* ``segment``: the mean of valid years from the city's current station segment, if at least
  ``min_years`` of them fall in the window; otherwise the 30-year mean.
* ``regional_eb``: fill the city's missing window years with its region's anomaly, then combine
  that anomaly-adjusted mean with the raw mean by empirical-Bayes weights. With every year
  present both estimates are the same number, so only cities with gaps change.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from proto_star.climate import BASELINE_WINDOW_YEARS


def _window(history: pd.DataFrame, metric: str, cutoff_year: int) -> pd.DataFrame:
    rows = history.loc[(history["metric"] == metric) & (history["year"] <= cutoff_year)]
    return rows.loc[rows["year"] > cutoff_year - BASELINE_WINDOW_YEARS]


def segment_levels(
    history: pd.DataFrame,
    segments: pd.DataFrame,
    metric: str,
    cutoff_year: int,
    min_years: int,
) -> pd.Series:
    """Mean of window years on each city's current station segment, where enough remain.

    ``segments`` has ``city_id``, ``year`` and ``segment``. Cities without enough current
    segment years are left out, so the caller keeps their 30-year mean.
    """
    rows = _window(history, metric, cutoff_year).merge(segments, on=["city_id", "year"])
    if rows.empty:
        return pd.Series(dtype=float)
    current = segments.sort_values("year").groupby("city_id")["segment"].last()
    rows = rows.loc[rows["segment"].to_numpy() == rows["city_id"].map(current).to_numpy()]
    counts = rows.groupby("city_id")["actual_value"].size()
    means = rows.groupby("city_id")["actual_value"].mean()
    return means.loc[counts >= min_years]


def regional_eb_levels(
    history: pd.DataFrame,
    city_region: pd.Series,
    metric: str,
    cutoff_year: int,
    iterations: int = 25,
) -> pd.Series:
    """Empirical-Bayes blend of each city's raw window mean and its anomaly-adjusted mean.

    The adjusted mean comes from a two-way fit ``value = city level + region-year anomaly``,
    with each region's anomalies averaging zero over the window years, so it estimates the mean
    a city would have had with no missing years. A city with every year keeps its raw mean.
    Weights: raw gets ``s_res^2 / (s_res^2 + s_reg^2)``, where ``s_res`` is the spread of the
    city's values after removing the regional anomaly and ``s_reg`` the spread of that anomaly
    over the window: the more a region swings, the more a gappy raw mean can be off.
    """
    rows = _window(history, metric, cutoff_year).copy()
    rows["region"] = rows["city_id"].map(city_region)
    rows = rows.dropna(subset=["region"])
    if rows.empty:
        return pd.Series(dtype=float)
    anomaly = pd.Series(0.0, index=rows.index)
    level = rows.groupby("city_id")["actual_value"].transform("mean")
    for _ in range(iterations):
        level = (rows["actual_value"] - anomaly).groupby(rows["city_id"]).transform("mean")
        year_effect = (rows["actual_value"] - level).groupby([rows["region"], rows["year"]]).mean()
        year_effect = year_effect - year_effect.groupby(level="region").transform("mean")
        index = pd.MultiIndex.from_frame(rows[["region", "year"]])
        anomaly = pd.Series(year_effect.reindex(index).to_numpy(), index=rows.index)
    by_city = rows.groupby("city_id")
    raw = by_city["actual_value"].mean()
    adjusted = level.groupby(rows["city_id"]).first()
    s_reg = by_city["region"].first().map(year_effect.groupby(level="region").var())
    s_res = (rows["actual_value"] - anomaly).groupby(rows["city_id"]).var()
    weight = (s_res / (s_reg + s_res)).where((s_reg + s_res) > 0).fillna(1.0)
    blended = weight * raw + (1.0 - weight) * adjusted
    return blended.loc[np.isfinite(blended)]
