"""Global-pattern scaling of city temperature on HadCRUT4 GMST (final round, T7).

Idea source: PstarAlu's README (Nibedita Biswal, Hugging Face dataset
``nbiswal-star/protostar-climate-submission``, CC BY 4.0, commit
``9e51c3ef5d3178ca194f28e2c4134201c1bf9675``, "Method / Average temperature": the forecast
averages "global-pattern scaling" with other parts). The README gives no formula; the one
specification below was fixed before running (``docs/trials/final_temp.md``). No code was
copied or downloaded.

Kind ``final_temp_gmst_scaling``:

1. GMST ``G(y)``: HadCRUT4.6.0.0 annual median anomaly, years <= the fold cut-off only
   (``load_hadcrut4_annual(cutoff_year)``, which applies ``assert_weather_cutoff``).
2. Per city, OLS slope ``beta_c`` of valid annual temperature on ``G`` over the
   ``scaling_window`` years ending at the cut-off (>= ``min_scaling_years``), with its
   standard error ``s_c``.
3. Empirical-Bayes shrinkage toward the regional mean slope ``m_c`` (mean over the
   ``n_cities`` nearest, city included): ``tau^2 = max(0, var(beta - m) - mean(s^2))``,
   ``beta* = m + tau^2 / (tau^2 + s^2) (beta - m)``.
4. GMST forecast: OLS line on ``G`` over the ``gmst_trend_window`` years ending at the
   cut-off, slope floored at 0 (the team's trend convention).
5. Forecast = city mean of its last ``level_years`` valid years + ``beta*`` x
   (``G_hat(year)`` - mean observed ``G`` over those same years).

Produces ``annual_avg_temp`` rows only; use it through ``swap_metric``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._final_temp_common import (
    coordinates,
    nearest_with_self,
    ols_slopes,
    pooled_trend_temperature,
    temperature_panel,
    to_long,
    window_columns,
    with_fallback,
)
from proto_star.neighbors import neighbor_mean


class GmstScalingSpec(ForecasterSpec):
    """T7 settings. Defaults are the pre-registered specification."""

    scaling_window: int = Field(default=40, ge=10)
    min_scaling_years: int = Field(default=20, ge=5)
    gmst_trend_window: int = Field(default=30, ge=5)
    level_years: int = Field(default=15, ge=1)
    n_cities: int = Field(default=32, ge=1)
    gmst_path: str | None = None  # None: the downloaded HadCRUT4 file (tests pass their own)

    def describe(self) -> str:
        return (
            f"GMST scaling: city temperature on HadCRUT4 GMST over {self.scaling_window} "
            f"years, slope shrunk (empirical Bayes) toward the {self.n_cities}-city regional "
            f"mean; GMST from its non-negative {self.gmst_trend_window}-year line; level = "
            f"last {self.level_years} valid years"
        )


def load_gmst(cutoff_year: int, path: str | None) -> pd.Series:
    """GMST anomaly by year up to the fold cut-off."""
    from proto_star.data.external.hadcrut import HADCRUT_FILE, load_hadcrut4_annual

    table = load_hadcrut4_annual(cutoff_year, Path(path) if path else HADCRUT_FILE)
    return table.set_index("year")["gmst"]


def shrunk_slopes(slopes: pd.DataFrame, weights: pd.DataFrame) -> pd.Series:
    """Empirical-Bayes shrinkage of per-city slopes toward their regional mean."""
    regional = neighbor_mean(slopes[["slope"]], weights)["slope"]
    if regional.isna().any():
        regional = regional.fillna(float(slopes["slope"].mean()))
    has = slopes["slope"].notna()
    gap = (slopes["slope"] - regional)[has]
    noise = float((slopes.loc[has, "se"] ** 2).mean()) if has.any() else 0.0
    tau2 = max(0.0, float(gap.var(ddof=1)) - noise) if has.sum() > 1 else 0.0
    se2 = slopes["se"] ** 2
    weight = (tau2 / (tau2 + se2)).where(se2 + tau2 > 0, 0.0)
    shrunk = regional + weight * (slopes["slope"] - regional)
    return shrunk.where(has, regional)


def gmst_line(gmst: pd.Series, cutoff_year: int, window: int) -> tuple[float, float, float]:
    """Mean year, mean GMST and non-negative OLS slope over ``window`` years to the cut-off."""
    recent = gmst.loc[(gmst.index > cutoff_year - window) & (gmst.index <= cutoff_year)]
    if len(recent) < 3:
        raise ValueError(f"need at least 3 GMST years before {cutoff_year}, got {len(recent)}")
    x = recent.index.to_numpy(dtype=float)
    dx = x - x.mean()
    slope = float((dx * (recent.to_numpy() - recent.mean())).sum() / (dx**2).sum())
    return float(x.mean()), float(recent.mean()), max(0.0, slope)


def gmst_scaling_table(
    train: pd.DataFrame, cutoff_year: int, forecast_years: list[int], spec: GmstScalingSpec
) -> pd.DataFrame:
    """T7 as a city x year table (NaN where a city has no level)."""
    gmst = load_gmst(cutoff_year, spec.gmst_path)
    panel = temperature_panel(train, cutoff_year)
    window = window_columns(panel, cutoff_year - spec.scaling_window + 1, cutoff_year)
    slopes = ols_slopes(window, gmst, min_years=spec.min_scaling_years)
    weights = nearest_with_self(coordinates(train), spec.n_cities)
    beta = shrunk_slopes(slopes, weights).reindex(panel.index)
    mean_year, mean_gmst, gmst_slope = gmst_line(gmst, cutoff_year, spec.gmst_trend_window)
    years = np.asarray(forecast_years, dtype=float)
    future = mean_gmst + gmst_slope * (years - mean_year)
    rows = {}
    for (city, series), slope in zip(panel.iterrows(), beta.to_numpy(), strict=True):
        recent = series.dropna().tail(spec.level_years)
        gmst_recent = gmst.reindex(recent.index)
        if recent.empty or gmst_recent.isna().any():
            rows[city] = np.full(len(years), np.nan)
            continue
        rows[city] = float(recent.mean()) + float(slope) * (future - gmst_recent.mean())
    return pd.DataFrame.from_dict(rows, orient="index", columns=list(forecast_years))


def build_gmst_scaling(spec: GmstScalingSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        fallback = pooled_trend_temperature(train, cutoff_year, forecast_years)
        table = gmst_scaling_table(train, cutoff_year, forecast_years, spec)
        return to_long(with_fallback(table, fallback))

    return forecast


register_kind("final_temp_gmst_scaling", GmstScalingSpec, build_gmst_scaling)
