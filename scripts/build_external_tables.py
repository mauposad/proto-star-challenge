"""Build the processed external tables from the files in ``data/external/``.

Writes ``data/processed/external/city_static.parquet`` (one row per city) and, when the
climate-index downloads exist, ``indices_to_2018.parquet`` (monthly, capped at 2018-12).
Run the ``scripts/download_*.py`` scripts first (see docs/data.md).
"""

import json
from pathlib import Path

import pandas as pd

from proto_star.data.external import CITY_STATIC_PATH, EXTERNAL_PROCESSED_DIR, INDICES_PATH
from proto_star.data.external.census import (
    CENSUS_DIR,
    GEOCODE_FILE,
    city_counties_from_geocoder,
    city_population_table,
    load_county_population,
)
from proto_star.data.external.city_static import build_city_static
from proto_star.data.external.geography import coast_and_lake_distances
from proto_star.data.protostar import load_city_info
from proto_star.paths import EXTERNAL_DIR
from proto_star.station_metadata import load_ghcn_station_metadata


def build_static() -> pd.DataFrame:
    cities = load_city_info().drop_duplicates("ID")
    stations = load_ghcn_station_metadata(
        EXTERNAL_DIR / "noaa_ghcn_stations" / "ghcnd-stations.txt"
    )
    counties = city_counties_from_geocoder(json.loads((CENSUS_DIR / GEOCODE_FILE).read_text()))
    population = city_population_table(counties, load_county_population())
    land_cover = None
    try:
        from proto_star.data.external.nlcd import load_city_land_cover

        land_cover = load_city_land_cover()
    except (ImportError, FileNotFoundError) as error:
        print(f"NLCD land cover skipped: {error}")
    return build_city_static(
        cities,
        stations=stations,
        distances=coast_and_lake_distances(cities),
        city_counties=counties,
        city_population=population,
        land_cover=land_cover,
    )


def build_indices() -> pd.DataFrame | None:
    try:
        from proto_star.data.external.indices import build_monthly_indices
    except ImportError as error:
        print(f"climate indices skipped: {error}")
        return None
    try:
        return build_monthly_indices()
    except FileNotFoundError as error:
        print(f"climate indices skipped: {error}")
        return None


def _write(table: pd.DataFrame, path: Path) -> None:
    """Write via a temporary file so a teammate reading the table never sees half a file."""
    temporary = path.with_suffix(".tmp.parquet")
    table.to_parquet(temporary, index=False)
    temporary.replace(path)


def main() -> None:
    EXTERNAL_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    static = build_static()
    _write(static, CITY_STATIC_PATH)
    print(f"wrote {CITY_STATIC_PATH} ({len(static)} rows, {static.shape[1]} columns)")
    indices = build_indices()
    if indices is not None:
        _write(indices, INDICES_PATH)
        print(
            f"wrote {INDICES_PATH} ({len(indices)} rows, "
            f"{indices['date'].min():%Y-%m} to {indices['date'].max():%Y-%m})"
        )


if __name__ == "__main__":
    main()
