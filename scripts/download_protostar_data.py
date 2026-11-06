"""Download the official ProtoStar challenge tables, enforcing the 2018 cutoff.

Tables already present in the destination are left untouched (raw data is
immutable); only missing tables are downloaded and written.  Every table is
checked against the forecast cutoff before anything is written.
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from proto_star.climate import FORECAST_CUTOFF, ClimateDataError, annual_to_long
from proto_star.paths import RAW_DIR

REPO = "CMU-OSPO/protostar-climate-train-to-2018"
TABLES = ("annual_indices", "city_info", "daily", "coverage_and_stations")


def _load_hub_table(name: str) -> pd.DataFrame:
    return load_dataset(REPO, name, split="train").to_pandas()


def check_cutoff(name: str, table: pd.DataFrame, *, cutoff_year: int = FORECAST_CUTOFF) -> None:
    """Reject a table containing observations after the forecast cutoff."""
    if name == "annual_indices":
        annual_to_long(table, cutoff_year=cutoff_year)
        return
    if "Year" in table.columns:
        last = int(pd.to_numeric(table["Year"]).max())
    elif "Date" in table.columns:
        last = int(pd.to_datetime(table["Date"]).max().year)
    else:
        return  # static metadata (city_info) has no observation dates
    if last > cutoff_year:
        raise ClimateDataError(f"{name} contains year {last}, after allowed cutoff {cutoff_year}")


def download_missing(
    destination: Path,
    load: Callable[[str], pd.DataFrame] = _load_hub_table,
    tables: tuple[str, ...] = TABLES,
) -> list[str]:
    """Write each table in ``tables`` that is not yet in ``destination``; return those written."""
    missing = [name for name in tables if not (destination / f"{name}.parquet").exists()]
    loaded = {name: load(name) for name in missing}
    for name, table in loaded.items():
        check_cutoff(name, table)

    destination.mkdir(parents=True, exist_ok=True)
    for name, table in loaded.items():
        table.to_parquet(destination / f"{name}.parquet", index=False)
    source = destination / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    f"source={REPO}",
                    f"configs={','.join(tables)}",
                    "license=CC0-1.0",
                    f"enforced_weather_cutoff={FORECAST_CUTOFF}-12-31",
                    "downloaded_by=scripts/download_protostar_data.py",
                    "",
                ]
            )
        )
    return missing


def main(destination: Path = RAW_DIR / "protostar") -> None:
    """Download any official ProtoStar tables missing from the local raw-data store."""
    written = download_missing(destination)
    if written:
        print(f"Wrote {', '.join(written)} to {destination}")
    else:
        print(f"All ProtoStar tables already present in {destination}; nothing written")


if __name__ == "__main__":
    main()
