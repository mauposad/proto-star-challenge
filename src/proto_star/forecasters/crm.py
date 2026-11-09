"""The Coupled Regional Model (CRM): between one pooled trend and 210 city trends, by shrinkage.

Pooled and local models are two ends of one scale: one region is the pooled model, one region
per city is the local model. The CRM starts at the pooled end (``proto_star.trend``, the
champion) and moves toward regions only as far as the data supports:

* Layer 1, regions: the six fixed coordinate regions, or spectral clusters of cities on the
  correlation of their detrended temperature anomalies plus closeness on the map, recomputed
  from each fold's training rows.
* Layer 2, shrunk regional trends: ``beta[r] = pooled + k_scale * k_r * (regional[r] - pooled)``
  with the empirical-Bayes weight ``k_r = tau^2 / (tau^2 + se_r^2)``. ``tau^2`` is the spread of
  regional slopes left after their sampling error, ``se_r`` a year-clustered standard error.
  ``k_r = 0`` (or ``k_scale = 0``) gives back the champion exactly. CDD keeps the champion's
  per-city sensitivity, times the region's shrunk temperature trend (``cdd_trend`` offers two
  alternatives). With ``urban``, one pooled gamma times census growth offsets city slopes.
* Layer 3, interactions (optional): a lasso VAR(1) on regional anomalies of all four metrics.
  Its forecast decays with lead and is added to every city of the region.
* Precipitation and hottest day keep the 30-year mean unless ``flat_level`` asks for the
  station-segment mean or a regional empirical-Bayes level (``_crm_levels``).

Everything is computed from ``train``. The one other input, read only with ``urban``, is the
census table (not weather), of which only censuses up to the cut-off are used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import METRICS, annual_to_long, baseline_forecast, validate_climate_history
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._crm_levels import regional_eb_levels, segment_levels
from proto_star.forecasters._crm_regions import city_coordinates, spectral_regions
from proto_star.forecasters._crm_urban import load_city_static, urban_gamma, urban_growth
from proto_star.forecasters._crm_var import VarFit, fit_sparse_var, regional_panel
from proto_star.trend import (
    CDD,
    FLAT_METHOD,
    TEMPERATURE,
    PooledTrendSpec,
    _levels,
    _window_anomalies,
    cdd_per_degree,
)

Metric = Literal["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
TREND_METRICS = (TEMPERATURE, CDD)


class CRMSpec(ForecasterSpec):
    """Settings of one Coupled Regional Model, set under ``models`` in a trial config."""

    # Champion parts (proto_star.trend), kept as they are
    level_years: list[int] = Field(default=[10, 15], min_length=1)
    trend_window: int = Field(default=40, ge=10)
    min_city_years: int = Field(default=10, ge=3)
    # CDD trend per city. sensitivity (champion): city CDD per degree x the region's shrunk
    # temperature trend. regional_slope: the region's shrunk CDD slope. rescaled_sensitivity:
    # the region's shrunk CDD slope, spread over its cities in proportion to their CDD per degree.
    cdd_trend: Literal["sensitivity", "regional_slope", "rescaled_sensitivity"] = "sensitivity"
    # Layer 1
    regions: Literal["fixed", "spectral"] = "fixed"
    n_clusters: int = Field(default=6, ge=2)
    cluster_window: int = Field(default=60, ge=10)  # years of anomalies the clusters use
    geo_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    geo_scale_km: float = Field(default=800.0, gt=0.0)
    # Layer 2
    k_scale: float = Field(default=1.0, ge=0.0, le=1.0)
    # Layer 3
    var: bool = False
    var_alpha: float | None = Field(default=None, gt=0.0)  # None: time-series CV inside train
    var_window: int = Field(default=40, ge=15)
    var_damping: float = Field(default=1.0, ge=0.0, le=1.0)
    var_metrics: list[Metric] = Field(  # metrics that get the VAR shift
        default=["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
    )
    # True: regions average each city's anomaly divided by its own spread, and the shift is
    # scaled back by that spread, so a cool city gets a smaller CDD shift than a hot one.
    var_city_scale: bool = False
    # Plan 5.5: precipitation and hottest-day level
    flat_level: Literal["thirty_year_mean", "segment", "regional_eb"] = "thirty_year_mean"
    flat_metrics: list[Metric] = Field(default=["total_precip_in", "hottest_day_temp"])
    segment_min_years: int = Field(default=15, ge=3)
    # Row 8: temperature slope offset gamma x centered urban growth, one pooled gamma (census)
    urban: bool = False
    seed: int = 0

    def trend_spec(self) -> PooledTrendSpec:
        """The champion's settings inside this spec."""
        return PooledTrendSpec(
            level_years=self.level_years,
            trend_window=self.trend_window,
            min_city_years=self.min_city_years,
            cdd_sensitivity=self.cdd_trend == "sensitivity",
        )

    def describe(self) -> str:
        regions = (
            "6 fixed regions"
            if self.regions == "fixed"
            else f"{self.n_clusters} spectral clusters (geo weight {self.geo_weight})"
        )
        parts = [
            f"CRM: levels {self.level_years}, non-negative pooled {self.trend_window}-year trend "
            f"for temperature and CDD shrunk toward {regions} by empirical Bayes "
            f"(k_scale {self.k_scale})",
            {
                "sensitivity": "CDD trend = shrunk regional temperature trend x city CDD per "
                "degree",
                "regional_slope": "CDD trend = shrunk regional CDD slope",
                "rescaled_sensitivity": "CDD trend = shrunk regional CDD slope spread by city "
                "CDD per degree",
            }[self.cdd_trend],
        ]
        if self.var:
            alpha = "CV" if self.var_alpha is None else self.var_alpha
            scaled = ", city-scaled" if self.var_city_scale else ""
            metrics = "" if set(self.var_metrics) == set(METRICS) else f" on {self.var_metrics}"
            parts.append(
                f"lasso VAR(1) regional interactions{metrics} (alpha {alpha}, "
                f"{self.var_window} years, damping {self.var_damping}{scaled})"
            )
        flat = {
            "thirty_year_mean": "30-year mean",
            "segment": f"current-station-segment mean (>= {self.segment_min_years} years)",
            "regional_eb": "regional empirical-Bayes 30-year level",
        }[self.flat_level]
        if self.urban:
            parts.append("temperature slope + pooled gamma x census growth of the last decade")
        parts.append(f"{flat} for {', '.join(self.flat_metrics)}")
        others = [m for m in ("total_precip_in", "hottest_day_temp") if m not in self.flat_metrics]
        if others:
            parts.append(f"30-year mean for {', '.join(others)}")
        return "; ".join(parts)


@dataclass(frozen=True)
class RegionalTrend:
    """Layer 2 for one metric: the pooled slope and each region's raw and shrunk slope."""

    pooled: float  # floored at zero, as in the champion
    pooled_raw: float
    tau2: float
    table: pd.DataFrame  # index region: beta, se, n_cities, k_eb, k, beta_final


@dataclass(frozen=True)
class CRMFit:
    """Everything the CRM fits for one cut-off, kept for diagnostics."""

    city_region: pd.Series
    trends: dict[str, RegionalTrend]
    city_slopes: dict[str, pd.Series]
    var: VarFit | None
    city_scale: pd.Series | None = None  # (city_id, metric) spread used by var_city_scale
    urban_gamma: float | None = None


def shrunk_regional_trend(
    history: pd.DataFrame,
    metric: str,
    cutoff_year: int,
    spec: CRMSpec,
    city_region: pd.Series,
) -> RegionalTrend:
    """Regional within-city slopes, shrunk toward the pooled slope by empirical Bayes."""
    anomalies = _window_anomalies(history, metric, cutoff_year, spec.trend_spec())
    spread = float((anomalies["x"] ** 2).sum())
    pooled_raw = float((anomalies["x"] * anomalies["y"]).sum()) / spread if spread else 0.0
    pooled = max(0.0, pooled_raw)
    anomalies = anomalies.assign(region=anomalies["city_id"].map(city_region)).dropna(
        subset=["region"]
    )
    rows = []
    for region, group in anomalies.groupby("region", sort=True):
        sxx = float((group["x"] ** 2).sum())
        if sxx == 0.0:
            continue
        beta = float((group["x"] * group["y"]).sum()) / sxx
        score = (group["x"] * (group["y"] - beta * group["x"])).groupby(group["year"]).sum()
        clusters = len(score)
        correction = clusters / (clusters - 1) if clusters > 1 else 1.0
        se = float(np.sqrt(correction * float((score**2).sum()) / sxx**2))
        rows.append(
            {"region": region, "beta": beta, "se": se, "n_cities": group["city_id"].nunique()}
        )
    table = pd.DataFrame(rows, columns=["region", "beta", "se", "n_cities"]).set_index("region")
    if table.empty:
        tau2 = 0.0
    else:
        tau2 = max(
            0.0, float(((table["beta"] - pooled_raw) ** 2).mean() - (table["se"] ** 2).mean())
        )
    denominator = tau2 + table["se"] ** 2
    table["k_eb"] = (tau2 / denominator).where(denominator > 0, 0.0) if tau2 > 0 else 0.0
    table["k"] = spec.k_scale * table["k_eb"]
    table["beta_final"] = (pooled + table["k"] * (table["beta"] - pooled)).clip(lower=0.0)
    return RegionalTrend(pooled=pooled, pooled_raw=pooled_raw, tau2=tau2, table=table)


def _regions(
    train: pd.DataFrame, history: pd.DataFrame, cutoff_year: int, spec: CRMSpec
) -> pd.Series:
    cities = city_coordinates(train)
    if spec.regions == "fixed":
        return cities["region"]
    return spectral_regions(
        history,
        cities,
        cutoff_year=cutoff_year,
        n_clusters=min(spec.n_clusters, len(cities)),
        window=spec.cluster_window,
        min_years=spec.min_city_years,
        geo_weight=spec.geo_weight,
        geo_scale_km=spec.geo_scale_km,
        seed=spec.seed,
    )


def _city_slopes(
    history: pd.DataFrame,
    cutoff_year: int,
    spec: CRMSpec,
    city_region: pd.Series,
    trends: dict[str, RegionalTrend],
    growth: pd.Series | None = None,
) -> tuple[dict[str, pd.Series], float | None]:
    cities = city_region.index
    slopes = {}
    for metric in TREND_METRICS:
        trend = trends[metric]
        slopes[metric] = (
            city_region.map(trend.table["beta_final"]).astype(float).fillna(trend.pooled)
        )
    gamma = None
    if growth is not None and not growth.empty:
        anomalies = _window_anomalies(history, TEMPERATURE, cutoff_year, spec.trend_spec())
        gamma, centered = urban_gamma(anomalies, slopes[TEMPERATURE], growth)
        offset = (gamma * centered).reindex(cities).fillna(0.0)
        slopes[TEMPERATURE] = (slopes[TEMPERATURE] + offset).clip(lower=0.0)
    if spec.cdd_trend == "regional_slope":
        return slopes, gamma
    # Cities too sparse for their own sensitivity fall back to the (shrunk) CDD slope.
    sensitivity = cdd_per_degree(history, cutoff_year, spec.trend_spec()).reindex(cities)
    if spec.cdd_trend == "sensitivity":
        slopes[CDD] = (sensitivity * slopes[TEMPERATURE]).fillna(slopes[CDD])
        return slopes, gamma
    regional_mean = sensitivity.groupby(city_region).transform("mean")
    share = (sensitivity / regional_mean.where(regional_mean > 0)).fillna(1.0)
    slopes[CDD] = slopes[CDD] * share
    return slopes, gamma


def _residuals(
    history: pd.DataFrame,
    cutoff_year: int,
    spec: CRMSpec,
    city_region: pd.Series,
    city_slopes: dict[str, pd.Series],
) -> pd.DataFrame:
    """Each city's departure from its Layer-2 baseline over the VAR window, with its region."""
    first_year = cutoff_year - spec.var_window + 1
    rows = history.loc[history["year"].between(first_year, cutoff_year)]
    key = [rows["city_id"], rows["metric"]]
    rows = rows.loc[rows.groupby(key)["year"].transform("size") >= spec.min_city_years]
    key = [rows["city_id"], rows["metric"]]
    x = rows["year"] - rows.groupby(key)["year"].transform("mean")
    y = rows["actual_value"] - rows.groupby(key)["actual_value"].transform("mean")
    slope = pd.Series(0.0, index=rows.index)
    for metric in TREND_METRICS:
        mask = rows["metric"] == metric
        slope.loc[mask] = rows.loc[mask, "city_id"].map(city_slopes[metric]).fillna(0.0)
    return pd.DataFrame(
        {
            "region": rows["city_id"].map(city_region),
            "metric": rows["metric"],
            "year": rows["year"],
            "city_id": rows["city_id"],
            "residual": y - slope * x,
        }
    ).dropna(subset=["region"])


def fit_crm(
    train: pd.DataFrame,
    history: pd.DataFrame,
    cutoff_year: int,
    spec: CRMSpec,
    city_static: pd.DataFrame | None = None,
) -> CRMFit:
    """Fit all CRM layers on rows up to ``cutoff_year`` (``history`` is ``train`` in long form).

    ``city_static`` (census table) is needed only when ``spec.urban`` is set; only censuses at
    or before the cut-off are read from it.
    """
    if spec.urban and city_static is None:
        raise ValueError("spec.urban needs the city_static table (see _crm_urban)")
    city_region = _regions(train, history, cutoff_year, spec)
    trends = {
        metric: shrunk_regional_trend(history, metric, cutoff_year, spec, city_region)
        for metric in TREND_METRICS
    }
    growth = (
        urban_growth(city_static, cutoff_year) if spec.urban and city_static is not None else None
    )
    city_slopes, gamma = _city_slopes(history, cutoff_year, spec, city_region, trends, growth)
    var_fit, city_scale = None, None
    if spec.var:
        residuals = _residuals(history, cutoff_year, spec, city_region, city_slopes)
        if spec.var_city_scale:
            spread = residuals.groupby(["city_id", "metric"])["residual"].std()
            city_scale = spread.loc[spread > 0]
            index = pd.MultiIndex.from_frame(residuals[["city_id", "metric"]])
            residuals["residual"] = residuals["residual"] / city_scale.reindex(index).to_numpy()
            residuals = residuals.dropna(subset=["residual"])
        panel = regional_panel(residuals, range(cutoff_year - spec.var_window + 1, cutoff_year + 1))
        var_fit = fit_sparse_var(panel, alpha=spec.var_alpha, seed=spec.seed)
    return CRMFit(
        city_region=city_region,
        trends=trends,
        city_slopes=city_slopes,
        var=var_fit,
        city_scale=city_scale,
        urban_gamma=gamma,
    )


def _trend_rows(
    history: pd.DataFrame,
    metric: str,
    cutoff_year: int,
    years: np.ndarray,
    spec: CRMSpec,
    slopes: pd.Series,
) -> pd.DataFrame:
    """The champion's level-plus-slope paths, with a slope per city."""
    windows = [_levels(history, metric, cutoff_year, n) for n in spec.level_years]
    cities = windows[0].index
    city_slope = slopes.reindex(cities.astype(str)).to_numpy(dtype=float)
    frames = []
    for year in years:
        paths = [
            levels["level"].to_numpy() + city_slope * (year - levels["center"].to_numpy())
            for levels in windows
        ]
        frames.append(
            pd.DataFrame(
                {
                    "city_id": cities.astype(str),
                    "year": int(year),
                    "metric": metric,
                    "predicted_value": np.mean(paths, axis=0),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _station_segments(train: pd.DataFrame) -> pd.DataFrame | None:
    if "Station Segment" not in train.columns:
        return None
    return pd.DataFrame(
        {
            "city_id": train["ID"].astype(str),
            "year": pd.to_numeric(train["Year"]).astype(int),
            "segment": train["Station Segment"],
        }
    ).dropna(subset=["segment"])


def _flat_levels(
    train: pd.DataFrame,
    history: pd.DataFrame,
    flat: pd.DataFrame,
    cutoff_year: int,
    spec: CRMSpec,
    city_region: pd.Series,
) -> pd.DataFrame:
    """Replace the 30-year mean for ``flat_metrics`` where the chosen level method applies."""
    if spec.flat_level == "thirty_year_mean":
        return flat
    flat = flat.copy()
    segments = _station_segments(train) if spec.flat_level == "segment" else None
    for metric in spec.flat_metrics:
        if spec.flat_level == "segment":
            if segments is None:
                continue
            levels = segment_levels(history, segments, metric, cutoff_year, spec.segment_min_years)
        else:
            levels = regional_eb_levels(history, city_region, metric, cutoff_year)
        mask = (flat["metric"] == metric) & flat["city_id"].isin(levels.index)
        flat.loc[mask, "predicted_value"] = flat.loc[mask, "city_id"].map(levels).to_numpy()
    return flat


def _add_var_shift(
    forecast: pd.DataFrame, fit: CRMFit, cutoff_year: int, spec: CRMSpec
) -> pd.DataFrame:
    if fit.var is None or spec.var_damping == 0.0:
        return forecast
    leads = sorted({int(y) - cutoff_year for y in forecast["year"]})
    shifts = fit.var.shifts(leads, spec.var_damping).reset_index()
    shifts = shifts.melt(id_vars=["region", "metric"], var_name="lead", value_name="shift")
    shifts["lead"] = shifts["lead"].astype(int)
    shifts = shifts.loc[shifts["metric"].isin(spec.var_metrics)]
    out = forecast.assign(
        region=forecast["city_id"].map(fit.city_region), lead=forecast["year"] - cutoff_year
    )
    out = out.merge(shifts, on=["region", "metric", "lead"], how="left")
    if fit.city_scale is not None:
        index = pd.MultiIndex.from_frame(out[["city_id", "metric"]])
        out["shift"] = out["shift"] * fit.city_scale.reindex(index).to_numpy()
    out["predicted_value"] = out["predicted_value"] + out["shift"].fillna(0.0)
    return out[list(forecast.columns)]


def crm_forecast(
    train: pd.DataFrame,
    history: pd.DataFrame,
    *,
    cutoff_year: int,
    forecast_years: Iterable[int],
    spec: CRMSpec,
    city_static: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Forecast all four metrics for every known city from ``train`` (wide) and ``history``."""
    validate_climate_history(history, max_year=cutoff_year)
    years = np.asarray(list(forecast_years), dtype=int)
    fit = fit_crm(train, history, cutoff_year, spec, city_static)
    flat = baseline_forecast(
        history, cutoff_year=cutoff_year, forecast_years=years, method=FLAT_METHOD
    )
    flat = flat.loc[~flat["metric"].isin(TREND_METRICS)]
    flat = _flat_levels(train, history, flat, cutoff_year, spec, fit.city_region)
    trends = [
        _trend_rows(history, metric, cutoff_year, years, spec, fit.city_slopes[metric])
        for metric in TREND_METRICS
    ]
    forecast = pd.concat([flat, *trends], ignore_index=True)
    return _add_var_shift(forecast, fit, cutoff_year, spec)


def build_crm(spec: CRMSpec, city_static: pd.DataFrame | None = None) -> Forecaster:
    """A forecaster for the backtest runner and ``build_submission``.

    With ``spec.urban`` the census table is read once, on the first call, unless given here.
    """
    static: dict[str, pd.DataFrame] = {} if city_static is None else {"table": city_static}

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        if spec.urban and "table" not in static:
            static["table"] = load_city_static()
        return crm_forecast(
            train,
            history,
            cutoff_year=cutoff_year,
            forecast_years=forecast_years,
            spec=spec,
            city_static=static.get("table"),
        )

    return forecast


register_kind("crm", CRMSpec, build_crm)
