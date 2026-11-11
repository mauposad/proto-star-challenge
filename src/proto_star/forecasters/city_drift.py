"""City-relative drift correction of a base forecaster, learned at in-fold pseudo-origins.

A city's recent level can drift against its neighbours (a station move, a siting change, a
local trend) while the weather they share cancels in the difference. The features at origin
``o`` are that difference, averaged over the last 1, 3, 5, 10 and 15 years:

* each city's values minus its own 30-year mean ending at ``o``;
* minus the same quantity averaged over its ``k`` nearest cities (``reference: neighbors``) or
  over all cities (``reference: national``, the control);
* centred across cities, with a missing feature counted as 0.

The base is refit at pseudo-origins ``p = c - pseudo_origins, ..., c - 1``. Its errors on the
years ``p + 1`` to ``min(p + 7, c)``, centred across cities for each year, are regressed on the
features with a Huber loss and no intercept, per metric and per lead group. At the cut-off the
fitted correction is centred across cities and added to the base forecast, so it moves cities
against each other and never changes the national level or trend.

Everything is computed from one fold's ``train``; features at ``o`` use only years up to ``o``.
The idea follows DragonDare's "learned city correction" (Placeholder_F4 model card, CC BY 4.0
dataset ``DragonDare/protostar-placeholders-f4``, revision ``6b69c82``); no code of that team
was downloaded or copied. It generalizes E2 of branch ``agent/hypothesis-trials``, which used
the national reference and one 15-year window.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import Field, model_validator

from proto_star.backtest import Forecaster
from proto_star.climate import annual_to_long
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters.residual_boost import base_at
from proto_star.forecasters.swap_metric import MemberEntry, cached_forecast
from proto_star.neighbors import (
    city_coordinates,
    departures,
    metric_panel,
    neighbor_weights,
    own_anomalies,
)

LOGGER = logging.getLogger(__name__)
Metric = Literal["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
KEY = ["city_id", "year", "metric"]


class CityDriftSpec(ForecasterSpec):
    """Base forecaster plus a robust linear correction on city-relative drift features."""

    base: MemberEntry = Field(default_factory=lambda: MemberEntry(kind="lead_blend"))
    metrics: list[Metric] = Field(min_length=1)
    reference: Literal["neighbors", "national"] = "neighbors"
    k: int = Field(default=10, ge=1)
    windows: list[int] = Field(default_factory=lambda: [1, 3, 5, 10, 15], min_length=1)
    lead_groups: list[tuple[int, int]] = Field(default_factory=lambda: [(1, 3), (4, 7)])
    pseudo_origins: int = Field(default=30, ge=5, le=60)
    epsilon: float = Field(default=1.35, gt=1.0)
    alpha: float = Field(default=1e-4, ge=0)
    shrink: float = Field(default=1.0, ge=0, le=1)
    min_fit_rows: int = Field(default=200, ge=10)

    @model_validator(mode="after")
    def _check(self) -> CityDriftSpec:
        if any(w < 1 or w > 30 for w in self.windows):
            raise ValueError("windows must lie between 1 and 30 years")
        covered = sorted(lead for lo, hi in self.lead_groups for lead in range(lo, hi + 1))
        if covered != list(range(1, 8)):
            raise ValueError("lead_groups must cover leads 1 to 7 exactly once")
        return self

    def describe(self) -> str:
        against = f"its {self.k} nearest cities" if self.reference == "neighbors" else "all cities"
        groups = ", ".join(f"{lo}-{hi}" for lo, hi in self.lead_groups)
        return (
            f"[{self.base.describe()}] plus a Huber-regression correction for "
            f"{', '.join(self.metrics)} on each city's drift against {against} over the last "
            f"{'/'.join(str(w) for w in self.windows)} years (lead groups {groups}; "
            f"{self.pseudo_origins} in-fold pseudo-origins; shrink {self.shrink})"
        )


def drift_features(
    panel: pd.DataFrame,
    origin: int,
    weights: pd.DataFrame,
    windows: list[int],
    reference: str,
) -> pd.DataFrame:
    """Per-city drift features at ``origin``, from the panel's years up to ``origin`` only."""
    upto = panel[[year for year in panel.columns if int(year) <= origin]]
    anomalies = own_anomalies(upto, origin, window=30, min_years=10)
    if reference == "neighbors":
        relative = departures(anomalies, weights)
    else:
        relative = anomalies.sub(anomalies.mean(axis=0), axis=1)
    features = {}
    for window in windows:
        years = [year for year in relative.columns if origin - window < int(year) <= origin]
        recent = relative[years].mean(axis=1)
        features[f"d{window}"] = (recent - recent.mean()).fillna(0.0)
    out = pd.DataFrame(features)
    out.index.name = "city_id"
    return out.reset_index()


def _fit_predict(
    fit_rows: pd.DataFrame, apply_rows: pd.DataFrame, names: list[str], spec: CityDriftSpec
) -> tuple[np.ndarray, np.ndarray]:
    """Huber coefficients from ``fit_rows`` and the correction they give on ``apply_rows``."""
    from sklearn.linear_model import HuberRegressor

    if len(fit_rows) < spec.min_fit_rows or len(apply_rows) == 0:
        return np.zeros(len(names)), np.zeros(len(apply_rows))
    scale = float(fit_rows["error"].std())
    if not np.isfinite(scale) or scale <= 0:
        return np.zeros(len(names)), np.zeros(len(apply_rows))
    model = HuberRegressor(
        epsilon=spec.epsilon, alpha=spec.alpha, fit_intercept=False, max_iter=500
    )
    model.fit(fit_rows[names].to_numpy() / scale, fit_rows["error"].to_numpy() / scale)
    return model.coef_, apply_rows[names].to_numpy() @ model.coef_


def build_city_drift(spec: CityDriftSpec) -> Forecaster:
    names = [f"d{window}" for window in spec.windows]

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        truth = history.rename(columns={"actual_value": "truth"})[[*KEY, "truth"]]
        weights = neighbor_weights(city_coordinates(train), k=spec.k)
        panels = {metric: metric_panel(train, metric, cutoff_year) for metric in spec.metrics}
        parts: dict[str, list[pd.DataFrame]] = {metric: [] for metric in spec.metrics}
        for origin in range(cutoff_year - spec.pseudo_origins, cutoff_year):
            base = base_at(spec.base, train, origin)
            base = base.loc[base["year"] <= cutoff_year].merge(truth, on=KEY, how="inner")
            for metric in spec.metrics:
                rows = base.loc[base["metric"] == metric]
                if rows.empty:
                    continue
                features = drift_features(
                    panels[metric], origin, weights, spec.windows, spec.reference
                )
                rows = rows.merge(features, on="city_id", how="left")
                rows[names] = rows[names].fillna(0.0)
                error = rows["truth"] - rows["predicted_value"]
                rows["error"] = error - error.groupby(rows["year"]).transform("mean")
                rows["lead"] = rows["year"] - origin
                parts[metric].append(rows)

        out = cached_forecast(spec.base, train, cutoff_year, forecast_years).reset_index(drop=True)
        for metric in spec.metrics:
            if not parts[metric]:
                continue
            data = pd.concat(parts[metric], ignore_index=True)
            selected = np.flatnonzero((out["metric"] == metric).to_numpy())
            here = out.iloc[selected][KEY].merge(
                drift_features(panels[metric], cutoff_year, weights, spec.windows, spec.reference),
                on="city_id",
                how="left",
            )
            here[names] = here[names].fillna(0.0)
            here["lead"] = here["year"] - cutoff_year
            correction = np.zeros(len(here))
            for low, high in spec.lead_groups:
                fit_rows = data.loc[data["lead"].between(low, high)]
                in_group = here["lead"].between(low, high).to_numpy()
                coef, values = _fit_predict(fit_rows, here.loc[in_group], names, spec)
                correction[in_group] = values
                LOGGER.info(
                    "city drift %s leads %d-%d at cutoff %s (%s): %d rows, coef %s",
                    metric,
                    low,
                    high,
                    cutoff_year,
                    spec.reference,
                    len(fit_rows),
                    ", ".join(
                        f"{name}={value:+.3f}" for name, value in zip(names, coef, strict=True)
                    ),
                )
            centred = pd.Series(correction)
            centred = centred - centred.groupby(here["year"].to_numpy()).transform("mean")
            values = out["predicted_value"].to_numpy(dtype=float).copy()
            values[selected] += spec.shrink * centred.to_numpy()
            out["predicted_value"] = values
        return out

    return forecast


register_kind("city_drift", CityDriftSpec, build_city_drift)
