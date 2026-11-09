import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

from proto_star.paths import PROJECT_ROOT
from proto_star.trial import TrialConfig


def _script() -> ModuleType:
    path = PROJECT_ROOT / "scripts" / "build_city_population.py"
    spec = importlib.util.spec_from_file_location("build_city_population", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config(submit: str | None) -> TrialConfig:
    return TrialConfig.model_validate(
        {
            "name": "unit",
            "description": "unit",
            "forecasters": ["thirty_year_mean", "urban", "plain"],
            "models": {
                "urban": {"kind": "crm", "params": {"urban": True}},
                "plain": {"kind": "crm", "params": {}},
            },
            "reference": "thirty_year_mean",
            "submit": submit,
        }
    )


@pytest.mark.parametrize(
    ("submit", "override", "expected"),
    [
        ("urban", None, True),
        ("plain", None, False),
        ("thirty_year_mean", None, False),
        (None, None, False),
        ("plain", "urban", True),
        ("urban", "plain", False),
    ],
)
def test_population_is_built_only_for_an_urban_crm(
    submit: str | None, override: str | None, expected: bool
) -> None:
    assert _script().needs_city_population(_config(submit), override) is expected


def test_population_table_has_one_row_per_city_and_rejects_gaps(tmp_path: Path) -> None:
    script = _script()
    census = tmp_path / "census"
    census.mkdir()
    (census / "city_county_geocoder.json").write_text(json.dumps({"A": {}, "B": {}}))
    counties = pd.DataFrame({"ID": ["A", "B"], "county_fips": ["01001", "01003"]})
    years = (1970, 1980, 1990, 2000, 2010, 2020)
    population = pd.DataFrame(
        [
            {"fips": fips, "year": year, "population": 1000.0 * (i + 1) + year, "kind": "census"}
            for i, fips in enumerate(["01001", "01003"])
            for year in years
        ]
    )
    script.city_counties_from_geocoder = lambda responses: counties
    script.load_county_population = lambda directory: population
    out = script.build_city_population(tmp_path / "out" / "city_static.parquet", census)
    table = pd.read_parquet(out)
    assert table.columns.tolist() == ["ID", *[f"pop_{year}" for year in years]]
    assert table["ID"].tolist() == ["A", "B"]

    script.load_county_population = lambda directory: population[population["fips"] == "01001"]
    with pytest.raises(ValueError, match="missing for cities \\['B'\\]"):
        script.build_city_population(tmp_path / "out2.parquet", census)
