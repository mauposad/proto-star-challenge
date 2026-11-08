import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import backtest_forecaster, ensemble_forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters import load_all
from proto_star.forecasters.station_p15 import (
    StepParams,
    boundaries,
    city_distances,
    estimate_steps,
    make_station_p15,
    station_panels,
)

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
SWITCH = 1995  # first year of CITY000's second station
STEP = 3.0  # the new station reads 3 degrees warmer
FAR = {"max_km": 5000.0}  # synthetic cities are ~800 km apart


def _with_stations(master: pd.DataFrame, switches: dict[str, tuple[int, float]]) -> pd.DataFrame:
    """Add station columns; each switched city gets a step on temperature and CDD."""
    out = master.copy()
    out["Station Segment"] = 1
    out["Station Changes"] = 0
    for city, (year, step) in switches.items():
        rows = out["ID"] == city
        late = rows & (out["Year"] >= year)
        out.loc[late, "Station Segment"] = 2
        out.loc[rows & (out["Year"] == year), "Station Changes"] = 1
        out.loc[late, "Avg Temp"] += step
        out.loc[late, "cdd"] += 30.0 * step
    return out


@pytest.fixture(scope="module")
def plain() -> pd.DataFrame:
    return _with_stations(make_annual_master(n_cities=6, first_year=1950, last_year=2018), {})


@pytest.fixture(scope="module")
def switched() -> pd.DataFrame:
    base = make_annual_master(n_cities=6, first_year=1950, last_year=2018)
    return _with_stations(base, {"CITY000": (SWITCH, STEP)})


def _train(master: pd.DataFrame) -> pd.DataFrame:
    return master.loc[master["Year"] <= CUTOFF].copy()


def _value(forecast: pd.DataFrame, city: str, metric: str) -> float:
    rows = forecast.loc[(forecast["city_id"] == city) & (forecast["metric"] == metric)]
    values = rows["predicted_value"].to_numpy()
    assert np.allclose(values, values[0])
    return float(rows["predicted_value"].iloc[0])


def _steps(train: pd.DataFrame, params: StepParams) -> pd.DataFrame:
    panel = feats.wide_panels(train, CUTOFF)["annual_avg_temp"]
    segment, changes = station_panels(train, CUTOFF)
    _, steps = estimate_steps(
        panel.reindex(columns=segment.columns),
        segment,
        changes,
        city_distances(train),
        metric="annual_avg_temp",
        window=10,
        cutoff_year=CUTOFF,
        params=params,
    )
    return steps


@pytest.mark.parametrize("mode", ["segment", "adjusted"])
def test_without_station_switches_it_equals_current_best(plain: pd.DataFrame, mode: str) -> None:
    metrics = list(METRICS)
    forecast = make_station_p15(mode=mode, metrics=metrics, **FAR)(_train(plain), CUTOFF, YEARS)
    base = ensemble_forecaster()(_train(plain), CUTOFF, YEARS)
    assert list(forecast.columns) == [*KEY, "predicted_value"]
    assert len(forecast) == plain["ID"].nunique() * len(METRICS) * len(YEARS)
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    assert np.allclose(merged["predicted_value"], merged["predicted_value_base"])


def test_boundaries_are_the_first_years_of_new_segments() -> None:
    row = pd.Series([1, 1, 2, 2, 3], index=[1990, 1991, 1992, 1993, 1994])
    assert boundaries(row) == [1992, 1994]


def test_pairwise_step_recovers_the_injected_shift(switched: pd.DataFrame) -> None:
    steps = _steps(_train(switched), StepParams(n_neighbors=5, side_years=5, max_km=5000.0))
    row = steps.loc[steps["city_id"] == "CITY000"].iloc[0]
    assert row["boundary"] == SWITCH and row["applied"] and row["n_neighbors"] == 5
    assert abs(row["step"] - STEP) < 1.5
    # Cities without a switch are not touched.
    assert set(steps["city_id"]) == {"CITY000"}


def test_adjusted_level_shifts_the_earlier_segment(switched: pd.DataFrame) -> None:
    train = _train(switched)
    steps = _steps(train, StepParams(n_neighbors=5, side_years=5, max_km=5000.0))
    step = float(steps["step"].iloc[0])
    forecast = make_station_p15(mode="adjusted", n_neighbors=5, side_years=5, **FAR)(
        train, CUTOFF, YEARS
    )
    city = train.loc[(train["ID"] == "CITY000") & (train["Year"] > CUTOFF - 10)]
    temp = city["Avg Temp"].to_numpy() + np.where(city["Year"] < SWITCH, step, 0.0)
    assert _value(forecast, "CITY000", "annual_avg_temp") == pytest.approx(temp.mean())
    # Raw 10-year mean is pulled down by the old station; the adjusted one is not.
    base = ensemble_forecaster()(train, CUTOFF, YEARS)
    assert _value(forecast, "CITY000", "annual_avg_temp") > _value(
        base, "CITY000", "annual_avg_temp"
    )
    # Other metrics and other cities keep the base forecast.
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    untouched = (merged["city_id"] != "CITY000") | merged["metric"].isin(
        ["total_precip_in", "hottest_day_temp"]
    )
    assert np.allclose(
        merged.loc[untouched, "predicted_value"], merged.loc[untouched, "predicted_value_base"]
    )


def test_a_high_t_threshold_skips_the_adjustment(switched: pd.DataFrame) -> None:
    train = _train(switched)
    forecast = make_station_p15(mode="adjusted", min_t=1e6, **FAR)(train, CUTOFF, YEARS)
    base = ensemble_forecaster()(train, CUTOFF, YEARS)
    pd.testing.assert_frame_equal(forecast, base)


def test_neighbors_with_their_own_switch_are_left_out(switched: pd.DataFrame) -> None:
    noisy = _with_stations(
        make_annual_master(n_cities=6, first_year=1950, last_year=2018),
        {"CITY000": (SWITCH, STEP), "CITY001": (SWITCH + 1, 40.0)},
    )
    params = StepParams(n_neighbors=5, side_years=5, max_km=5000.0)
    steps = _steps(_train(noisy), params).set_index("city_id")
    # CITY001 switches inside CITY000's span, so it is no neighbor: same as dropping it.
    without = _steps(_train(switched.loc[switched["ID"] != "CITY001"]), params)
    assert steps.loc["CITY000", "n_neighbors"] == 4
    assert steps.loc["CITY000", "step"] == pytest.approx(float(without["step"].iloc[0]))


def test_segment_mode_uses_the_current_segment_or_falls_back(switched: pd.DataFrame) -> None:
    train = _train(switched)
    city = train.loc[train["ID"] == "CITY000"]
    segment_mean = city.loc[city["Year"] >= SWITCH, "Avg Temp"].mean()  # 6 years
    short_ok = make_station_p15(mode="segment", min_years=5)(train, CUTOFF, YEARS)
    assert _value(short_ok, "CITY000", "annual_avg_temp") == pytest.approx(segment_mean)
    too_short = make_station_p15(mode="segment", min_years=7)(train, CUTOFF, YEARS)
    base = ensemble_forecaster()(train, CUTOFF, YEARS)
    pd.testing.assert_frame_equal(too_short, base)


def test_values_and_switches_after_the_cutoff_do_not_change_predictions(
    switched: pd.DataFrame,
) -> None:
    forecaster = make_station_p15(mode="adjusted", **FAR)
    before = forecaster(_train(switched), CUTOFF, YEARS)
    changed = switched.copy()
    late = changed["Year"] > CUTOFF
    for column in ("Avg Temp", "ToT Prcp", "Max Tmax", "cdd"):
        changed.loc[late, column] = changed.loc[late, column] * 3.0 + 100.0
    # A neighbor switching station after the cut-off must not alter the fold either.
    changed.loc[late & (changed["ID"] == "CITY002"), "Station Segment"] = 5
    changed.loc[
        (changed["Year"] == CUTOFF + 1) & (changed["ID"] == "CITY002"), "Station Changes"
    ] = 1
    after = forecaster(_train(changed), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(before, after)
    scores = backtest_forecaster(forecaster, changed, cutoffs=[CUTOFF])
    assert set(scores["window"]) == {"all", "years_1_3", "years_4_7"}


def test_registry_params_and_base_forecaster(switched: pd.DataFrame) -> None:
    registry = load_all()
    assert "station_p15" in registry
    variants = {
        "v": {
            "forecaster": "station_p15",
            "params": {
                "metrics": ["annual_avg_temp"],
                "max_km": 5000.0,
                "base_forecaster": "pooled_hybrid_p09_p14",
                "base_params": {"model_metrics": ["cdd"], "estimator": "ridge", "n_lags": 4},
            },
        }
    }
    train = _train(switched)
    forecast = resolve_forecaster("v", variants=variants)(train, CUTOFF, YEARS)
    pooled = resolve_forecaster(
        "p",
        variants={
            "p": {
                "forecaster": "pooled_hybrid_p09_p14",
                "params": {"model_metrics": ["cdd"], "estimator": "ridge", "n_lags": 4},
            }
        },
    )(train, CUTOFF, YEARS)
    merged = forecast.merge(pooled, on=KEY, suffixes=("", "_base"))
    cdd = merged["metric"] == "cdd"
    assert np.allclose(merged.loc[cdd, "predicted_value"], merged.loc[cdd, "predicted_value_base"])
    with pytest.raises(ValueError, match="rejected params"):
        registry["station_p15"].build({"bogus": 1})
    with pytest.raises(ValueError, match="unknown mode"):
        make_station_p15(mode="magic")
    with pytest.raises(ValueError, match="unknown metrics"):
        make_station_p15(metrics=["rain"])
