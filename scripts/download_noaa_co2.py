"""Download NOAA Mauna Loa annual mean CO2 and keep only years up to the team cut-off (2018).

CO2 is a forcing, not a weather observation, but it is a time series that runs past 2018,
so it is capped exactly like a weather input and checked with ``assert_weather_cutoff``.
Forecasters extrapolate it past each fold's cut-off with a fixed rule from the trial config
(see ``proto_star.forecasters.cdd_forcing_p06_p21``); observed post-2018 values are never kept.

    uv run python scripts/download_noaa_co2.py
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from proto_star.climate import FORECAST_CUTOFF, assert_weather_cutoff
from proto_star.paths import EXTERNAL_DIR

URL = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv"
FILE_NAME = "co2_annmean_mlo_to_2018.csv"
DESTINATION = EXTERNAL_DIR / "noaa_co2"


def parse_co2_annual(text: str, *, cutoff_year: int = FORECAST_CUTOFF) -> pd.DataFrame:
    """Parse NOAA's annual-mean CSV (``#`` comments) into ``year, co2_ppm`` up to the cut-off."""
    table = pd.read_csv(io.StringIO(text), comment="#", skipinitialspace=True)
    table.columns = [str(column).strip().lower() for column in table.columns]
    if not {"year", "mean"} <= set(table.columns):
        raise ValueError(f"unexpected NOAA CO2 columns {list(table.columns)}; need year, mean")
    frame = pd.DataFrame(
        {
            "year": pd.to_numeric(table["year"], errors="raise").astype(int),
            "co2_ppm": pd.to_numeric(table["mean"], errors="raise").astype(float),
        }
    )
    frame = frame.loc[frame["year"] <= cutoff_year].sort_values("year", ignore_index=True)
    if frame.empty or frame["year"].duplicated().any():
        raise ValueError("NOAA CO2 table is empty or has duplicate years after the cut-off filter")
    assert_weather_cutoff(frame, name="NOAA Mauna Loa CO2", cutoff_year=cutoff_year)
    return frame


def main(destination: Path = DESTINATION) -> None:
    """Write the capped CSV and a provenance receipt; refuse to overwrite existing data."""
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(
            f"{destination} already contains external data; refusing to overwrite it"
        )
    with urlopen(URL, timeout=60) as response:
        text = response.read().decode("utf-8")
    frame = parse_co2_annual(text)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / FILE_NAME
    frame.to_csv(path, index=False, float_format="%.2f")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (destination / "SOURCE.txt").write_text(
        "\n".join(
            [
                f"source={URL}",
                "artifact=NOAA GML Mauna Loa annual mean CO2 (ppm)",
                f"kept_years={frame['year'].min()}-{frame['year'].max()} (capped at 2018)",
                "use=forcing for the P21 forced-trend benchmark; never observed post-2018 values",
                "license=public domain U.S. government work (NOAA GML; cite Lan, Tans and Thoning)",
                f"sha256={digest}",
                "downloaded_by=scripts/download_noaa_co2.py",
                "",
            ]
        )
    )
    print(f"Wrote {len(frame)} years to {path} (sha256 {digest})")


if __name__ == "__main__":
    main()
