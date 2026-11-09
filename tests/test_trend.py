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
    assert callable(resolve_forecaster("mine", pooled_trends={"mine": SPEC}))


def _hot_history(per_degree_hot: float) -> pd.DataFrame:
    """Hottest day follows each city's annual temperature at a fixed rate."""
    history = _history(0.1)
    temp = history[history.metric == "annual_avg_temp"].set_index(["city_id", "year"])
    hot = history.metric == "hottest_day_temp"
    keys = list(zip(history.loc[hot, "city_id"], history.loc[hot, "year"], strict=True))
    base = temp.loc[keys, "actual_value"].to_numpy()
    history.loc[hot, "actual_value"] = 95.0 + per_degree_hot * (base - base.mean())
    return history


def test_hottest_sensitivity_off_keeps_the_thirty_year_mean() -> None:
    history = _hot_history(2.0)
    plain = _forecast(history)
    mean = history[(history.city_id == "A") & (history.metric == "hottest_day_temp")]
    assert plain.loc[("A", "hottest_day_temp", 2025), "predicted_value"] == pytest.approx(
        mean.actual_value.mean()
    )


def test_hottest_sensitivity_adds_a_damped_city_scaled_trend() -> None:
    history = _hot_history(2.0)
    half = PooledTrendSpec(level_years=[10], trend_window=30, hottest_sensitivity=0.5)
    full = PooledTrendSpec(level_years=[10], trend_window=30, hottest_sensitivity=1.0)
    plain = _forecast(history).loc[("A", "hottest_day_temp", 2025), "predicted_value"]
    gain_half = _forecast(history, half).loc[("A", "hottest_day_temp", 2025), "predicted_value"]
    gain_full = _forecast(history, full).loc[("A", "hottest_day_temp", 2025), "predicted_value"]
    assert gain_half > plain
    assert gain_full - plain == pytest.approx(2 * (gain_half - plain))
    years = history[(history.city_id == "A") & (history.metric == "hottest_day_temp")].year
    warming = pooled_slope(history, "annual_avg_temp", 2018, SPEC)
    assert gain_full - plain == pytest.approx(2.0 * warming * (2025 - years.mean()), rel=0.02)


def test_blend_averages_members_per_metric() -> None:
    from proto_star.backtest import blend_forecaster

    def constant(value: float):  # type: ignore[no-untyped-def] # tiny test helper
        def forecast(train: pd.DataFrame, cutoff: int, years: list[int]) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {"city_id": "A", "year": y, "metric": m, "predicted_value": value}
                    for y in years
                    for m in METRICS
                ]
            )

        return forecast

    members = {"low": constant(1.0), "high": constant(3.0)}
    plan = {m: ["low"] for m in METRICS} | {"cdd": ["low", "high"]}
    out = blend_forecaster(members, plan)(pd.DataFrame(), 2018, [2019]).set_index("metric")
    assert out.loc["cdd", "predicted_value"] == pytest.approx(2.0)
    assert out.loc["annual_avg_temp", "predicted_value"] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="every metric"):
        blend_forecaster(members, {"cdd": ["low"]})


def test_blend_rejects_nested_blends() -> None:
    plan = {m: ["thirty_year_mean"] for m in METRICS}
    with pytest.raises(ValueError, match="other blends"):
        resolve_forecaster("outer", blends={"outer": {**plan, "cdd": ["inner"]}, "inner": plan})
