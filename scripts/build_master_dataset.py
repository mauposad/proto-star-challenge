"""Build the team's shared annual master table from the raw ProtoStar tables.

Run `uv run python scripts/download_protostar_data.py` first, then compare the printed
content hash with the one in docs/data.md to confirm you have the team's exact table.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd

from proto_star.data.master import (
    MANIFEST_FILE,
    MASTER_DIR,
    MASTER_FILE,
    build_annual_master,
    content_hash,
    verify_master,
)
from proto_star.data.protostar import PROTOSTAR_DIR, load_annual, load_coverage, load_daily

SOURCES = ("annual_indices", "coverage_and_stations", "daily")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cells_blanked(raw: pd.DataFrame, master: pd.DataFrame) -> dict[str, int]:
    """Count, per raw column, how many values the cleaning step turned into NaN."""
    aligned = raw.sort_values(["ID", "Year"], ignore_index=True)
    numeric = aligned.select_dtypes("number").columns
    blanked = aligned[numeric].notna() & master[numeric].isna()
    counts = blanked.sum()
    return {str(column): int(count) for column, count in counts.items() if count}


def main(destination: Path = MASTER_DIR) -> None:
    """Write the master table and a manifest describing how it was built."""
    annual = load_annual()
    master = build_annual_master(annual, load_coverage(), load_daily())
    verify_master(master, annual)

    destination.mkdir(parents=True, exist_ok=True)
    master.to_parquet(destination / MASTER_FILE, index=False)
    manifest = {
        "rows": len(master),
        "cities": int(master["ID"].nunique()),
        "first_year": int(master["Year"].min()),
        "last_year": int(master["Year"].max()),
        "content_hash": content_hash(master),
        "cells_blanked": _cells_blanked(annual, master),
        "valid_rows": {
            column: int(master[column].sum())
            for column in master.columns
            if column.startswith("valid_")
        },
        "sources_sha256": {
            f"{name}.parquet": _sha256(PROTOSTAR_DIR / f"{name}.parquet") for name in SOURCES
        },
        "built_by": "scripts/build_master_dataset.py",
    }
    (destination / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
