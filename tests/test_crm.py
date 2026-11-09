import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import compare_forecasters, resolve_forecaster
from proto_star.climate import METRICS, annual_to_long
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import get_kind
from proto_star.forecasters._crm_levels import regional_eb_levels, segment_levels
from proto_star.forecasters._crm_urban import load_city_static, urban_gamma, urban_growth
from proto_star.forecasters._crm_var import fit_sparse_var
from proto_star.forecasters.crm import CRMSpec, build_crm, fit_crm, shrunk_regional_trend
from proto_star.trend import PooledTrendSpec

KEY = ["city_id", "year", "metric"]
CHAMPION = PooledTrendSpec(level_years=[10, 15], trend_window=40, cdd_sensitivity=True)
FULL = {
    "regions": "spectral",
    "n_clusters": 3,
    "var": True,
    "var_alpha": 0.1,
    "var_city_scale": True,
    "flat_level": "regional_eb",
    "urban": True,
}


def _master() -> pd.DataFrame:
    """Twelve cities, two per region, so regions and clusters have more than one member."""
    first = make_climate_master(seed=1)
    second = make_climate_master(seed=2)
    second["ID"] = second["ID"] + "_b"
    second["Lat"] = second["Lat"] + 1.0
    second["Avg Temp"] = second["Avg Temp"] + 0.02 * (second["Year"] - 1950)
    return pd.concat([first, second], ignore_index=True)


def _static(master: pd.DataFrame) -> pd.DataFrame:
    ids = sorted(master["ID"].unique())
    rng = np.random.default_rng(0)
    table = pd.DataFrame({"ID": ids})
    pop = 1e5 * (1 + rng.random(len(ids)))
    for year in (1970, 1980, 1990, 2000, 2010, 2020):
        pop = pop * (1 + 0.3 * rng.random(len(ids)))
        table[f"pop_{year}"] = pop
    return table


def _run(forecaster, master: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    train = master.loc[master["Year"] <= cutoff].copy()
    years = list(range(cutoff + 1, cutoff + 8))
    return forecaster(train, cutoff, years).set_index(KEY).sort_index()


def test_crm_is_registered_and_describes_itself() -> None:
    kind = get_kind("crm")
    spec = kind.make_spec(FULL)
    assert "spectral" in spec.describe() and "VAR" in spec.describe()
    with pytest.raises(ValueError, match="crm"):
        kind.make_spec({"no_such_setting": 1})


@pytest.mark.parametrize("regions", ["fixed", "spectral"])
def test_k_scale_zero_equals_the_champion(regions: str) -> None:
    master = _master()
    champion = resolve_forecaster("c", pooled_trends={"c": CHAMPION})
    crm = build_crm(CRMSpec(regions=regions, n_clusters=3, k_scale=0.0))
    for cutoff in (1995, 2011):
        expected = _run(champion, master, cutoff)
        got = _run(crm, master, cutoff)
        assert got.index.equals(expected.index)
        np.testing.assert_allclose(got["predicted_value"], expected["predicted_value"])


def test_forecast_ignores_rows_after_the_cutoff() -> None:
    master = _master()
    static = _static(master)
    altered = master.copy()
    late = altered["Year"] > 1995
    altered.loc[late, ["Avg Temp", "cdd", "Max Tmax", "ToT Prcp"]] *= 3.0
    altered_static = static.assign(pop_2000=static["pop_2000"] * 50, pop_2010=1.0)
    spec = CRMSpec(**FULL)
    before = _run(build_crm(spec, static), master, 1995)
    after = _run(build_crm(spec, altered_static), altered, 1995)
    pd.testing.assert_frame_equal(before, after)


def test_full_crm_backtests_on_every_metric() -> None:
    master = _master()
    forecaster = build_crm(CRMSpec(**FULL), _static(master))
    results = compare_forecasters({"crm": forecaster}, master, cutoffs=[1995])
    assert set(results["window"]) == {"all", "years_1_3", "years_4_7"}
    assert np.isfinite(results["raw_score"]).all()


def test_shrinkage_weights_stay_between_pooled_and_regional() -> None:
    master = _master()
    history = annual_to_long(master.loc[master["Year"] <= 2011], cutoff_year=2011)
    regions = master.groupby("ID")["region"].first().astype(str)
    trend = shrunk_regional_trend(history, "annual_avg_temp", 2011, CRMSpec(), regions)
    table = trend.table
    assert ((table["k"] >= 0) & (table["k"] <= 1)).all()
    low = np.minimum(trend.pooled, table["beta"]).clip(lower=0) - 1e-12
    high = np.maximum(trend.pooled, table["beta"]) + 1e-12
    assert ((table["beta_final"] >= low) & (table["beta_final"] <= high)).all()


def test_spectral_clusters_are_recomputed_per_fold_with_k_groups() -> None:
    master = _master()
    train = master.loc[master["Year"] <= 1995]
    history = annual_to_long(train, cutoff_year=1995)
    fit = fit_crm(train, history, 1995, CRMSpec(regions="spectral", n_clusters=3))
    assert fit.city_region.nunique() == 3
    assert set(fit.city_region.index) == set(master["ID"])


def test_sparse_var_finds_a_planted_persistence() -> None:
    rng = np.random.default_rng(0)
    n_years, columns = 80, pd.MultiIndex.from_product([["r1", "r2"], ["a", "b"]])
    values = np.zeros((n_years, 4))
    for t in range(1, n_years):
        values[t] = rng.normal(0, 1, 4)
        values[t, 0] += 0.8 * values[t - 1, 0]  # only r1/a remembers last year
    fit = fit_sparse_var(pd.DataFrame(values, columns=columns), alpha=0.1, seed=0)
    assert fit.coefficients[0, 0] > 0.4
    assert np.abs(fit.coefficients[1:, 1:]).max() < 0.2
    shifts = fit.shifts([1, 7], damping=1.0)
    assert abs(shifts.iloc[0][7]) < abs(shifts.iloc[0][1])
    assert (fit.shifts([1], damping=0.0).to_numpy() == 0).all()


def test_segment_level_uses_only_the_current_station() -> None:
    years = list(range(1989, 2019))
    history = pd.DataFrame(
        {"city_id": "A", "year": years, "metric": "total_precip_in", "actual_value": 0.0}
    )
    history.loc[history["year"] >= 2000, "actual_value"] = 10.0
    segments = pd.DataFrame({"city_id": "A", "year": years, "segment": 1})
    segments.loc[segments["year"] >= 2000, "segment"] = 2
    levels = segment_levels(history, segments, "total_precip_in", 2018, min_years=15)
    assert levels["A"] == pytest.approx(10.0)
    assert segment_levels(history, segments, "total_precip_in", 2018, min_years=25).empty


def test_regional_eb_fills_a_gappy_city_from_its_region() -> None:
    years = np.arange(1989, 2019)
    shared = np.where(years < 2004, -2.0, 2.0)  # a regional dry half then wet half
    rng = np.random.default_rng(0)
    frames = []
    for city in ("A", "B", "C"):
        values = 30.0 + shared + rng.normal(0, 0.5, len(years))
        frames.append(pd.DataFrame({"city_id": city, "year": years, "metric": "m"}))
        frames[-1]["actual_value"] = values
    history = pd.concat(frames, ignore_index=True)
    history.loc[(history["city_id"] == "C") & (history["year"] < 2004), "actual_value"] = np.nan
    history = history.dropna()
    region = pd.Series("R", index=["A", "B", "C"])
    levels = regional_eb_levels(history, region, "m", 2018)
    complete = history.loc[history["city_id"] == "A", "actual_value"].mean()
    assert levels["A"] == pytest.approx(complete)
    # C saw only the wet half (raw mean near 32); its region says the full-window mean is lower.
    gappy = history.loc[history["city_id"] == "C", "actual_value"].mean()
    assert levels["C"] < gappy - 1.0


def test_urban_growth_uses_only_censuses_up_to_the_cutoff(tmp_path) -> None:
    master = _master()
    static = _static(master)
    path = tmp_path / "city_static.parquet"
    static.to_parquet(path)
    loaded = load_city_static(path)
    growth = urban_growth(loaded, 1995)
    expected = np.log(static["pop_1990"] / static["pop_1980"]).to_numpy()
    np.testing.assert_allclose(growth.reindex(static["ID"]).to_numpy(), expected)
    assert urban_growth(loaded, 1975).empty
    with pytest.raises(FileNotFoundError):
        load_city_static(tmp_path / "missing.parquet")


def test_urban_gamma_recovers_a_planted_offset() -> None:
    rng = np.random.default_rng(0)
    growth = pd.Series(rng.normal(0, 0.2, 40), index=[f"c{i}" for i in range(40)])
    rows = []
    for city, g in growth.items():
        x = np.arange(-20, 20, dtype=float)
        slope = 0.03 + 0.05 * (g - growth.mean())
        rows.append(pd.DataFrame({"city_id": city, "x": x, "y": slope * x}))
    anomalies = pd.concat(rows, ignore_index=True)
    gamma, _ = urban_gamma(anomalies, pd.Series(0.03, index=growth.index), growth)
    assert gamma == pytest.approx(0.05)


def test_every_metric_is_forecast_for_every_city() -> None:
    master = _master()
    out = _run(build_crm(CRMSpec(**FULL), _static(master)), master, 2011).reset_index()
    assert set(out["metric"]) == set(METRICS)
    assert out.groupby("metric")["city_id"].nunique().eq(master["ID"].nunique()).all()
    assert np.isfinite(out["predicted_value"]).all()
