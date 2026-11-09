# Data

Data files are **never committed**. This page is the source of truth for what data we use and
how to reproduce it.

## Directory conventions

| Path | Contents | Rules |
|---|---|---|
| `data/raw/` | Source data exactly as downloaded | Immutable. Only download scripts write here |
| `data/external/` | Third-party reference data (e.g. station metadata, land cover) | Immutable |
| `data/interim/` | Cleaned / joined intermediate data | Regenerable from scripts |
| `data/processed/` | Final model-ready tables | Regenerable from scripts |

Prefer **Parquet** for tabular data (typed, compressed, fast). Use NetCDF/Zarr for gridded
data (`uv sync --extra geo`).

## Datasets

<!-- Add one section per dataset. Keep it current. -->

### synthetic (development only)

- **Source:** `scripts/make_synthetic_data.py`
- **Files:** `data/raw/synthetic/{train,test}.parquet`
- **Schema:** `id` (int), `date` (date), `station_id` (int), `humidity` (float, %),
  `pressure` (float, hPa), `max_temp` (float, °C, **target**, train only)

### CMU ProtoStar climate training data

- **Source / URL:** `CMU-OSPO/protostar-climate-train-to-2018` on Hugging Face;
  original records: Lai & Dzombak (2019), DOI
  [10.1184/R1/7890488.v6](https://doi.org/10.1184/R1/7890488.v6).
- **Download:** `uv run python scripts/download_protostar_data.py`. Downloads
  `annual_indices`, `city_info`, `daily` (~10M rows, ~50 MB parquet) and
  `coverage_and_stations`. Tables already present are left untouched (only missing ones are
  written), and every table is rejected if it has observations after 2018.
- **Files:** `data/raw/protostar/<table>.parquet`.
  - `daily`: `ID`, `Name`, `Date`, `tmax`/`tmin` (°F), `prcp` (in). This is a complete calendar,
    and missing values are NaN.
  - `coverage_and_stations`: one row per city-year with `Days Both` (days with both tmax and tmin
    observed), `Station Segment` (1-based station thread in use) and `Station Changes`
    (switches that year).
  - Loaders are in `proto_star.data.protostar`.
- **License:** CC0-1.0.
- **Temporal / spatial coverage:** 210 U.S. cities, historical values through
  2018-12-31 only.
- **Targets / units:** annual average temperature (°F), total precipitation
  (inches), hottest-day temperature (°F), cooling degree days (°F-days).
- **Official metric:** equal-weight mean relative MAE skill against the 30-year
  average baseline, floored at zero; implemented in `proto_star.climate`.
- **Known issues:** incomplete days can bias annual totals; a metric is eligible
  only when its relevant missing-day column(s) are at most 10. Threaded station
  changes can create discontinuities. Stations are mostly airports and do not
  support neighborhood-scale heat claims.
  EDA in `notebooks/0[1-3]_agent_*.ipynb` found the following:
  - In years with no data, max/min columns are ±inf, and `ToT Prcp`/`Wet Days` are 0 instead of NaN.
    `Warm Days`, `Cold Days`, `Warm Nights`, `Cold Nights` and `Max 5-day P` have the same problem.
  - Station switches shift temperature metrics by about 0.5 °F on average.
  - 30 cities switch station within 1989-2018.
  - Huntsville has almost no data after 1960.

#### Leakage policy

Forecasting code may only use weather observations dated on or before
2018-12-31. The download script, the `proto_star.data.protostar` loaders and
`annual_to_long` reject later years through `assert_weather_cutoff`; pass any
new weather input through it too. Do not download the original source records
(the DOIs above or their `CMU-OSPO` Hub copies), which run to 2023. Do not
add 2019–2025 weather-responsive data (weather, energy demand, air quality,
streamflow, vegetation or disease observations) to a forecasting feature set.
Static, non-weather-responsive data may be used only after its provenance,
license, and join logic are documented here.

### Annual master table (the team's shared file)

Use this file for annual experiments, so everyone works from the same cleaned data.

- **Build:** `uv run python scripts/download_protostar_data.py`, then
  `uv run python scripts/build_master_dataset.py`.
- **Files:** `data/processed/protostar/annual_master.parquet`, plus
  `annual_master.manifest.json` with source checksums and cleaning counts.
- **Load:** `from proto_star.data.master import load_master`.
- **Confirm you have the team's table:** the build prints `content_hash`, which must be
  `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1`. If the cleaning code
  changes on purpose, update this hash in the same PR and tell the team.
- **Shape:** 28,052 rows and 37 columns, one row per city and year, 1851–2018. No rows are
  dropped, so **filter on a `valid_*` column before using a metric**.
- **Compatibility:** `annual_to_long` gives identical results on this file and on the raw table,
  and the build fails otherwise.

**What changed from `annual_indices`.** Values became blank only where they cannot be measurements:

| Change | Columns | Cells |
|---|---|---|
| `±inf` to blank | `Max Tmax`, `Min Tmax`, `Max Tmin`, `Min Tmin`, `Max 1-day P` | 5,648 |
| Fake precipitation values to blank, in years with no precipitation data | `ToT Prcp`, `Wet Days`, `Max 5-day P` | 2,796 |
| Fake zeros to blank, in years with no data for that variable | `Warm Days`, `Cold Days`, `Warm Nights`, `Cold Nights` | 4,716 |

**What was added:**

| Column | Meaning |
|---|---|
| `valid_annual_avg_temp`, `valid_total_precip_in`, `valid_hottest_day_temp`, `valid_cdd` | The value passes the official missing-days rule |
| `Days Both`, `Station Segment`, `Station Changes` | Joined from `coverage_and_stations` |
| `cdd_days_short` | More than 10 days lack both tmax and tmin. 348 rows are still `valid_cdd`, because the official rule checks each variable separately |
| `years_since_switch` | Years since the latest station change at or before this row. Blank before the first change |
| `region` | Approximate region from coordinates (`assign_region`) |
| `days_tmax_below_tmin`, `days_extreme_cold`, `days_extreme_precip` | Counts of suspect days in the year (below -50 °F, over 10 in). These days are kept, not corrected |

**What is deliberately not in it:** filled gaps, station adjustments, or per-city statistics such
as climatologies and baseline counts. They depend on which years are known, so a version computed
through 2018 would leak later years into a 1995 backtest. **Compute them inside each backtest
fold**, using only years up to that fold's cutoff. Partially missing years also still read low
until screened, and temperatures in 2018 are not rounded (see the EDA findings).

### NOAA GHCN-Daily station inventory (static metadata)

- **Source / URL:** `ghcnd-stations.txt` from NOAA NCEI GHCN-Daily:
  `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt`.
- **Download:** `uv run python scripts/download_ghcn_station_metadata.py`.
- **License:** public-domain U.S. government work.
- **Content:** station ID, name, latitude, longitude, elevation, state, and
  network flags; no daily or annual weather observations are used.
- **Use:** joined only to the CMU `city_info.ID` key by
  `scripts/build_station_metadata_report.py`, producing a 210-city
  interoperability report. It is not read by the forecasting code.
- **Known limitation:** current station metadata can change administratively;
  the stored local artifact and checksum below are the version used here.

### External data for the regional model (agent D, plan Section 6)

Built by `src/proto_star/data/external/` (one loader per source) and
`scripts/download_<source>.py`. Reproduce everything with:

```bash
uv run python scripts/download_ghcn_station_metadata.py   # elevation, state (static)
uv run python scripts/download_census_population.py       # rank 1
uv run python scripts/download_natural_earth.py           # rank 3 (coast distance)
uv run python scripts/download_ersst.py                   # ranks 4 and 6 (needs geo extra)
uv run python scripts/download_climate_indices.py         # rank 4 (needs geo extra)
uv run python scripts/download_nlcd.py                    # rank 2
uv run python scripts/download_ghcn_neighbors.py          # rank 5
uv run python scripts/build_external_tables.py            # processed tables
```

Downloads write into new subfolders of `data/external/` and never overwrite a file that is
already there. **Use test** (plan 6, "would this 2019-2025 series differ in a hotter or
wetter year?"): census, coastline, elevation and NLCD answer *no* and carry no date cap.
ERSSTv5, the indices and the neighbor stations answer *yes*: each download is a
server-side, date-limited query ending 2018-12, is checked by
`proto_star.climate.assert_weather_cutoff` before it is written, and every loader checks
again with the fold cut-off (`load_indices(cutoff_year)`, `load_sst_grid(cutoff_year=...)`,
`load_neighbor_annual(cutoff_year)`). Each has a leak test in `tests/test_external_*.py`.

#### Processed outputs

- `data/processed/external/city_static.parquet` (`load_city_static()`): 210 rows, one per
  city `ID`. Columns: `Name`, `Lat`, `Lon`, `elevation_m`, `state` (GHCN inventory),
  `region` (`assign_region`), `dist_coast_km`, `dist_great_lakes_km`, `county_fips`,
  `county_name`, `county_land_km2`, `place_name`, `place_pop_2010`, `pop_<1970..2020>`
  with `pop_<year>_source` (`census` = decennial count, `census_base` = April 1
  estimates base for 2000 and 2020), `pop_density_2010_per_km2`,
  `log_pop_growth_<y>_<y+10>`, and NLCD `imperv_<2001|2011|2016>_<1|5|10>km`,
  `canopy_2011_<1|5|10>km` (percent). **Fold rule:** use the population change up to
  the fold cut-off: 1970-1980 for the 1980 fold, 1980-1990 for 1995, 2000-2010 for 2011
  and the final forecast (`census.population_growth_to_cutoff`). NLCD starts in 2001,
  so for the 1980 and 1995 folds it describes the station surroundings after the cut-off
  (static, not weather, but not "known at the time" either).
- `data/processed/external/indices_to_2018.parquet` (`load_indices(cutoff_year)`): monthly
  1854-01 to 2018-12 (1,980 rows). `nino34_anom`, `oni` (trailing 3-month mean), `amo`,
  `pdo` (computed here from ERSSTv5, base periods ending by 1980 so every value is usable
  in every fold), `pdo_cpc` (1950 on), `nao` (1948 on). Definitions in the
  `proto_star.data.external.indices` docstring.
- `data/interim/external/ghcn_neighbors_annual_to_2018.parquet`
  (`load_neighbor_annual(cutoff_year)`) and `ghcn_neighbors_list.csv`: see rank 5 below.

#### Rank 1: U.S. Census county population, 1970-2023

- **Source:** Census Bureau Population Estimates Program county files under
  `https://www2.census.gov/programs-surveys/popest/`: `e7079co.txt` (1970 census +
  1971-79), `e8089co.txt` (1980 census + 1981-89), `99c8_00.txt` (1990 base + 1991-99),
  `co-est00int-tot.csv` (2000 base, 2000-2010, 2010 census), `co-est2019-alldata.csv`,
  `co-est2023-alldata.csv` (2020 base, 2020-2023). City to county: Census geocoder
  (`geocoding.geo.census.gov`, 2010 county vintage) at the station coordinates.
- **License:** public domain (U.S. government work).
- **Files:** `data/external/census_county_population/` (six files, raw geocoder JSON
  `city_county_geocoder.json`, `SOURCE.txt`). Loader: `census.load_county_population()`
  (long `fips, year, population, kind, source_file`; 3,215 counties, 1970-2023).
- **Use test:** no. All 210 cities map to a county with all six decennial values.
- **Known issues:** the Census Data API now needs a key, so the flat files are used.
  `99c8_00.txt` as served has corrupted bytes in two block-1 lines (Sevier County UT,
  Windsor County VT); those fields become missing, nothing shifts. Dade County FL
  (12025) is renamed to Miami-Dade (12086). County population is a proxy for growth
  around the station (mostly airports), not city-centre growth. 55 stations lie outside
  any incorporated place or CDP (`place_name` blank).

#### Rank 3: elevation and distance to coast

- **Elevation:** `elevation_m` from the GHCN-Daily station inventory (section above).
- **Coast / Great Lakes:** Natural Earth 1:10m `ne_10m_coastline` and `ne_10m_lakes`
  GeoJSON, release v5.1.2 from `github.com/nvkelso/natural-earth-vector`; public domain.
  `scripts/download_natural_earth.py` writes `data/external/natural_earth/`.
  `geography.coast_and_lake_distances` gives the great-circle distance to the nearest
  vertex (km). Natural Earth's coastline follows tidal estuaries, so e.g. Washington
  National (Potomac) is 0.4 km from "coast".
- **Use test:** no.

#### Rank 4: climate indices to 2018-12 (weather-responding)

- **ERSSTv5** boxes from NOAA CoastWatch ERDDAP (`griddap/nceiErsstv5`), time constraint
  `(1854-01-15):1:(2018-12-15)`; see rank 6.
- **CPC PDO** from the CCIEA ERDDAP (`oceanview.pfeg.noaa.gov`, `tabledap/cciea_OC_PDO`)
  with `time<=2018-12-31T23:59:59Z`; 1950-01 to 2018-12. Its EOF and climatology come
  from 1900-1993 ERSST v3b; its normalisation period is not documented.
- **Sea-level pressure** for the NAO: NCEP/NCAR Reanalysis 1 monthly SLP (NOAA PSL
  THREDDS OPeNDAP), box 30-70N, 60W-2.5W, time indices `0:851` = 1948-01 to 2018-12
  (only the time axis is read to find the index). File
  `data/external/climate_indices/ncep_r1_slp_natl_to_2018.nc`.
- **Not used:** CPC's published ONI (its recent values use the 1991-2020 base, which is
  fitted on 2019-2020 data) and full-file index downloads (PSL/CPC ASCII files run to
  the present). ONI, AMO and a PDO are recomputed from the capped ERSSTv5 instead.
- **License:** public domain (NOAA). **Use test:** yes; capped as above.

#### Rank 2: NLCD impervious surface and tree canopy

- **Source:** MRLC GeoServer WCS 2.0.1 (`https://www.mrlc.gov/geoserver/ows`), coverages
  `NLCD_2001/2011/2016_Impervious_L48` (USGS) and `nlcd_tcc_conus_2011_v2021-4` (USFS).
  One ~20 km Deflate GeoTIFF window per city and layer (EPSG:5070, 30 m), so no national
  file (several GB) is fetched. `data/external/nlcd/<layer>/<ID>.tif`.
- **Buffers:** mean percent of valid pixels with centres within 1, 5 and 10 km of the
  station (`nlcd.buffer_means`; values above 100 are no-data; water counts as 0). The
  projection is computed in code (Snyder's Albers formulas; no pyproj needed).
- **License:** public domain. **Use test:** no (only pre-2019 editions used anyway).

#### Rank 5: GHCN-Daily neighbor stations (weather-responding)

- **Selection:** static `ghcnd-inventory.txt` (NCEI); U.S. stations within 100 km that
  report TMAX and TMIN from 1970 or earlier through 2000 or later, five nearest per city,
  the city's own station excluded (`ghcn_neighbors.nearest_neighbors`).
- **Data:** NCEI Access Data Service `dataset=global-summary-of-the-year`, `endDate=2018-12-31`,
  `units=standard`, types TAVG, TMAX, TMIN, PRCP, EMXT, CLDD. Raw batches in
  `data/external/ghcn_neighbors/gsoy/`. Result: 995 stations, 1,044 city links (208
  cities with 5 neighbors, one with 3, one with 1; median distance 35 km), 74,004
  station-years 1843-2018 in `data/interim/external/ghcn_neighbors_annual_to_2018.parquet`
  (`station_id, year, tavg, tmax, tmin, prcp, emxt, cldd`; degrees F, inches, F-days).
  NCEI's annual completeness rules differ from the challenge's missing-days rule, so
  screen before use. Some neighbors share the city station's coordinates under another
  ID (`distance_km` 0).
- **License:** public domain. **Use test:** yes; capped as above.

#### Rank 6: ERSSTv5 SST grid (weather-responding)

- **Source:** NOAA NCEI ERSSTv5 via NOAA CoastWatch ERDDAP (`griddap/nceiErsstv5`),
  2-degree monthly. Files in `data/external/ersst_v5/`: `global_4deg` (every second
  cell, whole ocean), `nino34`, `north_atlantic`, `north_pacific` (full 2-degree),
  1854-01 to 2018-12. `load_sst_grid(box, cutoff_year)` returns `sst(date, lat, lon)`.
- **Known issues:** the ERDDAP copy has no 1902-10 month (1,979 months). ERSSTv5 is a
  statistical reconstruction that NOAA re-runs as new data arrive; see the trial note.
- **License:** public domain. **Use test:** yes; capped as above.

## Input artifact checksums

| Local artifact | SHA-256 |
|---|---|
| `data/raw/protostar/annual_indices.parquet` | `8c772bb8a946409380acfd5387d9ea9cb84ddcf4a4187d40245e0b0f3a2054b0` |
| `data/raw/protostar/city_info.parquet` | `76c146ec1e474af1e2268f9620d7602e66a9331e45311cce3a643bc2681edb4b` |
| `data/raw/protostar/coverage_and_stations.parquet` | `3aad824b2a807bf520963c0599bad27d6dd8a0e894005ccbb57c1462dbd87027` |
| `data/raw/protostar/daily.parquet` | `e1f403ceb031827474fb0b6b5432c2c91038e2f3f87ac12a322e75d19e2288c7` |
| `data/external/noaa_ghcn_stations/ghcnd-stations.txt` | `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` |
| `data/external/census_county_population/99c8_00.txt` | `1cec5c7f14cace800c10b4831aeaa5a48bb1e52351d5fc766b87801fd8f90717` |
| `data/external/census_county_population/city_county_geocoder.json` | `0ada496a29fa3a30d0384b7a9ceea0736bec6f193ff9d1ef172fb4e5eaf10e29` |
| `data/external/census_county_population/co-est00int-tot.csv` | `273e56203b61c2ccfb05a54c9b2b025b0521e3764b175469ca22bcad4b6ae8f6` |
| `data/external/census_county_population/co-est2019-alldata.csv` | `654032fbb805bc9a7c124ba04ad47e170f5d9dc9d4974a73edfc20598fde77d8` |
| `data/external/census_county_population/co-est2023-alldata.csv` | `38dd59c70ef8067a3d476b6f5039e60f288e2d492015525ba9711faffd12c418` |
| `data/external/census_county_population/e7079co.txt` | `eaa4df09ae2a2f4a24ec0cf789f3675f9fa16a76c91185dc57fba094a71cd255` |
| `data/external/census_county_population/e8089co.txt` | `0385ddcf6a5a4325897a870ea82b74d06b65bdf4a5f1dc6a65bc3b3877917a8c` |
| `data/external/natural_earth/ne_10m_coastline.geojson` | `6f75ae0e0de157b14946e2255eb1f5486d9a13819032e26d4610852d296788f6` |
| `data/external/natural_earth/ne_10m_lakes.geojson` | `2d036f53dedec578001c5c30c2959ee7d4eebc1306900fa4367c49929ec8f2d9` |
| `data/external/ersst_v5/ersstv5_global_4deg_to_2018.nc` | `84dc495b56fba98693ea4cb7ff25c70e1a4a9773bf3ce24b6b16f52ed1e22354` |
| `data/external/ersst_v5/ersstv5_nino34_to_2018.nc` | `b608e6497ed779af4b1e37fa1944d9630c9c26ebffb183d5dfaedbbced5c17e7` |
| `data/external/ersst_v5/ersstv5_north_atlantic_to_2018.nc` | `ed9fade4b2fd740f8e86c12818ee3cabb6a6f9391286a877dabff1f505ec42f8` |
| `data/external/ersst_v5/ersstv5_north_pacific_to_2018.nc` | `f325d09c347a6af48b28c0b397a418043c553b9166630acc2389644e1115e414` |
| `data/external/climate_indices/cpc_pdo_to_2018.csv` | `cb035ee5420987b0f5f481aaec1e9a53ad7d272f5a40efdec0bc2ff72afd23a2` |
| `data/external/climate_indices/ncep_r1_slp_natl_to_2018.nc` | `360f350b48c825440689b7b9209a882cde51cde98fc77e145333e888364573d7` |

ERDDAP and OPeNDAP responses embed a request timestamp in their metadata, so a fresh
download of the ERSSTv5, PDO or SLP files has the same values but a different checksum.
NLCD windows and GHCN neighbor batches are many small files; their combined hashes are
printed by the download scripts and recorded in `docs/trials/external_data_notes.md`.

## Onboarding real data

1. Write `scripts/download_data.py` that saves to `data/raw/<dataset>/` (use
   `huggingface_hub.snapshot_download` or `datasets.load_dataset` for Hub data).
2. Fill in the dataset section above.
3. Copy `configs/baseline.yaml` → set `train_path`, `test_path`, `target`, `id_column`,
   `time_column`, and the `submission` column names required by the leaderboard.
   For a Hub dataset, set `source: hf` and `train_path: <org>/<dataset>`.
4. `uv run proto-star validate-data configs/<new>.yaml`. Add checks to
   `src/proto_star/data/validate.py` for any problems you find.
5. Make the official metric the first entry in `metrics:` (add it to
   `src/proto_star/evaluate.py` if missing).
6. Train `mean_baseline`, record it in `docs/experiments.md`, and make a first submission to
   confirm the format end to end.
7. If the data is gridded (lat/lon/time) rather than tabular, add a loader that flattens or
   windows it into the feature table; keep the train/predict interfaces unchanged.
