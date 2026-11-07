import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import backtest_forecaster, ensemble_forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters.combination_p16_p17 import (
    build_member,
    clear_member_cache,
    combine_values,
    inverse_mse_weights,
    make_forecast_combination,
)

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
MEMBERS = {
    "ten": {"forecaster": "ten_year_mean"},
    "thirty": {"forecaster": "thirty_year_mean"},
    "last": {"forecaster": "last_valid_year"},
    "ewma": {"forecaster": "ewma_normal", "params": {"alpha": 0.2}},
}
ALL4 = ["ten", "thirty", "last", "ewma"]


@pytest.fixture(scope="module")
def master() -> pd.DataFrame:
    return make_annual_master(n_cities=5, first_year=1940, last_year=2018)


def _train(master: pd.DataFrame, cutoff: int = CUTOFF) -> pd.DataFrame:
    return master.loc[master["Year"] <= cutoff].copy()


def _metric(frame: pd.DataFrame, metric: str) -> pd.Series:
    rows = frame.loc[frame["metric"] == metric].sort_values(KEY)
    return rows.set_index(KEY)["predicted_value"]


def test_both_names_registered_and_torch_pinned_only_for_the_torch_alias() -> None:
    registry = load_all()
    assert registry["forecast_combination"].requires == ()
    assert registry["forecast_combination_torch"].requires == ("torch",)


def test_combine_values_hand_computed() -> None:
    values = np.array([[1.0, 2.0, 3.0, 10.0], [4.0, 4.0, 4.0, 4.0]])
    assert combine_values(values, "mean") == pytest.approx([4.0, 4.0])
    assert combine_values(values, "median") == pytest.approx([2.5, 4.0])
    # Median 2.5; 10 is farthest, dropped; mean of 1, 2, 3.
    assert combine_values(values, "trimmed") == pytest.approx([2.0, 4.0])
    weights = np.array([0.5, 0.5, 0.0, 0.0])
    assert combine_values(values, "inverse_mse", weights) == pytest.approx([1.5, 4.0])
    with pytest.raises(ValueError, match="method"):
        combine_values(values, "best")
    with pytest.raises(ValueError, match="weight"):
        combine_values(values, "inverse_mse")


def test_mean_equals_average_of_members_and_rest_is_current_best(master: pd.DataFrame) -> None:
    clear_member_cache()
    combo = make_forecast_combination(
        members=MEMBERS, combine={"cdd": ALL4, "annual_avg_temp": ["ten", "last"]}
    )
    out = combo(_train(master), CUTOFF, YEARS)
    assert not out.duplicated(KEY).any()
    assert len(out) == master["ID"].nunique() * len(METRICS) * len(YEARS)
    parts = {name: build_member(MEMBERS[name])(_train(master), CUTOFF, YEARS) for name in ALL4}
    expected_cdd = sum(_metric(parts[name], "cdd") for name in ALL4) / 4
    pd.testing.assert_series_equal(_metric(out, "cdd"), expected_cdd, check_names=False)
    expected_temp = (
        _metric(parts["ten"], "annual_avg_temp") + _metric(parts["last"], "annual_avg_temp")
    ) / 2
    pd.testing.assert_series_equal(
        _metric(out, "annual_avg_temp"), expected_temp, check_names=False
    )
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    for metric in ("total_precip_in", "hottest_day_temp"):
        pd.testing.assert_series_equal(_metric(out, metric), _metric(base, metric))


def test_single_member_reproduces_that_member(master: pd.DataFrame) -> None:
    combo = make_forecast_combination(members=MEMBERS, combine={"cdd": ["ewma"]}, cache=False)
    out = combo(_train(master), CUTOFF, YEARS)
    direct = resolve_forecaster(
        "x", variants={"x": {"forecaster": "ewma_normal", "params": {"alpha": 0.2}}}
    )(_train(master), CUTOFF, YEARS)
    pd.testing.assert_series_equal(_metric(out, "cdd"), _metric(direct, "cdd"))


def test_cache_does_not_change_results(master: pd.DataFrame) -> None:
    clear_member_cache()
    spec = {"members": MEMBERS, "combine": {"cdd": ALL4}, "method": "median"}
    first = make_forecast_combination(**spec)(_train(master), CUTOFF, YEARS)
    cached = make_forecast_combination(**spec)(_train(master), CUTOFF, YEARS)
    uncached = make_forecast_combination(**spec, cache=False)(_train(master), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(first, cached)
    pd.testing.assert_frame_equal(first, uncached)
    # A different training set is a different cache entry.
    other = make_forecast_combination(**spec)(_train(master, 1999), 1999, YEARS[:-1])
    assert set(other["year"]) == set(YEARS[:-1])


def test_inverse_mse_weights_favour_the_better_member(master: pd.DataFrame) -> None:
    clear_member_cache()
    specs = {"ten": MEMBERS["ten"], "last": MEMBERS["last"]}
    members = {name: build_member(spec) for name, spec in specs.items()}
    weights = inverse_mse_weights(
        specs, members, _train(master), CUTOFF, metric="cdd", horizon=7, n_origins=2, step=7
    )
    assert sum(weights.values()) == pytest.approx(1.0)
    # A single noisy year is a worse forecast than a 10-year mean on noisy synthetic data.
    assert weights["ten"] > weights["last"]


def test_values_after_the_cutoff_do_not_change_predictions(master: pd.DataFrame) -> None:
    """No leakage: the combination and its in-train weights see only the training slice."""
    for method in ("mean", "inverse_mse"):
        clear_member_cache()
        forecaster = make_forecast_combination(
            members=MEMBERS, combine={"cdd": ALL4}, method=method, cache=False
        )
        before = forecaster(_train(master), CUTOFF, YEARS)
        changed = master.copy()
        late = changed["Year"] > CUTOFF
        for column in ("Avg Temp", "ToT Prcp", "Max Tmax", "cdd"):
            changed.loc[late, column] = changed.loc[late, column] * 3.0 + 100.0
        after = forecaster(_train(changed), CUTOFF, YEARS)
        pd.testing.assert_frame_equal(before, after)
        scores = backtest_forecaster(forecaster, changed, cutoffs=[CUTOFF])
        assert set(scores["window"]) == {"all", "years_1_3", "years_4_7"}


def test_hindcast_weights_come_from_training_years(master: pd.DataFrame) -> None:
    """Weights are measured at pseudo-origins inside the training years: poking a hindcast
    year moves them (and the leakage test above shows test years cannot)."""
    specs = {"ten": MEMBERS["ten"], "last": MEMBERS["last"]}
    members = {name: build_member(spec) for name, spec in specs.items()}

    def weights(table: pd.DataFrame) -> dict[str, float]:
        return inverse_mse_weights(
            specs,
            members,
            _train(table),
            CUTOFF,
            metric="cdd",
            horizon=7,
            n_origins=2,
            step=7,
            cache=False,
        )

    poked = master.copy()
    poked.loc[poked["Year"] == 1995, "cdd"] += 500.0
    assert weights(poked)["ten"] != pytest.approx(weights(master)["ten"])


@pytest.mark.parametrize(
    ("params", "match"),
    [
        ({"combine": {"cdd": ["nope"]}}, "unknown"),
        ({"combine": {"rain": ["ten"]}}, "combine must map"),
        ({"combine": {"cdd": ["ten", "last"]}, "method": "trimmed"}, "at least 3"),
        ({"combine": {"cdd": ["ten"]}, "method": "best"}, "method"),
    ],
)
def test_bad_params_are_rejected(params: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        make_forecast_combination(members=MEMBERS, **params)  # type: ignore[arg-type]  # bad on purpose
