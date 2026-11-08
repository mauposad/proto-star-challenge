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


Note: `nlcd2016_points.csv` comes from a live web service; a re-download may differ if MRLC
changes the served layer. The checksum above is the version used.

### NOAA GML Mauna Loa annual mean CO2 (forcing, capped at 2018)

- **Source / URL:** NOAA Global Monitoring Laboratory, Mauna Loa annual mean CO2:
  `https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.csv`.
- **Download:** `uv run python scripts/download_noaa_co2.py`. Keeps years ≤ 2018 only, checks
  them with `assert_weather_cutoff`, writes a `SOURCE.txt` receipt, and refuses to overwrite an
  existing folder.
- **Files:** `data/external/noaa_co2/co2_annmean_mlo_to_2018.csv` (60 rows, 1959–2018) and
  `data/external/noaa_co2/SOURCE.txt`.
- **Schema:** `year` (int), `co2_ppm` (float, annual mean dry-air mole fraction, ppm).
- **License:** public-domain U.S. government work (NOAA GML). NOAA asks users to cite the data
  (Lan, Tans and Thoning, NOAA GML).
- **Vintage:** downloaded on 2026-11-07 from the current file, so pre-2019 values are from
  NOAA's current calibration, not a 2018 vintage. CO2 is a forcing, not a weather observation,
  and no value after 2018 is kept.
- **Use:** forcing for the P21 forced-trend benchmark (`forced_trend_ar1_p21`, `shift10_co2`
  in `configs/agent_paper_cdd_forcing_p06_p21.yaml`). Inside a backtest fold only values up to
  that fold's cut-off are read. Later years are extrapolated linearly from the last 10 values.
- **CI:** the publish workflow does not download this file, so a CO2-based `submit:` would not
  rebuild on CI. No CO2 forecaster is submitted.

## Input artifact checksums

| Local artifact | SHA-256 |
|---|---|
| `data/raw/protostar/annual_indices.parquet` | `8c772bb8a946409380acfd5387d9ea9cb84ddcf4a4187d40245e0b0f3a2054b0` |
| `data/raw/protostar/city_info.parquet` | `76c146ec1e474af1e2268f9620d7602e66a9331e45311cce3a643bc2681edb4b` |
| `data/raw/protostar/coverage_and_stations.parquet` | `3aad824b2a807bf520963c0599bad27d6dd8a0e894005ccbb57c1462dbd87027` |
| `data/raw/protostar/daily.parquet` | `e1f403ceb031827474fb0b6b5432c2c91038e2f3f87ac12a322e75d19e2288c7` |
| `data/external/noaa_ghcn_stations/ghcnd-stations.txt` | `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` |
| `data/external/regional_p22_p24/ghcnd-stations.txt` | `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` |
| `data/external/regional_p22_p24/Gaz_places_national.zip` | `db63b4ef027f2118221c057b9e4911a4bbda09975bdc4aac7d0c0ba286e04c76` |
| `data/external/regional_p22_p24/nlcd2016_points.csv` | `849f440a17a2e927df8b312ab62933839a742a794c0c1bee3ca1ddd55c349553` |
| `data/external/regional_p22_p24/city_groups.csv` | `4ca0476f2ee85100c041fae40ca746040531c1a8d21432b000c057c07e48ab51` |
| `data/external/noaa_co2/co2_annmean_mlo_to_2018.csv` | `0ef2a07a4f2a5961efd070912079140446eb5ddd1b1d5587fddeb5844056a245` |

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
