"""Download HadCRUT4.6.0.0 annual GMST (2019-02-09 archive), keeping only years up to 2018.

The file has no server-side date filter, so it is fetched into memory, every row after 2018
is dropped (``cap_text``) before anything is written or printed, the capped table is checked
with ``assert_weather_cutoff``, and only then written to ``data/external/hadcrut4/``. An
existing file is never overwritten. Prints the byte count, year range and SHA-256 only.

Usage:
  uv run python scripts/download_hadcrut.py
"""

import hashlib
import urllib.request

from proto_star.climate import assert_weather_cutoff
from proto_star.data.external.hadcrut import HADCRUT_FILE, SOURCE_URL, cap_text, parse_annual


def main() -> None:
    if HADCRUT_FILE.exists():
        raise FileExistsError(f"{HADCRUT_FILE} already exists; external data is immutable")
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "proto-star-download"})
    with urllib.request.urlopen(request, timeout=60) as response:  # fixed https URL
        raw = response.read().decode("ascii")
    capped = cap_text(raw)
    del raw  # nothing after 2018 is kept, printed or written
    table = parse_annual(capped)
    assert_weather_cutoff(table, name=HADCRUT_FILE.name)
    HADCRUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = capped.encode("ascii")
    with HADCRUT_FILE.open("xb") as handle:
        handle.write(content)
    digest = hashlib.sha256(content).hexdigest()
    first, last = int(table["year"].min()), int(table["year"].max())
    print(f"Wrote {HADCRUT_FILE} ({len(content)} bytes, years {first}-{last})")
    print(f"sha256 {digest}")


if __name__ == "__main__":
    main()
