import numpy as np
import pandas as pd

from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters.city_drift import drift_features
from proto_star.neighbors import city_coordinates, metric_panel, neighbor_weights

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
BASE = {"kind": "pooled_trend", "params": {"level_years": [10, 15], "trend_window": 40}}


def _train() -> pd.DataFrame:
    master = make_climate_master(seed=5)
    return master.loc[master["Year"] <= CUTOFF].copy()


def _indexed(frame: pd.DataFrame) -> pd.Series:
    return frame.set_index(KEY)["predicted_value"].sort_index()


def _base() -> pd.Series:
    kind = get_kind("pooled_trend")
    return _indexed(kind.build(kind.make_spec(BASE["params"]))(_train(), CUTOFF, YEARS))


def _drift(**params: object) -> pd.Series:
    kind = get_kind("city_drift")
    spec = kind.make_spec(
        {
            "base": BASE,
            "metrics": ["annual_avg_temp"],
            "k": 3,
            "pseudo_origins": 8,
            "min_fit_rows": 20,
            **params,
        }
    )
    return _indexed(kind.build(spec)(_train(), CUTOFF, YEARS))


def test_zero_shrink_equals_the_base() -> None:
    pd.testing.assert_series_equal(_drift(shrink=0.0), _base(), check_names=False)


def test_correction_is_city_relative_and_touches_only_its_metric() -> None:
    shift = (_drift() - _base()).rename("shift").reset_index()
    temp = shift.loc[shift["metric"] == "annual_avg_temp"]
    assert np.allclose(temp.groupby("year")["shift"].mean().to_numpy(), 0.0, atol=1e-9)
    assert temp["shift"].abs().max() > 0
    assert np.allclose(shift.loc[shift["metric"] != "annual_avg_temp", "shift"], 0.0)


def test_features_ignore_years_after_the_origin_and_see_a_local_step() -> None:
    train = _train()
    weights = neighbor_weights(city_coordinates(train), k=3)
    panel = metric_panel(train, "annual_avg_temp", CUTOFF)
    origin = 1990
    city = panel.index[0]
    stepped = panel.copy()
    stepped.loc[city, [year for year in panel.columns if origin - 5 < year <= origin]] += 3.0
    later = stepped.copy()
    later.loc[:, [year for year in panel.columns if year > origin]] += 100.0
    first = drift_features(stepped, origin, weights, [1, 5, 15], "neighbors")
    second = drift_features(later, origin, weights, [1, 5, 15], "neighbors")
    pd.testing.assert_frame_equal(first, second)
    plain = drift_features(panel, origin, weights, [1, 5, 15], "neighbors")
    gain = first.set_index("city_id").loc[city, "d5"] - plain.set_index("city_id").loc[city, "d5"]
    assert gain > 1.5  # a +3 step in the last 5 years, less its share of the 30-year mean
