import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import resolve_forecaster
from proto_star.climate import METRICS, ClimateDataError, annual_to_long
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters.arima_p13 import (
    ArimaSettings,
    arima_forecast,
    boxcox,
    boxcox_shift,
    forecast_series,
    inverse_boxcox,
    kpss_ndiffs,
    make_arima_lai2020,
)

CUTOFF = 2000
YEARS = list(range(CUTOFF + 1, CUTOFF + 8))
KEY = ["city_id", "year", "metric"]


@pytest.fixture(scope="module")
def train() -> pd.DataFrame:
    master = make_annual_master(n_cities=1, first_year=1965, last_year=2018)
    return master.loc[master["Year"] <= CUTOFF].copy()


@pytest.fixture(scope="module")
def forecast(train: pd.DataFrame) -> pd.DataFrame:
    return make_arima_lai2020()(train, CUTOFF, YEARS)


def test_registered_and_buildable_from_a_variant() -> None:
    assert "arima_lai2020" in load_all()
    variant = {"v": {"forecaster": "arima_lai2020", "params": {"history_years": 30}}}
    assert callable(resolve_forecaster("v", variants=variant))
    with pytest.raises(ValueError, match="rejected params"):
        resolve_forecaster("v", variants={"v": {"forecaster": "arima_lai2020", "params": {"x": 1}}})


def test_forecast_covers_every_city_metric_and_year(
    train: pd.DataFrame, forecast: pd.DataFrame
) -> None:
    assert list(forecast.columns) == [*KEY, "predicted_value"]
    assert not forecast.duplicated(KEY).any()
    assert np.isfinite(forecast["predicted_value"]).all()
    assert set(forecast["year"]) == set(YEARS)
    assert set(forecast["metric"]) == set(METRICS)
    assert len(forecast) == train["ID"].nunique() * len(METRICS) * len(YEARS)
    counts = forecast.attrs["arima_diagnostics"]
    assert counts["series"] == train["ID"].nunique() * len(METRICS)
    assert counts["fallback_series"] == 0


def test_forecast_is_plausible(train: pd.DataFrame, forecast: pd.DataFrame) -> None:
    history = annual_to_long(train, cutoff_year=CUTOFF)
    level = history.groupby(["city_id", "metric"])["actual_value"].agg(["mean", "std"])
    merged = forecast.merge(level, left_on=["city_id", "metric"], right_index=True)
    assert ((merged["predicted_value"] - merged["mean"]).abs() < 5 * merged["std"]).all()


def test_rejects_years_after_the_cutoff(train: pd.DataFrame) -> None:
    master = make_annual_master(n_cities=1, first_year=1960, last_year=2018)
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        make_arima_lai2020()(master, CUTOFF, YEARS)
    history = annual_to_long(master)
    with pytest.raises(ValueError, match="past the cutoff"):
        arima_forecast(history, cutoff_year=CUTOFF, forecast_years=YEARS, settings=ArimaSettings())


def test_ignores_rows_it_is_not_given(train: pd.DataFrame, forecast: pd.DataFrame) -> None:
    """Changing values after the cutoff in the full table cannot change the forecast."""
    master = make_annual_master(n_cities=1, first_year=1965, last_year=2018)
    master.loc[master["Year"] > CUTOFF, "Avg Temp"] += 100.0
    changed = make_arima_lai2020()(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(forecast, changed)


def test_short_series_fall_back_to_the_thirty_year_mean(train: pd.DataFrame) -> None:
    short = train.loc[train["Year"] > CUTOFF - 5]
    out = make_arima_lai2020(min_obs=10)(short, CUTOFF, YEARS)
    counts = out.attrs["arima_diagnostics"]
    assert counts["short"] == counts["series"] == counts["fallback_series"]
    expected = annual_to_long(short, cutoff_year=CUTOFF)
    expected = expected.groupby(["city_id", "metric"], as_index=False)["actual_value"].mean()
    merged = out.merge(expected, on=["city_id", "metric"])
    assert merged["predicted_value"].to_numpy() == pytest.approx(merged["actual_value"])


def test_params_change_the_result(train: pd.DataFrame, forecast: pd.DataFrame) -> None:
    windowed = make_arima_lai2020(history_years=15)(train, CUTOFF, YEARS)
    assert not np.allclose(windowed["predicted_value"], forecast["predicted_value"])
    hybrid = make_arima_lai2020(metrics=["annual_avg_temp"])(train, CUTOFF, YEARS)
    best = resolve_forecaster("current_best")(train, CUTOFF, YEARS)
    other = hybrid.merge(best, on=KEY, suffixes=("", "_best"))
    other = other.loc[other["metric"] != "annual_avg_temp"]
    assert other["predicted_value"].to_numpy() == pytest.approx(other["predicted_value_best"])
    assert hybrid.attrs["arima_diagnostics"]["series"] == train["ID"].nunique()
    with pytest.raises(ValueError, match="unknown metrics"):
        make_arima_lai2020(metrics=["nope"])(train, CUTOFF, YEARS)
    with pytest.raises(ValueError, match="n_jobs"):
        make_arima_lai2020(n_jobs=0)


def test_parallel_matches_serial_so_results_are_deterministic(
    train: pd.DataFrame, forecast: pd.DataFrame
) -> None:
    parallel = make_arima_lai2020(n_jobs=2)(train, CUTOFF, YEARS)
    pd.testing.assert_frame_equal(forecast, parallel)


def test_series_paths() -> None:
    settings = ArimaSettings()
    constant = forecast_series(np.full(30, 4.0), 3, non_negative=True, settings=settings)
    assert constant.status == "constant"
    assert constant.forecast == pytest.approx(4.0)
    rng = np.random.default_rng(0)
    trend = 10.0 + 0.5 * np.arange(60) + rng.standard_normal(60)
    result = forecast_series(trend, 5, non_negative=False, settings=settings)
    assert result.status == "arima"
    assert result.drift
    assert np.all(np.diff(result.forecast) > 0)  # a strong trend carries forward
    falling = forecast_series(
        50.0 - 2.0 * np.arange(40) + rng.standard_normal(40),
        40,
        non_negative=True,
        settings=settings,
    )
    assert falling.forecast.min() >= 0.0


def test_helpers() -> None:
    rng = np.random.default_rng(1)
    assert kpss_ndiffs(rng.standard_normal(80), alpha=0.05, max_d=2) == 0
    assert kpss_ndiffs(np.cumsum(rng.standard_normal(200)) * 5, alpha=0.05, max_d=2) >= 1
    assert boxcox_shift(np.array([0.0, 2.0, 4.0])) == pytest.approx(1.0)
    assert boxcox_shift(np.array([1.0, 2.0])) == 0.0
    assert (np.array([-3.0, 2.0]) + boxcox_shift(np.array([-3.0, 2.0]))).min() > 0
    values = np.array([1.0, 2.5, 7.0])
    for lam in (0.0, 0.5, -1.0):
        assert inverse_boxcox(boxcox(values, lam), lam) == pytest.approx(values)
