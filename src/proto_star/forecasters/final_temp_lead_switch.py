"""Use one forecaster for the first leads and another for the rest (final round, T6).

Kind ``final_temp_lead_switch``: rows with lead (year - cut-off) <= ``last_early_lead`` come
from ``early``, later rows from ``late``. T6 is ``early`` = lead_split3 (whose temperature
holds the pooled ridge in leads 1-3) and ``late`` = T5, wrapped in ``swap_metric`` so only
``annual_avg_temp`` changes. Member forecasts are memoized per fold (``cached_forecast``).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import ClimateDataError
from proto_star.forecasters import ForecasterSpec, get_kind, register_kind
from proto_star.forecasters.swap_metric import MemberEntry, cached_forecast

_KEY = ["city_id", "year", "metric"]


class LeadSwitchSpec(ForecasterSpec):
    """Two member forecasters split by forecast lead."""

    early: MemberEntry
    late: MemberEntry
    last_early_lead: int = Field(default=3, ge=1)

    def describe(self) -> str:
        return (
            f"leads 1-{self.last_early_lead} from [{self.early.describe()}]; later leads from "
            f"[{self.late.describe()}]"
        )


def build_lead_switch(spec: LeadSwitchSpec) -> Forecaster:
    for entry in (spec.early, spec.late):
        get_kind(entry.kind).make_spec(entry.params)  # fail at build time on bad params

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        early = cached_forecast(spec.early, train, cutoff_year, forecast_years)
        late = cached_forecast(spec.late, train, cutoff_year, forecast_years)
        merged = early.merge(
            late, on=_KEY, how="outer", suffixes=("_early", "_late"), validate="one_to_one"
        )
        is_early = (merged["year"] - cutoff_year) <= spec.last_early_lead
        values = np.where(is_early, merged["predicted_value_early"], merged["predicted_value_late"])
        if not np.isfinite(values).all():
            raise ClimateDataError(
                f"final_temp_lead_switch: {int((~np.isfinite(values)).sum())} rows lack a "
                f"forecast at cut-off {cutoff_year}"
            )
        merged["predicted_value"] = values
        return merged[[*_KEY, "predicted_value"]].sort_values(_KEY, ignore_index=True)

    return forecast


register_kind("final_temp_lead_switch", LeadSwitchSpec, build_lead_switch)
