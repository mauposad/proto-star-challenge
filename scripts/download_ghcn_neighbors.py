"""Download annual summaries (to 2018) for GHCN-Daily neighbors within 100 km of each city.

1. The static GHCN-Daily inventory (station, element, first/last year; no observations)
   is written once to ``data/external/ghcn_neighbors/ghcnd-inventory.txt``.
2. Up to five neighbors per city are chosen from it (see ``ghcn_neighbors``).
3. Their ``global-summary-of-the-year`` records come from the NCEI Access Data Service
   with ``endDate=2018-12-31`` (server-side cap). Each batch is checked with
   ``assert_weather_cutoff`` before it is written; batches already on disk are kept.
4. The batches are combined into ``data/interim/external/ghcn_neighbors_annual_to_2018``.
"""

import hashlib
import time
from pathlib import Path

import pandas as pd
import requests

from proto_star.data.external.ghcn_neighbors import (
    ADS_URL,
    INVENTORY_URL,
    NEIGHBOR_ANNUAL_PATH,
    NEIGHBORS_DIR,
    ads_params,
    candidate_stations,
    nearest_neighbors,
    parse_gsoy,
    parse_inventory,
)
from proto_star.data.protostar import load_city_info

BATCH_SIZE = 10


def _fetch_inventory(path: Path) -> str:
    if path.exists():
        print(f"kept     {path.name} (already present)")
        return path.read_text()
    response = requests.get(INVENTORY_URL, timeout=600)
    response.raise_for_status()
    parse_inventory(response.text)
    path.write_text(response.text)
    print(f"fetched  {path.name} ({len(response.content):,} bytes)")
    return response.text


def _fetch_batch(stations: list[str], path: Path) -> None:
    for attempt in range(3):
        try:
            response = requests.get(ADS_URL, params=ads_params(stations), timeout=300)
            response.raise_for_status()
            parse_gsoy(response.content, name=path.name)  # cap checked before writing
            break
        except (requests.RequestException, pd.errors.ParserError):
            if attempt == 2:
                raise
            time.sleep(10)
    path.write_bytes(response.content)


def main() -> None:
    gsoy_dir = NEIGHBORS_DIR / "gsoy"
    gsoy_dir.mkdir(parents=True, exist_ok=True)
    inventory = parse_inventory(_fetch_inventory(NEIGHBORS_DIR / "ghcnd-inventory.txt"))
    cities = load_city_info().drop_duplicates("ID")
    neighbors = nearest_neighbors(cities, candidate_stations(inventory))
    stations = sorted(neighbors["neighbor_id"].unique())
    print(
        f"neighbors: {len(neighbors)} links, {len(stations)} stations, "
        f"{neighbors['ID'].nunique()} of {len(cities)} cities have at least one"
    )
    frames = []
    for start in range(0, len(stations), BATCH_SIZE):
        batch = stations[start : start + BATCH_SIZE]
        path = gsoy_dir / f"gsoy_{batch[0]}_{batch[-1]}_{len(batch)}.csv"
        if not path.exists():
            _fetch_batch(batch, path)
            time.sleep(1)
        frames.append(parse_gsoy(path.read_bytes(), name=path.name))
    annual = pd.concat(frames, ignore_index=True)
    NEIGHBOR_ANNUAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    annual.to_parquet(NEIGHBOR_ANNUAL_PATH, index=False)
    neighbors.to_csv(NEIGHBOR_ANNUAL_PATH.with_name("ghcn_neighbors_list.csv"), index=False)
    print(
        f"wrote {NEIGHBOR_ANNUAL_PATH} ({len(annual):,} station-years, "
        f"{annual['station_id'].nunique()} stations, years {annual['year'].min()}-"
        f"{annual['year'].max()})"
    )
    source = NEIGHBORS_DIR / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    f"source={INVENTORY_URL} (static inventory)",
                    f"source={ADS_URL}?dataset=global-summary-of-the-year&endDate=2018-12-31",
                    "license=public domain U.S. government work",
                    "cap=server-side endDate=2018-12-31, checked before writing",
                    "downloaded_by=scripts/download_ghcn_neighbors.py",
                    "",
                ]
            )
        )
    digest = hashlib.sha256()
    for path in sorted(gsoy_dir.iterdir()):
        digest.update(path.name.encode() + path.read_bytes())
    inventory_hash = hashlib.sha256((NEIGHBORS_DIR / "ghcnd-inventory.txt").read_bytes())
    print(f"sha256 {inventory_hash.hexdigest()}  ghcnd-inventory.txt")
    print(f"sha256 of all GSOY batches (sorted by name): {digest.hexdigest()}")


if __name__ == "__main__":
    main()
