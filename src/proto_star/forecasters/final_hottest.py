"""Final-round hottest-day components: Tatakae's nudge and PstarAlu's second-highest anchor.

Both are re-implemented from README text only (no code of either team was downloaded or
copied); the interpretation of every unclear point is fixed in ``docs/trials/final_precip_hot.md``.

* ``final_hottest_nudge`` (H1): Tatakae, dataset ``ironMan334/protostar-climate-team-tatakae``
  (CC BY 4.0), commit ``f18c1178c1b97566c75facc94c886184ebaa2a10``, "Rain and the hottest
  day": 30-year mean + 0.3 x the city's mean departure over the last 10 years from its 31
  nearest cities, each against its own 30-year mean.
* ``final_hottest_second_high`` (H2): PstarAlu (Nibedita Biswal), dataset
  ``nbiswal-star/protostar-climate-submission`` (CC BY 4.0), commit
  ``9e51c3ef5d3178ca194f28e2c4134201c1bf9675``, "Method > Hottest day": the second-highest
  daily maximum as a stable anchor (mean over complete years of the 30-year window) plus the
  tail spacing (highest minus second-highest), pooled with nearby cities by a 300 km Gaussian
  kernel. Their summer-state term and years 1-3 residual layer are not part of it.

Daily maxima are read only through :func:`proto_star.data.daily_fold.daily_to_cutoff` at the
fold cut-off. Only ``hottest_day_temp`` rows are returned; use them through ``swap_metric``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.data.daily_fold import daily_to_cutoff
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._final_common import (
    KEY,
    NudgeSpec,
    kernel_matrix,
    kernel_mean,
    neighbor_nudge,
    thirty_year_rows,
)

METRIC = "hottest_day_temp"


class HottestNudgeSpec(NudgeSpec):
    """Tatakae's hottest-day nudge (difference departures)."""

    def describe(self) -> str:
        return f"Hottest day: {super().describe()}"


def build_hottest_nudge(spec: HottestNudgeSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        rows = thirty_year_rows(train, cutoff_year, forecast_years, METRIC)
        nudge = neighbor_nudge(
            train,
            cutoff_year,
            METRIC,
            k=spec.k,
            recent_years=spec.recent_years,
            window=spec.window,
            min_years=spec.min_years,
            kind="difference",
        )
        rows["predicted_value"] += spec.fraction * rows["city_id"].map(nudge).fillna(0.0)
        return rows[[*KEY, "predicted_value"]]

    return forecast


class SecondHighSpec(ForecasterSpec):
    """PstarAlu's second-highest daily maximum plus pooled tail spacing."""

    window: int = Field(default=30, ge=1)
    min_days: int = Field(default=360, ge=1, le=366)
    min_complete: int = Field(default=10, ge=1)
    bandwidth_km: float = Field(default=300.0, gt=0.0)

    def describe(self) -> str:
        return (
            f"Hottest day: mean second-highest daily maximum over complete years (>= "
            f"{self.min_days} days) of the {self.window}-year window + tail spacing pooled by "
            f"a {self.bandwidth_km:g} km Gaussian kernel (PstarAlu); 30-year mean if < "
            f"{self.min_complete} complete years"
        )


def yearly_top_two(daily: pd.DataFrame) -> pd.DataFrame:
    """Per city and year: days with ``tmax``, highest and second-highest daily maximum.

    Ties count: if the highest value occurs on two days, the second-highest equals it.
    """
    frame = pd.DataFrame(
        {
            "city_id": daily["ID"].astype(str).to_numpy(),
            "year": daily["Date"].dt.year.to_numpy(),
            "tmax": daily["tmax"].to_numpy(dtype=float),
        }
    )
    frame = frame.loc[np.isfinite(frame["tmax"])]
    frame = frame.sort_values(
        ["city_id", "year", "tmax"], ascending=[True, True, False], kind="mergesort"
    )
    rank = frame.groupby(["city_id", "year"], sort=False).cumcount()
    days = frame.groupby(["city_id", "year"])["tmax"].size().rename("days")
    top = frame.loc[rank == 0].set_index(["city_id", "year"])["tmax"].rename("top1")
    second = frame.loc[rank == 1].set_index(["city_id", "year"])["tmax"].rename("top2")
    return pd.concat([days, top, second], axis=1).reset_index()


def build_second_high(spec: SecondHighSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        rows = thirty_year_rows(train, cutoff_year, forecast_years, METRIC)
        daily = daily_to_cutoff(cutoff_year, columns=["tmax"])
        daily = daily.loc[daily["Date"].dt.year > cutoff_year - spec.window]
        yearly = yearly_top_two(daily)
        del daily
        complete = yearly.loc[yearly["days"].ge(spec.min_days) & yearly["top2"].notna()]
        complete = complete.assign(spacing=complete["top1"] - complete["top2"])
        stats = complete.groupby("city_id").agg(
            n=("top2", "size"), level=("top2", "mean"), spacing=("spacing", "mean")
        )
        stats = stats.loc[stats["n"] >= spec.min_complete]

        kernel = kernel_matrix(train, spec.bandwidth_km, include_self=True)
        pooled = kernel_mean(stats["spacing"], kernel)
        anchor = (stats["level"] + pooled.reindex(stats.index)).dropna()
        rows["predicted_value"] = rows["city_id"].map(anchor).fillna(rows["predicted_value"])
        return rows[[*KEY, "predicted_value"]]

    return forecast


register_kind("final_hottest_nudge", HottestNudgeSpec, build_hottest_nudge)
register_kind("final_hottest_second_high", SecondHighSpec, build_second_high)
