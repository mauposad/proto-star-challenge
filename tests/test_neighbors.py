import numpy as np
import pandas as pd
import pytest

from proto_star.data.synthetic import make_climate_master
from proto_star.neighbors import (
    city_coordinates,
    departures,
    distance_matrix_km,
    gaussian_kernel,
    metric_panel,
    nearest_neighbors,
    neighbor_mean,
    neighbor_weights,
    own_anomalies,
)


def _coords() -> pd.DataFrame:
    # Four cities on one meridian, 1 degree of latitude (about 111.2 km) apart, plus a far one.
    return pd.DataFrame(
        {"Lat": [40.0, 41.0, 42.0, 43.0, 30.0], "Lon": [-80.0, -80.0, -80.0, -80.0, -100.0]},
        index=pd.Index(["a", "b", "c", "d", "far"], name="city_id"),
    )


def test_distance_matches_haversine_for_one_degree_of_latitude() -> None:
    km = distance_matrix_km(_coords())
    assert km.loc["a", "b"] == pytest.approx(111.19, abs=0.1)
    assert km.loc["a", "c"] == pytest.approx(2 * km.loc["a", "b"], rel=1e-9)
    assert np.allclose(km.to_numpy(), km.to_numpy().T)
    assert np.allclose(np.diag(km.to_numpy()), 0.0)


def test_nearest_neighbors_excludes_self_and_orders_by_distance() -> None:
    nearest = nearest_neighbors(_coords(), k=2)
    b = nearest.loc[nearest["city_id"] == "b"]
    assert set(b["neighbor_id"]) == {"a", "c"}  # tie at equal distance, broken by id
    assert b["rank"].tolist() == [1, 2]
    a = nearest.loc[nearest["city_id"] == "a"]
    assert a["neighbor_id"].tolist() == ["b", "c"]
    assert (nearest["city_id"] != nearest["neighbor_id"]).all()
    with pytest.raises(ValueError, match="other cities"):
        nearest_neighbors(_coords(), k=5)


def test_gaussian_weights_decay_and_rows_sum_to_one() -> None:
    assert gaussian_kernel(np.array([0.0]), 300.0)[0] == pytest.approx(1.0)
    assert gaussian_kernel(np.array([300.0]), 300.0)[0] == pytest.approx(np.exp(-0.5))
    weights = neighbor_weights(_coords(), bandwidth_km=300.0)
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert (np.diag(weights.to_numpy()) == 0).all()
    assert weights.loc["b", "a"] > weights.loc["b", "d"] > weights.loc["b", "far"]


def test_radius_and_k_restrict_neighbors() -> None:
    within = neighbor_weights(_coords(), radius_km=150.0)
    assert within.loc["a", "b"] == pytest.approx(1.0)  # only b is within 150 km of a
    assert within.loc["far"].sum() == 0.0  # nothing within 150 km: all-zero row
    equal = neighbor_weights(_coords(), k=2)
    assert equal.loc["a", "b"] == pytest.approx(0.5)
    assert equal.loc["a", "c"] == pytest.approx(0.5)


def test_departure_removes_shared_regional_signal() -> None:
    years = list(range(1990, 2000))
    shared = np.linspace(-1.0, 1.0, len(years))
    anomalies = pd.DataFrame([shared, shared, shared + 0.5], index=["a", "b", "c"], columns=years)
    weights = pd.DataFrame(0.5 * (1 - np.eye(3)), index=["a", "b", "c"], columns=["a", "b", "c"])
    dep = departures(anomalies, weights)
    assert np.allclose(dep.loc["c"], 0.5)
    assert np.allclose(dep.loc["a"], -0.25)


def test_neighbor_mean_renormalizes_over_missing_neighbors() -> None:
    anomalies = pd.DataFrame(
        {2000: [np.nan, 2.0, 4.0], 2001: [np.nan, np.nan, np.nan]}, index=["a", "b", "c"]
    )
    weights = pd.DataFrame(
        [[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]],
        index=["a", "b", "c"],
        columns=["a", "b", "c"],
    )
    mean = neighbor_mean(anomalies, weights)
    assert mean.loc["b", 2000] == pytest.approx(4.0)  # a is missing: c gets all the weight
    assert mean.loc["a", 2000] == pytest.approx(3.0)
    assert mean[2001].isna().all()


def test_anomalies_use_train_only_and_ignore_rows_after_cutoff() -> None:
    master = make_climate_master(seed=3)
    cutoff = 1990
    train = master.loc[master["Year"] <= cutoff]
    panel = metric_panel(train, "annual_avg_temp", cutoff)
    assert int(panel.columns.max()) == cutoff
    anomalies = own_anomalies(panel, cutoff, window=30, min_years=10)

    # Rows after the cut-off are refused outright, so they cannot leak into a fold.
    with pytest.raises(ValueError, match="after allowed cutoff"):
        metric_panel(master, "annual_avg_temp", cutoff)
    # Changing values after the cut-off cannot move anything built from the fold.
    poisoned = master.copy()
    poisoned.loc[poisoned["Year"] > cutoff, "Avg Temp"] = 999.0
    fold = poisoned.loc[poisoned["Year"] <= cutoff]
    again = own_anomalies(metric_panel(fold, "annual_avg_temp", cutoff), cutoff)
    pd.testing.assert_frame_equal(anomalies, again)

    window = [y for y in panel.columns if y > cutoff - 30]
    assert np.allclose(anomalies[window].mean(axis=1).dropna(), 0.0)
    with pytest.raises(ValueError, match="after the cut-off"):
        later = master.loc[master["Year"] <= 2000]
        own_anomalies(metric_panel(later, "annual_avg_temp", 2000), cutoff)


def test_ratio_anomalies_and_coordinates_from_train() -> None:
    panel = pd.DataFrame({y: [10.0 if y % 2 else 30.0] for y in range(1971, 2001)}, index=["a"])
    ratio = own_anomalies(panel, 2000, kind="ratio")
    assert ratio.loc["a", 2000] == pytest.approx(30.0 / 20.0 - 1.0)
    coords = city_coordinates(make_climate_master(seed=0))
    assert list(coords.columns) == ["Lat", "Lon"]
    assert coords.index.is_unique
