import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster
from proto_star.climate import ClimateDataError
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters._final_common import kernel_matrix, thirty_year_rows
from proto_star.forecasters.final_precip import (
    METRIC,
    TwoHalfSpec,
    _panels,
    fay_herriot_correction,
    method_of_moments_tau2,
    precision_weight,
)
from proto_star.forecasters.swap_metric import changed_metrics

CUTOFF = 2000
YEARS = list(range(2001, 2008))
BASE = {"kind": "pooled_trend", "params": {"level_years": [10, 15], "trend_window": 40}}
NUDGE = {"kind": "final_precip_nudge", "params": {"k": 3}}
TWO_HALF = {"kind": "final_precip_two_half", "params": {"bandwidth_km": 3000.0}}
FH = {"kind": "final_precip_two_half", "params": {"bandwidth_km": 3000.0, "fay_herriot": True}}


def _master() -> pd.DataFrame:
    return make_climate_master(first_year=1900, seed=11)


def _build(entry: dict) -> Forecaster:
    kind = get_kind(entry["kind"])
    return kind.build(kind.make_spec(entry["params"]))


def _values(frame: pd.DataFrame) -> pd.Series:
    rows = frame.loc[frame["metric"] == METRIC].sort_values(["city_id", "year"])
    return rows.set_index(["city_id", "year"])["predicted_value"]


def _wide(frame: pd.DataFrame) -> pd.DataFrame:
    rows = frame.loc[frame["metric"] == METRIC]
    return rows.pivot_table(index="city_id", columns="year", values="predicted_value")


@pytest.mark.parametrize("component", [NUDGE, TWO_HALF, FH])
def test_component_changes_only_precipitation(component: dict) -> None:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    base = _build(
        {"kind": "swap_metric", "params": {"metric": METRIC, "base": BASE, "components": [BASE]}}
    )
    swapped = _build(
        {
            "kind": "swap_metric",
            "params": {"metric": METRIC, "base": BASE, "components": [component]},
        }
    )
    assert changed_metrics(base(train, CUTOFF, YEARS), swapped(train, CUTOFF, YEARS)) == {METRIC}


@pytest.mark.parametrize("component", [NUDGE, TWO_HALF, FH])
def test_component_ignores_poisoned_future_rows(component: dict) -> None:
    master = _master()
    poisoned = master.copy()
    later = poisoned["Year"] > CUTOFF
    poisoned.loc[later, ["ToT Prcp", "Max Tmax", "Avg Temp", "cdd"]] = 1e6
    poisoned.loc[later, "Miss Prcp"] = 0
    forecaster = _build(component)
    clean = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    dirty = forecaster(poisoned.loc[poisoned["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, dirty)
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        forecaster(poisoned, CUTOFF, YEARS)
    moved = master.copy()
    moved.loc[(moved["Year"] > CUTOFF - 5) & (moved["Year"] <= CUTOFF), "ToT Prcp"] += 20.0
    shifted = forecaster(moved.loc[moved["Year"] <= CUTOFF], CUTOFF, YEARS)
    assert not np.allclose(_values(shifted), _values(clean))


def test_nudge_follows_a_local_shift_and_zero_fraction_is_the_mean() -> None:
    master = _master()
    city = master["ID"].iloc[0]
    shifted = master.copy()
    shifted.loc[(shifted["ID"] == city) & (shifted["Year"] > CUTOFF - 10), "ToT Prcp"] *= 1.5
    train = shifted.loc[shifted["Year"] <= CUTOFF]
    m30 = _values(thirty_year_rows(train, CUTOFF, YEARS, METRIC))
    nudged = _values(_build(NUDGE)(train, CUTOFF, YEARS))
    assert (nudged.loc[city] > m30.loc[city]).all()
    flat = _build({"kind": "final_precip_nudge", "params": {"k": 3, "fraction": 0.0}})
    pd.testing.assert_series_equal(_values(flat(train, CUTOFF, YEARS)), m30)


def test_two_half_uses_long_window_only_for_late_leads() -> None:
    master = _master()
    master.loc[master["Year"].between(CUTOFF - 44, CUTOFF - 30), "ToT Prcp"] += 15.0
    train = master.loc[master["Year"] <= CUTOFF]
    values = _wide(_build(TWO_HALF)(train, CUTOFF, YEARS))
    assert np.allclose(values[2001], values[2003])
    assert np.allclose(values[2004], values[2007])
    assert (values[2004] > values[2001]).all()


def test_two_half_keeps_the_mean_for_sparse_cities() -> None:
    master = _master()
    city = master["ID"].iloc[2]
    master.loc[(master["ID"] == city) & (master["Year"] > CUTOFF - 30), "Miss Prcp"] = 40
    master.loc[(master["ID"] == city) & (master["Year"].isin([1975, 1985, 1995])), "Miss Prcp"] = 0
    train = master.loc[master["Year"] <= CUTOFF]
    m30 = _values(thirty_year_rows(train, CUTOFF, YEARS, METRIC))
    for entry in (TWO_HALF, FH):
        values = _values(_build(entry)(train, CUTOFF, YEARS))
        assert np.allclose(values.loc[city], m30.loc[city])


def test_fay_herriot_leaves_early_leads_alone() -> None:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    p2 = _wide(_build(TWO_HALF)(train, CUTOFF, YEARS))
    p3 = _wide(_build(FH)(train, CUTOFF, YEARS))
    pd.testing.assert_frame_equal(p2[[2001, 2002, 2003]], p3[[2001, 2002, 2003]])


def test_tau2_is_floored_at_zero_and_needs_two_cities() -> None:
    small = pd.Series([0.01, -0.01, 0.0])
    noisy = pd.Series([0.5, 0.5, 0.5])
    assert method_of_moments_tau2(small, noisy) == 0.0
    assert method_of_moments_tau2(pd.Series([0.4]), pd.Series([0.0])) == 0.0
    assert method_of_moments_tau2(pd.Series([0.3, -0.3]), pd.Series([0.01, 0.01])) == (
        pytest.approx(0.08)
    )


def test_precision_weight_edge_cases() -> None:
    weights = precision_weight(0.0, pd.Series([0.2, 0.0]))
    assert weights.tolist() == [0.0, 1.0]  # tau^2 = 0: full shrinkage; nothing to shrink: keep
    assert precision_weight(1.0, pd.Series([1.0])).iloc[0] == pytest.approx(0.5)


def _fh_inputs(min_window: int) -> tuple[pd.Series, pd.DataFrame]:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    spec = TwoHalfSpec(fay_herriot=True, bandwidth_km=3000.0, fh_min_window_years=min_window)
    _, complete = _panels(train, CUTOFF, spec.min_days)
    kernel = kernel_matrix(train, spec.bandwidth_km, include_self=False)
    uses_long = pd.Series(True, index=complete.index)
    return fay_herriot_correction(complete, kernel, CUTOFF, uses_long, spec), complete


def test_fay_herriot_sparse_cities_get_no_correction() -> None:
    correction, _ = _fh_inputs(min_window=46)  # more years than the 45-year window holds
    assert (correction == 0.0).all()
    dense, _ = _fh_inputs(min_window=15)
    assert dense.abs().sum() > 0


def test_fay_herriot_without_neighbour_weight_gives_no_correction() -> None:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    spec = TwoHalfSpec(fay_herriot=True, bandwidth_km=1.0)  # neighbors carry ~0 weight
    _, complete = _panels(train, CUTOFF, spec.min_days)
    kernel = kernel_matrix(train, spec.bandwidth_km, include_self=False)
    uses_long = pd.Series(True, index=complete.index)
    correction = fay_herriot_correction(complete, kernel, CUTOFF, uses_long, spec)
    assert (correction == 0.0).all()
