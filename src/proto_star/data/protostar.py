"""Readers and light descriptive helpers for the raw ProtoStar climate tables.

These functions only read and annotate data; they never clean or impute it, so
exploratory notebooks see the tables exactly as downloaded.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import assert_weather_cutoff
from proto_star.paths import RAW_DIR

PROTOSTAR_DIR = RAW_DIR / "protostar"
DAILY_VALUE_COLUMNS = ("tmax", "tmin", "prcp")

# Approximate regions from coordinates only: the raw tables carry no state field.
# Longitude splits roughly follow the Rockies (-104) and the Mississippi/Ohio
# valley (-87); latitude 37 is roughly the Virginia/Kentucky/Missouri line.
REGION_LON_EDGES = (-104.0, -87.0)
REGION_LAT_EDGE = 37.0
REGIONS = (
    "Northwest",
    "Southwest",
    "North Central",
    "South Central",
    "Northeast",
    "Southeast",
)


def _path(name: str, data_dir: Path | None) -> Path:
    path = (data_dir or PROTOSTAR_DIR) / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python scripts/download_protostar_data.py` "
            "(see docs/data.md)."
        )
    return path


def load_annual(data_dir: Path | None = None) -> pd.DataFrame:
    """Read ``annual_indices`` unchanged (one row per city and year)."""
    annual = pd.read_parquet(_path("annual_indices", data_dir))
    assert_weather_cutoff(annual, name="annual_indices")
    return annual


def load_city_info(data_dir: Path | None = None) -> pd.DataFrame:
    """Read ``city_info`` (one row per station thread) with parsed thread dates."""
    cities = pd.read_parquet(_path("city_info", data_dir))
    for column in ("Stn.stDate", "Stn.edDate"):
        cities[column] = pd.to_datetime(cities[column])
    return cities


def load_coverage(data_dir: Path | None = None) -> pd.DataFrame:
    """Read ``coverage_and_stations`` unchanged (one row per city and year).

    ``Days Both`` counts days with both tmax and tmin observed, ``Station Segment``
    is the 1-based index of the station thread in use, and ``Station Changes`` is
    the number of station switches during that year.
    """
    coverage = pd.read_parquet(_path("coverage_and_stations", data_dir))
    assert_weather_cutoff(coverage, name="coverage_and_stations")
    return coverage


def load_daily(
    data_dir: Path | None = None,
    *,
    city_ids: Iterable[str] | None = None,
    columns: Sequence[str] = DAILY_VALUE_COLUMNS,
) -> pd.DataFrame:
    """Read the daily table compactly: categorical ``ID``, datetime ``Date``, float32 values.

    The full table is about 10M rows, so pass ``city_ids`` to read a subset and
    ``columns`` to drop value columns you do not need.  ``Name`` is not read;
    join it from :func:`city_table` when needed.
    """
    unknown = sorted(set(columns) - set(DAILY_VALUE_COLUMNS))
    if unknown:
        raise ValueError(f"unknown daily columns {unknown}; expected {list(DAILY_VALUE_COLUMNS)}")
    filters = None
    if city_ids is not None:
        ids = sorted({str(city_id) for city_id in city_ids})
        if not ids:
            raise ValueError("city_ids must contain at least one ID when given")
        filters = [("ID", "in", ids)]
    daily = pd.read_parquet(
        _path("daily", data_dir), columns=["ID", "Date", *columns], filters=filters
    )
    daily["ID"] = daily["ID"].astype("category")
    daily["Date"] = pd.to_datetime(daily["Date"])
    assert_weather_cutoff(daily, name="daily")
    for column in columns:
        daily[column] = daily[column].astype("float32")
    return daily


def assign_region(lat: pd.Series, lon: pd.Series) -> pd.Series:
    """Label each coordinate with one of :data:`REGIONS` (approximate, coordinate-based)."""
    west_edge, east_edge = REGION_LON_EDGES
    band = np.select([lon < west_edge, lon < east_edge], ["West", "Central"], default="East")
    north = np.asarray(lat >= REGION_LAT_EDGE)
    names = {
        ("West", True): "Northwest",
        ("West", False): "Southwest",
        ("Central", True): "North Central",
        ("Central", False): "South Central",
        ("East", True): "Northeast",
        ("East", False): "Southeast",
    }
    labels = [names[(b, n)] for b, n in zip(band, north, strict=True)]
    return pd.Series(
        pd.Categorical(labels, categories=list(REGIONS)), index=lat.index, name="region"
    )


def city_table(annual: pd.DataFrame, city_info: pd.DataFrame) -> pd.DataFrame:
    """One row per city: coordinates, region, record span and station-thread count."""
    years = annual.groupby("ID")["Year"].agg(first_year="min", last_year="max", n_years="count")
    threads = city_info.groupby("ID").size().rename("n_station_threads")
    cities = (
        annual.drop_duplicates("ID")[["ID", "Name", "Lat", "Lon"]]
        .set_index("ID")
        .join(years)
        .join(threads)
    )
    cities["n_station_threads"] = cities["n_station_threads"].fillna(0).astype(int)
    cities["region"] = assign_region(cities["Lat"], cities["Lon"])
    return cities.reset_index().sort_values("ID", ignore_index=True)
