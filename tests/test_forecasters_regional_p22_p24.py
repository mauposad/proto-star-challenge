from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import backtest_forecaster, ensemble_forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters import load_all
from proto_star.forecasters.regional_p22_p24 import (
    assign_groups,
    city_trends,
    make_pooled_groups,
    make_regional_trend,
    shrink_trends,
)

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
FAST = {"origin_stride": 3, "n_lags": 4}


@pytest.fixture(scope="module")
def master() -> pd.DataFrame:
    return make_annual_master(n_cities=6, first_year=1940, last_year=2018)


@pytest.fixture
def groups_csv(tmp_path: Path, master: pd.DataFrame) -> str:
    cities = sorted(master["ID"].unique())
    table = pd.DataFrame(
        {
            "city_id": cities,
            "elevation_m": [10.0, 200.0, 500.0, 20.0, 300.0, 900.0],
            "pop_2010": [50_000, 150_000, 900_000, 20_000, 300_000, 1_500_000],
            "land_cover": ["developed_high", "developed_low", "undeveloped"] * 2,
        }
    )
    path = tmp_path / "city_groups.csv"
    table.to_csv(path, index=False)
    return str(path)


def _train(master: pd.DataFrame) -> pd.DataFrame:
    return master.loc[master["Year"] <= CUTOFF].copy()


def _check_shape(forecast: pd.DataFrame, master: pd.DataFrame) -> None:
    assert list(forecast.columns) == [*KEY, "predicted_value"]
    assert not forecast.duplicated(KEY).any()
    assert len(forecast) == master["ID"].nunique() * len(METRICS) * len(YEARS)
    assert np.isfinite(forecast["predicted_value"]).all()


def _changed_metrics(forecast: pd.DataFrame, master: pd.DataFrame) -> set[str]:
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    differs = ~np.isclose(merged["predicted_value"], merged["predicted_value_base"])
    return set(merged.loc[differs, "metric"])


def test_shrinkage_pulls_noisy_slopes_to_the_group_trend() -> None:
    trends = pd.DataFrame(
        {"slope": [0.0, 0.4, 0.2, -1.0], "slope_var": [0.02, 0.02, 0.02, 0.02]},
        index=["a", "b", "c", "d"],
    )
    groups = pd.Series({"a": "G", "b": "G", "c": "G", "d": "H"})
    group = shrink_trends(trends, groups, mode="group")
    assert np.allclose(group[["a", "b", "c"]], 0.2)
    assert group["d"] == pytest.approx(-1.0)  # a group of one keeps its own trend
    eb = shrink_trends(trends, groups, mode="eb")
    # Spread 0.04 = true spread 0.02 + sampling variance 0.02: half-way to the group trend.
    assert eb["a"] == pytest.approx(0.1)
    assert eb["b"] == pytest.approx(0.3)
    noisy = trends.assign(slope_var=[1.0, 1.0, 1.0, 1.0])
    assert np.allclose(shrink_trends(noisy, groups, mode="eb")[["a", "b", "c"]], 0.2)
    assert np.allclose(shrink_trends(trends, groups, mode="none"), trends["slope"])


def test_city_trends_recover_a_linear_slope() -> None:
    years = np.arange(1971, 2001)
    history = pd.DataFrame(
        {"city_id": "x", "year": years, "metric": "cdd", "actual_value": 3.0 + 0.5 * years}
    )
    trends = city_trends(history, cutoff_year=2000, trend_years=30)
    assert trends.loc["x", "slope"] == pytest.approx(0.5)
    assert trends.loc["x", "slope_var"] == pytest.approx(0.0, abs=1e-12)


def test_regional_trend_adds_the_damped_trend_to_the_recent_level(master: pd.DataFrame) -> None:
    flat = make_regional_trend(extrapolate_lead=False)(_train(master), CUTOFF, YEARS)
    full = make_regional_trend(damping=1.0)(_train(master), CUTOFF, YEARS)
    half = make_regional_trend(damping=0.5)(_train(master), CUTOFF, YEARS)
    none = make_regional_trend(damping=0.0)(_train(master), CUTOFF, YEARS)
    for forecast in (flat, full, half, none):
        _check_shape(forecast, master)
    assert _changed_metrics(full, master) == {"annual_avg_temp", "cdd"}
    assert _changed_metrics(none, master) == set()  # no trend: exactly current_best
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    gap_full = full["predicted_value"] - base["predicted_value"]
    gap_half = half["predicted_value"] - base["predicted_value"]
    assert np.allclose(gap_half, 0.5 * gap_full)
    # The synthetic cities warm, so the trend lifts temperature and grows with the lead.
    temp = full.loc[full["metric"] == "annual_avg_temp"].merge(base, on=KEY, suffixes=("", "_b"))
    temp["gap"] = temp["predicted_value"] - temp["predicted_value_b"]
    by_year = temp.groupby("year")["gap"].mean()
    assert (by_year > 0).all() and by_year.is_monotonic_increasing
    # The flat control holds the cutoff-year level for every lead.
    flat_temp = flat.loc[flat["metric"] == "annual_avg_temp"]
    assert flat_temp.groupby("city_id")["predicted_value"].nunique().eq(1).all()


@pytest.mark.parametrize(
    "params",
    [
        {"mode": "interact", "group_by": ["region"]},
        {"mode": "separate", "group_by": ["region"]},
        {"mode": "additive", "group_by": ["elevation", "population", "land_cover"]},
        {"mode": "interact", "group_by": ["land_cover"], "model_metrics": ["annual_avg_temp"]},
    ],
)
def test_pooled_groups_cover_every_row_and_model_only_their_metrics(
    master: pd.DataFrame, groups_csv: str, params: dict[str, object]
) -> None:
    forecaster = make_pooled_groups(**FAST, groups_path=groups_csv, **params)
    forecast = forecaster(_train(master), CUTOFF, YEARS)
    _check_shape(forecast, master)
    expected = {"annual_avg_temp"} if "model_metrics" in params else {"cdd"}
    assert _changed_metrics(forecast, master) == expected


def test_groups_come_from_static_attributes(master: pd.DataFrame, groups_csv: str) -> None:
    static = feats.city_static(_train(master))
    groups = assign_groups(
        static,
        ["region", "elevation", "population", "land_cover", "national"],
        bands={"elevation": [100.0, 400.0]},
        groups_path=groups_csv,
    )
    assert groups.loc["CITY000", "elevation"] == "elev_0"
    assert groups.loc["CITY001", "elevation"] == "elev_1"
    assert groups.loc["CITY005", "elevation"] == "elev_2"
    assert groups.loc["CITY002", "population"] == "pop_2"
    assert groups.loc["CITY001", "region"] == "North"
    assert set(groups["national"]) == {"all"}
    with pytest.raises(FileNotFoundError, match="download_regional_p22_p24"):
        assign_groups(static, ["elevation"], groups_path=str(Path(groups_csv).parent / "no.csv"))
    with pytest.raises(ValueError, match="unknown groupings"):
        assign_groups(static, ["zodiac"])


@pytest.mark.parametrize("which", ["p22", "p24"])
def test_values_after_the_cutoff_do_not_change_predictions(
    master: pd.DataFrame, groups_csv: str, which: str
) -> None:
    if which == "p22":
        forecaster = make_regional_trend(group_by="elevation", groups_path=groups_csv)
    else:
        forecaster = make_pooled_groups(**FAST, mode="interact", groups_path=groups_csv)
    before = forecaster(_train(master), CUTOFF, YEARS)
    changed = master.copy()
    late = changed["Year"] > CUTOFF
    for column in ("Avg Temp", "ToT Prcp", "Max Tmax", "cdd"):
        changed.loc[late, column] = changed.loc[late, column] * 3.0 + 100.0
    after = forecaster(_train(changed), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(before, after)
    scores = backtest_forecaster(forecaster, changed, cutoffs=[CUTOFF])
    assert set(scores["window"]) == {"all", "years_1_3", "years_4_7"}


def test_registry_and_param_checks() -> None:
    registry = load_all()
    assert {"regional_trend_p22", "pooled_groups_p24"} <= set(registry)
    variants = {"v": {"forecaster": "regional_trend_p22", "params": {"damping": 0.5}}}
    assert callable(resolve_forecaster("v", variants=variants))
    with pytest.raises(ValueError, match="rejected params"):
        registry["regional_trend_p22"].build({"bogus": 1})
    with pytest.raises(ValueError, match="damping"):
        make_regional_trend(damping=2.0)
    with pytest.raises(ValueError, match="unknown shrink"):
        make_regional_trend(shrink="magic")
    with pytest.raises(ValueError, match="unknown mode"):
        make_pooled_groups(mode="magic")
    with pytest.raises(ValueError, match="unknown metrics"):
        make_pooled_groups(model_metrics=["rain"])
