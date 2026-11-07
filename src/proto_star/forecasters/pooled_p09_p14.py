"""Pooled (global) median forecasters: papers P14 (Montero-Manso & Hyndman 2021) and P09.

One model is fitted across all cities for each metric (or across all metrics), on
per-series normalized lags, trailing means, Lat/Lon, region and the forecast lead.  The
objective is the pinball loss at quantile 0.5 (the median minimizes MAE, which the official
skill uses).  The multi-horizon strategy is *direct*: features at origin ``t`` predict
``y[t + lead]`` for leads 1-7, never by iterating one-step forecasts.  See
``papers/2021_montero-manso_global_pooled/README.md`` for the method card.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST_METHODS, Forecaster, ensemble_forecaster
from proto_star.climate import METRICS
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters.registry import register_forecaster

ESTIMATORS = ("quantile_linear", "ridge", "hgb_quantile")
NON_NEGATIVE = frozenset({"total_precip_in", "cdd"})
_KEY = ["city_id", "year", "metric"]


def _make_estimator(
    estimator: str,
    *,
    numeric: list[str],
    categorical: list[str],
    quantile: float,
    alpha: float,
    hgb: dict[str, Any],
    seed: int,
) -> Any:
    """An sklearn pipeline whose scalers and encoders are fitted on training examples only."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import QuantileRegressor, Ridge
    from sklearn.pipeline import Pipeline, make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    if estimator == "hgb_quantile":
        # NaN lags are handled natively by the trees, so no imputation here.
        prep = ColumnTransformer([("num", "passthrough", numeric), ("cat", encoder, categorical)])
        model: Any = HistGradientBoostingRegressor(
            loss="quantile", quantile=quantile, random_state=seed, early_stopping=False, **hgb
        )
    else:
        # A missing normalized lag is set to 0, i.e. the series' trailing 30-year level.
        numeric_steps = make_pipeline(
            SimpleImputer(strategy="constant", fill_value=0.0, keep_empty_features=True),
            StandardScaler(),
        )
        # Drop one level per category: the intercept already spans it (keeps the LP well posed).
        linear_encoder = OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)
        prep = ColumnTransformer(
            [("num", numeric_steps, numeric), ("cat", linear_encoder, categorical)]
        )
        if estimator == "quantile_linear":
            model = QuantileRegressor(
                # Interior point: about 6x faster than the default simplex on ~12k rows.
                quantile=quantile,
                alpha=alpha,
                solver="highs-ipm",
            )
        elif estimator == "ridge":
            model = Ridge(alpha=alpha)
        else:
            raise ValueError(f"unknown estimator {estimator!r}; use one of {list(ESTIMATORS)}")
    return Pipeline([("prep", prep), ("model", model)])


def make_pooled_median(
    *,
    estimator: str = "quantile_linear",
    quantile: float = 0.5,
    alpha: float = 0.0,
    n_lags: int = 10,
    windows: Sequence[int] = (5, 10, 15),
    per_lead: bool = True,
    pool_metrics: bool = False,
    use_static: bool = True,
    train_years: int | None = 60,
    origin_stride: int = 1,
    model_metrics: Sequence[str] = METRICS,
    hgb: dict[str, Any] | None = None,
    seed: int = 0,
) -> Forecaster:
    """Build the pooled median forecaster with hyperparameters from the trial config.

    ``per_lead`` fits one model per lead; otherwise lead is a feature of a single model.
    ``pool_metrics`` fits one model across all modelled metrics (with a metric one-hot).
    ``train_years`` keeps only examples whose target year is in the last ``train_years``
    years of ``train`` (``None`` keeps all).  Metrics not in ``model_metrics``, and series
    without a level at the cutoff, take the ``current_best`` forecast.
    """
    if estimator not in ESTIMATORS:
        raise ValueError(f"unknown estimator {estimator!r}; use one of {list(ESTIMATORS)}")
    if not 0.0 < quantile < 1.0:
        raise ValueError(f"quantile must be in (0, 1), got {quantile}")
    if n_lags < 1 or origin_stride < 1:
        raise ValueError("n_lags and origin_stride must be at least 1")
    unknown = sorted(set(model_metrics) - set(METRICS))
    if unknown:
        raise ValueError(f"model_metrics has unknown metrics {unknown}; use {list(METRICS)}")
    window_list = [int(w) for w in windows]
    modelled = [m for m in METRICS if m in set(model_metrics)]
    hgb_params = dict(hgb or {})
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        leads = [int(year) - cutoff_year for year in forecast_years]
        panels = feats.wide_panels(train, cutoff_year)
        static = feats.city_static(train)

        examples: dict[str, pd.DataFrame] = {}
        origins: dict[str, pd.DataFrame] = {}
        for metric in modelled:
            if metric not in panels:
                continue
            wide = panels[metric]
            features = feats.origin_features(wide, n_lags=n_lags, windows=window_list)
            train_rows = feats.training_examples(
                wide,
                features,
                cutoff_year=cutoff_year,
                leads=leads,
                train_years=train_years,
                origin_stride=origin_stride,
            )
            now = features.loc[features["origin"] == cutoff_year].dropna(subset=["level", "scale"])
            examples[metric] = feats.add_static(train_rows, static).assign(metric=metric)
            origins[metric] = feats.add_static(now, static).assign(metric=metric)

        numeric = [*feats.lag_names(n_lags), *feats.mean_names(window_list)]
        categorical: list[str] = []
        if use_static:
            numeric += list(feats.STATIC_NUMERIC)
            categorical += list(feats.STATIC_CATEGORICAL)
        if not per_lead:
            numeric.append("lead")
        if pool_metrics:
            categorical.append("metric")

        groups = [list(examples)] if pool_metrics else [[m] for m in examples]
        predictions: list[pd.DataFrame] = []
        for group in groups:
            fit_rows = pd.concat([examples[m] for m in group], ignore_index=True)
            now_rows = pd.concat([origins[m] for m in group], ignore_index=True)
            if fit_rows.empty or now_rows.empty:
                continue
            lead_sets = [[lead] for lead in leads] if per_lead else [leads]
            for lead_set in lead_sets:
                rows = fit_rows.loc[fit_rows["lead"].isin(lead_set)]
                if rows.empty:
                    continue
                pipeline = _make_estimator(
                    estimator,
                    numeric=numeric,
                    categorical=categorical,
                    quantile=quantile,
                    alpha=alpha,
                    hgb=hgb_params,
                    seed=seed,
                )
                columns = numeric + categorical
                pipeline.fit(rows[columns], rows["target"].to_numpy())
                for lead in lead_set:
                    target = now_rows.assign(lead=lead)
                    normalized = np.asarray(pipeline.predict(target[columns]), dtype=float)
                    value = target["level"].to_numpy() + target["scale"].to_numpy() * normalized
                    predictions.append(
                        pd.DataFrame(
                            {
                                "city_id": target["city_id"].to_numpy(),
                                "year": cutoff_year + lead,
                                "metric": target["metric"].to_numpy(),
                                "model_value": value,
                            }
                        )
                    )

        if not predictions:
            return base
        model = pd.concat(predictions, ignore_index=True)
        floor = model["metric"].isin(NON_NEGATIVE)
        model.loc[floor, "model_value"] = model.loc[floor, "model_value"].clip(lower=0.0)
        merged = base.merge(model, on=_KEY, how="left")
        use = merged["model_value"].notna() & np.isfinite(merged["model_value"])
        merged.loc[use, "predicted_value"] = merged.loc[use, "model_value"]
        return merged[[*_KEY, "predicted_value"]]

    return forecast


register_forecaster(
    "pooled_median_p09_p14",
    description=(
        "Global (pooled over cities) direct multi-horizon model on per-series normalized "
        "lags, trailing means, Lat/Lon, region (P14); loss set by estimator: pinball 0.5 "
        "(P09) or ridge"
    ),
)(make_pooled_median)


@register_forecaster(
    "pooled_hybrid_p09_p14",
    description=(
        "Pooled global model (P14; loss set by estimator, P09 median or ridge) for the "
        "metrics in model_metrics, current_best for the rest"
    ),
)
def make_pooled_hybrid(
    *, model_metrics: Sequence[str] = ("annual_avg_temp", "cdd"), **params: Any
) -> Forecaster:
    """Per-metric hybrid: same model and params, applied only to ``model_metrics``."""
    return make_pooled_median(model_metrics=model_metrics, **params)
