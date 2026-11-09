"""One row per challenge city of static, non-weather covariates.

Joins the CMU ``city_info`` coordinates to GHCN station metadata (elevation, state),
Natural Earth distances (coast, Great Lakes), Census county population by decade and,
where available, NLCD land cover around the station. Nothing here responds to the
weather, so no date cap applies. For backtests, use only population up to each fold's
cut-off: ``log_pop_growth_1970_1980`` for the 1980 fold, ``_1980_1990`` for 1995 and
``_2000_2010`` for 2011 and the final forecast
(``proto_star.data.external.census.population_growth_to_cutoff`` picks it).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import ClimateDataError
from proto_star.data.external import CITY_STATIC_PATH
from proto_star.data.protostar import assign_region


def build_city_static(
    cities: pd.DataFrame,
    *,
    stations: pd.DataFrame,
    distances: pd.DataFrame,
    city_counties: pd.DataFrame,
    city_population: pd.DataFrame,
    land_cover: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Combine the per-city pieces; every piece must cover every city ``ID`` once.

    ``cities`` needs ``ID``, ``Name``, ``Lat``, ``Lon`` (one row per ID or per station
    thread); ``stations`` is the parsed GHCN inventory.
    """
    base = cities.drop_duplicates("ID")[["ID", "Name", "Lat", "Lon"]].reset_index(drop=True)
    ghcn = stations[["station_id", "elevation_m", "state"]].rename(columns={"station_id": "ID"})
    table = base.merge(ghcn, on="ID", how="left", validate="one_to_one")
    table["region"] = assign_region(table["Lat"], table["Lon"]).astype(str)
    pieces = [distances, city_counties, city_population]
    if land_cover is not None:
        pieces.append(land_cover)
    for piece in pieces:
        if piece["ID"].duplicated().any():
            raise ClimateDataError("a city_static piece has duplicate city IDs")
        missing = set(base["ID"]) - set(piece["ID"])
        if missing:
            raise ClimateDataError(f"a city_static piece lacks {len(missing)} cities")
        table = table.merge(piece, on="ID", how="left", validate="one_to_one")
    if "county_land_km2" in table and "pop_2010" in table:
        table["pop_density_2010_per_km2"] = table["pop_2010"] / table["county_land_km2"]
    for start in range(1970, 2020, 10):
        first, last = f"pop_{start}", f"pop_{start + 10}"
        if first in table and last in table:
            ratio = (table[last] / table[first]).to_numpy(dtype=float)
            table[f"log_pop_growth_{start}_{start + 10}"] = np.log(ratio)
    return table.sort_values("ID", ignore_index=True)


def load_city_static(path: Path = CITY_STATIC_PATH) -> pd.DataFrame:
    """Read ``city_static.parquet`` (build it with ``scripts/build_external_tables.py``)."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the download scripts, then "
            "`uv run python scripts/build_external_tables.py` (see docs/data.md)."
        )
    return pd.read_parquet(path)
