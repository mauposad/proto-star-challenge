"""Distance from each city station to the ocean coast and to the Great Lakes.

Source: Natural Earth 1:10m coastline and lakes (public domain), as GeoJSON. Distances
are great-circle distances (km) to the nearest line vertex, which slightly overstates
the true distance where vertices are sparse (Natural Earth 10m vertices are typically
well under 1 km apart). Static: does not respond to the weather.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import ClimateDataError
from proto_star.paths import EXTERNAL_DIR

NATURAL_EARTH_DIR = EXTERNAL_DIR / "natural_earth"
NATURAL_EARTH_TAG = "v5.1.2"
NATURAL_EARTH_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"{NATURAL_EARTH_TAG}/geojson/{{name}}.geojson"
)
COASTLINE_FILE = "ne_10m_coastline.geojson"
LAKES_FILE = "ne_10m_lakes.geojson"
GREAT_LAKES = ("Lake Superior", "Lake Michigan", "Lake Huron", "Lake Erie", "Lake Ontario")
# The challenge cities lie in the 50 states; vertices outside this box cannot be nearest.
NORTH_AMERICA_BBOX = (-180.0, 10.0, -50.0, 75.0)  # lon_min, lat_min, lon_max, lat_max
EARTH_RADIUS_KM = 6371.0088


def _rings(geometry: dict) -> Iterable[list[list[float]]]:
    kind, coords = geometry["type"], geometry["coordinates"]
    if kind == "LineString":
        yield coords
    elif kind in ("MultiLineString", "Polygon"):
        yield from coords
    elif kind == "MultiPolygon":
        for polygon in coords:
            yield from polygon
    else:
        raise ClimateDataError(f"unsupported geometry type {kind!r}")


def line_vertices(
    geojson: dict,
    *,
    names: Iterable[str] | None = None,
    bbox: tuple[float, float, float, float] = NORTH_AMERICA_BBOX,
) -> np.ndarray:
    """Return an ``(n, 2)`` array of (lat, lon) vertices, optionally only named features."""
    wanted = set(names) if names is not None else None
    lon_min, lat_min, lon_max, lat_max = bbox
    chunks = []
    for feature in geojson["features"]:
        if wanted is not None and feature["properties"].get("name") not in wanted:
            continue
        for ring in _rings(feature["geometry"]):
            points = np.asarray(ring, dtype=float)[:, :2]
            keep = (
                (points[:, 0] >= lon_min)
                & (points[:, 0] <= lon_max)
                & (points[:, 1] >= lat_min)
                & (points[:, 1] <= lat_max)
            )
            if keep.any():
                chunks.append(points[keep][:, ::-1])
    if not chunks:
        raise ClimateDataError("no line vertices matched the requested features and box")
    return np.concatenate(chunks)


def nearest_distance_km(lat: pd.Series, lon: pd.Series, vertices: np.ndarray) -> pd.Series:
    """Great-circle distance (km) from each point to its nearest vertex."""
    v_lat, v_lon = np.radians(vertices[:, 0]), np.radians(vertices[:, 1])
    out = []
    for p_lat, p_lon in zip(np.radians(lat.to_numpy()), np.radians(lon.to_numpy()), strict=True):
        a = (
            np.sin((v_lat - p_lat) / 2) ** 2
            + np.cos(p_lat) * np.cos(v_lat) * np.sin((v_lon - p_lon) / 2) ** 2
        )
        out.append(2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a.min())))
    return pd.Series(out, index=lat.index, dtype=float)


def coast_and_lake_distances(
    cities: pd.DataFrame, directory: Path = NATURAL_EARTH_DIR
) -> pd.DataFrame:
    """``ID``, ``dist_coast_km`` (ocean coastline) and ``dist_great_lakes_km`` per city."""
    paths = [directory / COASTLINE_FILE, directory / LAKES_FILE]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"{missing} not found. Run `uv run python scripts/download_natural_earth.py`."
        )
    coast = line_vertices(json.loads(paths[0].read_text()))
    lakes = line_vertices(json.loads(paths[1].read_text()), names=GREAT_LAKES)
    return pd.DataFrame(
        {
            "ID": cities["ID"].to_numpy(),
            "dist_coast_km": nearest_distance_km(cities["Lat"], cities["Lon"], coast).to_numpy(),
            "dist_great_lakes_km": nearest_distance_km(
                cities["Lat"], cities["Lon"], lakes
            ).to_numpy(),
        }
    )
