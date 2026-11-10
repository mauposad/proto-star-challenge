"""Replace one metric of a base forecaster by a (weighted) mean of component forecasters.

The final round tests each component for one metric only. ``swap_metric`` keeps the base
forecast (lead_split3 by default) for every other metric unchanged, so metric isolation holds
by construction, and :func:`changed_metrics` lets a test confirm it. Example::

    models:
      T1:
        kind: swap_metric
        params:
          metric: annual_avg_temp
          base: {kind: lead_blend, params: {}}
          components: [{kind: my_temp_kind, params: {window: 15}}]

``components`` with more than one entry give their equal-weight mean (or ``weights``). Member
forecasts are memoized per fold (same model entry, cut-off, years and training rows), because
the same base and components recur across candidates; see :func:`cached_forecast`.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.backtest import Forecaster
from proto_star.climate import METRICS, ClimateDataError
from proto_star.forecasters import ForecasterSpec, get_kind, register_kind

Metric = Literal["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
_KEY = ["city_id", "year", "metric"]
_CACHE_SIZE = 64


class MemberEntry(BaseModel):
    """A registered model kind and its params, as under ``models`` in a trial config."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str
    params: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> str:
        kind = get_kind(self.kind)
        return f"{self.kind}: {kind.make_spec(self.params).describe()}"


class SwapMetricSpec(ForecasterSpec):
    """Base forecaster with one metric replaced by a mean of components."""

    metric: Metric
    base: MemberEntry = Field(default_factory=lambda: MemberEntry(kind="lead_blend"))
    components: list[MemberEntry] = Field(min_length=1)
    weights: list[float] | None = None

    @model_validator(mode="after")
    def _check_weights(self) -> SwapMetricSpec:
        if self.weights is not None:
            if len(self.weights) != len(self.components):
                raise ValueError("weights must have one value per component")
            if any(w < 0 for w in self.weights) or not np.isclose(sum(self.weights), 1.0):
                raise ValueError("weights must be non-negative and sum to 1")
        return self

    def describe(self) -> str:
        n = len(self.components)
        weights = self.weights or [1.0 / n] * n
        parts = "; ".join(
            f"{w:.2g} x [{c.describe()}]" for w, c in zip(weights, self.components, strict=True)
        )
        return f"{self.metric} = {parts}; other metrics from [{self.base.describe()}]"


# Memo of member forecasts. Keys hold everything the forecast depends on (model entry, fold
# cut-off, years, a hash of the training rows), so a hit returns exactly what a new call would.
_MEMO: OrderedDict[tuple[str, int, tuple[int, ...], int], pd.DataFrame] = OrderedDict()


def _fingerprint(train: pd.DataFrame) -> int:
    return int(pd.util.hash_pandas_object(train, index=False).sum())


def cached_forecast(
    entry: MemberEntry, train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]
) -> pd.DataFrame:
    """Run (or reuse) the forecaster of ``entry`` on one fold. Returns a copy."""
    key = (
        json.dumps(entry.model_dump(), sort_keys=True, default=str),
        int(cutoff_year),
        tuple(int(y) for y in forecast_years),
        _fingerprint(train),
    )
    if key in _MEMO:
        _MEMO.move_to_end(key)
        return _MEMO[key].copy()
    kind = get_kind(entry.kind)
    result = kind.build(kind.make_spec(entry.params))(train, cutoff_year, forecast_years)
    result = result[[*_KEY, "predicted_value"]].copy()
    _MEMO[key] = result
    while len(_MEMO) > _CACHE_SIZE:
        _MEMO.popitem(last=False)
    return result.copy()


def build_swap_metric(spec: SwapMetricSpec) -> Forecaster:
    n = len(spec.components)
    weights = spec.weights or [1.0 / n] * n
    for entry in (spec.base, *spec.components):
        get_kind(entry.kind).make_spec(entry.params)  # fail at build time on bad params

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        base = cached_forecast(spec.base, train, cutoff_year, forecast_years)
        target = base.loc[base["metric"] == spec.metric, _KEY]
        combined = pd.Series(0.0, index=target.index)
        for weight, entry in zip(weights, spec.components, strict=True):
            part = cached_forecast(entry, train, cutoff_year, forecast_years)
            part = part.loc[part["metric"] == spec.metric]
            values = target.merge(part, on=_KEY, how="left")["predicted_value"].to_numpy()
            if not np.isfinite(values).all():
                raise ClimateDataError(
                    f"swap_metric: component {entry.kind} has no finite {spec.metric} forecast "
                    f"for {int((~np.isfinite(values)).sum())} rows at cut-off {cutoff_year}"
                )
            combined += weight * values
        out = base.copy()
        out.loc[target.index, "predicted_value"] = combined.to_numpy()
        return out

    return forecast


def changed_metrics(first: pd.DataFrame, second: pd.DataFrame, *, atol: float = 1e-9) -> set[str]:
    """Metrics whose forecasts differ between two forecasts of the same rows."""
    merged = first.merge(second, on=_KEY, suffixes=("_a", "_b"), validate="one_to_one")
    if len(merged) != len(first) or len(merged) != len(second):
        raise ValueError("the two forecasts do not cover the same rows")
    diff = (merged["predicted_value_a"] - merged["predicted_value_b"]).abs() > atol
    return {str(m) for m in merged.loc[diff, "metric"].unique() if m in METRICS}


register_kind("swap_metric", SwapMetricSpec, build_swap_metric)
