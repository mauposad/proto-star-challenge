import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import Forecaster, pooled_trend_forecaster
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters._pooled_ridge import make_pooled_ridge
from proto_star.forecasters.lead_blend import lead_weight
from proto_star.trend import PooledTrendSpec

KEY = ["city_id", "year", "metric"]
CUTOFF = 2000
YEARS = list(range(2001, 2008))


def _train() -> pd.DataFrame:
    master = make_climate_master(seed=4)
    return master.loc[master["Year"] <= CUTOFF].copy()


def _build(**params: object) -> Forecaster:
    kind = get_kind("lead_blend")
    return kind.build(kind.make_spec(params))


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def test_lead_weight_holds_last_value() -> None:
    weights = [0.5, 0.5, 0.5, 1.0]
    assert [lead_weight(weights, k) for k in range(1, 8)] == [0.5, 0.5, 0.5, 1, 1, 1, 1]
    with pytest.raises(ValueError):
        lead_weight(weights, 0)


def test_lead_split3_mixes_trend_and_ridge_by_lead() -> None:
    train = _train()
    blend = _indexed(_build()(train, CUTOFF, YEARS))
    trend = _indexed(
        pooled_trend_forecaster(
            PooledTrendSpec(level_years=[10, 15], trend_window=40, cdd_sensitivity=True)
        )(train, CUTOFF, YEARS)
    )
    ridge = _indexed(
        make_pooled_ridge(model_metrics=["annual_avg_temp", "cdd"])(train, CUTOFF, YEARS)
    )
    idx = pd.IndexSlice
    for year in YEARS:
        w = 0.5 if year - CUTOFF <= 3 else 1.0
        temp = idx[:, year, "annual_avg_temp"]
        expected = w * trend.loc[temp] + (1 - w) * ridge.loc[temp]
        assert np.allclose(blend.loc[temp], expected)
    cdd = idx[:, :, "cdd"]
    assert np.allclose(blend.loc[cdd], 0.5 * trend.loc[cdd] + 0.5 * ridge.loc[cdd])
    for metric in ("total_precip_in", "hottest_day_temp"):  # metric isolation
        rows = idx[:, :, metric]
        assert np.allclose(blend.loc[rows], trend.loc[rows])


def test_h2_mean_cdd_is_trend_temperature() -> None:
    train = _train()
    h2 = _indexed(_build(temp_trend_weights=[1.0])(train, CUTOFF, YEARS))
    split3 = _indexed(_build()(train, CUTOFF, YEARS))
    later = pd.IndexSlice[:, YEARS[3:], :]
    assert np.allclose(h2.loc[later], split3.loc[later])
    assert np.isfinite(h2).all()


def test_lead_blend_ignores_rows_after_cutoff() -> None:
    master = make_climate_master(seed=4)
    poisoned = master.copy()
    poisoned.loc[poisoned["Year"] > CUTOFF, ["Avg Temp", "cdd"]] = 999.0
    forecaster = _build()
    clean = forecaster(master.loc[master["Year"] <= CUTOFF], CUTOFF, YEARS)
    again = forecaster(poisoned.loc[poisoned["Year"] <= CUTOFF], CUTOFF, YEARS)
    pd.testing.assert_frame_equal(clean, again)


def test_lead_blend_rejects_bad_weights() -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        _build(temp_trend_weights=[1.5])
    with pytest.raises(ValueError, match="rejected params"):
        _build(unknown=1)
