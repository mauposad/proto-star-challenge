from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.climate import METRICS, ClimateDataError, annual_to_long
from proto_star.data.master import (
    MASTER_FILE,
    build_annual_master,
    clean_annual,
    content_hash,
    daily_quality_counts,
    days_in_year,
    load_master,
    verify_master,
)


def _annual() -> pd.DataFrame:
    """Four years for one city: 2000 is a leap year, and 2002 has no data at all."""
    return pd.DataFrame(
        {
            "Name": ["A"] * 4,
            "ID": ["X1"] * 4,
            "Lat": [45.0] * 4,
            "Lon": [-120.0] * 4,
            "Year": [2000, 2001, 2002, 2003],
            "Miss Tmax": [365, 0, 365, 11],
            "Miss Tmin": [0, 0, 365, 0],
            "Miss Prcp": [0, 0, 365, 0],
            "Avg Temp": [50.0, 51.0, np.nan, 52.0],
            "Avg Tmax": [60.0, 61.0, np.nan, 62.0],
            "Avg Tmin": [40.0, 41.0, np.nan, 42.0],
            "ToT Prcp": [0.0, 30.0, 0.0, 31.0],
            "Max Tmax": [90.0, 91.0, -np.inf, 92.0],
            "Min Tmax": [10.0, 11.0, np.inf, 12.0],
            "Max Tmin": [70.0, 71.0, -np.inf, 72.0],
            "Min Tmin": [-5.0, -4.0, np.inf, -3.0],
            "Warm Days": [0.0, 12.0, 0.0, 13.0],
            "Warm Nights": [11.0, 12.0, 0.0, 13.0],
            "Cold Days": [9.0, 8.0, 0.0, 7.0],
            "Cold Nights": [9.0, 8.0, 0.0, 7.0],
            "Max 1-day P": [2.0, 2.1, -np.inf, 2.2],
            "Max 5-day P": [3.0, 3.1, 1.5, 3.2],
            "Wet Days": [5.0, 5.1, 0.0, 5.2],
            "cdd": [500.0, 510.0, np.nan, 520.0],
        }
    )


def _coverage() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": ["X1"] * 4,
            "Name": ["A"] * 4,
            "Year": [2000, 2001, 2002, 2003],
            "Days Both": [366, 365, 0, 340],
            "Station Segment": [1, 1, 2, 2],
            "Station Changes": [0, 0, 1, 0],
        }
    )


def _daily() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": ["X1", "X1", "X1", "X1"],
            "Date": ["2001-01-01", "2001-01-02", "2003-07-01", "2003-07-02"],
            "tmax": [10.0, 40.0, 90.0, np.nan],
            "tmin": [12.0, -51.0, 70.0, 60.0],
            "prcp": [0.0, 0.0, 10.5, np.nan],
        }
    )


def _master() -> pd.DataFrame:
    return build_annual_master(_annual(), _coverage(), _daily())


def test_days_in_year_handles_leap_years() -> None:
    assert days_in_year(pd.Series([1900, 2000, 2001])).tolist() == [365, 366, 365]


def test_clean_annual_removes_infinities_and_leaves_input_unchanged() -> None:
    annual = _annual()
    cleaned = clean_annual(annual)
    assert np.isnan(cleaned.loc[2, "Max Tmax"])
    assert np.isnan(cleaned.loc[2, "Max 1-day P"])
    assert np.isinf(annual.loc[2, "Max Tmax"])


@pytest.mark.parametrize(
    "column",
    ["ToT Prcp", "Wet Days", "Max 5-day P", "Warm Days", "Cold Days", "Warm Nights", "Cold Nights"],
)
def test_clean_annual_blanks_fake_values_in_no_data_years(column: str) -> None:
    assert np.isnan(clean_annual(_annual()).loc[2, column])


def test_clean_annual_keeps_real_zero_precipitation() -> None:
    assert clean_annual(_annual()).loc[0, "ToT Prcp"] == 0.0


def test_clean_annual_keeps_values_when_leap_year_has_one_observed_day() -> None:
    assert clean_annual(_annual()).loc[0, "Warm Days"] == 0.0


def test_master_keeps_invalid_rows_and_flags_them() -> None:
    master = _master()
    assert len(master) == 4
    assert master["valid_annual_avg_temp"].tolist() == [False, True, False, False]
    assert master["valid_total_precip_in"].tolist() == [True, True, False, True]


def test_valid_flags_match_official_screen() -> None:
    master = _master()
    history = annual_to_long(_annual())
    for metric in METRICS:
        flagged = set(master.loc[master[f"valid_{metric}"], "Year"])
        assert flagged == set(history.loc[history["metric"] == metric, "year"])


def test_cdd_days_short_flags_years_missing_more_than_ten_days() -> None:
    assert _master()["cdd_days_short"].tolist() == [False, False, True, True]


def test_years_since_switch_is_blank_before_first_switch() -> None:
    values = _master()["years_since_switch"]
    assert values.isna().tolist() == [True, True, False, False]
    assert values.iloc[2:].tolist() == [0, 1]


def test_added_columns_do_not_depend_on_later_years() -> None:
    full = _master()
    early = build_annual_master(
        _annual().iloc[:2], _coverage().iloc[:2], _daily().iloc[:2]
    ).reset_index(drop=True)
    pd.testing.assert_frame_equal(early, full.iloc[:2].reset_index(drop=True))


def test_daily_quality_counts_flags_but_ignores_missing_values() -> None:
    counts = daily_quality_counts(_daily()).set_index("Year")
    assert counts.loc[2001, "days_tmax_below_tmin"] == 1
    assert counts.loc[2001, "days_extreme_cold"] == 1
    assert counts.loc[2003, "days_extreme_precip"] == 1
    assert counts.loc[2003, "days_tmax_below_tmin"] == 0


def test_master_flag_counts_default_to_zero() -> None:
    master = _master().set_index("Year")
    assert master.loc[2000, "days_extreme_cold"] == 0
    assert master.loc[2001, "days_extreme_cold"] == 1


def test_verify_master_accepts_a_correct_build() -> None:
    verify_master(_master(), _annual())


def test_verify_master_rejects_dropped_rows() -> None:
    with pytest.raises(ClimateDataError, match="rows"):
        verify_master(_master().iloc[:3], _annual())


def test_verify_master_rejects_changed_scored_values() -> None:
    master = _master()
    master.loc[1, "cdd"] = 999.0
    with pytest.raises(ClimateDataError, match="changed a value"):
        verify_master(master, _annual())


def test_verify_master_rejects_post_cutoff_rows() -> None:
    master = _master()
    master.loc[3, "Year"] = 2019
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        verify_master(master, _annual())


def test_content_hash_is_stable_and_detects_changes() -> None:
    master = _master()
    assert content_hash(master) == content_hash(_master())
    master.loc[1, "cdd"] = 999.0
    assert content_hash(master) != content_hash(_master())


def test_content_hash_survives_a_parquet_round_trip(tmp_path: Path) -> None:
    master = _master()
    master.to_parquet(tmp_path / MASTER_FILE, index=False)
    assert content_hash(load_master(tmp_path)) == content_hash(master)


def test_load_master_rejects_post_cutoff_file(tmp_path: Path) -> None:
    master = _master()
    master.loc[3, "Year"] = 2019
    master.to_parquet(tmp_path / MASTER_FILE, index=False)
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        load_master(tmp_path)


def test_load_master_explains_how_to_build(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="build_master_dataset"):
        load_master(tmp_path)
