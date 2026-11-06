import math

import pandas as pd
import pytest

from proto_star.backtest import (
    CURRENT_BEST_METHODS,
    WINDOWS,
    backtest_forecaster,
    baseline_forecaster,
    build_submission,
    compare_forecasters,
    ensemble_forecaster,
    summarize_backtest,
)
from proto_star.climate import (
    METRICS,
    ClimateDataError,
    ClimateSubmissionError,
    annual_to_long,
    backtest_baselines,
    backtest_metric_ensemble,
)

CUTOFFS = [2000, 2005]


def _master(last_year: int = 2018) -> pd.DataFrame:
    """Two cities with a trend and deterministic year-to-year noise."""
    rows = []
    for offset, city in enumerate(["A", "B"]):
        for year in range(1960, last_year + 1):
            wiggle = math.sin(year * 1.7 + offset)
            trend = (year - 1960) * 0.05
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Avg Temp": 50.0 + 10 * offset + trend + wiggle,
                    "ToT Prcp": 30.0 + 5 * offset + 3 * wiggle,
                    "Max Tmax": 95.0 + 2 * wiggle,
                    "cdd": 800.0 + 300 * offset + 10 * trend + 50 * wiggle,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _long(master: pd.DataFrame) -> pd.DataFrame:
    return annual_to_long(master).rename(columns={"actual_value": "predicted_value"})


def _perfect(master: pd.DataFrame, *, leads: tuple[int, int] = (1, 7)):
    """Test-only oracle: it reads the answers, which real forecasters must never do."""
    answers = _long(master)

    def forecast(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        rows = answers.loc[answers["year"].isin(years)].copy()
        lead = rows["year"] - cutoff_year
        rows.loc[~lead.between(*leads), "predicted_value"] += 100.0
        return rows

    return forecast


def test_forecaster_only_sees_rows_up_to_each_cutoff() -> None:
    seen: list[tuple[int, int]] = []
    inner = baseline_forecaster("ten_year_mean")

    def spy(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        seen.append((cutoff_year, int(train["Year"].max())))
        return inner(train, cutoff_year, years)

    backtest_forecaster(spy, _master(), cutoffs=CUTOFFS)
    assert seen == [(2000, 2000), (2005, 2005)]


def test_forecaster_cannot_change_data_for_later_folds() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def vandal(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        result = inner(train, cutoff_year, years)
        train["cdd"] = 0.0
        return result

    clean = backtest_forecaster(inner, _master(), cutoffs=CUTOFFS)
    vandalized = backtest_forecaster(vandal, _master(), cutoffs=CUTOFFS)
    pd.testing.assert_frame_equal(clean, vandalized)


@pytest.mark.parametrize("method", ["ten_year_mean", "linear_trend"])
def test_matches_existing_baseline_backtest(method: str) -> None:
    master = _master()
    expected = backtest_baselines(annual_to_long(master), cutoffs=CUTOFFS, methods=[method])
    results = backtest_forecaster(baseline_forecaster(method), master, cutoffs=CUTOFFS)
    actual = results.loc[results["window"] == "all"].reset_index(drop=True)
    assert actual["score"].tolist() == pytest.approx(expected["score"].tolist())


def test_matches_existing_ensemble_backtest() -> None:
    master = _master()
    expected = backtest_metric_ensemble(
        annual_to_long(master), cutoffs=CUTOFFS, methods_by_metric=CURRENT_BEST_METHODS
    )
    results = backtest_forecaster(ensemble_forecaster(), master, cutoffs=CUTOFFS)
    actual = results.loc[results["window"] == "all"].reset_index(drop=True)
    assert actual["score"].tolist() == pytest.approx(expected["score"].tolist())


def test_results_have_one_row_per_origin_and_window() -> None:
    results = backtest_forecaster(baseline_forecaster("ten_year_mean"), _master(), cutoffs=CUTOFFS)
    assert len(results) == len(CUTOFFS) * len(WINDOWS)
    counts = results.loc[results["cutoff_year"] == 2000].set_index("window")["n_rows"]
    assert counts["all"] == 2 * 7 * len(METRICS)
    assert counts["years_1_3"] == 2 * 3 * len(METRICS)
    assert counts["years_4_7"] == 2 * 4 * len(METRICS)


def test_far_window_scores_only_forecast_years_four_to_seven() -> None:
    master = _master()
    results = backtest_forecaster(_perfect(master, leads=(4, 7)), master, cutoffs=[2000])
    scores = results.set_index("window")["raw_score"]
    assert scores["years_4_7"] == pytest.approx(100.0)
    assert scores["years_1_3"] < 0


def test_raw_score_keeps_negative_values_that_score_floors() -> None:
    master = _master()
    results = backtest_forecaster(_perfect(master, leads=(99, 99)), master, cutoffs=[2000])
    row = results.loc[results["window"] == "all"].iloc[0]
    assert row["score"] == 0.0
    assert row["raw_score"] < 0


def test_rejects_forecast_that_skips_scored_rows() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def skips_city(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        forecast = inner(train, cutoff_year, years)
        return forecast.loc[forecast["city_id"] != "B"]

    with pytest.raises(ClimateDataError, match="skips 28 scored rows"):
        backtest_forecaster(skips_city, _master(), cutoffs=[2000])


def test_rejects_forecast_with_years_outside_the_fold() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def extra_year(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        return inner(train, cutoff_year, [*years, years[-1] + 1])

    with pytest.raises(ClimateDataError, match="outside the fold"):
        backtest_forecaster(extra_year, _master(), cutoffs=[2000])


def test_rejects_forecast_with_missing_columns() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def no_metric(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        return inner(train, cutoff_year, years).drop(columns="metric")

    with pytest.raises(ClimateDataError, match="missing columns"):
        backtest_forecaster(no_metric, _master(), cutoffs=[2000])


def test_rejects_forecast_with_blank_predictions() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def blank(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        forecast = inner(train, cutoff_year, years)
        forecast.loc[forecast.index[0], "predicted_value"] = float("nan")
        return forecast

    with pytest.raises(ClimateDataError, match="non-finite"):
        backtest_forecaster(blank, _master(), cutoffs=[2000])


def test_rejects_forecast_with_duplicate_rows() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def doubled(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        forecast = inner(train, cutoff_year, years)
        return pd.concat([forecast, forecast])

    with pytest.raises(ClimateDataError, match="duplicate"):
        backtest_forecaster(doubled, _master(), cutoffs=[2000])


def test_compare_and_summarize_count_wins_against_baseline() -> None:
    master = _master()
    results = compare_forecasters(
        {"oracle": _perfect(master), "plain": baseline_forecaster("ten_year_mean")},
        master,
        cutoffs=CUTOFFS,
    )
    summary = summarize_backtest(results, baseline="plain").set_index(["window", "method"])
    assert summary.loc[("all", "oracle"), "origins_beating_baseline"] == 2
    assert summary.loc[("all", "oracle"), "origins"] == 2
    assert summary.loc[("all", "plain"), "origins_beating_baseline"] == 0
    assert summary.loc[("all", "oracle"), "raw_score"] == pytest.approx(100.0)


def test_summarize_rejects_unknown_baseline() -> None:
    results = backtest_forecaster(baseline_forecaster("ten_year_mean"), _master(), cutoffs=[2000])
    with pytest.raises(ValueError, match="not in the results"):
        summarize_backtest(results, baseline="missing")


def test_build_submission_uses_all_data_and_validates_rows() -> None:
    seen: list[int] = []
    inner = ensemble_forecaster()

    def spy(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        seen.append(int(train["Year"].max()))
        assert cutoff_year == 2018
        assert years == list(range(2019, 2026))
        return inner(train, cutoff_year, years)

    submission = build_submission(spy, _master())
    assert seen == [2018]
    assert len(submission) == 2 * 7 * len(METRICS)
    assert list(submission.columns) == ["city_id", "year", "metric", "predicted_value"]


def test_build_submission_rejects_incomplete_forecast() -> None:
    inner = baseline_forecaster("ten_year_mean")

    def skips_city(train: pd.DataFrame, cutoff_year: int, years: list[int]) -> pd.DataFrame:
        forecast = inner(train, cutoff_year, years)
        return forecast.loc[forecast["city_id"] != "B"]

    with pytest.raises(ClimateSubmissionError, match="city IDs"):
        build_submission(skips_city, _master())


def test_build_submission_rejects_post_cutoff_master() -> None:
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        build_submission(baseline_forecaster("ten_year_mean"), _master(last_year=2019))
