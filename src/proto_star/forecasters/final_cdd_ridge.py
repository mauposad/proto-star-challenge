"""The pooled P09/P14 ridge for CDD alone, as a plug-in kind (``cdd_ridge``).

lead_split3's CDD is 0.5 x the scaled pooled trend + 0.5 x this ridge. The final round's C4
candidate needs the ridge as its own component; this thin wrapper calls
:func:`proto_star.forecasters._pooled_ridge.make_pooled_ridge` with ``model_metrics=["cdd"]``
and lead_split3's settings by default. Other metrics come from the ridge's ``current_best``
fallback and are not meant to be used.
"""

from __future__ import annotations

from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._pooled_ridge import make_pooled_ridge
from proto_star.trend import CDD


class CddRidgeSpec(ForecasterSpec):
    """Settings of the CDD ridge. Defaults are lead_split3's ridge."""

    alpha: float = Field(default=1.0, gt=0.0)
    train_years: int | None = Field(default=None, ge=10)

    def describe(self) -> str:
        years = "all training years" if self.train_years is None else f"{self.train_years} years"
        return f"Pooled P09/P14 ridge for CDD alone (alpha {self.alpha:g}, {years})"


def build_cdd_ridge(spec: CddRidgeSpec) -> Forecaster:
    return make_pooled_ridge(model_metrics=[CDD], alpha=spec.alpha, train_years=spec.train_years)


register_kind("cdd_ridge", CddRidgeSpec, build_cdd_ridge)
