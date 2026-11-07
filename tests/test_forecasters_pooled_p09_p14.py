import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import backtest_forecaster, ensemble_forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters import load_all
from proto_star.forecasters.pooled_p09_p14 import _make_estimator, make_pooled_median

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
FAST = {"origin_stride": 3, "n_lags": 4}


@pytest.fixture(scope="module")
def master() -> pd.DataFrame:
    return make_annual_master(n_cities=6, first_year=1940, last_year=2018)


def _train(master: pd.DataFrame) -> pd.DataFrame:
    return master.loc[master["Year"] <= CUTOFF].copy()


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"estimator": "ridge", "alpha": 1.0},
        {"estimator": "hgb_quantile", "per_lead": False, "hgb": {"max_iter": 20}},
        {"pool_metrics": True, "per_lead": False},
    ],
)
def test_forecast_covers_every_city_metric_and_year(
    master: pd.DataFrame, params: dict[str, object]
) -> None:
    forecast = make_pooled_median(**FAST, **params)(_train(master), CUTOFF, YEARS)
    assert list(forecast.columns) == [*KEY, "predicted_value"]
    assert not forecast.duplicated(KEY).any()
    assert len(forecast) == master["ID"].nunique() * len(METRICS) * len(YEARS)
    assert set(forecast["year"]) == set(YEARS)
    assert np.isfinite(forecast["predicted_value"]).all()
    # The model is used, not just the fallback.
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    assert not np.allclose(merged["predicted_value"], merged["predicted_value_base"])


def test_values_after_the_cutoff_do_not_change_predictions(master: pd.DataFrame) -> None:
    forecaster = make_pooled_median(**FAST)
    before = forecaster(_train(master), CUTOFF, YEARS)
    changed = master.copy()
    late = changed["Year"] > CUTOFF
    for column in ("Avg Temp", "ToT Prcp", "Max Tmax", "cdd"):
        changed.loc[late, column] = changed.loc[late, column] * 3.0 + 100.0
    # The backtest slices train itself; the forecast must only see that slice.
    after = forecaster(_train(changed), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(before, after)
    # And the scored backtest runs on the changed truth without touching the forecasts.
    scores = backtest_forecaster(forecaster, changed, cutoffs=[CUTOFF])
    assert set(scores["window"]) == {"all", "years_1_3", "years_4_7"}


def test_features_look_backward_only(master: pd.DataFrame) -> None:
    panels = feats.wide_panels(_train(master), CUTOFF)
    wide = panels["annual_avg_temp"]
    full = feats.origin_features(wide, n_lags=3, windows=(5,))
    poked = wide.copy()
    poked[1990] = poked[1990] + 50.0
    changed = feats.origin_features(poked, n_lags=3, windows=(5,))
    early = full["origin"] < 1990
    pd.testing.assert_frame_equal(full.loc[early], changed.loc[early])
    examples = feats.training_examples(
        wide, full, cutoff_year=CUTOFF, leads=[1, 7], train_years=None, origin_stride=1
    )
    assert (examples["target_year"] <= CUTOFF).all()
    assert (examples["target_year"] - examples["origin"]).isin([1, 7]).all()


def test_quantile_objective_fits_the_median_not_the_mean() -> None:
    rng = np.random.default_rng(0)
    n = 400
    frame = pd.DataFrame({"x": rng.standard_normal(n), "region": "A"})
    # Skewed noise: median 0, mean 4.
    noise = np.where(rng.random(n) < 0.8, rng.normal(0, 0.1, n), 20.0)
    target = 2.0 * frame["x"].to_numpy() + noise
    kwargs = {"numeric": ["x"], "categorical": ["region"], "alpha": 0.0, "hgb": {}, "seed": 0}
    median = _make_estimator("quantile_linear", quantile=0.5, **kwargs)
    median.fit(frame, target)
    ols = _make_estimator("ridge", quantile=0.5, **kwargs)
    ols.fit(frame, target)
    zero = pd.DataFrame({"x": [0.0], "region": ["A"]})
    assert abs(median.predict(zero)[0]) < 0.3
    assert ols.predict(zero)[0] > 2.0


def test_params_pass_through_the_registry_and_hybrid_keeps_other_metrics(
    master: pd.DataFrame,
) -> None:
    registry = load_all()
    assert {"pooled_median_p09_p14", "pooled_hybrid_p09_p14"} <= set(registry)
    variants = {
        "hybrid": {
            "forecaster": "pooled_hybrid_p09_p14",
            "params": {"model_metrics": ["cdd"], **FAST},
        }
    }
    hybrid = resolve_forecaster("hybrid", variants=variants)(_train(master), CUTOFF, YEARS)
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    merged = hybrid.merge(base, on=KEY, suffixes=("", "_base"))
    others = merged["metric"] != "cdd"
    assert np.allclose(
        merged.loc[others, "predicted_value"], merged.loc[others, "predicted_value_base"]
    )
    assert not np.allclose(
        merged.loc[~others, "predicted_value"], merged.loc[~others, "predicted_value_base"]
    )
    with pytest.raises(ValueError, match="rejected params"):
        registry["pooled_median_p09_p14"].build({"bogus": 1})
    with pytest.raises(ValueError, match="unknown estimator"):
        make_pooled_median(estimator="magic")
    with pytest.raises(ValueError, match="unknown metrics"):
        make_pooled_median(model_metrics=["rain"])


def test_seeded_boosting_is_reproducible(master: pd.DataFrame) -> None:
    params = {"estimator": "hgb_quantile", "per_lead": False, "hgb": {"max_iter": 15}, "seed": 3}
    first = make_pooled_median(**FAST, **params)(_train(master), CUTOFF, YEARS)
    second = make_pooled_median(**FAST, **params)(_train(master), CUTOFF, YEARS)
    pd.testing.assert_frame_equal(first, second)
