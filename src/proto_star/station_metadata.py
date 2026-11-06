"""Static NOAA GHCN station metadata for climate challenge interoperability.

This inventory holds station descriptors, not weather observations. It may
support cross-repository reporting and policy analysis, but never forecasting
from post-2018 weather evidence.
"""

from pathlib import Path

import pandas as pd

from proto_star.climate import ClimateDataError

GHCN_STATION_COLUMNS = [
    "station_id",
    "latitude",
    "longitude",
    "elevation_m",
    "state",
    "station_name",
    "gsn_flag",
    "hcn_flag",
    "wmo_id",
]
_COLSPECS = [
    (0, 11),
    (12, 20),
    (21, 30),
    (31, 37),
    (38, 40),
    (41, 71),
    (72, 75),
    (76, 79),
    (80, 85),
]


def load_ghcn_station_metadata(path: Path) -> pd.DataFrame:
    """Parse NOAA's documented `ghcnd-stations.txt` fixed-width inventory."""
    stations = pd.read_fwf(
        path,
        colspecs=_COLSPECS,
        names=GHCN_STATION_COLUMNS,
        dtype={"station_id": str},
    )
    stations["station_id"] = stations["station_id"].str.strip()
    stations["station_name"] = stations["station_name"].str.strip()
    stations["state"] = stations["state"].fillna("").str.strip()
    stations = stations.dropna(subset=["station_id"])
    if stations["station_id"].duplicated().any():
        raise ClimateDataError("NOAA station metadata contains duplicate station IDs")
    return stations


def build_station_metadata_report(cities: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Join CMU city records to NOAA metadata and flag coordinate differences."""
    required_cities = {"ID", "Name", "Lat", "Lon"}
    missing_cities = sorted(required_cities - set(cities.columns))
    if missing_cities:
        raise ClimateDataError(f"city metadata is missing columns: {missing_cities}")
    required_stations = {"station_id", "latitude", "longitude", "elevation_m"}
    if not required_stations <= set(stations.columns):
        raise ClimateDataError("NOAA metadata is missing required station fields")

    city_rows = (
        cities[["ID", "Name", "Lat", "Lon"]]
        .drop_duplicates("ID")
        .rename(
            columns={
                "ID": "station_id",
                "Name": "challenge_city",
                "Lat": "cmu_latitude",
                "Lon": "cmu_longitude",
            }
        )
    )
    city_rows["station_id"] = city_rows["station_id"].astype(str)
    report = city_rows.merge(stations, on="station_id", how="left", validate="one_to_one")
    report["metadata_found"] = report["latitude"].notna()
    report["latitude_delta"] = report["latitude"] - report["cmu_latitude"]
    report["longitude_delta"] = report["longitude"] - report["cmu_longitude"]
    return report.sort_values("station_id", ignore_index=True)
