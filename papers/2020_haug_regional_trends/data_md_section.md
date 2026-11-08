<!-- For docs/data.md: add this section under "## Datasets" and the rows under "## Input artifact checksums". -->

### Regional pooling-group attributes (static, papers P22/P24)

- **Download:** `uv run python scripts/download_regional_p22_p24.py` (about 13 MB, a few minutes;
  refuses to overwrite). Writes `data/external/regional_p22_p24/`.
- **Sources and licenses (all public domain U.S. government works):**
  - `ghcnd-stations.txt`: NOAA NCEI GHCN-Daily station inventory,
    `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt`, for station elevation.
    Same file and checksum as the existing `noaa_ghcn_stations` artifact.
  - `Gaz_places_national.zip`: U.S. Census Bureau 2010 Gazetteer of places (2010 Census `POP10`,
    file dated 2012),
    `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_places_national.zip`.
  - `nlcd2016_points.csv`: USGS MRLC NLCD 2016 Land Cover (CONUS), layer
    `NLCD_2016_Land_Cover_L48`, read one pixel at a time with WMS `GetFeatureInfo` from
    `https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms` at 5 points per
    station (centre and +-0.005 degrees N/S/E/W). Used instead of the multi-GB raster.
- **Schema of `city_groups.csv`** (one row per challenge city, 210 rows): `city_id` (GHCN ID, =
  master `ID`), `name`, `state`, `lat`, `lon` (master), `elevation_m` (GHCN), `place_2010`,
  `pop_2010`, `place_distance_km` (most populous 2010 Census place within 20 km of the station;
  the nearest place if none), `nlcd_c/n/s/e/w` (NLCD class codes), `land_cover`
  (majority of the 5 pixels: `developed_high` = 23/24, `developed_low` = 21/22, `undeveloped`).
- **Use:** static city attributes for pooling groups in `regional_trend_p22` and
  `pooled_groups_p24` (elevation, population and land-cover groups only). No weather observations.
  Vintages are pre-2019 (2010 Census, NLCD 2016); GHCN elevation is static station metadata from the
  current inventory. The 2010 and 2016 vintages postdate the 1980 and 1995 backtest cutoffs (mild
  look-ahead in group assignment only).
- **CI:** the publish workflow does not download these files, so a `submit:` forecaster that
  needs them would not rebuild on CI. `submit` in the trial config is `hybrid_ridge_all_cdd`.

| Local artifact | SHA-256 |
|---|---|
| `data/external/regional_p22_p24/ghcnd-stations.txt` | `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` |
| `data/external/regional_p22_p24/Gaz_places_national.zip` | `db63b4ef027f2118221c057b9e4911a4bbda09975bdc4aac7d0c0ba286e04c76` |
| `data/external/regional_p22_p24/nlcd2016_points.csv` | `849f440a17a2e927df8b312ab62933839a742a794c0c1bee3ca1ddd55c349553` |
| `data/external/regional_p22_p24/city_groups.csv` | `4ca0476f2ee85100c041fae40ca746040531c1a8d21432b000c057c07e48ab51` |

Note: `nlcd2016_points.csv` comes from a live web service; a re-download may differ if MRLC
changes the served layer. The checksum above is the version used.
