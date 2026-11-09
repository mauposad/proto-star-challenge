"""Download NOAA ERSSTv5 boxes from ERDDAP, capped at 2018-12 by the query itself.

ERSSTv5 responds to the weather, so each request is a server-side time-limited griddap
query ending 2018-12-15 (ERSSTv5 stamps months on the 15th). Every response is opened
and checked with ``assert_weather_cutoff`` *before* it is written; a response reaching
2019 is never saved. Files already present are left untouched (external data is
immutable). One download at a time.
"""

import hashlib
import io
from collections.abc import Callable

import requests
import xarray as xr

from proto_star.data.external.indices import (
    ERDDAP_ERSST,
    ERSST_BOXES,
    ERSST_DIR,
    ersst_array,
    ersst_url,
    fetch_checked,
)


def _get(url: str) -> bytes:
    response = requests.get(url, timeout=600)
    response.raise_for_status()
    return response.content


def _checker(box: str) -> Callable[[bytes], None]:
    def check(content: bytes) -> None:
        with xr.open_dataset(io.BytesIO(content), engine="scipy") as dataset:
            sst = ersst_array(dataset, name=box)
            dates = sst["date"].to_index()
            print(f"  {box}: {dates.min():%Y-%m} to {dates.max():%Y-%m}, shape {sst.shape}")

    return check


def main() -> None:
    ERSST_DIR.mkdir(parents=True, exist_ok=True)
    for box in ERSST_BOXES:
        path = ERSST_DIR / f"ersstv5_{box}_to_2018.nc"
        if path.exists():
            print(f"kept     {path.name} (already present)")
            continue
        url = ersst_url(box)
        size = fetch_checked(url, _get, _checker(box), path)
        print(f"fetched  {path.name} ({size:,} bytes) from {url}")
    source = ERSST_DIR / "SOURCE.txt"
    if not source.exists():
        source.write_text(
            "\n".join(
                [
                    f"source={ERDDAP_ERSST} (NOAA NCEI ERSSTv5 via NOAA CoastWatch ERDDAP)",
                    *(f"query={ersst_url(box)}" for box in ERSST_BOXES),
                    "license=public domain U.S. government work; ERDDAP: no constraints",
                    "cap=server-side time constraint ending 2018-12-15, checked before writing",
                    "downloaded_by=scripts/download_ersst.py",
                    "",
                ]
            )
        )
    for path in sorted(ERSST_DIR.iterdir()):
        print(f"sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    main()
