"""Final-round precipitation components: Tatakae's nudge and PstarAlu's two-half level.

Both are re-implemented from README text only (no code of either team was downloaded or
copied); the interpretation of every unclear point is fixed in ``docs/trials/final_precip_hot.md``.

* ``final_precip_nudge`` (P1): Tatakae, dataset ``ironMan334/protostar-climate-team-tatakae``
  (CC BY 4.0), commit ``f18c1178c1b97566c75facc94c886184ebaa2a10``, "Rain and the hottest
  day": 30-year mean x (1 + 0.3 x the city's mean ratio departure over the last 10 years from
  its 31 nearest cities, each against its own 30-year mean).
* ``final_precip_two_half`` (P2, and P3 with ``fay_herriot``): PstarAlu (Nibedita Biswal),
  dataset ``nbiswal-star/protostar-climate-submission`` (CC BY 4.0), commit
  ``9e51c3ef5d3178ca194f28e2c4134201c1bf9675``, "Method > Precipitation". Level = 0.5 x shrunk
  30-year median + 0.5 x mean of complete years (>= 360 days of data); the mean half uses 30
  years for leads 1-3 and 45 years for leads 4-7 when the city has enough complete years. P3
  adds, for leads 4-7, a Fay-Herriot (Fay & Herriot 1979, JASA 74(366), 269-277) precision
  shrinkage of the city's local deviation (45-year window vs 90-year record, after removing a
  300 km leave-one-out Gaussian-kernel neighbor mean), with ``tau^2`` by the method of moments
  floored at 0, and no change for sparse cities.

Only ``total_precip_in`` rows are returned; use them through ``swap_metric``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pydantic import Field

from proto_star.backtest import Forecaster
from proto_star.climate import metric_valid_mask
from proto_star.forecasters import ForecasterSpec, register_kind
from proto_star.forecasters._final_common import (
    KEY,
    NudgeSpec,
    kernel_matrix,
    kernel_mean,
    neighbor_nudge,
    thirty_year_rows,
)

METRIC = "total_precip_in"
HALF = 0.5  # PstarAlu: "two equal halves"


class PrecipNudgeSpec(NudgeSpec):
    """Tatakae's precipitation nudge (ratio departures)."""

    def describe(self) -> str:
        return f"Precipitation: {super().describe()}, as a ratio"


def build_precip_nudge(spec: PrecipNudgeSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        rows = thirty_year_rows(train, cutoff_year, forecast_years, METRIC)
        nudge = neighbor_nudge(
            train,
            cutoff_year,
            METRIC,
            k=spec.k,
            recent_years=spec.recent_years,
            window=spec.window,
            min_years=spec.min_years,
            kind="ratio",
        )
        factor = 1.0 + spec.fraction * rows["city_id"].map(nudge).fillna(0.0)
        rows["predicted_value"] = (rows["predicted_value"] * factor).clip(lower=0.0)
        return rows[[*KEY, "predicted_value"]]

    return forecast


class TwoHalfSpec(ForecasterSpec):
    """PstarAlu's two-half precipitation level, optionally with the Fay-Herriot step."""

    fay_herriot: bool = False
    window: int = Field(default=30, ge=1)
    long_window: int = Field(default=45, ge=1)
    record_years: int = Field(default=90, ge=1)
    early_leads: int = Field(default=3, ge=0)
    min_days: int = Field(default=360, ge=1, le=366)
    min_valid: int = Field(default=10, ge=1)
    min_complete: int = Field(default=10, ge=1)
    min_complete_long: int = Field(default=15, ge=1)
    median_shrink: float = Field(default=0.5, ge=0.0, le=1.0)
    bandwidth_km: float = Field(default=300.0, gt=0.0)
    fh_min_window_years: int = Field(default=15, ge=2)
    fh_min_record_years: int = Field(default=30, ge=2)
    fh_min_kernel_weight: float = Field(default=0.5, ge=0.0)

    def describe(self) -> str:
        text = (
            f"Precipitation: 0.5 x {self.window}-year median (median/mean ratio shrunk "
            f"{self.median_shrink:g} toward the {self.bandwidth_km:g} km kernel mean) + 0.5 x "
            f"complete-year mean ({self.window} years for leads 1-{self.early_leads}, "
            f"{self.long_window} for later leads if >= {self.min_complete}/"
            f"{self.min_complete_long} complete years) (PstarAlu)"
        )
        if self.fay_herriot:
            text += (
                f"; leads > {self.early_leads}: Fay-Herriot shrinkage of the "
                f"{self.long_window}-year local deviation vs the {self.record_years}-year "
                f"record ({self.bandwidth_km:g} km leave-one-out kernel)"
            )
        return text


def _panels(train: pd.DataFrame, cutoff_year: int, min_days: int) -> tuple[pd.DataFrame, ...]:
    """City x year panels of valid and of complete precipitation totals up to the cut-off."""
    year = pd.to_numeric(train["Year"]).astype(int)
    value = pd.to_numeric(train["ToT Prcp"], errors="coerce")
    days = np.where((year % 4 == 0) & ((year % 100 != 0) | (year % 400 == 0)), 366, 365)
    with_data = days - pd.to_numeric(train["Miss Prcp"], errors="coerce")
    complete = value.notna() & np.isfinite(value) & with_data.ge(min_days)
    frame = pd.DataFrame(
        {
            "city_id": train["ID"].astype(str),
            "year": year,
            "valid": value.where(metric_valid_mask(train, METRIC)),
            "complete": value.where(complete),
        }
    )
    cities = sorted(frame["city_id"].unique())
    years = range(int(year.min()), cutoff_year + 1)
    out = []
    for column in ("valid", "complete"):
        panel = frame.pivot_table(index="city_id", columns="year", values=column, aggfunc="first")
        out.append(panel.reindex(index=cities, columns=years))
    return tuple(out)


def _window(panel: pd.DataFrame, cutoff_year: int, years: int) -> pd.DataFrame:
    return panel.loc[:, [y for y in panel.columns if int(y) > cutoff_year - years]]


def fay_herriot_correction(
    complete: pd.DataFrame,
    kernel: pd.DataFrame,
    cutoff_year: int,
    uses_long: pd.Series,
    spec: TwoHalfSpec,
) -> pd.Series:
    """Correction in inches to add to each city's leads 4-7 level (0 where not eligible).

    ``kernel`` is the leave-one-out raw Gaussian weight matrix. The city's local deviation
    ``D`` (mean residual in the long window minus mean residual in the record) is replaced by
    ``B D`` with ``B = tau^2 / (tau^2 + V)``, so the correction is ``(B - 1) D`` in units of
    the city's record mean.
    """
    record = _window(complete, cutoff_year, spec.record_years)
    record_mean = record.mean(axis=1)
    relative = record.div(record_mean.where(record_mean > 0), axis=0) - 1.0
    y = relative.to_numpy(dtype=float)
    present = np.isfinite(y)
    w = kernel.reindex(index=relative.index, columns=relative.index).to_numpy(dtype=float)
    weight = w @ present.astype(float)
    numerator = w @ np.where(present, y, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        regional = np.where(
            weight >= max(spec.fh_min_kernel_weight, 1e-12), numerator / weight, np.nan
        )
    residual = pd.DataFrame(y - regional, index=relative.index, columns=relative.columns)

    in_window = _window(residual, cutoff_year, spec.long_window)
    n_window = in_window.notna().sum(axis=1)
    n_record = residual.notna().sum(axis=1)
    deviation = in_window.mean(axis=1) - residual.mean(axis=1)
    sampling = residual.var(axis=1, ddof=1) * (
        1.0 / n_window.where(n_window > 0) - 1.0 / n_record.where(n_record > 0)
    )
    eligible = (
        uses_long.reindex(residual.index).fillna(False).astype(bool)
        & n_window.ge(spec.fh_min_window_years)
        & n_record.ge(spec.fh_min_record_years)
        & np.isfinite(deviation)
        & np.isfinite(sampling)
    )
    tau2 = method_of_moments_tau2(deviation[eligible], sampling[eligible])
    weight_b = precision_weight(tau2, sampling)
    correction = (weight_b - 1.0) * deviation * record_mean
    return correction.where(eligible, 0.0).fillna(0.0)


def method_of_moments_tau2(deviation: pd.Series, sampling: pd.Series) -> float:
    """Between-city variance of the true deviations: mean(D^2) - mean(V), floored at 0."""
    if len(deviation) < 2:
        return 0.0
    return float(max(0.0, np.mean(deviation.to_numpy() ** 2) - np.mean(sampling.to_numpy())))


def precision_weight(tau2: float, sampling: pd.Series) -> pd.Series:
    """``tau^2 / (tau^2 + V)``; 1 where both are 0 (a deviation known exactly is kept)."""
    total = tau2 + sampling
    return (tau2 / total.where(total > 0)).fillna(1.0)


def build_two_half(spec: TwoHalfSpec) -> Forecaster:
    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        rows = thirty_year_rows(train, cutoff_year, forecast_years, METRIC)
        m30 = rows.groupby("city_id")["predicted_value"].first()
        valid, complete = _panels(train, cutoff_year, spec.min_days)
        loo = kernel_matrix(train, spec.bandwidth_km, include_self=False)

        recent = _window(valid, cutoff_year, spec.window)
        n_valid = recent.notna().sum(axis=1)
        mean_valid = recent.mean(axis=1)
        dense = n_valid.ge(spec.min_valid) & mean_valid.gt(0)
        ratio = (recent.median(axis=1) / mean_valid).where(dense)
        neighbor_ratio = kernel_mean(ratio, loo).reindex(ratio.index)
        shrunk_ratio = (
            (1.0 - spec.median_shrink) * ratio + spec.median_shrink * neighbor_ratio
        ).fillna(ratio)
        shrunk_median = mean_valid * shrunk_ratio

        c30 = _window(complete, cutoff_year, spec.window)
        c45 = _window(complete, cutoff_year, spec.long_window)
        n30 = c30.notna().sum(axis=1)
        n45 = c45.notna().sum(axis=1)
        m30_city = m30.reindex(valid.index)
        mean_early = c30.mean(axis=1).where(n30.ge(spec.min_complete), m30_city)
        uses_long = n30.ge(spec.min_complete) & n45.ge(spec.min_complete_long) & dense
        mean_late = c45.mean(axis=1).where(uses_long, mean_early)

        early = (HALF * shrunk_median + HALF * mean_early).where(dense, m30_city)
        late = (HALF * shrunk_median + HALF * mean_late).where(dense, m30_city)
        if spec.fay_herriot:
            correction = fay_herriot_correction(complete, loo, cutoff_year, uses_long, spec)
            late = (late + correction.reindex(late.index).fillna(0.0)).clip(lower=0.0).round(4)

        lead = rows["year"] - cutoff_year
        value = np.where(
            lead <= spec.early_leads, rows["city_id"].map(early), rows["city_id"].map(late)
        )
        rows["predicted_value"] = pd.Series(value, index=rows.index).fillna(rows["predicted_value"])
        return rows[[*KEY, "predicted_value"]]

    return forecast


register_kind("final_precip_nudge", PrecipNudgeSpec, build_precip_nudge)
register_kind("final_precip_two_half", TwoHalfSpec, build_two_half)
