"""Alternative climate "normals" from P02 (Huang et al. 1996), P03 (Wilks 2013) and P04
(Wilks & Livezey 2013), adapted to the challenge's annual city panel.

Three families of normals, each a flat or gently sloped projection of a city's history:

* **OCN** (optimal climate normal): the mean of the last ``k`` valid years, with ``k`` chosen
  from a candidate list by hindcasts *inside the training years*.
* **EWMA**: an exponentially weighted moving average of the valid years.  A fixed ``alpha`` or
  a candidate list chosen by the same hindcasts ("optimal EWMA").
* **Damped trend**: the recent ``k``-year mean plus a shrunk least-squares slope
  (``phi`` in ``phis`` chosen by hindcast; ``phi = 0`` is the plain ``k``-year mean).

Hindcast selection (P02's recipe): pseudo-origins at ``cutoff - step``, ``cutoff - 2 * step``,
... each forecast the following ``horizon`` years, which all lie on or before the fold cutoff.
The candidate with the lowest pooled absolute error wins, per metric, per region or per city
(``scope``).  Nothing after the fold's cutoff is ever read: ``train`` holds only those years.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from proto_star.climate import METRICS, annual_to_long
from proto_star.forecasters.registry import Forecaster, register_forecaster

# rule(years, values, target_years) -> predictions.  ``years``/``values`` are the valid
# observations up to the origin, oldest first.
Rule = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]
Series = dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]
SCOPES = ("metric", "region", "city")
_KEY = ["city_id", "year", "metric"]
# Fewest valid years a series needs at a pseudo-origin to take part in the hindcast.
MIN_HINDCAST_HISTORY = 5
# Fewest valid years in the trend window before a slope is fitted at all.
MIN_TREND_POINTS = 10


def window_mean_rule(window: int) -> Rule:
    """Mean of the last ``window`` valid years, held flat (P02/P03)."""
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")

    def rule(years: np.ndarray, values: np.ndarray, targets: np.ndarray) -> np.ndarray:
        return np.full(len(targets), float(values[-window:].mean()))

    return rule


def ewma(values: np.ndarray, alpha: float) -> float:
    """Exponentially weighted moving average of ``values`` (oldest first).

    ``m_0 = x_0`` and ``m_i = alpha * x_i + (1 - alpha) * m_{i-1}``; returns the last ``m``.
    Gaps between valid years are ignored: the recursion runs over valid values only.
    """
    if not 0.0 < alpha <= 1.0:
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    if values.size == 0:
        raise ValueError("ewma needs at least one value")
    level = float(values[0])
    for value in values[1:]:
        level = alpha * float(value) + (1.0 - alpha) * level
    return level


def ewma_rule(alpha: float) -> Rule:
    """EWMA level held flat (P04)."""
    ewma(np.array([0.0]), alpha)  # validate alpha early

    def rule(years: np.ndarray, values: np.ndarray, targets: np.ndarray) -> np.ndarray:
        return np.full(len(targets), ewma(values, alpha))

    return rule


def damped_trend_rule(window: int, trend_window: int, phi: float) -> Rule:
    """Recent ``window``-year mean plus ``phi`` times the OLS slope of the last
    ``trend_window`` calendar years, extrapolated from the window's mean year (P04)."""
    if window < 1 or trend_window < 2:
        raise ValueError("window must be >= 1 and trend_window >= 2")

    def rule(years: np.ndarray, values: np.ndarray, targets: np.ndarray) -> np.ndarray:
        level = float(values[-window:].mean())
        center = float(years[-window:].mean())
        recent = years > years[-1] - trend_window
        slope = 0.0
        if phi != 0.0 and recent.sum() >= MIN_TREND_POINTS and np.ptp(years[recent]) > 0:
            slope = float(np.polyfit(years[recent], values[recent], deg=1)[0])
        return level + phi * slope * (targets.astype(float) - center)

    return rule


def series_by_key(history: pd.DataFrame) -> Series:
    """``(city_id, metric) -> (years, values)``, oldest first, from long-form history."""
    ordered = history.sort_values(["city_id", "metric", "year"])
    out: Series = {}
    for (city_id, metric), group in ordered.groupby(["city_id", "metric"], sort=True):
        out[(str(city_id), str(metric))] = (
            group["year"].to_numpy(dtype=int),
            group["actual_value"].to_numpy(dtype=float),
        )
    return out


def hindcast_errors(
    series: Series,
    keys: Sequence[tuple[str, str]],
    cutoff_year: int,
    rule: Rule,
    *,
    n_origins: int,
    step: int,
    horizon: int,
    leads: Sequence[int],
) -> dict[tuple[str, str], tuple[float, int]]:
    """Sum of absolute hindcast errors and count per key, using only years <= ``cutoff_year``."""
    lead_set = set(leads)
    out: dict[tuple[str, str], tuple[float, int]] = {}
    for key in keys:
        years, values = series[key]
        inside = years <= cutoff_year
        years, values = years[inside], values[inside]
        total, count = 0.0, 0
        for j in range(1, n_origins + 1):
            origin = cutoff_year - step * j
            past = years <= origin
            if past.sum() < MIN_HINDCAST_HISTORY:
                continue
            lead = years - origin
            future = (lead >= 1) & (lead <= horizon) & np.isin(lead, list(lead_set))
            if not future.any():
                continue
            predicted = rule(years[past], values[past], years[future])
            total += float(np.abs(predicted - values[future]).sum())
            count += int(future.sum())
        out[key] = (total, count)
    return out


def select_rules(
    series: Series,
    cutoff_year: int,
    candidates: Mapping[str, Rule],
    *,
    metric: str,
    scope: str,
    regions: Mapping[str, str],
    n_origins: int,
    step: int,
    horizon: int,
    leads: Sequence[int],
) -> dict[str, str]:
    """Pick the candidate label with the lowest pooled hindcast MAE for each city of ``metric``.

    Ties go to the earlier candidate.  A region or city with no hindcast points takes the
    metric-wide choice.
    """
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {SCOPES}, got {scope!r}")
    keys = [key for key in series if key[1] == metric]
    labels = list(candidates)
    if len(labels) == 1:
        return {key[0]: labels[0] for key in keys}
    errors = {
        label: hindcast_errors(
            series,
            keys,
            cutoff_year,
            rule,
            n_origins=n_origins,
            step=step,
            horizon=horizon,
            leads=leads,
        )
        for label, rule in candidates.items()
    }

    def best(group: Sequence[tuple[str, str]]) -> str | None:
        scores = []
        for label in labels:
            total = sum(errors[label][key][0] for key in group)
            count = sum(errors[label][key][1] for key in group)
            scores.append(total / count if count else np.inf)
        if not np.isfinite(min(scores)):
            return None
        return labels[int(np.argmin(scores))]

    overall = best(keys) or labels[0]
    if scope == "metric":
        return {key[0]: overall for key in keys}
    if scope == "region":
        choice: dict[str, str] = {}
        by_region: dict[str, list[tuple[str, str]]] = {}
        for key in keys:
            by_region.setdefault(regions.get(key[0], ""), []).append(key)
        for group in by_region.values():
            label = best(group) or overall
            choice.update({key[0]: label for key in group})
        return choice
    return {key[0]: best([key]) or overall for key in keys}


def fill_missing(
    forecast: pd.DataFrame,
    fallback: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
) -> pd.DataFrame:
    """Fill every row ``forecast`` lacks (other metrics, sparse cities) from ``fallback``."""
    backup = fallback(train, cutoff_year, forecast_years)[[*_KEY, "predicted_value"]]
    if forecast.empty:
        return backup.reset_index(drop=True)
    merged = backup.merge(forecast[_KEY], on=_KEY, how="left", indicator=True)
    extra = merged.loc[merged["_merge"] == "left_only"].drop(columns="_merge")
    return pd.concat([forecast[[*_KEY, "predicted_value"]], extra], ignore_index=True)


def _resolve_fallback(name: str) -> Forecaster:
    from proto_star.backtest import resolve_forecaster  # lazy: backtest imports the registry

    return resolve_forecaster(name)


def _check_metrics(metrics: Sequence[str] | None) -> list[str]:
    chosen = list(METRICS if metrics is None else metrics)
    unknown = sorted(set(chosen) - set(METRICS))
    if unknown:
        raise ValueError(f"unknown metrics {unknown}; use {list(METRICS)}")
    return chosen


def selected_normals_forecaster(
    candidates: Mapping[str, Rule],
    *,
    scope: str = "metric",
    n_origins: int = 4,
    step: int = 7,
    horizon: int = 7,
    leads: Sequence[int] | None = None,
    metrics: Sequence[str] | None = None,
    fallback: str = "thirty_year_mean",
    selections: dict[int, dict[str, dict[str, str]]] | None = None,
) -> Forecaster:
    """Forecaster that picks one rule per scope by in-train hindcast and applies it at the cutoff.

    ``selections``, if given, is filled with ``{cutoff: {metric: {city: label}}}`` so tests and
    notes can see what was chosen.
    """
    if not candidates:
        raise ValueError("at least one candidate rule is needed")
    chosen_metrics = _check_metrics(metrics)
    lead_list = list(range(1, horizon + 1)) if leads is None else [int(x) for x in leads]

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        series = series_by_key(history)
        regions: dict[str, str] = {}
        if scope == "region" and "region" in train.columns:
            pairs = train[["ID", "region"]].dropna().drop_duplicates("ID")
            regions = dict(zip(pairs["ID"].astype(str), pairs["region"].astype(str), strict=True))
        targets = np.asarray(forecast_years, dtype=int)
        frames: list[pd.DataFrame] = []
        for metric in chosen_metrics:
            choice = select_rules(
                series,
                cutoff_year,
                candidates,
                metric=metric,
                scope=scope,
                regions=regions,
                n_origins=n_origins,
                step=step,
                horizon=horizon,
                leads=lead_list,
            )
            if selections is not None:
                selections.setdefault(cutoff_year, {})[metric] = dict(choice)
            for city_id, label in choice.items():
                years, values = series[(city_id, metric)]
                frames.append(
                    pd.DataFrame(
                        {
                            "city_id": city_id,
                            "year": targets,
                            "metric": metric,
                            "predicted_value": candidates[label](years, values, targets),
                        }
                    )
                )
        result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_KEY)
        return fill_missing(
            result,
            _resolve_fallback(fallback),
            train,
            cutoff_year,
            forecast_years,
        )

    return forecast


@register_forecaster(
    "ocn_normal",
    description="Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03)",
)
def make_ocn_normal(
    *,
    windows: Sequence[int] = (5, 7, 10, 12, 15, 20, 25, 30),
    scope: str = "metric",
    n_origins: int = 4,
    step: int = 7,
    leads: Sequence[int] | None = None,
    metrics: Sequence[str] | None = None,
    fallback: str = "thirty_year_mean",
) -> Forecaster:
    candidates = {f"k{int(k)}": window_mean_rule(int(k)) for k in windows}
    return selected_normals_forecaster(
        candidates,
        scope=scope,
        n_origins=n_origins,
        step=step,
        leads=leads,
        metrics=metrics,
        fallback=fallback,
    )


@register_forecaster(
    "ewma_normal",
    description="Exponentially weighted moving average; alpha fixed or picked by hindcast (P04)",
)
def make_ewma_normal(
    *,
    alpha: float | None = 0.1,
    alphas: Sequence[float] | None = None,
    scope: str = "metric",
    n_origins: int = 4,
    step: int = 7,
    leads: Sequence[int] | None = None,
    metrics: Sequence[str] | None = None,
    fallback: str = "thirty_year_mean",
) -> Forecaster:
    grid = [float(a) for a in alphas] if alphas else [float(alpha if alpha is not None else 0.1)]
    candidates = {f"a{a:g}": ewma_rule(a) for a in grid}
    return selected_normals_forecaster(
        candidates,
        scope=scope,
        n_origins=n_origins,
        step=step,
        leads=leads,
        metrics=metrics,
        fallback=fallback,
    )


@register_forecaster(
    "damped_trend_normal",
    description="Recent k-year mean plus a damped OLS slope, damping picked by hindcast (P04)",
)
def make_damped_trend_normal(
    *,
    window: int = 10,
    trend_window: int = 30,
    phis: Sequence[float] = (0.0, 0.25, 0.5, 1.0),
    scope: str = "metric",
    n_origins: int = 4,
    step: int = 7,
    leads: Sequence[int] | None = None,
    metrics: Sequence[str] | None = None,
    fallback: str = "thirty_year_mean",
) -> Forecaster:
    candidates = {
        f"phi{float(p):g}": damped_trend_rule(int(window), int(trend_window), float(p))
        for p in phis
    }
    return selected_normals_forecaster(
        candidates,
        scope=scope,
        n_origins=n_origins,
        step=step,
        leads=leads,
        metrics=metrics,
        fallback=fallback,
    )


def optimal_normal_candidates(windows: Sequence[int], alphas: Sequence[float]) -> dict[str, Rule]:
    """k-year means then EWMAs, in that order (ties go to the earlier one)."""
    candidates: dict[str, Rule] = {f"k{int(k)}": window_mean_rule(int(k)) for k in windows}
    candidates.update({f"a{float(a):g}": ewma_rule(float(a)) for a in alphas})
    return candidates


@register_forecaster(
    "optimal_normal",
    description="Picks among k-year means and EWMAs per metric by in-train hindcast (P02/P04)",
)
def make_optimal_normal(
    *,
    windows: Sequence[int] = (5, 10, 15, 20, 30),
    alphas: Sequence[float] = (0.03, 0.05, 0.1, 0.2),
    scope: str = "metric",
    n_origins: int = 4,
    step: int = 7,
    leads: Sequence[int] | None = None,
    metrics: Sequence[str] | None = None,
    fallback: str = "thirty_year_mean",
) -> Forecaster:
    return selected_normals_forecaster(
        optimal_normal_candidates(windows, alphas),
        scope=scope,
        n_origins=n_origins,
        step=step,
        leads=leads,
        metrics=metrics,
        fallback=fallback,
    )
