"""ARIMA per city series, after Lai and Dzombak (2020), paper P13.

Card: ``papers/2020_lai_arima/README.md``.  Per city and metric:

1. take the valid annual values up to the cutoff (gaps dropped, values treated as consecutive);
2. Mann-Kendall trend test: drift is allowed when p < ``drift_alpha``;
3. pick d by repeated KPSS tests and (p, q) by a stepwise AICc search (``auto.arima``);
4. Shapiro-Wilk on the residuals: when p < ``normality_alpha``, Box-Cox transform and repeat 3;
5. refit the chosen order with drift as the trend test said, forecast, back-transform,
   clip non-negative metrics at zero.

A series that is too short, or whose fit fails, gets the 30-year mean.  Counts of each path
are attached to the returned frame as ``frame.attrs["arima_diagnostics"]`` and logged.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from typing import Any

import numpy as np
import pandas as pd

from proto_star.forecasters.registry import Forecaster, register_forecaster

logger = logging.getLogger(__name__)

NON_NEGATIVE_METRICS = ("total_precip_in", "cdd")
# Roots closer than this to the unit circle make auto.arima reject a candidate model.
_ROOT_MARGIN = 1.01


@dataclass(frozen=True)
class ArimaSettings:
    """Hyperparameters shared by every series (from the trial config)."""

    drift_alpha: float = 0.2
    normality_alpha: float = 0.05
    kpss_alpha: float = 0.05
    boxcox: bool = True
    max_d: int = 2
    max_p: int = 5
    max_q: int = 5
    min_obs: int = 10


@dataclass(frozen=True)
class SeriesResult:
    """Forecast for one series and which path produced it."""

    forecast: np.ndarray  # one value per year after the last value; NaN means use the fallback
    status: str  # "arima", "constant", "short", "failed"
    order: tuple[int, int, int] | None = None
    drift: bool = False
    boxcox: bool = False


# ---------- statistical pieces ----------


def mann_kendall_pvalue(values: np.ndarray) -> float:
    """Two-sided Mann-Kendall trend p-value (Kendall's tau against time)."""
    from scipy.stats import kendalltau

    result = kendalltau(np.arange(values.size), values)
    pvalue = float(result.pvalue)
    return 1.0 if np.isnan(pvalue) else pvalue


def kpss_ndiffs(values: np.ndarray, *, alpha: float, max_d: int) -> int:
    """Number of differences until a level KPSS test no longer rejects stationarity."""
    from statsmodels.tools.sm_exceptions import InterpolationWarning
    from statsmodels.tsa.stattools import kpss

    series = values.astype(float)
    d = 0
    while d < max_d:
        if series.size < 3 or np.isclose(np.ptp(series), 0.0):
            break
        lags = int(3 * np.sqrt(series.size) / 13)
        with warnings.catch_warnings():
            # p-values outside the table are clipped to its ends; that is fine for a test.
            warnings.simplefilter("ignore", InterpolationWarning)
            pvalue = kpss(series, regression="c", nlags=lags, result_object=False)[1]
        if pvalue >= alpha:
            break
        series = np.diff(series)
        d += 1
    return d


def boxcox_shift(values: np.ndarray) -> float:
    """Amount added before Box-Cox so the series is positive (the authors' rule)."""
    low, high = float(values.min()), float(values.max())
    positive = values[values > 0]
    if low == 0:
        return float(positive.min()) / 2.0
    if low < 0:
        if high < 0:
            return abs(low + high / 2.0)
        return float(positive.min()) / 2.0 + abs(low)
    return 0.0


def boxcox_lambda(values: np.ndarray, lower: float = -1.0, upper: float = 2.0) -> float:
    """Box-Cox lambda maximising the normal profile log-likelihood on [lower, upper]."""
    from scipy.optimize import minimize_scalar
    from scipy.stats import boxcox_llf

    result = minimize_scalar(
        lambda lam: -float(boxcox_llf(lam, values)), bounds=(lower, upper), method="bounded"
    )
    return float(result.x)


def boxcox(values: np.ndarray, lam: float) -> np.ndarray:
    if lam == 0:
        return np.log(values)
    return (values**lam - 1.0) / lam


def inverse_boxcox(values: np.ndarray, lam: float) -> np.ndarray:
    if lam == 0:
        return np.exp(values)
    base = lam * values + 1.0
    with np.errstate(invalid="ignore"):
        return np.where(base > 0, base ** (1.0 / lam), np.nan)


# ---------- ARIMA fitting ----------


def _trend(d: int, constant: bool) -> str:
    """statsmodels trend spec in the search: mean for d=0, drift for d=1, none for d>=2."""
    if d == 0:
        return "c" if constant else "n"
    return "t" if d == 1 and constant else "n"


def _final_trend(d: int, drift: bool) -> str:
    """Trend of the authors' refit, ``Arima(order, include.drift = drift)``.

    ``include.mean`` defaults to true and only applies when d = 0; R drops drift when d > 1.
    """
    if d == 0:
        return "ct" if drift else "c"
    return "t" if d == 1 and drift else "n"


def _fit(values: np.ndarray, order: tuple[int, int, int], trend: str) -> Any:
    """Fit one ARIMA by state-space MLE, or return None if statsmodels cannot."""
    from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning
    from statsmodels.tsa.arima.model import ARIMA

    # Degenerate candidates (zero variance, zero coefficients) raise numpy floating-point
    # warnings; they end with a non-finite AICc or fail the root check, and are rejected there.
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        # Non-convergence is judged below by the root check and AICc, as auto.arima does.
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", ValueWarning)
        warnings.filterwarnings("ignore", message="Non-stationary starting")
        warnings.filterwarnings("ignore", message="Non-invertible starting")
        try:
            return ARIMA(values, order=order, trend=trend, concentrate_scale=True).fit()
        except (np.linalg.LinAlgError, ValueError):
            return None


def _usable(result: Any, order: tuple[int, int, int]) -> bool:
    if result is None or not np.isfinite(result.aicc):
        return False
    p, _, q = order
    with np.errstate(divide="ignore"):  # a zero coefficient gives an infinite root: fine
        if p and np.any(np.abs(result.arroots) < _ROOT_MARGIN):
            return False
        return not (q and np.any(np.abs(result.maroots) < _ROOT_MARGIN))


def stepwise_order(
    values: np.ndarray, *, allow_drift: bool, settings: ArimaSettings
) -> tuple[tuple[int, int, int], bool, Any]:
    """Hyndman-Khandakar stepwise search (non-seasonal ``auto.arima`` defaults).

    Returns the order, whether it has a constant, and the fitted result (None if none fit).
    """
    d = kpss_ndiffs(values, alpha=settings.kpss_alpha, max_d=settings.max_d)
    allow_constant = d == 0 or (d == 1 and allow_drift)
    fitted: dict[tuple[int, int, bool], tuple[float, Any]] = {}

    def score(p: int, q: int, constant: bool) -> float:
        if p < 0 or q < 0 or p > settings.max_p or q > settings.max_q:
            return np.inf
        if constant and not allow_constant:
            return np.inf
        key = (p, q, constant)
        if key not in fitted:
            order = (p, d, q)
            result = _fit(values, order, _trend(d, constant))
            ic = float(result.aicc) if _usable(result, order) else np.inf
            fitted[key] = (ic, result)
        return fitted[key][0]

    starts = [(2, 2, allow_constant), (0, 0, allow_constant), (1, 0, allow_constant)]
    starts += [(0, 1, allow_constant)]
    if allow_constant:
        starts.append((0, 0, False))
    best = min(starts, key=lambda key: score(*key))
    best_ic = score(*best)
    improved = True
    while improved:
        improved = False
        p, q, constant = best
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]
        neighbours = [(p + dp, q + dq, constant) for dp, dq in moves]
        neighbours.append((p, q, not constant))
        for candidate in neighbours:
            ic = score(*candidate)
            if ic < best_ic:
                best, best_ic, improved = candidate, ic, True
                break
    if not np.isfinite(best_ic):
        return (0, d, 0), False, None
    return (best[0], d, best[1]), best[2], fitted[best][1]


def _residuals(result: Any, d: int) -> np.ndarray:
    # The first d state-space residuals come from the diffuse start, not the model.
    return np.asarray(result.resid, dtype=float)[d:]


def forecast_series(
    values: np.ndarray, steps: int, *, non_negative: bool, settings: ArimaSettings
) -> SeriesResult:
    """Point forecasts 1..``steps`` years after the last value, by the paper's procedure."""
    from scipy.stats import shapiro

    if values.size < settings.min_obs:
        return SeriesResult(np.full(steps, np.nan), "short")
    if np.isclose(np.ptp(values), 0.0):
        return SeriesResult(np.full(steps, values[0]), "constant")

    drift = mann_kendall_pvalue(values) < settings.drift_alpha
    order, _, result = stepwise_order(values, allow_drift=drift, settings=settings)
    if result is None:
        return SeriesResult(np.full(steps, np.nan), "failed", order, drift)

    use_boxcox = False
    if settings.boxcox:
        tested = _residuals(result, order[1]) if any(order) else values
        use_boxcox = tested.size >= 3 and float(shapiro(tested).pvalue) < settings.normality_alpha

    shift, lam = 0.0, 1.0
    data = values
    if use_boxcox:
        shift = boxcox_shift(values)
        lam = boxcox_lambda(values + shift)
        data = boxcox(values + shift, lam)
        order, _, result = stepwise_order(data, allow_drift=drift, settings=settings)
        if result is None:
            return SeriesResult(np.full(steps, np.nan), "failed", order, drift, True)

    if any(order):
        # The authors refit the chosen order with drift as the trend test said.
        refit = _fit(data, order, _final_trend(order[1], drift))
        if refit is not None and np.all(np.isfinite(refit.params)):
            result = refit
    mean = np.asarray(result.forecast(steps), dtype=float)
    if use_boxcox:
        mean = inverse_boxcox(mean, lam) - shift
    if non_negative:
        mean = np.maximum(mean, 0.0)
    if not np.all(np.isfinite(mean)):
        return SeriesResult(np.full(steps, np.nan), "failed", order, drift, use_boxcox)
    return SeriesResult(mean, "arima", order, drift, use_boxcox)


# ---------- forecaster ----------


def _run_task(task: tuple[np.ndarray, int, bool, ArimaSettings]) -> SeriesResult:
    values, steps, non_negative, settings = task
    return forecast_series(values, steps, non_negative=non_negative, settings=settings)


def _map(
    tasks: list[tuple[np.ndarray, int, bool, ArimaSettings]], n_jobs: int
) -> Iterable[SeriesResult]:
    if n_jobs <= 1:
        return [_run_task(task) for task in tasks]
    # spawn, not fork: forking a process that already runs BLAS threads can deadlock.
    with ProcessPoolExecutor(max_workers=n_jobs, mp_context=get_context("spawn")) as pool:
        return list(pool.map(_run_task, tasks, chunksize=8))


def arima_forecast(
    history: pd.DataFrame,
    *,
    cutoff_year: int,
    forecast_years: list[int],
    settings: ArimaSettings,
    history_years: int | None = None,
    metrics: Iterable[str] | None = None,
    n_jobs: int = 1,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """ARIMA forecasts for every city/metric in ``history`` plus counts of each path.

    Metrics not in ``metrics`` and every fallback series use ``current_best``'s per-metric
    baseline and the 30-year mean respectively.  ``history`` must hold only years up to
    ``cutoff_year``.
    """
    from proto_star.backtest import CURRENT_BEST_METHODS
    from proto_star.climate import METRICS, baseline_forecast, metric_ensemble_forecast

    if int(history["year"].max()) > cutoff_year:
        raise ValueError(f"history runs past the cutoff {cutoff_year}")
    modeled = set(METRICS if metrics is None else metrics)
    unknown = sorted(modeled - set(METRICS))
    if unknown:
        raise ValueError(f"unknown metrics {unknown}; use {list(METRICS)}")
    years = np.asarray(forecast_years, dtype=int)

    fit_rows = history.loc[history["metric"].isin(modeled)]
    if history_years is not None:
        fit_rows = fit_rows.loc[fit_rows["year"] > cutoff_year - history_years]
    keys: list[tuple[str, str, int]] = []
    tasks: list[tuple[np.ndarray, int, bool, ArimaSettings]] = []
    for (city_id, metric), group in fit_rows.groupby(["city_id", "metric"], sort=True):
        ordered = group.sort_values("year")
        last_year = int(ordered["year"].iloc[-1])
        steps = int(years.max()) - last_year
        values = ordered["actual_value"].to_numpy(dtype=float)
        keys.append((str(city_id), str(metric), last_year))
        tasks.append((values, steps, str(metric) in NON_NEGATIVE_METRICS, settings))
    results = list(_map(tasks, n_jobs))

    rows: list[pd.DataFrame] = []
    counts: dict[str, int] = {"series": len(results)}
    for (city_id, metric, last_year), result in zip(keys, results, strict=True):
        counts[result.status] = counts.get(result.status, 0) + 1
        counts["boxcox"] = counts.get("boxcox", 0) + int(result.boxcox)
        counts["drift"] = counts.get("drift", 0) + int(result.drift)
        if result.order is not None and result.status == "arima":
            label = f"d{result.order[1]}"
            counts[label] = counts.get(label, 0) + 1
        rows.append(
            pd.DataFrame(
                {
                    "city_id": city_id,
                    "year": years,
                    "metric": metric,
                    "predicted_value": result.forecast[years - last_year - 1],
                }
            )
        )
    columns = ["city_id", "year", "metric", "predicted_value"]
    arima = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=columns)
    arima = arima.dropna(subset=["predicted_value"])

    fallback = baseline_forecast(
        history, cutoff_year=cutoff_year, forecast_years=years, method="thirty_year_mean"
    )
    others = metric_ensemble_forecast(
        history,
        cutoff_year=cutoff_year,
        forecast_years=years,
        methods_by_metric=dict(CURRENT_BEST_METHODS),
    )
    others = others.loc[~others["metric"].isin(modeled)]
    key = ["city_id", "year", "metric"]
    filled = pd.concat([arima, others], ignore_index=True)
    missing = fallback.merge(filled[key], on=key, how="left", indicator=True)
    missing = missing.loc[missing["_merge"] == "left_only", columns]
    counts["fallback_series"] = len(missing.drop_duplicates(["city_id", "metric"]))
    output = pd.concat([filled[columns], missing], ignore_index=True)
    output = output.sort_values(key, ignore_index=True)
    output["year"] = output["year"].astype(int)
    return output, counts


@register_forecaster(
    "arima_lai2020",
    description=(
        "Lai & Dzombak 2020 (P13): per-series ARIMA, KPSS + stepwise AICc order, drift if "
        "Mann-Kendall p<0.2, Box-Cox if residuals non-normal; 30-year-mean fallback"
    ),
    requires=(),
)
def make_arima_lai2020(
    *,
    drift_alpha: float = 0.2,
    normality_alpha: float = 0.05,
    kpss_alpha: float = 0.05,
    boxcox: bool = True,
    max_d: int = 2,
    max_p: int = 5,
    max_q: int = 5,
    min_obs: int = 10,
    history_years: int | None = None,
    metrics: list[str] | None = None,
    n_jobs: int = 1,
) -> Forecaster:
    """Build the P13 forecaster.  Defaults are the paper's settings (full history)."""
    settings = ArimaSettings(
        drift_alpha=drift_alpha,
        normality_alpha=normality_alpha,
        kpss_alpha=kpss_alpha,
        boxcox=boxcox,
        max_d=max_d,
        max_p=max_p,
        max_q=max_q,
        min_obs=min_obs,
    )
    if n_jobs < 1:
        raise ValueError("n_jobs must be at least 1")

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        from proto_star.climate import annual_to_long

        history = annual_to_long(train, cutoff_year=cutoff_year)
        output, counts = arima_forecast(
            history,
            cutoff_year=cutoff_year,
            forecast_years=list(forecast_years),
            settings=settings,
            history_years=history_years,
            metrics=metrics,
            n_jobs=n_jobs,
        )
        logger.info("arima_lai2020 cutoff %s: %s", cutoff_year, counts)
        output.attrs["arima_diagnostics"] = counts
        return output

    return forecast
