import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.anomaly import (
    AnomalyCorrectionSpec,
    RelativeTrendSpec,
    TrendScaleSpec,
    anomaly_correction_forecast,
    relative_trend_forecast,
    trend_scale_forecast,
)
from proto_star.backtest import baseline_forecaster, pooled_trend_forecaster
from proto_star.climate import annual_to_long
from proto_star.trend import PooledTrendSpec, pooled_trend_forecast

KEY = ["city_id", "year", "metric"]
CUTOFF = 2000
YEARS = list(range(2001, 2008))


def _master(
    step_city: str | None = None, precip_growth: float = 0.0, temp_slope: float = 0.03
) -> pd.DataFrame:
    """Eight cities, 1920-2000. One city can get a persistent +3 step in hottest day from 1985."""
    rng = np.random.default_rng(11)
    rows = []
    for offset, city in enumerate("ABCDEFGH"):
        for year in range(1920, CUTOFF + 1):
            hot = 95.0 + offset + (3.0 if city == step_city and year >= 1985 else 0.0)
            temp = 50.0 + offset + temp_slope * (year - 1920)
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Avg Temp": temp,
                    "ToT Prcp": (30.0 + offset) * (1 + precip_growth * (year - 1960))
                    + 0.5 * rng.normal(),
                    "Max Tmax": hot + 0.5 * rng.normal(),
                    "cdd": 1000.0 + 100.0 * (temp - 50.0),
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def test_damped_anomaly_moves_a_persistently_stepped_city_toward_its_new_level() -> None:
    master = _master(step_city="C")
    base = baseline_forecaster("thirty_year_mean")
    spec = AnomalyCorrectionSpec(base="b", metrics=["hottest_day_temp"], window=10)
    corrected = _indexed(anomaly_correction_forecast(base, master, CUTOFF, YEARS, spec))
    plain = _indexed(base(master, CUTOFF, YEARS))
    key = ("C", 2003, "hottest_day_temp")
    assert plain[key] < corrected[key] <= 98.0 + 2 + 0.5  # toward 97 + 3, not past it
    untouched = corrected.index.get_level_values("metric") != "hottest_day_temp"
    pd.testing.assert_series_equal(corrected[untouched], plain[untouched])


def test_trend_scale_is_one_when_the_trend_is_exact() -> None:
    master = _master()
    spec = TrendScaleSpec(pseudo_origins=8)
    scaled = _indexed(trend_scale_forecast(master, CUTOFF, YEARS, spec))
    plain = _indexed(
        pooled_trend_forecaster(PooledTrendSpec(level_years=[10, 15], trend_window=40))(
            master, CUTOFF, YEARS
        )
    )
    temp = scaled.index.get_level_values("metric") == "annual_avg_temp"
    pd.testing.assert_series_equal(scaled[temp], plain[temp], atol=1e-6)


def test_slope_scale_zero_gives_a_flat_forecast() -> None:
    history = annual_to_long(_master(), cutoff_year=CUTOFF)
    spec = PooledTrendSpec(level_years=[10], trend_window=40, slope_scale=0.0)
    forecast = pooled_trend_forecast(history, cutoff_year=CUTOFF, forecast_years=YEARS, spec=spec)
    temp = forecast.loc[forecast["metric"] == "annual_avg_temp"]
    assert temp.groupby("city_id")["predicted_value"].nunique().max() == 1


def test_relative_trend_recovers_a_shared_percentage_growth() -> None:
    master = _master(precip_growth=0.01)
    base = baseline_forecaster("thirty_year_mean")
    spec = RelativeTrendSpec(base="b", trend_window=40)
    forecast = _indexed(relative_trend_forecast(base, master, CUTOFF, YEARS, spec))
    truth_2005 = 30.0 * (1 + 0.01 * (2005 - 1960))
    assert forecast[("A", 2005, "total_precip_in")] == pytest.approx(truth_2005, rel=0.02)


def test_specs_reject_unknown_metrics() -> None:
    with pytest.raises(ValidationError):
        AnomalyCorrectionSpec(base="b", metrics=["snow"])
    with pytest.raises(ValidationError):
        RelativeTrendSpec(base="b", metric="snow")


def _with_diurnal(master: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    out["Avg Tmax"] = out["Avg Temp"] + 10.0
    out["Avg Tmin"] = out["Avg Temp"] - 10.0
    return out


def test_missing_contrast_falls_back_to_the_nested_parent() -> None:
    """With no Tmax/Tmin data the contrast is missing, so the arm must equal E2 exactly."""
    master = _with_diurnal(_master(step_city="C"))
    master["Avg Tmax"] = np.nan
    master["Avg Tmin"] = np.nan
    base = baseline_forecaster("thirty_year_mean")
    parent = AnomalyCorrectionSpec(base="b", metrics=["cdd"], window=10, pseudo_origins=8)
    child = parent.model_copy(update={"split": "diurnal_contrast"})
    a = _indexed(anomaly_correction_forecast(base, master, CUTOFF, YEARS, parent))
    b = _indexed(anomaly_correction_forecast(base, master, CUTOFF, YEARS, child))
    pd.testing.assert_series_equal(a, b)


def test_cdd_contrast_regressor_is_centred_across_cities() -> None:
    from proto_star.anomaly import _anomalies, _diurnal_history

    master = _with_diurnal(_master())
    master.loc[master["ID"] == "B", "Avg Tmin"] += 2.0  # one city's Tmin anomaly differs
    history = annual_to_long(master, cutoff_year=CUTOFF)
    parts = _anomalies(history, CUTOFF, 10, diurnal=_diurnal_history(master, CUTOFF))
    cdd = parts.xs("cdd", level="metric")["contrast"].dropna()
    assert abs(cdd.mean()) < 1e-9
