import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from proto_star.backtest import resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters._neural_common import (
    build_panel,
    forecast_windows,
    inner_split,
)

CUTOFF = 2000
YEARS = list(range(CUTOFF + 1, CUTOFF + 8))
TINY = {"lookbacks": [10], "seeds": 1, "max_epochs": 2, "width": 8, "threads": 1}
KEY = ["city_id", "year", "metric"]


def _run(train: pd.DataFrame, **params: object) -> pd.DataFrame:
    forecaster = load_all()["nbeats_p05"].build({**TINY, **params})
    return forecaster(train, CUTOFF, YEARS).sort_values(KEY, ignore_index=True)


def _train() -> pd.DataFrame:
    master = make_annual_master()
    return master.loc[master["Year"] <= CUTOFF].copy()


def test_covers_every_city_metric_and_year() -> None:
    forecast = _run(_train())
    assert len(forecast) == 4 * len(METRICS) * len(YEARS)
    assert set(forecast["metric"]) == set(METRICS)
    assert set(forecast["year"]) == set(YEARS)
    assert np.isfinite(forecast["predicted_value"]).all()


def test_same_seed_is_deterministic_and_seed_matters() -> None:
    train = _train()
    first, second = _run(train, seed=3), _run(train, seed=3)
    pd.testing.assert_frame_equal(first, second)
    other = _run(train, seed=4)
    assert not np.allclose(first["predicted_value"], other["predicted_value"])


def test_values_after_the_cutoff_change_nothing() -> None:
    master = make_annual_master()
    forecaster = load_all()["nbeats_p05"].build(TINY)
    perturbed = master.copy()
    late = perturbed["Year"] > CUTOFF
    perturbed.loc[late, ["Avg Temp", "ToT Prcp", "Max Tmax", "cdd"]] += 1000.0
    # The backtest hands a forecaster only rows up to the cutoff; do the same here.
    clean = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    dirty = forecaster(perturbed.loc[perturbed["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, dirty)
    # Handed post-cutoff rows by mistake, it refuses instead of quietly using them.
    with pytest.raises(ValueError, match="after allowed cutoff"):
        forecaster(perturbed, CUTOFF, YEARS)


def test_inner_split_keeps_validation_targets_out_of_training() -> None:
    panel = build_panel(_train(), CUTOFF, ["annual_avg_temp"])
    fit, valid = inner_split(
        panel, lookback=10, horizon=7, min_obs=5, cutoff_year=CUTOFF, holdout=7
    )
    # Training targets stop at cutoff - holdout: the last target lead of the latest origin
    # (cutoff - holdout - 1) is masked beyond lead 1.
    latest = fit.y_mask[-1]
    assert latest[0] == 1.0 and latest[1:].sum() == 0.0
    assert len(valid) == 4 and valid.y_mask.all()
    # Forecast windows end at the cutoff and carry no targets.
    windows = forecast_windows(panel, lookback=10, horizon=7, min_obs=5)
    assert len(windows) == 4 and windows.y_mask.sum() == 0.0


def test_params_pass_through_and_hybrid_falls_back_to_current_best() -> None:
    train = _train()
    hybrid = _run(train, neural_metrics=["annual_avg_temp"], architecture="interpretable")
    best = resolve_forecaster("current_best")(train, CUTOFF, YEARS).sort_values(
        KEY, ignore_index=True
    )
    other = hybrid["metric"] != "annual_avg_temp"
    np.testing.assert_allclose(
        hybrid.loc[other, "predicted_value"], best.loc[other, "predicted_value"]
    )
    temp = ~other
    assert not np.allclose(hybrid.loc[temp, "predicted_value"], best.loc[temp, "predicted_value"])


def test_series_too_short_to_window_fall_back() -> None:
    train = _train()
    short = train["ID"].eq("CITY000") & train["Year"].lt(CUTOFF - 3)
    train.loc[short, "Miss Tmax"] = 99  # fails the missing-days rule: only 3 valid years left
    forecast = _run(train)
    best = resolve_forecaster("current_best")(train, CUTOFF, YEARS)
    rows = (forecast["city_id"] == "CITY000") & (forecast["metric"] == "hottest_day_temp")
    expected = best.loc[
        (best["city_id"] == "CITY000") & (best["metric"] == "hottest_day_temp"),
        "predicted_value",
    ]
    np.testing.assert_allclose(forecast.loc[rows, "predicted_value"], expected.to_numpy())


def test_bad_params_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown metrics"):
        load_all()["nbeats_p05"].build({"neural_metrics": ["snow"]})
    with pytest.raises(ValueError, match="rejected params"):
        load_all()["nbeats_p05"].build({"bogus": 1})
    with pytest.raises(ValueError, match="threads"):
        _run(_train(), threads=64)
