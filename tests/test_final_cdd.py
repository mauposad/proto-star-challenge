from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster
from proto_star.data import daily_fold
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import final_cdd, get_kind
from proto_star.forecasters.final_cdd import days_in_year, map_cdd
from proto_star.forecasters.swap_metric import changed_metrics

KEY = ["city_id", "year", "metric"]
CUTOFF = 2000
YEARS = list(range(2001, 2008))
T0 = {"kind": "lead_blend", "params": {}}
C1 = {"kind": "cdd_daily_map", "params": {"temperature": T0, "windows": [10]}}
C2 = {
    "kind": "cdd_daily_map",
    "params": {"temperature": T0, "base": "complete_calendar", "windows": [30, 10]},
}
TREND = {
    "kind": "pooled_trend",
    "params": {"level_years": [10, 15], "trend_window": 40, "cdd_sensitivity": True},
}
RIDGE = {"kind": "cdd_ridge", "params": {}}


def _daily(master: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Daily rows for the synthetic cities: a seasonal cycle around each year's Avg Temp."""
    rng = np.random.default_rng(seed)
    frames = []
    for (city, year), avg in master.set_index(["ID", "Year"])["Avg Temp"].items():
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        season = 20.0 * np.sin(2 * np.pi * (dates.day_of_year.to_numpy() - 105) / 365.0)
        mean = avg + season + rng.normal(0, 4, len(dates))
        frames.append(
            pd.DataFrame(
                {
                    "ID": city,
                    "Name": city,
                    "Date": dates,
                    "tmax": mean + 10.0,
                    "tmin": mean - 10.0,
                    "prcp": 0.1,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


@pytest.fixture
def master() -> pd.DataFrame:
    return make_climate_master(first_year=1950, last_year=2010, seed=3)


def _use_daily(monkeypatch: pytest.MonkeyPatch, directory: Path, daily: pd.DataFrame) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(directory / "daily.parquet", index=False)
    monkeypatch.setattr(
        final_cdd, "daily_to_cutoff", partial(daily_fold.daily_to_cutoff, data_dir=directory)
    )


def _build(entry: dict[str, object]) -> Forecaster:
    kind = get_kind(str(entry["kind"]))
    params = entry["params"]
    assert isinstance(params, dict)
    return kind.build(kind.make_spec(params))


def _swap(*components: dict[str, object], weights: list[float] | None = None) -> Forecaster:
    params: dict[str, object] = {"metric": "cdd", "components": list(components)}
    if weights is not None:
        params["weights"] = weights
    return _build({"kind": "swap_metric", "params": params})


def _cdd(frame: pd.DataFrame) -> pd.Series:
    rows = frame.loc[frame["metric"] == "cdd"]
    return rows.set_index(["city_id", "year"])["predicted_value"].sort_index()


def test_unshifted_map_reproduces_the_recount() -> None:
    rng = np.random.default_rng(1)
    days = rng.normal(60, 15, 365 * 3)
    groups = np.repeat([1990, 1991, 1992], 365)
    for year in (1990, 1991, 1992):
        own = days[groups == year]
        recount = np.maximum(own - 65.0, 0.0).sum()
        mapped = map_cdd(own, np.full(len(own), year), np.array([own.mean()]))
        assert mapped[0] == pytest.approx(recount)
    target = np.array([62.0, 70.0])
    expected = [
        np.mean(
            [
                np.maximum(days[groups == y] - days[groups == y].mean() + t - 65, 0).sum()
                for y in (1990, 1991, 1992)
            ]
        )
        for t in target
    ]
    assert np.allclose(map_cdd(days, groups, target), expected)
    assert (np.diff(map_cdd(days, groups, np.array([55.0, 60.0, 65.0]))) > 0).all()


def test_days_in_year_counts_leap_years() -> None:
    assert days_in_year(np.array([1900, 1996, 2000, 2018])).tolist() == [365, 366, 366, 365]


def test_map_changes_only_cdd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, master: pd.DataFrame
) -> None:
    _use_daily(monkeypatch, tmp_path, _daily(master))
    train = master.loc[master["Year"] <= CUTOFF].copy()
    default = _build(T0)(train, CUTOFF, YEARS)
    for candidate in (
        _swap(C1),
        _swap(C2),
        _swap(C1, T0, weights=[0.5, 0.5]),
        _swap(TREND, RIDGE, C1),
    ):
        assert changed_metrics(default, candidate(train, CUTOFF, YEARS)) == {"cdd"}


def test_trend_and_ridge_halves_give_back_the_default_cdd(master: pd.DataFrame) -> None:
    train = master.loc[master["Year"] <= CUTOFF].copy()
    default = _build(T0)(train, CUTOFF, YEARS)
    halves = _swap(TREND, RIDGE, weights=[0.5, 0.5])(train, CUTOFF, YEARS)
    assert changed_metrics(default, halves) == set()


def test_map_is_the_mean_of_shifted_recounts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, master: pd.DataFrame
) -> None:
    daily = _daily(master)
    _use_daily(monkeypatch, tmp_path, daily)
    train = master.loc[master["Year"] <= CUTOFF].copy()
    mapped = _cdd(_build(C1)(train, CUTOFF, YEARS))
    temperature = _build(T0)(train, CUTOFF, YEARS)
    target = temperature.loc[
        (temperature["metric"] == "annual_avg_temp")
        & (temperature["city_id"] == "NC")
        & (temperature["year"] == 2003),
        "predicted_value",
    ].iloc[0]
    tm = (daily["tmax"] + daily["tmin"]) / 2
    counts = []
    for year in range(1991, 2001):  # the last 10 valid years
        own = tm[(daily["ID"] == "NC") & (daily["Date"].dt.year == year)].to_numpy()
        counts.append(np.maximum(own - own.mean() + target - 65.0, 0.0).sum())
    assert mapped.loc[("NC", 2003)] == pytest.approx(np.mean(counts))


def test_map_ignores_everything_after_the_cutoff(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, master: pd.DataFrame
) -> None:
    daily = _daily(master)
    train = master.loc[master["Year"] <= CUTOFF].copy()
    _use_daily(monkeypatch, tmp_path / "clean", daily)
    clean = {name: _build(e)(train, CUTOFF, YEARS) for name, e in (("c1", C1), ("c2", C2))}

    poisoned = daily.copy()
    later = poisoned["Date"].dt.year > CUTOFF
    poisoned.loc[later, ["tmax", "tmin"]] = 500.0
    poisoned_master = master.copy()
    poisoned_master.loc[poisoned_master["Year"] > CUTOFF, ["Avg Temp", "cdd"]] = 1e6
    poisoned_train = poisoned_master.loc[poisoned_master["Year"] <= CUTOFF].copy()
    _use_daily(monkeypatch, tmp_path / "poisoned", poisoned)
    for name, entry in (("c1", C1), ("c2", C2)):
        again = _build(entry)(poisoned_train, CUTOFF, YEARS)
        pd.testing.assert_frame_equal(clean[name], again)

    moved = daily.copy()
    # Positive control: a hotter July at the cut-off changes that base year's shape. (A uniform
    # shift would not move the map, which removes each base year's own mean.)
    july = (moved["Date"].dt.year == CUTOFF) & (moved["Date"].dt.month == 7)
    moved.loc[july, ["tmax", "tmin"]] += 10.0
    _use_daily(monkeypatch, tmp_path / "moved", moved)
    shifted = _cdd(_build(C1)(train, CUTOFF, YEARS))
    assert not np.allclose(shifted.to_numpy(), _cdd(clean["c1"]).to_numpy())


def test_complete_years_and_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, master: pd.DataFrame
) -> None:
    daily = _daily(master)
    # NE loses one day in each of its last 10 years: not complete, still valid for C1.
    gaps = (daily["ID"] == "NE") & (daily["Date"].dt.year > CUTOFF - 10)
    gaps &= (daily["Date"].dt.month == 7) & (daily["Date"].dt.day == 1)
    daily = daily.loc[~gaps]
    # SW has no daily data at all: it keeps the temperature model's CDD.
    daily = daily.loc[daily["ID"] != "SW"]
    _use_daily(monkeypatch, tmp_path, daily)
    train = master.loc[master["Year"] <= CUTOFF].copy()
    default = _cdd(_build(T0)(train, CUTOFF, YEARS))
    c2 = _cdd(_build(C2)(train, CUTOFF, YEARS))
    only30 = {
        "kind": "cdd_daily_map",
        "params": {"temperature": T0, "base": "complete_calendar", "windows": [30]},
    }
    c30 = _cdd(_build(only30)(train, CUTOFF, YEARS))
    assert np.allclose(c2.loc["SW"], default.loc["SW"])
    assert np.allclose(c2.loc["NE"], c30.loc["NE"])  # the 10-year window has no complete year
    assert not np.allclose(c2.loc["NC"], c30.loc["NC"])
    c1 = _cdd(_build(C1)(train, CUTOFF, YEARS))
    assert not np.allclose(c1.loc["NE"], default.loc["NE"])


def test_spec_rejects_bad_settings() -> None:
    kind = get_kind("cdd_daily_map")
    with pytest.raises(ValueError, match="cdd_daily_map"):
        kind.make_spec({"base": "everything"})
    with pytest.raises(ValueError, match="cdd_daily_map"):
        kind.make_spec({"windows": []})
    assert "last 10 valid years" in kind.make_spec({}).describe()
