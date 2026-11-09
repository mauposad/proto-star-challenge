"""Download Natural Earth 1:10m coastline and lakes (GeoJSON) for distance-to-coast.

Static geography; it does not respond to the weather. Pinned to a release tag of the
Natural Earth vector repository so the files are reproducible. Files already present in
``data/external/natural_earth/`` are left untouched.
"""

import hashlib
import json
from pathlib import Path

import requests

from proto_star.data.external.geography import (
    COASTLINE_FILE,
    LAKES_FILE,
    NATURAL_EARTH_DIR,
    NATURAL_EARTH_TAG,
    NATURAL_EARTH_URL,
)


def main(destination: Path = NATURAL_EARTH_DIR) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    urls = []
    for name in (COASTLINE_FILE, LAKES_FILE):
        path = destination / name
        url = NATURAL_EARTH_URL.format(name=name.removesuffix(".geojson"))
        urls.append(url)
        if path.exists():
            print(f"kept     {name} (already present)")
            continue
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        features = len(json.loads(response.content)["features"])
        path.write_bytes(response.content)
        print(f"fetched  {name} ({len(response.content):,} bytes, {features} features)")
    source = destination / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    *(f"source={url}" for url in urls),
                    f"release={NATURAL_EARTH_TAG}",
                    "license=public domain (Natural Earth terms of use)",
                    "use=static geography; distance to coast and Great Lakes",
                    "downloaded_by=scripts/download_natural_earth.py",
                    "",
                ]
            )
        )
    for path in sorted(destination.iterdir()):
        print(f"sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    main()
