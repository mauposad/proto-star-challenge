"""Hottest-day forecasts from summer-mean Tmax: hypotheses H2 and H14 in ``hypotheses.md``.

Every arm starts from the hottest day's 30-year mean, the official reference, and adds a shift:

* ``jja_slope`` (H2 primary): ``kappa`` x the pooled within-city June-August Tmax slope x
  (year - centre of the 30-year window).  ``kappa = 1`` is a pure location shift, an a-priori
  assumption, not a constant taken from post-2018 work.
* ``annual_slope`` / ``own_slope``: the same with the pooled annual-temperature slope, or with the
  hottest day's own pooled slope (H2's discriminating arms).
* ``constant_shift``: the mean of the ``jja_slope`` shift over the forecast years, applied flat
  (methodologist H2-b control).
* ``summer_level`` (H14): the recent June-August level minus its 30-year mean.
* ``summer_level_slope`` (H14): ``summer_level`` plus the June-August slope from the recent
  level's centre.

Slopes are floored at 0, as in the candidate, and fitted over ``trend_window`` calendar years.
The June-August means arrive as per-year columns of ``train``; see ``proto_star.data.summer``.
Other metrics come from the base forecaster.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from proto_star.climate import BASELINE_WINDOW_YEARS, annual_to_long
from proto_star.trend import PooledTrendSpec, pooled_slope
from proto_star.utils.logging import get_logger

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
HOTTEST = "hottest_day_temp"
SUMMER = "jja_tmax"
log = get_logger(__name__)


class HottestSummerSpec(BaseModel):
    """Settings of one hottest-day arm, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    arm: Literal[
        "jja_slope",
        "annual_slope",
        "own_slope",
        "constant_shift",
        "summer_level",
        "summer_level_slope",
    ]
    kappa: float = 1.0
    trend_window: int = Field(default=40, ge=10)
    level_years: list[int] = Field(default_factory=lambda: [10, 15], min_length=1)
    min_city_years: int = Field(default=10, ge=3)


def _summer_history(train: pd.DataFrame) -> pd.DataFrame:
    if SUMMER not in train.columns:
        raise ValueError("hottest_summer needs the June-August columns: set join_summer: true")
    rows = train.loc[train[SUMMER].notna(), ["ID", "Year", SUMMER]]
    return pd.DataFrame(
        {
            "city_id": rows["ID"].astype(str),
            "year": rows["Year"].astype(int),
            "metric": SUMMER,
            "actual_value": rows[SUMMER].astype(float),
        }
    )


def _recent_level(rows: pd.DataFrame, level_years: list[int]) -> tuple[pd.Series, pd.Series]:
    """Mean over windows of each city's last-N values, and the mean year they sit at."""
    levels, centres = [], []
    for n in level_years:
        recent = rows.sort_values("year").groupby("city_id").tail(n).groupby("city_id")
        levels.append(recent["actual_value"].mean())
        centres.append(recent["year"].mean())
    return pd.concat(levels, axis=1).mean(axis=1), pd.concat(centres, axis=1).mean(axis=1)


def hottest_summer_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: HottestSummerSpec,
) -> pd.DataFrame:
    """The base forecast with the hottest day replaced by one H2/H14 arm."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    summer = _summer_history(train.loc[train["Year"] <= cutoff_year])
    both = pd.concat([history, summer], ignore_index=True)
    trend_spec = PooledTrendSpec(
        level_years=[10], trend_window=spec.trend_window, min_city_years=spec.min_city_years
    )
    slopes = {
        name: pooled_slope(both, metric, cutoff_year, trend_spec)
        for name, metric in (
            ("jja", SUMMER),
            ("annual", "annual_avg_temp"),
            ("own", HOTTEST),
        )
    }
    ratio = slopes["own"] / slopes["jja"] if slopes["jja"] > 0 else float("nan")
    log.info(
        "hottest slopes at cutoff %d: jja=%.4f annual=%.4f own=%.4f kappa_hat=%.2f",
        cutoff_year,
        slopes["jja"],
        slopes["annual"],
        slopes["own"],
        ratio,
    )

    hottest = history.loc[history["metric"] == HOTTEST]
    window = hottest.loc[hottest["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
    m30 = window.groupby("city_id")["actual_value"].mean()
    centre30 = window.groupby("city_id")["year"].mean()

    forecast = base(train, cutoff_year, forecast_years).copy()
    is_hot = forecast["metric"] == HOTTEST
    rows = forecast.loc[is_hot, ["city_id", "year"]]
    cities, years = rows["city_id"], rows["year"].to_numpy(dtype=float)
    level = m30.reindex(cities).to_numpy()
    from_centre = years - centre30.reindex(cities).to_numpy()

    if spec.arm in ("jja_slope", "annual_slope", "own_slope", "constant_shift"):
        key = {"jja_slope": "jja", "annual_slope": "annual", "own_slope": "own"}.get(
            spec.arm, "jja"
        )
        shift = spec.kappa * slopes[key] * from_centre
        if spec.arm == "constant_shift":
            shift = np.full_like(shift, np.nanmean(shift))
    else:
        summer_window = summer.loc[summer["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
        s30 = summer_window.groupby("city_id")["actual_value"].mean()
        recent, centre = _recent_level(summer, spec.level_years)
        shift = (recent - s30).reindex(cities).to_numpy()
        if spec.arm == "summer_level_slope":
            shift = shift + slopes["jja"] * (years - centre.reindex(cities).to_numpy())
    derived = level + shift
    keep = np.isfinite(derived)
    values = forecast.loc[is_hot, "predicted_value"].to_numpy()
    forecast.loc[is_hot, "predicted_value"] = np.where(keep, derived, values)
    return forecast
