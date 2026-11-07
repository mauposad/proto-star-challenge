"""Nonstationary GEV for the hottest day of the year (P23, UCAR extremes course notes).

``hottest_day_temp`` is an annual block maximum of daily Tmax, so the generalized extreme
value distribution is its natural model.  For each city we fit, by maximum likelihood on the
valid years in the last ``window`` calendar years of the fold's training data::

    X_t ~ GEV(mu(t) = mu0 + mu1 * (t - t_bar) / 10, sigma, xi)

and forecast a location statistic of the fitted distribution for each forecast year: the
median by default (the MAE-optimal point forecast), or the mean, or any quantile.  Raw trends
extrapolate badly on this data (docs/trials/baselines_round1.md), so the trend can be shrunk:
the fitted ``mu1`` is multiplied by ``trend_shrink``, either fixed or picked from a list by
hindcasts inside the training years (pseudo-origins ``cutoff - 7``, ``cutoff - 14``, ...).
Every other metric comes from a configurable ``fallback`` forecaster.

Sign convention: ``xi`` is the climate-literature shape (``xi < 0`` bounded upper tail);
``scipy.stats.genextreme`` uses ``c = -xi``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import optimize, stats

from proto_star.climate import METRICS, annual_to_long
from proto_star.forecasters.normals_p02_p04 import fill_missing, series_by_key
from proto_star.forecasters.registry import Forecaster, register_forecaster

GEV_METRIC = "hottest_day_temp"
# Fewest valid years in the window for a GEV fit; shorter series use their sample median.
MIN_GEV_YEARS = 15
_KEY = ["city_id", "year", "metric"]


@dataclass(frozen=True)
class GevFit:
    """Fitted nonstationary GEV.  ``mu1`` is per decade of ``(t - t_bar)``."""

    mu0: float
    mu1: float
    sigma: float
    xi: float
    t_bar: float
    converged: bool

    def location(self, years: np.ndarray, *, statistic: str | float, shrink: float) -> np.ndarray:
        """``statistic`` of the GEV at each year, with the trend multiplied by ``shrink``."""
        mu = self.mu0 + shrink * self.mu1 * (years.astype(float) - self.t_bar) / 10.0
        dist = stats.genextreme(c=-self.xi, loc=0.0, scale=self.sigma)
        if statistic == "median":
            offset = float(dist.median())
        elif statistic == "mean":
            offset = float(dist.mean())
        elif isinstance(statistic, int | float) and 0.0 < float(statistic) < 1.0:
            offset = float(dist.ppf(float(statistic)))
        else:
            raise ValueError(f"statistic must be 'median', 'mean' or a quantile, got {statistic!r}")
        return np.asarray(mu + offset, dtype=float)


def gev_negative_log_likelihood(
    params: np.ndarray, x: np.ndarray, z: np.ndarray, trend: bool
) -> float:
    """GEV negative log-likelihood; ``z`` is ``(t - t_bar) / 10``.  Infeasible points give inf."""
    mu0, mu1, log_sigma, xi = (float(p) for p in params)
    sigma = np.exp(log_sigma)
    mu = mu0 + (mu1 * z if trend else 0.0)
    y = (x - mu) / sigma
    if abs(xi) < 1e-6:
        return float(x.size * log_sigma + np.sum(y + np.exp(-y)))
    w = 1.0 + xi * y
    if np.any(w <= 0.0):
        return float(np.inf)
    return float(x.size * log_sigma + (1.0 + 1.0 / xi) * np.sum(np.log(w)) + np.sum(w ** (-1 / xi)))


def fit_gev(
    years: np.ndarray,
    values: np.ndarray,
    *,
    trend: bool = True,
    xi_bounds: tuple[float, float] = (-0.5, 0.3),
) -> GevFit:
    """Maximum-likelihood GEV with an optional linear location trend (Nelder-Mead, deterministic).

    ``xi`` is kept inside ``xi_bounds``; temperature maxima have a bounded tail and an
    unrestricted shape is poorly identified from 30 points.
    """
    if values.size < 3:
        raise ValueError("fit_gev needs at least 3 values")
    t_bar = float(years.mean())
    z = (years.astype(float) - t_bar) / 10.0
    slope = float(np.polyfit(z, values, 1)[0]) if trend and np.ptp(z) > 0 else 0.0
    resid = values - slope * z
    sigma0 = max(float(np.std(resid)) * np.sqrt(6.0) / np.pi, 1e-3)
    start = np.array([float(resid.mean()) - 0.5772 * sigma0, slope, np.log(sigma0), -0.1])
    lo, hi = xi_bounds

    def objective(params: np.ndarray) -> float:
        if not lo <= params[3] <= hi:
            return float(np.inf)
        return gev_negative_log_likelihood(params, values, z, trend)

    result = optimize.minimize(
        objective,
        start,
        method="Nelder-Mead",
        options={"maxiter": 4000, "xatol": 1e-6, "fatol": 1e-8},
    )
    params = result.x if np.isfinite(result.fun) else start
    return GevFit(
        mu0=float(params[0]),
        mu1=float(params[1]) if trend else 0.0,
        sigma=float(np.exp(params[2])),
        xi=float(params[3]),
        t_bar=t_bar,
        converged=bool(result.success and np.isfinite(result.fun)),
    )


def _window(years: np.ndarray, values: np.ndarray, origin: int, window: int) -> np.ndarray:
    return (years <= origin) & (years > origin - window)


def gev_predict(
    years: np.ndarray,
    values: np.ndarray,
    origin: int,
    targets: np.ndarray,
    *,
    window: int,
    trend: bool,
    statistic: str | float,
    shrinks: Sequence[float],
    xi_bounds: tuple[float, float],
) -> dict[float, np.ndarray]:
    """Forecast ``targets`` from data up to ``origin`` for each shrink factor (one fit)."""
    inside = _window(years, values, origin, window)
    x, t = values[inside], years[inside]
    if x.size < MIN_GEV_YEARS:
        past = values[years <= origin]
        level = float(np.median(past[-window:])) if past.size else float("nan")
        return {s: np.full(len(targets), level) for s in shrinks}
    fit = fit_gev(t, x, trend=trend, xi_bounds=xi_bounds)
    return {s: fit.location(targets, statistic=statistic, shrink=s) for s in shrinks}


def _choose_shrink(
    series: Mapping[tuple[str, str], tuple[np.ndarray, np.ndarray]],
    cutoff_year: int,
    shrinks: Sequence[float],
    *,
    n_origins: int,
    step: int,
    horizon: int,
    settings: Mapping[str, Any],
) -> float:
    """Shrink factor with the lowest pooled MAE over in-train pseudo-origins."""
    totals = dict.fromkeys(shrinks, 0.0)
    count = 0
    for (_, metric), (years, values) in series.items():
        if metric != GEV_METRIC:
            continue
        for j in range(1, n_origins + 1):
            origin = cutoff_year - step * j
            lead = years - origin
            future = (lead >= 1) & (lead <= horizon) & (years <= cutoff_year)
            if not future.any() or (years <= origin).sum() < MIN_GEV_YEARS:
                continue
            preds = gev_predict(years, values, origin, years[future], shrinks=shrinks, **settings)
            for s in shrinks:
                totals[s] += float(np.abs(preds[s] - values[future]).sum())
            count += int(future.sum())
    if count == 0:
        return float(shrinks[0])
    return float(min(shrinks, key=lambda s: (totals[s], list(shrinks).index(s))))


@register_forecaster(
    "gev_hottest_day",
    description="Nonstationary GEV (location trend, shrunk) median for hottest day; "
    "other metrics from a fallback (P23)",
)
def make_gev_hottest_day(
    *,
    window: int = 30,
    trend: bool = True,
    trend_shrink: float | Sequence[float] = 0.5,
    statistic: str | float = "median",
    xi_bounds: Sequence[float] = (-0.5, 0.3),
    n_origins: int = 3,
    step: int = 7,
    fallback: str = "current_best",
    shrink_log: dict[int, float] | None = None,
) -> Forecaster:
    """``trend_shrink`` as a list is chosen per fold by in-train hindcast (one factor for all
    cities).  ``shrink_log`` collects ``{cutoff: chosen shrink}`` for tests."""
    shrinks = (
        [float(s) for s in trend_shrink]
        if isinstance(trend_shrink, Sequence) and not isinstance(trend_shrink, str)
        else [float(trend_shrink)]
    )
    if len(xi_bounds) != 2 or xi_bounds[0] >= xi_bounds[1]:
        raise ValueError(f"xi_bounds must be (low, high), got {xi_bounds}")
    settings: dict[str, Any] = {
        "window": int(window),
        "trend": bool(trend),
        "statistic": statistic,
        "xi_bounds": (float(xi_bounds[0]), float(xi_bounds[1])),
    }

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        series = series_by_key(history.loc[history["metric"] == GEV_METRIC])
        shrink = shrinks[0]
        if trend and len(shrinks) > 1:
            shrink = _choose_shrink(
                series,
                cutoff_year,
                shrinks,
                n_origins=n_origins,
                step=step,
                horizon=len(forecast_years),
                settings=settings,
            )
        if shrink_log is not None:
            shrink_log[cutoff_year] = shrink
        targets = np.asarray(forecast_years, dtype=int)
        frames = []
        for (city_id, metric), (years, values) in series.items():
            preds = gev_predict(years, values, cutoff_year, targets, shrinks=[shrink], **settings)
            frames.append(
                pd.DataFrame(
                    {
                        "city_id": city_id,
                        "year": targets,
                        "metric": metric,
                        "predicted_value": preds[shrink],
                    }
                )
            )
        result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_KEY)
        result = result.loc[np.isfinite(result["predicted_value"].astype(float))]
        from proto_star.backtest import resolve_forecaster

        return fill_missing(
            result, resolve_forecaster(fallback), train, cutoff_year, forecast_years
        )

    return forecast


@register_forecaster(
    "normals_hybrid",
    description="Per metric: any registered forecaster or baseline, e.g. OCN + GEV (P02/P04/P23)",
)
def make_normals_hybrid(*, components: Mapping[str, Mapping[str, Any]]) -> Forecaster:
    """``components`` maps every metric to ``{forecaster: <name>, params: {...}}``.  A name is
    a built-in baseline, ``current_best`` or a registered forecaster."""
    if set(components) != set(METRICS):
        raise ValueError(f"components must map exactly {list(METRICS)}")
    from proto_star.backtest import resolve_forecaster

    parts: dict[str, Forecaster] = {}
    for metric, spec in components.items():
        spec = dict(spec)
        unknown = sorted(set(spec) - {"forecaster", "params"})
        if unknown or "forecaster" not in spec:
            raise ValueError(f"component {metric!r} needs only 'forecaster' and 'params'")
        name = str(spec["forecaster"])
        parts[metric] = (
            resolve_forecaster(
                "_part", variants={"_part": {"forecaster": name, "params": spec.get("params", {})}}
            )
            if spec.get("params")
            else resolve_forecaster(name)
        )

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        frames = []
        for metric, part in parts.items():
            rows = part(train, cutoff_year, forecast_years)
            frames.append(rows.loc[rows["metric"] == metric, [*_KEY, "predicted_value"]])
        return pd.concat(frames, ignore_index=True)

    return forecast
