import importlib.util
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

from proto_star.climate import ClimateDataError
from proto_star.paths import PROJECT_ROOT


def _script() -> ModuleType:
    path = PROJECT_ROOT / "scripts" / "download_protostar_data.py"
    spec = importlib.util.spec_from_file_location("download_protostar_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_tables(last_year: int = 2018) -> dict[str, pd.DataFrame]:
    return {
        "city_info": pd.DataFrame({"ID": ["A"], "Name": ["a"]}),
        "daily": pd.DataFrame({"ID": ["A"], "Date": [f"{last_year}-12-31"], "tmax": [1.0]}),
        "coverage_and_stations": pd.DataFrame({"ID": ["A"], "Year": [last_year]}),
    }


def test_download_missing_writes_only_absent_tables(tmp_path: Path) -> None:
    script = _script()
    tables = _fake_tables()
    existing = tmp_path / "city_info.parquet"
    pd.DataFrame({"ID": ["original"]}).to_parquet(existing, index=False)
    requested: list[str] = []

    def load(name: str) -> pd.DataFrame:
        requested.append(name)
        return tables[name]

    written = script.download_missing(tmp_path, load=load, tables=tuple(tables))

    assert written == ["daily", "coverage_and_stations"]
    assert requested == written
    assert list(pd.read_parquet(existing)["ID"]) == ["original"]
    assert (tmp_path / "coverage_and_stations.parquet").exists()
    assert "coverage_and_stations" in (tmp_path / "SOURCE.txt").read_text()


def test_download_missing_rejects_post_cutoff_rows_before_writing(tmp_path: Path) -> None:
    script = _script()
    tables = _fake_tables(last_year=2019)
    with pytest.raises(ClimateDataError, match="after allowed cutoff"):
        script.download_missing(tmp_path, load=tables.__getitem__, tables=tuple(tables))
    assert not list(tmp_path.glob("*.parquet"))
