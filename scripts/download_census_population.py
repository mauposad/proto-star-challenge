"""Download U.S. Census county population files (1970-2023) and map cities to counties.

Population does not respond to the weather, so no date cap applies (docs/honor_code.md).
Writes into ``data/external/census_county_population/`` once: files already there are
left untouched (external data is immutable). Prints what it fetched and the year range.
"""

import hashlib
import json
import time
from pathlib import Path

import requests

from proto_star.data.external.census import (
    CENSUS_DIR,
    GEOCODE_FILE,
    SOURCE_FILES,
    geocode_city,
    load_county_population,
)
from proto_star.data.protostar import load_city_info


def _get(url: str, params: dict[str, str], attempts: int = 4) -> str:
    """GET with a short backoff: the geocoder sometimes answers 5xx under load (CI runs)."""
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            if attempt == attempts:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def download_files(destination: Path) -> None:
    """Write every file in ``SOURCE_FILES`` that is not yet in ``destination``."""
    for name, url in SOURCE_FILES.items():
        path = destination / name
        if path.exists():
            print(f"kept     {name} (already present)")
            continue
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        if response.content.lstrip()[:15].lower().startswith(b"<!doctype html"):
            raise RuntimeError(f"{url} returned an HTML page, not a data file")
        path.write_bytes(response.content)
        print(f"fetched  {name} ({len(response.content):,} bytes) from {url}")


def geocode_cities(destination: Path) -> None:
    """Look up the county containing each city's station once; store the raw JSON."""
    path = destination / GEOCODE_FILE
    if path.exists():
        print(f"kept     {GEOCODE_FILE} (already present)")
        return
    cities = load_city_info().drop_duplicates("ID")
    responses = {}
    for row in cities.itertuples():
        responses[row.ID] = geocode_city(float(row.Lat), float(row.Lon), _get)
        time.sleep(0.2)
    path.write_text(json.dumps(responses, indent=1, sort_keys=True))
    print(f"fetched  {GEOCODE_FILE} ({len(responses)} cities)")


def main(destination: Path = CENSUS_DIR) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    download_files(destination)
    geocode_cities(destination)
    source = destination / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    *(f"source={url}" for url in SOURCE_FILES.values()),
                    "source=https://geocoding.geo.census.gov/geocoder (2010 county vintage)",
                    "license=public domain U.S. government work",
                    "use=static; population does not respond to the weather",
                    "downloaded_by=scripts/download_census_population.py",
                    "",
                ]
            )
        )
    population = load_county_population(destination)
    print(
        f"county population: {population['fips'].nunique():,} counties, "
        f"years {population['year'].min()}-{population['year'].max()}, {len(population):,} rows"
    )
    for path in sorted(destination.iterdir()):
        print(f"sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    main()
