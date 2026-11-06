"""Download static NOAA GHCN station metadata for reproducible integration."""

from pathlib import Path
from urllib.request import urlretrieve

from proto_star.paths import EXTERNAL_DIR
from proto_star.station_metadata import load_ghcn_station_metadata

URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"


def main(destination: Path = EXTERNAL_DIR / "noaa_ghcn_stations") -> None:
    """Write NOAA's static inventory and provenance receipt without overwriting data."""
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"{destination} already contains external data; refusing to overwrite it"
        )
    destination.mkdir(parents=True, exist_ok=False)
    station_path = destination / "ghcnd-stations.txt"
    try:
        urlretrieve(URL, station_path)
        load_ghcn_station_metadata(station_path)
    except Exception:
        station_path.unlink(missing_ok=True)
        destination.rmdir()
        raise
    (destination / "SOURCE.txt").write_text(
        "\n".join(
            [
                f"source={URL}",
                "artifact=GHCN-Daily station inventory",
                "use=static station metadata only; never weather observations",
                "license=public domain U.S. government work",
                "downloaded_by=scripts/download_ghcn_station_metadata.py",
                "",
            ]
        )
    )
    print(f"Wrote NOAA GHCN station metadata to {destination}")


if __name__ == "__main__":
    main()
