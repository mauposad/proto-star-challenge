import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.climate import ClimateDataError
from proto_star.data.external.city_static import build_city_static
from proto_star.data.external.geography import (
    COASTLINE_FILE,
    LAKES_FILE,
    coast_and_lake_distances,
    line_vertices,
    nearest_distance_km,
)


def _line(name: str, coords: list[list[float]]) -> dict:
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {"type": "LineString", "coordinates": coords},
    }


def test_distance_to_vertices_is_great_circle() -> None:
    vertices = line_vertices({"features": [_line("x", [[-80.0, 40.0], [-80.0, 41.0]])]})
    distance = nearest_distance_km(pd.Series([42.0]), pd.Series([-80.0]), vertices)
    assert distance.iloc[0] == pytest.approx(111.2, abs=0.2)  # one degree of latitude


def test_line_vertices_filters_names_and_box() -> None:
    geojson = {
        "features": [
            _line("Lake Erie", [[-81.0, 42.0]]),
            _line("Other", [[-90.0, 45.0]]),
            _line("Lake Erie", [[100.0, 42.0]]),  # outside North America box
        ]
    }
    vertices = line_vertices(geojson, names=["Lake Erie"])
    assert vertices.tolist() == [[42.0, -81.0]]
    with pytest.raises(ClimateDataError):
        line_vertices(geojson, names=["Lake Nowhere"])


def test_coast_and_lake_distances_from_files(tmp_path: Path) -> None:
    (tmp_path / COASTLINE_FILE).write_text(
        json.dumps({"features": [_line("coast", [[-70.0, 40.0]])]})
    )
    (tmp_path / LAKES_FILE).write_text(
        json.dumps({"features": [_line("Lake Erie", [[-81.0, 42.0]])]})
    )
    cities = pd.DataFrame({"ID": ["A"], "Lat": [40.0], "Lon": [-70.0]})
    out = coast_and_lake_distances(cities, tmp_path)
    assert out.loc[0, "dist_coast_km"] == pytest.approx(0.0)
    assert out.loc[0, "dist_great_lakes_km"] > 900


def test_build_city_static_requires_every_city() -> None:
    cities = pd.DataFrame(
        {
            "ID": ["A", "A", "B"],
            "Name": ["a", "a", "b"],
            "Lat": [40.0, 40.0, 30.0],
            "Lon": [-80.0, -80.0, -100.0],
        }
    )
    stations = pd.DataFrame(
        {"station_id": ["A", "B", "C"], "elevation_m": [1.0, 2.0, 3.0], "state": ["PA", "TX", "XX"]}
    )
    distances = pd.DataFrame({"ID": ["A", "B"], "dist_coast_km": [1.0, 2.0]})
    counties = pd.DataFrame({"ID": ["A", "B"], "county_land_km2": [10.0, 20.0]})
    population = pd.DataFrame(
        {"ID": ["A", "B"], "pop_2000": [50.0, 400.0], "pop_2010": [100.0, 400.0]}
    )
    table = build_city_static(
        cities,
        stations=stations,
        distances=distances,
        city_counties=counties,
        city_population=population,
    )
    assert table["ID"].tolist() == ["A", "B"]
    assert table["pop_density_2010_per_km2"].tolist() == [10.0, 20.0]
    assert table["region"].tolist() == ["Northeast", "South Central"]
    assert table["log_pop_growth_2000_2010"].tolist() == pytest.approx([np.log(2), 0.0])
    with pytest.raises(ClimateDataError):
        build_city_static(
            cities,
            stations=stations,
            distances=distances.iloc[:1],
            city_counties=counties,
            city_population=population,
        )
