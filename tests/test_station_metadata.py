from pathlib import Path

import pandas as pd

from proto_star.station_metadata import build_station_metadata_report, load_ghcn_station_metadata


def test_station_metadata_parsing_and_challenge_join(tmp_path: Path) -> None:
    station_file = tmp_path / "ghcnd-stations.txt"
    station_file.write_text(
        f"{'USW00012345':<11} {'40.0000':>8} {'-79.0000':>9} {'300.0':>6} "
        f"{'PA':<2} {'Example Station':<30}\n"
    )
    stations = load_ghcn_station_metadata(station_file)
    cities = pd.DataFrame(
        {"ID": ["USW00012345"], "Name": ["ExampleCity"], "Lat": [40.0], "Lon": [-79.0]}
    )
    report = build_station_metadata_report(cities, stations)
    assert bool(report.loc[0, "metadata_found"])
    assert report.loc[0, "elevation_m"] == 300.0
    assert report.loc[0, "challenge_city"] == "ExampleCity"
