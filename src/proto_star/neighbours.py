"""Neighbour-anchored levels: hypothesis H1 in ``hypotheses.md``, scoped by the methodologist.

For each city and metric, the 30-year mean is moved toward an anchored value ``a``:

    forecast = m30 + B * (a - m30),   B = clip(mean(v) / mean((m30 - a)^2), 0, 1)

``v`` is the sampling variance of the 30-year mean (``s^2 / n30``).  ``B`` is pooled per metric
and fitted on the fold's rows.  ``a`` depends on the arm:

* ``anchored`` (primary): the city's mean offset from its neighbours' anomaly, over its current
  station segment, put back on the neighbours' 30-year window.  Neighbours are the ``k``
  nearest cities within ``radius_km`` that have at least ``min_neighbour_years`` valid years in
  the 30-year window.  Anomalies are relative to each neighbour's own 30-year mean; precipitation
  uses ratios, the other metrics differences.
* ``own_segment``: the city's own mean over its current segment, with no neighbours (rival (b):
  a longer window).
* ``all_cities``: as ``anchored``, but every other eligible city is a neighbour.
* ``placebo``: as ``anchored``, but with ``k`` random cities more than ``placebo_min_km`` away,
  drawn with ``seed``.

Every quantity, the current segment included, is computed from the fold's training rows.
Cities with fewer than ``min_offset_years`` usable years keep the base forecast.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.climate import BASELINE_WINDOW_YEARS, METRICS, annual_to_long
from proto_star.utils.logging import get_logger

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
RATIO_METRICS = frozenset({"total_precip_in"})
EARTH_RADIUS_KM = 6371.0
log = get_logger(__name__)


class NeighbourSpec(BaseModel):
    """Settings of one H1 arm, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    arm: Literal["anchored", "own_segment", "all_cities", "placebo"]
    metrics: list[str] = Field(default_factory=lambda: ["total_precip_in", "hottest_day_temp"])
    k: int = Field(default=5, ge=1)
    radius_km: float = Field(default=500.0, gt=0)
    placebo_min_km: float = Field(default=1500.0, gt=0)
    min_neighbour_years: int = Field(default=20, ge=1)
    min_offset_years: int = Field(default=10, ge=2)
    seed: int = 0

    @model_validator(mode="after")
    def _check_metrics(self) -> NeighbourSpec:
        if not self.metrics or not set(self.metrics) <= set(METRICS):
            raise ValueError(f"metrics must be a non-empty subset of {list(METRICS)}")
        return self


def _distances(coords: np.ndarray) -> np.ndarray:
    """Great-circle distances in km between every pair of (lat, lon) rows."""
    lat, lon = np.radians(coords[:, 0]), np.radians(coords[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    h = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))


def _neighbour_sets(
    spec: NeighbourSpec, distances: np.ndarray, eligible: np.ndarray
) -> list[np.ndarray]:
    rng = np.random.default_rng(spec.seed)
    sets = []
    for i in range(len(distances)):
        candidates = np.flatnonzero(eligible & (np.arange(len(distances)) != i))
        if spec.arm == "all_cities":
            sets.append(candidates)
        elif spec.arm == "placebo":
            far = candidates[distances[i, candidates] > spec.placebo_min_km]
            sets.append(rng.choice(far, size=min(spec.k, len(far)), replace=False))
        else:
            near = candidates[distances[i, candidates] <= spec.radius_km]
            sets.append(near[np.argsort(distances[i, near])][: spec.k])
    return sets


def _anchored_values(
    grid: np.ndarray,
    in_segment: np.ndarray,
    window: np.ndarray,
    spec: NeighbourSpec,
    distances: np.ndarray,
    ratio: bool,
) -> np.ndarray:
    """The anchored value ``a`` for every city (NaN where it cannot be formed)."""
    m30 = np.nanmean(np.where(window[:, None], grid, np.nan), axis=0)
    n30 = (~np.isnan(grid) & window[:, None]).sum(axis=0)
    own = np.where(in_segment, grid, np.nan)
    if spec.arm == "own_segment":
        usable = (~np.isnan(own)).sum(axis=0)
        return np.where(usable >= spec.min_offset_years, np.nanmean(own, axis=0), np.nan)
    anomaly = grid / m30 if ratio else grid - m30
    sets = _neighbour_sets(spec, distances, n30 >= spec.min_neighbour_years)
    values = np.full(grid.shape[1], np.nan)
    for i, members in enumerate(sets):
        if len(members) == 0:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN years: no neighbour data
            common = np.nanmean(anomaly[:, members], axis=1)
        offsets = own[:, i] / common if ratio else own[:, i] - common
        usable = np.isfinite(offsets)
        if usable.sum() < spec.min_offset_years:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            level = float(np.nanmean(common[window]))
        offset = float(offsets[usable].mean())
        values[i] = offset * level if ratio else offset + level
    return values


def neighbour_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: NeighbourSpec,
) -> pd.DataFrame:
    """The base forecast with ``spec.metrics`` replaced by the H1 level for one arm."""
    with warnings.catch_warnings():
        # Cities with no valid year in a window give empty-slice warnings; they are skipped.
        warnings.simplefilter("ignore", RuntimeWarning)
        return _neighbour_forecast(base, train, cutoff_year, forecast_years, spec)


def _neighbour_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: NeighbourSpec,
) -> pd.DataFrame:
    history = annual_to_long(train, cutoff_year=cutoff_year)
    cities = np.array(sorted(history["city_id"].unique()))
    years = np.arange(int(history["year"].min()), cutoff_year + 1)
    window = years > cutoff_year - BASELINE_WINDOW_YEARS
    keyed = train.assign(city_id=train["ID"].astype(str))
    coords = keyed.groupby("city_id")[["Lat", "Lon"]].first().reindex(cities).to_numpy(float)
    distances = _distances(coords)
    segments = keyed.pivot_table(index="Year", columns="city_id", values="Station Segment")
    segments = segments.reindex(index=years, columns=cities)

    forecast = base(train, cutoff_year, forecast_years).copy()
    for metric in spec.metrics:
        rows = history.loc[history["metric"] == metric]
        grid = (
            rows.pivot_table(index="year", columns="city_id", values="actual_value")
            .reindex(index=years, columns=cities)
            .to_numpy(float)
        )
        observed = ~np.isnan(grid)
        last = np.where(observed, years[:, None], -1).max(axis=0)
        seg = segments.to_numpy(float)
        current = np.array([seg[years == y, i][0] if y > 0 else np.nan for i, y in enumerate(last)])
        in_segment = observed & (seg == current[None, :])
        ratio = metric in RATIO_METRICS
        anchored = _anchored_values(grid, in_segment, window, spec, distances, ratio)

        in_window = np.where(window[:, None], grid, np.nan)
        m30 = np.nanmean(in_window, axis=0)
        n30 = (~np.isnan(in_window)).sum(axis=0)
        variance = np.nanvar(in_window, axis=0, ddof=1) / np.maximum(n30, 1)
        usable = np.isfinite(anchored) & np.isfinite(m30) & (n30 > 1)
        gap = float(((m30 - anchored)[usable] ** 2).mean()) if usable.any() else 0.0
        weight = float(np.clip(variance[usable].mean() / gap, 0.0, 1.0)) if gap > 0 else 0.0
        log.info(
            "neighbours %s %s at cutoff %d: B=%.3f over %d cities",
            spec.arm,
            metric,
            cutoff_year,
            weight,
            int(usable.sum()),
        )
        level = pd.Series(np.where(usable, m30 + weight * (anchored - m30), np.nan), index=cities)
        is_metric = forecast["metric"] == metric
        derived = level.reindex(forecast.loc[is_metric, "city_id"]).to_numpy()
        values = forecast.loc[is_metric, "predicted_value"].to_numpy()
        forecast.loc[is_metric, "predicted_value"] = np.where(np.isfinite(derived), derived, values)
    return forecast
