"""Pooled (global) ridge forecaster from papers P14 (Montero-Manso & Hyndman 2021) and P09.

Ported unchanged in behaviour from the ``pooled_hybrid_p09_p14`` forecaster that lead_split3
used (Hugging Face dataset ``corbe19/protostar-climate-MKDir-lead``, revision ``0449d70``,
``code/src/proto_star/forecasters/pooled_p09_p14.py``), with only the ridge estimator that
lead_split3 used.

One ridge model per metric and per lead is fitted across all cities on per-series normalized
lags, trailing means, Lat/Lon and region. The multi-horizon strategy is *direct*: features at
origin ``t`` predict ``y[t + lead]``. Scalers and encoders live inside the sklearn pipeline, so
they are fitted on training examples only. Metrics not modelled, and series without a level at
the cut-off, take the ``current_best`` forecast.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST_METHODS, Forecaster, ensemble_forecaster
from proto_star.climate import METRICS
from proto_star.forecasters import _pooled_features as feats

NON_NEGATIVE = frozenset({"total_precip_in", "cdd"})
_KEY = ["city_id", "year", "metric"]


def _ridge_pipeline(*, numeric: list[str], categorical: list[str], alpha: float) -> Any:
    """Impute, scale and one-hot inside the pipeline, then ridge."""
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline, make_pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    # A missing normalized lag is set to 0, i.e. the series' trailing 30-year level.
    numeric_steps = make_pipeline(
        SimpleImputer(strategy="constant", fill_value=0.0, keep_empty_features=True),
        StandardScaler(),
    )
    encoder = OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)
    prep = ColumnTransformer([("num", numeric_steps, numeric), ("cat", encoder, categorical)])
    return Pipeline([("prep", prep), ("model", Ridge(alpha=alpha))])


def make_pooled_ridge(
    *,
    model_metrics: Sequence[str],
    alpha: float = 1.0,
    n_lags: int = 10,
    windows: Sequence[int] = (5, 10, 15),
    train_years: int | None = None,
) -> Forecaster:
    """Pooled ridge for ``model_metrics``; ``current_best`` for the rest.

    ``train_years`` keeps only examples whose target year is in the last ``train_years`` years
    of ``train`` (``None`` keeps all), as in lead_split3.
    """
    unknown = sorted(set(model_metrics) - set(METRICS))
    if unknown:
        raise ValueError(f"model_metrics has unknown metrics {unknown}; use {list(METRICS)}")
    window_list = [int(w) for w in windows]
    modelled = [m for m in METRICS if m in set(model_metrics)]
    fallback = ensemble_forecaster(CURRENT_BEST_METHODS)
    numeric = [
        *feats.lag_names(n_lags),
        *feats.mean_names(window_list),
        *feats.STATIC_NUMERIC,
    ]
    categorical = list(feats.STATIC_CATEGORICAL)
    columns = numeric + categorical

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = fallback(train, cutoff_year, forecast_years)
        leads = [int(year) - cutoff_year for year in forecast_years]
        panels = feats.wide_panels(train, cutoff_year)
        static = feats.city_static(train)
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
                origin_stride=1,
            )
            examples = feats.add_static(examples, static)
            now = features.loc[features["origin"] == cutoff_year].dropna(subset=["level", "scale"])
            now = feats.add_static(now, static)
            if examples.empty or now.empty:
                continue
            for lead in leads:
                rows = examples.loc[examples["lead"] == lead]
                if rows.empty:
                    continue
                pipeline = _ridge_pipeline(numeric=numeric, categorical=categorical, alpha=alpha)
                pipeline.fit(rows[columns], rows["target"].to_numpy())
                normalized = np.asarray(pipeline.predict(now[columns]), dtype=float)
                value = now["level"].to_numpy() + now["scale"].to_numpy() * normalized
                predictions.append(
                    pd.DataFrame(
                        {
                            "city_id": now["city_id"].to_numpy(),
                            "year": cutoff_year + lead,
                            "metric": metric,
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
