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
  - Station switches shift temperature metrics by about 0.5 °F on average.
  - 30 cities switch station within 1989-2018.
  - Huntsville has almost no data after 1960.

#### Leakage policy

Forecasting code may only use weather observations dated on or before
2018-12-31. The download script and `annual_to_long` reject later years. Do not
add 2019–2025 weather-responsive data (weather, energy demand, air quality,
streamflow, vegetation or disease observations) to a forecasting feature set.
Static, non-weather-responsive data may be used only after its provenance,
license, and join logic are documented here.

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

## Input artifact checksums

| Local artifact | SHA-256 |
|---|---|
| `data/raw/protostar/annual_indices.parquet` | `8c772bb8a946409380acfd5387d9ea9cb84ddcf4a4187d40245e0b0f3a2054b0` |
| `data/raw/protostar/city_info.parquet` | `76c146ec1e474af1e2268f9620d7602e66a9331e45311cce3a643bc2681edb4b` |
| `data/external/noaa_ghcn_stations/ghcnd-stations.txt` | `437ee87f0343bcad408a492cf7a02163fb69255364c541b4006d5d76055d0dc3` |

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
