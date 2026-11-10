from pathlib import Path

import pandas as pd

from proto_star.data.daily_fold import daily_to_cutoff


def _write_daily(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "ID": ["X1", "X1", "X1", "X2"],
            "Name": ["A", "A", "A", "B"],
            "Date": pd.to_datetime(["1989-12-31", "1990-12-31", "1991-01-01", "2018-12-31"]),
            "tmax": [50.0, 60.0, 70.0, 80.0],
            "tmin": [30.0, 40.0, 50.0, 60.0],
            "prcp": [0.0, 0.1, 0.2, 0.3],
        }
    ).to_parquet(tmp_path / "daily.parquet", index=False)


def test_daily_to_cutoff_drops_every_later_date(tmp_path: Path) -> None:
    _write_daily(tmp_path)
    fold = daily_to_cutoff(1990, data_dir=tmp_path, columns=["tmax"])
    assert fold["Date"].max() == pd.Timestamp("1990-12-31")
    assert fold["tmax"].tolist() == [50.0, 60.0]
    assert list(fold.columns) == ["ID", "Date", "tmax"]


def test_daily_to_cutoff_returns_independent_copies(tmp_path: Path) -> None:
    _write_daily(tmp_path)
    first = daily_to_cutoff(2018, data_dir=tmp_path, columns=["tmax"])
    first["tmax"] = -999.0
    again = daily_to_cutoff(2018, data_dir=tmp_path, columns=["tmax"])
    assert (again["tmax"] > 0).all()
    assert len(again) == 4
