"""Score any forecast function the same way, and turn the winner into a submission.

A forecaster is a plain function ``forecaster(train, cutoff_year, forecast_years)``
returning rows of ``city_id, year, metric, predicted_value``.  ``train`` holds only master
rows up to ``cutoff_year``, so anything computed from it inside the function is safe for
that fold.  Work out everything from ``train``: reading data from anywhere else inside a
forecaster defeats this protection, and nothing here can detect it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import numpy as np
import pandas as pd

from proto_star.climate import (
    BASELINE_METHODS,
    DEFAULT_CUTOFFS,
    FORECAST_CUTOFF,
    FORECAST_YEARS,
    METRICS,
    SUBMISSION_COLUMNS,
    ClimateDataError,
    ClimateSubmissionError,
    annual_to_long,
    assert_weather_cutoff,
    baseline_forecast,
    metric_ensemble_forecast,
    official_score,
    validate_submission,
)
from proto_star.trend import PooledTrendSpec, pooled_trend_forecast

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]

DEFAULT_HORIZON = 7
# Forecast lead in years. 1-3 mirrors the Live Score (2019-2021), 4-7 the Final Score (2022-2025).
WINDOWS = {"all": (1, 7), "years_1_3": (1, 3), "years_4_7": (4, 7)}
CURRENT_BEST = "current_best"
CURRENT_BEST_METHODS = {
    "annual_avg_temp": "ten_year_mean",
    "total_precip_in": "thirty_year_mean",
    "hottest_day_temp": "thirty_year_mean",
    "cdd": "ten_year_mean",
}
_KEY = ["city_id", "year", "metric"]


def baseline_forecaster(method: str) -> Forecaster:
    """Wrap a built-in baseline, such as ``ten_year_mean``, as a forecaster."""

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        return baseline_forecast(
            history, cutoff_year=cutoff_year, forecast_years=forecast_years, method=method
        )

    return forecast


def ensemble_forecaster(methods: Mapping[str, str] = CURRENT_BEST_METHODS) -> Forecaster:
    """Wrap a metric-specific ensemble of baselines as a forecaster."""

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        return metric_ensemble_forecast(
            history,
            cutoff_year=cutoff_year,
            forecast_years=forecast_years,
            methods_by_metric=dict(methods),
        )

    return forecast


def pooled_trend_forecaster(spec: PooledTrendSpec) -> Forecaster:
    """Wrap a pooled-trend model as a forecaster."""

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        if spec.slope_within == "segment":
            segments = train[["ID", "Year", "Station Segment"]].rename(
                columns={"ID": "city_id", "Year": "year", "Station Segment": "segment"}
            )
            segments["city_id"] = segments["city_id"].astype(str)
            history = history.merge(segments, on=["city_id", "year"], how="left")
        return pooled_trend_forecast(
            history, cutoff_year=cutoff_year, forecast_years=forecast_years, spec=spec
        )

    return forecast


def resolve_forecaster(
    name: str,
    ensembles: Mapping[str, Mapping[str, str]] | None = None,
    pooled_trends: Mapping[str, PooledTrendSpec] | None = None,
) -> Forecaster:
    """Look up a forecaster by the name used in trial configs.

    ``current_best`` is the team's current ensemble, a built-in baseline name is that
    baseline, anything in ``ensembles`` is a metric-to-baseline mapping from the config, and
    anything in ``pooled_trends`` is a pooled-trend model from the config.
    """
    if pooled_trends and name in pooled_trends:
        return pooled_trend_forecaster(pooled_trends[name])
    if ensembles and name in ensembles:
        mapping = dict(ensembles[name])
        if set(mapping) != set(METRICS):
            raise ValueError(f"ensemble {name!r} must map exactly {list(METRICS)}")
        unknown = sorted(set(mapping.values()) - set(BASELINE_METHODS))
        if unknown:
            raise ValueError(f"ensemble {name!r} uses unknown baselines {unknown}")
        return ensemble_forecaster(mapping)
    if name == CURRENT_BEST:
        return ensemble_forecaster()
    if name in BASELINE_METHODS:
        return baseline_forecaster(name)
    raise ValueError(
        f"unknown forecaster {name!r}; use {CURRENT_BEST!r}, one of {list(BASELINE_METHODS)}, "
        "or define it under `ensembles` or `pooled_trends` in the trial config"
    )


def _check_coverage(
    forecast: pd.DataFrame, required: pd.DataFrame, years: list[int], label: str
) -> None:
    """Reject forecasts that skip scored rows, which would make a method look better."""
    missing_columns = sorted(set(SUBMISSION_COLUMNS) - set(forecast.columns))
    if missing_columns:
        raise ClimateDataError(f"{label}: forecast is missing columns {missing_columns}")
    outside = sorted(set(forecast["year"]) - set(years))
    if outside:
        raise ClimateDataError(f"{label}: forecast has years outside the fold: {outside[:5]}")
    merged = required[_KEY].merge(
        forecast[_KEY].drop_duplicates(), on=_KEY, how="left", indicator=True
    )
    skipped = merged.loc[merged["_merge"] == "left_only", _KEY]
    if not skipped.empty:
        example = skipped.iloc[0].to_dict()
        raise ClimateDataError(
            f"{label}: forecast skips {len(skipped)} scored rows, for example {example}"
        )


def backtest_forecaster(
    forecaster: Forecaster,
    master: pd.DataFrame,
    *,
    name: str = "forecast",
    cutoffs: Iterable[int] = DEFAULT_CUTOFFS,
    horizon: int = DEFAULT_HORIZON,
) -> pd.DataFrame:
    """Score a forecaster at each origin, with one row per origin and forecast window.

    ``score`` is the official floored score.  ``raw_score`` is the same number without the
    floor at zero, so two methods can still be compared when both lose to the reference.
    Every method is scored on the same rows: all those with an actual value and a reference.
    """
    history = annual_to_long(master)
    rows: list[dict[str, float | int | str]] = []
    for cutoff in cutoffs:
        years = list(range(cutoff + 1, cutoff + horizon + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        assert_weather_cutoff(train, name="training fold", cutoff_year=cutoff)
        forecast = forecaster(train, cutoff, years)

        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        )
        truth = history.loc[history["year"].isin(years)].merge(reference[_KEY], on=_KEY)
        _check_coverage(forecast, truth, years, f"{name} at cutoff {cutoff}")

        for window, (first_lead, last_lead) in WINDOWS.items():
            lead = truth["year"] - cutoff
            window_truth = truth.loc[lead.between(first_lead, last_lead)]
            if window_truth.empty:
                continue
            score = official_score(forecast, window_truth, reference)
            row: dict[str, float | int | str] = {
                "method": name,
                "cutoff_year": cutoff,
                "window": window,
                "score": score.score,
                "raw_score": 100.0 * sum(score.skill.values()) / len(METRICS),
                "n_rows": score.n_rows,
            }
            for metric in METRICS:
                row[f"{metric}_mae"] = score.mae[metric]
                row[f"{metric}_skill"] = score.skill[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def compare_forecasters(
    forecasters: Mapping[str, Forecaster],
    master: pd.DataFrame,
    *,
    cutoffs: Iterable[int] = DEFAULT_CUTOFFS,
    horizon: int = DEFAULT_HORIZON,
) -> pd.DataFrame:
    """Backtest several named forecasters on identical folds."""
    origins = list(cutoffs)
    return pd.concat(
        [
            backtest_forecaster(forecaster, master, name=name, cutoffs=origins, horizon=horizon)
            for name, forecaster in forecasters.items()
        ],
        ignore_index=True,
    )


def summarize_backtest(results: pd.DataFrame, *, baseline: str) -> pd.DataFrame:
    """Average each method across origins and count the origins where it beats ``baseline``.

    Means alone can hide one lucky origin, so read ``origins_beating_baseline`` alongside
    them.  Skill columns are shown as percentages.
    """
    if baseline not in set(results["method"]):
        raise ValueError(f"baseline {baseline!r} is not in the results")
    skill_columns = [f"{metric}_skill" for metric in METRICS]
    summary = results.groupby(["window", "method"])[["raw_score", *skill_columns]].mean()
    summary[skill_columns] = summary[skill_columns] * 100.0

    reference = results.loc[results["method"] == baseline]
    reference = reference[["window", "cutoff_year", "raw_score"]].rename(
        columns={"raw_score": "baseline_raw_score"}
    )
    paired = results.merge(reference, on=["window", "cutoff_year"])
    paired["wins"] = paired["raw_score"] > paired["baseline_raw_score"]
    summary["origins_beating_baseline"] = paired.groupby(["window", "method"])["wins"].sum()
    summary["origins"] = paired.groupby(["window", "method"])["wins"].size()
    return summary.round(2).reset_index()


def build_submission(forecaster: Forecaster, master: pd.DataFrame) -> pd.DataFrame:
    """Run a forecaster on all data through 2018 and validate the 5,880-row result."""
    train = master.loc[master["Year"] <= FORECAST_CUTOFF].copy()
    assert_weather_cutoff(master, name="master")
    forecast = forecaster(train, FORECAST_CUTOFF, list(FORECAST_YEARS))
    missing_columns = sorted(set(SUBMISSION_COLUMNS) - set(forecast.columns))
    if missing_columns:
        raise ClimateSubmissionError(f"forecast is missing columns {missing_columns}")
    submission = forecast[SUBMISSION_COLUMNS].sort_values(_KEY, ignore_index=True)
    validate_submission(submission, master["ID"].astype(str).unique())
    return submission


def fold_rows(
    forecaster: Forecaster,
    master: pd.DataFrame,
    *,
    name: str = "forecast",
    cutoffs: Iterable[int] = DEFAULT_CUTOFFS,
    horizon: int = DEFAULT_HORIZON,
) -> pd.DataFrame:
    """Every scored row of every fold, with the forecast, the actual value and the reference.

    The rows are exactly those :func:`backtest_forecaster` scores, so paired comparisons built
    from them (see :func:`paired_year_bootstrap`) reproduce the official differences.
    """
    history = annual_to_long(master)
    frames = []
    for cutoff in cutoffs:
        years = list(range(cutoff + 1, cutoff + horizon + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        assert_weather_cutoff(train, name="training fold", cutoff_year=cutoff)
        forecast = forecaster(train, cutoff, years)
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "reference_value"})
        truth = history.loc[history["year"].isin(years)].merge(reference, on=_KEY)
        _check_coverage(forecast, truth, years, f"{name} at cutoff {cutoff}")
        rows = truth.merge(forecast[[*_KEY, "predicted_value"]], on=_KEY, how="left")
        frames.append(rows.assign(cutoff_year=cutoff))
    return pd.concat(frames, ignore_index=True)


def paired_year_bootstrap(
    rows_a: pd.DataFrame,
    rows_b: pd.DataFrame,
    *,
    window: str = "all",
    metrics: Iterable[str] = METRICS,
    n_boot: int = 4000,
    seed: int = 0,
) -> dict[str, float]:
    """Difference in mean raw score, b minus a, with a 95% interval from resampling years.

    Each fold's skill difference is a sum of per-year contributions,
    ``(|e_a| - |e_b|) / (n * MAE_ref)`` summed over that year's rows.  Errors are strongly
    correlated across cities within a year, so the forecast year (within its fold) is the
    resampling unit.  Years are resampled with replacement within each fold.  ``n`` and
    ``MAE_ref`` are held fixed.  Restrict ``metrics`` to get the difference in one metric's
    skill (times 100 / number of metrics).
    """
    chosen = list(metrics)
    keys = ["cutoff_year", *_KEY]
    paired = rows_a[[*keys, "actual_value", "reference_value", "predicted_value"]].merge(
        rows_b[[*keys, "predicted_value"]], on=keys, suffixes=("_a", "_b"), validate="1:1"
    )
    first, last = WINDOWS[window]
    lead = paired["year"] - paired["cutoff_year"]
    paired = paired.loc[lead.between(first, last) & paired["metric"].isin(chosen)].copy()
    paired["gain"] = (paired["predicted_value_a"] - paired["actual_value"]).abs() - (
        paired["predicted_value_b"] - paired["actual_value"]
    ).abs()
    paired["ref_error"] = (paired["reference_value"] - paired["actual_value"]).abs()
    by_fold_metric = paired.groupby(["cutoff_year", "metric"])
    scale = by_fold_metric["ref_error"].transform("sum")  # n * MAE_ref
    n_folds = paired["cutoff_year"].nunique()
    paired["contribution"] = 100.0 * paired["gain"] / scale / (n_folds * len(chosen))
    per_year = paired.groupby(["cutoff_year", "year"])["contribution"].sum()

    rng = np.random.default_rng(seed)
    draws = np.zeros(n_boot)
    for _, values in per_year.groupby(level="cutoff_year"):
        array = values.to_numpy()
        picks = rng.integers(0, len(array), size=(n_boot, len(array)))
        draws += array[picks].sum(axis=1)
    low, high = np.percentile(draws, [2.5, 97.5])
    return {
        "difference": float(per_year.sum()),
        "low": float(low),
        "high": float(high),
        "share_not_better": float((draws <= 0).mean()),
        "years": float(len(per_year)),
    }
