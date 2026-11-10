from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster
from proto_star.climate import ClimateDataError
from proto_star.data.daily_fold import daily_to_cutoff
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import final_hottest, get_kind
from proto_star.forecasters._final_common import thirty_year_rows
from proto_star.forecasters.final_hottest import METRIC, yearly_top_two
from proto_star.forecasters.swap_metric import changed_metrics

CUTOFF = 2000
YEARS = list(range(2001, 2008))
BASE = {"kind": "pooled_trend", "params": {"level_years": [10, 15], "trend_window": 40}}
NUDGE = {"kind": "final_hottest_nudge", "params": {"k": 3}}
SECOND = {"kind": "final_hottest_second_high", "params": {"bandwidth_km": 300.0}}


def _master() -> pd.DataFrame:
    return make_climate_master(first_year=1950, seed=7)


def _daily(
    master: pd.DataFrame, *, spacing: float = 2.0, short_city: str | None = None
) -> pd.DataFrame:
    """Each year: 80 F every day but two hot days, ``Max Tmax`` and ``Max Tmax - spacing``."""
    frames = []
    for city, year, hottest in master[["ID", "Year", "Max Tmax"]].itertuples(index=False):
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        if city == short_city:
            dates = dates[:300]
        tmax = np.full(len(dates), 80.0)
        tmax[100] = hottest
        tmax[200] = hottest - spacing
        frames.append(pd.DataFrame({"ID": city, "Name": city, "Date": dates, "tmax": tmax}))
    daily = pd.concat(frames, ignore_index=True)
    daily["tmin"] = daily["tmax"] - 20.0
    daily["prcp"] = 0.1
    return daily


def _use_daily(monkeypatch: pytest.MonkeyPatch, directory: Path, daily: pd.DataFrame) -> None:
    directory.mkdir(parents=True)
    daily.to_parquet(directory / "daily.parquet", index=False)

    def reader(cutoff_year: int, columns: Sequence[str] = ("tmax",)) -> pd.DataFrame:
        return daily_to_cutoff(cutoff_year, data_dir=directory, columns=columns)

    monkeypatch.setattr(final_hottest, "daily_to_cutoff", reader)


def _build(entry: dict) -> Forecaster:
    kind = get_kind(entry["kind"])
    return kind.build(kind.make_spec(entry["params"]))


def _values(frame: pd.DataFrame) -> pd.Series:
    rows = frame.loc[frame["metric"] == METRIC].sort_values(["city_id", "year"])
    return rows.set_index(["city_id", "year"])["predicted_value"]


def _swap(component: dict) -> Forecaster:
    params = {"metric": METRIC, "base": BASE, "components": [component]}
    return _build({"kind": "swap_metric", "params": params})


@pytest.mark.parametrize("component", [NUDGE, SECOND])
def test_component_changes_only_hottest_day(
    component: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    master = _master()
    _use_daily(monkeypatch, tmp_path / "daily", _daily(master))
    train = master.loc[master["Year"] <= CUTOFF]
    base = _swap(BASE)(train, CUTOFF, YEARS)
    assert changed_metrics(base, _swap(component)(train, CUTOFF, YEARS)) == {METRIC}


@pytest.mark.parametrize("component", [NUDGE, SECOND])
def test_component_ignores_poisoned_future_rows(
    component: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    master = _master()
    forecaster = _build(component)
    _use_daily(monkeypatch, tmp_path / "clean", _daily(master))
    clean = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)

    poisoned = master.copy()
    poisoned.loc[poisoned["Year"] > CUTOFF, ["Max Tmax", "ToT Prcp", "Avg Temp", "cdd"]] = 999.0
    poisoned_daily = _daily(master)
    poisoned_daily.loc[poisoned_daily["Date"].dt.year > CUTOFF, "tmax"] = 999.0
    _use_daily(monkeypatch, tmp_path / "poisoned", poisoned_daily)
    dirty = forecaster(poisoned.loc[poisoned["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, dirty)
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        forecaster(poisoned, CUTOFF, YEARS)

    moved = master.copy()
    moved.loc[moved["Year"].between(CUTOFF - 4, CUTOFF), "Max Tmax"] += 5.0
    _use_daily(monkeypatch, tmp_path / "moved", _daily(moved))
    shifted = forecaster(moved.loc[moved["Year"] <= CUTOFF], CUTOFF, YEARS)
    assert not np.allclose(_values(shifted), _values(clean))


def test_yearly_top_two_counts_ties() -> None:
    daily = pd.DataFrame(
        {
            "ID": ["A"] * 4 + ["B"] * 3,
            "Date": pd.to_datetime(
                ["2000-01-01", "2000-06-01", "2000-07-01", "2000-08-01"] * 1
                + ["2000-01-01", "2000-06-01", "2000-07-01"]
            ),
            "tmax": [70.0, 95.0, 95.0, np.nan, 60.0, 90.0, 88.0],
        }
    )
    top = yearly_top_two(daily).set_index("city_id")
    assert top.loc["A", ["days", "top1", "top2"]].tolist() == [3, 95.0, 95.0]
    assert top.loc["B", ["days", "top1", "top2"]].tolist() == [3, 90.0, 88.0]


def test_second_high_is_level_plus_pooled_spacing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    master = _master()
    _use_daily(monkeypatch, tmp_path / "daily", _daily(master, spacing=2.0))
    train = master.loc[master["Year"] <= CUTOFF]
    values = _values(_build(SECOND)(train, CUTOFF, YEARS))
    window = train.loc[train["Year"] > CUTOFF - 30]
    expected = window.groupby("ID")["Max Tmax"].mean()  # second-highest + 2, spacing pooled = 2
    for city, value in expected.items():
        assert np.allclose(values.loc[city], value)


def test_second_high_keeps_the_mean_without_complete_years(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    master = _master()
    city = str(master["ID"].iloc[0])
    _use_daily(monkeypatch, tmp_path / "daily", _daily(master, short_city=city))
    train = master.loc[master["Year"] <= CUTOFF]
    m30 = _values(thirty_year_rows(train, CUTOFF, YEARS, METRIC))
    values = _values(_build(SECOND)(train, CUTOFF, YEARS))
    assert np.allclose(values.loc[city], m30.loc[city])


def test_nudge_follows_a_local_shift() -> None:
    master = _master()
    city = master["ID"].iloc[1]
    master.loc[(master["ID"] == city) & (master["Year"] > CUTOFF - 10), "Max Tmax"] += 4.0
    train = master.loc[master["Year"] <= CUTOFF]
    m30 = _values(thirty_year_rows(train, CUTOFF, YEARS, METRIC))
    nudged = _values(_build(NUDGE)(train, CUTOFF, YEARS))
    assert (nudged.loc[city] > m30.loc[city]).all()
