import numpy as np
import pandas as pd
import pytest

from proto_star.climate import annual_to_long
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import chronos_zero_shot as cz
from proto_star.forecasters import get_kind
from proto_star.forecasters.residual_boost import _coords, _switches, origin_features

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
BASE = {"kind": "pooled_trend", "params": {"level_years": [10, 15], "trend_window": 40}}


def _train() -> pd.DataFrame:
    master = make_climate_master(seed=5)
    return master.loc[master["Year"] <= CUTOFF].copy()


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def _residual_boost(**params: object) -> pd.DataFrame:
    kind = get_kind("residual_boost")
    spec = kind.make_spec({"base": BASE, "pseudo_origins": 8, "max_iter": 20, **params})
    return kind.build(spec)(_train(), CUTOFF, YEARS)


def test_residual_boost_with_zero_shrink_equals_its_base() -> None:
    base_kind = get_kind("pooled_trend")
    base = base_kind.build(base_kind.make_spec(BASE["params"]))(_train(), CUTOFF, YEARS)
    boosted = _residual_boost(shrink=0.0)
    pd.testing.assert_series_equal(_indexed(boosted), _indexed(base), check_names=False)


def test_city_target_corrections_have_zero_mean_across_cities() -> None:
    base_kind = get_kind("pooled_trend")
    base = _indexed(base_kind.build(base_kind.make_spec(BASE["params"]))(_train(), CUTOFF, YEARS))
    shift = (_indexed(_residual_boost(target="city")) - base).rename("shift").reset_index()
    means = shift.groupby(["metric", "year"])["shift"].mean()
    assert np.allclose(means.to_numpy(), 0.0, atol=1e-9)


def test_origin_features_ignore_rows_after_the_origin() -> None:
    train = _train()
    origin = 1990
    history = annual_to_long(train, cutoff_year=CUTOFF)
    changed = history.copy()
    changed.loc[changed["year"] > origin, "actual_value"] += 100.0
    first = origin_features(history, origin, _coords(train), _switches(train))
    second = origin_features(changed, origin, _coords(train), _switches(train))
    pd.testing.assert_frame_equal(first, second)


class _LastValuePipeline:
    """Stand-in for a Chronos pipeline: repeats each context's last value."""

    def predict_quantiles(self, contexts, prediction_length, quantile_levels, num_samples):  # type: ignore[no-untyped-def]  # mirrors the chronos API
        import torch

        last = torch.stack([context[-1] for context in contexts])
        values = last[:, None, None].repeat(1, prediction_length, len(quantile_levels))
        return values, values[:, :, 0]


def test_chronos_kind_uses_model_medians_and_falls_back_for_short_series(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("torch")
    revision = "test-revision"
    monkeypatch.setitem(cz._PIPELINES, ("amazon/chronos-t5-small", revision), _LastValuePipeline())
    train = _train()
    short = train["ID"].astype(str) == train["ID"].astype(str).iloc[0]
    train.loc[short & (train["Year"] < CUTOFF - 5), "Avg Temp"] = np.nan
    kind = get_kind("chronos_zero_shot")
    spec = kind.make_spec({"revision": revision, "metrics": ["annual_avg_temp"], "min_years": 10})
    forecast = _indexed(kind.build(spec)(train, CUTOFF, YEARS))
    history = annual_to_long(train, cutoff_year=CUTOFF)
    temp = history.loc[history["metric"] == "annual_avg_temp"]
    city = sorted(set(temp["city_id"]) - {str(train["ID"].iloc[0])})[0]
    last = temp.loc[temp["city_id"] == city].sort_values("year")["actual_value"].iloc[-1]
    assert forecast[(city, 2004, "annual_avg_temp")] == pytest.approx(last, rel=1e-6)
    short_city = str(train["ID"].iloc[0])
    window = temp.loc[(temp["city_id"] == short_city) & (temp["year"] > CUTOFF - 30)]
    assert forecast[(short_city, 2004, "annual_avg_temp")] == pytest.approx(
        window["actual_value"].mean()
    )
