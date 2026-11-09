"""NLCD impervious surface and tree canopy around each city station (1, 5, 10 km).

Source: MRLC GeoServer WCS 2.0.1 (USGS NLCD impervious, USFS NLCD tree canopy cover),
30 m CONUS grids in EPSG:5070 (NAD83 / CONUS Albers). Instead of the national files
(several GB each) the download asks for a ~20 km square around each station. Land
cover does not respond to the weather; only pre-2019 editions are used anyway.

Buffer values are the mean percent over valid 30 m pixels whose centres lie within the
radius (values above 100 are no-data flags and are skipped; open water counts as 0).
"""

from __future__ import annotations

import io
import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import ClimateDataError
from proto_star.paths import EXTERNAL_DIR

NLCD_DIR = EXTERNAL_DIR / "nlcd"
WCS_URL = "https://www.mrlc.gov/geoserver/ows"
# short name: WCS coverage id
LAYERS = {
    "imperv_2001": "mrlc_download__NLCD_2001_Impervious_L48",
    "imperv_2011": "mrlc_download__NLCD_2011_Impervious_L48",
    "imperv_2016": "mrlc_download__NLCD_2016_Impervious_L48",
    "canopy_2011": "mrlc_download__nlcd_tcc_conus_2011_v2021-4",
}
RADII_M = (1000, 5000, 10000)
HALF_WIDTH_M = 10_050  # request window half-width; covers the 10 km buffer

# EPSG:5070 parameters (GRS80 ellipsoid).
_A = 6378137.0
_F = 1 / 298.257222101
_LAT1, _LAT2, _LAT0, _LON0 = 29.5, 45.5, 23.0, -96.0


def _albers_terms() -> tuple[float, float, float, float]:
    e2 = 2 * _F - _F**2
    e = math.sqrt(e2)

    def q(phi: float) -> float:
        s = math.sin(phi)
        return (1 - e2) * (s / (1 - e2 * s * s) - math.log((1 - e * s) / (1 + e * s)) / (2 * e))

    def m(phi: float) -> float:
        s = math.sin(phi)
        return math.cos(phi) / math.sqrt(1 - e2 * s * s)

    phi1, phi2, phi0 = (math.radians(v) for v in (_LAT1, _LAT2, _LAT0))
    n = (m(phi1) ** 2 - m(phi2) ** 2) / (q(phi2) - q(phi1))
    c = m(phi1) ** 2 + n * q(phi1)
    rho0 = _A * math.sqrt(c - n * q(phi0)) / n
    return e, n, c, rho0


def albers_conus(lat: float, lon: float) -> tuple[float, float]:
    """Project NAD83 latitude/longitude (degrees) to EPSG:5070 metres (Snyder 1987)."""
    e, n, c, rho0 = _albers_terms()
    phi = math.radians(lat)
    s = math.sin(phi)
    q = (1 - e * e) * (s / (1 - e * e * s * s) - math.log((1 - e * s) / (1 + e * s)) / (2 * e))
    rho = _A * math.sqrt(c - n * q) / n
    theta = n * math.radians(lon - _LON0)
    return rho * math.sin(theta), rho0 - rho * math.cos(theta)


def wcs_params(coverage: str, x: float, y: float) -> dict[str, str]:
    """GetCoverage parameters for a Deflate GeoTIFF window centred on (x, y)."""
    return {
        "service": "WCS",
        "version": "2.0.1",
        "request": "GetCoverage",
        "coverageId": coverage,
        "subset": f"X({x - HALF_WIDTH_M:.0f},{x + HALF_WIDTH_M:.0f})",
        "subset_y": f"Y({y - HALF_WIDTH_M:.0f},{y + HALF_WIDTH_M:.0f})",
        "format": "image/geotiff",
        "geotiff:compression": "Deflate",
    }


def wcs_query(params: dict[str, str]) -> str:
    """Query string; WCS needs two ``subset`` keys, which a dict cannot hold."""
    parts = [f"{('subset' if k == 'subset_y' else k)}={v}" for k, v in params.items()]
    return "&".join(parts)


def read_geotiff(content: bytes) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Return pixel values and ``(left, top, dx, dy)`` from a north-up GeoTIFF."""
    from PIL import Image, TiffImagePlugin

    with Image.open(io.BytesIO(content)) as image:
        if not isinstance(image, TiffImagePlugin.TiffImageFile):
            raise ClimateDataError("expected a GeoTIFF")
        values = np.array(image)
        tags = image.tag_v2
        if 34264 in tags:  # ModelTransformationTag
            t = tags[34264]
            transform = (float(t[3]), float(t[7]), float(t[0]), float(t[5]))
        elif 33922 in tags and 33550 in tags:  # ModelTiepoint + ModelPixelScale
            tie, scale = tags[33922], tags[33550]
            transform = (float(tie[3]), float(tie[4]), float(scale[0]), -float(scale[1]))
        else:
            raise ClimateDataError("GeoTIFF has no georeferencing tags")
    if values.ndim != 2:
        raise ClimateDataError(f"expected a single-band GeoTIFF, got shape {values.shape}")
    return values, transform


def buffer_means(
    values: np.ndarray,
    transform: tuple[float, float, float, float],
    x: float,
    y: float,
    radii: Iterable[int] = RADII_M,
) -> dict[int, float]:
    """Mean of valid (0-100) pixels whose centres lie within each radius of (x, y)."""
    left, top, dx, dy = transform
    rows, cols = values.shape
    xs = left + dx * (np.arange(cols) + 0.5)
    ys = top + dy * (np.arange(rows) + 0.5)
    distance = np.hypot(xs[None, :] - x, ys[:, None] - y)
    valid = values <= 100
    out = {}
    for radius in radii:
        inside = (distance <= radius) & valid
        out[radius] = float(values[inside].mean()) if inside.any() else np.nan
    return out


def tile_path(directory: Path, layer: str, city_id: str) -> Path:
    return directory / layer / f"{city_id}.tif"


def load_city_land_cover(
    cities: pd.DataFrame | None = None, directory: Path = NLCD_DIR
) -> pd.DataFrame:
    """``ID`` plus ``<layer>_<r>km`` percent columns from the downloaded windows."""
    if cities is None:
        from proto_star.data.protostar import load_city_info

        cities = load_city_info()
    cities = cities.drop_duplicates("ID")
    rows = []
    for city_id, lat, lon in zip(cities["ID"], cities["Lat"], cities["Lon"], strict=True):
        x, y = albers_conus(float(lat), float(lon))
        row: dict[str, object] = {"ID": city_id}
        for layer in LAYERS:
            path = tile_path(directory, layer, str(city_id))
            if not path.exists():
                raise FileNotFoundError(
                    f"{path} not found. Run `uv run python scripts/download_nlcd.py`."
                )
            values, transform = read_geotiff(path.read_bytes())
            for radius, mean in buffer_means(values, transform, x, y).items():
                row[f"{layer}_{radius // 1000}km"] = mean
        rows.append(row)
    return pd.DataFrame(rows)
