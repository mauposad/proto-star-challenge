"""Join CMU challenge cities with static NOAA station metadata and write a report."""

from pathlib import Path

import pandas as pd

from proto_star.paths import EXTERNAL_DIR, INTERIM_DIR, RAW_DIR
from proto_star.station_metadata import build_station_metadata_report, load_ghcn_station_metadata


def main(
    city_path: Path = RAW_DIR / "protostar" / "city_info.parquet",
    station_path: Path = EXTERNAL_DIR / "noaa_ghcn_stations" / "ghcnd-stations.txt",
    output_path: Path = INTERIM_DIR / "protostar_station_metadata.parquet",
) -> None:
    """Write the reproducible CMU-to-NOAA station interoperability report."""
    report = build_station_metadata_report(
        pd.read_parquet(city_path),
        load_ghcn_station_metadata(station_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_parquet(output_path, index=False)
    print(
        f"Wrote {len(report)} city metadata rows; "
        f"{int(report['metadata_found'].sum())} matched NOAA station IDs to {output_path}"
    )


if __name__ == "__main__":
    main()
