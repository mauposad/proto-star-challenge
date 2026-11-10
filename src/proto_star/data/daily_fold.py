"""Daily ProtoStar records for one backtest fold, capped at the fold's cut-off year.

A forecaster gets only annual rows in ``train``. Methods that need daily values (the CDD daily
map, the second-highest daily maximum) read them here, the one place allowed by plan rule 4:
every result is filtered to dates up to 31 December of ``cutoff_year`` and then checked with
:func:`proto_star.climate.assert_weather_cutoff` at that cut-off.

The full table (about 10M rows) is read once per process and kept in a small cache, because a
27-origin run would otherwise read it hundreds of times. The cache holds the raw file only;
each call returns a new, fold-capped copy, so callers cannot change what later folds see.

In the repo the table is ``data/raw/protostar/daily.parquet``. In a submission package it is
``<package>/data/daily.parquet``, beside the packaged code (``proto_star.submission_package``
ships it when the submitted forecaster reads daily data); see :func:`default_daily_dir`.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

import pandas as pd

from proto_star.climate import assert_weather_cutoff
from proto_star.data.protostar import DAILY_VALUE_COLUMNS, PROTOSTAR_DIR, load_daily
from proto_star.paths import PROJECT_ROOT

DAILY_FILE = "daily.parquet"
DAILY_DIR = PROTOSTAR_DIR
PACKAGED_DAILY_DIR = PROJECT_ROOT.parent / "data"  # <package>/data when run from <package>/code


def default_daily_dir() -> Path:
    """The repo's raw daily folder, or the packaged copy beside the code if the repo has none."""
    return DAILY_DIR if (DAILY_DIR / DAILY_FILE).exists() else PACKAGED_DAILY_DIR


@lru_cache(maxsize=2)  # cache of an immutable raw file, not mutable state: see module docstring
def _full_daily(data_dir: str, columns: tuple[str, ...]) -> pd.DataFrame:
    return load_daily(Path(data_dir), columns=columns)


def daily_to_cutoff(
    cutoff_year: int,
    *,
    data_dir: Path | None = None,
    columns: Sequence[str] = DAILY_VALUE_COLUMNS,
) -> pd.DataFrame:
    """Daily rows (``ID, Date, *columns``) with ``Date`` up to the end of ``cutoff_year``."""
    full = _full_daily(str(data_dir or default_daily_dir()), tuple(columns))
    fold = full.loc[full["Date"].dt.year <= cutoff_year].copy()
    assert_weather_cutoff(fold, name=f"daily fold {cutoff_year}", cutoff_year=cutoff_year)
    return fold
