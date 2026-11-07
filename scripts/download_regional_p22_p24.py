"""Download static city attributes for the regional pooling-group trial (papers P22, P24).

Writes ``data/external/regional_p22_p24/`` (about 13 MB, all static, none of it weather):

* ``ghcnd-stations.txt``: NOAA GHCN-Daily station inventory, for station elevation.
* ``Gaz_places_national.zip``: U.S. Census Bureau 2010 Gazetteer of places (2010 Census
  population ``POP10``, released 2012).
* ``nlcd2016_points.csv``: NLCD 2016 land cover class at 5 points around each station
  (centre and +-0.005 degrees N/S/E/W), read one pixel at a time from the MRLC WMS
  ``GetFeatureInfo`` service.  The full NLCD raster is several GB, so we only sample points.
* ``city_groups.csv``: one row per challenge city, the table the forecasters read.
* ``SOURCE.txt``: URLs, licenses and SHA-256 checksums.

Every attribute is a fixed property of the city (elevation) or a pre-2019 vintage (2010
Census, NLCD 2016), so assigning cities to groups uses nothing from 2019 or later.  The
challenge cities come from the master table (only ``ID``, ``Name``, ``Lat``, ``Lon``).

Run: ``uv run python scripts/download_regional_p22_p24.py`` (refuses to overwrite).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, urlretrieve

import numpy as np
import pandas as pd

from proto_star.data.master import load_master
from proto_star.paths import EXTERNAL_DIR
from proto_star.station_metadata import load_ghcn_station_metadata

GHCN_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
GAZ_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_places_national.zip"
NLCD_WMS = "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms"
NLCD_LAYER = "NLCD_2016_Land_Cover_L48"
NLCD_OFFSET_DEG = 0.005  # about 500 m
PLACE_RADIUS_KM = 20.0  # largest Census place within this distance of the station
DESTINATION = EXTERNAL_DIR / "regional_p22_p24"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Great-circle distance from one point to many, in km."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dlat = p2 - p1
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return np.asarray(6371.0 * 2 * np.arcsin(np.sqrt(a)), dtype=float)


def load_places(zip_path: Path) -> pd.DataFrame:
    """2010 Census Gazetteer places: name, state, POP10, internal point."""
    with zipfile.ZipFile(zip_path) as archive:
        raw = archive.read("Gaz_places_national.txt").decode("latin-1")
    places = pd.read_csv(io.StringIO(raw), sep="\t", dtype={"GEOID": str})
    places.columns = [c.strip() for c in places.columns]
    return places[["USPS", "GEOID", "NAME", "POP10", "INTPTLAT", "INTPTLONG"]]


def largest_place(lat: float, lon: float, places: pd.DataFrame) -> tuple[str, int, float]:
    """Name, 2010 population and distance (km) of the most populous place nearby."""
    distance = haversine_km(lat, lon, places["INTPTLAT"].to_numpy(), places["INTPTLONG"].to_numpy())
    near = places.loc[distance <= PLACE_RADIUS_KM].assign(
        distance_km=distance[distance <= PLACE_RADIUS_KM]
    )
    if near.empty:  # no place within the radius: take the nearest one
        nearest = int(np.argmin(distance))
        row = places.iloc[nearest]
        return f"{row['NAME']}, {row['USPS']}", int(row["POP10"]), float(distance[nearest])
    row = near.sort_values(["POP10", "distance_km"], ascending=[False, True]).iloc[0]
    return f"{row['NAME']}, {row['USPS']}", int(row["POP10"]), float(row["distance_km"])


def nlcd_class(lat: float, lon: float) -> int:
    """NLCD 2016 class code of the pixel at (lat, lon); 0 if the service returns none."""
    half = 0.0005
    query = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": NLCD_LAYER,
        "QUERY_LAYERS": NLCD_LAYER,
        "SRS": "EPSG:4326",
        "BBOX": f"{lon - half},{lat - half},{lon + half},{lat + half}",
        "WIDTH": 3,
        "HEIGHT": 3,
        "X": 1,
        "Y": 1,
        "INFO_FORMAT": "application/json",
    }
    for attempt in range(4):
        try:
            with urlopen(f"{NLCD_WMS}?{urlencode(query)}", timeout=60) as response:
                payload = json.load(response)
            features = payload.get("features", [])
            return int(features[0]["properties"]["PALETTE_INDEX"]) if features else 0
        except (OSError, ValueError, KeyError):
            if attempt == 3:
                raise
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def sample_nlcd(cities: pd.DataFrame) -> pd.DataFrame:
    offsets = {
        "c": (0.0, 0.0),
        "n": (NLCD_OFFSET_DEG, 0.0),
        "s": (-NLCD_OFFSET_DEG, 0.0),
        "e": (0.0, NLCD_OFFSET_DEG),
        "w": (0.0, -NLCD_OFFSET_DEG),
    }
    rows = []
    for city in cities.itertuples():
        row: dict[str, object] = {"city_id": city.city_id}
        for key, (dlat, dlon) in offsets.items():
            row[f"nlcd_{key}"] = nlcd_class(float(city.lat) + dlat, float(city.lon) + dlon)
            time.sleep(0.1)  # be polite to the public server
        rows.append(row)
    return pd.DataFrame(rows)


def land_cover_group(codes: list[int]) -> str:
    """Majority of 5 sampled pixels: developed_high (23, 24), developed_low (21, 22) or other."""
    labels = [
        "developed_high" if c in (23, 24) else "developed_low" if c in (21, 22) else "undeveloped"
        for c in codes
        if c != 0
    ]
    if not labels:
        return "unknown"
    counts = pd.Series(labels).value_counts()
    best = counts[counts == counts.max()].index
    # Ties go to the more developed class (stations sit on the developed edge of a mix).
    for label in ("developed_high", "developed_low", "undeveloped"):
        if label in best:
            return label
    return "unknown"


def main(destination: Path = DESTINATION) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"{destination} already holds data; refusing to overwrite it")
    destination.mkdir(parents=True, exist_ok=True)

    master = load_master()
    cities = (
        master.assign(city_id=master["ID"].astype(str))
        .groupby("city_id", as_index=False)
        .agg(name=("Name", "first"), lat=("Lat", "first"), lon=("Lon", "first"))
    )

    ghcn_path = destination / "ghcnd-stations.txt"
    urlretrieve(GHCN_URL, ghcn_path)
    stations = load_ghcn_station_metadata(ghcn_path)[["station_id", "elevation_m", "state"]]
    gaz_path = destination / "Gaz_places_national.zip"
    urlretrieve(GAZ_URL, gaz_path)
    places = load_places(gaz_path)

    print(f"Sampling NLCD 2016 at {len(cities) * 5} points (a few minutes)...")
    nlcd = sample_nlcd(cities)
    nlcd_path = destination / "nlcd2016_points.csv"
    nlcd.to_csv(nlcd_path, index=False)

    table = cities.merge(stations, left_on="city_id", right_on="station_id", how="left")
    missing = table.loc[table["elevation_m"].isna(), "city_id"].tolist()
    if missing:
        raise ValueError(f"no GHCN elevation for cities {missing}")
    found = [largest_place(r.lat, r.lon, places) for r in table.itertuples()]
    table["place_2010"] = [f[0] for f in found]
    table["pop_2010"] = [f[1] for f in found]
    table["place_distance_km"] = np.round([f[2] for f in found], 2)
    table = table.merge(nlcd, on="city_id", how="left")
    codes = table[[f"nlcd_{k}" for k in "cnsew"]].to_numpy().tolist()
    table["land_cover"] = [land_cover_group([int(c) for c in row]) for row in codes]
    columns = [
        "city_id",
        "name",
        "state",
        "lat",
        "lon",
        "elevation_m",
        "place_2010",
        "pop_2010",
        "place_distance_km",
        *[f"nlcd_{k}" for k in "cnsew"],
        "land_cover",
    ]
    groups_path = destination / "city_groups.csv"
    table[columns].sort_values("city_id").to_csv(groups_path, index=False)

    lines = [
        f"ghcnd-stations.txt source={GHCN_URL} license=public domain (U.S. government work)",
        f"Gaz_places_national.zip source={GAZ_URL} vintage=2010 Census license=public domain",
        f"nlcd2016_points.csv source={NLCD_WMS} layer={NLCD_LAYER}",
        "nlcd2016_points.csv license=public domain (USGS MRLC)",
        "city_groups.csv derived by scripts/download_regional_p22_p24.py",
        "use=static city attributes for pooling groups only; never weather observations",
        "",
    ]
    for path in (ghcn_path, gaz_path, nlcd_path, groups_path):
        lines.append(f"sha256 {path.name} {sha256(path)}")
    (destination / "SOURCE.txt").write_text("\n".join(lines) + "\n")
    print(f"Wrote {groups_path} ({len(table)} cities)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()
    main()
