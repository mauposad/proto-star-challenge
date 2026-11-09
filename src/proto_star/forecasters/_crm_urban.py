"""Urban-growth covariate for the Coupled Regional Model (plan 5.6 row 8, replication item 12).

Census population is not weather and does not respond to it, so it may be read inside a
forecaster. Only censuses held on or before the fold cut-off are used: growth is the log ratio
of the latest census at or before the cut-off to the one ten years earlier (1980 fold: 1980 over
1970; 2018 forecast: 2010 over 2000, the same rule as the folds).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.paths import PROCESSED_DIR, PROJECT_ROOT

CITY_STATIC_PATH = PROCESSED_DIR / "external" / "city_static.parquet"
PACKAGED_CITY_STATIC_PATH = PROJECT_ROOT.parent / "data" / "city_static.parquet"
CENSUS_YEARS = (1970, 1980, 1990, 2000, 2010, 2020)


def _default_city_static_path() -> Path:
    """Repository artifact, or the curated population-only copy beside packaged code."""
    return CITY_STATIC_PATH if CITY_STATIC_PATH.exists() else PACKAGED_CITY_STATIC_PATH


def load_city_static(path: Path | None = None) -> pd.DataFrame:
    """Read the per-city Census table built by the external-data work (one row per city)."""
    path = _default_city_static_path() if path is None else path
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found; the CRM urban covariate needs the external city_static table"
        )
    columns = ["ID", *[f"pop_{year}" for year in CENSUS_YEARS]]
    table = pd.read_parquet(path, columns=columns)
    if table["ID"].duplicated().any():
        raise ValueError(f"{path} has duplicate city IDs")
    return table


def urban_growth(city_static: pd.DataFrame, cutoff_year: int) -> pd.Series:
    """Log population growth over the last census decade at or before ``cutoff_year``.

    Empty when fewer than two censuses precede the cut-off; then the covariate is off.
    """
    held = [year for year in CENSUS_YEARS if year <= cutoff_year]
    if len(held) < 2:
        return pd.Series(dtype=float)
    latest, earlier = held[-1], held[-2]
    table = city_static.set_index(city_static["ID"].astype(str))
    now = pd.to_numeric(table[f"pop_{latest}"], errors="coerce")
    before = pd.to_numeric(table[f"pop_{earlier}"], errors="coerce")
    ratio = now.where(now > 0) / before.where(before > 0)
    growth = pd.Series(np.log(ratio.to_numpy(dtype=float)), index=ratio.index, name="urban_growth")
    return growth.dropna()


def urban_gamma(
    anomalies: pd.DataFrame, base_slope: pd.Series, growth: pd.Series
) -> tuple[float, pd.Series]:
    """One pooled ``gamma``: city slope offset per unit of centered urban growth.

    ``anomalies`` are the champion's within-city ``x, y`` rows (``city_id``, ``x``, ``y``);
    ``base_slope`` the city's slope before the covariate. Gamma is the least-squares fit of
    ``y - base_slope * x = gamma * g * x`` across all cities, with ``g`` growth minus its mean,
    so the average slope is unchanged. Returns gamma and the centered growth per city.
    """
    rows = anomalies.loc[anomalies["city_id"].isin(growth.index)]
    if rows.empty:
        return 0.0, pd.Series(dtype=float)
    centered = growth - growth.loc[rows["city_id"].unique()].mean()
    g = rows["city_id"].map(centered)
    residual = rows["y"] - rows["city_id"].map(base_slope).fillna(0.0) * rows["x"]
    spread = float(((g * rows["x"]) ** 2).sum())
    gamma = float((g * rows["x"] * residual).sum()) / spread if spread > 0 else 0.0
    return gamma, centered
