"""CDD from a daily temperature map driven by a temperature forecast (kind ``cdd_daily_map``).

Re-implemented from the README text of two public challenge submissions (no code was read or
copied; both datasets are CC BY 4.0):

* Team Tatakae (Mashrafi Mahmud Rafi), Hugging Face dataset
  ``ironMan334/protostar-climate-team-tatakae``, commit
  ``f18c1178c1b97566c75facc94c886184ebaa2a10``, README "Method", third view "daily shape":
  for each of the city's last 10 valid years, shift that year's daily temperatures so the
  year's mean equals the temperature forecast, recount CDD, and average the 10 counts.
* Team PstarAlu (Nibedita Biswal), Hugging Face dataset
  ``nbiswal-star/protostar-climate-submission``, commit
  ``9e51c3ef5d3178ca194f28e2c4134201c1bf9675``, README "Method > Cooling degree days": the same
  kind of map over complete years, as the mean of a 30-year and a 10-year base; a city with
  fewer than five usable base years keeps its CDD.

Both build on the Lai and Dzombak (2019) records (doi 10.1184/R1/7890488.v6, 7961012.v6).

For base year ``k`` with daily means ``tm_i = (tmax_i + tmin_i) / 2`` (days with both values,
the days the annual ``cdd`` counts) and mean ``m_k``, the map to a forecast temperature ``T`` is
``CDD_k(T) = sum_i max(0, tm_i + T - m_k - 65)``. Without a shift it gives back that year's
annual ``cdd``. ``base`` picks the base years per window:

* ``last_valid``: the last ``n`` valid CDD years up to the cut-off (Tatakae, C1);
* ``complete_calendar``: the complete years (valid, and both temperatures on every day) in the
  ``n`` calendar years ending at the cut-off (PstarAlu, C2).

The forecast is the mean over ``windows`` of each window's mean map; windows with fewer than
``min_base_years`` base years are skipped, and a city with no usable window keeps the CDD of the
``temperature`` model. Daily rows come only from :func:`daily_to_cutoff` at the fold cut-off.
Details and the pre-registered choices: ``docs/trials/final_cdd.md``.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import annual_to_long
from proto_star.data.daily_fold import daily_to_cutoff
from proto_star.forecasters import ForecasterSpec, get_kind, register_kind
from proto_star.forecasters.swap_metric import MemberEntry, cached_forecast
from proto_star.trend import CDD, TEMPERATURE

_KEY = ["city_id", "year", "metric"]
CDD_BASE_TEMP = 65.0


class CddDailyMapSpec(ForecasterSpec):
    """Settings of the daily CDD map. Defaults are C1 driven by T0 (lead_split3)."""

    temperature: MemberEntry = Field(default_factory=lambda: MemberEntry(kind="lead_blend"))
    base: Literal["last_valid", "complete_calendar"] = "last_valid"
    windows: list[int] = Field(default=[10], min_length=1)
    min_base_years: int = Field(default=5, ge=1)

    def describe(self) -> str:
        rule = (
            "last {n} valid years"
            if self.base == "last_valid"
            else "complete years in the last {n} calendar years"
        )
        bases = " and ".join(rule.format(n=n) for n in self.windows)
        return (
            f"CDD = daily mean temperatures of each base year shifted to the temperature "
            f"forecast of [{self.temperature.describe()}] and recounted (base 65 F); mean map "
            f"over {bases} (at least {self.min_base_years} base years per window, otherwise "
            f"the temperature model's CDD)"
        )


def daily_means(daily: pd.DataFrame, first_year: int | None = None) -> pd.DataFrame:
    """Daily mean temperature (``tm``) per city and day, on days with both tmax and tmin.

    ``first_year`` drops earlier days first, so the full daily table is never copied as strings.
    """
    year = daily["Date"].dt.year
    keep = daily["tmax"].notna() & daily["tmin"].notna()
    if first_year is not None:
        keep &= year >= first_year
    both = daily.loc[keep]
    return pd.DataFrame(
        {
            "city_id": both["ID"].astype(str).to_numpy(),
            "year": year.loc[keep].to_numpy(),
            "tm": (both["tmax"].to_numpy(np.float64) + both["tmin"].to_numpy(np.float64)) / 2.0,
        }
    )


def days_in_year(years: np.ndarray) -> np.ndarray:
    """365 or 366 for each calendar year."""
    leap = (years % 4 == 0) & ((years % 100 != 0) | (years % 400 == 0))
    return np.where(leap, 366, 365)


def candidate_years(
    valid: pd.DataFrame, *, base: str, window: int, cutoff_year: int
) -> pd.DataFrame:
    """Valid ``(city_id, year)`` pairs a window may use, before the daily completeness check.

    ``last_valid``: each city's last ``window`` valid years. ``complete_calendar``: the valid
    years in the ``window`` calendar years ending at the cut-off.
    """
    pairs = valid.loc[valid["year"] <= cutoff_year, ["city_id", "year"]].drop_duplicates()
    if base == "last_valid":
        return pairs.sort_values("year").groupby("city_id").tail(window)
    if base == "complete_calendar":
        return pairs.loc[pairs["year"].between(cutoff_year - window + 1, cutoff_year)]
    raise ValueError(f"unknown base rule {base!r}")


def base_years(candidates: pd.DataFrame, day_counts: pd.Series, *, base: str) -> pd.DataFrame:
    """Candidate pairs that have daily data (and, for ``complete_calendar``, every day).

    ``day_counts`` holds the days with both temperatures, indexed by ``(city_id, year)``.
    """
    counts = day_counts.reindex(pd.MultiIndex.from_frame(candidates)).fillna(0).to_numpy()
    keep = counts > 0
    if base == "complete_calendar":
        keep &= counts == days_in_year(candidates["year"].to_numpy())
    return candidates.loc[keep]


def map_cdd(days: np.ndarray, groups: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Mean over base years of the recounted CDD, for each target temperature.

    ``days`` are daily mean temperatures, ``groups`` the base-year label of each day, and
    ``targets`` the temperatures each base year is shifted to (its mean becomes the target).
    """
    labels, index = np.unique(groups, return_inverse=True)
    means = np.bincount(index, weights=days) / np.bincount(index)
    shifted = days[None, :] - means[index][None, :] + targets[:, None]
    counts = np.maximum(shifted - CDD_BASE_TEMP, 0.0)
    per_year = np.stack([np.bincount(index, weights=row, minlength=len(labels)) for row in counts])
    result: np.ndarray = per_year.mean(axis=1)
    return result


def daily_map_forecast(
    temperature: pd.DataFrame,
    daily: pd.DataFrame,
    valid: pd.DataFrame,
    *,
    cutoff_year: int,
    base: str,
    windows: list[int],
    min_base_years: int,
) -> pd.DataFrame:
    """CDD map forecasts (``city_id, year, predicted_value``) where a city has a usable base.

    ``temperature`` holds the ``annual_avg_temp`` forecast rows, ``daily`` the fold's daily
    rows (``ID, Date, tmax, tmin``), ``valid`` the valid CDD years (``city_id, year``).
    """
    candidates = [
        candidate_years(valid, base=base, window=n, cutoff_year=cutoff_year) for n in windows
    ]
    needed = pd.concat(candidates, ignore_index=True).drop_duplicates()
    if needed.empty:
        return pd.DataFrame({"city_id": [], "year": [], "predicted_value": []})
    means = daily_means(daily, first_year=int(needed["year"].min()))
    means = means.merge(needed, on=["city_id", "year"])
    day_counts = means.groupby(["city_id", "year"]).size()
    selections = [base_years(c, day_counts, base=base) for c in candidates]
    by_city = dict(tuple(means.groupby("city_id", sort=False)))
    frames: list[pd.DataFrame] = []
    for city, temps in temperature.groupby("city_id", sort=False):
        if city not in by_city:
            continue
        rows = by_city[city]
        targets = temps["predicted_value"].to_numpy(np.float64)
        maps = []
        for chosen in selections:
            years = chosen.loc[chosen["city_id"] == city, "year"].to_numpy()
            if len(years) < min_base_years:
                continue
            use = rows.loc[rows["year"].isin(years)]
            maps.append(map_cdd(use["tm"].to_numpy(), use["year"].to_numpy(), targets))
        if maps:
            frames.append(
                pd.DataFrame(
                    {
                        "city_id": city,
                        "year": temps["year"].to_numpy(),
                        "predicted_value": np.mean(maps, axis=0),
                    }
                )
            )
    if not frames:
        return pd.DataFrame({"city_id": [], "year": [], "predicted_value": []})
    return pd.concat(frames, ignore_index=True)


def build_cdd_daily_map(spec: CddDailyMapSpec) -> Forecaster:
    get_kind(spec.temperature.kind).make_spec(spec.temperature.params)  # fail early on bad params

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        driver = cached_forecast(spec.temperature, train, cutoff_year, forecast_years)
        history = annual_to_long(train, cutoff_year=cutoff_year)
        valid = history.loc[history["metric"] == CDD, ["city_id", "year"]]
        daily = daily_to_cutoff(cutoff_year, columns=["tmax", "tmin"])
        mapped = daily_map_forecast(
            driver.loc[driver["metric"] == TEMPERATURE],
            daily,
            valid,
            cutoff_year=cutoff_year,
            base=spec.base,
            windows=spec.windows,
            min_base_years=spec.min_base_years,
        )
        del daily
        out = driver.copy()
        is_cdd = out["metric"] == CDD
        cdd = out.loc[is_cdd, ["city_id", "year"]].merge(mapped, on=["city_id", "year"], how="left")
        fallback = out.loc[is_cdd, "predicted_value"].to_numpy()
        values = cdd["predicted_value"].to_numpy(np.float64)
        out.loc[is_cdd, "predicted_value"] = np.where(np.isnan(values), fallback, values)
        return out[[*_KEY, "predicted_value"]]

    return forecast


register_kind("cdd_daily_map", CddDailyMapSpec, build_cdd_daily_map)
