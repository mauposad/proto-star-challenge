from pathlib import Path

import pandas as pd
import pytest

from proto_star.data.protostar import (
    REGIONS,
    assign_region,
    city_table,
    load_annual,
    load_city_info,
    load_coverage,
    load_daily,
)


def _write_tables(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "Name": ["A", "A", "B"],
            "ID": ["X1", "X1", "X2"],
            "Lat": [45.0, 45.0, 30.0],
            "Lon": [-120.0, -120.0, -80.0],
            "Year": [2000, 2001, 2001],
        }
    ).to_parquet(tmp_path / "annual_indices.parquet", index=False)
    pd.DataFrame(
        {
            "Name": ["A", "A", "B"],
            "ID": ["X1", "X1", "X2"],
            "Stn.stDate": ["1990-01-01", "2000-06-01", "1990-01-01"],
            "Stn.edDate": ["2000-05-31", "2018-12-31", "2018-12-31"],
        }
    ).to_parquet(tmp_path / "city_info.parquet", index=False)
    pd.DataFrame(
        {
            "ID": ["X1", "X1", "X2"],
            "Name": ["A", "A", "B"],
            "Year": [2000, 2001, 2001],
            "Days Both": [366, 364, 365],
            "Station Segment": [1, 2, 1],
            "Station Changes": [0, 1, 0],
        }
    ).to_parquet(tmp_path / "coverage_and_stations.parquet", index=False)
    pd.DataFrame(
        {
            "ID": ["X1", "X1", "X2"],
            "Name": ["A", "A", "B"],
            "Date": ["2001-01-01", "2001-01-02", "2001-01-01"],
            "tmax": [50.0, None, 70.0],
            "tmin": [30.0, 31.0, 55.0],
            "prcp": [0.0, 0.1, None],
        }
    ).to_parquet(tmp_path / "daily.parquet", index=False)


def test_assign_region_covers_all_six_regions() -> None:
    lat = pd.Series([45.0, 30.0, 45.0, 30.0, 45.0, 30.0])
    lon = pd.Series([-120.0, -110.0, -95.0, -95.0, -75.0, -82.0])
    assert list(assign_region(lat, lon)) == list(REGIONS)


def test_assign_region_boundaries_go_east_and_north() -> None:
    region = assign_region(pd.Series([37.0, 36.99]), pd.Series([-104.0, -87.0]))
    assert list(region) == ["North Central", "Southeast"]


def test_load_daily_filters_cities_and_compacts_types(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    daily = load_daily(tmp_path, city_ids=["X1"], columns=["tmax"])
    assert list(daily.columns) == ["ID", "Date", "tmax"]
    assert set(daily["ID"]) == {"X1"}
    assert isinstance(daily["ID"].dtype, pd.CategoricalDtype)
    assert pd.api.types.is_datetime64_any_dtype(daily["Date"])
    assert daily["tmax"].dtype == "float32"
    assert daily["tmax"].isna().sum() == 1


def test_load_daily_rejects_unknown_columns(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    with pytest.raises(ValueError, match="unknown daily columns"):
        load_daily(tmp_path, columns=["snow"])


def test_missing_table_points_to_download_script(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="download_protostar_data"):
        load_annual(tmp_path)


def test_city_table_summarises_span_threads_and_region(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    cities = city_table(load_annual(tmp_path), load_city_info(tmp_path))
    x1 = cities.set_index("ID").loc["X1"]
    assert (x1["first_year"], x1["last_year"], x1["n_years"]) == (2000, 2001, 2)
    assert x1["n_station_threads"] == 2
    assert x1["region"] == "Northwest"
    assert cities.set_index("ID").loc["X2", "region"] == "Southeast"


def test_load_coverage_reads_city_year_rows(tmp_path: Path) -> None:
    _write_tables(tmp_path)
    coverage = load_coverage(tmp_path)
    assert not coverage.duplicated(["ID", "Year"]).any()
    assert list(coverage["Station Segment"]) == [1, 2, 1]
