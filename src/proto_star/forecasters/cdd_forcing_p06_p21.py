"""CDD from daily data after a warming shift (replication step 9), P06 and P21 benchmarks.

Three forecasters, all ``current_best`` for the metrics they do not model:

* ``cdd_daily_shift`` (step 9).  Take each city's daily mean temperature
  ``(tmax + tmin) / 2`` over its last ``clim_years`` valid years, add a forecast temperature
  anomaly ``delta = T_hat(year) - T_clim``, and recompute annual CDD with the challenge
  definition: the sum over observed days of ``max(0, Tmean - 65 F)`` (checked to match the
  ``cdd`` column exactly).  CDD is convex in temperature, so under warming the mean of past
  CDD understates future CDD.  ``mode="linear"`` replaces the recomputation by its first-order
  approximation ``CDD_clim + delta * (mean days above 65 F)``, which removes the convexity and
  keeps the level shift: the ablation that tests whether convexity drives a gain.
* ``cdd_on_temp_p06`` (P06, EIA STEO weather model, as adapted in the brief).  Per city, OLS
  of annual CDD on annual mean temperature over the last ``fit_years`` valid years, evaluated
  at a temperature forecast.  The EIA note itself fits a 30-year *time* trend line, which is
  the built-in ``linear_trend`` baseline applied to CDD (an ensemble in the config).
* ``forced_trend_ar1_p21`` (P21; P20 for context).  Per city and metric, OLS on a forcing
  ``F`` (log of NOAA Mauna Loa CO2, or a regional-mean temperature anomaly) plus an AR(1)
  residual: ``y(t+h) = a + b * F_hat(t+h) + phi**h * e(t)``.  ``F`` after the fold's cut-off
  is always extrapolated by a fixed linear rule from values up to the cut-off.

Temperature forecasts ``T_hat`` (``anomaly`` / ``temp_source``):
``recent`` = mean of the last 10 valid years (``current_best``);
``trend`` = ``recent`` plus ``trend_shrink`` times the 30-year OLS slope, carried from the
centre of the 10-year window to the target year; ``co2`` / ``regional`` = the P21 model.

Leakage: everything comes from ``train`` (rows up to the cut-off), except the daily table and
the CO2 file, which are read here and cut to ``Year <= cutoff_year`` and passed through
``assert_weather_cutoff`` before use.  Cards: ``papers/2025_eia_steo_cdd/README.md`` (step 9,
P06) and ``papers/2013_ho_forced_trend_ar1/README.md`` (P21).
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST_METHODS, Forecaster, ensemble_forecaster
from proto_star.climate import (
    BASELINE_WINDOW_YEARS,
    METRICS,
    annual_to_long,
    assert_weather_cutoff,
    metric_valid_mask,
)
from proto_star.forecasters.registry import register_forecaster
from proto_star.paths import EXTERNAL_DIR, RAW_DIR

CDD_BASE_F = 65.0
RECENT_YEARS = 10
TEMP_SOURCES = ("recent", "trend", "co2", "regional")
SHIFT_MODES = ("daily", "linear")
FORCINGS = ("co2", "regional")
DEFAULT_DAILY_DIR = RAW_DIR / "protostar"
DEFAULT_CO2_FILE = EXTERNAL_DIR / "noaa_co2" / "co2_annmean_mlo_to_2018.csv"
_KEY = ["city_id", "year", "metric"]
_TEMP = "annual_avg_temp"


# ---------------------------------------------------------------- inputs read from disk
@lru_cache(maxsize=2)  # one read per process and path: the table is ~10M rows
def _daily_tmean(daily_dir: str) -> pd.DataFrame:
    """Daily ``ID, Year, tmean`` (float32) for all observed days, sorted by city and year."""
    from proto_star.data.protostar import load_daily

    daily = load_daily(Path(daily_dir), columns=("tmax", "tmin"))
    tmean = (daily["tmax"] + daily["tmin"]) / np.float32(2.0)
    frame = pd.DataFrame(
        {
            "ID": daily["ID"].astype(str).astype("category"),
            "Year": daily["Date"].dt.year.astype("int16"),
            "tmean": tmean.astype("float32"),
        }
    )
    del daily
    frame = frame.loc[frame["tmean"].notna()]
    return frame.sort_values(["ID", "Year"], kind="stable", ignore_index=True)


def _daily_up_to(daily_dir: str, cutoff_year: int, first_year: int) -> pd.DataFrame:
    """Daily rows of years ``first_year..cutoff_year`` only, checked against the cut-off."""
    daily = _daily_tmean(daily_dir)
    keep = (daily["Year"] <= cutoff_year) & (daily["Year"] >= first_year)
    window = daily.loc[keep]
    assert_weather_cutoff(window, name="daily (fold)", cutoff_year=cutoff_year)
    return window


def load_co2(path: Path, cutoff_year: int) -> pd.Series:
    """Annual mean CO2 (ppm) indexed by year, cut to ``cutoff_year`` and checked."""
    table = pd.read_csv(path)
    if not {"year", "co2_ppm"} <= set(table.columns):
        raise ValueError(f"{path} needs columns year, co2_ppm; run scripts/download_noaa_co2.py")
    table = table.loc[table["year"] <= cutoff_year]
    assert_weather_cutoff(table, name="NOAA CO2", cutoff_year=cutoff_year)
    if table.empty:
        raise ValueError(f"no CO2 values on or before {cutoff_year} in {path}")
    return pd.Series(table["co2_ppm"].to_numpy(float), index=table["year"].astype(int).to_numpy())


def _extrapolate_linear(series: pd.Series, years: Sequence[int], fit_years: int) -> pd.Series:
    """``series`` where known, else a straight line fitted to its last ``fit_years`` values."""
    tail = series.dropna().sort_index().tail(fit_years)
    wanted = np.asarray(sorted(set(series.index) | set(years)), dtype=int)
    if len(tail) < 2:
        line = np.full(len(wanted), float(tail.mean()) if len(tail) else np.nan)
    else:
        slope, intercept = np.polyfit(tail.index.to_numpy(float), tail.to_numpy(float), deg=1)
        line = intercept + slope * wanted.astype(float)
    result = pd.Series(line, index=wanted)
    known = series.dropna()
    result.loc[known.index] = known.to_numpy(float)
    return result


# ---------------------------------------------------------------- annual panels
def _valid_panel(train: pd.DataFrame, cutoff_year: int) -> pd.DataFrame:
    """One row per city-year with ``temp`` and ``cdd`` where each passes the official rule."""
    temp_ok = metric_valid_mask(train, _TEMP)
    cdd_ok = metric_valid_mask(train, "cdd")
    panel = pd.DataFrame(
        {
            "city_id": train["ID"].astype(str).to_numpy(),
            "year": pd.to_numeric(train["Year"]).astype(int).to_numpy(),
            "temp": pd.to_numeric(train["Avg Temp"], errors="coerce").where(temp_ok).to_numpy(),
            "cdd": pd.to_numeric(train["cdd"], errors="coerce").where(cdd_ok).to_numpy(),
            "region": (train["region"].astype(str).to_numpy() if "region" in train else "all"),
        }
    )
    panel = panel.loc[panel["year"] <= cutoff_year]
    return panel.sort_values(["city_id", "year"], ignore_index=True)


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Intercept and slope of ``y`` on ``x`` (slope 0 when ``x`` is constant)."""
    if x.size < 2 or np.isclose(np.ptp(x), 0.0):
        return float(np.mean(y)), 0.0
    slope, intercept = np.polyfit(x, y, deg=1)
    return float(intercept), float(slope)


def _ar1_phi(years: np.ndarray, residuals: np.ndarray, phi_max: float) -> float:
    """Lag-1 autocorrelation of residuals over consecutive years, clipped to ``[0, phi_max]``."""
    order = np.argsort(years)
    years, residuals = years[order], residuals[order]
    pairs = np.diff(years) == 1
    if pairs.sum() < 3:
        return 0.0
    lead, lag = residuals[1:][pairs], residuals[:-1][pairs]
    denominator = float(np.sum(lag**2))
    phi = float(np.sum(lead * lag) / denominator) if denominator > 0 else 0.0
    return float(np.clip(phi, 0.0, phi_max))


def _forcing(
    kind: str,
    panel: pd.DataFrame,
    cutoff_year: int,
    years: Sequence[int],
    *,
    fit_years: int,
    extrap_years: int,
    co2_file: Path,
) -> dict[str, pd.Series]:
    """Forcing per region (``"all"`` for CO2), known to the cut-off and extrapolated after it."""
    if kind == "co2":
        co2 = load_co2(co2_file, cutoff_year)
        full = _extrapolate_linear(co2, years, extrap_years)
        return {"all": pd.Series(np.log(full.to_numpy(float)), index=full.index)}
    if kind != "regional":
        raise ValueError(f"unknown forcing {kind!r}; use one of {list(FORCINGS)}")
    recent = panel.loc[panel["year"] > cutoff_year - fit_years].dropna(subset=["temp"])
    anomaly = recent["temp"] - recent.groupby("city_id")["temp"].transform("mean")
    regional = anomaly.groupby([recent["region"], recent["year"]]).mean()
    return {
        str(region): _extrapolate_linear(series.droplevel(0), years, extrap_years)
        for region, series in regional.groupby(level=0)
    }


def forced_trend_ar1(
    panel: pd.DataFrame,
    cutoff_year: int,
    years: Sequence[int],
    *,
    metrics: Sequence[str],
    forcing: str,
    fit_years: int,
    extrap_years: int,
    min_points: int,
    phi_max: float,
    co2_file: Path,
) -> pd.DataFrame:
    """P21 forecasts ``city_id, year, metric, model_value`` for each series with enough years."""
    forcings = _forcing(
        forcing,
        panel,
        cutoff_year,
        years,
        fit_years=fit_years,
        extrap_years=extrap_years,
        co2_file=co2_file,
    )
    columns = {_TEMP: "temp", "cdd": "cdd"}
    target_years = np.asarray(list(years), dtype=int)
    rows: list[pd.DataFrame] = []
    window = panel.loc[panel["year"] > cutoff_year - fit_years]
    for (city_id, region), group in window.groupby(["city_id", "region"], sort=True):
        series = forcings.get("all" if forcing == "co2" else str(region))
        if series is None:
            continue
        for metric in metrics:
            data = group.dropna(subset=[columns[metric]])
            data = data.loc[data["year"].isin(series.index)]
            if len(data) < min_points:
                continue
            obs_years = data["year"].to_numpy(int)
            x = series.loc[obs_years].to_numpy(float)
            y = data[columns[metric]].to_numpy(float)
            intercept, slope = _ols(x, y)
            residuals = y - (intercept + slope * x)
            phi = _ar1_phi(obs_years, residuals, phi_max)
            last = int(np.argmax(obs_years))
            steps = target_years - obs_years[last]
            value = (
                intercept
                + slope * series.loc[target_years].to_numpy(float)
                + phi**steps * residuals[last]
            )
            rows.append(
                pd.DataFrame(
                    {
                        "city_id": city_id,
                        "year": target_years,
                        "metric": metric,
                        "model_value": value,
                    }
                )
            )
    if not rows:
        return pd.DataFrame(columns=[*_KEY, "model_value"])
    return pd.concat(rows, ignore_index=True)


def temperature_forecast(
    train: pd.DataFrame,
    panel: pd.DataFrame,
    cutoff_year: int,
    years: Sequence[int],
    *,
    source: str,
    trend_shrink: float,
    p21: dict[str, Any],
) -> pd.DataFrame:
    """``city_id, year, t_hat``: the annual mean temperature forecast that drives the CDD shift."""
    if source not in TEMP_SOURCES:
        raise ValueError(f"unknown temperature source {source!r}; use one of {list(TEMP_SOURCES)}")
    base = ensemble_forecaster(CURRENT_BEST_METHODS)(train, cutoff_year, list(years))
    t_hat = base.loc[base["metric"] == _TEMP, ["city_id", "year", "predicted_value"]]
    t_hat = t_hat.rename(columns={"predicted_value": "t_hat"}).reset_index(drop=True)
    if source == "recent":
        return t_hat
    if source == "trend":
        offsets: list[pd.DataFrame] = []
        temps = panel.dropna(subset=["temp"])
        for city_id, group in temps.groupby("city_id", sort=True):
            recent = group.tail(RECENT_YEARS)
            window = group.loc[group["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
            if len(window) < RECENT_YEARS:
                continue
            _, slope = _ols(window["year"].to_numpy(float), window["temp"].to_numpy(float))
            centre = float(recent["year"].mean())
            offsets.append(
                pd.DataFrame(
                    {
                        "city_id": city_id,
                        "year": list(years),
                        "offset": trend_shrink * slope * (np.asarray(years, float) - centre),
                    }
                )
            )
        if not offsets:
            return t_hat
        merged = t_hat.merge(pd.concat(offsets), on=["city_id", "year"], how="left")
        merged["t_hat"] = merged["t_hat"] + merged["offset"].fillna(0.0)
        return merged[["city_id", "year", "t_hat"]]
    model = forced_trend_ar1(panel, cutoff_year, years, metrics=[_TEMP], forcing=source, **p21)
    merged = t_hat.merge(
        model[["city_id", "year", "model_value"]], on=["city_id", "year"], how="left"
    )
    use = merged["model_value"].notna() & np.isfinite(merged["model_value"])
    merged.loc[use, "t_hat"] = merged.loc[use, "model_value"]
    return merged[["city_id", "year", "t_hat"]]


# ---------------------------------------------------------------- shifted daily CDD
def shifted_cdd(
    tmean: np.ndarray, n_years: int, deltas: np.ndarray, *, mode: str = "daily"
) -> np.ndarray:
    """Mean annual CDD of the climatology days after adding each ``delta`` (°F) to every day.

    ``mode="daily"`` recomputes ``sum(max(0, T + delta - 65)) / n_years`` exactly.
    ``mode="linear"`` is its tangent at ``delta = 0``: same level shift, no convexity.
    """
    if mode not in SHIFT_MODES:
        raise ValueError(f"unknown mode {mode!r}; use one of {list(SHIFT_MODES)}")
    if n_years < 1:
        raise ValueError("n_years must be at least 1")
    values = np.asarray(tmean, dtype=float)
    base = np.maximum(values - CDD_BASE_F, 0.0).sum() / n_years
    if mode == "linear":
        hot_days = float((values > CDD_BASE_F).sum()) / n_years
        return np.maximum(base + deltas * hot_days, 0.0)
    excess = values[:, None] + np.asarray(deltas, float)[None, :] - CDD_BASE_F
    return np.asarray(np.maximum(excess, 0.0).sum(axis=0) / n_years, dtype=float)


def _p21_params(
    fit_years: int, extrap_years: int, min_points: int, phi_max: float, co2_file: str | None
) -> dict[str, Any]:
    if fit_years < 5 or extrap_years < 2 or min_points < 3:
        raise ValueError("need fit_years >= 5, extrap_years >= 2 and min_points >= 3")
    if not 0.0 <= phi_max < 1.0:
        raise ValueError(f"phi_max must be in [0, 1), got {phi_max}")
    return {
        "fit_years": fit_years,
        "extrap_years": extrap_years,
        "min_points": min_points,
        "phi_max": phi_max,
        "co2_file": Path(co2_file) if co2_file else DEFAULT_CO2_FILE,
    }


def _overlay(base: pd.DataFrame, model: pd.DataFrame) -> pd.DataFrame:
    """``base`` with ``model_value`` substituted where it exists and is finite."""
    if model.empty:
        return base
    merged = base.merge(model[[*_KEY, "model_value"]], on=_KEY, how="left")
    use = merged["model_value"].notna() & np.isfinite(merged["model_value"].astype(float))
    merged.loc[use, "predicted_value"] = merged.loc[use, "model_value"]
    return merged[[*_KEY, "predicted_value"]]


@register_forecaster(
    "cdd_daily_shift",
    description=(
        "Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD "
        "recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics"
    ),
)
def make_cdd_daily_shift(
    *,
    clim_years: int = 30,
    anomaly: str = "recent",
    mode: str = "daily",
    trend_shrink: float = 0.5,
    blend_ridge_weight: float = 0.0,
    ridge_params: dict[str, Any] | None = None,
    fit_years: int = 40,
    extrap_years: int = 10,
    min_points: int = 15,
    phi_max: float = 0.95,
    co2_file: str | None = None,
    daily_dir: str | None = None,
) -> Forecaster:
    """Build the step-9 forecaster; ``blend_ridge_weight`` averages in the pooled ridge CDD."""
    if clim_years < 1:
        raise ValueError("clim_years must be at least 1")
    if mode not in SHIFT_MODES:
        raise ValueError(f"unknown mode {mode!r}; use one of {list(SHIFT_MODES)}")
    if anomaly not in TEMP_SOURCES:
        raise ValueError(f"unknown anomaly {anomaly!r}; use one of {list(TEMP_SOURCES)}")
    if not 0.0 <= blend_ridge_weight <= 1.0:
        raise ValueError("blend_ridge_weight must be in [0, 1]")
    p21 = _p21_params(fit_years, extrap_years, min_points, phi_max, co2_file)
    source_dir = str(Path(daily_dir) if daily_dir else DEFAULT_DAILY_DIR)
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)
    ridge: Forecaster | None = None
    if blend_ridge_weight > 0.0:
        from proto_star.forecasters.pooled_p09_p14 import make_pooled_median

        settings = dict(ridge_params or {"estimator": "ridge", "alpha": 1.0, "train_years": None})
        ridge = make_pooled_median(model_metrics=["cdd"], **settings)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        panel = _valid_panel(train, cutoff_year)
        both = panel.dropna(subset=["temp", "cdd"])
        clim = both.groupby("city_id", sort=True).tail(clim_years)
        if clim.empty:
            return base
        daily = _daily_up_to(source_dir, cutoff_year, int(clim["year"].min()))
        t_hat = temperature_forecast(
            train,
            panel,
            cutoff_year,
            forecast_years,
            source=anomaly,
            trend_shrink=trend_shrink,
            p21=p21,
        )
        t_by_city = {city: group for city, group in t_hat.groupby("city_id")}
        days_by_city = {
            str(city): group for city, group in daily.groupby("ID", observed=True, sort=False)
        }
        rows: list[pd.DataFrame] = []
        for city_id, group in clim.groupby("city_id", sort=True):
            days = days_by_city.get(str(city_id))
            target = t_by_city.get(city_id)
            if days is None or target is None:
                continue
            days = days.loc[days["Year"].isin(group["year"].to_numpy())]
            n_years = int(days["Year"].nunique())
            if n_years == 0:
                continue
            delta = target["t_hat"].to_numpy(float) - float(group["temp"].mean())
            value = shifted_cdd(days["tmean"].to_numpy(), n_years, delta, mode=mode)
            rows.append(
                pd.DataFrame(
                    {
                        "city_id": city_id,
                        "year": target["year"].to_numpy(int),
                        "metric": "cdd",
                        "model_value": value,
                    }
                )
            )
        model = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=_KEY)
        result = _overlay(base, model)
        if ridge is not None:
            pooled = ridge(train, cutoff_year, forecast_years)
            merged = result.merge(pooled, on=_KEY, suffixes=("", "_ridge"))
            cdd = merged["metric"] == "cdd"
            merged.loc[cdd, "predicted_value"] = (1.0 - blend_ridge_weight) * merged.loc[
                cdd, "predicted_value"
            ] + blend_ridge_weight * merged.loc[cdd, "predicted_value_ridge"]
            result = merged[[*_KEY, "predicted_value"]]
        return result

    return forecast


@register_forecaster(
    "cdd_on_temp_p06",
    description=(
        "P06 (EIA, adapted): per-city OLS of annual CDD on annual mean temperature, "
        "evaluated at a temperature forecast; current_best for the other metrics"
    ),
)
def make_cdd_on_temp(
    *,
    fit_years: int = 30,
    temp_source: str = "recent",
    trend_shrink: float = 0.5,
    min_points: int = 10,
) -> Forecaster:
    """Build the P06 regression forecaster (``fit_years`` = last valid years per city)."""
    if fit_years < 3 or min_points < 3:
        raise ValueError("fit_years and min_points must be at least 3")
    if temp_source not in ("recent", "trend"):
        raise ValueError("temp_source must be 'recent' or 'trend' for cdd_on_temp_p06")
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        panel = _valid_panel(train, cutoff_year)
        t_hat = temperature_forecast(
            train,
            panel,
            cutoff_year,
            forecast_years,
            source=temp_source,
            trend_shrink=trend_shrink,
            p21={},
        )
        fits = panel.dropna(subset=["temp", "cdd"]).groupby("city_id", sort=True).tail(fit_years)
        coefficients = []
        for city_id, group in fits.groupby("city_id", sort=True):
            if len(group) < min_points:
                continue
            intercept, slope = _ols(group["temp"].to_numpy(float), group["cdd"].to_numpy(float))
            coefficients.append((city_id, intercept, slope))
        if not coefficients:
            return base
        table = pd.DataFrame(coefficients, columns=["city_id", "intercept", "slope"])
        model = t_hat.merge(table, on="city_id")
        model["model_value"] = (model["intercept"] + model["slope"] * model["t_hat"]).clip(lower=0)
        model["metric"] = "cdd"
        return _overlay(base, model)

    return forecast


@register_forecaster(
    "forced_trend_ar1_p21",
    description=(
        "P21: per-city OLS on a forcing (log NOAA CO2 or regional-mean temperature, "
        "extrapolated past the cut-off by a fixed linear rule) plus AR(1) residual"
    ),
)
def make_forced_trend_ar1(
    *,
    forcing: str = "co2",
    metrics: Sequence[str] = (_TEMP, "cdd"),
    fit_years: int = 40,
    extrap_years: int = 10,
    min_points: int = 15,
    phi_max: float = 0.95,
    co2_file: str | None = None,
) -> Forecaster:
    """Build the P21 benchmark for ``metrics`` (temperature and/or CDD)."""
    if forcing not in FORCINGS:
        raise ValueError(f"unknown forcing {forcing!r}; use one of {list(FORCINGS)}")
    allowed = {_TEMP, "cdd"}
    if not metrics or not set(metrics) <= allowed:
        raise ValueError(f"metrics must be a non-empty subset of {sorted(allowed)}")
    modelled = [m for m in METRICS if m in set(metrics)]
    p21 = _p21_params(fit_years, extrap_years, min_points, phi_max, co2_file)
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        annual_to_long(train, cutoff_year=cutoff_year)  # same input checks as the baselines
        panel = _valid_panel(train, cutoff_year)
        model = forced_trend_ar1(
            panel, cutoff_year, forecast_years, metrics=modelled, forcing=forcing, **p21
        )
        cdd = model["metric"] == "cdd"
        model.loc[cdd, "model_value"] = model.loc[cdd, "model_value"].astype(float).clip(lower=0)
        return _overlay(base, model)

    return forecast
