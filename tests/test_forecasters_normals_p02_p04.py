import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters.normals_p02_p04 import (
    damped_trend_rule,
    ewma,
    ewma_rule,
    hindcast_errors,
    selected_normals_forecaster,
    window_mean_rule,
)

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]


def _train(cutoff: int = CUTOFF) -> pd.DataFrame:
    master = make_annual_master()
    return master.loc[master["Year"] <= cutoff].copy()


def test_registered_and_full_coverage() -> None:
    registry = load_all()
    for name in ("ocn_normal", "ewma_normal", "damped_trend_normal", "optimal_normal"):
        forecast = registry[name].build()(_train(), CUTOFF, YEARS)
        assert set(forecast["metric"]) == set(METRICS)
        assert len(forecast) == 4 * len(METRICS) * len(YEARS)
        assert not forecast.duplicated(KEY).any()
        assert np.isfinite(forecast["predicted_value"]).all()


def test_ewma_matches_hand_computation() -> None:
    assert ewma(np.array([0.0, 10.0]), 0.5) == pytest.approx(5.0)
    assert ewma(np.array([0.0, 10.0, 20.0]), 0.5) == pytest.approx(12.5)
    assert ewma(np.array([4.0, 8.0]), 1.0) == pytest.approx(8.0)
    rule = ewma_rule(0.25)
    out = rule(np.array([1, 2, 3]), np.array([8.0, 0.0, 4.0]), np.array([4, 5]))
    # 8 -> 0.25*0 + 0.75*8 = 6 -> 0.25*4 + 0.75*6 = 5.5
    assert out == pytest.approx([5.5, 5.5])
    with pytest.raises(ValueError, match="alpha"):
        ewma_rule(0.0)


def test_window_and_damped_trend_rules() -> None:
    years = np.arange(1981, 2001)
    values = 0.1 * (years - 1981).astype(float)  # exact line, slope 0.1 per year
    assert window_mean_rule(4)(years, values, np.array([2001]))[0] == pytest.approx(1.75)
    targets = np.array([2001, 2005])
    flat = damped_trend_rule(4, 30, 0.0)(years, values, targets)
    full = damped_trend_rule(4, 30, 1.0)(years, values, targets)
    half = damped_trend_rule(4, 30, 0.5)(years, values, targets)
    assert flat == pytest.approx([1.75, 1.75])
    assert full == pytest.approx(0.1 * (targets - 1981))  # line recovered exactly
    assert half == pytest.approx((flat + full) / 2)


def test_ocn_picks_long_window_for_noise_and_short_for_a_step() -> None:
    """On white noise the longest window wins; after a level shift the shortest does."""
    rng = np.random.default_rng(0)
    years = np.arange(1900, 2001)
    rows = []
    for city in range(3):
        noise = rng.standard_normal(years.size)
        step = np.where(years >= 1960, 10.0, 0.0)
        for year, n, s in zip(years, noise, step, strict=True):
            rows.append({"ID": f"C{city}", "Year": year, "noise": n, "step": s + 0.1 * n})
    frame = pd.DataFrame(rows)
    master = make_annual_master(n_cities=3, first_year=1900, last_year=2000)
    master["ID"] = frame["ID"].to_numpy()
    master["Avg Temp"] = frame["noise"].to_numpy()
    master["cdd"] = frame["step"].to_numpy()
    selections: dict[int, dict[str, dict[str, str]]] = {}
    candidates = {"k3": window_mean_rule(3), "k30": window_mean_rule(30)}
    forecaster = selected_normals_forecaster(
        candidates, n_origins=4, selections=selections, metrics=["annual_avg_temp", "cdd"]
    )
    forecaster(master, CUTOFF, YEARS)
    assert set(selections[CUTOFF]["annual_avg_temp"].values()) == {"k30"}
    # A step in 1960 is old news by the pseudo-origins (1972-1993); noise is tiny, so the
    # short window is at least as good.  Ties go to the first candidate (k3).
    assert set(selections[CUTOFF]["cdd"].values()) == {"k3"}


def test_selection_ignores_years_after_the_cutoff() -> None:
    """Perturbing post-cutoff rows of the full table cannot change the forecast."""
    master = make_annual_master()
    perturbed = master.copy()
    later = perturbed["Year"] > CUTOFF
    for column in ("Avg Temp", "ToT Prcp", "Max Tmax", "cdd"):
        perturbed.loc[later, column] = perturbed.loc[later, column] * 3.0 + 100.0
    for scope in ("metric", "region", "city"):
        forecaster = resolve_forecaster(
            "v", variants={"v": {"forecaster": "ocn_normal", "params": {"scope": scope}}}
        )
        a = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS).sort_values(KEY)
        b = forecaster(perturbed.loc[perturbed["Year"] <= CUTOFF], CUTOFF, YEARS)
        pd.testing.assert_frame_equal(
            a.reset_index(drop=True), b.sort_values(KEY).reset_index(drop=True)
        )


def test_hindcast_errors_never_score_years_after_the_cutoff() -> None:
    """Even if a series holds later years, the hindcast scores only years <= cutoff."""
    years = np.arange(1950, 2011)
    values = np.zeros(years.size)
    series = {("C", "cdd"): (years, values)}
    later = {("C", "cdd"): (years, np.where(years > CUTOFF, 1e6, values))}
    kwargs = {"n_origins": 4, "step": 7, "horizon": 7, "leads": range(1, 8)}
    rule = window_mean_rule(10)
    clean = hindcast_errors(series, [("C", "cdd")], CUTOFF, rule, **kwargs)
    dirty = hindcast_errors(later, [("C", "cdd")], CUTOFF, rule, **kwargs)
    assert clean == dirty == {("C", "cdd"): (0.0, 28)}


def test_metrics_subset_uses_fallback_and_sparse_city_is_filled() -> None:
    train = _train()
    # CITY003 has only two valid temperature years: too short for any hindcast.
    sparse = (train["ID"] == "CITY003") & (train["Year"] < CUTOFF - 1)
    train.loc[sparse, "Miss Tmax"] = 99
    forecaster = resolve_forecaster(
        "v",
        variants={
            "v": {
                "forecaster": "ocn_normal",
                "params": {"metrics": ["annual_avg_temp"], "fallback": "ten_year_mean"},
            }
        },
    )
    forecast = forecaster(train, CUTOFF, YEARS)
    assert len(forecast) == 4 * len(METRICS) * len(YEARS)
    ten = resolve_forecaster("ten_year_mean")(train, CUTOFF, YEARS)
    precip = forecast.loc[forecast["metric"] == "total_precip_in"].sort_values(KEY)
    expected = ten.loc[ten["metric"] == "total_precip_in"].sort_values(KEY)
    assert precip["predicted_value"].to_numpy() == pytest.approx(
        expected["predicted_value"].to_numpy()
    )


def test_bad_params_are_rejected() -> None:
    registry = load_all()
    with pytest.raises(ValueError, match="scope"):
        registry["ocn_normal"].build({"scope": "planet"})(_train(), CUTOFF, YEARS)
    with pytest.raises(ValueError, match="unknown metrics"):
        registry["ocn_normal"].build({"metrics": ["rain"]})
