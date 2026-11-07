"""Torch-free helpers shared by the neural forecasters (P05 N-BEATS, P08 DeepAR).

The leading underscore keeps this module out of forecaster auto-discovery.

Every series is one (city, metric) pair of quality-screened annual values from
:func:`proto_star.climate.annual_to_long`.  Series are laid on a calendar-year grid that
ends at the fold's cut-off, with NaN for years that are missing or fail the missing-days
rule.  Windows are cut from that grid:

* inputs: the ``lookback`` calendar years ending at an origin year (the origin included)
* targets: the ``horizon`` years after the origin, masked where missing or after
  ``target_limit`` (the inner-validation boundary)

Each window is scaled by its own input level (mean of the observed inputs) and the series'
standard deviation over the training fold, so all cities share one model.  Nothing here
reads data after the cut-off: the grid is built from the fold's ``train`` frame only.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST_METHODS
from proto_star.climate import METRICS, annual_to_long, metric_ensemble_forecast

KEY = ["city_id", "year", "metric"]
# Series scale floor: a constant series would otherwise divide by zero.
MIN_SCALE = 1e-6


@dataclass(frozen=True)
class Panel:
    """All series of one fold on a shared calendar-year grid."""

    city_ids: np.ndarray  # (S,) str
    metrics: np.ndarray  # (S,) str
    metric_index: np.ndarray  # (S,) int, position in METRICS
    city_index: np.ndarray  # (S,) int, position in the sorted city list
    years: np.ndarray  # (T,) int, first observed year .. cutoff
    grid: np.ndarray  # (S, T) float, NaN where missing
    scale: np.ndarray  # (S,) float, std of observed values (train fold only)


@dataclass(frozen=True)
class Windows:
    """Scaled training or forecast windows.  Masks are 1.0 where a value is observed."""

    x: np.ndarray  # (N, L) scaled inputs, 0 where missing
    x_mask: np.ndarray  # (N, L)
    y: np.ndarray  # (N, H) scaled targets, 0 where missing or masked
    y_mask: np.ndarray  # (N, H)
    series: np.ndarray  # (N,) int, row in Panel
    level: np.ndarray  # (N,) window level in original units
    scale: np.ndarray  # (N,) series scale in original units

    def __len__(self) -> int:
        return len(self.series)


def build_panel(train: pd.DataFrame, cutoff_year: int, metrics: Sequence[str]) -> Panel:
    """Pivot the fold's training rows for ``metrics`` onto a calendar-year grid."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    history = history.loc[history["metric"].isin(list(metrics))]
    if history.empty:
        raise ValueError(f"no training history for metrics {list(metrics)}")
    years = np.arange(int(history["year"].min()), cutoff_year + 1)
    wide = history.pivot_table(
        index=["city_id", "metric"], columns="year", values="actual_value", aggfunc="first"
    ).reindex(columns=years)
    wide = wide.sort_index()
    values = wide.to_numpy(dtype=float)
    city_ids = wide.index.get_level_values("city_id").to_numpy(dtype=str)
    metric_names = wide.index.get_level_values("metric").to_numpy(dtype=str)
    all_cities = np.sort(np.unique(train["ID"].astype(str).to_numpy()))
    scale = np.nanstd(values, axis=1)
    scale = np.where(np.isfinite(scale) & (scale > MIN_SCALE), scale, 1.0)
    return Panel(
        city_ids=city_ids,
        metrics=metric_names,
        metric_index=np.array([METRICS.index(m) for m in metric_names], dtype=np.int64),
        city_index=np.searchsorted(all_cities, city_ids).astype(np.int64),
        years=years,
        grid=values,
        scale=scale,
    )


def make_windows(
    panel: Panel,
    *,
    lookback: int,
    horizon: int,
    min_obs: int,
    first_origin: int | None = None,
    last_origin: int | None = None,
    target_limit: int | None = None,
) -> Windows:
    """Cut every window whose origin year lies in ``[first_origin, last_origin]``.

    A window is kept if it has at least ``min_obs`` observed inputs and, when targets are
    wanted (``target_limit`` set), at least one observed target year ``<= target_limit``.
    With ``target_limit=None`` targets are all masked: that is the forecast case.
    """
    n_series, n_years = panel.grid.shape
    if n_years < lookback:
        return _empty_windows(lookback, horizon)
    padded = np.concatenate([panel.grid, np.full((n_series, horizon), np.nan)], axis=1)
    view = np.lib.stride_tricks.sliding_window_view(padded, lookback + horizon, axis=1)
    origins = panel.years[lookback - 1 :]  # origin year of window k
    keep_origin = np.ones(len(origins), dtype=bool)
    if first_origin is not None:
        keep_origin &= origins >= first_origin
    if last_origin is not None:
        keep_origin &= origins <= last_origin
    view = view[:, keep_origin, :]
    origins = origins[keep_origin]

    x = view[:, :, :lookback]
    y = view[:, :, lookback:].copy()
    target_years = origins[:, None] + np.arange(1, horizon + 1)[None, :]
    if target_limit is None:
        y[:] = np.nan
    else:
        y[:, target_years > target_limit] = np.nan
    x_ok = np.isfinite(x)
    y_ok = np.isfinite(y)
    keep = x_ok.sum(axis=2) >= min_obs
    if target_limit is not None:
        keep &= y_ok.any(axis=2)
    series_idx, window_idx = np.nonzero(keep)
    x, y = x[series_idx, window_idx], y[series_idx, window_idx]
    x_ok, y_ok = x_ok[series_idx, window_idx], y_ok[series_idx, window_idx]
    if len(series_idx) == 0:
        return _empty_windows(lookback, horizon)

    level = np.nanmean(x, axis=1)
    scale = panel.scale[series_idx]
    xs = np.where(x_ok, (x - level[:, None]) / scale[:, None], 0.0)
    ys = np.where(y_ok, (y - level[:, None]) / scale[:, None], 0.0)
    return Windows(
        x=xs.astype(np.float32),
        x_mask=x_ok.astype(np.float32),
        y=ys.astype(np.float32),
        y_mask=y_ok.astype(np.float32),
        series=series_idx.astype(np.int64),
        level=level,
        scale=scale,
    )


def _empty_windows(lookback: int, horizon: int) -> Windows:
    return Windows(
        x=np.zeros((0, lookback), dtype=np.float32),
        x_mask=np.zeros((0, lookback), dtype=np.float32),
        y=np.zeros((0, horizon), dtype=np.float32),
        y_mask=np.zeros((0, horizon), dtype=np.float32),
        series=np.zeros(0, dtype=np.int64),
        level=np.zeros(0),
        scale=np.zeros(0),
    )


def inner_split(
    panel: Panel, *, lookback: int, horizon: int, min_obs: int, cutoff_year: int, holdout: int
) -> tuple[Windows, Windows]:
    """Training and early-stopping windows, both inside the fold's training years.

    Validation windows forecast the last ``holdout`` years before the cut-off from the
    origin ``cutoff_year - holdout``.  Training windows only score targets up to that origin,
    so no validation target is ever a training target.
    """
    boundary = cutoff_year - holdout
    fit = make_windows(
        panel,
        lookback=lookback,
        horizon=horizon,
        min_obs=min_obs,
        last_origin=boundary - 1,
        target_limit=boundary,
    )
    valid = make_windows(
        panel,
        lookback=lookback,
        horizon=horizon,
        min_obs=min_obs,
        first_origin=boundary,
        last_origin=boundary,
        target_limit=cutoff_year,
    )
    return fit, valid


def forecast_windows(panel: Panel, *, lookback: int, horizon: int, min_obs: int) -> Windows:
    """One input window per series ending at the cut-off (series with too few inputs drop)."""
    last = int(panel.years[-1])
    return make_windows(
        panel,
        lookback=lookback,
        horizon=horizon,
        min_obs=min_obs,
        first_origin=last,
        last_origin=last,
    )


def to_frame(
    panel: Panel,
    series: np.ndarray,
    scaled: np.ndarray,
    level: np.ndarray,
    scale: np.ndarray,
    cutoff_year: int,
    forecast_years: Sequence[int],
) -> pd.DataFrame:
    """Unscale ``scaled`` (N, H) forecasts and return the rows for ``forecast_years``."""
    values = level[:, None] + scale[:, None] * scaled
    leads = np.asarray(forecast_years, dtype=int) - cutoff_year
    frame = pd.DataFrame(
        {
            "city_id": np.repeat(panel.city_ids[series], len(leads)),
            "year": np.tile(np.asarray(forecast_years, dtype=int), len(series)),
            "metric": np.repeat(panel.metrics[series], len(leads)),
            "predicted_value": values[:, leads - 1].reshape(-1),
        }
    )
    return frame


def with_fallback(
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: Sequence[int],
    neural: pd.DataFrame,
) -> pd.DataFrame:
    """Fill every row the neural model did not produce with the ``current_best`` baseline.

    That covers metrics left out of ``neural_metrics`` and series whose last lookback
    window has fewer than ``min_obs`` observed years (too short or too gappy to window).
    """
    history = annual_to_long(train, cutoff_year=cutoff_year)
    base = metric_ensemble_forecast(
        history,
        cutoff_year=cutoff_year,
        forecast_years=list(forecast_years),
        methods_by_metric=dict(CURRENT_BEST_METHODS),
    )
    if neural.empty:
        return base[[*KEY, "predicted_value"]].reset_index(drop=True)
    merged = base.merge(neural, on=KEY, how="left", suffixes=("_base", ""), validate="1:1")
    merged["predicted_value"] = merged["predicted_value"].fillna(merged["predicted_value_base"])
    if not np.isfinite(merged["predicted_value"]).all():
        raise ValueError("neural forecaster produced non-finite predictions")
    return merged[[*KEY, "predicted_value"]].reset_index(drop=True)


def check_metrics(neural_metrics: Sequence[str] | None) -> list[str]:
    """Validate the ``neural_metrics`` param (None means all four)."""
    chosen = list(METRICS) if neural_metrics is None else list(neural_metrics)
    unknown = sorted(set(chosen) - set(METRICS))
    if unknown:
        raise ValueError(f"neural_metrics has unknown metrics {unknown}; use {list(METRICS)}")
    return [m for m in METRICS if m in chosen]
