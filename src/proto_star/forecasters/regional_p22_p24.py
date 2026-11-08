"""Regional trends and pooling groups: papers P22 (Haug et al. 2020) and P24 (Hausfather 2013).

Two forecasters, both per-metric hybrids that keep ``current_best`` for the metrics they do
not model:

* ``regional_trend_p22`` (replication step 7).  Each city's linear trend over the last
  ``trend_years`` is shrunk toward the trend of its group (climate region, elevation band, ...)
  by empirical-Bayes partial pooling, a simple stand-in for P22's hierarchical Bayesian trend
  model.  The forecast is the recent level (mean of the last ``level_years`` valid years) plus
  ``damping`` x shrunk trend x years from the centre of that window.
* ``pooled_groups_p24`` (replication step 12).  The round-1 pooled ridge
  (``pooled_median_p09_p14``) with pooling groups: one model per group (``separate``), group
  one-hots (``additive``), or group x feature interactions (``interact``).  It imports the
  round-1 feature code instead of copying it.

Groups other than ``region`` are static city attributes from
``scripts/download_regional_p22_p24.py`` (GHCN station elevation, 2010 Census population,
NLCD 2016 land cover), read from ``data/external/regional_p22_p24/city_groups.csv``.  None of
them is weather data, and all are pre-2019 vintages.  Card:
``papers/2020_haug_regional_trends/README.md``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST_METHODS, Forecaster, ensemble_forecaster
from proto_star.climate import METRICS, annual_to_long
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters.pooled_p09_p14 import NON_NEGATIVE, _make_estimator
from proto_star.forecasters.registry import register_forecaster
from proto_star.paths import EXTERNAL_DIR

GROUPS_PATH = EXTERNAL_DIR / "regional_p22_p24" / "city_groups.csv"
GROUPINGS = ("national", "region", "elevation", "population", "land_cover")
SHRINK_MODES = ("eb", "none", "group")
POOL_MODES = ("additive", "interact", "separate")
DEFAULT_BANDS: dict[str, list[float]] = {
    "elevation": [130.0, 310.0],  # metres (rough terciles of the 210 stations)
    "population": [50_000.0, 175_000.0],  # 2010 Census, largest place within 20 km (terciles)
}
MIN_SEPARATE_ROWS = 500  # a group with fewer training rows uses the all-cities model
_KEY = ["city_id", "year", "metric"]


# --- group assignment -------------------------------------------------------------------


def load_city_groups(path: Path | str | None = None) -> pd.DataFrame:
    """Static city attributes indexed by ``city_id`` (written by the download script)."""
    source = Path(path) if path is not None else GROUPS_PATH
    if not source.exists():
        raise FileNotFoundError(
            f"{source} not found; run `uv run python scripts/download_regional_p22_p24.py` "
            "or use group_by='region' / 'national', which need no external data"
        )
    table = pd.read_csv(source, dtype={"city_id": str})
    required = {"city_id", "elevation_m", "pop_2010", "land_cover"}
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"{source} is missing columns {missing}")
    return table.set_index("city_id")


def _band(values: pd.Series, edges: Sequence[float], name: str) -> pd.Series:
    """Label each value by the band it falls in: ``<name>_0`` below the first edge, etc."""
    codes = np.searchsorted(np.asarray(sorted(edges), dtype=float), values.to_numpy(), side="right")
    labels = pd.Series([f"{name}_{int(c)}" for c in codes], index=values.index)
    return labels.where(values.notna(), f"{name}_unknown")


def assign_groups(
    static: pd.DataFrame,
    groupings: Sequence[str],
    *,
    bands: Mapping[str, Sequence[float]] | None = None,
    groups_path: Path | str | None = None,
) -> pd.DataFrame:
    """One string column per grouping, indexed like ``static`` (``city_static`` output).

    ``region`` comes from the fold's own rows.  ``elevation`` and ``population`` are banded at
    the edges in ``bands``; ``land_cover`` is the NLCD class group.  Cities missing from the
    attribute table get an ``*_unknown`` group rather than being dropped.
    """
    unknown = sorted(set(groupings) - set(GROUPINGS))
    if unknown:
        raise ValueError(f"unknown groupings {unknown}; use {list(GROUPINGS)}")
    edges = {**DEFAULT_BANDS, **{k: list(v) for k, v in (bands or {}).items()}}
    out = pd.DataFrame(index=static.index)
    external = None
    if set(groupings) & {"elevation", "population", "land_cover"}:
        external = load_city_groups(groups_path).reindex(static.index)
    for grouping in groupings:
        if grouping == "national":
            out[grouping] = "all"
        elif grouping == "region":
            out[grouping] = static["region"].astype(str)
        else:
            assert external is not None
            if grouping == "elevation":
                out[grouping] = _band(external["elevation_m"], edges["elevation"], "elev")
            elif grouping == "population":
                out[grouping] = _band(external["pop_2010"], edges["population"], "pop")
            else:
                out[grouping] = external["land_cover"].fillna("lc_unknown").astype(str)
    return out


# --- P22: empirical-Bayes shrunk trends -------------------------------------------------


def city_trends(history: pd.DataFrame, *, cutoff_year: int, trend_years: int) -> pd.DataFrame:
    """OLS slope and its sampling variance per city over the last ``trend_years`` years.

    ``history`` is one metric's rows of ``annual_to_long``.  Cities with fewer than
    ``max(8, trend_years // 2)`` valid years in the window get NaN.
    """
    window = history.loc[history["year"] > cutoff_year - trend_years]
    min_years = max(8, trend_years // 2)
    rows = []
    for city, part in window.groupby("city_id"):
        years = part["year"].to_numpy(dtype=float)
        values = part["actual_value"].to_numpy(dtype=float)
        slope = variance = np.nan
        if len(years) >= min_years:
            centred = years - years.mean()
            sxx = float((centred**2).sum())
            slope = float((centred * (values - values.mean())).sum() / sxx)
            residual = values - values.mean() - slope * centred
            variance = float((residual**2).sum() / (len(years) - 2) / sxx)
        rows.append({"city_id": str(city), "slope": slope, "slope_var": variance})
    return pd.DataFrame(rows, columns=["city_id", "slope", "slope_var"]).set_index("city_id")


def shrink_trends(trends: pd.DataFrame, groups: pd.Series, *, mode: str) -> pd.Series:
    """Partially pooled slope per city (method of moments, DerSimonian-Laird style).

    Within each group: ``tau2 = max(0, var(slope) - mean(slope_var))`` is the spread of true
    city trends, the group trend is the precision-weighted mean with weights
    ``1 / (slope_var + tau2)``, and a city keeps the share ``tau2 / (tau2 + slope_var)`` of its
    own slope.  ``mode='group'`` uses the group trend for every city, ``'none'`` the raw slope.
    Cities without a slope take their group's trend (0 if the group has none).
    """
    if mode not in SHRINK_MODES:
        raise ValueError(f"unknown shrink mode {mode!r}; use one of {list(SHRINK_MODES)}")
    frame = trends.join(groups.rename("group"), how="left")
    frame["group"] = frame["group"].fillna("unknown")
    result = pd.Series(np.nan, index=frame.index, dtype=float)
    for _, part in frame.groupby("group"):
        ok = part.dropna(subset=["slope", "slope_var"])
        if ok.empty:
            result.loc[part.index] = 0.0
            continue
        tau2 = (
            max(0.0, float(ok["slope"].var(ddof=1)) - float(ok["slope_var"].mean()))
            if len(ok) > 1
            else 0.0
        )
        weights = 1.0 / (ok["slope_var"] + tau2).clip(lower=1e-12)
        group_trend = float((weights * ok["slope"]).sum() / weights.sum())
        if mode == "group":
            own_share = pd.Series(0.0, index=ok.index)
        elif mode == "none":
            own_share = pd.Series(1.0, index=ok.index)
        else:
            own_share = tau2 / (tau2 + ok["slope_var"]).clip(lower=1e-12)
        result.loc[part.index] = group_trend
        result.loc[ok.index] = own_share * ok["slope"] + (1.0 - own_share) * group_trend
    return result


def _check_metrics(model_metrics: Sequence[str]) -> list[str]:
    unknown = sorted(set(model_metrics) - set(METRICS))
    if unknown:
        raise ValueError(f"model_metrics has unknown metrics {unknown}; use {list(METRICS)}")
    return [m for m in METRICS if m in set(model_metrics)]


def _overlay(base: pd.DataFrame, model: pd.DataFrame) -> pd.DataFrame:
    """Replace ``base`` predictions with finite ``model_value`` rows (non-negative floors kept)."""
    floor = model["metric"].isin(NON_NEGATIVE)
    model.loc[floor, "model_value"] = model.loc[floor, "model_value"].clip(lower=0.0)
    merged = base.merge(model, on=_KEY, how="left")
    use = merged["model_value"].notna() & np.isfinite(merged["model_value"])
    merged.loc[use, "predicted_value"] = merged.loc[use, "model_value"]
    return merged[[*_KEY, "predicted_value"]]


@register_forecaster(
    "regional_trend_p22",
    description=(
        "Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes "
        "partial pooling (P22), damped; current_best for metrics not modelled"
    ),
)
def make_regional_trend(
    *,
    model_metrics: Sequence[str] = ("annual_avg_temp", "cdd"),
    group_by: str = "region",
    shrink: str = "eb",
    trend_years: int = 30,
    level_years: int = 10,
    damping: float = 1.0,
    extrapolate_lead: bool = True,
    bands: Mapping[str, Sequence[float]] | None = None,
    groups_path: str | None = None,
) -> Forecaster:
    """Build the P22 forecaster.

    The level is the mean of the last ``level_years`` valid years, centred on their mean year
    ``c``.  The forecast for year ``Y`` is ``level + damping * trend * (Y - c)``; with
    ``extrapolate_lead=False`` it is held at ``Y = cutoff`` (a level-update-only control).
    """
    modelled = _check_metrics(model_metrics)
    if group_by not in GROUPINGS:
        raise ValueError(f"unknown group_by {group_by!r}; use one of {list(GROUPINGS)}")
    if shrink not in SHRINK_MODES:
        raise ValueError(f"unknown shrink mode {shrink!r}; use one of {list(SHRINK_MODES)}")
    if trend_years < 10 or level_years < 1:
        raise ValueError("trend_years must be >= 10 and level_years >= 1")
    if not 0.0 <= damping <= 1.0:
        raise ValueError(f"damping must be in [0, 1], got {damping}")
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        history = annual_to_long(train, cutoff_year=cutoff_year)
        groups = assign_groups(
            feats.city_static(train), [group_by], bands=bands, groups_path=groups_path
        )[group_by]
        frames = []
        for metric in modelled:
            rows = history.loc[history["metric"] == metric]
            if rows.empty:
                continue
            recent = rows.sort_values("year").groupby("city_id").tail(level_years)
            level = recent.groupby("city_id").agg(
                level=("actual_value", "mean"), centre=("year", "mean")
            )
            trends = city_trends(rows, cutoff_year=cutoff_year, trend_years=trend_years)
            trend = shrink_trends(trends, groups, mode=shrink).reindex(level.index).fillna(0.0)
            for year in forecast_years:
                target = float(year) if extrapolate_lead else float(cutoff_year)
                value = level["level"] + damping * trend * (target - level["centre"])
                frames.append(
                    pd.DataFrame(
                        {
                            "city_id": level.index.astype(str),
                            "year": int(year),
                            "metric": metric,
                            "model_value": value.to_numpy(),
                        }
                    )
                )
        if not frames:
            return base
        return _overlay(base, pd.concat(frames, ignore_index=True))

    return forecast


# --- P24: pooled ridge with pooling groups ----------------------------------------------


def _interactions(
    frame: pd.DataFrame, numeric: list[str], group_columns: list[str]
) -> pd.DataFrame:
    """Numeric features (NaN as 0, the trailing level) times one indicator per group level."""
    columns: dict[str, np.ndarray] = {}
    values = frame[numeric].fillna(0.0)
    for column in group_columns:
        for level in sorted(frame[column].astype(str).unique()):
            indicator = (frame[column].astype(str) == level).to_numpy(dtype=float)
            for name in numeric:
                columns[f"{name}__{column}_{level}"] = values[name].to_numpy() * indicator
    return pd.DataFrame(columns, index=frame.index)


@register_forecaster(
    "pooled_groups_p24",
    description=(
        "Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, "
        "population or land cover as separate models, one-hots or interactions"
    ),
)
def make_pooled_groups(
    *,
    group_by: Sequence[str] = ("region",),
    mode: str = "interact",
    model_metrics: Sequence[str] = ("cdd",),
    estimator: str = "ridge",
    alpha: float = 1.0,
    n_lags: int = 10,
    windows: Sequence[int] = (5, 10, 15),
    train_years: int | None = None,
    origin_stride: int = 1,
    bands: Mapping[str, Sequence[float]] | None = None,
    groups_path: str | None = None,
    seed: int = 0,
) -> Forecaster:
    """Build the P24 forecaster: one model per lead, features as in ``pooled_median_p09_p14``.

    Base features are the normalized lags and trailing means, Lat/Lon and region.  ``mode``:
    ``additive`` adds the group one-hots; ``interact`` also adds every numeric feature times
    every group indicator (a group-specific slope for each feature, shrunk by the ridge
    penalty); ``separate`` fits one model per level of the first grouping.
    """
    modelled = _check_metrics(model_metrics)
    if mode not in POOL_MODES:
        raise ValueError(f"unknown mode {mode!r}; use one of {list(POOL_MODES)}")
    groupings = [str(g) for g in group_by]
    if not groupings:
        raise ValueError("group_by needs at least one grouping")
    unknown = sorted(set(groupings) - set(GROUPINGS))
    if unknown:
        raise ValueError(f"unknown groupings {unknown}; use {list(GROUPINGS)}")
    if estimator not in ("ridge", "quantile_linear"):
        raise ValueError(f"unknown estimator {estimator!r}; use 'ridge' or 'quantile_linear'")
    window_list = [int(w) for w in windows]
    group_columns = [f"group_{g}" for g in groupings]
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        leads = [int(year) - cutoff_year for year in forecast_years]
        panels = feats.wide_panels(train, cutoff_year)
        static = feats.city_static(train)
        assigned = assign_groups(static, groupings, bands=bands, groups_path=groups_path)
        static = static.join(assigned.add_prefix("group_"))

        base_numeric = [
            *feats.lag_names(n_lags),
            *feats.mean_names(window_list),
            *feats.STATIC_NUMERIC,
        ]
        categorical = list(feats.STATIC_CATEGORICAL)
        if mode != "separate":
            categorical += [c for c in group_columns if c != "group_region"]

        predictions: list[pd.DataFrame] = []
        for metric in modelled:
            if metric not in panels:
                continue
            wide = panels[metric]
            features = feats.origin_features(wide, n_lags=n_lags, windows=window_list)
            examples = feats.training_examples(
                wide,
                features,
                cutoff_year=cutoff_year,
                leads=leads,
                train_years=train_years,
                origin_stride=origin_stride,
            )
            now = features.loc[features["origin"] == cutoff_year].dropna(subset=["level", "scale"])
            examples = feats.add_static(examples, static)
            now = feats.add_static(now, static)
            if examples.empty or now.empty:
                continue
            numeric = list(base_numeric)
            if mode == "interact":
                extra_fit = _interactions(examples, base_numeric, group_columns)
                extra_now = _interactions(now, base_numeric, group_columns)
                extra_now = extra_now.reindex(columns=extra_fit.columns, fill_value=0.0)
                examples = pd.concat([examples, extra_fit], axis=1)
                now = pd.concat([now, extra_now], axis=1)
                numeric += list(extra_fit.columns)
            columns = numeric + categorical

            if mode == "separate":
                key = group_columns[0]
                parts = [
                    (examples.loc[examples[key] == level], now.loc[now[key] == level])
                    for level in sorted(now[key].unique())
                ]
            else:
                parts = [(examples, now)]
            for fit_rows, now_rows in parts:
                if mode == "separate" and len(fit_rows) < MIN_SEPARATE_ROWS * len(leads):
                    fit_rows = examples  # too small a group: use the all-cities model
                for lead in leads:
                    rows = fit_rows.loc[fit_rows["lead"] == lead]
                    if rows.empty or now_rows.empty:
                        continue
                    pipeline = _make_estimator(
                        estimator,
                        numeric=numeric,
                        categorical=categorical,
                        quantile=0.5,
                        alpha=alpha,
                        hgb={},
                        seed=seed,
                    )
                    pipeline.fit(rows[columns], rows["target"].to_numpy())
                    normalized = np.asarray(pipeline.predict(now_rows[columns]), dtype=float)
                    value = now_rows["level"].to_numpy() + now_rows["scale"].to_numpy() * normalized
                    predictions.append(
                        pd.DataFrame(
                            {
                                "city_id": now_rows["city_id"].to_numpy(),
                                "year": cutoff_year + lead,
                                "metric": metric,
                                "model_value": value,
                            }
                        )
                    )
        if not predictions:
            return base
        return _overlay(base, pd.concat(predictions, ignore_index=True))

    return forecast
