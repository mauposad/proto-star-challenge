import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.backtest import ensemble_forecaster, resolve_forecaster
from proto_star.climate import METRICS
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import load_all
from proto_star.forecasters.cdd_forcing_p06_p21 import (
    CDD_BASE_F,
    load_co2,
    make_cdd_daily_shift,
    make_cdd_on_temp,
    make_forced_trend_ar1,
    shifted_cdd,
)
from proto_star.paths import PROJECT_ROOT
from proto_star.trial import build_forecasters, load_trial_config

CUTOFF = 2000
YEARS = list(range(2001, 2008))
KEY = ["city_id", "year", "metric"]
CONFIG = PROJECT_ROOT / "configs" / "agent_paper_cdd_forcing_p06_p21.yaml"


def _daily(master: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Daily tmax/tmin whose (tmax + tmin) / 2 has the master's annual level, plus seasons."""
    rng = np.random.default_rng(seed)
    frames = []
    for (city, year), row in master.set_index(["ID", "Year"]).iterrows():
        dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        season = 18.0 * np.sin(2 * np.pi * (dates.day_of_year.to_numpy() - 110) / 365.25)
        tmean = row["Avg Temp"] + 10.0 + season + rng.normal(0.0, 3.0, len(dates))
        frames.append(
            pd.DataFrame(
                {"ID": city, "Name": city, "Date": dates, "tmax": tmean + 8, "tmin": tmean - 8}
            )
        )
    daily = pd.concat(frames, ignore_index=True)
    daily["prcp"] = 0.1
    return daily


def _cdd_from_daily(daily: pd.DataFrame) -> pd.Series:
    tmean = (daily["tmax"].astype("float32") + daily["tmin"].astype("float32")) / 2
    excess = np.maximum(tmean.astype(float) - CDD_BASE_F, 0.0)
    return excess.groupby([daily["ID"], daily["Date"].dt.year]).sum()


@pytest.fixture(scope="module")
def data(tmp_path_factory: pytest.TempPathFactory) -> tuple[pd.DataFrame, Path, Path]:
    master = make_annual_master(n_cities=4, first_year=1950, last_year=2018)
    daily = _daily(master)
    # Make the master's cdd column follow the challenge definition on this daily table.
    cdd = _cdd_from_daily(daily)
    master["cdd"] = cdd.loc[list(zip(master["ID"], master["Year"], strict=True))].to_numpy()
    root = tmp_path_factory.mktemp("cdd_forcing")
    daily_dir = root / "daily"
    daily_dir.mkdir()
    daily.to_parquet(daily_dir / "daily.parquet", index=False)
    co2 = pd.DataFrame({"year": np.arange(1959, 2019)})
    co2["co2_ppm"] = 315.0 + 1.5 * (co2["year"] - 1959)
    co2_file = root / "co2.csv"
    co2.to_csv(co2_file, index=False)
    return master, daily_dir, co2_file


def _train(master: pd.DataFrame) -> pd.DataFrame:
    return master.loc[master["Year"] <= CUTOFF].copy()


def test_shifted_cdd_is_convex_and_linear_mode_is_its_tangent() -> None:
    tmean = np.array([50.0, 64.0, 66.0, 70.0, 80.0, 64.5])
    zero = shifted_cdd(tmean, 2, np.array([0.0]))
    assert zero[0] == pytest.approx((1.0 + 5.0 + 15.0) / 2)
    deltas = np.array([-2.0, 0.0, 1.0, 3.0])
    daily = shifted_cdd(tmean, 2, deltas, mode="daily")
    linear = shifted_cdd(tmean, 2, deltas, mode="linear")
    assert linear[1] == pytest.approx(daily[1])
    # Convexity: the exact recomputation never falls below its tangent.
    assert np.all(daily >= linear - 1e-12)
    assert daily[3] > linear[3]
    # All days above the base: CDD is linear in the shift, so both modes agree.
    hot = np.array([70.0, 75.0, 90.0])
    assert np.allclose(shifted_cdd(hot, 1, deltas), shifted_cdd(hot, 1, deltas, mode="linear"))
    with pytest.raises(ValueError, match="mode"):
        shifted_cdd(tmean, 1, deltas, mode="cubic")


def test_zero_shift_reproduces_the_ten_year_mean_of_cdd(
    data: tuple[pd.DataFrame, Path, Path],
) -> None:
    master, daily_dir, _ = data
    # 10 climatology years and the 10-year mean temperature: delta is exactly zero.
    forecast = make_cdd_daily_shift(clim_years=10, anomaly="recent", daily_dir=str(daily_dir))(
        _train(master), CUTOFF, YEARS
    )
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    assert len(merged) == master["ID"].nunique() * len(METRICS) * len(YEARS)
    assert np.allclose(merged["predicted_value"], merged["predicted_value_base"], atol=1e-3)


@pytest.mark.parametrize(
    "params",
    [
        {"clim_years": 30, "anomaly": "recent"},
        {"clim_years": 10, "anomaly": "trend", "mode": "linear"},
        {"clim_years": 10, "anomaly": "co2"},
        {"clim_years": 10, "anomaly": "regional", "extrap_years": 20},
        {"clim_years": 30, "blend_ridge_weight": 0.5, "ridge_params": {"n_lags": 4}},
    ],
)
def test_shift_changes_only_cdd(
    data: tuple[pd.DataFrame, Path, Path], params: dict[str, object]
) -> None:
    master, daily_dir, co2_file = data
    forecaster = make_cdd_daily_shift(daily_dir=str(daily_dir), co2_file=str(co2_file), **params)
    forecast = forecaster(_train(master), CUTOFF, YEARS)
    base = ensemble_forecaster()(_train(master), CUTOFF, YEARS)
    merged = forecast.merge(base, on=KEY, suffixes=("", "_base"))
    assert len(merged) == len(base) and not forecast.duplicated(KEY).any()
    cdd = merged["metric"] == "cdd"
    assert np.allclose(
        merged.loc[~cdd, "predicted_value"], merged.loc[~cdd, "predicted_value_base"]
    )
    assert not np.allclose(
        merged.loc[cdd, "predicted_value"], merged.loc[cdd, "predicted_value_base"]
    )
    assert (merged.loc[cdd, "predicted_value"] >= 0).all()


def test_no_data_after_the_cutoff_reaches_any_forecaster(
    data: tuple[pd.DataFrame, Path, Path], tmp_path: Path
) -> None:
    master, daily_dir, co2_file = data
    # A second copy of the inputs whose post-cutoff daily, annual and CO2 values are wild.
    daily = pd.read_parquet(daily_dir / "daily.parquet")
    late = daily["Date"].dt.year > CUTOFF
    daily.loc[late, ["tmax", "tmin"]] += 40.0
    (tmp_path / "daily").mkdir()
    daily.to_parquet(tmp_path / "daily" / "daily.parquet", index=False)
    co2 = pd.read_csv(co2_file)
    co2.loc[co2["year"] > CUTOFF, "co2_ppm"] *= 3.0
    co2.to_csv(tmp_path / "co2.csv", index=False)
    changed = master.copy()
    changed.loc[changed["Year"] > CUTOFF, ["Avg Temp", "cdd"]] *= 3.0

    builders = [
        lambda d, c: make_cdd_daily_shift(clim_years=10, anomaly="co2", daily_dir=d, co2_file=c),
        lambda d, c: make_cdd_daily_shift(clim_years=30, anomaly="trend", daily_dir=d),
        lambda d, c: make_cdd_on_temp(temp_source="trend"),
        lambda d, c: make_forced_trend_ar1(forcing="co2", co2_file=c),
        lambda d, c: make_forced_trend_ar1(forcing="regional", extrap_years=20),
    ]
    for build in builders:
        before = build(str(daily_dir), str(co2_file))(_train(master), CUTOFF, YEARS)
        after = build(str(tmp_path / "daily"), str(tmp_path / "co2.csv"))(
            _train(changed), CUTOFF, YEARS
        )
        pd.testing.assert_frame_equal(before, after)


def test_co2_is_cut_at_the_fold_and_rejects_nothing_else(
    data: tuple[pd.DataFrame, Path, Path],
) -> None:
    _, _, co2_file = data
    series = load_co2(co2_file, 1990)
    assert series.index.max() == 1990
    with pytest.raises(ValueError, match="no CO2"):
        load_co2(co2_file, 1950)


def test_forced_trend_recovers_an_exact_linear_forcing(
    data: tuple[pd.DataFrame, Path, Path],
) -> None:
    master, _, co2_file = data
    exact = master.copy()
    co2 = pd.read_csv(co2_file).set_index("year")["co2_ppm"]
    # Temperature exactly linear in log CO2 (no residual): the forecast is the line itself,
    # at CO2 extrapolated linearly (the synthetic CO2 is a straight line, so exactly).
    in_co2 = exact["Year"].isin(co2.index)
    exact.loc[in_co2, "Avg Temp"] = (
        10.0 + 8.0 * np.log(co2.loc[exact.loc[in_co2, "Year"]]).to_numpy()
    )
    forecast = make_forced_trend_ar1(
        forcing="co2", metrics=["annual_avg_temp"], co2_file=str(co2_file)
    )(_train(exact), CUTOFF, YEARS)
    temp = forecast.loc[forecast["metric"] == "annual_avg_temp"].sort_values(KEY)
    expected = 10.0 + 8.0 * np.log(315.0 + 1.5 * (temp["year"].to_numpy() - 1959))
    assert np.allclose(temp["predicted_value"].to_numpy(), expected, atol=1e-6)


def test_cdd_on_temp_recovers_an_exact_relation(data: tuple[pd.DataFrame, Path, Path]) -> None:
    master, _, _ = data
    exact = master.copy()
    exact["cdd"] = 100.0 + 50.0 * exact["Avg Temp"]
    forecast = make_cdd_on_temp(temp_source="recent")(_train(exact), CUTOFF, YEARS)
    base = ensemble_forecaster()(_train(exact), CUTOFF, YEARS)
    temp = base.loc[base["metric"] == "annual_avg_temp", ["city_id", "year", "predicted_value"]]
    cdd = forecast.loc[forecast["metric"] == "cdd"].merge(temp, on=["city_id", "year"])
    assert np.allclose(cdd["predicted_value_x"], 100.0 + 50.0 * cdd["predicted_value_y"])


def test_bad_params_are_rejected() -> None:
    with pytest.raises(ValueError, match="anomaly"):
        make_cdd_daily_shift(anomaly="psychic")
    with pytest.raises(ValueError, match="forcing"):
        make_forced_trend_ar1(forcing="sunspots")
    with pytest.raises(ValueError, match="metrics"):
        make_forced_trend_ar1(metrics=["total_precip_in"])
    with pytest.raises(ValueError, match="temp_source"):
        make_cdd_on_temp(temp_source="co2")
    with pytest.raises(ValueError, match="rejected params"):
        resolve_forecaster(
            "x", variants={"x": {"forecaster": "cdd_daily_shift", "params": {"nope": 1}}}
        )


def test_trial_config_resolves_every_forecaster() -> None:
    assert {"cdd_daily_shift", "cdd_on_temp_p06", "forced_trend_ar1_p21"} <= set(load_all())
    cfg = load_trial_config(CONFIG)
    assert {"current_best", "ten_year_mean", "hybrid_ridge_all_cdd"} <= set(cfg.forecasters)
    assert cfg.submit is not None
    assert set(build_forecasters(cfg)) == set(cfg.forecasters)


def test_co2_download_parser_caps_at_2018() -> None:
    spec = importlib.util.spec_from_file_location(
        "download_noaa_co2", PROJECT_ROOT / "scripts" / "download_noaa_co2.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    text = "# comment\nyear,mean,unc\n2017,406.76,0.12\n2018,408.72,0.12\n2019,411.65,0.12\n"
    frame = module.parse_co2_annual(text)
    assert frame["year"].tolist() == [2017, 2018]
    assert frame["co2_ppm"].tolist() == [406.76, 408.72]
    with pytest.raises(ValueError, match="empty"):
        module.parse_co2_annual("year,mean\n2019,411.0\n")
