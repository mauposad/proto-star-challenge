"""Paired comparisons of two forecasters, with intervals from resampling forecast years.

Ported from branch ``agent/hypothesis-trials`` (``proto_star.backtest`` there). The scorer, the
folds and the metric are unchanged: :func:`fold_rows` returns exactly the rows
:func:`proto_star.backtest.backtest_forecaster` scores, and :func:`paired_year_bootstrap` adds
an interval to the difference of two methods' mean raw scores. Errors are strongly correlated
across cities within a year, so the resampling unit is the forecast year within a fold.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from proto_star.backtest import (
    DEFAULT_HORIZON,
    WINDOWS,
    Forecaster,
    _check_coverage,
)
from proto_star.climate import (
    DEFAULT_CUTOFFS,
    METRICS,
    annual_to_long,
    assert_weather_cutoff,
    baseline_forecast,
)

KEY = ["city_id", "year", "metric"]


def fold_rows(
    forecaster: Forecaster,
    master: pd.DataFrame,
    *,
    name: str = "forecast",
    cutoffs: Iterable[int] = DEFAULT_CUTOFFS,
    horizon: int = DEFAULT_HORIZON,
) -> pd.DataFrame:
    """Every scored row of every fold, with the forecast, the actual value and the reference."""
    history = annual_to_long(master)
    frames = []
    for cutoff in cutoffs:
        years = list(range(cutoff + 1, cutoff + horizon + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        assert_weather_cutoff(train, name="training fold", cutoff_year=cutoff)
        forecast = forecaster(train, cutoff, years)
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "reference_value"})
        truth = history.loc[history["year"].isin(years)].merge(reference, on=KEY)
        _check_coverage(forecast, truth, years, f"{name} at cutoff {cutoff}")
        rows = truth.merge(forecast[[*KEY, "predicted_value"]], on=KEY, how="left")
        frames.append(rows.assign(cutoff_year=cutoff))
    return pd.concat(frames, ignore_index=True)


def paired_year_bootstrap(
    rows_a: pd.DataFrame,
    rows_b: pd.DataFrame,
    *,
    window: str = "all",
    metrics: Iterable[str] = METRICS,
    n_boot: int = 4000,
    seed: int = 0,
) -> dict[str, float]:
    """Difference in mean raw score, b minus a, with a 95% interval from resampling years.

    Each fold's skill difference is a sum of per-year contributions,
    ``(|e_a| - |e_b|) / (n * MAE_ref)`` over that year's rows. Years are resampled with
    replacement within each fold; ``n`` and ``MAE_ref`` are held fixed. Restrict ``metrics``
    to get one metric's skill difference (times 100 / number of metrics).
    """
    chosen = list(metrics)
    keys = ["cutoff_year", *KEY]
    paired = rows_a[[*keys, "actual_value", "reference_value", "predicted_value"]].merge(
        rows_b[[*keys, "predicted_value"]], on=keys, suffixes=("_a", "_b"), validate="1:1"
    )
    first, last = WINDOWS[window]
    lead = paired["year"] - paired["cutoff_year"]
    paired = paired.loc[lead.between(first, last) & paired["metric"].isin(chosen)].copy()
    paired["gain"] = (paired["predicted_value_a"] - paired["actual_value"]).abs() - (
        paired["predicted_value_b"] - paired["actual_value"]
    ).abs()
    paired["ref_error"] = (paired["reference_value"] - paired["actual_value"]).abs()
    scale = paired.groupby(["cutoff_year", "metric"])["ref_error"].transform("sum")
    n_folds = paired["cutoff_year"].nunique()
    paired["contribution"] = 100.0 * paired["gain"] / scale / (n_folds * len(chosen))
    per_year = paired.groupby(["cutoff_year", "year"])["contribution"].sum()

    rng = np.random.default_rng(seed)
    draws = np.zeros(n_boot)
    for _, values in per_year.groupby(level="cutoff_year"):
        array = values.to_numpy()
        picks = rng.integers(0, len(array), size=(n_boot, len(array)))
        draws += array[picks].sum(axis=1)
    low, high = np.percentile(draws, [2.5, 97.5])
    return {
        "difference": float(per_year.sum()),
        "low": float(low),
        "high": float(high),
        "share_not_better": float((draws <= 0).mean()),
        "years": float(len(per_year)),
    }
