"""Corrections grounded in the candidate error analysis: hypotheses E1-E4 in ``hypotheses.md``.

See ``docs/trials/candidate_error_analysis.md`` for the diagnostics behind each one.

* :func:`anomaly_correction_forecast` (E1, E2): add ``beta_c`` x the city part of the recent
  anomaly, and optionally ``beta_n`` x the national part, to a base forecast.  The anomaly is
  the mean of the last ``window`` valid years minus the 30-year mean.  Its city part is the
  deviation from the cross-city mean.  The betas are fitted by least squares on the base
  model's own errors at in-fold pseudo-origins.  With the 30-year mean as base this is a damped
  anomaly (E1).  With the candidate as base, a negative ``beta_c`` shrinks the city part the
  candidate already carries (E2).
* :func:`trend_scale_forecast` (E3): a pooled-trend forecast whose trend term is scaled by
  ``kappa = 1 + beta``, with ``beta`` fitted on in-fold pseudo-origins.
* :func:`relative_trend_forecast` (E4): the 30-year mean times (1 + g x years from the window's
  centre), where g is a pooled within-city relative slope over a long window.

Every pseudo-origin ``o`` uses only rows up to ``o`` for its inputs, and only targets
``o + h <= cutoff``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.climate import BASELINE_WINDOW_YEARS, MAX_MISSING_DAYS, METRICS, annual_to_long
from proto_star.trend import PooledTrendSpec, cdd_per_degree, pooled_slope, pooled_trend_forecast
from proto_star.utils.logging import get_logger

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
_KEY = ["city_id", "year", "metric"]
HORIZON = 7
log = get_logger(__name__)


def _check_metrics(metrics: list[str]) -> None:
    if not metrics or not set(metrics) <= set(METRICS):
        raise ValueError(f"metrics must be a non-empty subset of {list(METRICS)}")


def _anomalies(
    history: pd.DataFrame,
    origin: int,
    window: int,
    region: pd.Series | None = None,
    diurnal: pd.DataFrame | None = None,
    trend_window: int = 40,
) -> pd.DataFrame:
    """Per metric and city at ``origin``: the recent anomaly's parts used as regressors.

    ``city`` and ``national`` are always present.  With ``region`` (city -> region), ``regional``
    is the leave-one-out regional mean of the city part and ``local`` the remainder.  With
    ``diurnal`` (long rows of ``tmax``/``tmin``), ``tmax_half`` and ``tmin_half`` are half the city
    parts of the Avg Tmax and Avg Tmin anomalies, attached to the temperature rows.
    """

    def parts(rows: pd.DataFrame) -> pd.DataFrame:
        past = rows.loc[rows["year"] <= origin]
        m30 = (
            past.loc[past["year"] > origin - BASELINE_WINDOW_YEARS]
            .groupby(["metric", "city_id"])["actual_value"]
            .mean()
        )
        recent = past.sort_values("year").groupby(["metric", "city_id"]).tail(window)
        anomaly = (recent.groupby(["metric", "city_id"])["actual_value"].mean() - m30).dropna()
        national = anomaly.groupby(level="metric").transform("mean")
        return pd.DataFrame({"city": anomaly - national, "national": national})

    out = parts(history)
    if region is not None:
        groups = pd.MultiIndex.from_arrays(
            [
                out.index.get_level_values("metric"),
                region.reindex(out.index.get_level_values("city_id")).to_numpy(),
            ]
        )
        total = out["city"].groupby(groups).transform("sum").to_numpy()
        count = out["city"].groupby(groups).transform("size").to_numpy()
        loo = np.where(count > 1, (total - out["city"].to_numpy()) / np.maximum(count - 1, 1), 0.0)
        out["regional"] = loo
        out["local"] = out["city"] - loo
    if diurnal is not None:
        halves = (
            parts(diurnal)["city"]
            .reset_index()
            .pivot_table(index="city_id", columns="metric", values="city")
            .reindex(columns=["tmax", "tmin"])
            / 2
        )
        temp = out.index.get_level_values("metric") == "annual_avg_temp"
        cities = out.index.get_level_values("city_id")[temp]
        out["tmax_half"] = np.nan
        out["tmin_half"] = np.nan
        out.loc[temp, "tmax_half"] = halves["tmax"].reindex(cities).to_numpy()
        out.loc[temp, "tmin_half"] = halves["tmin"].reindex(cities).to_numpy()
        # H36: (Tmin - Tmax)/2 contrast; on CDD rows scaled by CDD per degree fitted at origin.
        contrast = halves["tmin"] - halves["tmax"]
        out["contrast"] = np.nan
        out.loc[temp, "contrast"] = contrast.reindex(cities).to_numpy()
        cdd = out.index.get_level_values("metric") == "cdd"
        if cdd.any():
            sens = cdd_per_degree(
                history.loc[history["year"] <= origin],
                origin,
                PooledTrendSpec(level_years=[10], trend_window=trend_window),
            )
            cdd_cities = out.index.get_level_values("city_id")[cdd]
            scaled = contrast.reindex(cdd_cities).to_numpy() * sens.reindex(cdd_cities).to_numpy()
            # Centre across cities so the regressor cannot absorb a common CDD bias (R3-H36-a).
            out.loc[cdd, "contrast"] = scaled - np.nanmean(scaled)
    return out


def _diurnal_history(train: pd.DataFrame, cutoff_year: int) -> pd.DataFrame:
    """Long rows of Avg Tmax and Avg Tmin, each screened by its own missing-days column."""
    frames = []
    for column, missing, name in (
        ("Avg Tmax", "Miss Tmax", "tmax"),
        ("Avg Tmin", "Miss Tmin", "tmin"),
    ):
        values = pd.to_numeric(train[column], errors="coerce")
        valid = values.notna() & np.isfinite(values) & train[missing].le(MAX_MISSING_DAYS)
        valid &= train["Year"] <= cutoff_year
        frames.append(
            pd.DataFrame(
                {
                    "city_id": train.loc[valid, "ID"].astype(str),
                    "year": train.loc[valid, "Year"].astype(int),
                    "metric": name,
                    "actual_value": values.loc[valid].astype(float),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _errors(
    base: Forecaster, train: pd.DataFrame, history: pd.DataFrame, origin: int, last: int
) -> pd.DataFrame:
    """Actual minus the base forecast for years ``origin+1 .. min(origin+7, last)``."""
    years = list(range(origin + 1, min(origin + HORIZON, last) + 1))
    forecast = base(train.loc[train["Year"] <= origin], origin, years)
    truth = history.set_index(_KEY)["actual_value"]
    keyed = forecast.set_index(_KEY)["predicted_value"]
    return (truth.reindex(keyed.index) - keyed).dropna().rename("error").reset_index()


class AnomalyCorrectionSpec(BaseModel):
    """Settings of an E1/E2 correction, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    metrics: list[str]
    window: int = Field(default=15, ge=1)
    national: bool = False  # also fit a coefficient on the national part
    # "region" (H21): separate coefficients for the regional and local parts of the city part.
    # "diurnal" (H23/H32): separate coefficients for the Tmax and Tmin halves of temperature's
    # city part; other metrics keep the single city coefficient.
    # "diurnal_contrast" (H32 one-df form, H36): the city part plus the (Tmin - Tmax)/2 contrast;
    # on CDD rows the contrast is scaled by the city's CDD per degree.
    split: Literal["none", "region", "diurnal", "diurnal_contrast"] = "none"
    # H37: separate coefficients for leads <= lead_split and > lead_split (None: one set).
    lead_split: int | None = Field(default=None, ge=1, le=6)
    # H26: add each regressor times (lead - 4), so the coefficient varies linearly with lead.
    lead_slope: bool = False
    lead_clip: tuple[float, float] = (-0.2, 0.2)
    pseudo_origins: int = Field(default=30, ge=5)
    clip: tuple[float, float] = (-1.0, 1.0)

    @model_validator(mode="after")
    def _check(self) -> AnomalyCorrectionSpec:
        _check_metrics(self.metrics)
        return self


def anomaly_correction_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: AnomalyCorrectionSpec,
) -> pd.DataFrame:
    """The base forecast plus fitted multiples of the recent anomaly's city and national parts."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    region = None
    if spec.split == "region":
        region = train.assign(city_id=train["ID"].astype(str)).groupby("city_id")["region"].first()
    uses_diurnal = spec.split in ("diurnal", "diurnal_contrast")
    diurnal = _diurnal_history(train, cutoff_year) if uses_diurnal else None

    def regressors(metric: str) -> list[str]:
        if spec.split == "region":
            names = ["regional", "local"]
        elif spec.split == "diurnal" and metric == "annual_avg_temp":
            names = ["tmax_half", "tmin_half"]
        elif spec.split == "diurnal_contrast" and metric in ("annual_avg_temp", "cdd"):
            names = ["city", "contrast"]
        else:
            names = ["city"]
        names = [*names, "national"] if spec.national else names
        return [*names, *(f"{n}_lead" for n in names)] if spec.lead_slope else names

    def add_lead_terms(frame: pd.DataFrame, lead: pd.Series) -> pd.DataFrame:
        if not spec.lead_slope:
            return frame
        base_names = [
            c
            for c in ("city", "national", "regional", "local", "tmax_half", "tmin_half", "contrast")
            if c in frame.columns
        ]
        extra = {f"{n}_lead": frame[n].to_numpy() * (lead.to_numpy() - 4.0) for n in base_names}
        return frame.assign(**extra)

    samples = []
    for origin in range(cutoff_year - spec.pseudo_origins, cutoff_year):
        errors = _errors(base, train, history, origin, cutoff_year)
        parts = _anomalies(history, origin, spec.window, region, diurnal).reset_index()
        samples.append(errors.merge(parts, on=["metric", "city_id"]).assign(origin=origin))
    data = pd.concat(samples, ignore_index=True)
    groups = ("all",) if spec.lead_split is None else ("short", "long")

    def group_of(lead: pd.Series) -> pd.Series:
        if spec.lead_split is None:
            return pd.Series("all", index=lead.index)
        return lead.le(spec.lead_split).map({True: "short", False: "long"})

    data["group"] = group_of(data["year"] - data["origin"])
    data = add_lead_terms(data, data["year"] - data["origin"])
    betas: dict[tuple[str, str], dict[str, float]] = {}
    for metric in spec.metrics:
        columns = regressors(metric)
        for group in groups:
            rows = data.loc[(data["metric"] == metric) & (data["group"] == group)]
            # A missing regressor contributes 0 rather than dropping the row, so a model with
            # extra terms still nests its parent on the same rows (R3-H36-b).
            rows = rows.dropna(subset=["error"]).fillna(dict.fromkeys(columns, 0.0))
            coef, *_ = np.linalg.lstsq(
                rows[columns].to_numpy(), rows["error"].to_numpy(), rcond=None
            )
            bounds = [spec.lead_clip if c.endswith("_lead") else spec.clip for c in columns]
            clipped = [float(np.clip(v, lo, hi)) for v, (lo, hi) in zip(coef, bounds, strict=True)]
            betas[(metric, group)] = dict(zip(columns, clipped, strict=True))
            log.info(
                "anomaly correction %s window %d split %s leads %s at cutoff %d: %s",
                metric,
                spec.window,
                spec.split,
                group,
                cutoff_year,
                ", ".join(f"beta_{k}={v:.3f}" for k, v in betas[(metric, group)].items()),
            )

    forecast = base(train, cutoff_year, forecast_years).copy()
    parts = _anomalies(history, cutoff_year, spec.window, region, diurnal)
    forecast_group = group_of(forecast["year"] - cutoff_year)
    for (metric, group), coefs in betas.items():
        selected = (forecast["metric"] == metric) & (forecast_group == group)
        cities = forecast.loc[selected, "city_id"]
        here = pd.DataFrame(parts.xs(metric, level="metric")).reindex(cities)
        lead = (forecast.loc[selected, "year"] - cutoff_year).set_axis(here.index)
        here = add_lead_terms(here, lead)
        shift = sum(coef * here[name].fillna(0.0) for name, coef in coefs.items())
        values = forecast.loc[selected, "predicted_value"].to_numpy()
        forecast.loc[selected, "predicted_value"] = values + np.nan_to_num(
            np.asarray(shift, dtype=float)
        )
    return forecast


class TrendScaleSpec(BaseModel):
    """Settings of an E3 trend multiplier, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    level_years: list[int] = Field(default_factory=lambda: [10, 15], min_length=1)
    trend_window: int = Field(default=40, ge=10)
    cdd_sensitivity: bool = True
    pseudo_origins: int = Field(default=30, ge=5)
    clip: tuple[float, float] = (0.0, 3.0)  # bounds on kappa


def trend_scale_forecast(
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: TrendScaleSpec,
) -> pd.DataFrame:
    """The pooled-trend forecast with its trend term scaled by an in-fold kappa per metric."""
    full = PooledTrendSpec(
        level_years=spec.level_years,
        trend_window=spec.trend_window,
        cdd_sensitivity=spec.cdd_sensitivity,
    )
    flat = full.model_copy(update={"slope_scale": 0.0})

    def run(rows: pd.DataFrame, origin: int, years: list[int], s: PooledTrendSpec) -> pd.Series:
        frame = pooled_trend_forecast(rows, cutoff_year=origin, forecast_years=years, spec=s)
        return frame.set_index(_KEY)["predicted_value"]

    history = annual_to_long(train, cutoff_year=cutoff_year)
    truth = history.set_index(_KEY)["actual_value"]
    samples = []
    for origin in range(cutoff_year - spec.pseudo_origins, cutoff_year):
        years = list(range(origin + 1, min(origin + HORIZON, cutoff_year) + 1))
        past = history.loc[history["year"] <= origin]
        with_trend, without = run(past, origin, years, full), run(past, origin, years, flat)
        frame = pd.DataFrame(
            {"trend": with_trend - without, "error": truth.reindex(with_trend.index) - with_trend}
        )
        samples.append(frame.dropna().reset_index())
    data = pd.concat(samples, ignore_index=True)

    forecast = pooled_trend_forecast(
        history, cutoff_year=cutoff_year, forecast_years=forecast_years, spec=full
    ).set_index(_KEY)
    trend = forecast["predicted_value"] - run(history, cutoff_year, forecast_years, flat)
    for metric in ("annual_avg_temp", "cdd"):
        rows = data.loc[data["metric"] == metric]
        spread = float((rows["trend"] ** 2).sum())
        beta = float((rows["trend"] * rows["error"]).sum() / spread) if spread > 0 else 0.0
        kappa = float(np.clip(1.0 + beta, *spec.clip))
        log.info("trend scale %s at cutoff %d: kappa=%.3f", metric, cutoff_year, kappa)
        is_metric = forecast.index.get_level_values("metric") == metric
        forecast.loc[is_metric, "predicted_value"] += (kappa - 1.0) * trend[is_metric]
    return forecast.reset_index()


class RelativeTrendSpec(BaseModel):
    """Settings of an E4 relative trend, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    metric: str = "total_precip_in"
    trend_window: int = Field(default=60, ge=10)
    min_city_years: int = Field(default=20, ge=3)
    floor: bool = False

    @model_validator(mode="after")
    def _check(self) -> RelativeTrendSpec:
        _check_metrics([self.metric])
        return self


def relative_trend_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: RelativeTrendSpec,
) -> pd.DataFrame:
    """The base forecast with ``spec.metric`` set to m30 x (1 + g x (year - window centre))."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    rows = history.loc[history["metric"] == spec.metric]
    first = cutoff_year - spec.trend_window + 1
    window = rows.loc[rows["year"] >= first]
    relative = window.assign(
        actual_value=window["actual_value"]
        / window.groupby("city_id")["actual_value"].transform("mean")
    )
    slope_spec = PooledTrendSpec(
        level_years=[10], trend_window=spec.trend_window, min_city_years=spec.min_city_years
    )
    g = pooled_slope(relative, spec.metric, cutoff_year, slope_spec)  # floored at 0 there
    if not spec.floor:
        anomalies = relative.assign(
            x=relative["year"] - relative.groupby("city_id")["year"].transform("mean"),
            y=relative["actual_value"]
            - relative.groupby("city_id")["actual_value"].transform("mean"),
        )
        keep = anomalies.groupby("city_id")["year"].transform("size") >= spec.min_city_years
        a = anomalies.loc[keep]
        g = float((a["x"] * a["y"]).sum() / (a["x"] ** 2).sum())
    log.info("relative trend %s at cutoff %d: g=%.5f per year", spec.metric, cutoff_year, g)

    recent = rows.loc[rows["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
    m30 = recent.groupby("city_id")["actual_value"].mean()
    centre = recent.groupby("city_id")["year"].mean()
    forecast = base(train, cutoff_year, forecast_years).copy()
    is_metric = forecast["metric"] == spec.metric
    cities = forecast.loc[is_metric, "city_id"]
    years = forecast.loc[is_metric, "year"].to_numpy(float)
    derived = m30.reindex(cities).to_numpy() * (1 + g * (years - centre.reindex(cities).to_numpy()))
    values = forecast.loc[is_metric, "predicted_value"].to_numpy()
    forecast.loc[is_metric, "predicted_value"] = np.where(np.isfinite(derived), derived, values)
    return forecast
