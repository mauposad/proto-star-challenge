"""Station-segment levels and pairwise neighbor step adjustment: paper P15 (Menne & Williams 2009).

Each city's record is stitched from several weather stations (``Station Segment`` in the
master table).  A station move can shift a series by a constant step that is not climate.
The ``current_best`` levels (10-year mean for temperature/CDD, 30-year mean for
precipitation/hottest day) average across such a step when a switch falls inside the window.
Two fixes are offered:

``mode="segment"``
    Average only the years of the station segment in use at the cut-off, with the same
    window rule as ``current_best`` (so the segment is capped at the window length).  If the
    segment has fewer than ``min_years`` valid years in the window, use the unrestricted
    ``current_best`` level.

``mode="adjusted"``
    The pairwise idea of P15.  At each segment boundary that affects the averaging window,
    the step is the change in the city-minus-neighbors difference series across the boundary.
    Neighbors are the ``n_neighbors`` nearest cities (great-circle distance, within
    ``max_km``) with no segment boundary of their own in the ``side_years`` before or after it.
    The earlier years are shifted by the step, latest boundary first, and the usual window
    mean is taken on the adjusted series.

Everything is computed from the fold's ``train`` frame, so neighbors also only contribute
years up to the cut-off.  Metrics outside ``metrics`` come from ``base_forecaster``
(``current_best`` by default, or any registered forecaster with ``base_params``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST, CURRENT_BEST_METHODS, Forecaster, resolve_forecaster
from proto_star.climate import BASELINE_WINDOW_YEARS, METRICS
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters.registry import register_forecaster

MODES = ("segment", "adjusted")
NON_NEGATIVE = frozenset({"total_precip_in", "cdd"})
SEGMENT_COLUMN = "Station Segment"
CHANGES_COLUMN = "Station Changes"
EARTH_RADIUS_KM = 6371.0
_KEY = ["city_id", "year", "metric"]
# Window length per metric, matching current_best: last N valid years, or 30 calendar years.
DEFAULT_WINDOWS = {
    metric: (BASELINE_WINDOW_YEARS if method == "thirty_year_mean" else 10)
    for metric, method in CURRENT_BEST_METHODS.items()
}


@dataclass(frozen=True)
class StepParams:
    """Settings of the pairwise step estimate."""

    n_neighbors: int = 5
    side_years: int = 5
    min_side_years: int = 3
    min_neighbors: int = 2
    max_km: float = 1000.0
    min_t: float = 0.0


def station_panels(train: pd.DataFrame, cutoff_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """City x calendar-year panels of the station segment in use and of switch counts.

    Without station columns (synthetic data) every city is one segment with no switches.
    Gaps in the segment are filled forward then backward, since a missing year has no station.
    """
    cities = sorted(train["ID"].astype(str).unique())
    first = int(train["Year"].min())
    years = pd.RangeIndex(first, cutoff_year + 1, name="year")
    frame = train.assign(city_id=train["ID"].astype(str))
    if SEGMENT_COLUMN not in frame.columns:
        ones = pd.DataFrame(1.0, index=cities, columns=years)
        return ones, ones * 0.0
    segment = frame.pivot_table(
        index="city_id", columns="Year", values=SEGMENT_COLUMN, aggfunc="first"
    ).reindex(index=cities, columns=years)
    segment = segment.ffill(axis=1).bfill(axis=1).fillna(1.0)
    if CHANGES_COLUMN in frame.columns:
        changes = frame.pivot_table(
            index="city_id", columns="Year", values=CHANGES_COLUMN, aggfunc="first"
        ).reindex(index=cities, columns=years)
        changes = changes.fillna(0.0)
    else:
        changes = segment * 0.0
    return segment.astype(float), changes.astype(float)


def boundaries(segment_row: pd.Series) -> list[int]:
    """First years of each new station segment (the segment differs from the year before)."""
    values = segment_row.to_numpy(dtype=float)
    years = segment_row.index.to_numpy(dtype=int)
    changed = np.flatnonzero(values[1:] != values[:-1]) + 1
    return [int(years[i]) for i in changed]


def window_years(series: pd.Series, metric: str, window: int, cutoff_year: int) -> pd.Series:
    """The valid values ``current_best`` would average for ``metric`` (year-indexed).

    Last ``window`` valid years for 10-year-mean metrics; for 30-year-mean metrics the
    valid years in the last ``window`` calendar years, or the last ``window`` valid ones if
    that is empty (the same rule as ``proto_star.climate``).
    """
    valid = series.dropna()
    if CURRENT_BEST_METHODS[metric] == "thirty_year_mean":
        recent = valid.loc[valid.index > cutoff_year - window]
        return recent if not recent.empty else valid.tail(window)
    return valid.tail(window)


def city_distances(train: pd.DataFrame) -> pd.DataFrame:
    """Great-circle distance in km between every pair of cities in ``train``."""
    coords = (
        train.assign(city_id=train["ID"].astype(str))
        .groupby("city_id")[["Lat", "Lon"]]
        .first()
        .sort_index()
    )
    lat = np.radians(coords["Lat"].to_numpy(dtype=float))
    lon = np.radians(coords["Lon"].to_numpy(dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    h = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    km = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))
    return pd.DataFrame(km, index=coords.index, columns=coords.index)


def _neighbor_reference(
    panel: pd.DataFrame,
    span: list[int],
    candidates: list[str],
    params: StepParams,
) -> tuple[pd.Series, int]:
    """Mean neighbor anomaly per year over ``span`` and the number of neighbors used."""
    used: list[pd.Series] = []
    for other in candidates:
        values = pd.Series(panel.loc[other, span], dtype=float)
        if values.notna().sum() < 2 * params.min_side_years:
            continue
        used.append(values - values.mean())
        if len(used) == params.n_neighbors:
            break
    if not used:
        return pd.Series(np.nan, index=span), 0
    return pd.concat(used, axis=1).mean(axis=1), len(used)


def estimate_steps(
    panel: pd.DataFrame,
    segment: pd.DataFrame,
    changes: pd.DataFrame,
    distances: pd.DataFrame,
    *,
    metric: str,
    window: int,
    cutoff_year: int,
    params: StepParams,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Adjust each city's ``panel`` row for station steps inside its averaging window.

    Returns the adjusted panel and one row per boundary examined: ``city_id, boundary,
    step, t_stat, n_neighbors, applied``.  Boundaries are handled latest first, so the
    years before an earlier boundary carry the sum of the later steps (the current station
    is the reference frame, as in P15).  Years with a recorded switch are mixed and are left
    out of the step estimate.
    """
    adjusted = panel.copy()
    city_bounds = {city: boundaries(segment.loc[city]) for city in segment.index}
    records: list[dict[str, Any]] = []
    for city in panel.index:
        series = panel.loc[city]
        in_window = window_years(series, metric, window, cutoff_year)
        if in_window.empty:
            continue
        start = int(in_window.index.min())
        bounds = city_bounds.get(city, [])
        relevant = [b for b in bounds if b > start]
        for b in sorted(relevant, reverse=True):
            earlier = [x for x in bounds if x < b]
            lo = max(b - params.side_years, earlier[-1] if earlier else -(10**6))
            before = [y for y in range(lo, b) if y in panel.columns]
            after = [y for y in range(b, min(b + params.side_years, cutoff_year + 1))]
            span = before + after
            near = distances.loc[city].drop(city).sort_values()
            near = near.loc[near <= params.max_km]
            quiet = [
                other
                for other in near.index
                if not any(span[0] <= x <= span[-1] for x in city_bounds.get(other, []))
            ]
            reference, n_used = _neighbor_reference(panel, span, quiet, params)
            diff = adjusted.loc[city, span] - reference
            mixed = changes.loc[city, span] > 0
            diff = diff.loc[~mixed.to_numpy()].dropna()
            d_before = diff.loc[diff.index < b]
            d_after = diff.loc[diff.index >= b]
            record: dict[str, Any] = {
                "city_id": city,
                "boundary": b,
                "step": np.nan,
                "t_stat": np.nan,
                "n_neighbors": n_used,
                "applied": False,
            }
            enough = (
                n_used >= params.min_neighbors
                and len(d_before) >= params.min_side_years
                and len(d_after) >= params.min_side_years
            )
            if enough:
                step = float(d_after.mean() - d_before.mean())
                se = float(
                    np.sqrt(
                        d_before.var(ddof=1) / len(d_before) + d_after.var(ddof=1) / len(d_after)
                    )
                )
                t_stat = abs(step) / se if se > 0 else np.inf
                record.update(step=step, t_stat=t_stat)
                if t_stat >= params.min_t:
                    earlier_years = [y for y in adjusted.columns if int(y) < b]
                    adjusted.loc[city, earlier_years] = adjusted.loc[city, earlier_years] + step
                    record["applied"] = True
            records.append(record)
    columns = ["city_id", "boundary", "step", "t_stat", "n_neighbors", "applied"]
    return adjusted, pd.DataFrame(records, columns=columns)


def segment_level(
    series: pd.Series,
    segment_row: pd.Series,
    *,
    metric: str,
    window: int,
    cutoff_year: int,
    min_years: int,
) -> float:
    """Window mean over the current station segment only; NaN if it is too short."""
    current = segment_row.iloc[-1]
    in_segment = series.where(segment_row == current)
    values = window_years(in_segment, metric, window, cutoff_year)
    if CURRENT_BEST_METHODS[metric] == "thirty_year_mean":
        values = values.loc[values.index > cutoff_year - window]
    if len(values) < min_years:
        return float("nan")
    return float(values.mean())


def make_station_p15(
    *,
    mode: str = "adjusted",
    metrics: Sequence[str] = ("annual_avg_temp", "cdd"),
    windows: Mapping[str, int] | None = None,
    min_years: int = 5,
    n_neighbors: int = 5,
    side_years: int = 5,
    min_side_years: int = 3,
    min_neighbors: int = 2,
    max_km: float = 1000.0,
    min_t: float = 0.0,
    base_forecaster: str = CURRENT_BEST,
    base_params: Mapping[str, Any] | None = None,
) -> Forecaster:
    """Build the P15 station forecaster with hyperparameters from the trial config.

    ``windows`` overrides the per-metric window length (the cap on the segment), defaults
    10 for temperature/CDD and 30 for precipitation/hottest day.  ``base_forecaster`` with
    ``base_params`` supplies metrics outside ``metrics`` and any series this method leaves
    alone.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; use one of {list(MODES)}")
    unknown = sorted(set(metrics) - set(METRICS))
    if unknown:
        raise ValueError(f"metrics has unknown metrics {unknown}; use {list(METRICS)}")
    window_by_metric = {**DEFAULT_WINDOWS, **dict(windows or {})}
    bad = sorted(set(window_by_metric) - set(METRICS))
    if bad or any(int(w) < 1 for w in window_by_metric.values()):
        raise ValueError(f"windows must map metrics in {list(METRICS)} to positive lengths")
    if min_years < 1 or n_neighbors < 1 or side_years < 1 or min_side_years < 2:
        raise ValueError("min_years, n_neighbors, side_years >= 1 and min_side_years >= 2")
    if min_side_years > side_years:
        raise ValueError("min_side_years cannot exceed side_years")
    step_params = StepParams(
        n_neighbors=n_neighbors,
        side_years=side_years,
        min_side_years=min_side_years,
        min_neighbors=min_neighbors,
        max_km=max_km,
        min_t=min_t,
    )
    if base_forecaster == CURRENT_BEST:
        base = resolve_forecaster(CURRENT_BEST)
    else:
        spec = {"base": {"forecaster": base_forecaster, "params": dict(base_params or {})}}
        base = resolve_forecaster("base", variants=spec)
    modelled = [m for m in METRICS if m in set(metrics)]

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        result = base(train, cutoff_year, forecast_years)
        panels = feats.wide_panels(train, cutoff_year)
        segment, changes = station_panels(train, cutoff_year)
        distances = city_distances(train) if mode == "adjusted" else None
        levels: list[pd.DataFrame] = []
        for metric in modelled:
            if metric not in panels:
                continue
            panel = panels[metric].reindex(columns=segment.columns)
            window = int(window_by_metric[metric])
            if mode == "adjusted":
                assert distances is not None
                adjusted, _ = estimate_steps(
                    panel,
                    segment,
                    changes,
                    distances,
                    metric=metric,
                    window=window,
                    cutoff_year=cutoff_year,
                    params=step_params,
                )
                values = {
                    city: window_years(adjusted.loc[city], metric, window, cutoff_year).mean()
                    for city in adjusted.index
                }
            else:
                values = {
                    city: segment_level(
                        panel.loc[city],
                        segment.loc[city],
                        metric=metric,
                        window=window,
                        cutoff_year=cutoff_year,
                        min_years=min_years,
                    )
                    for city in panel.index
                }
            level = pd.Series(values, dtype=float).dropna()
            if metric in NON_NEGATIVE:
                level = level.clip(lower=0.0)
            levels.append(
                pd.DataFrame({"city_id": level.index, "metric": metric, "level": level.to_numpy()})
            )
        if not levels:
            return result
        model = pd.concat(levels, ignore_index=True)
        merged = result.merge(model, on=["city_id", "metric"], how="left")
        use = merged["level"].notna() & np.isfinite(merged["level"])
        merged.loc[use, "predicted_value"] = merged.loc[use, "level"]
        return merged[[*_KEY, "predicted_value"]]

    return forecast


register_forecaster(
    "station_p15",
    description=(
        "P15: level from the current station segment only (mode=segment), or window mean "
        "after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); "
        "base_forecaster for the other metrics"
    ),
)(make_station_p15)
