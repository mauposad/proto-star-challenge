from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proto_star.climate import ClimateDataError

xr = pytest.importorskip("xarray")

from proto_star.data.external.indices import (  # noqa: E402  # needs xarray (geo extra)
    area_mean,
    check_months,
    combine_indices,
    cpc_pdo_url,
    ersst_array,
    ersst_url,
    fetch_checked,
    load_indices,
    load_sst_grid,
    monthly_anomaly,
    nao_from_slp,
    pdo_from_grid,
)

MONTHS = pd.date_range("1940-01-01", "1990-12-01", freq="MS")


def _grid(values: np.ndarray, lats: list[float], lons: list[float]) -> xr.DataArray:
    return xr.DataArray(
        values, coords={"date": MONTHS, "lat": lats, "lon": lons}, dims=("date", "lat", "lon")
    )


def test_queries_end_in_2018() -> None:
    assert "(2018-12-15)" in ersst_url("nino34")
    assert "time%3C=2018-12-31" in cpc_pdo_url()


def test_leak_check_rejects_2019_months() -> None:
    check_months(pd.date_range("2018-01-01", "2018-12-01", freq="MS"), name="ok")
    with pytest.raises(ClimateDataError, match="2019"):
        check_months(pd.date_range("2018-12-01", "2019-01-01", freq="MS"), name="leaky")


def test_erddap_array_is_checked_before_use() -> None:
    times = pd.to_datetime(["2018-12-15", "2019-01-15"])
    dataset = xr.Dataset(
        {"sst": (("time", "depth", "latitude", "longitude"), np.zeros((2, 1, 1, 1)))},
        coords={"time": times, "depth": [0.0], "latitude": [0.0], "longitude": [190.0]},
    )
    with pytest.raises(ClimateDataError):
        ersst_array(dataset, name="box")
    ok = ersst_array(dataset.isel(time=[0]), name="box")
    assert ok["date"].to_index()[0] == pd.Timestamp("2018-12-01")


def test_fetch_checked_writes_nothing_when_check_fails(tmp_path: Path) -> None:
    destination = tmp_path / "x.nc"

    def reject(content: bytes) -> None:
        raise ClimateDataError("contains year 2019")

    with pytest.raises(ClimateDataError):
        fetch_checked("u", lambda url: b"data", reject, destination)
    assert not destination.exists()
    assert fetch_checked("u", lambda url: b"data", lambda content: None, destination) == 4
    with pytest.raises(FileExistsError):
        fetch_checked("u", lambda url: b"data", lambda content: None, destination)


def test_area_mean_weights_by_latitude_and_skips_land() -> None:
    values = np.zeros((len(MONTHS), 2, 1))
    values[:, 1, 0] = 1.0
    values[0, 0, 0] = np.nan
    mean = area_mean(_grid(values, [0.0, 60.0], [0.0]))
    assert mean.iloc[0] == pytest.approx(1.0)
    assert mean.iloc[1] == pytest.approx(0.5 / 1.5)  # cos 60 = 0.5


def test_monthly_anomaly_uses_base_only() -> None:
    series = pd.Series(np.where(MONTHS.year > 1980, 5.0, 1.0), index=MONTHS)
    anomaly = monthly_anomaly(series)
    assert anomaly[MONTHS.year <= 1980].abs().max() == 0
    assert anomaly[MONTHS.year > 1980].min() == 4.0
    with pytest.raises(ClimateDataError):
        monthly_anomaly(series, base=(2000, 2010))


def test_pdo_recovers_planted_mode_with_conventional_sign() -> None:
    rng = np.random.default_rng(0)
    mode = rng.standard_normal(len(MONTHS))
    lats, lons = [36.0, 40.0, 44.0], [170.0, 180.0, 230.0]
    pattern = np.array([[-1.0, -1.0, 0.5], [-1.0, -2.0, 0.5], [-1.0, -1.0, 0.5]])
    noise = 0.05 * rng.standard_normal((len(MONTHS), 3, 3))
    grid = _grid(10 + mode[:, None, None] * pattern + noise, lats, lons)
    pdo = pdo_from_grid(grid, pd.Series(0.0, index=MONTHS))
    assert np.corrcoef(pdo, mode)[0, 1] > 0.95  # monthly climatology removes a little of the mode
    fit = (MONTHS.year >= 1900) & (MONTHS.year <= 1980)
    assert np.std(pdo[fit].to_numpy()) == pytest.approx(1.0, rel=1e-6)


def test_nao_is_azores_minus_iceland() -> None:
    rng = np.random.default_rng(1)
    azores = 1020 + rng.standard_normal(len(MONTHS))
    values = np.stack([azores, np.full(len(MONTHS), 1000.0) + rng.standard_normal(len(MONTHS))])
    slp = xr.DataArray(
        values.T[:, :, None] * np.ones((1, 1, 2)),
        coords={"date": MONTHS, "lat": [37.5, 65.0], "lon": [335.0, 337.5]},
        dims=("date", "lat", "lon"),
    )
    nao = nao_from_slp(slp)
    assert np.corrcoef(nao, azores)[0, 1] > 0.6
    with pytest.raises(ClimateDataError):
        nao_from_slp(slp.sel(lat=[65.0]))


def test_index_table_and_fold_loader_leak_test(tmp_path: Path) -> None:
    months = pd.date_range("1979-01-01", "2018-12-01", freq="MS")
    table = combine_indices({"oni": pd.Series(0.0, index=months)})
    path = tmp_path / "indices.parquet"
    table.to_parquet(path)
    fold = load_indices(1980, path)
    assert fold["date"].max() == pd.Timestamp("1980-12-01")
    assert load_indices(path=path)["year"].max() == 2018
    leaky = pd.date_range("2018-01-01", "2019-01-01", freq="MS")
    with pytest.raises(ClimateDataError):
        combine_indices({"oni": pd.Series(0.0, index=leaky)})
    leaky_table = pd.concat([table, table.iloc[[-1]].assign(year=2019)], ignore_index=True)
    leaky_table.to_parquet(path)
    with pytest.raises(ClimateDataError):
        load_indices(1980, path)


def test_sst_grid_loader_caps_at_fold_cutoff(tmp_path: Path) -> None:
    times = pd.date_range("1979-01-15", "2018-12-15", freq="MS") + pd.Timedelta(days=14)
    dataset = xr.Dataset(
        {"sst": (("time", "depth", "latitude", "longitude"), np.ones((len(times), 1, 1, 2)))},
        coords={"time": times, "depth": [0.0], "latitude": [0.0], "longitude": [0.0, 4.0]},
    )
    dataset.to_netcdf(tmp_path / "ersstv5_global_4deg_to_2018.nc")
    sst = load_sst_grid(cutoff_year=1995, directory=tmp_path)
    assert sst["date"].to_index().max() == pd.Timestamp("1995-12-01")
    assert sst.dims == ("date", "lat", "lon")
    with pytest.raises(FileNotFoundError):
        load_sst_grid(box="nino34", directory=tmp_path)
