"""Direct multi-horizon pooled median forecaster (hypothesis U1 in ``hypotheses.md``).

For each modeled metric, one model is pooled across all cities and lead years.  Its training rows
come from earlier forecast origins inside the fold: origin ``o`` contributes lead ``h`` only when
``o + h <= cutoff``, so every target is a year the fold may see.  The target is the value ``h``
years after the origin minus the city's mean over the 30 calendar years ending at the origin,
which is the reference the official score uses.  Every feature looks backward from its origin.

Models are fitted with an absolute-error (median) objective, because the score is MAE-based.
Metrics not listed in :class:`DirectSpec` get no rows here; the caller fills them.
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from proto_star.climate import BASELINE_WINDOW_YEARS, METRICS

TEMPERATURE = "annual_avg_temp"
CDD = "cdd"
FEATURES = (
    "lead",
    "d5",
    "d10",
    "d15",
    "last",
    "sd30",
    "n30",
    "slope",
    "trend_step",
    "lat",
    "lon",
)
_X_OFFSET = 1900.0  # keeps the year sums in the slope fit well conditioned


class DirectSpec(BaseModel):
    """Settings of one direct model, set under ``params`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metrics: list[str] = Field(default_factory=lambda: [TEMPERATURE, CDD])
    model: Literal["linear", "gbm"] = "gbm"
    features: list[str] = Field(default_factory=lambda: list(FEATURES))
    first_origin: int = 1920  # earliest training origin
    horizon: int = Field(default=7, ge=1)
    trend_window: int = Field(default=40, ge=10)  # calendar years for the pooled slope
    min_city_years: int = Field(default=10, ge=3)  # valid years a city needs to enter a slope
    seed: int = 0
    gbm_max_iter: int = Field(default=300, ge=1)
    gbm_learning_rate: float = Field(default=0.05, gt=0)
    gbm_max_leaf_nodes: int = Field(default=15, ge=2)
    gbm_min_samples_leaf: int = Field(default=200, ge=1)
    linear_alpha: float = Field(default=0.0, ge=0)
    # The exact LP behind QuantileRegressor grows fast with rows; fit it on a seeded subsample.
    linear_max_rows: int = Field(default=20_000, ge=100)

    @model_validator(mode="after")
    def _check_names(self) -> DirectSpec:
        unknown_metrics = sorted(set(self.metrics) - set(METRICS))
        unknown_features = sorted(set(self.features) - set(FEATURES))
        if not self.metrics or unknown_metrics:
            raise ValueError(f"metrics must be a non-empty subset of {list(METRICS)}")
        if not self.features or unknown_features:
            raise ValueError(f"unknown features {unknown_features}; choose from {list(FEATURES)}")
        return self


def _cumulative(values: np.ndarray) -> np.ndarray:
    """Column-wise cumulative sum with a leading zero row, for O(1) window sums."""
    out = np.zeros((values.shape[0] + 1, values.shape[1]))
    np.cumsum(values, axis=0, out=out[1:])
    return out


def _window(cumulative: np.ndarray, end: int, length: int) -> np.ndarray:
    """Sum over rows ``end - length + 1 .. end`` (inclusive) of the array behind ``cumulative``."""
    return cumulative[end + 1] - cumulative[max(0, end - length + 1)]


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denominator > 0, numerator / denominator, np.nan)


class _Panel:
    """One metric as a year x city matrix, with the window sums every feature needs."""

    def __init__(self, values: np.ndarray, years: np.ndarray) -> None:
        self.grid = values
        observed = ~np.isnan(values)
        filled = np.where(observed, values, 0.0)
        x = np.where(observed, (years - _X_OFFSET)[:, None], 0.0)
        self.n = _cumulative(observed.astype(float))
        self.sum = _cumulative(filled)
        self.sum2 = _cumulative(filled**2)
        self.sx = _cumulative(x)
        self.sx2 = _cumulative(x**2)
        self.sxy = _cumulative(x * filled)

    def mean(self, end: int, length: int) -> np.ndarray:
        return _ratio(_window(self.sum, end, length), _window(self.n, end, length))

    def pooled_slope(self, end: int, length: int, min_years: int) -> float:
        """Within-city least-squares slope per year, pooled over cities (not floored)."""
        n = _window(self.n, end, length)
        sx, sy = _window(self.sx, end, length), _window(self.sum, end, length)
        sxx = _window(self.sx2, end, length) - _ratio(sx**2, n)
        sxy = _window(self.sxy, end, length) - _ratio(sx * sy, n)
        keep = (n >= min_years) & np.isfinite(sxx) & np.isfinite(sxy)
        spread = float(sxx[keep].sum())
        return float(sxy[keep].sum()) / spread if spread > 0 else 0.0


def _cdd_per_degree(
    temp: np.ndarray, cdd: np.ndarray, end: int, length: int, min_years: int
) -> np.ndarray:
    """Each city's CDD gained per degree of annual temperature over the window, clipped at 0."""
    lo = max(0, end - length + 1)
    t, c = temp[lo : end + 1], cdd[lo : end + 1]
    joint = ~np.isnan(t) & ~np.isnan(c)
    n = joint.sum(axis=0)
    t0, c0 = np.where(joint, t, 0.0), np.where(joint, c, 0.0)
    st, sc = t0.sum(axis=0), c0.sum(axis=0)
    stt = (t0**2).sum(axis=0) - _ratio(st**2, n)
    stc = (t0 * c0).sum(axis=0) - _ratio(st * sc, n)
    sensitivity = np.where((n >= min_years) & (stt > 0), _ratio(stc, stt), np.nan)
    return np.clip(sensitivity, 0.0, None)


def _features(
    panel: _Panel,
    end: int,
    lead: int,
    slope: np.ndarray,
    years: np.ndarray,
    coords: np.ndarray,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Features of every city at origin ``years[end]`` for one lead, and the 30-year mean."""
    n30 = _window(panel.n, end, BASELINE_WINDOW_YEARS)
    m30 = panel.mean(end, BASELINE_WINDOW_YEARS)
    variance = _ratio(_window(panel.sum2, end, BASELINE_WINDOW_YEARS), n30) - m30**2
    n10 = _window(panel.n, end, 10)
    center10 = _ratio(_window(panel.sx, end, 10), n10) + _X_OFFSET
    origin = float(years[end])
    feats = {
        "lead": np.full(m30.shape, float(lead)),
        "d5": panel.mean(end, 5) - m30,
        "d10": panel.mean(end, 10) - m30,
        "d15": panel.mean(end, 15) - m30,
        "last": panel.grid[end] - m30,
        "sd30": np.sqrt(np.clip(variance, 0.0, None)),
        "n30": n30,
        "slope": slope,
        "trend_step": np.clip(slope, 0.0, None) * (origin + lead - center10),
        "lat": coords[:, 0],
        "lon": coords[:, 1],
    }
    return feats, m30


def _model(spec: DirectSpec) -> Any:
    if spec.model == "linear":
        return make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            QuantileRegressor(quantile=0.5, alpha=spec.linear_alpha, solver="highs"),
        )
    return HistGradientBoostingRegressor(
        loss="absolute_error",
        max_iter=spec.gbm_max_iter,
        learning_rate=spec.gbm_learning_rate,
        max_leaf_nodes=spec.gbm_max_leaf_nodes,
        min_samples_leaf=spec.gbm_min_samples_leaf,
        early_stopping=False,
        random_state=spec.seed,
    )


def direct_forecast(
    train: pd.DataFrame,
    history: pd.DataFrame,
    cutoff_year: int,
    forecast_years: list[int],
    spec: DirectSpec,
) -> pd.DataFrame:
    """Forecast ``spec.metrics`` for every city with a 30-year mean at the cut-off.

    ``history`` is the quality-screened long table of ``train`` (``annual_to_long``);
    ``train`` supplies static coordinates only.  Cities with no valid value in the last 30
    calendar years get no row, so the caller can fall back to the official baseline.
    """
    leads = [year - cutoff_year for year in forecast_years]
    if min(leads) < 1 or max(leads) > spec.horizon:
        raise ValueError(f"forecast years must be 1..{spec.horizon} years after the cut-off")
    history = history.loc[history["year"] <= cutoff_year]
    cities = np.array(sorted(history["city_id"].unique()))
    years = np.arange(int(history["year"].min()), cutoff_year + 1)
    static = train.assign(city_id=train["ID"].astype(str)).groupby("city_id")[["Lat", "Lon"]]
    coords = static.first().reindex(cities).to_numpy(dtype=float)

    def wide(metric: str) -> np.ndarray:
        rows = history.loc[history["metric"] == metric]
        table = rows.pivot_table(index="year", columns="city_id", values="actual_value")
        return table.reindex(index=years, columns=cities).to_numpy(dtype=float)

    panels = {metric: _Panel(wide(metric), years) for metric in set(spec.metrics) | {TEMPERATURE}}
    cut = len(years) - 1
    outputs = []
    for metric in spec.metrics:
        panel = panels[metric]

        def city_slopes(end: int, metric: str = metric, panel: _Panel = panel) -> np.ndarray:
            own = panel.pooled_slope(end, spec.trend_window, spec.min_city_years)
            if metric != CDD:
                return np.full(len(cities), own)
            warming = panels[TEMPERATURE].pooled_slope(end, spec.trend_window, spec.min_city_years)
            sensitivity = _cdd_per_degree(
                panels[TEMPERATURE].grid, panel.grid, end, spec.trend_window, spec.min_city_years
            )
            return np.where(np.isnan(sensitivity), own, sensitivity * warming)

        x_rows, y_rows = [], []
        first = max(int(np.searchsorted(years, spec.first_origin)), BASELINE_WINDOW_YEARS - 1)
        for end in range(first, cut):
            slope = city_slopes(end)
            for lead in range(1, min(spec.horizon, cut - end) + 1):
                feats, m30 = _features(panel, end, lead, slope, years, coords)
                target = panel.grid[end + lead] - m30
                keep = np.isfinite(target) & np.isfinite(m30)
                x_rows.append(np.column_stack([feats[f][keep] for f in spec.features]))
                y_rows.append(target[keep])
        if not x_rows:
            continue
        x_fit, y_fit = np.vstack(x_rows), np.concatenate(y_rows)
        if spec.model == "linear" and len(y_fit) > spec.linear_max_rows:
            pick = np.random.default_rng(spec.seed).choice(
                len(y_fit), spec.linear_max_rows, replace=False
            )
            x_fit, y_fit = x_fit[pick], y_fit[pick]
        model = _model(spec)
        model.fit(x_fit, y_fit)

        slope = city_slopes(cut)
        for year, lead in zip(forecast_years, leads, strict=True):
            feats, m30 = _features(panel, cut, lead, slope, years, coords)
            keep = np.isfinite(m30)
            x = np.column_stack([feats[f][keep] for f in spec.features])
            outputs.append(
                pd.DataFrame(
                    {
                        "city_id": cities[keep],
                        "year": int(year),
                        "metric": metric,
                        "predicted_value": m30[keep] + model.predict(x),
                    }
                )
            )
    if not outputs:
        return pd.DataFrame(columns=["city_id", "year", "metric", "predicted_value"])
    return pd.concat(outputs, ignore_index=True)
