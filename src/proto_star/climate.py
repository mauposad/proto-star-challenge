"""Climate-specific tooling for the CMU ProtoStar challenge.

The generic training pipeline remains useful for tabular experiments.  This
module owns the challenge's panel structure, temporal cutoff, quality rule,
official relative-skill score, and exact submission contract.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

METRICS = (
    "annual_avg_temp",
    "total_precip_in",
    "hottest_day_temp",
    "cdd",
)
SUBMISSION_COLUMNS = ["city_id", "year", "metric", "predicted_value"]
FORECAST_CUTOFF = 2018
FORECAST_YEARS = tuple(range(2019, 2026))
MAX_MISSING_DAYS = 10
BASELINE_WINDOW_YEARS = 30
BASELINE_METHODS = (
    "last_valid_year",
    "ten_year_mean",
    "thirty_year_mean",
    "linear_trend",
)


class ClimateDataError(ValueError):
    """The climate input cannot safely be used for challenge forecasting."""


class ClimateSubmissionError(ValueError):
    """A climate submission violates the organizer's file contract."""


@dataclass(frozen=True)
class ClimateScore:
    """Official score and its metric-level MAE and skill diagnostics."""

    score: float
    mae: dict[str, float]
    skill: dict[str, float]
    n_rows: int


_METRIC_SPECS: dict[str, tuple[str, tuple[str, ...]]] = {
    "annual_avg_temp": ("Avg Temp", ("Miss Tmax", "Miss Tmin")),
    "total_precip_in": ("ToT Prcp", ("Miss Prcp",)),
    "hottest_day_temp": ("Max Tmax", ("Miss Tmax",)),
    "cdd": ("cdd", ("Miss Tmax", "Miss Tmin")),
}


def assert_weather_cutoff(
    table: pd.DataFrame, *, name: str, cutoff_year: int = FORECAST_CUTOFF
) -> None:
    """Stop if a weather table holds observations after the challenge cutoff.

    Run every weather input through this, including external sources.  A table with
    no recognizable date column fails rather than passes: static metadata should
    simply not be sent here, so an unchecked weather table cannot slip through.
    """
    columns = [column for column in ("Year", "year", "Date", "date") if column in table.columns]
    if not columns:
        raise ClimateDataError(f"{name} has no Year or Date column to check against the cutoff")
    for column in columns:
        if column.lower() == "year":
            years = pd.to_numeric(table[column], errors="coerce")
        else:
            years = pd.to_datetime(table[column], errors="coerce").dt.year
        if (years.isna() & table[column].notna()).any():
            raise ClimateDataError(f"{name} has unparseable values in column {column!r}")
        last = years.max()
        if pd.notna(last) and int(last) > cutoff_year:
            raise ClimateDataError(
                f"{name} contains year {int(last)}, after allowed cutoff {cutoff_year}"
            )


def metric_valid_mask(annual: pd.DataFrame, metric: str) -> pd.Series:
    """Rows of ``annual`` whose ``metric`` passes the organizer's missing-days rule."""
    value_column, missing_columns = _METRIC_SPECS[metric]
    values = pd.to_numeric(annual[value_column], errors="coerce")
    valid = values.notna() & np.isfinite(values)
    for column in missing_columns:
        valid &= pd.to_numeric(annual[column], errors="coerce").le(MAX_MISSING_DAYS)
    return valid


def annual_to_long(annual: pd.DataFrame, *, cutoff_year: int = FORECAST_CUTOFF) -> pd.DataFrame:
    """Melt annual indices to one quality-screened city/year/metric value per row.

    Every retained value meets the organizer's missing-days threshold.  Input
    years after ``cutoff_year`` are rejected instead of silently filtered, so a
    changed source cannot introduce forbidden observations into an experiment.
    """
    required = {"ID", "Year"}
    for value_column, missing_columns in _METRIC_SPECS.values():
        required.add(value_column)
        required.update(missing_columns)
    missing = sorted(required - set(annual.columns))
    if missing:
        raise ClimateDataError(f"annual indices are missing required columns: {missing}")

    year = pd.to_numeric(annual["Year"], errors="coerce")
    if year.isna().any():
        raise ClimateDataError("annual indices contain non-numeric years")
    if int(year.max()) > cutoff_year:
        raise ClimateDataError(
            f"annual indices contain year {int(year.max())}, after allowed cutoff {cutoff_year}"
        )

    frames: list[pd.DataFrame] = []
    for metric, (value_column, _) in _METRIC_SPECS.items():
        values = pd.to_numeric(annual[value_column], errors="coerce")
        valid = metric_valid_mask(annual, metric)
        frames.append(
            pd.DataFrame(
                {
                    "city_id": annual.loc[valid, "ID"].astype(str),
                    "year": year.loc[valid].astype(int),
                    "metric": metric,
                    "actual_value": values.loc[valid].astype(float),
                }
            )
        )

    result = pd.concat(frames, ignore_index=True).sort_values(
        ["city_id", "metric", "year"], ignore_index=True
    )
    validate_climate_history(result, max_year=cutoff_year)
    return result


def validate_climate_history(history: pd.DataFrame, *, max_year: int | None = None) -> None:
    """Validate long-form quality-screened training history."""
    required = {"city_id", "year", "metric", "actual_value"}
    missing = sorted(required - set(history.columns))
    if missing:
        raise ClimateDataError(f"climate history is missing required columns: {missing}")
    if history.empty:
        raise ClimateDataError("climate history is empty")
    if not set(history["metric"]).issubset(METRICS):
        unknown = sorted(set(history["metric"]) - set(METRICS))
        raise ClimateDataError(f"climate history has unknown metrics: {unknown}")
    year = pd.to_numeric(history["year"], errors="coerce")
    if year.isna().any():
        raise ClimateDataError("climate history contains non-numeric years")
    if max_year is not None and int(year.max()) > max_year:
        raise ClimateDataError(f"climate history must end on or before {max_year}")
    value = pd.to_numeric(history["actual_value"], errors="coerce")
    if value.isna().any() or not np.isfinite(value).all():
        raise ClimateDataError("climate history contains missing or non-finite actual values")
    key = ["city_id", "year", "metric"]
    if history.duplicated(key).any():
        raise ClimateDataError("climate history contains duplicate city/year/metric values")


def _predict_group(
    group: pd.DataFrame, years: np.ndarray, method: str, fallback: float, cutoff_year: int
) -> np.ndarray:
    ordered = group.sort_values("year")
    all_values = ordered["actual_value"].to_numpy(dtype=float)
    if all_values.size == 0:
        return np.full(len(years), fallback)
    if method == "last_valid_year":
        return np.full(len(years), all_values[-1])
    if method == "ten_year_mean":
        return np.full(len(years), all_values[-10:].mean())

    # The organizers' 30-year baselines cover calendar years (1989-2018 for the real
    # forecast), not the last 30 valid years. Sparse cities must not reach back decades.
    recent = ordered.loc[ordered["year"] > cutoff_year - BASELINE_WINDOW_YEARS]
    if recent.empty:
        recent = ordered.tail(BASELINE_WINDOW_YEARS)
    values = recent["actual_value"].to_numpy(dtype=float)
    observed_years = recent["year"].to_numpy(dtype=float)
    if method == "thirty_year_mean":
        return np.full(len(years), values.mean())
    if method == "linear_trend":
        if values.size < 2 or np.isclose(np.ptp(observed_years), 0):
            return np.full(len(years), values.mean())
        slope, intercept = np.polyfit(observed_years, values, deg=1)
        return slope * years + intercept
    raise ValueError(f"unknown climate baseline {method!r}")


def baseline_forecast(
    history: pd.DataFrame,
    *,
    cutoff_year: int,
    forecast_years: Iterable[int],
    method: str,
) -> pd.DataFrame:
    """Forecast each known city and metric using a leakage-safe baseline."""
    validate_climate_history(history)
    years = np.asarray(list(forecast_years), dtype=int)
    if years.size == 0 or np.any(years <= cutoff_year):
        raise ValueError("forecast years must be non-empty and strictly after the cutoff")

    train = history.loc[history["year"] <= cutoff_year].copy()
    if train.empty:
        raise ClimateDataError(f"no climate history is available on or before {cutoff_year}")
    fallbacks = train.groupby("metric")["actual_value"].mean()
    outputs: list[pd.DataFrame] = []
    for (city_id, metric), group in train.groupby(["city_id", "metric"], sort=True):
        city_key = str(city_id)
        metric_key = str(metric)
        fallback = float(fallbacks[metric_key])
        predictions = _predict_group(group, years, method, fallback, cutoff_year)
        outputs.append(
            pd.DataFrame(
                {
                    "city_id": city_key,
                    "year": years,
                    "metric": metric_key,
                    "predicted_value": predictions,
                }
            )
        )
    result = pd.concat(outputs, ignore_index=True)
    if not np.isfinite(result["predicted_value"]).all():
        raise ClimateDataError("baseline produced non-finite predictions")
    return result


def official_score(
    predictions: pd.DataFrame, truth: pd.DataFrame, reference_predictions: pd.DataFrame
) -> ClimateScore:
    """Compute the published relative-skill score against a 30-year reference."""
    key = ["city_id", "year", "metric"]
    predicted = _prediction_frame(predictions, "predicted_value")
    reference = _prediction_frame(reference_predictions, "reference_value")
    actual = truth[[*key, "actual_value"]].copy()
    scored = actual.merge(predicted, on=key, how="inner").merge(reference, on=key, how="inner")
    if scored.empty:
        raise ClimateDataError("no overlapping rows are available for scoring")

    mae: dict[str, float] = {}
    skill: dict[str, float] = {}
    for metric in METRICS:
        rows = scored.loc[scored["metric"] == metric]
        if rows.empty:
            raise ClimateDataError(f"no scored rows for metric {metric!r}")
        model_mae = float((rows["predicted_value"] - rows["actual_value"]).abs().mean())
        reference_mae = float((rows["reference_value"] - rows["actual_value"]).abs().mean())
        if reference_mae <= 0:
            raise ClimateDataError(f"reference MAE for metric {metric!r} must be positive")
        mae[metric] = model_mae
        skill[metric] = 1.0 - model_mae / reference_mae
    return ClimateScore(
        score=100.0 * max(0.0, sum(skill.values()) / len(METRICS)),
        mae=mae,
        skill=skill,
        n_rows=len(scored),
    )


def _prediction_frame(predictions: pd.DataFrame, value_column: str) -> pd.DataFrame:
    key = ["city_id", "year", "metric"]
    required = set(key) | {"predicted_value"}
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise ClimateDataError(f"forecast is missing columns: {missing}")
    frame = predictions[[*key, "predicted_value"]].copy()
    frame["predicted_value"] = pd.to_numeric(frame["predicted_value"], errors="coerce")
    if frame["predicted_value"].isna().any() or not np.isfinite(frame["predicted_value"]).all():
        raise ClimateDataError("forecast contains missing or non-finite predictions")
    if frame.duplicated(key).any():
        raise ClimateDataError("forecast contains duplicate city/year/metric values")
    return frame.rename(columns={"predicted_value": value_column})


def backtest_baselines(
    history: pd.DataFrame,
    *,
    cutoffs: Iterable[int],
    horizon: int = 7,
    methods: Iterable[str] = BASELINE_METHODS,
) -> pd.DataFrame:
    """Evaluate methods at multiple historical origins using challenge scoring."""
    rows: list[dict[str, float | int | str]] = []
    for cutoff in cutoffs:
        years = range(cutoff + 1, cutoff + horizon + 1)
        truth = history.loc[history["year"].isin(years)]
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        )
        for method in methods:
            forecast = baseline_forecast(
                history, cutoff_year=cutoff, forecast_years=years, method=method
            )
            score = official_score(forecast, truth, reference)
            row: dict[str, float | int | str] = {
                "cutoff_year": cutoff,
                "method": method,
                "score": score.score,
                "n_rows": score.n_rows,
            }
            for metric in METRICS:
                row[f"{metric}_mae"] = score.mae[metric]
                row[f"{metric}_skill"] = score.skill[metric]
            rows.append(row)
    return pd.DataFrame(rows)


def select_metric_methods(backtest_results: pd.DataFrame) -> dict[str, str]:
    """Select the highest mean-skill baseline for each official metric."""
    if "method" not in backtest_results.columns:
        raise ClimateDataError("backtest results are missing the method column")

    selected: dict[str, str] = {}
    for metric in METRICS:
        skill_column = f"{metric}_skill"
        if skill_column not in backtest_results.columns:
            raise ClimateDataError(f"backtest results are missing {skill_column!r}")
        mean_skill = backtest_results.groupby("method")[skill_column].mean()
        if mean_skill.empty:
            raise ClimateDataError("backtest results contain no methods")
        best_skill = float(mean_skill.max())
        selected[metric] = sorted(mean_skill[mean_skill == best_skill].index.astype(str))[0]
    return selected


def metric_ensemble_forecast(
    history: pd.DataFrame,
    *,
    cutoff_year: int,
    forecast_years: Iterable[int],
    methods_by_metric: dict[str, str],
) -> pd.DataFrame:
    """Forecast each metric with its independently backtest-selected method."""
    if set(methods_by_metric) != set(METRICS):
        raise ValueError(f"methods_by_metric must contain exactly {list(METRICS)}")

    forecasts = []
    for metric in METRICS:
        forecast = baseline_forecast(
            history,
            cutoff_year=cutoff_year,
            forecast_years=forecast_years,
            method=methods_by_metric[metric],
        )
        forecasts.append(forecast.loc[forecast["metric"] == metric])
    return pd.concat(forecasts, ignore_index=True)


def backtest_metric_ensemble(
    history: pd.DataFrame,
    *,
    cutoffs: Iterable[int],
    methods_by_metric: dict[str, str],
    horizon: int = 7,
) -> pd.DataFrame:
    """Score one metric-specific ensemble at each historical forecast origin."""
    rows: list[dict[str, float | int]] = []
    for cutoff in cutoffs:
        years = range(cutoff + 1, cutoff + horizon + 1)
        truth = history.loc[history["year"].isin(years)]
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        )
        forecast = metric_ensemble_forecast(
            history,
            cutoff_year=cutoff,
            forecast_years=years,
            methods_by_metric=methods_by_metric,
        )
        score = official_score(forecast, truth, reference)
        row: dict[str, float | int] = {
            "cutoff_year": cutoff,
            "score": score.score,
            "n_rows": score.n_rows,
        }
        for metric in METRICS:
            row[f"{metric}_mae"] = score.mae[metric]
            row[f"{metric}_skill"] = score.skill[metric]
        rows.append(row)
    return pd.DataFrame(rows)


def validate_submission(submission: pd.DataFrame, city_ids: Iterable[str]) -> None:
    """Validate all organizer-required rows before a human submits them."""
    if list(submission.columns) != SUBMISSION_COLUMNS:
        raise ClimateSubmissionError(f"columns must be exactly {SUBMISSION_COLUMNS}")
    expected_cities = {str(city_id) for city_id in city_ids}
    years = set(FORECAST_YEARS)
    metrics = set(METRICS)
    if set(submission["city_id"]) != expected_cities:
        raise ClimateSubmissionError("submission city IDs do not match the official city set")
    if set(submission["year"]) != years:
        raise ClimateSubmissionError("submission years must be 2019 through 2025")
    if set(submission["metric"]) != metrics:
        raise ClimateSubmissionError(f"submission metrics must be {sorted(metrics)}")
    if submission.duplicated(["city_id", "year", "metric"]).any():
        raise ClimateSubmissionError("submission contains duplicate city/year/metric rows")
    expected_rows = len(expected_cities) * len(years) * len(metrics)
    if len(submission) != expected_rows:
        raise ClimateSubmissionError(
            f"submission must have {expected_rows} rows, got {len(submission)}"
        )
    values = pd.to_numeric(submission["predicted_value"], errors="coerce")
    if values.isna().any() or not np.isfinite(values).all():
        raise ClimateSubmissionError("submission contains missing or non-finite predictions")
