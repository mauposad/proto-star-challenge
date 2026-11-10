import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster, baseline_forecaster
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters.swap_metric import changed_metrics

CUTOFF = 2000
YEARS = list(range(2001, 2008))
TREND = {"kind": "pooled_trend", "params": {"level_years": [10], "trend_window": 30}}
BASE = {"kind": "pooled_trend", "params": {"level_years": [10, 15], "trend_window": 40}}


def _train() -> pd.DataFrame:
    master = make_climate_master(seed=5)
    return master.loc[master["Year"] <= CUTOFF].copy()


def _build(**params: object) -> Forecaster:
    kind = get_kind("swap_metric")
    return kind.build(kind.make_spec(params))


def _values(frame: pd.DataFrame, metric: str) -> np.ndarray:
    rows = frame.loc[frame["metric"] == metric].sort_values(["city_id", "year"])
    return rows["predicted_value"].to_numpy()


def test_swap_changes_only_its_metric() -> None:
    train = _train()
    base = _build(metric="cdd", base=BASE, components=[BASE])(train, CUTOFF, YEARS)
    swapped = _build(metric="cdd", base=BASE, components=[TREND])(train, CUTOFF, YEARS)
    assert changed_metrics(base, swapped) == {"cdd"}
    reference = get_kind("pooled_trend")
    trend = reference.build(reference.make_spec(TREND["params"]))(train, CUTOFF, YEARS)
    assert np.allclose(_values(swapped, "cdd"), _values(trend, "cdd"))


def test_swap_takes_weighted_mean_of_components() -> None:
    train = _train()
    flat = {"kind": "pooled_trend", "params": {"level_years": [30], "trend_window": 30}}
    mean = _build(metric="annual_avg_temp", base=BASE, components=[TREND, flat])
    tilted = _build(
        metric="annual_avg_temp", base=BASE, components=[TREND, flat], weights=[0.25, 0.75]
    )
    only_a = _build(metric="annual_avg_temp", base=BASE, components=[TREND])
    only_b = _build(metric="annual_avg_temp", base=BASE, components=[flat])
    a = _values(only_a(train, CUTOFF, YEARS), "annual_avg_temp")
    b = _values(only_b(train, CUTOFF, YEARS), "annual_avg_temp")
    assert np.allclose(_values(mean(train, CUTOFF, YEARS), "annual_avg_temp"), (a + b) / 2)
    assert np.allclose(
        _values(tilted(train, CUTOFF, YEARS), "annual_avg_temp"), 0.25 * a + 0.75 * b
    )


def test_memo_does_not_leak_between_folds() -> None:
    master = make_climate_master(seed=5)
    forecaster = _build(metric="cdd", base=BASE, components=[TREND])
    early = forecaster(master.loc[master["Year"] <= 1990], 1990, list(range(1991, 1998)))
    late = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    assert early["year"].max() == 1997 and late["year"].min() == 2001
    again = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(late, again)
    changed = master.copy()
    changed.loc[changed["Year"] == CUTOFF, "Avg Temp"] += 5.0
    moved = forecaster(changed.loc[changed["Year"] <= CUTOFF], CUTOFF, YEARS)
    assert not np.allclose(_values(moved, "annual_avg_temp"), _values(late, "annual_avg_temp"))


def test_changed_metrics_needs_same_rows() -> None:
    train = _train()
    flat = baseline_forecaster("thirty_year_mean")(train, CUTOFF, YEARS)
    assert changed_metrics(flat, flat) == set()
    with pytest.raises(ValueError, match="same rows"):
        changed_metrics(flat, flat.iloc[1:])


def test_swap_rejects_bad_weights_and_params() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        _build(metric="cdd", components=[TREND, BASE], weights=[0.5, 0.6])
    with pytest.raises(ValueError, match="one value per component"):
        _build(metric="cdd", components=[TREND], weights=[0.5, 0.5])
    with pytest.raises(ValueError, match="rejected params"):
        _build(metric="cdd", components=[{"kind": "pooled_trend", "params": {"bad": 1}}])
