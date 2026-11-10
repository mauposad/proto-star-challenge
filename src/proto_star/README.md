# proto_star

## Overview

The `proto_star` package holds all reusable code for the CMU OSPO x Hugging Face ProtoStar
climate challenge. It has two independent workflows:

- **Climate challenge workflow** (the one that produces submissions). It covers the panel of 210
  cities × years × 4 metrics, the 2018 data cut-off, the organizer's missing-days rule, the
  official relative-skill score, rolling-origin backtests, the pooled-trend forecaster, trial
  records, and the Hugging Face submission package. Modules: `climate.py`, `backtest.py`,
  `trend.py`, `trial.py`, `submission_package.py`, `station_metadata.py`.
- **Generic tabular pipeline** (sklearn estimators through a registry, synthetic data, time
  split). Modules: `config.py`, `train.py`, `predict.py`, `evaluate.py`, `tracking.py`.

`cli.py` exposes both workflows as the `proto-star` Typer app. `paths.py` defines every
filesystem location.

## Interface

### Subpackages

- [`data/`](./data/README.md): loaders for the raw ProtoStar tables, the shared annual master
  table, generic load/validate/features/split, and synthetic data.
- [`models/`](./models/README.md): sklearn-API model registry for the generic pipeline.
- [`utils/`](./utils/README.md): logger factory and RNG seeding.

### Challenge constants and errors (`climate.py`)

- `METRICS = ("annual_avg_temp", "total_precip_in", "hottest_day_temp", "cdd")`: the four
  official metrics [climate.py:METRICS].
- `SUBMISSION_COLUMNS = ["city_id", "year", "metric", "predicted_value"]` [climate.py:SUBMISSION_COLUMNS].
- `FORECAST_CUTOFF = 2018`, `FORECAST_YEARS = 2019..2025`, `MAX_MISSING_DAYS = 10`,
  `BASELINE_WINDOW_YEARS = 30` [climate.py].
- `DEFAULT_CUTOFFS = (1980, 1995, 2011)`: backtest origins. ADR 0004 says this is the only place
  they are defined [climate.py:DEFAULT_CUTOFFS].
- `BASELINE_METHODS` and `BASELINE_DESCRIPTIONS`: `last_valid_year`,
  `ten/fifteen/thirty_year_mean`, `ten/fifteen/thirty_year_median`, `linear_trend`, `hinge_fit`
  [climate.py].
- `HINGE_MIN_POINTS = 20`, `HINGE_MIN_FLAT_POINTS = 5`, `HINGE_MIN_RAMP_POINTS = 10`:
  `hinge_fit` returns the window mean below 20 points and keeps at least 5 flat and 10 ramp
  points. `linear_trend` returns the mean with fewer than 2 points or no year spread
  [climate.py:_hinge_fit, climate.py:_predict_group].
- `ClimateDataError(ValueError)`, `ClimateSubmissionError(ValueError)`, and the frozen dataclass
  `ClimateScore(score, mae, skill, n_rows)` [climate.py].

### Climate functions (`climate.py`)

- `assert_weather_cutoff(table, *, name, cutoff_year=2018)`: raises if a weather table has
  observations after the cut-off [climate.py:assert_weather_cutoff].
- `metric_valid_mask(annual, metric)` and `annual_to_long(annual, *, cutoff_year=2018)`: apply
  the quality screen, then melt to long form `city_id, year, metric, actual_value`
  [climate.py:metric_valid_mask, climate.py:annual_to_long].
- `validate_climate_history(history, *, max_year=None)` [climate.py:validate_climate_history].
- `baseline_forecast(history, *, cutoff_year, forecast_years, method)` [climate.py:baseline_forecast].
- `official_score(predictions, truth, reference_predictions) -> ClimateScore` [climate.py:official_score].
- `backtest_baselines`, `select_metric_methods`, `metric_ensemble_forecast`,
  `backtest_metric_ensemble` [climate.py].
- `validate_submission(submission, city_ids)` [climate.py:validate_submission].

### Shared scorer (`backtest.py`)

- `Forecaster = Callable[[train, cutoff_year, forecast_years], DataFrame]` [backtest.py:Forecaster].
- `DEFAULT_HORIZON = 7`; `WINDOWS = {"all": (1, 7), "years_1_3": (1, 3), "years_4_7": (4, 7)}`
  [backtest.py].
- `CURRENT_BEST = "current_best"` and `CURRENT_BEST_METHODS`: 10-year mean for temperature and
  CDD, 30-year mean for precipitation and hottest day [backtest.py].
- `baseline_forecaster(method)`, `ensemble_forecaster(methods)`,
  `pooled_trend_forecaster(spec)`, `resolve_forecaster(name, ensembles, pooled_trends)`
  [backtest.py].
- `backtest_forecaster(forecaster, master, *, name, cutoffs, horizon)`,
  `compare_forecasters(forecasters, master, ...)`, `summarize_backtest(results, *, baseline)`,
  `build_submission(forecaster, master)` [backtest.py].

### Pooled-trend forecaster (`trend.py`)

- `TEMPERATURE = "annual_avg_temp"`, `CDD = "cdd"`, `FLAT_METHOD = "thirty_year_mean"` [trend.py].
- `PooledTrendSpec(level_years, trend_window, min_city_years=10, cdd_sensitivity=True)`. It is
  frozen and forbids extra keys. `level_years` must be non-empty, `trend_window >= 10` and
  `min_city_years >= 3` [trend.py:PooledTrendSpec].
- `pooled_slope(history, metric, cutoff_year, spec) -> float`: within-city least-squares slope
  pooled across cities [trend.py:pooled_slope].
- `cdd_per_degree(history, cutoff_year, spec) -> Series`: each city's CDD gained per °F of annual
  temperature [trend.py:cdd_per_degree].
- `pooled_trend_forecast(history, *, cutoff_year, forecast_years, spec)` [trend.py:pooled_trend_forecast].

### Config-defined forecasters (round-1 hypotheses, `hypotheses.md`)

- `forecasters.py`: `CustomSpec(kind, params, description)`, `register_kind`,
  `available_kinds`, `build_custom`, `describe_custom`. The registered kinds are:

  | Kind | Implementation | Hypothesis |
  | :--- | :------------- | :--------- |
  | `blend` | `forecasters.py` | U2 |
  | `per_metric` | `forecasters.py` | — |
  | `direct` | `direct.py` | U1 |
  | `persistence` | `adjust.py` | H16 |
  | `skew_shift` | `adjust.py` | H3/H13 |
  | `cdd_from_temp` | `adjust.py` | H5 |
  | `level_adjust` | `levels.py` | H4/H11 |
  | `hottest_summer` | `hottest.py` | H2/H14 |
  | `neighbours` | `neighbours.py` | H1 |

  A trial config uses them under `custom:` [forecasters.py, trial.py:build_forecasters].
- `backtest.fold_rows(forecaster, master, ...)` returns every scored row. Its partner
  `backtest.paired_year_bootstrap(rows_a, rows_b, *, window, metrics, n_boot, seed)` gives
  the paired raw-score or skill difference with a 95% interval from resampling forecast years
  within folds [backtest.py].

### Trials and submission package

- `TrialConfig`, `load_trial_config(path)`, `build_forecasters(cfg)`,
  `describe_forecaster(name, cfg)`, `markdown_table(frame)`,
  `run_trial(config_path, *, master, trials_dir, notes_dir, record)`, `read_meta(run_dir)`
  [trial.py].
- `build_package(config_path, *, forecaster, master, master_dir, raw_dir, out_root, team_path)`,
  `open_placeholders(package_dir)`, `verify_package(root, *, tolerance=1e-9)`
  [submission_package.py].
- Package layout constants: `RAW_INPUTS`, `PIPELINE_SCRIPTS`, `EVIDENCE_SCRIPTS`, `DOWNLOAD`,
  `TEAM_FILE` (default `team_path` = `docs/submission/team.yaml`), `SUBMISSION_DOCS`,
  `PLACEHOLDER`, `REPRODUCE_SCRIPT` and `CODE_README` [submission_package.py].
  `PLACEHOLDER` is the regex that decides what `open_placeholders` reports.
- `GHCN_STATION_COLUMNS`, `load_ghcn_station_metadata(path)`,
  `build_station_metadata_report(cities, stations)` [station_metadata.py].

### Generic pipeline

- `DataConfig`, `SplitConfig`, `ModelConfig`, `SubmissionConfig`, `ExperimentConfig`,
  `load_config(path)` [config.py].
- `train(cfg, runs_dir=RUNS_DIR) -> Path` [train.py:train].
- `SubmissionError`, `load_run(run_dir)`, `predict(run_dir, out_dir=SUBMISSIONS_DIR) -> Path`,
  `validate_submission(sub, cfg, expected_rows)` [predict.py].
- `Metric` (type alias), `METRICS = {mae, rmse, r2}` and `compute_metrics(y_true, y_pred, names)`
  [evaluate.py]. This dict is a different object from `climate.METRICS`.
- `git_info()`, `create_run_dir(cfg, runs_dir)`, `write_json(path, obj)`, `read_json(path)`
  [tracking.py].

### Paths and CLI

- `PROJECT_ROOT`, `DATA_DIR`, `RAW_DIR`, `INTERIM_DIR`, `PROCESSED_DIR`, `EXTERNAL_DIR`,
  `CONFIGS_DIR`, `RUNS_DIR`, `SUBMISSIONS_DIR`, `TRIALS_DIR` (`runs/trials`), `TRIAL_NOTES_DIR`
  (`docs/trials`), and `resolve(path)` [paths.py].
- `app` (Typer) commands [cli.py]:
  - Generic pipeline: `train`, `predict`, `validate-data`, `models`.
  - Downloads: `download-climate-data`, `download-station-metadata`.
  - Climate workflow: `climate-metadata-report`, `climate-backtest`, `climate-trial`,
    `climate-package`, `climate-submission`, `climate-ensemble-submission`.
  - `climate-backtest` takes a repeatable `--cutoff`. `climate-package` runs
    `verify_package` and prints the `TODO before upload` placeholders.
  - **Known defect:** `download-climate-data`, `download-station-metadata` and
    `climate-metadata-report` import the top-level `scripts.*` modules. That package sits
    outside `src/`, has no `__init__.py`, and is not on `sys.path` when you run the
    `proto-star` console script. Expect `ModuleNotFoundError`; run
    `uv run python scripts/<name>.py` instead. This was checked with `find_spec`; the
    commands themselves were not run.

## Invariants

- **Data cut-off.** Weather inputs must end by 2018. `assert_weather_cutoff` fails when a table
  has no `Year`/`Date` column, has unparseable dates, or has a year after the cut-off.
  `annual_to_long` rejects later years instead of filtering them out
  [climate.py:assert_weather_cutoff, climate.py:annual_to_long].
- **Quality screen.** A value counts only if it is finite and every missing-days column for its
  metric is ≤ 10. The metric-to-column map is `_METRIC_SPECS`: `Avg Temp`, `ToT Prcp`,
  `Max Tmax`, `cdd` [climate.py:metric_valid_mask, climate.py:_METRIC_SPECS].
- **Baseline windows.** The 10- and 15-year methods use the last N valid years. The 30-year
  mean, 30-year median, linear trend, and hinge fit use calendar years after `cutoff - 30`.
  If that window is empty they fall back to the last 30 valid rows (ADR 0003)
  [climate.py:_predict_group].
- **Official score.** For each metric, skill = 1 − MAE_model / MAE_ref. Score =
  100 × max(0, mean of the 4 skills). Truth, forecast, and reference are inner-joined.
  `ClimateDataError` is raised in these cases [climate.py:official_score,
  climate.py:_prediction_frame]:
  - the join is empty;
  - a metric has no rows;
  - a metric's reference MAE is ≤ 0;
  - a forecast is missing columns, has non-finite values, or repeats a city/year/metric key.

  The caller chooses the reference; every caller passes `thirty_year_mean`.
- **Backtest folds.** Each fold trains on `master[Year <= cutoff]` after
  `assert_weather_cutoff(cutoff_year=cutoff)`. The reference is `thirty_year_mean`. Forecasts
  that skip a scored row, or include years outside the fold, raise `ClimateDataError`.
  `raw_score` is the unfloored score [backtest.py:backtest_forecaster, backtest.py:_check_coverage].
- **Forecaster contract.** A forecaster must compute everything from its `train` argument. The
  scorer cannot detect leakage from other sources [backtest.py:module docstring].
- **Custom forecasters.** Custom names must not collide with baselines, `current_best`,
  ensembles or pooled trends. Custom forecasters may refer to each other, but a cycle raises
  `ValueError`. Every kind fits its parameters from the fold's `train` rows only. Pseudo-origins
  inside a fold satisfy origin + lead ≤ cut-off [trial.py:TrialConfig, trial.py:build_forecasters,
  adjust.py, direct.py].
- **Summer join.** `join_summer: true` joins the per-year June–August means on (ID, Year)
  through `trial_master`. `build_package` refuses such trials [trial.py:trial_master,
  submission_package.py:build_package].
- **Trial cut-offs.** Trial configs cannot set cut-offs. `run_trial` always uses
  `DEFAULT_CUTOFFS`. `TrialConfig` forbids extra keys. `name` must match `^[a-z0-9_]+$`,
  `forecasters` must be non-empty, and `reference` and `submit` must be among `forecasters`
  [trial.py:TrialConfig, trial.py:run_trial].
- **Pooled trend.** The slope is fitted over the calendar years `[cutoff − trend_window + 1,
  cutoff]` and floored at 0. A city enters the fit only with at least `min_city_years` rows. CDD
  sensitivity is clipped at 0, and cities without an estimate fall back to the pooled CDD slope.
  Per city, the forecast is the mean over the `level_years` windows of
  `level + slope × (year − mean year of that window)`. Precipitation and hottest day use
  `thirty_year_mean` [trend.py:pooled_slope, trend.py:cdd_per_degree, trend.py:_city_slopes,
  trend.py:_trend_rows, trend.py:pooled_trend_forecast].
- **No reruns within the same second.** `run_trial`, `build_package` and `create_run_dir` each
  create a timestamped directory with `exist_ok=False` [trial.py:run_trial,
  submission_package.py:build_package, tracking.py:create_run_dir].
- **Submission contract.** The columns are exactly `SUBMISSION_COLUMNS`. Cities match the
  official set, years are 2019–2025, all 4 metrics are present, keys are unique, rows =
  cities × 7 × 4, and every value is finite [climate.py:validate_submission].
- **Package checks.** `build_package` raises `ValueError` when no forecaster or `submit` is
  given, or when that name is not in `forecasters`. `verify_package` rebuilds the forecast
  from `code/trial.yaml` and the shipped `data/`. It raises in these cases
  [submission_package.py:build_package, submission_package.py:verify_package]:
  - `ValueError`: `submit` is missing;
  - `ClimateSubmissionError`: the row counts or keys differ, or any value differs from
    `submission.csv` by more than `1e-9`;
  - pandas `MergeError`: keys are duplicated.

  On success it prints `OK: ...`.
- **Generic pipeline.** `train` runs, in order: seed, validate, drop rows with no target, split
  (time by default), build features separately for train and validation, fit through the
  registry, score on validation only. `predict` requires every training feature column
  [train.py:train, predict.py:predict].
- **Strict configs.** Config models forbid unknown keys. `split.strategy="time"` requires
  `data.time_column` [config.py:_Strict, config.py:ExperimentConfig].

## Side Effects

- Importing `cli.py` runs `load_dotenv()`, which loads `.env` into the environment
  [cli.py:module level].
- `train` writes `runs/<stamp>_<name>/` with `config.yaml`, `model.joblib`, `metrics.json`, and
  `meta.json`. Through `set_seed` it also seeds the global `random`, NumPy (and torch) RNGs and
  sets `os.environ["PYTHONHASHSEED"]` [train.py:train, tracking.py:create_run_dir,
  utils/seed.py:set_seed].
- `predict` reads `model.joblib` with `joblib.load` (unpickling) and writes
  `submissions/<run>.csv`, overwriting any file with that name [predict.py:load_run, predict.py:predict].
- `run_trial` reads `data/processed/protostar/annual_master.parquet` when `master=None`. It
  writes `runs/trials/<stamp>_<name>/`, and with `record=True` it also overwrites
  `docs/trials/<name>.md` [trial.py:run_trial].
- `build_package` writes `submissions/<stamp>_<name>/` [submission_package.py:build_package,
  submission_package.py:_copy_code, submission_package.py:_copy_data]:
  - `submission.csv` and `README.md`
  - `code/`: `src/proto_star`, the 4 `PIPELINE_SCRIPTS` + `EVIDENCE_SCRIPTS`,
    `check_submission.py`, `AGENTS.md`, `trial.yaml`, `reproduce.py`, `README.md`,
    `requirements.txt`
  - `data/`: the master parquet, its manifest, the `RAW_INPUTS`, and `README.md`

  It also:
  - reads `docs/submission/team.yaml`, `policy-idea.md`, `ecosystem-feedback.md` and the
    installed package metadata (for the pins);
  - re-runs `compare_forecasters` for the README;
  - calls `git_info`.

  It makes no Hub upload.
- `climate-submission` and `climate-ensemble-submission` write CSVs to paths relative to the
  current directory (`submissions/...`) [cli.py].
- `git_info` runs `git rev-parse --short HEAD` and `git status --porcelain`. Both are read-only
  [tracking.py:git_info].
- `adjust.py`, `levels.py`, `hottest.py` and `neighbours.py` log their fitted parameters
  (φ, q, B, slopes, κ̂) at INFO level through `utils.logging.get_logger`.
- `climate.py`, `backtest.py`, `trend.py`, `evaluate.py`, and `paths.py` do no I/O.
- Network access within the package:
  - `data/load.py:read_hf` calls `datasets.load_dataset`. `train`, `predict` and
    `validate-data` reach it when `data.source == "hf"`.
  - The `download-*` CLI commands run the scripts' `main()` in-process [cli.py].
  - Nothing in `src/` uploads to the Hub.

## Verification

- Run: `make check` (ruff + mypy + pytest with coverage)
- Targeted tests:
  `uv run pytest tests/test_climate.py tests/test_backtest.py tests/test_baselines.py tests/test_trend.py tests/test_trial.py tests/test_pipeline.py tests/test_station_metadata.py tests/test_forecasters.py tests/test_direct.py tests/test_adjust.py tests/test_round1_families.py -q`
