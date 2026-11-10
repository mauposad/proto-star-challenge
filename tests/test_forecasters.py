import math

import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.backtest import Forecaster, baseline_forecaster, compare_forecasters
from proto_star.forecasters import CustomSpec, available_kinds, build_custom, describe_custom
from proto_star.trial import TrialConfig, build_forecasters, describe_forecaster

KEY = ["city_id", "year", "metric"]
YEARS = [2011, 2012, 2013]


def _master(first: int = 1950, last: int = 2010) -> pd.DataFrame:
    """Three cities with a trend and deterministic noise, in the master table's columns."""
    rows = []
    for offset, city in enumerate(["A", "B", "C"]):
        for year in range(first, last + 1):
            wiggle = math.sin(year * 1.7 + offset)
            trend = (year - first) * 0.03
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Lat": 30.0 + 5 * offset,
                    "Lon": -100.0 + 10 * offset,
                    "Station Segment": 1 if year < 1990 else 2,
                    "Avg Temp": 50.0 + 8 * offset + trend + wiggle,
                    "ToT Prcp": 30.0 + 5 * offset + 3 * wiggle,
                    "Max Tmax": 95.0 + 2 * wiggle,
                    "cdd": 800.0 + 300 * offset + 20 * trend + 50 * wiggle,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _resolve(name: str) -> Forecaster:
    return baseline_forecaster(name)


def _values(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def test_registered_kinds() -> None:
    assert {"blend", "direct", "per_metric"} <= set(available_kinds())


def test_blend_is_the_weighted_mean_of_its_members() -> None:
    master = _master()
    ten = _values(baseline_forecaster("ten_year_mean")(master, 2010, YEARS))
    thirty = _values(baseline_forecaster("thirty_year_mean")(master, 2010, YEARS))
    spec = CustomSpec(
        kind="blend",
        params={"members": ["ten_year_mean", "thirty_year_mean"], "weights": [3, 1]},
    )
    blended = _values(build_custom(spec, _resolve)(master, 2010, YEARS))
    pd.testing.assert_series_equal(blended, 0.75 * ten + 0.25 * thirty, check_names=False)


@pytest.mark.parametrize(
    "params",
    [
        {"members": ["ten_year_mean"]},
        {"members": ["ten_year_mean", "thirty_year_mean"], "weights": [1, -1]},
        {"members": ["ten_year_mean", "thirty_year_mean"], "weights": [1]},
        {"members": ["ten_year_mean", "thirty_year_mean"], "typo": 1},
    ],
)
def test_blend_rejects_bad_params(params: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        build_custom(CustomSpec(kind="blend", params=params), _resolve)


def test_per_metric_takes_each_metric_from_its_forecaster() -> None:
    master = _master()
    params = {
        "annual_avg_temp": "ten_year_mean",
        "total_precip_in": "thirty_year_mean",
        "hottest_day_temp": "thirty_year_mean",
        "cdd": "fifteen_year_mean",
    }
    mixed = build_custom(CustomSpec(kind="per_metric", params=params), _resolve)(
        master, 2010, YEARS
    )
    for metric, method in params.items():
        expected = baseline_forecaster(method)(master, 2010, YEARS)
        expected = _values(expected.loc[expected["metric"] == metric])
        got = _values(mixed.loc[mixed["metric"] == metric])
        pd.testing.assert_series_equal(got, expected)


def test_per_metric_needs_every_metric() -> None:
    with pytest.raises(ValueError):
        build_custom(CustomSpec(kind="per_metric", params={"cdd": "ten_year_mean"}), _resolve)


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown forecaster kind"):
        build_custom(CustomSpec(kind="magic"), _resolve)


def _config(**custom: object) -> TrialConfig:
    return TrialConfig.model_validate(
        {
            "name": "t",
            "description": "d",
            "forecasters": ["thirty_year_mean", *custom],
            "custom": custom,
            "reference": "thirty_year_mean",
        }
    )


def test_trial_config_builds_and_describes_custom_forecasters() -> None:
    cfg = _config(
        mix={"kind": "blend", "params": {"members": ["ten_year_mean", "thirty_year_mean"]}},
        mix_of_mix={"kind": "blend", "params": {"members": ["mix", "fifteen_year_mean"]}},
    )
    forecasters = build_forecasters(cfg)
    results = compare_forecasters(forecasters, _master(1900, 2018), cutoffs=[1995])
    assert set(results["method"]) == {"thirty_year_mean", "mix", "mix_of_mix"}
    assert "Weighted mean" in describe_forecaster("mix", cfg)
    assert describe_custom(CustomSpec(kind="blend", description="Mine")) == "Mine"


def test_trial_config_rejects_custom_names_that_are_taken_and_cycles() -> None:
    with pytest.raises(ValidationError, match="already used"):
        _config(ten_year_mean={"kind": "blend", "params": {}})
    cycle = _config(
        a={"kind": "blend", "params": {"members": ["b", "thirty_year_mean"]}},
        b={"kind": "blend", "params": {"members": ["a", "thirty_year_mean"]}},
    )
    with pytest.raises(ValueError, match="cycle"):
        build_forecasters(cycle)
