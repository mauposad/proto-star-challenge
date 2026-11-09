"""U.S. Census county population (1970-2023) joined to the challenge cities.

Population does not respond to the weather, so any year may be read. The forecasting
convention (docs/plan_regional_and_papers.md, Section 6.1) is still to use only the
population change up to each fold's cut-off; ``population_growth_to_cutoff`` does that.

Each city is mapped to the county that contains its station coordinates (Census
geocoder, 2010 county vintage). County population is a proxy for urban growth around
the station; the stations are mostly airports, not city centres.
"""

from __future__ import annotations

import io
import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.climate import ClimateDataError
from proto_star.paths import EXTERNAL_DIR

CENSUS_DIR = EXTERNAL_DIR / "census_county_population"
DECENNIAL_YEARS = (1970, 1980, 1990, 2000, 2010, 2020)

POPEST = "https://www2.census.gov/programs-surveys/popest"
SOURCE_FILES = {
    "e7079co.txt": f"{POPEST}/tables/1900-1980/counties/totals/e7079co.txt",
    "e8089co.txt": f"{POPEST}/tables/1980-1990/counties/totals/e8089co.txt",
    "99c8_00.txt": f"{POPEST}/tables/1990-2000/counties/totals/99c8_00.txt",
    "co-est00int-tot.csv": f"{POPEST}/datasets/2000-2010/intercensal/county/co-est00int-tot.csv",
    "co-est2019-alldata.csv": f"{POPEST}/datasets/2010-2019/counties/totals/co-est2019-alldata.csv",
    "co-est2023-alldata.csv": f"{POPEST}/datasets/2020-2023/counties/totals/co-est2023-alldata.csv",
}
GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
GEOCODER_PARAMS = {
    "benchmark": "Public_AR_Census2020",
    "vintage": "Census2010_Census2020",
    "layers": "Counties,Incorporated Places,Census Designated Places",
    "format": "json",
}
GEOCODE_FILE = "city_county_geocoder.json"

# County FIPS codes renamed after 1990; older files use the left-hand code.
FIPS_RENAMES = {"12025": "12086"}  # Dade -> Miami-Dade County, FL (1997)

_KIND_RANK = {"estimate": 0, "census_base": 1, "census": 2}
_POPULATION_COLUMNS = ["fips", "year", "population", "kind", "source_file"]


def _long(rows: list[tuple[str, int, float, str]], source_file: str) -> pd.DataFrame:
    table = pd.DataFrame(rows, columns=["fips", "year", "population", "kind"])
    table = table.dropna(subset=["population"])
    table["fips"] = table["fips"].replace(FIPS_RENAMES)
    table["source_file"] = source_file
    return table[_POPULATION_COLUMNS]


def parse_intercensal_text(text: str, *, source_file: str) -> pd.DataFrame:
    """Parse the 1970s (``e7079co``) or 1980s (``e8089co``) county estimate tables.

    Each block starts with a ``FIPS`` line naming ``Census``/``Estimate`` columns and a
    ``Code`` line naming the years; county lines are ``FIPS name value...``. State and
    national totals (FIPS ending in ``000``) are dropped.
    """
    rows: list[tuple[str, int, float, str]] = []
    kinds: list[str] = []
    years: list[int] = []
    pending: str | None = None  # long names wrap: values sit on the following line
    for line in text.splitlines():
        if line.startswith("FIPS"):
            kinds = [token.lower() for token in line.split()[1:]]
            continue
        if line.startswith("Code"):
            years = [int(token) for token in re.findall(r"\b(1[89]\d\d)\b", line)]
            if len(years) != len(kinds):
                raise ClimateDataError(f"{source_file}: header years {years} vs kinds {kinds}")
            continue
        match = re.match(r"^(\d{5})\s", line)
        if match:
            fips, pending = match.group(1), None
        elif pending is not None and line.strip():
            fips, pending = pending, None
        else:
            continue
        if not years or fips.endswith("000"):
            continue
        values = line.split()[-len(years) :]
        if not all(value.isdigit() for value in values):
            if match and not any(token.isdigit() for token in line.split()[1:]):
                pending = fips
                continue
            raise ClimateDataError(f"{source_file}: cannot parse county line {line!r}")
        rows.extend(
            (fips, year, float(value), kind)
            for year, value, kind in zip(years, values, kinds, strict=True)
        )
    if not rows:
        raise ClimateDataError(f"{source_file}: no county rows found")
    return _long(rows, source_file)


def parse_co99_text(text: str, *, source_file: str = "99c8_00.txt") -> pd.DataFrame:
    """Parse block 1 (total population) of ``CO-99-8``: July 1999 ... July 1990, April 1990.

    The last column is the April 1, 1990 census base, kept as the 1990 census count; the
    July 1990 estimate is dropped so each county has one value per year. Values sit in
    fixed 12-character columns. The file as served holds a few corrupted bytes (two
    county lines in block 1); a field that is not a number becomes NaN instead of
    shifting the other columns.
    """
    rows: list[tuple[str, int, float, str]] = []
    for line in text.splitlines():
        match = re.match(r"^1  (\d{5}) ", line)
        if not match:
            continue
        fields = [line[9 + 12 * i : 21 + 12 * i].strip() for i in range(11)]
        numbers = [
            float(field.replace(",", "")) if re.fullmatch(r"[\d,]+", field) else np.nan
            for field in fields
        ]
        rows.extend((match.group(1), 1999 - i, numbers[i], "estimate") for i in range(9))
        rows.append((match.group(1), 1990, numbers[10], "census"))
    if not rows:
        raise ClimateDataError(f"{source_file}: no county rows found")
    return _long(rows, source_file)


def parse_popest_csv(raw: bytes, *, source_file: str) -> pd.DataFrame:
    """Parse a Census ``co-est*`` county CSV (2000s, 2010s or 2020s vintage).

    ``CENSUS<yyyy>POP`` columns become ``census`` rows, ``ESTIMATESBASE<yyyy>`` (the
    April 1 census count with later corrections) ``census_base`` rows, and
    ``POPESTIMATE<yyyy>`` (July 1) ``estimate`` rows. Only county rows (SUMLEV 50) are kept.
    """
    table = pd.read_csv(io.BytesIO(raw), encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
    table = table[pd.to_numeric(table["SUMLEV"], errors="coerce") == 50]
    fips = table["STATE"].str.zfill(2) + table["COUNTY"].str.zfill(3)
    rows: list[tuple[str, int, float, str]] = []
    for column in table.columns:
        census = re.fullmatch(r"CENSUS(\d{4})POP", column)
        base = re.fullmatch(r"ESTIMATESBASE(\d{4})", column)
        estimate = re.fullmatch(r"POPESTIMATE(\d{4})", column)
        if census:
            year, kind = int(census.group(1)), "census"
        elif base:
            year, kind = int(base.group(1)), "census_base"
        elif estimate:
            year, kind = int(estimate.group(1)), "estimate"
        else:
            continue
        values = pd.to_numeric(table[column], errors="coerce")
        rows.extend(
            (code, year, float(value), kind)
            for code, value in zip(fips, values, strict=True)
            if pd.notna(value)
        )
    if not rows:
        raise ClimateDataError(f"{source_file}: no population columns found")
    return _long(rows, source_file)


def parse_source_file(name: str, raw: bytes) -> pd.DataFrame:
    """Dispatch one downloaded file in ``SOURCE_FILES`` to its parser."""
    if name.endswith(".csv"):
        return parse_popest_csv(raw, source_file=name)
    text = raw.decode("latin-1")
    if name.startswith("99c8"):
        return parse_co99_text(text, source_file=name)
    return parse_intercensal_text(text, source_file=name)


def combine_county_population(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """One population per county and year: ``census`` beats ``census_base`` beats ``estimate``.

    Within the same kind, the later vintage (later in ``parts``) wins.
    """
    frames = [part.assign(_order=i) for i, part in enumerate(parts)]
    table = pd.concat(frames, ignore_index=True)
    table["_rank"] = table["kind"].map(_KIND_RANK)
    if table["_rank"].isna().any():
        raise ClimateDataError(f"unknown population kinds: {set(table['kind']) - set(_KIND_RANK)}")
    table = table.sort_values(["fips", "year", "_rank", "_order"])
    table = table.drop_duplicates(["fips", "year"], keep="last")
    return table.drop(columns=["_order", "_rank"]).reset_index(drop=True)


def load_county_population(directory: Path = CENSUS_DIR) -> pd.DataFrame:
    """Read and combine every downloaded county population file in ``directory``."""
    missing = [name for name in SOURCE_FILES if not (directory / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"{directory} is missing {missing}. Run "
            "`uv run python scripts/download_census_population.py` (see docs/data.md)."
        )
    return combine_county_population(
        parse_source_file(name, (directory / name).read_bytes()) for name in SOURCE_FILES
    )


def geocode_city(lat: float, lon: float, get: Callable[[str, dict[str, str]], str]) -> dict:
    """Return the raw geocoder JSON for one coordinate. ``get(url, params)`` returns text."""
    params = {**GEOCODER_PARAMS, "x": f"{lon}", "y": f"{lat}"}
    return dict(json.loads(get(GEOCODER_URL, params)))


def city_counties_from_geocoder(responses: dict[str, dict]) -> pd.DataFrame:
    """Turn ``{city ID: geocoder JSON}`` into one county (and place, if any) per city."""
    rows = []
    for city_id, response in responses.items():
        geographies = response.get("result", {}).get("geographies", {})
        counties = geographies.get("Counties", [])
        places = geographies.get("Incorporated Places", []) or geographies.get(
            "Census Designated Places", []
        )
        county = counties[0] if counties else {}
        place = places[0] if places else {}
        rows.append(
            {
                "ID": city_id,
                "county_fips": county.get("GEOID"),
                "county_name": county.get("NAME"),
                "county_land_km2": float(county["AREALAND"]) / 1e6 if county else np.nan,
                "place_name": place.get("NAME"),
                "place_pop_2010": float(place["POP100"]) if place else np.nan,
            }
        )
    return pd.DataFrame(rows)


def city_population_table(
    city_counties: pd.DataFrame, county_population: pd.DataFrame
) -> pd.DataFrame:
    """Wide decennial table: ``pop_<year>`` and ``pop_<year>_source`` for each city.

    ``pop_<year>_source`` is ``census`` for a decennial count, ``census_base`` for the
    April 1 estimates base (2000, 2020), or ``estimate`` when only a July estimate exists.
    """
    decennial = county_population[county_population["year"].isin(DECENNIAL_YEARS)]
    merged = city_counties[["ID", "county_fips"]].merge(
        decennial, left_on="county_fips", right_on="fips", how="left"
    )
    values = merged.pivot_table(index="ID", columns="year", values="population", aggfunc="first")
    kinds = merged.pivot_table(index="ID", columns="year", values="kind", aggfunc="first")
    out = city_counties[["ID"]].set_index("ID")
    for year in DECENNIAL_YEARS:
        out[f"pop_{year}"] = values.get(year, np.nan)
        out[f"pop_{year}_source"] = kinds.get(year)
    return out.reset_index()


def population_growth_to_cutoff(city_population: pd.DataFrame, cutoff_year: int) -> pd.Series:
    """Log county population growth over the last census decade ending at or before cutoff.

    For the 1980 fold this is ``log(pop_1980 / pop_1970)``; for 1995, 1980 to 1990; for
    2011 and the final 2018 forecast, 2000 to 2010. Indexed by city ``ID``.
    """
    ends = [year for year in DECENNIAL_YEARS if year <= cutoff_year and year - 10 >= 1970]
    if not ends:
        raise ClimateDataError(f"no census decade ends at or before {cutoff_year}")
    end = ends[-1]
    ratio = city_population[f"pop_{end}"] / city_population[f"pop_{end - 10}"]
    growth = np.log(ratio.to_numpy(dtype=float))
    return pd.Series(growth, index=city_population["ID"], name=f"log_pop_growth_{end}")
