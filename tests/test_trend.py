import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.backtest import resolve_forecaster
from proto_star.climate import METRICS
from proto_star.trend import (
    PooledTrendSpec,
    cdd_per_degree,
    pooled_slope,
    pooled_trend_forecast,
)

SPEC = PooledTrendSpec(level_years=[10], trend_window=30)
YEARS = list(range(1989, 2019))


def _rows(city: str, metric: str, values: list[float], years: list[int]) -> pd.DataFrame:
    return pd.DataFrame({"city_id": city, "year": years, "metric": metric, "actual_value": values})


def _history(
    temp_slope: float = 0.1, per_degree: tuple[float, float] = (100.0, 300.0)
) -> pd.DataFrame:
    """Two cities warming alike, with CDD that follows temperature at different rates."""
    frames = []
    for city, base, gain in (("A", 50.0, per_degree[0]), ("B", 70.0, per_degree[1])):
        wiggle = [0.5 * ((year % 3) - 1) for year in YEARS]
        temp = [base + temp_slope * (y - 1989) + w for y, w in zip(YEARS, wiggle, strict=True)]
        frames.append(_rows(city, "annual_avg_temp", temp, YEARS))
        frames.append(_rows(city, "cdd", [1000.0 + gain * (t - base) for t in temp], YEARS))
        frames.append(_rows(city, "total_precip_in", [30.0] * len(YEARS), YEARS))
        frames.append(_rows(city, "hottest_day_temp", [95.0] * len(YEARS), YEARS))
    return pd.concat(frames, ignore_index=True)


def _forecast(history: pd.DataFrame, spec: PooledTrendSpec = SPEC) -> pd.DataFrame:
    return pooled_trend_forecast(
        history, cutoff_year=2018, forecast_years=[2019, 2025], spec=spec
    ).set_index(["city_id", "metric", "year"])


def test_pooled_slope_recovers_a_shared_trend() -> None:
    assert pooled_slope(_history(0.1), "annual_avg_temp", 2018, SPEC) == pytest.approx(
        0.1, abs=0.01
    )


def test_pooled_slope_cannot_go_negative() -> None:
    assert pooled_slope(_history(-0.1), "annual_avg_temp", 2018, SPEC) == 0.0


def test_pooled_slope_ignores_a_sparse_city() -> None:
    sparse = _rows("C", "annual_avg_temp", [0.0, 500.0], [2017, 2018])
    history = pd.concat([_history(0.1), sparse], ignore_index=True)
    assert pooled_slope(history, "annual_avg_temp", 2018, SPEC) == pytest.approx(
        pooled_slope(_history(0.1), "annual_avg_temp", 2018, SPEC)
    )


def test_cdd_per_degree_recovers_each_citys_rate() -> None:
    rates = cdd_per_degree(_history(), 2018, SPEC)
    assert rates["A"] == pytest.approx(100.0)
    assert rates["B"] == pytest.approx(300.0)


def test_temperature_forecast_is_level_plus_trend_from_the_levels_center() -> None:
    history = _history(0.1)
    forecast = _forecast(history)
    recent = history[(history.city_id == "A") & (history.metric == "annual_avg_temp")].tail(10)
    slope = pooled_slope(history, "annual_avg_temp", 2018, SPEC)
    expected = recent.actual_value.mean() + slope * (2025 - recent.year.mean())
    assert forecast.loc[("A", "annual_avg_temp", 2025), "predicted_value"] == pytest.approx(
        expected
    )


def test_level_windows_are_averaged() -> None:
    history = _history()
    both = _forecast(history, PooledTrendSpec(level_years=[10, 15], trend_window=30))
    ten = _forecast(history, PooledTrendSpec(level_years=[10], trend_window=30))
    fifteen = _forecast(history, PooledTrendSpec(level_years=[15], trend_window=30))
    key = ("A", "annual_avg_temp", 2025)
    assert both.loc[key, "predicted_value"] == pytest.approx(
        (ten.loc[key, "predicted_value"] + fifteen.loc[key, "predicted_value"]) / 2
    )


def test_sensitive_city_gains_more_cdd_than_a_flat_pooled_trend_would_give() -> None:
    forecast = _forecast(_history())

    def gain(city: str) -> float:
        rows = forecast.loc[(city, "cdd"), "predicted_value"]
        return float(rows.loc[2025] - rows.loc[2019])

    assert gain("B") == pytest.approx(3 * gain("A"))
    pooled = _forecast(
        _history(), PooledTrendSpec(level_years=[10], trend_window=30, cdd_sensitivity=False)
    )
    rows = pooled.loc[:, "predicted_value"]
    assert rows.loc[("A", "cdd", 2025)] - rows.loc[("A", "cdd", 2019)] == pytest.approx(
        rows.loc[("B", "cdd", 2025)] - rows.loc[("B", "cdd", 2019)]
    )


def test_city_without_enough_years_falls_back_to_the_pooled_cdd_slope() -> None:
    sparse = pd.concat(
        [
            _rows("C", metric, [value] * 3, [2016, 2017, 2018])
            for metric, value in (
                ("annual_avg_temp", 60.0),
                ("cdd", 900.0),
                ("total_precip_in", 30.0),
                ("hottest_day_temp", 95.0),
            )
        ],
        ignore_index=True,
    )
    history = pd.concat([_history(), sparse], ignore_index=True)
    forecast = _forecast(history).loc[("C", "cdd"), "predicted_value"]
    slope = pooled_slope(history, "cdd", 2018, SPEC)
    assert forecast.loc[2025] - forecast.loc[2019] == pytest.approx(6 * slope)


def test_precipitation_and_hottest_day_stay_on_the_thirty_year_mean() -> None:
    forecast = _forecast(_history())
    assert forecast.loc[("A", "total_precip_in", 2025), "predicted_value"] == pytest.approx(30.0)
    assert forecast.loc[("A", "hottest_day_temp", 2019), "predicted_value"] == pytest.approx(95.0)


def test_forecast_ignores_years_after_the_cutoff() -> None:
    history = _history()
    later = pd.concat([_rows("A", metric, [1e6], [2019]) for metric in METRICS], ignore_index=True)
    both = pd.concat([history, later], ignore_index=True)
    assert np.allclose(
        _forecast(both)["predicted_value"].sort_index(),
        _forecast(history)["predicted_value"].sort_index(),
    )


def test_forecast_covers_every_city_metric_and_year() -> None:
    forecast = _forecast(_history())
    assert len(forecast) == 2 * len(METRICS) * 2
    assert np.isfinite(forecast["predicted_value"]).all()


def test_spec_rejects_unknown_settings() -> None:
    with pytest.raises(ValidationError):
        PooledTrendSpec(level_years=[10], trend_window=30, magic=True)  # type: ignore[call-arg]


def test_resolve_forecaster_finds_a_pooled_trend() -> None:
    assert callable(resolve_forecaster("mine", None, {"mine": SPEC}))


def test_segment_slope_ignores_a_station_step() -> None:
    """A flat city whose new station reads 2 degrees warmer is not warming."""
    years = list(range(1979, 2019))
    frames = []
    for city in ("A", "B"):
        values = [50.0 + (2.0 if (city == "A" and y >= 1999) else 0.0) for y in years]
        frame = _rows(city, "annual_avg_temp", values, years)
        frame["segment"] = [2 if (city == "A" and y >= 1999) else 1 for y in years]
        frames.append(frame)
    history = pd.concat(frames, ignore_index=True)
    by_city = PooledTrendSpec(level_years=[10], trend_window=40)
    by_segment = PooledTrendSpec(level_years=[10], trend_window=40, slope_within="segment")
    assert pooled_slope(history, "annual_avg_temp", 2018, by_city) > 0.01
    assert pooled_slope(history, "annual_avg_temp", 2018, by_segment) == pytest.approx(0.0)


def test_segment_slope_needs_a_segment_column() -> None:
    spec = PooledTrendSpec(level_years=[10], trend_window=30, slope_within="segment")
    with pytest.raises(ValueError, match="segment"):
        pooled_slope(_history(), "annual_avg_temp", 2018, spec)
