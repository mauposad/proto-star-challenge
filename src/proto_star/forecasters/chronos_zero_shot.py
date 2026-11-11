"""Zero-shot Chronos forecasts of each city's annual series (pretrained time-series model).

Each city and metric's annual series up to the cut-off (organizer-valid years only; invalid
or missing years are NaN, which Chronos masks) is passed to a pretrained Chronos model. The
forecast is the median of ``num_samples`` sample paths, because the score is an MAE. Series
with fewer than ``min_years`` valid values in the context fall back to the 30-year mean.

Provenance and the 2018 cut-off: the default model is ``amazon/chronos-t5-small`` at a pinned
revision, whose training corpus is public (Ansari et al. 2024, arXiv 2403.07815, Appendix B;
``autogluon/chronos_datasets``). Its weather data are USHCN daily (ends 2014-12-31 in the
published files) and WeatherBench (1979-2018). Chronos-Bolt is not used because its training
data are not published. Results are exploratory: the pretrained weights are an input the team
did not fit, see docs/trials/ml_challengers.md.

Requires the ``hf`` extra (``uv sync --extra hf``). torch and chronos are imported inside the
build function, as the registry requires.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import annual_to_long, baseline_forecast
from proto_star.forecasters import ForecasterSpec, register_kind

LOGGER = logging.getLogger(__name__)
Metric = Literal["annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd"]
ALL_METRICS: tuple[Metric, ...] = ("annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd")
KEY = ["city_id", "year", "metric"]
_PIPELINES: dict[tuple[str, str], Any] = {}


class ChronosZeroShotSpec(ForecasterSpec):
    """Pretrained Chronos median forecasts; 30-year mean for other metrics and short series."""

    model_id: str = "amazon/chronos-t5-small"
    revision: str = Field(min_length=7)
    metrics: list[Metric] = Field(default_factory=lambda: list(ALL_METRICS), min_length=1)
    context_years: int = Field(default=64, ge=10, le=512)
    min_years: int = Field(default=10, ge=3)
    num_samples: int = Field(default=20, ge=1)
    batch_size: int = Field(default=10, ge=1)
    seed: int = 0

    def describe(self) -> str:
        return (
            f"Chronos zero-shot ({self.model_id}@{self.revision[:7]}), median of "
            f"{self.num_samples} samples from the last {self.context_years} years, for "
            f"{', '.join(self.metrics)}; 30-year mean elsewhere"
        )


def _pipeline(spec: ChronosZeroShotSpec) -> Any:
    key = (spec.model_id, spec.revision)
    if key not in _PIPELINES:
        import torch
        from chronos import BaseChronosPipeline

        _PIPELINES[key] = BaseChronosPipeline.from_pretrained(
            spec.model_id, revision=spec.revision, device_map="cpu", torch_dtype=torch.float32
        )
    return _PIPELINES[key]


def context_panel(
    history: pd.DataFrame, cutoff_year: int, metric: str, context_years: int
) -> pd.DataFrame:
    """City x year table of valid values for the last ``context_years`` years (NaN if invalid)."""
    first = cutoff_year - context_years + 1
    rows = history.loc[(history["metric"] == metric) & history["year"].between(first, cutoff_year)]
    panel = rows.pivot_table(index="city_id", columns="year", values="actual_value")
    return panel.reindex(columns=range(first, cutoff_year + 1))


def build_chronos_zero_shot(spec: ChronosZeroShotSpec) -> Forecaster:
    import torch

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        history = annual_to_long(train, cutoff_year=cutoff_year)
        out = baseline_forecast(
            history,
            cutoff_year=cutoff_year,
            forecast_years=forecast_years,
            method="thirty_year_mean",
        )
        out = out[[*KEY, "predicted_value"]].reset_index(drop=True)
        horizon = max(forecast_years) - cutoff_year
        pipeline = _pipeline(spec)
        torch.manual_seed(spec.seed + cutoff_year)
        for metric in spec.metrics:
            panel = context_panel(history, cutoff_year, metric, spec.context_years)
            panel = panel.loc[panel.notna().sum(axis=1) >= spec.min_years]
            # Drop leading all-NaN years so each context starts at its first valid value.
            values = panel.to_numpy(dtype=float)
            contexts = []
            for row in values:
                start = int(np.argmax(np.isfinite(row)))
                contexts.append(torch.tensor(row[start:], dtype=torch.float32))
            medians = []
            for begin in range(0, len(contexts), spec.batch_size):
                quantiles, _ = pipeline.predict_quantiles(
                    contexts[begin : begin + spec.batch_size],
                    prediction_length=horizon,
                    quantile_levels=[0.5],
                    num_samples=spec.num_samples,
                )
                medians.append(quantiles[:, :, 0].numpy())
            if not medians:
                continue
            predicted = pd.DataFrame(
                np.concatenate(medians),
                index=panel.index,
                columns=range(cutoff_year + 1, cutoff_year + 1 + horizon),
            )
            predicted.index.name = "city_id"
            long = (
                predicted[forecast_years]
                .reset_index()
                .melt(id_vars="city_id", var_name="year", value_name="chronos")
            )
            long["year"] = long["year"].astype(int)
            long["metric"] = metric
            merged = out.merge(long, on=KEY, how="left")
            has = merged["chronos"].notna().to_numpy()
            out.loc[has, "predicted_value"] = merged.loc[has, "chronos"].to_numpy()
            LOGGER.info(
                "chronos %s at cutoff %s: %d of %d cities forecast",
                metric,
                cutoff_year,
                len(panel),
                out.loc[out["metric"] == metric, "city_id"].nunique(),
            )
        return out

    return forecast


register_kind("chronos_zero_shot", ChronosZeroShotSpec, build_chronos_zero_shot)
