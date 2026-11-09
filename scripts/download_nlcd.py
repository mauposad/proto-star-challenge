"""Download ~20 km NLCD windows (impervious, tree canopy) around each city station.

Uses the MRLC GeoServer WCS so no national file (several GB) is fetched: one Deflate
GeoTIFF of about 670 x 670 30 m pixels per city and layer, about 300 KB each. Land
cover does not respond to the weather. Windows already on disk are left untouched.
"""

import hashlib
import time
from pathlib import Path

import requests

from proto_star.data.external.nlcd import (
    LAYERS,
    NLCD_DIR,
    WCS_URL,
    albers_conus,
    read_geotiff,
    tile_path,
    wcs_params,
    wcs_query,
)
from proto_star.data.protostar import load_city_info


def main(directory: Path = NLCD_DIR) -> None:
    cities = load_city_info().drop_duplicates("ID")
    fetched = kept = 0
    total_bytes = 0
    for layer, coverage in LAYERS.items():
        (directory / layer).mkdir(parents=True, exist_ok=True)
        for city in cities.itertuples():
            path = tile_path(directory, layer, str(city.ID))
            if path.exists():
                kept += 1
                continue
            x, y = albers_conus(float(city.Lat), float(city.Lon))
            url = f"{WCS_URL}?{wcs_query(wcs_params(coverage, x, y))}"
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=180)
                    response.raise_for_status()
                    read_geotiff(response.content)  # reject error pages before writing
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(5)
            path.write_bytes(response.content)
            fetched += 1
            total_bytes += len(response.content)
        print(f"{layer}: done ({coverage})")
    source = directory / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    f"source={WCS_URL} (MRLC GeoServer WCS 2.0.1)",
                    *(f"coverage={layer}:{coverage}" for layer, coverage in LAYERS.items()),
                    "window=station +/- 10.05 km in EPSG:5070, Deflate GeoTIFF, one per city",
                    "license=public domain U.S. government work (USGS / USFS)",
                    "use=static land cover; does not respond to the weather",
                    "downloaded_by=scripts/download_nlcd.py",
                    "",
                ]
            )
        )
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*.tif")):
        digest.update(path.name.encode() + path.parent.name.encode() + path.read_bytes())
    print(f"fetched {fetched} windows ({total_bytes:,} bytes), kept {kept}")
    print(f"sha256 of all windows (sorted by path): {digest.hexdigest()}")


if __name__ == "__main__":
    main()
