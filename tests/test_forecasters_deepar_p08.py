import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from proto_star.backtest import resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all

CUTOFF = 2000
YEARS = list(range(CUTOFF + 1, CUTOFF + 8))
TINY = {
    "context": 10,
    "hidden": 8,
    "layers": 1,
    "seeds": 1,
    "samples": 20,
    "max_epochs": 2,
    "threads": 1,
}
KEY = ["city_id", "year", "metric"]


def _run(train: pd.DataFrame, **params: object) -> pd.DataFrame:
    forecaster = load_all()["deepar_p08"].build({**TINY, **params})
    return forecaster(train, CUTOFF, YEARS).sort_values(KEY, ignore_index=True)


def _train() -> pd.DataFrame:
    master = make_annual_master()
    return master.loc[master["Year"] <= CUTOFF].copy()


def test_covers_every_city_metric_and_year() -> None:
    forecast = _run(_train())
    assert len(forecast) == 4 * len(METRICS) * len(YEARS)
    assert set(forecast["metric"]) == set(METRICS)
    assert np.isfinite(forecast["predicted_value"]).all()


def test_same_seed_is_deterministic_and_seed_matters() -> None:
    train = _train()
    first, second = _run(train, seed=5), _run(train, seed=5)
    pd.testing.assert_frame_equal(first, second)
    other = _run(train, seed=6)
    assert not np.allclose(first["predicted_value"], other["predicted_value"])


def test_values_after_the_cutoff_change_nothing() -> None:
    master = make_annual_master()
    forecaster = load_all()["deepar_p08"].build(TINY)
    perturbed = master.copy()
    late = perturbed["Year"] > CUTOFF
    perturbed.loc[late, ["Avg Temp", "ToT Prcp", "Max Tmax", "cdd"]] += 1000.0
    clean = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    dirty = forecaster(perturbed.loc[perturbed["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, dirty)
    with pytest.raises(ValueError, match="after allowed cutoff"):
        forecaster(perturbed, CUTOFF, YEARS)


def test_params_pass_through_and_hybrid_falls_back_to_current_best() -> None:
    train = _train()
    hybrid = _run(train, neural_metrics=["cdd"], city_dim=0)
    best = resolve_forecaster("current_best")(train, CUTOFF, YEARS).sort_values(
        KEY, ignore_index=True
    )
    other = hybrid["metric"] != "cdd"
    np.testing.assert_allclose(
        hybrid.loc[other, "predicted_value"], best.loc[other, "predicted_value"]
    )
    assert not np.allclose(
        hybrid.loc[~other, "predicted_value"], best.loc[~other, "predicted_value"]
    )
    more_samples = _run(train, neural_metrics=["cdd"], city_dim=0, samples=40)
    assert not np.allclose(more_samples["predicted_value"], hybrid["predicted_value"])


def test_series_too_short_to_window_fall_back() -> None:
    train = _train()
    short = train["ID"].eq("CITY001") & train["Year"].lt(CUTOFF - 2)
    train.loc[short, "Miss Prcp"] = 99  # only 2 valid precipitation years remain
    forecast = _run(train)
    best = resolve_forecaster("current_best")(train, CUTOFF, YEARS)

    def pick(frame: pd.DataFrame) -> np.ndarray:
        rows = (frame["city_id"] == "CITY001") & (frame["metric"] == "total_precip_in")
        return frame.loc[rows].sort_values("year")["predicted_value"].to_numpy()

    np.testing.assert_allclose(pick(forecast), pick(best))


def test_bad_params_are_rejected() -> None:
    with pytest.raises(ValueError, match="rejected params"):
        load_all()["deepar_p08"].build({"bogus": 1})
    with pytest.raises(ValueError, match="samples"):
        load_all()["deepar_p08"].build({"samples": 0})
