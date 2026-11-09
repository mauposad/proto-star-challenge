import json

import numpy as np
import pandas as pd
import pytest

from proto_star.climate import ClimateDataError
from proto_star.data.external.census import (
    city_counties_from_geocoder,
    city_population_table,
    combine_county_population,
    geocode_city,
    parse_co99_text,
    parse_intercensal_text,
    parse_popest_csv,
    population_growth_to_cutoff,
)

E7079 = """Preliminary Estimates of the Intercensal Population of Counties

FIPS                      Census Estimate  Estimate  Estimate  Estimate
Code  Area Name            1970      1971      1972      1973      1974

01000 Alabama           3444354   3497000   3540000   3581000   3628000
01001 Autauga Co.         24460     25500     27200     28500     29300
02090 Fairbanks North
       Star Bor.          45864     47300     47700     47700     48500
12025 Dade Co.          1267792   1325000   1377400   1409500   1448700
"""


def _co99_line(fips: str, values: list[str]) -> str:
    return f"1  {fips}" + "".join(f"{value:>12}" for value in values) + " Some County"


def test_intercensal_text_handles_wrapped_names_and_renames() -> None:
    table = parse_intercensal_text(E7079, source_file="e7079co.txt")
    assert set(table["fips"]) == {"01001", "02090", "12086"}  # state row dropped, Dade renamed
    fairbanks = table[table["fips"] == "02090"].set_index("year")
    assert fairbanks.loc[1970, "population"] == 45864
    assert fairbanks.loc[1970, "kind"] == "census"
    assert fairbanks.loc[1974, "kind"] == "estimate"


def test_co99_uses_april_base_and_survives_corrupt_field() -> None:
    values = [f"{1000 + i:,}" for i in range(10, 0, -1)] + ["900"]
    corrupt = list(values)
    corrupt[2] = "1\x00\xa0\x9e0"
    text = "\n".join([_co99_line("01001", values), _co99_line("01003", corrupt)])
    table = parse_co99_text(text)
    first = table[table["fips"] == "01001"].set_index("year")
    assert first.loc[1990, "population"] == 900 and first.loc[1990, "kind"] == "census"
    assert first.loc[1999, "population"] == 1010
    assert len(first) == 10  # 1991-1999 estimates + 1990 census, July 1990 dropped
    second = table[table["fips"] == "01003"].set_index("year")
    assert 1997 not in second.index  # corrupted field dropped, neighbours intact
    assert second.loc[1996, "population"] == 1007


def test_popest_csv_kinds_and_county_rows_only() -> None:
    raw = (
        b"SUMLEV,STATE,COUNTY,CENSUS2010POP,ESTIMATESBASE2010,POPESTIMATE2011\n"
        b"40,1,0,100,100,110\n"
        b"50,1,1,40,41,45\n"
    )
    table = parse_popest_csv(raw, source_file="x.csv")
    assert set(table["fips"]) == {"01001"}
    combined = combine_county_population([table])
    row_2010 = combined[combined["year"] == 2010].iloc[0]
    assert row_2010["kind"] == "census" and row_2010["population"] == 40


def test_combine_prefers_census_then_later_vintage() -> None:
    old = pd.DataFrame(
        {
            "fips": ["01001", "01001"],
            "year": [1990, 1991],
            "population": [10.0, 11.0],
            "kind": ["census", "estimate"],
            "source_file": "a",
        }
    )
    new = old.assign(population=[99.0, 12.0], kind=["estimate", "estimate"], source_file="b")
    combined = combine_county_population([old, new]).set_index("year")
    assert combined.loc[1990, "population"] == 10.0
    assert combined.loc[1991, "population"] == 12.0


def test_geocoder_to_city_population_and_growth() -> None:
    response = {
        "result": {
            "geographies": {
                "Counties": [{"GEOID": "01001", "NAME": "Autauga County", "AREALAND": 2e9}],
                "Incorporated Places": [],
            }
        }
    }
    seen: dict[str, str] = {}

    def fake_get(url: str, params: dict[str, str]) -> str:
        seen.update(params)
        return json.dumps(response)

    raw = geocode_city(32.5, -86.6, fake_get)
    assert seen["x"] == "-86.6" and seen["y"] == "32.5"
    counties = city_counties_from_geocoder({"USW1": raw})
    assert counties.loc[0, "county_land_km2"] == 2000.0
    assert pd.isna(counties.loc[0, "place_name"])
    population = pd.DataFrame(
        {
            "fips": "01001",
            "year": [1970, 1980, 1990, 2000, 2010, 2020],
            "population": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
            "kind": "census",
            "source_file": "x",
        }
    )
    wide = city_population_table(counties, population)
    assert wide.loc[0, "pop_1980"] == 200.0
    assert population_growth_to_cutoff(wide, 1980)["USW1"] == pytest.approx(np.log(2))
    assert population_growth_to_cutoff(wide, 1995)["USW1"] == pytest.approx(np.log(1.5))
    assert population_growth_to_cutoff(wide, 2018)["USW1"] == pytest.approx(np.log(1.25))
    with pytest.raises(ClimateDataError):
        population_growth_to_cutoff(wide, 1975)
