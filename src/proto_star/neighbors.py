"""Neighbor cities by great-circle distance, kernel weights and neighbor anomalies.

Shared by the final-round components (Tatakae's 31/32 nearest cities, PstarAlu's 300 km
Gaussian kernel). Coordinates are each city's ``Lat``/``Lon`` from the master table, which
come from ``city_info``. Anomalies are built from one fold's ``train`` only: the panel holds
years up to the cut-off, and each city's own mean is taken over a window ending at the cut-off.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from proto_star.climate import annual_to_long

EARTH_RADIUS_KM = 6371.0088


def city_coordinates(train: pd.DataFrame) -> pd.DataFrame:
    """One row per city id (index ``city_id``) with ``Lat`` and ``Lon``."""
    coords = train.groupby(train["ID"].astype(str))[["Lat", "Lon"]].first().astype(float)
    if coords.isna().any().any():
        missing = coords.index[coords.isna().any(axis=1)].tolist()
        raise ValueError(f"cities without coordinates: {missing[:5]}")
    coords.index.name = "city_id"
    return coords.sort_index()


def distance_matrix_km(coords: pd.DataFrame) -> pd.DataFrame:
    """Great-circle (haversine) distance in km between every pair of cities."""
    lat = np.radians(coords["Lat"].to_numpy(dtype=float))
    lon = np.radians(coords["Lon"].to_numpy(dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    km = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return pd.DataFrame(km, index=coords.index, columns=coords.index)


def nearest_neighbors(coords: pd.DataFrame, k: int) -> pd.DataFrame:
    """Each city's ``k`` nearest other cities: ``city_id, neighbor_id, rank, distance_km``.

    Ties in distance are broken by neighbor id, so the result is deterministic.
    """
    if k < 1:
        raise ValueError(f"k must be at least 1, got {k}")
    if k > len(coords) - 1:
        raise ValueError(f"k={k} but only {len(coords) - 1} other cities exist")
    distances = distance_matrix_km(coords)
    frame = distances.rename_axis(index="city_id", columns="neighbor_id").reset_index()
    frame = frame.melt(id_vars="city_id", var_name="neighbor_id", value_name="distance_km")
    frame = frame.loc[frame["city_id"] != frame["neighbor_id"]]
    frame = frame.sort_values(["city_id", "distance_km", "neighbor_id"], kind="mergesort")
    frame["rank"] = frame.groupby("city_id").cumcount() + 1
    frame = frame.loc[frame["rank"] <= k]
    return frame[["city_id", "neighbor_id", "rank", "distance_km"]].reset_index(drop=True)


def gaussian_kernel(distance_km: np.ndarray | pd.DataFrame, bandwidth_km: float) -> np.ndarray:
    """Unnormalized Gaussian weights ``exp(-0.5 (d / bandwidth)^2)``."""
    if bandwidth_km <= 0:
        raise ValueError(f"bandwidth_km must be positive, got {bandwidth_km}")
    d = np.asarray(distance_km, dtype=float)
    return np.asarray(np.exp(-0.5 * (d / bandwidth_km) ** 2))


def neighbor_weights(
    coords: pd.DataFrame,
    *,
    k: int | None = None,
    bandwidth_km: float | None = None,
    radius_km: float | None = None,
) -> pd.DataFrame:
    """City x neighbor weight matrix; each row sums to 1 over the city's neighbors.

    The city itself always gets weight 0 (leave-one-out). ``k`` keeps only the k nearest,
    ``radius_km`` only cities within that distance. ``bandwidth_km`` gives Gaussian weights;
    without it, kept neighbors weigh equally. A city with no neighbor kept gets an all-zero row.
    """
    if k is None and bandwidth_km is None and radius_km is None:
        raise ValueError("set at least one of k, bandwidth_km or radius_km")
    distances = distance_matrix_km(coords)
    n = len(distances)
    keep = ~np.eye(n, dtype=bool)
    if k is not None:
        position = {city: i for i, city in enumerate(distances.index)}
        nearest = nearest_neighbors(coords, k)
        in_k = np.zeros((n, n), dtype=bool)
        in_k[nearest["city_id"].map(position), nearest["neighbor_id"].map(position)] = True
        keep &= in_k
    if radius_km is not None:
        keep &= distances.to_numpy() <= radius_km
    raw = gaussian_kernel(distances, bandwidth_km) if bandwidth_km is not None else 1.0
    weights = pd.DataFrame(
        np.where(keep, raw, 0.0), index=distances.index, columns=distances.columns
    )
    total = weights.sum(axis=1)
    return weights.div(total.where(total > 0), axis=0).fillna(0.0)


def metric_panel(train: pd.DataFrame, metric: str, cutoff_year: int) -> pd.DataFrame:
    """City x year panel of one metric's valid values up to ``cutoff_year`` (NaN elsewhere)."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    rows = history.loc[history["metric"] == metric]
    panel = rows.pivot_table(
        index="city_id", columns="year", values="actual_value", aggfunc="first"
    )
    cities = sorted(train["ID"].astype(str).unique())
    years = range(int(train["Year"].min()), cutoff_year + 1)
    return panel.reindex(index=cities, columns=years)


def own_anomalies(
    panel: pd.DataFrame,
    cutoff_year: int,
    *,
    window: int = 30,
    min_years: int = 10,
    kind: Literal["difference", "ratio"] = "difference",
) -> pd.DataFrame:
    """Each value against the city's own mean over the ``window`` years ending at the cut-off.

    ``difference``: value - mean. ``ratio``: value / mean - 1 (for precipitation). Cities with
    fewer than ``min_years`` valid years in the window (or a non-positive mean, for ratio)
    get NaN everywhere.
    """
    if int(panel.columns.max()) > cutoff_year:
        raise ValueError("panel has years after the cut-off")
    years = [y for y in panel.columns if cutoff_year - window < int(y) <= cutoff_year]
    base = panel[years]
    mean = base.mean(axis=1).where(base.notna().sum(axis=1) >= min_years)
    if kind == "difference":
        return panel.sub(mean, axis=0)
    if kind == "ratio":
        mean = mean.where(mean > 0)
        return panel.div(mean, axis=0) - 1.0
    raise ValueError(f"kind must be 'difference' or 'ratio', got {kind!r}")


def neighbor_mean(anomalies: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """Weighted mean of each city's neighbors' anomalies per year, over neighbors with data.

    Weights of neighbors missing a year are dropped and the rest renormalized. A year with no
    neighbor data is NaN.
    """
    w = weights.reindex(index=anomalies.index, columns=anomalies.index).fillna(0.0).to_numpy()
    values = anomalies.to_numpy(dtype=float)
    present = np.isfinite(values)
    filled = np.where(present, values, 0.0)
    numerator = w @ filled
    denominator = w @ present.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(denominator > 0, numerator / denominator, np.nan)
    return pd.DataFrame(mean, index=anomalies.index, columns=anomalies.columns)


def departures(anomalies: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """Each city's anomaly minus its neighbors' weighted mean anomaly, per year."""
    return anomalies - neighbor_mean(anomalies, weights)
