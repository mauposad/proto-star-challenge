from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster
from proto_star.climate import ClimateDataError
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters._final_temp_common import nearest_with_self, ols_slopes
from proto_star.forecasters.final_temp_gmst import gmst_line, shrunk_slopes
from proto_star.forecasters.final_temp_two_scale import (
    area_weights,
    bias_corrected_ar1,
    weighted_median,
)
from proto_star.forecasters.swap_metric import changed_metrics
from proto_star.neighbors import city_coordinates

CUTOFF = 2000
YEARS = list(range(2001, 2008))
TEMP = "annual_avg_temp"
SMALL = {"n_cities": 3}
T1 = {"kind": "final_temp_recent_normal", "params": SMALL}
T2 = {"kind": "final_temp_region_departure", "params": SMALL}
T3 = {"kind": "final_temp_two_scale", "params": {"radius_km": 1500.0}}
BASE = {"kind": "lead_blend", "params": {}}


def _gmst_file(tmp_path: Path, last_year: int = 2018, poison_after: int | None = None) -> Path:
    years = np.arange(1900, last_year + 1)
    rng = np.random.default_rng(3)
    values = 0.01 * (years - 1900) + rng.normal(0, 0.1, len(years))
    if poison_after is not None:
        values[years > poison_after] = 99.0
    lines = [f"{y} {v:.3f} " + " ".join(["0.0"] * 10) for y, v in zip(years, values, strict=True)]
    path = tmp_path / "gmst.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


def _t7(path: Path) -> dict[str, object]:
    return {"kind": "final_temp_gmst_scaling", "params": {"n_cities": 3, "gmst_path": str(path)}}


def _build(kind: str, params: dict[str, object]) -> Forecaster:
    spec = get_kind(kind)
    return spec.build(spec.make_spec(params))


def _swap(*components: dict[str, object]) -> Forecaster:
    return _build("swap_metric", {"metric": TEMP, "base": BASE, "components": list(components)})


def _master() -> pd.DataFrame:
    return make_climate_master(seed=7)


def _train(master: pd.DataFrame) -> pd.DataFrame:
    return master.loc[master["Year"] <= CUTOFF].copy()


def _values(frame: pd.DataFrame) -> pd.Series:
    rows = frame.loc[frame["metric"] == TEMP]
    return rows.set_index(["city_id", "year"])["predicted_value"].sort_index()


def test_components_change_only_temperature(tmp_path: Path) -> None:
    train = _train(_master())
    base = _build("lead_blend", {})(train, CUTOFF, YEARS)
    late = {"kind": "swap_metric", "params": {"metric": TEMP, "components": [BASE, T2, T3]}}
    switch = {
        "kind": "final_temp_lead_switch",
        "params": {"early": BASE, "late": late, "last_early_lead": 3},
    }
    for components in ([T1], [T2], [T3], [_t7(_gmst_file(tmp_path))], [BASE, T2, T3], [switch]):
        swapped = _swap(*components)(train, CUTOFF, YEARS)
        assert changed_metrics(base, swapped) == {TEMP}
        assert np.isfinite(swapped["predicted_value"]).all()


def test_t6_keeps_lead_split3_in_years_1_to_3_and_t5_later() -> None:
    train = _train(_master())
    t0 = _values(_build("lead_blend", {})(train, CUTOFF, YEARS))
    t5 = _values(_swap(BASE, T2, T3)(train, CUTOFF, YEARS))
    late = {"kind": "swap_metric", "params": {"metric": TEMP, "components": [BASE, T2, T3]}}
    switch = {"kind": "final_temp_lead_switch", "params": {"early": BASE, "late": late}}
    t6 = _values(_swap(switch)(train, CUTOFF, YEARS))
    early = t6.index.get_level_values("year") <= CUTOFF + 3
    assert np.allclose(t6[early], t0[early])
    assert np.allclose(t6[~early], t5[~early])
    assert not np.allclose(t6[~early], t0[~early])


def test_t2_mixes_view_and_t1() -> None:
    train = _train(_master())
    t1 = _values(_build(T1["kind"], SMALL)(train, CUTOFF, YEARS))
    t2 = _values(_build(T2["kind"], SMALL)(train, CUTOFF, YEARS))
    view = _values(_build(T2["kind"], {**SMALL, "view_weight": 1.0})(train, CUTOFF, YEARS))
    assert np.allclose(t2, 0.75 * view + 0.25 * t1)


def test_recent_normal_matches_hand_calculation() -> None:
    train = _train(_master())
    forecast = _values(_build(T1["kind"], {"n_cities": 1})(train, CUTOFF, YEARS))
    city = sorted(train["ID"].unique())[0]
    own = train.loc[train["ID"] == city].set_index("Year")["Avg Temp"]
    recent = own.loc[CUTOFF - 14 :]
    window = own.loc[CUTOFF - 39 :]
    slope = np.polyfit(window.index.to_numpy(float), window.to_numpy(), 1)[0]
    expected = recent.mean() + slope * (2005 - recent.index.to_numpy().mean())
    assert forecast[(city, 2005)] == pytest.approx(expected)


@pytest.mark.parametrize("component", [T1, T2, T3])
def test_components_ignore_and_reject_rows_after_cutoff(component: dict[str, object]) -> None:
    master = _master()
    poisoned = master.copy()
    poisoned.loc[poisoned["Year"] > CUTOFF, ["Avg Temp", "cdd", "ToT Prcp", "Max Tmax"]] = 999.0
    forecaster = _build(str(component["kind"]), dict(component["params"]))  # type: ignore[call-overload]  # test dict
    clean = forecaster(_train(master), CUTOFF, YEARS)
    again = forecaster(_train(poisoned), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, again)
    with pytest.raises(ClimateDataError):
        forecaster(poisoned, CUTOFF, YEARS)  # unsliced rows after the cut-off are refused
    moved = master.copy()
    moved.loc[moved["Year"] == CUTOFF, "Avg Temp"] += 5.0  # positive control
    assert not np.allclose(_values(forecaster(_train(moved), CUTOFF, YEARS)), _values(clean))


def test_gmst_scaling_ignores_gmst_after_fold_cutoff(tmp_path: Path) -> None:
    train = _train(_master())
    clean_dir, poisoned_dir = tmp_path / "a", tmp_path / "b"
    clean_dir.mkdir()
    poisoned_dir.mkdir()
    clean = _build("final_temp_gmst_scaling", _t7(_gmst_file(clean_dir))["params"])  # type: ignore[arg-type]  # test dict
    poisoned = _build(
        "final_temp_gmst_scaling",
        _t7(_gmst_file(poisoned_dir, poison_after=CUTOFF))["params"],  # type: ignore[arg-type]  # test dict
    )
    pd.testing.assert_frame_equal(clean(train, CUTOFF, YEARS), poisoned(train, CUTOFF, YEARS))
    leaky_dir = tmp_path / "c"
    leaky_dir.mkdir()
    leaky = _build("final_temp_gmst_scaling", _t7(_gmst_file(leaky_dir, 2019))["params"])  # type: ignore[arg-type]  # test dict
    with pytest.raises(ClimateDataError, match="2019"):
        leaky(train, CUTOFF, YEARS)


def test_weighted_median_and_area_weights() -> None:
    values = np.array([1.0, 2.0, 3.0, np.nan])
    assert weighted_median(values, np.array([1.0, 1.0, 1.0, 5.0])) == 2.0
    assert weighted_median(values, np.array([0.1, 0.1, 1.0, 1.0])) == 3.0
    assert np.isnan(weighted_median(np.array([np.nan]), np.array([1.0])))
    coords = pd.DataFrame(
        {"Lat": [40.0, 40.0, 30.0], "Lon": [-100.0, -100.5, -80.0]}, index=["a", "b", "c"]
    )
    weights = area_weights(coords, 300.0)
    assert weights.sum() == pytest.approx(1.0)
    assert weights["c"] == pytest.approx(2 * weights["a"])  # c is alone, a and b share


def test_bias_corrected_ar1_recovers_persistence() -> None:
    rng = np.random.default_rng(0)
    phi, n_years, n_cities = 0.5, 30, 400
    series = np.zeros((n_cities, n_years))
    series[:, 0] = rng.normal(0, 1 / np.sqrt(1 - phi**2), n_cities)
    for t in range(1, n_years):
        series[:, t] = phi * series[:, t - 1] + rng.normal(0, 1, n_cities)
    estimate = bias_corrected_ar1(pd.DataFrame(series))
    demeaned = series - series.mean(axis=1, keepdims=True)
    raw = (demeaned[:, 1:] * demeaned[:, :-1]).sum() / (demeaned[:, :-1] ** 2).sum()
    # Kendall's per-series correction slightly over-corrects the pooled ratio (about +0.025
    # here, raw about -0.055); the pre-registered formula is kept, see the trial note.
    assert abs(estimate - phi) < 0.05
    assert abs(estimate - phi) < abs(raw - phi)


def test_shrinkage_and_gmst_line() -> None:
    slopes = pd.DataFrame(
        {"slope": [1.0, 3.0, 4.0, np.nan], "se": [0.1, 0.1, 1.0, np.nan]},
        index=["a", "b", "c", "d"],
    )
    weights = pd.DataFrame(0.25, index=slopes.index, columns=slopes.index)
    shrunk = shrunk_slopes(slopes, weights)
    assert shrunk["d"] == pytest.approx(8.0 / 3)  # no own slope: regional mean
    assert abs(shrunk["a"] - 1.0) < 0.05 * abs(shrunk["c"] - 4.0)  # precise slopes move less
    assert 8.0 / 3 < shrunk["c"] < 4.0
    gmst = pd.Series(np.linspace(1.0, 0.0, 40), index=range(1961, 2001))
    assert gmst_line(gmst, 2000, 30)[2] == 0.0  # cooling GMST trend is floored


def test_helpers_weights_and_slopes() -> None:
    coords = city_coordinates(_master())
    weights = nearest_with_self(coords, 3)
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert np.allclose(np.diag(weights), 1.0 / 3)
    table = pd.DataFrame([[1.0, 3.0, 5.0, np.nan]], columns=[2000, 2001, 2002, 2003])
    assert ols_slopes(table, min_years=3)["slope"].iloc[0] == pytest.approx(2.0)
    assert np.isnan(ols_slopes(table, min_years=4)["slope"].iloc[0])
