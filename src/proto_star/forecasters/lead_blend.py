"""lead_split3 (the current submission) and h2_mean_cdd as one plug-in kind, ``lead_blend``.

Ported from the team's submitted package (Hugging Face dataset
``corbe19/protostar-climate-MKDir-lead``, revision ``0449d70``: ``code/trial.yaml``,
``code/evidence/lead_blend.md``), where it was a ``lead_blends`` block over two members:

* ``trend``: the pooled-trend champion (``proto_star.trend``; levels from the last 10 and 15
  valid years, non-negative pooled 40-year slope, CDD trend = city CDD per degree x pooled
  temperature slope; 30-year mean for precipitation and hottest day).
* ``ridge``: the pooled ridge of papers P09/P14 (``_pooled_ridge``) for temperature and CDD.

Per metric and forecast lead (lead 1 = first year after the cut-off):

* temperature = ``w[lead] x trend + (1 - w[lead]) x ridge``, with ``temp_trend_weights`` by
  lead; the last value holds for every later lead. lead_split3 is ``[0.5, 0.5, 0.5, 1.0]``;
  ``[1.0]`` gives h2_mean_cdd.
* CDD = ``cdd_trend_weight x trend + (1 - cdd_trend_weight) x ridge`` (0.5 in both).
* precipitation and hottest day = ``trend`` (the 30-year mean).
"""

from __future__ import annotations

import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster, pooled_trend_forecaster
from proto_star.climate import ClimateDataError
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._pooled_ridge import make_pooled_ridge
from proto_star.trend import CDD, TEMPERATURE, PooledTrendSpec

_KEY = ["city_id", "year", "metric"]


class LeadBlendSpec(ForecasterSpec):
    """Settings of a lead-dependent trend/ridge blend. Defaults are lead_split3."""

    level_years: list[int] = Field(default=[10, 15], min_length=1)
    trend_window: int = Field(default=40, ge=10)
    ridge_alpha: float = Field(default=1.0, gt=0.0)
    ridge_train_years: int | None = Field(default=None, ge=10)
    temp_trend_weights: list[float] = Field(default=[0.5, 0.5, 0.5, 1.0], min_length=1)
    cdd_trend_weight: float = Field(default=0.5, ge=0.0, le=1.0)

    def describe(self) -> str:
        temp = "/".join(f"{w:g}" for w in self.temp_trend_weights)
        return (
            f"Pooled trend (levels {self.level_years}, {self.trend_window}-year slope, CDD "
            f"sensitivity) blended with the pooled P09/P14 ridge (alpha {self.ridge_alpha:g}): "
            f"temperature trend weight by lead {temp} (last holds), CDD trend weight "
            f"{self.cdd_trend_weight:g}; 30-year mean for precipitation and hottest day"
        )


def lead_weight(weights: list[float], lead: int) -> float:
    """Weight at a forecast lead (1 = first year after the cut-off); the last value holds."""
    if lead < 1:
        raise ValueError(f"lead must be at least 1, got {lead}")
    return float(weights[min(lead, len(weights)) - 1])


def build_lead_blend(spec: LeadBlendSpec) -> Forecaster:
    for weight in spec.temp_trend_weights:
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"temp_trend_weights must lie in [0, 1], got {weight}")
    trend = pooled_trend_forecaster(
        PooledTrendSpec(
            level_years=spec.level_years, trend_window=spec.trend_window, cdd_sensitivity=True
        )
    )
    ridge = make_pooled_ridge(
        model_metrics=[TEMPERATURE, CDD],
        alpha=spec.ridge_alpha,
        train_years=spec.ridge_train_years,
    )

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = trend(train, cutoff_year, forecast_years)
        model = ridge(train, cutoff_year, forecast_years)
        merged = base.merge(model.rename(columns={"predicted_value": "ridge"}), on=_KEY, how="left")
        lead = merged["year"] - cutoff_year
        weight = pd.Series(1.0, index=merged.index)
        is_temp = merged["metric"] == TEMPERATURE
        weight[is_temp] = lead[is_temp].map(lambda k: lead_weight(spec.temp_trend_weights, k))
        weight[merged["metric"] == CDD] = spec.cdd_trend_weight
        needs_ridge = weight < 1.0
        missing = needs_ridge & merged["ridge"].isna()
        if missing.any():
            example = merged.loc[missing, _KEY].iloc[0].to_dict()
            raise ClimateDataError(
                f"lead_blend: {int(missing.sum())} rows lack a ridge forecast, e.g. {example}"
            )
        blended = weight * merged["predicted_value"] + (1.0 - weight) * merged["ridge"]
        merged["predicted_value"] = merged["predicted_value"].where(~needs_ridge, blended)
        return merged[[*_KEY, "predicted_value"]]

    return forecast


register_kind("lead_blend", LeadBlendSpec, build_lead_blend)
