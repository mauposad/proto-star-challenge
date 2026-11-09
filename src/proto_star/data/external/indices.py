"""Monthly climate indices (ONI-style Nino 3.4, PDO, AMO, NAO), capped at 2018-12.

These respond to the weather, so every download is a server-side, date-limited query
that ends in 2018-12 (ERDDAP time constraints, OPeNDAP index ranges), the result is
checked with :func:`proto_star.climate.assert_weather_cutoff` before it is written, and
:func:`load_indices` checks again on every read.

To keep every value usable in every backtest fold (cut-offs 1980, 1995, 2011), the
indices computed here use only base periods that end by 1980:

- ``nino34_anom``: ERSSTv5 area mean over 5S-5N, 170W-120W, minus its 1951-1980 monthly
  climatology. ``oni`` is its *trailing* 3-month mean (CPC's ONI is centred, which would
  read the next month, and CPC's recent base periods use 1991-2020 data).
- ``amo``: North Atlantic (0-60N, 80W-0) minus 60S-60N mean ERSSTv5 anomaly (Trenberth
  and Shea 2006 form, so no detrending over the full record is needed), 1951-1980 base.
- ``pdo``: leading EOF of North Pacific (20N-60N, 120E-100W) ERSSTv5 anomalies, with the
  global (60S-60N) mean removed, fitted on 1900-1980 and projected on all months;
  normalised by its 1900-1980 standard deviation.
- ``pdo_cpc``: NOAA CPC/PSL PDO via the CCIEA ERDDAP (EOF and climatology from 1900-1993
  ERSST v3b), for comparison. Its normalisation period is not documented.
- ``nao``: standardised sea-level pressure difference, Azores (37.5N, 25W) minus Iceland
  (65N, 22.5W) grid points of NCEP/NCAR Reanalysis 1, 1951-1980 base (from 1948),
  re-scaled to unit variance over the base.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from proto_star.climate import FORECAST_CUTOFF, ClimateDataError, assert_weather_cutoff
from proto_star.data.external import INDICES_PATH
from proto_star.paths import EXTERNAL_DIR

ERSST_DIR = EXTERNAL_DIR / "ersst_v5"
INDICES_DIR = EXTERNAL_DIR / "climate_indices"
BASE_YEARS = (1951, 1980)
PDO_EOF_YEARS = (1900, 1980)

ERDDAP_ERSST = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/nceiErsstv5"
ERDDAP_CPC_PDO = "https://oceanview.pfeg.noaa.gov/erddap/tabledap/cciea_OC_PDO"
NCEP_R1_SLP = (
    "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.derived/surface/slp.mon.mean.nc"
)
LAST_MONTH = f"{FORECAST_CUTOFF}-12-15"  # ERSSTv5 stamps months on the 15th

# name: (lat_min, lat_max, lon_min, lon_max, stride, first_month); lon in 0-358 E.
ERSST_BOXES: dict[str, tuple[float, float, float, float, int, str]] = {
    "nino34": (-4.0, 4.0, 190.0, 240.0, 1, "1854-01-15"),
    "north_atlantic": (0.0, 60.0, 280.0, 358.0, 1, "1854-01-15"),
    "north_pacific": (20.0, 60.0, 120.0, 260.0, 1, "1854-01-15"),
    "global_4deg": (-88.0, 88.0, 0.0, 356.0, 2, "1854-01-15"),
}
NAO_POINTS = {"azores": (37.5, 335.0), "iceland": (65.0, 337.5)}
SLP_BOX = (30.0, 70.0, 300.0, 357.5)  # lat_min, lat_max, lon_min, lon_max


def ersst_url(box: str) -> str:
    """ERDDAP griddap NetCDF query for one ERSSTv5 box, ending at 2018-12."""
    lat_min, lat_max, lon_min, lon_max, stride, first = ERSST_BOXES[box]
    return (
        f"{ERDDAP_ERSST}.nc?sst%5B({first}):1:({LAST_MONTH})%5D%5B(0.0)%5D"
        f"%5B({lat_min}):{stride}:({lat_max})%5D%5B({lon_min}):{stride}:({lon_max})%5D"
    )


def cpc_pdo_url() -> str:
    """ERDDAP tabledap CSV query for the CPC PDO, ending at 2018-12-31."""
    return f"{ERDDAP_CPC_PDO}.csv?time%2CPDO&time%3C={FORECAST_CUTOFF}-12-31T23%3A59%3A59Z"


def check_months(times: Iterable[object], *, name: str) -> None:
    """Reject a downloaded series that reaches past the 2018 cut-off."""
    assert_weather_cutoff(pd.DataFrame({"date": pd.DatetimeIndex(list(times))}), name=name)


def _monthly_dates(values: np.ndarray) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(values).to_period("M").to_timestamp()


def ersst_array(dataset: xr.Dataset, *, name: str) -> xr.DataArray:
    """``sst(date, lat, lon)`` from an ERDDAP ERSSTv5 file, checked at 2018-12."""
    sst = dataset["sst"]
    if "depth" in sst.dims:
        sst = sst.squeeze("depth", drop=True)
    sst = sst.rename({"time": "date", "latitude": "lat", "longitude": "lon"})
    sst = sst.assign_coords(date=_monthly_dates(sst["date"].values))
    check_months(sst["date"].to_index(), name=name)
    return sst


def read_ersst(path: Path) -> xr.DataArray:
    """Read one downloaded ERSSTv5 box into memory (the files are a few MB each)."""
    with xr.open_dataset(path) as dataset:
        return ersst_array(dataset, name=path.name).load()


def load_sst_grid(
    box: str = "global_4deg", cutoff_year: int = FORECAST_CUTOFF, directory: Path = ERSST_DIR
) -> xr.DataArray:
    """ERSSTv5 ``sst(date, lat, lon)`` for one downloaded box, up to December of cutoff_year.

    ``global_4deg`` is the whole ocean on every second 2-degree cell (4 degrees), 1854 on.
    The file is checked against the 2018 cap, the months after ``cutoff_year`` are
    dropped, and the result is checked against ``cutoff_year`` (use the fold cut-off).
    """
    path = directory / f"ersstv5_{box}_to_2018.nc"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `uv run python scripts/download_ersst.py`.")
    sst = read_ersst(path)
    sst = sst.sel(date=sst["date"].dt.year <= cutoff_year)
    check_cutoff = pd.DataFrame({"date": sst["date"].to_index()})
    assert_weather_cutoff(check_cutoff, name=path.name, cutoff_year=cutoff_year)
    return sst


def area_mean(sst: xr.DataArray) -> pd.Series:
    """Cos-latitude weighted mean per month, ignoring land / missing cells."""
    lat = sst["lat"]
    weights = xr.DataArray(np.cos(np.radians(lat.to_numpy())), coords={"lat": lat}, dims="lat")
    mean = sst.weighted(weights).mean(("lat", "lon"), skipna=True)
    return pd.Series(mean.to_numpy(), index=sst["date"].to_index(), name="sst")


def monthly_anomaly(series: pd.Series, base: tuple[int, int] = BASE_YEARS) -> pd.Series:
    """Subtract the base-period mean of each calendar month (index must be dates)."""
    index = pd.DatetimeIndex(series.index)
    in_base = (index.year >= base[0]) & (index.year <= base[1])
    climatology = series[in_base].groupby(index[in_base].month).mean()
    if len(climatology) != 12:
        raise ClimateDataError(f"base period {base} does not cover all 12 months")
    return series - climatology.reindex(index.month).to_numpy()


def pdo_from_grid(
    north_pacific: xr.DataArray,
    global_mean_anomaly: pd.Series,
    *,
    eof_years: tuple[int, int] = PDO_EOF_YEARS,
) -> pd.Series:
    """Leading-EOF PDO index; pattern and scale use only ``eof_years``.

    Anomalies are relative to the ``eof_years`` monthly climatology with the global mean
    anomaly removed (Mantua et al. 1997). Sign is set so the pattern is negative in the
    central North Pacific (40N, 180), the usual PDO convention.
    """
    stacked = north_pacific.stack(cell=("lat", "lon")).transpose("date", "cell")  # noqa: PD013  # xarray stack, not pandas
    values = stacked.to_numpy().astype(float)
    full = ~np.isnan(values).any(axis=0)  # cells with a full record only
    values = values[:, full]
    lats = stacked["lat"].to_numpy()[full]
    lons = stacked["lon"].to_numpy()[full]
    index = pd.DatetimeIndex(stacked["date"].to_index())
    fit = np.asarray((index.year >= eof_years[0]) & (index.year <= eof_years[1]))
    months = np.asarray(index.month)
    anomalies = np.empty_like(values)
    for month in range(1, 13):
        rows = months == month
        anomalies[rows] = values[rows] - values[rows & fit].mean(axis=0)
    anomalies -= global_mean_anomaly.reindex(index).to_numpy()[:, None]
    matrix = anomalies * np.sqrt(np.cos(np.radians(lats)))
    _, _, vt = np.linalg.svd(matrix[fit], full_matrices=False)
    pattern = vt[0]
    central = (np.abs(lats - 40) <= 4) & (np.abs(lons - 180) <= 10)
    if central.any() and pattern[central].mean() > 0:
        pattern = -pattern
    projection = matrix @ pattern
    return pd.Series(projection / projection[fit].std(), index=index, name="pdo")


def read_cpc_pdo(path: Path) -> pd.Series:
    """Read the CPC PDO CSV from ERDDAP (second line holds units)."""
    table = pd.read_csv(path, skiprows=[1])
    dates = pd.to_datetime(table["time"]).dt.tz_localize(None).dt.to_period("M").dt.to_timestamp()
    check_months(dates, name=path.name)
    return pd.Series(table["PDO"].to_numpy(dtype=float), index=dates, name="pdo_cpc")


def read_slp_box(path: Path) -> xr.DataArray:
    """Read the NCEP R1 sea-level pressure box as ``slp(date, lat, lon)``."""
    with xr.open_dataset(path) as dataset:
        slp = dataset["slp"].rename({"time": "date"}).load()
    slp = slp.assign_coords(date=_monthly_dates(slp["date"].values))
    check_months(slp["date"].to_index(), name=path.name)
    return slp


def nao_from_slp(slp: xr.DataArray, base: tuple[int, int] = BASE_YEARS) -> pd.Series:
    """Azores minus Iceland SLP, each standardised by calendar month over ``base``.

    The difference is re-scaled to unit standard deviation over ``base``.
    """
    standardised = []
    for lat, lon in NAO_POINTS.values():
        try:
            point = slp.sel(lat=lat, lon=lon).to_series()
        except KeyError as error:
            raise ClimateDataError(f"SLP grid has no point at {lat}N {lon}E") from error
        index = pd.DatetimeIndex(point.index)
        in_base = (index.year >= base[0]) & (index.year <= base[1])
        groups = point[in_base].groupby(index[in_base].month)
        mean = groups.mean().reindex(index.month).to_numpy()
        std = groups.std().reindex(index.month).to_numpy()
        standardised.append((point - mean) / std)
    difference = standardised[0] - standardised[1]
    index = pd.DatetimeIndex(difference.index)
    in_base = (index.year >= base[0]) & (index.year <= base[1])
    return (difference / difference[in_base].std()).rename("nao")


def combine_indices(series: dict[str, pd.Series]) -> pd.DataFrame:
    """Align monthly series into ``date, year, month, <index>...`` and check the cap."""
    table = pd.concat(series, axis=1).sort_index()
    table.index = pd.DatetimeIndex(table.index, name="date")
    table = table.reset_index()
    table.insert(1, "year", table["date"].dt.year)
    table.insert(2, "month", table["date"].dt.month)
    assert_weather_cutoff(table, name="climate indices")
    return table


def build_monthly_indices(
    ersst_dir: Path = ERSST_DIR, indices_dir: Path = INDICES_DIR
) -> pd.DataFrame:
    """Compute the monthly index table from the downloaded files."""
    paths = {box: ersst_dir / f"ersstv5_{box}_to_2018.nc" for box in ERSST_BOXES}
    paths["cpc_pdo"] = indices_dir / "cpc_pdo_to_2018.csv"
    paths["slp"] = indices_dir / "ncep_r1_slp_natl_to_2018.nc"
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"{missing} not found. Run `uv run python scripts/download_ersst.py` and "
            "`uv run python scripts/download_climate_indices.py`."
        )
    global_grid = read_ersst(paths["global_4deg"])
    global_anomaly = monthly_anomaly(area_mean(global_grid.where(abs(global_grid["lat"]) <= 60)))
    del global_grid
    # asfreq: the ERDDAP copy lacks 1902-10, so the 3-month mean must not bridge gaps
    nino34 = monthly_anomaly(area_mean(read_ersst(paths["nino34"]))).asfreq("MS")
    north_atlantic = monthly_anomaly(area_mean(read_ersst(paths["north_atlantic"])))
    pdo = pdo_from_grid(read_ersst(paths["north_pacific"]), global_anomaly)
    return combine_indices(
        {
            "nino34_anom": nino34,
            "oni": nino34.rolling(3).mean(),
            "amo": north_atlantic - global_anomaly,
            "pdo": pdo,
            "pdo_cpc": read_cpc_pdo(paths["cpc_pdo"]),
            "nao": nao_from_slp(read_slp_box(paths["slp"])),
        }
    )


def load_indices(cutoff_year: int = FORECAST_CUTOFF, path: Path = INDICES_PATH) -> pd.DataFrame:
    """Monthly indices up to December of ``cutoff_year`` (use the fold cut-off).

    The file is checked against the 2018 cap, then the rows after ``cutoff_year`` are
    dropped and the result is checked against ``cutoff_year`` as well.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the index downloads, then "
            "`uv run python scripts/build_external_tables.py` (see docs/data.md)."
        )
    table = pd.read_parquet(path)
    assert_weather_cutoff(table, name=path.name)
    table = table[table["year"] <= cutoff_year].reset_index(drop=True)
    assert_weather_cutoff(table, name=path.name, cutoff_year=cutoff_year)
    return table


def fetch_checked(
    url: str, get: Callable[[str], bytes], check: Callable[[bytes], None], destination: Path
) -> int:
    """Download ``url`` into memory, run ``check`` on it, then write it once.

    Returns the byte count. Refuses to overwrite: external data is immutable.
    """
    if destination.exists():
        raise FileExistsError(f"{destination} already exists; external data is immutable")
    content = get(url)
    check(content)
    destination.write_bytes(content)
    return len(content)
