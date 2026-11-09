"""Build the population-only city table that the urban CRM reads, when a config needs it.

The urban covariate of the Coupled Regional Model reads
``data/processed/external/city_static.parquet`` (``ID`` plus ``pop_<census year>``). On a fresh
checkout, such as the GitHub Actions publish run, that file does not exist. This script:

1. checks whether the trial config's submitted forecaster (or ``--forecaster``) is an urban CRM,
   and does nothing otherwise;
2. downloads the Census county population files and city-to-county lookups
   (``scripts/download_census_population.py``; population does not respond to weather);
3. writes the population columns to ``city_static.parquet``, unless that file already exists
   (a full table from ``scripts/build_external_tables.py`` is kept as it is).

    uv run python scripts/build_city_population.py --config configs/mp_crm.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from proto_star.data.external.census import (
    CENSUS_DIR,
    GEOCODE_FILE,
    city_counties_from_geocoder,
    city_population_table,
    load_county_population,
)
from proto_star.forecasters._crm_urban import CENSUS_YEARS, CITY_STATIC_PATH
from proto_star.trial import TrialConfig, load_trial_config


def needs_city_population(cfg: TrialConfig, forecaster: str | None) -> bool:
    """True when the forecaster that will be packaged is a CRM with the urban covariate."""
    name = forecaster or cfg.submit
    entry = cfg.models.get(name) if name else None
    return entry is not None and entry.kind == "crm" and bool(entry.params.get("urban", False))


def build_city_population(out_path: Path = CITY_STATIC_PATH, census_dir: Path = CENSUS_DIR) -> Path:
    """Write ``ID`` and ``pop_<year>`` for every city from the downloaded Census files."""
    counties = city_counties_from_geocoder(json.loads((census_dir / GEOCODE_FILE).read_text()))
    table = city_population_table(counties, load_county_population(census_dir))
    columns = ["ID", *[f"pop_{year}" for year in CENSUS_YEARS]]
    missing = table[columns[1:]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"census population missing for cities {sorted(table.loc[missing, 'ID'])}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_path.with_suffix(".tmp.parquet")
    table[columns].to_parquet(temporary, index=False)
    temporary.replace(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--forecaster", default=None)
    args = parser.parse_args()
    if not needs_city_population(load_trial_config(args.config), args.forecaster or None):
        print("city population not needed for this forecaster; nothing to do")
        return
    if CITY_STATIC_PATH.exists():
        print(f"kept     {CITY_STATIC_PATH} (already present)")
        return
    from download_census_population import main as download_census  # same scripts/ folder

    download_census()
    path = build_city_population()
    print(f"wrote    {path}")


if __name__ == "__main__":
    main()
