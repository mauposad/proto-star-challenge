from pathlib import Path

import pandas as pd
import pytest

from proto_star.climate import ClimateDataError
from proto_star.data.external.ghcn_neighbors import (
    ads_params,
    candidate_stations,
    load_neighbor_annual,
    nearest_neighbors,
    parse_gsoy,
    parse_inventory,
)


def _inventory_line(
    station: str, lat: float, lon: float, element: str, first: int, last: int
) -> str:
    return f"{station:<11} {lat:>8.4f} {lon:>9.4f} {element:<4} {first:>4} {last:>4}"


def test_inventory_candidates_and_neighbors() -> None:
    text = "\n".join(
        [
            _inventory_line("USW00000001", 40.0, -80.0, "TMAX", 1900, 2026),
            _inventory_line("USW00000001", 40.0, -80.0, "TMIN", 1900, 2026),
            _inventory_line("USC00000002", 40.1, -80.0, "TMAX", 1950, 2026),
            _inventory_line("USC00000002", 40.1, -80.0, "TMIN", 1950, 2026),
            _inventory_line("USC00000003", 40.2, -80.0, "TMAX", 1980, 2026),  # starts too late
            _inventory_line("USC00000003", 40.2, -80.0, "TMIN", 1980, 2026),
            _inventory_line("USC00000004", 40.3, -80.0, "TMAX", 1900, 2026),  # no TMIN
            _inventory_line("USC00000005", 45.0, -80.0, "TMAX", 1900, 2026),  # too far
            _inventory_line("USC00000005", 45.0, -80.0, "TMIN", 1900, 2026),
            _inventory_line("CA000000006", 40.0, -80.1, "TMAX", 1900, 2026),  # not U.S.
            _inventory_line("CA000000006", 40.0, -80.1, "TMIN", 1900, 2026),
        ]
    )
    candidates = candidate_stations(parse_inventory(text))
    assert set(candidates["station_id"]) == {"USW00000001", "USC00000002", "USC00000005"}
    cities = pd.DataFrame({"ID": ["USW00000001"], "Lat": [40.0], "Lon": [-80.0]})
    neighbors = nearest_neighbors(cities, candidates)
    assert neighbors["neighbor_id"].tolist() == ["USC00000002"]  # own station excluded
    assert neighbors.loc[0, "distance_km"] == pytest.approx(11.1, abs=0.1)


def test_query_is_capped_server_side() -> None:
    params = ads_params(["USW00000001", "USC00000002"])
    assert params["endDate"] == "2018-12-31"
    assert params["stations"] == "USW00000001,USC00000002"


def test_gsoy_leak_test_rejects_2019() -> None:
    ok = b'"STATION","DATE","TAVG","PRCP"\n"USC00000002","2017","55.1","40.2"\n'
    table = parse_gsoy(ok, name="ok")
    assert table.columns.tolist()[:3] == ["station_id", "year", "tavg"]
    assert table["cldd"].isna().all()
    leaky = ok + b'"USC00000002","2019","56.0","41.0"\n'
    with pytest.raises(ClimateDataError, match="2019"):
        parse_gsoy(leaky, name="leaky")
    with pytest.raises(ClimateDataError):
        parse_gsoy(b"<html>error</html>\n", name="page")


def test_fold_loader_caps_at_cutoff(tmp_path: Path) -> None:
    path = tmp_path / "annual.parquet"
    pd.DataFrame({"station_id": "A", "year": [1979, 1980, 1981, 2018], "tavg": 1.0}).to_parquet(
        path
    )
    assert load_neighbor_annual(1980, path)["year"].max() == 1980
    pd.DataFrame({"station_id": "A", "year": [1980, 2019], "tavg": 1.0}).to_parquet(path)
    with pytest.raises(ClimateDataError):
        load_neighbor_annual(1980, path)
