import pandas as pd
import pytest

from proto_star.climate import (
    ClimateDataError,
    ClimateSubmissionError,
    annual_to_long,
    backtest_baselines,
    baseline_forecast,
    metric_ensemble_forecast,
    official_score,
    select_metric_methods,
    validate_submission,
)


def _annual() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": ["A", "A", "A", "B", "B", "B"],
            "Year": [2015, 2016, 2017, 2015, 2016, 2017],
            "Avg Temp": [50.0, 51.0, 52.0, 60.0, 61.0, 62.0],
            "ToT Prcp": [20.0, 21.0, 22.0, 30.0, 31.0, 32.0],
            "Max Tmax": [90.0, 91.0, 92.0, 95.0, 96.0, 97.0],
            "cdd": [100.0, 120.0, 140.0, 500.0, 520.0, 540.0],
            "Miss Tmax": [0, 0, 0, 0, 0, 0],
            "Miss Tmin": [0, 0, 0, 0, 0, 0],
            "Miss Prcp": [0, 0, 0, 0, 0, 0],
        }
    )


def test_annual_to_long_applies_metric_quality_screen() -> None:
    annual = _annual()
    annual.loc[0, "Miss Prcp"] = 11
    history = annual_to_long(annual)
    assert len(history) == 23
    assert not (
        (history["city_id"] == "A")
        & (history["year"] == 2015)
        & (history["metric"] == "total_precip_in")
    ).any()


def test_annual_to_long_rejects_post_cutoff_data() -> None:
    annual = _annual()
    annual.loc[0, "Year"] = 2019
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        annual_to_long(annual)


def test_official_score_is_relative_to_reference() -> None:
    truth = pd.DataFrame(
        {
            "city_id": ["A"] * 4,
            "year": [2019] * 4,
            "metric": [
                "annual_avg_temp",
                "total_precip_in",
                "hottest_day_temp",
                "cdd",
            ],
            "actual_value": [10.0, 10.0, 10.0, 10.0],
        }
    )
    perfect = truth.rename(columns={"actual_value": "predicted_value"})
    reference = perfect.copy()
    reference["predicted_value"] = 12.0
    result = official_score(perfect, truth, reference)
    assert result.score == 100.0
    assert result.n_rows == 4


def test_backtest_and_submission_validation() -> None:
    history = annual_to_long(_annual())
    results = backtest_baselines(
        history, cutoffs=[2015], horizon=2, methods=["thirty_year_mean", "linear_trend"]
    )
    assert set(results["method"]) == {"thirty_year_mean", "linear_trend"}

    forecast = baseline_forecast(
        history, cutoff_year=2017, forecast_years=range(2019, 2026), method="linear_trend"
    )
    validate_submission(forecast, ["A", "B"])
    with pytest.raises(ClimateSubmissionError, match="columns"):
        validate_submission(forecast.drop(columns="metric"), ["A", "B"])


def test_metric_selection_and_ensemble_forecast() -> None:
    history = annual_to_long(_annual())
    results = pd.DataFrame(
        {
            "method": ["ten_year_mean", "thirty_year_mean"],
            "annual_avg_temp_skill": [0.2, 0.1],
            "total_precip_in_skill": [-0.1, 0.0],
            "hottest_day_temp_skill": [0.0, 0.1],
            "cdd_skill": [0.3, 0.2],
        }
    )
    methods = select_metric_methods(results)
    assert methods == {
        "annual_avg_temp": "ten_year_mean",
        "total_precip_in": "thirty_year_mean",
        "hottest_day_temp": "thirty_year_mean",
        "cdd": "ten_year_mean",
    }
    forecast = metric_ensemble_forecast(
        history,
        cutoff_year=2017,
        forecast_years=[2019],
        methods_by_metric=methods,
    )
    assert len(forecast) == 8
