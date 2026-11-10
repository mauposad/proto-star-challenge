"""HadCRUT4 annual global mean surface temperature (GMST) anomaly, capped at 2018.

Source: Met Office Hadley Centre / Climatic Research Unit, HadCRUT4 version 4.6.0.0, file
``HadCRUT.4.6.0.0.annual_ns_avg.txt`` (annual global mean of the ensemble median, anomaly
against 1961-1990), as archived by the Internet Archive on 2019-02-09 (the file date
PstarAlu cites). Morice et al. (2012), doi:10.1029/2011JD017187. Crown copyright (Met Office
terms: download for private study and scientific research; other uses need a Met Office
licence), so the file is not redistributed (``data/`` is git-ignored).

GMST responds to the weather, and the file has no server-side date filter, so
``scripts/download_hadcrut.py`` fetches it into memory, drops every row after 2018 with
:func:`cap_text` before anything is written or shown, and saves only the capped text.
:func:`load_hadcrut4_annual` checks the cap again on every read and then applies the fold
cut-off (use it from forecasters with ``cutoff_year`` = the fold cut-off).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from proto_star.climate import FORECAST_CUTOFF, ClimateDataError, assert_weather_cutoff
from proto_star.paths import EXTERNAL_DIR

HADCRUT_DIR = EXTERNAL_DIR / "hadcrut4"
HADCRUT_VERSION = "HadCRUT.4.6.0.0"
HADCRUT_FILE = HADCRUT_DIR / f"{HADCRUT_VERSION}.annual_ns_avg_to_2018.txt"
ARCHIVE_TIMESTAMP = "20190209180836"
ORIGINAL_URL = (
    "https://www.metoffice.gov.uk/hadobs/hadcrut4/data/current/time_series/"
    f"{HADCRUT_VERSION}.annual_ns_avg.txt"
)
# ``id_`` asks the archive for the original bytes, without its banner.
SOURCE_URL = f"https://web.archive.org/web/{ARCHIVE_TIMESTAMP}id_/{ORIGINAL_URL}"


def cap_text(text: str, last_year: int = FORECAST_CUTOFF) -> str:
    """Keep only the data lines of an annual HadCRUT4 file whose year is <= ``last_year``.

    Each data line starts with the year. Lines that do not start with a year are rejected,
    so an unexpected format stops the download rather than slipping through.
    """
    kept = []
    for line in text.splitlines():
        if not line.strip():
            continue
        first = line.split()[0]
        if not first.isdigit():
            raise ClimateDataError(f"unexpected HadCRUT4 line (no leading year): {line[:20]!r}")
        if int(first) <= last_year:
            kept.append(line)
    if not kept:
        raise ClimateDataError("HadCRUT4 text has no rows up to the cut-off")
    return "\n".join(kept) + "\n"


def parse_annual(text: str) -> pd.DataFrame:
    """``year, gmst`` from annual HadCRUT4 text (column 2 = ensemble median anomaly, degC)."""
    rows = [line.split() for line in text.splitlines() if line.strip()]
    if any(len(row) < 2 for row in rows):
        raise ClimateDataError("HadCRUT4 rows need at least a year and a median column")
    table = pd.DataFrame(
        {
            "year": [int(row[0]) for row in rows],
            "gmst": [float(row[1]) for row in rows],
        }
    )
    if table["year"].duplicated().any() or not table["year"].is_monotonic_increasing:
        raise ClimateDataError("HadCRUT4 years must be unique and increasing")
    return table


def load_hadcrut4_annual(
    cutoff_year: int = FORECAST_CUTOFF, path: Path = HADCRUT_FILE
) -> pd.DataFrame:
    """Annual GMST anomaly up to ``cutoff_year`` (use the fold cut-off): ``year, gmst``.

    The file is checked against the 2018 cap, then rows after ``cutoff_year`` are dropped
    and the result is checked against ``cutoff_year`` as well.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python scripts/download_hadcrut.py` (docs/data.md)."
        )
    table = parse_annual(path.read_text())
    assert_weather_cutoff(table, name=path.name)
    table = table.loc[table["year"] <= cutoff_year].reset_index(drop=True)
    assert_weather_cutoff(table, name=path.name, cutoff_year=cutoff_year)
    return table
