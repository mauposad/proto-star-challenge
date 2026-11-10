"""Tests for the round-1 family kinds: paired bootstrap, summer table, H4/H11, H2/H14, H1."""

import math

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.backtest import (
    baseline_forecaster,
    compare_forecasters,
    fold_rows,
    paired_year_bootstrap,
)
from proto_star.data.summer import join_summer, summer_means
from proto_star.hottest import HottestSummerSpec, hottest_summer_forecast
from proto_star.levels import LevelAdjustSpec, level_adjust_forecast
from proto_star.neighbours import NeighbourSpec, neighbour_forecast

KEY = ["city_id", "year", "metric"]
CUTOFF = 2000
YEARS = list(range(2001, 2008))


def _master(first: int = 1930, last: int = 2018, noise: float = 1.0) -> pd.DataFrame:
    """Six cities in two regions, with a shared trend, noise, and June-August columns."""
    rng = np.random.default_rng(7)
    rows = []
    for offset, city in enumerate("ABCDEF"):
        for year in range(first, last + 1):
            trend = 0.03 * (year - first)
            temp = 50.0 + 2 * offset + trend + noise * rng.normal()
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Lat": 30.0 + 0.5 * offset,
                    "Lon": -100.0 + 0.5 * offset,
                    "region": "South" if offset < 3 else "North",
                    "Station Segment": 1 if year < 1980 else 2,
                    "Avg Temp": temp,
                    "ToT Prcp": 30.0 + offset + 3 * math.sin(year + offset) + noise * rng.normal(),
                    "Max Tmax": 95.0 + trend + noise * rng.normal(),
                    "cdd": 1000.0 + 100.0 * (temp - 50.0),
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                    "jja_tmax": 88.0 + trend + noise * rng.normal(),
                }
            )
    return pd.DataFrame(rows)


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def test_paired_bootstrap_reproduces_the_official_raw_score_difference() -> None:
    master = _master()
    a, b = baseline_forecaster("thirty_year_mean"), baseline_forecaster("ten_year_mean")
    cutoffs = [1980, 1995, 2011]
    official = compare_forecasters({"a": a, "b": b}, master, cutoffs=cutoffs)
    for window in ("all", "years_1_3", "years_4_7"):
        scores = official.loc[official["window"] == window].groupby("method")["raw_score"].mean()
        result = paired_year_bootstrap(
            fold_rows(a, master, cutoffs=cutoffs),
            fold_rows(b, master, cutoffs=cutoffs),
            window=window,
        )
        assert result["difference"] == pytest.approx(scores["b"] - scores["a"], abs=1e-9)
        assert result["low"] <= result["difference"] <= result["high"]


def test_summer_means_blank_short_summers_and_join_one_to_one() -> None:
    days = pd.date_range("2001-06-01", "2001-08-31")
    short = pd.date_range("2002-06-01", "2002-08-20")  # 81 days
    daily = pd.DataFrame(
        {
            "ID": "A",
            "Date": [*days, *short],
            "tmax": [90.0] * len(days) + [80.0] * len(short),
            "tmin": [70.0] * (len(days) + len(short)),
        }
    )
    table = summer_means(daily).set_index("Year")
    assert table.loc[2001, "jja_tmax"] == pytest.approx(90.0)
    assert table.loc[2001, "jja_tavg"] == pytest.approx(80.0)
    assert math.isnan(table.loc[2002, "jja_tmax"])
    master = pd.DataFrame({"ID": ["A", "A", "A"], "Year": [2000, 2001, 2002]})
    joined = join_summer(master, table.reset_index())
    assert len(joined) == 3 and math.isnan(joined.loc[0, "jja_tmax"])


def test_level_adjust_without_residuals_or_regional_spread_changes_nothing() -> None:
    master = _master(noise=0.0)
    train = master.loc[master["Year"] <= CUTOFF]
    base = baseline_forecaster("ten_year_mean")
    plain = _indexed(base(train, CUTOFF, YEARS))
    for params in ({"common_residual": True}, {"shrink": "region"}):
        spec = LevelAdjustSpec(base="ten_year_mean", **params)
        adjusted = _indexed(level_adjust_forecast(base, train, CUTOFF, YEARS, spec))
        pd.testing.assert_series_equal(adjusted, plain, atol=1e-6)


def test_level_adjust_rejects_metrics_it_does_not_handle() -> None:
    with pytest.raises(ValidationError):
        LevelAdjustSpec(base="x", metrics=["total_precip_in"])


def test_hottest_constant_shift_is_the_mean_of_the_slope_shift() -> None:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    base = baseline_forecaster("thirty_year_mean")
    slope = _indexed(
        hottest_summer_forecast(
            base, train, CUTOFF, YEARS, HottestSummerSpec(base="b", arm="jja_slope")
        )
    )
    flat = _indexed(
        hottest_summer_forecast(
            base, train, CUTOFF, YEARS, HottestSummerSpec(base="b", arm="constant_shift")
        )
    )
    hottest = slope.index.get_level_values("metric") == "hottest_day_temp"
    assert slope[hottest].mean() == pytest.approx(flat[hottest].mean())
    assert slope[hottest].std() > flat[hottest].std()
    other = ~hottest
    pd.testing.assert_series_equal(slope[other], flat[other])


def test_hottest_summer_needs_the_summer_columns() -> None:
    train = _master().drop(columns="jja_tmax").loc[lambda m: m["Year"] <= CUTOFF]
    spec = HottestSummerSpec(base="b", arm="summer_level")
    with pytest.raises(ValueError, match="join_summer"):
        hottest_summer_forecast(baseline_forecaster("thirty_year_mean"), train, CUTOFF, YEARS, spec)


def test_neighbour_placebo_is_reproducible_and_covers_every_row() -> None:
    train = _master().loc[lambda m: m["Year"] <= CUTOFF]
    base = baseline_forecaster("thirty_year_mean")
    spec = NeighbourSpec(base="b", arm="placebo", placebo_min_km=1.0, seed=3)
    first = neighbour_forecast(base, train, CUTOFF, YEARS, spec)
    second = neighbour_forecast(base, train, CUTOFF, YEARS, spec)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 6 * len(YEARS) * 4
    assert np.isfinite(first["predicted_value"]).all()


def test_neighbour_anchor_of_a_constant_series_is_its_mean() -> None:
    master = _master(noise=0.0)
    master["ToT Prcp"] = 30.0 + master["ID"].map({c: i for i, c in enumerate("ABCDEF")})
    train = master.loc[master["Year"] <= CUTOFF]
    base = baseline_forecaster("thirty_year_mean")
    spec = NeighbourSpec(base="b", arm="anchored", metrics=["total_precip_in"])
    anchored = _indexed(neighbour_forecast(base, train, CUTOFF, YEARS, spec))
    plain = _indexed(base(train, CUTOFF, YEARS))
    pd.testing.assert_series_equal(anchored, plain, atol=1e-9)
