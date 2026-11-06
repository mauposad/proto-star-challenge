"""Build the team's shared annual master table from the raw ProtoStar tables.

The master table corrects only what is provably not a measurement and flags everything
else, so every row of ``annual_indices`` survives.  It deliberately contains no imputed
values, station adjustments, or per-city statistics: those depend on which years are
known, so computing them over 1851-2018 here would leak later years into backtests.
Compute them inside each backtest fold instead.  Every added column uses only the
row's own year or earlier years.
"""

from __future__ import annotations

import calendar
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import (
    METRICS,
    ClimateDataError,
    annual_to_long,
    assert_weather_cutoff,
    metric_valid_mask,
)
from proto_star.data.protostar import assign_region
from proto_star.paths import PROCESSED_DIR

MASTER_DIR = PROCESSED_DIR / "protostar"
MASTER_FILE = "annual_master.parquet"
MANIFEST_FILE = "annual_master.manifest.json"

# Columns that read as a number in a year with no observations of the variable.
NO_DATA_COLUMNS: dict[str, tuple[str, ...]] = {
    "Miss Prcp": ("ToT Prcp", "Wet Days", "Max 1-day P", "Max 5-day P"),
    "Miss Tmax": ("Warm Days", "Cold Days"),
    "Miss Tmin": ("Warm Nights", "Cold Nights"),
}
EXTREME_COLD_F = -50.0
EXTREME_PRECIP_IN = 10.0
MAX_SHORT_CDD_DAYS = 10
DAILY_FLAG_COLUMNS = ("days_tmax_below_tmin", "days_extreme_cold", "days_extreme_precip")


def days_in_year(years: pd.Series) -> pd.Series:
    """Return 365 or 366 for each calendar year."""
    return years.map(lambda year: 366 if calendar.isleap(int(year)) else 365).astype("int64")


def clean_annual(annual: pd.DataFrame) -> pd.DataFrame:
    """Blank values that are artifacts of having no data, and change nothing else.

    ``±inf`` becomes NaN, as do the columns in :data:`NO_DATA_COLUMNS` when the year has
    no observations of that variable.  Partially missing years keep their values: use
    the ``valid_*`` flags to screen them.
    """
    cleaned = annual.copy()
    numeric = cleaned.select_dtypes("number").columns
    cleaned[numeric] = cleaned[numeric].replace([np.inf, -np.inf], np.nan)
    year_length = days_in_year(cleaned["Year"])
    for missing_column, columns in NO_DATA_COLUMNS.items():
        no_data = cleaned[missing_column] >= year_length
        cleaned.loc[no_data, list(columns)] = np.nan
    return cleaned


def daily_quality_counts(daily: pd.DataFrame) -> pd.DataFrame:
    """Count flagged days per city and year.  These are flags, not corrections."""
    flags = pd.DataFrame(
        {
            "ID": daily["ID"].astype(str),
            "Year": pd.to_datetime(daily["Date"]).dt.year.astype("int64"),
            "days_tmax_below_tmin": daily["tmax"] < daily["tmin"],
            "days_extreme_cold": daily["tmin"] < EXTREME_COLD_F,
            "days_extreme_precip": daily["prcp"] > EXTREME_PRECIP_IN,
        }
    )
    flagged = flags.loc[flags[list(DAILY_FLAG_COLUMNS)].any(axis=1)]
    return flagged.groupby(["ID", "Year"], as_index=False)[list(DAILY_FLAG_COLUMNS)].sum()


def _years_since_switch(frame: pd.DataFrame) -> pd.Series:
    """Years since the latest station switch at or before each row (NA before any switch)."""
    ordered = frame.sort_values(["ID", "Year"])
    switch_year = ordered["Year"].where(ordered["Station Changes"] > 0)
    latest = switch_year.groupby(ordered["ID"]).ffill()
    return (ordered["Year"] - latest).astype("Int64").reindex(frame.index)


def build_annual_master(
    annual: pd.DataFrame, coverage: pd.DataFrame, daily: pd.DataFrame
) -> pd.DataFrame:
    """Join, clean, and flag the raw tables into one row per city and year."""
    master = clean_annual(annual)
    for metric in METRICS:
        master[f"valid_{metric}"] = metric_valid_mask(annual, metric)

    station_columns = ["ID", "Year", "Days Both", "Station Segment", "Station Changes"]
    master = master.merge(coverage[station_columns], on=["ID", "Year"], how="left", validate="1:1")
    if master["Days Both"].isna().any():
        raise ClimateDataError("coverage_and_stations has no row for some annual rows")

    short_days = days_in_year(master["Year"]) - master["Days Both"]
    master["cdd_days_short"] = short_days > MAX_SHORT_CDD_DAYS
    master["years_since_switch"] = _years_since_switch(master)
    master["region"] = assign_region(master["Lat"], master["Lon"]).astype(str)

    master = master.merge(daily_quality_counts(daily), on=["ID", "Year"], how="left")
    for column in DAILY_FLAG_COLUMNS:
        master[column] = master[column].fillna(0).astype("int64")
    return master.sort_values(["ID", "Year"], ignore_index=True)


def verify_master(master: pd.DataFrame, annual: pd.DataFrame) -> None:
    """Fail unless the master table keeps every row and every scored value of the raw table."""
    assert_weather_cutoff(master, name="annual_master")
    if len(master) != len(annual):
        raise ClimateDataError(f"master has {len(master)} rows, raw table has {len(annual)}")
    if master.duplicated(["ID", "Year"]).any():
        raise ClimateDataError("master has duplicate city/year rows")
    numeric = master.select_dtypes("number")
    if np.isinf(numeric.astype("float64")).any(axis=None):
        raise ClimateDataError("master still contains infinite values")

    key = ["city_id", "metric", "year"]
    expected = annual_to_long(annual).sort_values(key, ignore_index=True)
    actual = annual_to_long(master).sort_values(key, ignore_index=True)
    if not expected.equals(actual):
        raise ClimateDataError("master changed a value that the official scoring screen keeps")


def content_hash(master: pd.DataFrame) -> str:
    """Hash table contents, so teammates can compare builds regardless of file encoding."""
    row_hashes = pd.util.hash_pandas_object(master, index=False).to_numpy()
    columns = ",".join(master.columns).encode()
    return hashlib.sha256(columns + row_hashes.tobytes()).hexdigest()


def load_master(data_dir: Path | None = None) -> pd.DataFrame:
    """Read the master table, enforcing the forecast cutoff."""
    path = (data_dir or MASTER_DIR) / MASTER_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python scripts/build_master_dataset.py` "
            "(see docs/data.md)."
        )
    master = pd.read_parquet(path)
    assert_weather_cutoff(master, name="annual_master")
    return master
