"""Loaders for third-party reference data joined to the 210 challenge cities.

One module per source. Static sources (census, coastline, land cover) do not respond to
the weather. Weather-responding sources (climate indices, SST, neighbor stations) are
capped at 2018-12-31 when downloaded, and every loader re-checks the cap with
``proto_star.climate.assert_weather_cutoff``.
"""

from proto_star.paths import EXTERNAL_DIR, PROCESSED_DIR

EXTERNAL_PROCESSED_DIR = PROCESSED_DIR / "external"
CITY_STATIC_PATH = EXTERNAL_PROCESSED_DIR / "city_static.parquet"
INDICES_PATH = EXTERNAL_PROCESSED_DIR / "indices_to_2018.parquet"

__all__ = ["CITY_STATIC_PATH", "EXTERNAL_DIR", "EXTERNAL_PROCESSED_DIR", "INDICES_PATH"]
