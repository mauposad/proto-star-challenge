import numpy as np
import pandas as pd
import pytest
from scipy import stats

from proto_star.backtest import Forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters.gev_p23 import GevFit, fit_gev, gev_negative_log_likelihood

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]


def _variant(forecaster: str, **params: object) -> Forecaster:
    return resolve_forecaster("v", variants={"v": {"forecaster": forecaster, "params": params}})


def test_fit_recovers_a_known_location_trend() -> None:
    rng = np.random.default_rng(1)
    years = np.arange(1900, 2000)
    mu = 95.0 + 0.3 * (years - years.mean()) / 10.0  # 0.3 degrees per decade
    sample = stats.genextreme.rvs(c=0.2, loc=mu, scale=2.0, random_state=rng)  # xi = -0.2
    fit = fit_gev(years, sample, trend=True)
    assert fit.converged
    assert fit.mu1 == pytest.approx(0.3, abs=0.12)
    assert fit.sigma == pytest.approx(2.0, rel=0.2)
    assert fit.xi == pytest.approx(-0.2, abs=0.12)
    assert fit.mu0 == pytest.approx(95.0, abs=0.5)


def test_nll_matches_scipy_and_location_statistics() -> None:
    x = np.array([94.0, 96.5, 98.0, 95.2])
    z = np.zeros(4)
    params = np.array([95.0, 0.0, np.log(2.0), -0.2])
    expected = -stats.genextreme.logpdf(x, c=0.2, loc=95.0, scale=2.0).sum()
    assert gev_negative_log_likelihood(params, x, z, trend=False) == pytest.approx(expected)
    fit = GevFit(mu0=95.0, mu1=1.0, sigma=2.0, xi=-0.2, t_bar=2000.0, converged=True)
    years = np.array([2010])
    median = stats.genextreme.median(c=0.2, loc=96.0, scale=2.0)
    assert fit.location(years, statistic="median", shrink=1.0)[0] == pytest.approx(median)
    no_trend = stats.genextreme.median(c=0.2, loc=95.0, scale=2.0)
    assert fit.location(years, statistic="median", shrink=0.0)[0] == pytest.approx(no_trend)
    q9 = stats.genextreme.ppf(0.9, c=0.2, loc=95.5, scale=2.0)
    assert fit.location(years, statistic=0.9, shrink=0.5)[0] == pytest.approx(q9)
    with pytest.raises(ValueError, match="statistic"):
        fit.location(years, statistic="mode", shrink=1.0)


def test_coverage_and_fallback_for_other_metrics() -> None:
    master = make_annual_master()
    train = master.loc[master["Year"] <= CUTOFF]
    forecast = _variant("gev_hottest_day", fallback="ten_year_mean")(train, CUTOFF, YEARS)
    assert len(forecast) == 4 * len(METRICS) * len(YEARS)
    assert not forecast.duplicated(KEY).any()
    ten = resolve_forecaster("ten_year_mean")(train, CUTOFF, YEARS)
    other = forecast.loc[forecast["metric"] != "hottest_day_temp"].sort_values(KEY)
    expected = ten.loc[ten["metric"] != "hottest_day_temp"].sort_values(KEY)
    assert other["predicted_value"].to_numpy() == pytest.approx(
        expected["predicted_value"].to_numpy()
    )
    hot = forecast.loc[forecast["metric"] == "hottest_day_temp", "predicted_value"]
    assert hot.between(85, 110).all()


def test_short_series_falls_back_to_sample_median() -> None:
    master = make_annual_master(n_cities=1)
    train = master.loc[master["Year"] <= CUTOFF].copy()
    train.loc[train["Year"] <= CUTOFF - 10, "Miss Tmax"] = 99  # 10 valid years left
    forecast = _variant("gev_hottest_day")(train, CUTOFF, YEARS)
    hot = forecast.loc[forecast["metric"] == "hottest_day_temp", "predicted_value"]
    last10 = train.loc[train["Year"] > CUTOFF - 10, "Max Tmax"]
    assert hot.to_numpy() == pytest.approx(np.full(len(YEARS), np.median(last10)))


def test_shrink_selection_uses_train_only() -> None:
    master = make_annual_master()
    perturbed = master.copy()
    later = perturbed["Year"] > CUTOFF
    perturbed.loc[later, "Max Tmax"] = perturbed.loc[later, "Max Tmax"] + 50.0
    log_a: dict[int, float] = {}
    log_b: dict[int, float] = {}
    a = _variant("gev_hottest_day", trend_shrink=[0.0, 1.0], shrink_log=log_a)(
        master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS
    )
    b = _variant("gev_hottest_day", trend_shrink=[0.0, 1.0], shrink_log=log_b)(
        perturbed.loc[perturbed["Year"] <= CUTOFF], CUTOFF, YEARS
    )
    assert log_a == log_b and set(log_a) == {CUTOFF}
    pd.testing.assert_frame_equal(
        a.sort_values(KEY).reset_index(drop=True), b.sort_values(KEY).reset_index(drop=True)
    )


def test_hybrid_takes_each_metric_from_its_component() -> None:
    master = make_annual_master()
    train = master.loc[master["Year"] <= CUTOFF]
    components = {
        "annual_avg_temp": {"forecaster": "ocn_normal", "params": {"windows": [10]}},
        "total_precip_in": {"forecaster": "thirty_year_mean"},
        "hottest_day_temp": {"forecaster": "gev_hottest_day", "params": {"trend": False}},
        "cdd": {"forecaster": "ten_year_mean"},
    }
    forecast = _variant("normals_hybrid", components=components)(train, CUTOFF, YEARS)
    assert len(forecast) == 4 * len(METRICS) * len(YEARS)
    ten = resolve_forecaster("ten_year_mean")(train, CUTOFF, YEARS)
    for metric in ("annual_avg_temp", "cdd"):  # a 10-year OCN equals the 10-year mean
        got = forecast.loc[forecast["metric"] == metric].sort_values(KEY)["predicted_value"]
        want = ten.loc[ten["metric"] == metric].sort_values(KEY)["predicted_value"]
        assert got.to_numpy() == pytest.approx(want.to_numpy())
    with pytest.raises(ValueError, match="components"):
        load_all()["normals_hybrid"].build({"components": {"cdd": {"forecaster": "x"}}})
