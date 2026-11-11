"""Gradient-boosted correction of a base forecaster's errors, learned at in-fold pseudo-origins.

The base (``r4_winners`` or ``lead_split3`` in the trial configs) is refit at pseudo-origins
``p = c - pseudo_origins, ..., c - 1`` inside the fold. Its errors on the years ``p + 1`` to
``min(p + 7, c)`` become the targets of one ``HistGradientBoostingRegressor`` per metric, with
absolute-error loss because the score is an MAE. The features at origin ``o`` use only rows up
to ``o``:

* the lead and the base forecast's departure from the city's 30-year mean;
* the 30-year mean, its standard deviation and the 30-year least-squares slope;
* the last valid year's anomaly and the 3/5/10/15-year mean anomalies, each split into the
  cross-city mean at ``o`` (national part) and the rest (city part);
* latitude, longitude and years since the latest station switch.

At the cut-off the fitted correction is added to the base forecast. With ``target: city``, the
targets and the predicted corrections are centred across cities for each year, so the model
can only move cities relative to each other and cannot learn a common shift.

Everything is computed from one fold's ``train``. The truth for pseudo-origin targets stops at
the cut-off. Base forecasts at pseudo-origins are memoized per training-row fingerprint, because
neighbouring folds and rolling origins share most pseudo-origins.
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from typing import Literal

import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import annual_to_long
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters.swap_metric import MemberEntry, cached_forecast

LOGGER = logging.getLogger(__name__)
Metric = Literal["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
ALL_METRICS: tuple[Metric, ...] = ("annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd")
KEY = ["city_id", "year", "metric"]
HORIZON = 7
ANOMALY_YEARS = (3, 5, 10, 15)
_BASE_MEMO_SIZE = 512
_BASE_MEMO: OrderedDict[tuple[str, int, int], pd.DataFrame] = OrderedDict()


class ResidualBoostSpec(ForecasterSpec):
    """Base forecaster plus a boosted, in-fold correction of its errors."""

    base: MemberEntry = Field(default_factory=lambda: MemberEntry(kind="lead_blend"))
    metrics: list[Metric] = Field(
        default_factory=lambda: list(ALL_METRICS),
        min_length=1,
    )
    pseudo_origins: int = Field(default=30, ge=5, le=60)
    target: Literal["raw", "city"] = "raw"
    max_iter: int = Field(default=200, ge=10)
    learning_rate: float = Field(default=0.05, gt=0, le=1)
    max_depth: int = Field(default=3, ge=1)
    min_samples_leaf: int = Field(default=200, ge=1)
    l2_regularization: float = Field(default=1.0, ge=0)
    shrink: float = Field(default=1.0, ge=0, le=1)
    seed: int = 0

    def describe(self) -> str:
        part = "city-relative " if self.target == "city" else ""
        return (
            f"[{self.base.describe()}] plus a gradient-boosted {part}correction of its errors "
            f"for {', '.join(self.metrics)}, learned at {self.pseudo_origins} in-fold "
            f"pseudo-origins (depth {self.max_depth}, {self.max_iter} trees, lr "
            f"{self.learning_rate}, leaf {self.min_samples_leaf}, shrink {self.shrink})"
        )


def _fingerprint(train: pd.DataFrame) -> int:
    return int(pd.util.hash_pandas_object(train, index=False).sum())


def base_at(entry: MemberEntry, train: pd.DataFrame, origin: int) -> pd.DataFrame:
    """The base forecast made at ``origin`` from rows up to ``origin``, for the next 7 years."""
    upto = train.loc[train["Year"] <= origin]
    key = (json.dumps(entry.model_dump(), sort_keys=True, default=str), origin, _fingerprint(upto))
    if key in _BASE_MEMO:
        _BASE_MEMO.move_to_end(key)
        return _BASE_MEMO[key].copy()
    years = list(range(origin + 1, origin + 1 + HORIZON))
    result = cached_forecast(entry, upto, origin, years)[[*KEY, "predicted_value"]]
    _BASE_MEMO[key] = result
    while len(_BASE_MEMO) > _BASE_MEMO_SIZE:
        _BASE_MEMO.popitem(last=False)
    return result.copy()


def _slope(frame: pd.DataFrame) -> pd.Series:
    x = frame["year"] - frame.groupby(["city_id", "metric"])["year"].transform("mean")
    y = frame["actual_value"] - frame.groupby(["city_id", "metric"])["actual_value"].transform(
        "mean"
    )
    grouped = pd.DataFrame({"city_id": frame["city_id"], "metric": frame["metric"], "xy": x * y})
    grouped["xx"] = x * x
    sums = grouped.groupby(["city_id", "metric"])[["xy", "xx"]].sum()
    return sums["xy"] / sums["xx"].where(sums["xx"] > 0)


def origin_features(
    history: pd.DataFrame, origin: int, coords: pd.DataFrame, switches: pd.DataFrame
) -> pd.DataFrame:
    """Per city and metric features at ``origin``, from history rows up to ``origin`` only."""
    past = history.loc[history["year"] <= origin]
    window = past.loc[past["year"] > origin - 30]
    grouped = window.groupby(["city_id", "metric"])["actual_value"]
    out = pd.DataFrame({"m30": grouped.mean(), "sd30": grouped.std(), "n30": grouped.size()})
    out["slope30"] = _slope(window)
    last = past.sort_values("year").groupby(["city_id", "metric"]).tail(1)
    last = last.set_index(["city_id", "metric"])
    out["a1"] = last["actual_value"] - out["m30"]
    out["age1"] = origin - last["year"]
    for years in ANOMALY_YEARS:
        recent = past.loc[past["year"] > origin - years]
        out[f"a{years}"] = recent.groupby(["city_id", "metric"])["actual_value"].mean() - out["m30"]
    for name in ["a1", *(f"a{years}" for years in ANOMALY_YEARS)]:
        national = out.groupby(level="metric")[name].transform("mean")
        out[f"{name}_nat"] = national
        out[f"{name}_city"] = out[name] - national
    out = out.reset_index().merge(coords, on="city_id", how="left")
    latest = switches.loc[switches["Year"] <= origin].sort_values("Year").groupby("city_id").tail(1)
    latest = latest.set_index("city_id")
    since = latest["years_since_switch"] + (origin - latest["Year"])
    out["years_since_switch"] = out["city_id"].map(since).astype(float)
    return out


def _coords(train: pd.DataFrame) -> pd.DataFrame:
    coords = train.groupby(train["ID"].astype(str))[["Lat", "Lon"]].first().astype(float)
    coords.index.name = "city_id"
    return coords.reset_index()


def _switches(train: pd.DataFrame) -> pd.DataFrame:
    """Years since the latest station switch, per city and year (backward-only in the master)."""
    if "years_since_switch" not in train.columns:
        return pd.DataFrame(columns=["city_id", "Year", "years_since_switch"])
    frame = pd.DataFrame(
        {
            "city_id": train["ID"].astype(str),
            "Year": train["Year"].astype(int),
            "years_since_switch": pd.to_numeric(train["years_since_switch"], errors="coerce"),
        }
    )
    return frame.dropna(subset=["years_since_switch"])


def _design(base: pd.DataFrame, features: pd.DataFrame, origin: int) -> pd.DataFrame:
    rows = base.merge(features, on=["city_id", "metric"], how="left")
    rows["lead"] = rows["year"] - origin
    rows["base_dep"] = rows["predicted_value"] - rows["m30"]
    return rows


FEATURES = [
    "lead",
    "base_dep",
    "m30",
    "sd30",
    "n30",
    "slope30",
    "age1",
    *[
        f"{name}_{part}"
        for name in ["a1", *(f"a{years}" for years in ANOMALY_YEARS)]
        for part in ("nat", "city")
    ],
    "Lat",
    "Lon",
    "years_since_switch",
]


def _centre(values: pd.Series, frame: pd.DataFrame, by: list[str]) -> pd.Series:
    return values - values.groupby([frame[column] for column in by]).transform("mean")


def build_residual_boost(spec: ResidualBoostSpec) -> Forecaster:
    from sklearn.ensemble import HistGradientBoostingRegressor

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        coords, switches = _coords(train), _switches(train)
        truth = history.rename(columns={"actual_value": "truth"})[[*KEY, "truth"]]
        parts = []
        for origin in range(cutoff_year - spec.pseudo_origins, cutoff_year):
            base = base_at(spec.base, train, origin)
            base = base.loc[(base["year"] <= cutoff_year) & base["metric"].isin(spec.metrics)]
            rows = _design(base, origin_features(history, origin, coords, switches), origin)
            rows = rows.merge(truth, on=KEY, how="inner")
            rows["error"] = rows["truth"] - rows["predicted_value"]
            rows["origin"] = origin
            parts.append(rows)
        data = pd.concat(parts, ignore_index=True)
        if spec.target == "city":
            data["error"] = _centre(data["error"], data, ["metric", "origin", "year"])

        out = cached_forecast(spec.base, train, cutoff_year, forecast_years).reset_index(drop=True)
        features = [column for column in FEATURES if column in data.columns]
        here = _design(out, origin_features(history, cutoff_year, coords, switches), cutoff_year)
        for metric in spec.metrics:
            fit_rows = data.loc[data["metric"] == metric]
            usable = [column for column in features if fit_rows[column].notna().any()]
            model = HistGradientBoostingRegressor(
                loss="absolute_error",
                max_iter=spec.max_iter,
                learning_rate=spec.learning_rate,
                max_depth=spec.max_depth,
                min_samples_leaf=spec.min_samples_leaf,
                l2_regularization=spec.l2_regularization,
                early_stopping=False,
                random_state=spec.seed,
            )
            model.fit(fit_rows[usable], fit_rows["error"])
            selected = (here["metric"] == metric).to_numpy()
            correction = pd.Series(
                model.predict(here.loc[selected, usable]), index=here.index[selected]
            )
            if spec.target == "city":
                correction = _centre(correction, here.loc[selected], ["year"])
            LOGGER.info(
                "residual boost %s at cutoff %s: %d training rows, mean |correction| %.3f",
                metric,
                cutoff_year,
                len(fit_rows),
                float(correction.abs().mean()),
            )
            out.loc[selected, "predicted_value"] = (
                out.loc[selected, "predicted_value"].to_numpy()
                + spec.shrink * correction.to_numpy()
            )
        return out

    return forecast


register_kind("residual_boost", ResidualBoostSpec, build_residual_boost)
