"""Annual summaries of GHCN-Daily neighbor stations within 100 km of each city, to 2018.

These are weather observations, so the download is a server-side, date-limited query
(NCEI Access Data Service, ``global-summary-of-the-year``, ``endDate=2018-12-31``), each
response is checked with ``assert_weather_cutoff`` before it is written, and
:func:`load_neighbor_annual` checks again with the fold cut-off on every read.

Neighbors are chosen from the static GHCN-Daily inventory (station, element, first and
last year): U.S. stations within 100 km that report TMAX and TMIN from 1970 or earlier
through 2000 or later, nearest first, at most five per city. The inventory's last-year
field is metadata, not an observation. NCEI computes the annual values with its own
completeness rules, which differ from the challenge's missing-days rule.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import FORECAST_CUTOFF, ClimateDataError, assert_weather_cutoff
from proto_star.paths import EXTERNAL_DIR, INTERIM_DIR

NEIGHBORS_DIR = EXTERNAL_DIR / "ghcn_neighbors"
INVENTORY_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"
ADS_URL = "https://www.ncei.noaa.gov/access/services/data/v1"
DATA_TYPES = ("TAVG", "TMAX", "TMIN", "PRCP", "EMXT", "CLDD")
NEIGHBOR_ANNUAL_PATH = INTERIM_DIR / "external" / "ghcn_neighbors_annual_to_2018.parquet"
MAX_DISTANCE_KM = 100.0
MAX_NEIGHBORS = 5
FIRST_YEAR_BY = 1970
LAST_YEAR_FROM = 2000
EARTH_RADIUS_KM = 6371.0088


def parse_inventory(text: str) -> pd.DataFrame:
    """Parse ``ghcnd-inventory.txt`` (fixed width: ID, lat, lon, element, first, last)."""
    table = pd.read_fwf(
        io.StringIO(text),
        colspecs=[(0, 11), (12, 20), (21, 30), (31, 35), (36, 40), (41, 45)],
        names=["station_id", "lat", "lon", "element", "first_year", "last_year"],
        dtype={"station_id": str, "element": str},
    )
    if table.empty:
        raise ClimateDataError("GHCN inventory is empty")
    return table


def candidate_stations(inventory: pd.DataFrame) -> pd.DataFrame:
    """U.S. stations with TMAX and TMIN from ``FIRST_YEAR_BY`` through ``LAST_YEAR_FROM``."""
    temps = inventory[
        inventory["station_id"].str.startswith("US") & inventory["element"].isin(["TMAX", "TMIN"])
    ]
    spans = temps.groupby("station_id").agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        n_elements=("element", "nunique"),
        first_year=("first_year", "max"),
        last_year=("last_year", "min"),
    )
    keep = (
        (spans["n_elements"] == 2)
        & (spans["first_year"] <= FIRST_YEAR_BY)
        & (spans["last_year"] >= LAST_YEAR_FROM)
    )
    return spans[keep].drop(columns="n_elements").reset_index()


def nearest_neighbors(
    cities: pd.DataFrame,
    candidates: pd.DataFrame,
    *,
    max_km: float = MAX_DISTANCE_KM,
    k: int = MAX_NEIGHBORS,
) -> pd.DataFrame:
    """Up to ``k`` candidates within ``max_km`` of each city, excluding its own station."""
    c_lat = np.radians(candidates["lat"].to_numpy())
    c_lon = np.radians(candidates["lon"].to_numpy())
    rows = []
    for city_id, lat, lon in zip(cities["ID"], cities["Lat"], cities["Lon"], strict=True):
        p_lat, p_lon = np.radians(lat), np.radians(lon)
        a = (
            np.sin((c_lat - p_lat) / 2) ** 2
            + np.cos(p_lat) * np.cos(c_lat) * np.sin((c_lon - p_lon) / 2) ** 2
        )
        distance = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
        order = np.argsort(distance)
        rank = 0
        for i in order:
            if distance[i] > max_km or rank >= k:
                break
            if candidates["station_id"].iloc[i] == city_id:
                continue
            rank += 1
            rows.append(
                {
                    "ID": city_id,
                    "neighbor_id": candidates["station_id"].iloc[i],
                    "rank": rank,
                    "distance_km": float(distance[i]),
                    "first_year": int(candidates["first_year"].iloc[i]),
                    "last_year_inventory": int(candidates["last_year"].iloc[i]),
                }
            )
    return pd.DataFrame(rows)


def ads_params(stations: list[str]) -> dict[str, str]:
    """NCEI Access Data Service query for annual summaries, ending 2018-12-31."""
    return {
        "dataset": "global-summary-of-the-year",
        "stations": ",".join(stations),
        "dataTypes": ",".join(DATA_TYPES),
        "startDate": "1800-01-01",
        "endDate": f"{FORECAST_CUTOFF}-12-31",
        "units": "standard",
        "format": "csv",
    }


def parse_gsoy(content: bytes, *, name: str) -> pd.DataFrame:
    """Parse one Access Data Service CSV to ``station_id, year, <types>`` (checked)."""
    table = pd.read_csv(io.BytesIO(content), dtype={"STATION": str})
    if "STATION" not in table.columns or "DATE" not in table.columns:
        raise ClimateDataError(f"{name}: not an annual-summary CSV (columns {list(table)[:5]})")
    table = table.rename(columns={"STATION": "station_id", "DATE": "year"})
    table["year"] = pd.to_numeric(table["year"], errors="raise").astype(int)
    assert_weather_cutoff(table, name=name)
    for column in DATA_TYPES:
        if column not in table.columns:
            table[column] = np.nan
    columns = ["station_id", "year", *DATA_TYPES]
    return table[columns].rename(columns=str.lower)


def load_neighbor_annual(
    cutoff_year: int = FORECAST_CUTOFF, path: Path = NEIGHBOR_ANNUAL_PATH
) -> pd.DataFrame:
    """Neighbor annual summaries up to ``cutoff_year`` (use the fold cut-off)."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python scripts/download_ghcn_neighbors.py`."
        )
    table = pd.read_parquet(path)
    assert_weather_cutoff(table, name=path.name)
    table = table[table["year"] <= cutoff_year].reset_index(drop=True)
    assert_weather_cutoff(table, name=path.name, cutoff_year=cutoff_year)
    return table
