"""Per-city, per-year June-August means from the daily table (for hypotheses H2/H14).

Every value uses only that year's days; nothing here is a multi-year statistic.  Joining the
table to the annual master on ``(ID, Year)`` therefore leaves the backtest's ``Year <= cutoff``
filter as the only guard against leakage (methodologist finding X5 in
``hypotheses_review.md``).  Levels, slopes and anything else that spans years must still be
computed inside each forecaster.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from proto_star.climate import assert_weather_cutoff
from proto_star.paths import INTERIM_DIR

SUMMER_DIR = INTERIM_DIR / "protostar"
SUMMER_FILE = "summer_means.parquet"
SUMMER_MONTHS = (6, 7, 8)
MIN_SUMMER_DAYS = 85  # of 92 June-August days, with both tmax and tmin observed
SUMMER_COLUMNS = ("jja_tmax", "jja_tavg", "jja_days")


def summer_means(daily: pd.DataFrame) -> pd.DataFrame:
    """June-August mean Tmax and mean (Tmax+Tmin)/2 per city and year, blank below 85 days."""
    dates = pd.to_datetime(daily["Date"])
    summer = daily.loc[dates.dt.month.isin(SUMMER_MONTHS)].copy()
    summer = summer.dropna(subset=["tmax", "tmin"])
    summer["ID"] = summer["ID"].astype(str)
    summer["Year"] = pd.to_datetime(summer["Date"]).dt.year.astype("int64")
    summer["tavg"] = (summer["tmax"].astype(float) + summer["tmin"].astype(float)) / 2
    table = summer.groupby(["ID", "Year"], as_index=False).agg(
        jja_tmax=("tmax", "mean"), jja_tavg=("tavg", "mean"), jja_days=("tmax", "size")
    )
    short = table["jja_days"] < MIN_SUMMER_DAYS
    table.loc[short, ["jja_tmax", "jja_tavg"]] = float("nan")
    table["jja_tmax"] = table["jja_tmax"].astype(float)
    table["jja_tavg"] = table["jja_tavg"].astype(float)
    return table.sort_values(["ID", "Year"], ignore_index=True)


def load_summer_means(data_dir: Path | None = None) -> pd.DataFrame:
    """Read the summer table, enforcing the forecast cut-off."""
    path = (data_dir or SUMMER_DIR) / SUMMER_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `uv run python scripts/build_summer_means.py`."
        )
    table = pd.read_parquet(path)
    assert_weather_cutoff(table, name="summer_means")
    return table


def join_summer(master: pd.DataFrame, summer: pd.DataFrame) -> pd.DataFrame:
    """Add the summer columns to the master, one-to-one on ``(ID, Year)``."""
    keyed = summer.assign(ID=summer["ID"].astype(str))
    out = master.assign(ID=master["ID"].astype(str)).merge(
        keyed[["ID", "Year", *SUMMER_COLUMNS]], on=["ID", "Year"], how="left", validate="1:1"
    )
    return out
