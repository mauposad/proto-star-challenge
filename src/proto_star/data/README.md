# proto_star.data

## Overview

`proto_star.data` is the data layer of the `proto_star` package
("load -> validate -> build features -> split" [__init__.py:module docstring]).
It holds two independent paths:

- **Config-driven tabular path** (`load.py`, `validate.py`, `features.py`,
  `split.py`, plus `synthetic.py` for smoke tests). Driven by `DataConfig` /
  `SplitConfig` from `src/proto_star/config.py`. Used by `src/proto_star/train.py`,
  `src/proto_star/predict.py`, `src/proto_star/cli.py`, and (for `make_train_test`)
  `scripts/make_synthetic_data.py`.
- **ProtoStar climate path** (`protostar.py`, `master.py`). Reads the raw ProtoStar
  parquet tables under `data/raw/protostar/`, enforces the 2018 weather cutoff, and
  builds, verifies, hashes, and loads the shared annual master table under
  `data/processed/protostar/`. Used by `src/proto_star/trial.py`,
  `src/proto_star/submission_package.py`, `scripts/build_master_dataset.py`,
  `scripts/compare_baselines.py`, `scripts/robustness_origins.py`, and the
  `notebooks/0[1-3]_agent_*.ipynb` EDA notebooks.

- **Summer table** (`summer.py`): `summer_means(daily)`, `load_summer_means()` and
  `join_summer(master, summer)`. They produce per-city, per-year June–August mean Tmax and
  Tavg, blank below 85 days. Each value uses only its own year's days.

No module in this directory writes files. It has no subdirectories.

## Interface

### `features.py`

- `add_calendar_features(df: pd.DataFrame, time_column: str) -> pd.DataFrame` -
  returns a copy with `doy_sin`, `doy_cos`, `month`, `year` [features.py:add_calendar_features]
- `build_features(df: pd.DataFrame, cfg: DataConfig) -> pd.DataFrame` - returns the
  model input matrix X [features.py:build_features]

### `load.py`

- `read_table(path: str) -> pd.DataFrame` - reads `.csv`, `.parquet`, `.pq`, `.json`,
  `.jsonl` (suffix lower-cased) from `resolve(path)` [load.py:read_table]
- `read_hf(repo_id: str, split: str) -> pd.DataFrame` -
  `datasets.load_dataset(repo_id, split=split).to_pandas()`, with `datasets` imported
  lazily [load.py:read_hf]
- `load_train(cfg: DataConfig) -> pd.DataFrame` - loads `cfg.train_path`
  (HF split `cfg.hf_train_split`) [load.py:load_train]
- `load_test(cfg: DataConfig) -> pd.DataFrame` - loads test inputs; for `source == "hf"`
  uses `cfg.test_path or cfg.train_path` with `cfg.hf_test_split` [load.py:load_test]

### `validate.py`

- `class DataValidationError(ValueError)` [validate.py:DataValidationError]
- `validate(df: pd.DataFrame, cfg: DataConfig, *, has_target: bool = True) -> None` -
  raises `DataValidationError` listing every problem found [validate.py:validate]

### `split.py`

- `split(df: pd.DataFrame, cfg: SplitConfig, *, time_column: str | None, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]` -
  dispatches to `time_split` when `cfg.strategy == "time"`, else `random_split`;
  returns `(train, valid)` [split.py:split]
- `time_split(df: pd.DataFrame, time_column: str, valid_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame]`
  [split.py:time_split]
- `random_split(df: pd.DataFrame, valid_fraction: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]`
  [split.py:random_split]

### `synthetic.py`

- `make_weather(n_days: int = 1500, n_stations: int = 3, seed: int = 0) -> pd.DataFrame` -
  synthetic daily weather with columns `id`, `date`, `station_id`, `humidity`,
  `pressure`, `max_temp` [synthetic.py:make_weather]
- `make_train_test(test_fraction: float = 0.15, **kwargs: int) -> tuple[pd.DataFrame, pd.DataFrame]` -
  "Mimic a leaderboard: test = latest period with the target removed"; `kwargs` go to
  `make_weather` [synthetic.py:make_train_test]

### `protostar.py`

- `PROTOSTAR_DIR = RAW_DIR / "protostar"` [protostar.py:PROTOSTAR_DIR]
- `DAILY_VALUE_COLUMNS = ("tmax", "tmin", "prcp")` [protostar.py:DAILY_VALUE_COLUMNS]
- `REGION_LON_EDGES = (-104.0, -87.0)`, `REGION_LAT_EDGE = 37.0`
  [protostar.py:REGION_LON_EDGES, REGION_LAT_EDGE]
- `REGIONS = ("Northwest", "Southwest", "North Central", "South Central", "Northeast", "Southeast")`
  [protostar.py:REGIONS]
- `load_annual(data_dir: Path | None = None) -> pd.DataFrame` - reads `annual_indices`
  unchanged [protostar.py:load_annual]
- `load_city_info(data_dir: Path | None = None) -> pd.DataFrame` - reads `city_info`
  (one row per station thread), parsing `Stn.stDate` and `Stn.edDate`
  [protostar.py:load_city_info]
- `load_coverage(data_dir: Path | None = None) -> pd.DataFrame` - reads
  `coverage_and_stations` unchanged [protostar.py:load_coverage]
- `load_daily(data_dir: Path | None = None, *, city_ids: Iterable[str] | None = None, columns: Sequence[str] = DAILY_VALUE_COLUMNS) -> pd.DataFrame` -
  reads `daily` with categorical `ID`, datetime `Date`, float32 values; `Name` is not
  read [protostar.py:load_daily]
- `assign_region(lat: pd.Series, lon: pd.Series) -> pd.Series` - categorical Series
  named `region` with categories `list(REGIONS)` and index `lat.index`
  [protostar.py:assign_region]
- `city_table(annual: pd.DataFrame, city_info: pd.DataFrame) -> pd.DataFrame` - one row
  per city: `ID`, `Name`, `Lat`, `Lon`, `first_year`, `last_year`, `n_years`,
  `n_station_threads`, `region` [protostar.py:city_table]

### `master.py`

- `MASTER_DIR = PROCESSED_DIR / "protostar"` [master.py:MASTER_DIR]
- `MASTER_FILE = "annual_master.parquet"` [master.py:MASTER_FILE]
- `MANIFEST_FILE = "annual_master.manifest.json"` - not used inside `proto_star.data`;
  imported by `src/proto_star/submission_package.py` (copies and reads the manifest) and
  `scripts/build_master_dataset.py` (writes it) [master.py:MANIFEST_FILE]
- `NO_DATA_COLUMNS: dict[str, tuple[str, ...]]` - `"Miss Prcp"` ->
  (`ToT Prcp`, `Wet Days`, `Max 1-day P`, `Max 5-day P`); `"Miss Tmax"` ->
  (`Warm Days`, `Cold Days`); `"Miss Tmin"` -> (`Warm Nights`, `Cold Nights`)
  [master.py:NO_DATA_COLUMNS]
- `EXTREME_COLD_F = -50.0`, `EXTREME_PRECIP_IN = 10.0`, `MAX_SHORT_CDD_DAYS = 10`
  [master.py:EXTREME_COLD_F, EXTREME_PRECIP_IN, MAX_SHORT_CDD_DAYS]
- `DAILY_FLAG_COLUMNS = ("days_tmax_below_tmin", "days_extreme_cold", "days_extreme_precip")`
  [master.py:DAILY_FLAG_COLUMNS]
- `days_in_year(years: pd.Series) -> pd.Series` - 366 for leap years, else 365, as
  `int64` [master.py:days_in_year]
- `clean_annual(annual: pd.DataFrame) -> pd.DataFrame` - blanks no-data artifacts
  [master.py:clean_annual]
- `daily_quality_counts(daily: pd.DataFrame) -> pd.DataFrame` - flagged-day counts per
  (`ID`, `Year`) [master.py:daily_quality_counts]
- `build_annual_master(annual: pd.DataFrame, coverage: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame` -
  one row per city and year; adds `valid_<metric>`, `Days Both`, `Station Segment`,
  `Station Changes`, `cdd_days_short`, `years_since_switch`, `region`, and the
  `DAILY_FLAG_COLUMNS` counts [master.py:build_annual_master]
- `verify_master(master: pd.DataFrame, annual: pd.DataFrame) -> None` - raises unless
  the master keeps every row and every scored value of the raw table
  [master.py:verify_master]
- `content_hash(master: pd.DataFrame) -> str` - sha256 hex digest of the comma-joined
  column names plus `pd.util.hash_pandas_object(master, index=False)` row hashes
  [master.py:content_hash]
- `load_master(data_dir: Path | None = None) -> pd.DataFrame` - reads
  `(data_dir or MASTER_DIR) / MASTER_FILE` [master.py:load_master]

## Invariants

### Leakage and determinism

- Feature functions may only use information available at prediction time for the row;
  centered rolling means or whole-dataset statistics leak [features.py:module docstring]
- `build_features` is "Deterministic and identical for train and test". Calendar
  columns are added only when `cfg.calendar_features and cfg.time_column`. With
  `cfg.features` set, columns are `cfg.features` plus the four calendar columns (when
  enabled). Otherwise, every numeric column not in
  `{cfg.target, cfg.id_column, cfg.time_column}` [features.py:build_features]
- Calendar encoding is `sin/cos(2 * pi * day_of_year / 365.25)` [features.py:add_calendar_features]
- `time_split`: cutoff is `df[time_column].quantile(1 - valid_fraction)`, train is
  `< cutoff`, valid is `>= cutoff`. Docstring: "All validation timestamps are strictly
  later than all training timestamps" [split.py:time_split]
- `split` raises `ValueError("time split requires a time column")` when
  `cfg.strategy == "time"` and `time_column is None` [split.py:split]
- `random_split` is seeded via `df.sample(frac=valid_fraction, random_state=seed)`;
  train is `df.drop(valid.index)` [split.py:random_split]
- `make_weather` uses `np.random.default_rng(seed)` and dates from
  `pd.date_range("2018-01-01", periods=n_days, freq="D")`. It does not call
  `assert_weather_cutoff`, so the default 1500 days run past 2018
  [synthetic.py:make_weather]
- `make_train_test` splits on `df["date"].quantile(1 - test_fraction)` (`<` train,
  `>=` test) and drops `max_temp` from test [synthetic.py:make_train_test]

### Loading and validation

- `read_table` raises `ValueError` for an unsupported suffix (checked first), then
  `FileNotFoundError` if the resolved path does not exist [load.py:read_table]
- `source == "hf"` selects `read_hf`, otherwise `read_table`. The time column is
  parsed with `pd.to_datetime` only if `cfg.time_column` is set and present [load.py:_load]
- `load_test` raises `ValueError("data.test_path must be set to generate a submission")`
  when `source != "hf"` and `cfg.test_path is None` [load.py:load_test]
- `validate` collects all problems, then raises one `DataValidationError`. It checks:
  required columns (truthy `id_column`/`time_column`, `target` if `has_target`,
  `cfg.features` if truthy); empty frame; target entirely null, else target not numeric;
  duplicate `id_column` values; `time_column` present but not datetime [validate.py:validate]

### ProtoStar cutoff and raw tables

- `assert_weather_cutoff` (from `src/proto_star/climate.py`, default cutoff 2018) runs in
  `load_annual`, `load_coverage`, `load_daily`, `load_master`, and `verify_master`, but
  not in `load_city_info` [protostar.py:load_annual, load_coverage, load_daily;
  master.py:load_master, verify_master]
- Raw readers "only read and annotate data; they never clean or impute it"
  [protostar.py:module docstring]
- A missing raw table raises `FileNotFoundError` pointing to
  `uv run python scripts/download_protostar_data.py` [protostar.py:_path]
- `load_daily` raises `ValueError` for columns outside `DAILY_VALUE_COLUMNS`, and for an
  empty but non-`None` `city_ids`. IDs are str-cast, de-duplicated, sorted, and passed
  as the parquet filter `[("ID", "in", ids)]` [protostar.py:load_daily]
- `assign_region`: `lon < -104.0` is West, `lon < -87.0` is Central, otherwise East;
  north is `lat >= 37.0`. Uses `zip(..., strict=True)` [protostar.py:assign_region]
- `city_table` takes `Name`/`Lat`/`Lon` from the first row per `ID`, fills missing
  `n_station_threads` with 0, and sorts by `ID` [protostar.py:city_table]

### Master table

- Corrects only what is provably not a measurement and flags everything else, so every
  row of `annual_indices` survives. No imputed values, station adjustments, or
  per-city statistics; every added column uses only the row's own year or earlier
  [master.py:module docstring]
- `clean_annual` turns numeric `+/-inf` into NaN and blanks the `NO_DATA_COLUMNS` values
  where `Miss <var> >= days_in_year(Year)`. Partially missing years keep their values
  [master.py:clean_annual]
- `daily_quality_counts` flags `tmax < tmin`, `tmin < EXTREME_COLD_F`, and
  `prcp > EXTREME_PRECIP_IN`, and keeps only (`ID`, `Year`) groups with at least one
  flag. It reads `tmax`, `tmin`, and `prcp`, so the `daily` passed to
  `build_annual_master` needs all of `DAILY_VALUE_COLUMNS` [master.py:daily_quality_counts]
- `build_annual_master`:
  - computes `valid_<metric>` with `metric_valid_mask` on the raw `annual`, not the
    cleaned copy, for each of `METRICS` [master.py:build_annual_master]
  - merges coverage with `how="left", validate="1:1"` and raises `ClimateDataError` if
    any `Days Both` is NaN [master.py:build_annual_master]
  - sets `cdd_days_short = (days_in_year(Year) - Days Both) > MAX_SHORT_CDD_DAYS`
    [master.py:build_annual_master]
  - stores `region` as plain `str` via `assign_region(...).astype(str)`, not the
    categorical that `assign_region` and `city_table` return; this affects the parquet
    schema and `content_hash` [master.py:build_annual_master]
  - fills daily flag counts with 0 as `int64` and sorts the output by
    `["ID", "Year"]` [master.py:build_annual_master]
- `years_since_switch` is `Year` minus the latest year at or before it with
  `Station Changes > 0`. It is `Int64`, NA before any switch [master.py:_years_since_switch]
- `verify_master` raises `ClimateDataError` in any of these cases [master.py:verify_master]:
  - the cutoff fails
  - row counts differ
  - (`ID`, `Year`) is duplicated
  - any numeric value is infinite
  - `annual_to_long(annual)` and `annual_to_long(master)` differ
- `content_hash` ignores the index and depends on column names and their order
  [master.py:content_hash]
- `load_master` raises `FileNotFoundError` pointing to
  `uv run python scripts/build_master_dataset.py` [master.py:load_master]

## Side Effects

- Disk read: `read_table` reads a local file at `resolve(path)` (relative to the
  project root) [load.py:read_table]
- Network: `read_hf` calls `datasets.load_dataset` (Hugging Face Hub); any caching is
  done by that library [load.py:read_hf]
- Disk read: `load_annual`, `load_city_info`, `load_coverage`, `load_daily` read
  `(data_dir or PROTOSTAR_DIR)/<name>.parquet` (default `data/raw/protostar/`)
  [protostar.py:_path, load_annual, load_city_info, load_coverage, load_daily]
- Disk read: `load_master` reads `(data_dir or MASTER_DIR)/annual_master.parquet`
  (default `data/processed/protostar/`) [master.py:load_master]
- No input mutation: `add_calendar_features` works on `df.copy()`; `clean_annual` on
  `annual.copy()`; `build_annual_master` on that copy and on merge results
  [features.py:add_calendar_features; master.py:clean_annual, build_annual_master]
- No file writes, env var reads, printing, or logging in this package. The master
  parquet and manifest are written by `scripts/build_master_dataset.py`, outside this
  directory [master.py:MASTER_FILE, MANIFEST_FILE]

## Verification

- Run: `make check` (ruff lint + format check, mypy, pytest with coverage)
- Targeted: `uv run pytest tests/test_data.py tests/test_master.py tests/test_protostar.py -q`
- `tests/conftest.py` builds fixtures with `make_train_test`.
  `tests/test_download_protostar.py` covers `scripts/download_protostar_data.py`, not
  this package.
