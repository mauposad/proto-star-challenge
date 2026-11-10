import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.backtest import baseline_forecaster
from proto_star.climate import annual_to_long
from proto_star.direct import FEATURES, DirectSpec, _features, _Panel, direct_forecast
from proto_star.forecasters import CustomSpec, build_custom

CUTOFF = 2010
YEARS = list(range(2011, 2018))


def _master(slope: float = 0.04, noise: float = 0.0) -> pd.DataFrame:
    """Five cities sharing one linear warming trend from 1900 to the cut-off."""
    rng = np.random.default_rng(0)
    rows = []
    for offset, city in enumerate(["A", "B", "C", "D", "E"]):
        for year in range(1900, CUTOFF + 1):
            temp = 45.0 + 4 * offset + slope * (year - 1900) + noise * rng.normal()
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Lat": 30.0 + 3 * offset,
                    "Lon": -110.0 + 6 * offset,
                    "Avg Temp": temp,
                    "ToT Prcp": 30.0 + offset + noise * rng.normal(),
                    "Max Tmax": 95.0 + noise * rng.normal(),
                    "cdd": 900.0 + 120.0 * (temp - 45.0),
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _run(master: pd.DataFrame, **params: object) -> pd.DataFrame:
    spec = DirectSpec.model_validate(params)
    history = annual_to_long(master, cutoff_year=CUTOFF)
    return direct_forecast(master, history, CUTOFF, YEARS, spec)


def test_linear_direct_model_extrapolates_a_shared_trend() -> None:
    master = _master()
    forecast = _run(master, model="linear", metrics=["annual_avg_temp"])
    expected = 45.0 + 4 * forecast["city_id"].map(dict(zip("ABCDE", range(5), strict=True)))
    expected += 0.04 * (forecast["year"] - 1900)
    assert np.abs(forecast["predicted_value"] - expected).max() < 0.05


def test_direct_forecast_covers_modeled_metrics_only() -> None:
    forecast = _run(_master(noise=0.5), model="gbm", gbm_min_samples_leaf=20)
    assert set(forecast["metric"]) == {"annual_avg_temp", "cdd"}
    assert len(forecast) == 5 * len(YEARS) * 2
    assert np.isfinite(forecast["predicted_value"]).all()


def test_features_only_look_backward_from_the_origin() -> None:
    values = np.random.default_rng(1).normal(size=(80, 4))
    years = np.arange(1931, 2011)
    coords = np.zeros((4, 2))
    slope = np.zeros(4)
    end = 50
    before, m30 = _features(_Panel(values, years), end, 3, slope, years, coords)
    changed = values.copy()
    changed[end + 1 :] += 100.0
    after, m30_after = _features(_Panel(changed, years), end, 3, slope, years, coords)
    np.testing.assert_array_equal(m30, m30_after)
    for name in FEATURES:
        np.testing.assert_array_equal(before[name], after[name])


def test_custom_kind_fills_unmodeled_metrics_with_the_30_year_mean() -> None:
    master = _master(noise=0.5)
    fn = build_custom(
        CustomSpec(kind="direct", params={"model": "linear", "metrics": ["annual_avg_temp"]}),
        baseline_forecaster,  # direct names no members, so the resolver is never called
    )
    forecast = fn(master, CUTOFF, YEARS)
    assert len(forecast) == 5 * len(YEARS) * 4
    assert not forecast.duplicated(["city_id", "year", "metric"]).any()


@pytest.mark.parametrize("params", [{"metrics": ["snow"]}, {"features": ["future"]}, {"typo": 1}])
def test_direct_spec_rejects_unknown_names(params: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DirectSpec.model_validate(params)


def test_direct_forecast_rejects_years_beyond_the_horizon() -> None:
    master = _master()
    history = annual_to_long(master, cutoff_year=CUTOFF)
    with pytest.raises(ValueError, match="years after the cut-off"):
        direct_forecast(master, history, CUTOFF, [2011, 2020], DirectSpec(horizon=7))
