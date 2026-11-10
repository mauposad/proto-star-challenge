"""Adjustments layered on any base forecaster, each with one pooled parameter fitted in-fold.

* :func:`persistence_forecast` (hypothesis H16 in ``hypotheses.md``): add a lead-specific fraction
  ``phi_h`` of the last year's error of the base model, for the first few leads.
* :func:`skew_shift_forecast` (hypothesis H13): scale the base forecast by ``1 - q * CV^2``, a
  pooled shift from the mean toward the median for right-skewed metrics.

Parameters are fitted on pseudo-origins inside the fold: an origin ``o`` used for lead ``h``
satisfies ``o + h <= cutoff``, and the base model at ``o`` sees only rows up to ``o``.  So the
adjusted forecaster still computes everything from ``train``.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.climate import BASELINE_WINDOW_YEARS, METRICS, annual_to_long
from proto_star.trend import PooledTrendSpec, cdd_per_degree
from proto_star.utils.logging import get_logger

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
_KEY = ["city_id", "year", "metric"]
log = get_logger(__name__)


def _check_metrics(metrics: list[str]) -> None:
    unknown = sorted(set(metrics) - set(METRICS))
    if not metrics or unknown:
        raise ValueError(f"metrics must be a non-empty subset of {list(METRICS)}")


class PersistenceSpec(BaseModel):
    """Settings of a persistence adjustment, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str
    metrics: list[str] = Field(default_factory=lambda: ["annual_avg_temp", "cdd"])
    max_lead: int = Field(default=3, ge=1, le=7)  # phi is zero beyond this lead
    pseudo_origins: int = Field(default=20, ge=3)  # how many past origins fit phi
    clip: tuple[float, float] = (0.0, 1.0)

    @model_validator(mode="after")
    def _check(self) -> PersistenceSpec:
        _check_metrics(self.metrics)
        return self


class SkewShiftSpec(BaseModel):
    """Settings of a skew shift, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str = "thirty_year_mean"
    metrics: list[str] = Field(default_factory=lambda: ["total_precip_in"])
    pseudo_origins: int = Field(default=20, ge=3)
    q_grid: tuple[float, float, int] = (-1.0, 2.0, 61)  # start, stop, number of q values
    # Fixed q skips the in-fold fit (H3: q = 1/3 is the gamma-distribution mean-median gap).
    q: float | None = None

    @model_validator(mode="after")
    def _check(self) -> SkewShiftSpec:
        _check_metrics(self.metrics)
        return self


def _truth(train: pd.DataFrame, cutoff_year: int) -> pd.Series:
    history = annual_to_long(train, cutoff_year=cutoff_year)
    return history.set_index(_KEY)["actual_value"]


def _run(base: Forecaster, train: pd.DataFrame, origin: int, years: list[int]) -> pd.Series:
    rows = base(train.loc[train["Year"] <= origin], origin, years)
    return rows.set_index(_KEY)["predicted_value"]


def _last_year_error(
    base: Forecaster, train: pd.DataFrame, origin: int, truth: pd.Series
) -> pd.Series:
    """Actual minus the base model's one-year-ahead forecast of ``origin``, keyed by city/metric."""
    forecast = _run(base, train, origin - 1, [origin])
    error = (truth.reindex(forecast.index) - forecast).dropna()
    return error.droplevel("year")


def persistence_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: PersistenceSpec,
) -> pd.DataFrame:
    """The base forecast plus ``phi_h`` times the base model's error in the cut-off year."""
    truth = _truth(train, cutoff_year)
    pairs: dict[tuple[str, int], list[tuple[np.ndarray, np.ndarray]]] = {}
    last_origin = cutoff_year - 1
    for origin in range(last_origin - spec.pseudo_origins + 1, last_origin + 1):
        leads = [h for h in range(1, spec.max_lead + 1) if origin + h <= cutoff_year]
        if not leads:
            continue
        error = _last_year_error(base, train, origin, truth)
        ahead = _run(base, train, origin, [origin + h for h in leads])
        miss = (truth.reindex(ahead.index) - ahead).dropna()
        for h in leads:
            future = miss.xs(origin + h, level="year")
            joined = pd.DataFrame({"last": error, "next": future}).dropna()
            metric_of = joined.index.get_level_values("metric")
            for metric in spec.metrics:
                part = joined.loc[metric_of == metric]
                if not part.empty:
                    pairs.setdefault((metric, h), []).append(
                        (part["last"].to_numpy(), part["next"].to_numpy())
                    )

    phi: dict[tuple[str, int], float] = {}
    for key, chunks in pairs.items():
        x = np.concatenate([c[0] for c in chunks])
        y = np.concatenate([c[1] for c in chunks])
        raw = float(x @ y / (x @ x)) if x @ x > 0 else 0.0
        phi[key] = float(np.clip(raw, *spec.clip))
        log.info("persistence %s lead %d at cutoff %d: phi=%.3f", *key, cutoff_year, raw)

    forecast = base(train, cutoff_year, forecast_years).copy()
    error = _last_year_error(base, train, cutoff_year, truth)
    lead = forecast["year"] - cutoff_year
    weights = np.array(
        [phi.get((m, int(h)), 0.0) for m, h in zip(forecast["metric"], lead, strict=True)]
    )
    keys = pd.MultiIndex.from_frame(forecast[["city_id", "metric"]])
    last = error.reindex(keys).fillna(0.0).to_numpy()
    forecast["predicted_value"] = forecast["predicted_value"].to_numpy() + weights * last
    return forecast


def _cv2(train: pd.DataFrame, origin: int) -> pd.Series:
    """Squared coefficient of variation over the 30 calendar years to ``origin``."""
    history = annual_to_long(train.loc[train["Year"] <= origin], cutoff_year=origin)
    window = history.loc[history["year"] > origin - BASELINE_WINDOW_YEARS]
    stats = window.groupby(["city_id", "metric"])["actual_value"].agg(["mean", "std"])
    return ((stats["std"] / stats["mean"]) ** 2).replace([np.inf, -np.inf], np.nan)


def _fit_q(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    horizon: int,
    spec: SkewShiftSpec,
) -> dict[str, float]:
    """One ``q`` per metric, minimising pooled absolute error over in-fold pseudo-origins."""
    truth = _truth(train, cutoff_year)
    samples: dict[str, list[pd.DataFrame]] = {metric: [] for metric in spec.metrics}
    last_origin = cutoff_year - 1
    for origin in range(last_origin - spec.pseudo_origins + 1, last_origin + 1):
        years = [y for y in range(origin + 1, origin + horizon + 1) if y <= cutoff_year]
        ahead = _run(base, train, origin, years).rename("forecast").reset_index()
        ahead = ahead.merge(
            _cv2(train, origin).rename("cv2").reset_index(), on=["city_id", "metric"]
        )
        ahead["actual"] = truth.reindex(pd.MultiIndex.from_frame(ahead[_KEY])).to_numpy()
        ahead = ahead.dropna()
        for metric in spec.metrics:
            samples[metric].append(ahead.loc[ahead["metric"] == metric])

    start, stop, count = spec.q_grid
    grid = np.linspace(start, stop, int(count))
    q: dict[str, float] = {}
    for metric, frames in samples.items():
        rows = pd.concat(frames, ignore_index=True)
        f, c, a = (rows[col].to_numpy() for col in ("forecast", "cv2", "actual"))
        losses = [np.abs(a - f * (1 - value * c)).mean() for value in grid]
        q[metric] = float(grid[int(np.argmin(losses))])
        log.info("skew shift %s at cutoff %d: q=%.3f", metric, cutoff_year, q[metric])
    return q


def skew_shift_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: SkewShiftSpec,
) -> pd.DataFrame:
    """The base forecast times ``1 - q * CV^2`` for ``spec.metrics``; one ``q`` per metric."""
    if spec.q is None:
        q = _fit_q(base, train, cutoff_year, len(forecast_years), spec)
    else:
        q = dict.fromkeys(spec.metrics, spec.q)
    forecast = base(train, cutoff_year, forecast_years).copy()
    cv2 = _cv2(train, cutoff_year)
    keys = pd.MultiIndex.from_frame(forecast[["city_id", "metric"]])
    factor = (
        1
        - forecast["metric"].map(q).fillna(0.0).to_numpy()
        * cv2.reindex(keys).fillna(0.0).to_numpy()
    )
    forecast["predicted_value"] = forecast["predicted_value"].to_numpy() * factor
    return forecast


class CddFromTemperatureSpec(BaseModel):
    """Settings of the H5 CDD forecast, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base: str  # supplies every metric except CDD, and the temperature path
    trend_window: int = Field(default=40, ge=10)  # years used to fit CDD per degree
    min_city_years: int = Field(default=10, ge=3)


def cdd_from_temperature_forecast(
    base: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: CddFromTemperatureSpec,
) -> pd.DataFrame:
    """CDD = its 30-year mean + CDD per degree x (temperature forecast - temperature 30-year mean).

    Hypothesis H5: the part of CDD that annual temperature does not explain is stationary, so its
    level is best estimated over 30 years, while the warming signal comes from the temperature
    forecast.  Cities without a CDD-per-degree estimate keep the base CDD forecast.
    """
    history = annual_to_long(train, cutoff_year=cutoff_year)
    window = history.loc[history["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
    m30 = window.groupby(["city_id", "metric"])["actual_value"].mean()
    sens = cdd_per_degree(
        history,
        cutoff_year,
        PooledTrendSpec(
            level_years=[10], trend_window=spec.trend_window, min_city_years=spec.min_city_years
        ),
    )
    forecast = base(train, cutoff_year, forecast_years).copy()
    temp = forecast.loc[forecast["metric"] == "annual_avg_temp"].set_index(["city_id", "year"])
    is_cdd = forecast["metric"] == "cdd"
    rows = forecast.loc[is_cdd, ["city_id", "year"]]
    t_hat = temp["predicted_value"].reindex(pd.MultiIndex.from_frame(rows)).to_numpy()
    t30 = m30.xs("annual_avg_temp", level="metric").reindex(rows["city_id"]).to_numpy()
    c30 = m30.xs("cdd", level="metric").reindex(rows["city_id"]).to_numpy()
    per_degree = sens.reindex(rows["city_id"]).to_numpy()
    derived = c30 + per_degree * (t_hat - t30)
    keep = np.isfinite(derived)
    values = forecast.loc[is_cdd, "predicted_value"].to_numpy()
    forecast.loc[is_cdd, "predicted_value"] = np.where(keep, derived, values)
    return forecast
