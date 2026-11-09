"""Regions for the Coupled Regional Model: the fixed coordinate regions or data-driven clusters.

Clusters are recomputed from the training rows of each fold, so they never see later years.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from proto_star.data.protostar import assign_region

TEMPERATURE = "annual_avg_temp"
EARTH_RADIUS_KM = 6371.0


def city_coordinates(train: pd.DataFrame) -> pd.DataFrame:
    """One row per city id with ``Lat``, ``Lon`` and the fixed ``region`` label."""
    cities = train.groupby(train["ID"].astype(str))[["Lat", "Lon"]].first()
    if "region" in train.columns:
        region = train.groupby(train["ID"].astype(str))["region"].first().astype(str)
    else:
        region = assign_region(cities["Lat"], cities["Lon"]).astype(str)
    cities["region"] = region.reindex(cities.index)
    cities.index.name = "city_id"
    return cities


def _distance_km(cities: pd.DataFrame) -> np.ndarray:
    lat = np.radians(cities["Lat"].to_numpy(dtype=float))
    lon = np.radians(cities["Lon"].to_numpy(dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat)[:, None] * np.cos(lat)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def detrended_anomalies(
    history: pd.DataFrame, cutoff_year: int, window: int, min_years: int
) -> pd.DataFrame:
    """Year x city table of temperature minus each city's own straight line over ``window``."""
    rows = history.loc[
        (history["metric"] == TEMPERATURE)
        & history["year"].between(cutoff_year - window + 1, cutoff_year)
    ]
    rows = rows.loc[rows.groupby("city_id")["year"].transform("size") >= min_years]
    by_city = rows.groupby("city_id")
    x = rows["year"] - by_city["year"].transform("mean")
    y = rows["actual_value"] - by_city["actual_value"].transform("mean")
    slope = (x * y).groupby(rows["city_id"]).sum() / (x**2).groupby(rows["city_id"]).sum()
    residual = y - x * rows["city_id"].map(slope)
    return pd.DataFrame(
        {"city_id": rows["city_id"], "year": rows["year"], "r": residual}
    ).pivot_table(index="year", columns="city_id", values="r")


def spectral_regions(
    history: pd.DataFrame,
    cities: pd.DataFrame,
    *,
    cutoff_year: int,
    n_clusters: int,
    window: int,
    min_years: int,
    geo_weight: float,
    geo_scale_km: float,
    seed: int,
) -> pd.Series:
    """Spectral clusters of cities from anomaly correlation blended with closeness on the map.

    Affinity = (1 - geo_weight) * max(correlation, 0) + geo_weight * exp(-(distance/scale)^2).
    Cities with too few years have no correlation and are placed by geography alone.
    """
    from sklearn.cluster import SpectralClustering  # lazy: only this region option needs it

    anomalies = detrended_anomalies(history, cutoff_year, window, min_years)
    corr = (
        anomalies.corr(min_periods=min_years)
        .reindex(index=cities.index, columns=cities.index)
        .fillna(0.0)
        .to_numpy()
    )
    geo = np.exp(-((_distance_km(cities) / geo_scale_km) ** 2))
    affinity = (1.0 - geo_weight) * np.clip(corr, 0.0, 1.0) + geo_weight * geo
    affinity = (affinity + affinity.T) / 2.0
    np.fill_diagonal(affinity, 1.0)
    model = SpectralClustering(
        n_clusters=n_clusters,
        affinity="precomputed",
        assign_labels="discretize",
        random_state=seed,
    )
    labels = model.fit_predict(affinity)
    return pd.Series([f"cluster_{label}" for label in labels], index=cities.index, name="region")
