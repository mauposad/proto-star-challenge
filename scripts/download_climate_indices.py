"""Download the CPC PDO (ERDDAP) and a North Atlantic NCEP R1 sea-level pressure box.

Both respond to the weather, so each request ends in 2018-12 on the server side: an
ERDDAP ``time<=2018-12-31`` constraint for the PDO, and an OPeNDAP time-index range
that stops at the last 2018 month for the pressure box (only the coordinate axis is read
to find that index). Every response is checked with ``assert_weather_cutoff`` before it
is written. Files already present are left untouched. ONI, AMO and the ERSST-based PDO
are computed from the ERSSTv5 boxes (``scripts/download_ersst.py``).
"""

import hashlib
import io

import pandas as pd
import requests
import xarray as xr

from proto_star.climate import FORECAST_CUTOFF
from proto_star.data.external.indices import (
    INDICES_DIR,
    NCEP_R1_SLP,
    SLP_BOX,
    check_months,
    cpc_pdo_url,
    fetch_checked,
    read_cpc_pdo,
)


def _get(url: str) -> bytes:
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    return response.content


def _check_pdo(content: bytes) -> None:
    table = pd.read_csv(io.BytesIO(content), skiprows=[1])
    dates = pd.to_datetime(table["time"]).dt.tz_localize(None)
    check_months(dates, name="cpc_pdo")
    print(f"  cpc_pdo: {dates.min():%Y-%m} to {dates.max():%Y-%m}, {len(table)} months")


def download_slp(destination_name: str = "ncep_r1_slp_natl_to_2018.nc") -> str:
    """Subset the NCEP R1 monthly SLP over OPeNDAP, ending at the last 2018 month."""
    path = INDICES_DIR / destination_name
    if path.exists():
        print(f"kept     {path.name} (already present)")
        return ""
    lat_min, lat_max, lon_min, lon_max = SLP_BOX
    with xr.open_dataset(NCEP_R1_SLP) as remote:
        times = pd.DatetimeIndex(remote["time"].to_numpy())
        last = int((times.year <= FORECAST_CUTOFF).nonzero()[0].max())
        lats, lons = remote["lat"].to_numpy(), remote["lon"].to_numpy()
        lat_idx = ((lats >= lat_min) & (lats <= lat_max)).nonzero()[0]
        lon_idx = ((lons >= lon_min) & (lons <= lon_max)).nonzero()[0]
        subset = remote["slp"].isel(
            time=slice(0, last + 1),
            lat=slice(int(lat_idx.min()), int(lat_idx.max()) + 1),
            lon=slice(int(lon_idx.min()), int(lon_idx.max()) + 1),
        )
        subset = subset.load()
    check_months(subset["time"].to_index(), name="ncep_r1_slp")
    subset.to_dataset(name="slp").to_netcdf(path)
    dates = subset["time"].to_index()
    query = (
        f"{NCEP_R1_SLP}?slp[0:{last}][{lat_idx.min()}:{lat_idx.max()}]"
        f"[{lon_idx.min()}:{lon_idx.max()}]"
    )
    print(
        f"fetched  {path.name} {dates.min():%Y-%m} to {dates.max():%Y-%m}, "
        f"shape {subset.shape}, via {query}"
    )
    return query


def main() -> None:
    INDICES_DIR.mkdir(parents=True, exist_ok=True)
    pdo_path = INDICES_DIR / "cpc_pdo_to_2018.csv"
    if pdo_path.exists():
        print(f"kept     {pdo_path.name} (already present)")
    else:
        size = fetch_checked(cpc_pdo_url(), _get, _check_pdo, pdo_path)
        print(f"fetched  {pdo_path.name} ({size:,} bytes) from {cpc_pdo_url()}")
        read_cpc_pdo(pdo_path)
    slp_query = download_slp()
    source = INDICES_DIR / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    f"source={cpc_pdo_url()} (NOAA CPC PDO via CCIEA ERDDAP)",
                    f"source={slp_query or NCEP_R1_SLP} (NCEP/NCAR Reanalysis 1, NOAA PSL)",
                    "license=public domain U.S. government work",
                    "cap=server-side date limit ending 2018-12, checked before writing",
                    "downloaded_by=scripts/download_climate_indices.py",
                    "",
                ]
            )
        )
    for path in sorted(INDICES_DIR.iterdir()):
        print(f"sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    main()
