"""The pooled-trend model as a plug-in kind, so new models can build on it under ``models``.

``models: {x: {kind: pooled_trend, params: {...}}}`` gives the same forecaster as the older
``pooled_trends: {x: {...}}`` block, which stays for existing configs.
"""

from __future__ import annotations

from proto_star.backtest import Forecaster, pooled_trend_forecaster
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.trend import PooledTrendSpec, describe_pooled_trend


class PooledTrendKindSpec(PooledTrendSpec, ForecasterSpec):
    """:class:`PooledTrendSpec` with a description, for the plug-in registry."""

    def describe(self) -> str:
        return describe_pooled_trend(self)


def build_pooled_trend(spec: PooledTrendKindSpec) -> Forecaster:
    return pooled_trend_forecaster(spec)


register_kind("pooled_trend", PooledTrendKindSpec, build_pooled_trend)
