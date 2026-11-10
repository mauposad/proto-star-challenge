# scripts

## Overview

Standalone Python command-line scripts for the ProtoStar climate challenge workflow. They
download the official tables, build the team's shared annual master table, join NOAA station
metadata, print backtest reference tables, and check a submission CSV. There is also a
synthetic dev-data generator and a general Hugging Face pipeline demo. Run them from the
repository root with `uv run python scripts/<name>.py`.

Most scripts connect functions from `src/proto_star/` to default paths under `data/`, built
from the constants in `src/proto_star/paths.py` (`RAW_DIR`, `INTERIM_DIR`, `PROCESSED_DIR`,
`EXTERNAL_DIR`). Some logic lives only here:

- `check_cutoff` and `download_missing` in `download_protostar_data.py` (tests import them).
- The manifest and `_cells_blanked` in `build_master_dataset.py`.
- All the checks in `check_submission.py`. That file is a vendored copy of the official
  CMU-OSPO submission template script [check_submission.py:module docstring].

In the repo checkout, all paths below are relative to the repository root
[src/proto_star/paths.py:PROJECT_ROOT]. Inside a built submission package, `PROJECT_ROOT`
resolves to the package root instead. See the packaged-copies note under Callers.

Typical order, from the script docstrings:

1. `download_protostar_data.py`
2. `build_master_dataset.py` [build_master_dataset.py:module docstring]
3. `compare_baselines.py` or `robustness_origins.py`, both of which read the master table
   [compare_baselines.py:module docstring]

Station metadata uses a second order: `download_ghcn_station_metadata.py`, then
`build_station_metadata_report.py`. The report also reads
`data/raw/protostar/city_info.parquet`, so `download_protostar_data.py` must run first
[build_station_metadata_report.py:main].

## Interface

| Script | Public symbols | Command line |
|---|---|---|
| [`build_master_dataset.py`](./build_master_dataset.py) | `main(destination=MASTER_DIR)`, `SOURCES` [build_master_dataset.py:main, SOURCES] | No arguments |
| [`build_station_metadata_report.py`](./build_station_metadata_report.py) | `main(city_path, station_path, output_path)`, all with default paths [build_station_metadata_report.py:main] | No arguments. Also run by `proto-star climate-metadata-report` [src/proto_star/cli.py:climate_metadata_report] |
| [`build_summer_means.py`](./build_summer_means.py) | `main()` [build_summer_means.py:main] | No arguments. Reads `data/raw/protostar/daily.parquet` and writes `data/interim/protostar/summer_means.parquet` |
| [`paired_bootstrap.py`](./paired_bootstrap.py) | `main()`, `ORIGINS` [paired_bootstrap.py:main] | Takes a trial YAML and `--origins official\|seven\|early`. Prints paired year-block bootstrap tables and writes nothing |
| [`check_submission.py`](./check_submission.py) | No functions. The checks are module-level code, with no `__main__` guard, so they run on import. Constants `TRAIN`, `COLUMNS`, `YEARS`, `METRICS` [check_submission.py:TRAIN, COLUMNS, YEARS, METRICS] | Optional CSV path. Defaults to `submission.csv` in the current directory [check_submission.py:path] |
| [`compare_baselines.py`](./compare_baselines.py) | `main()` [compare_baselines.py:main] | No arguments |
| [`download_ghcn_station_metadata.py`](./download_ghcn_station_metadata.py) | `main(destination=EXTERNAL_DIR / "noaa_ghcn_stations")`, `URL` [download_ghcn_station_metadata.py:main, URL] | No arguments. Also run by `proto-star download-station-metadata` [src/proto_star/cli.py:download_station_metadata] |
| [`download_protostar_data.py`](./download_protostar_data.py) | `main(destination=RAW_DIR / "protostar")`, `download_missing(destination, load=_load_hub_table, tables=TABLES) -> list[str]`, `check_cutoff(name, table, *, cutoff_year=FORECAST_CUTOFF)`, `REPO`, `TABLES`, `STATIC_TABLES` [download_protostar_data.py:main, download_missing, check_cutoff] | No arguments. Also run by `proto-star download-climate-data` [src/proto_star/cli.py:download_climate_data] |
| [`evaluate_metric_ensemble.py`](./evaluate_metric_ensemble.py) | `main(annual_path=RAW_DIR / "protostar" / "annual_indices.parquet")` [evaluate_metric_ensemble.py:main] | No arguments |
| [`hf_pipeline_demo.py`](./hf_pipeline_demo.py) | `TASKS`, `parse_args()`, `run_once(pipe, args, text)`, `main()` [hf_pipeline_demo.py:TASKS, parse_args, run_once, main] | See the flags below |
| [`make_synthetic_data.py`](./make_synthetic_data.py) | `main()` [make_synthetic_data.py:main] | No arguments |
| [`robustness_origins.py`](./robustness_origins.py) | `ORIGINS`, `main()` [robustness_origins.py:ORIGINS, main] | Required trial YAML path, read from `sys.argv[1]`: `uv run python scripts/robustness_origins.py configs/<trial>.yaml` [robustness_origins.py:main] |

Flags for `hf_pipeline_demo.py`. Install its dependencies first with `uv sync --extra hf`
[hf_pipeline_demo.py:module docstring; pyproject.toml:project.optional-dependencies.hf].

- `task`: required. One of `sentiment`, `generate`, `summarize`, or `classify`
  [hf_pipeline_demo.py:task].
- `text`: optional. If you omit it, the script runs an interactive `> ` prompt that stops on
  an empty line, `quit`, EOF, or Ctrl-C [hf_pipeline_demo.py:text; hf_pipeline_demo.py:main].
- `--model`: Hub model ID. Defaults to the task's model in `TASKS` [hf_pipeline_demo.py:--model].
- `--labels`: comma-separated labels for `classify`. Default `positive,negative,neutral`
  [hf_pipeline_demo.py:--labels].
- `--max-new-tokens`: integer length limit for `generate`. Default `50`
  [hf_pipeline_demo.py:--max-new-tokens].
- Environment: `HF_TOKEN` is optional and is read only by name [hf_pipeline_demo.py:main].

Callers outside this directory:

- `src/proto_star/cli.py` imports `main` as `scripts.<module>` from three scripts and calls
  it with no arguments: `download_protostar_data`, `download_ghcn_station_metadata`, and
  `build_station_metadata_report` [src/proto_star/cli.py:download_climate_data,
  download_station_metadata, climate_metadata_report]. `scripts/` has no `__init__.py`.
  It is a namespace package that resolves only when the repository root is on `sys.path`.
  The editable install adds only `src/`, and the `proto-star` console script does not add
  the current directory. So `uv run proto-star download-climate-data`,
  `download-station-metadata` and `climate-metadata-report` should fail with
  `ModuleNotFoundError: scripts`. This was checked with `importlib.util.find_spec("scripts")`
  after removing the working directory from `sys.path`; the commands themselves were not
  run. No test covers these commands. Use `uv run python scripts/<name>.py` instead.
- `.github/workflows/publish.yml`:
  - runs `scripts/download_protostar_data.py` and `scripts/build_master_dataset.py` by path;
  - runs the packaged `code/check_submission.py`;
  - asserts that `code/scripts/` holds at least 4 `.py` files.
- Error messages name these scripts as the fix: `src/proto_star/data/master.py:load_master`
  and `src/proto_star/data/protostar.py:_path`. So does the trial-note template
  (`src/proto_star/trial.py`).
- `src/proto_star/submission_package.py` copies five scripts by file name
  [src/proto_star/submission_package.py:_copy_code]:
  - into `code/scripts/`: `download_protostar_data.py` and `build_master_dataset.py`
    (`PIPELINE_SCRIPTS`), plus `compare_baselines.py` and `evaluate_metric_ensemble.py`
    (`EVIDENCE_SCRIPTS`)
  - into `code/`: `check_submission.py`
  - The packaged copies import `proto_star`. Only the generated `code/reproduce.py` puts
    `code/src` on `sys.path`, and `requirements.txt` does not pin `proto-star` itself.
    Inside a package, `RAW_DIR` and `MASTER_DIR` point to `<package>/data/raw/...` and
    `<package>/data/processed/...`, while the package's `data/` folder is flat
    [src/proto_star/submission_package.py:_copy_code, _copy_data, _runtime_pins].
- `download_missing` takes a `load` callable in place of the Hub loader, which is how the
  tests run it offline [download_protostar_data.py:download_missing;
  tests/test_download_protostar.py:_script].
- There are no subdirectories.

## Invariants

- **2018 cutoff before any write.** `download_missing` loads every missing table and runs
  `check_cutoff` on each before it creates the destination or writes a file. A post-cutoff
  table raises `ClimateDataError` and nothing is written
  [download_protostar_data.py:download_missing]. How each table is checked
  [download_protostar_data.py:check_cutoff; src/proto_star/climate.py:FORECAST_CUTOFF]:
  - `annual_indices` goes through `annual_to_long`.
  - `city_info` is exempt (`STATIC_TABLES`).
  - All other tables go through `assert_weather_cutoff`.
- **Raw ProtoStar tables are never overwritten.** Only tables whose
  `<destination>/<name>.parquet` is missing are downloaded and written. `SOURCE.txt` is
  written only if it is absent [download_protostar_data.py:download_missing].
- **NOAA external data is never overwritten.** If the destination exists and is not empty,
  `main` raises `FileExistsError`. `mkdir(exist_ok=False)` also raises `FileExistsError` when
  the destination exists but is empty. If the download or parse fails, `main` deletes the
  partial `ghcnd-stations.txt`, removes the destination directory, and re-raises
  [download_ghcn_station_metadata.py:main]. The cleanup catches only `Exception`.
  A Ctrl-C during the download therefore leaves a partial file, and the next run refuses to
  start. `rmdir` removes only the leaf directory.
- **The master table is verified before it is written.** `main` calls
  `verify_master(master, annual)` before any file write. That function raises
  `ClimateDataError` for any of these [build_master_dataset.py:main;
  src/proto_star/data/master.py:verify_master]:
  - `assert_weather_cutoff(master, name="annual_master")` fails (a year after 2018). The
    inputs are also cutoff-checked on load by `load_annual`, `load_coverage` and
    `load_daily`
  - the row count differs from the raw table
  - duplicate `ID`/`Year` rows
  - infinite values remain
  - a value the official scoring screen keeps has changed
- **Submission format.** `check_submission.py` requires the following
  [check_submission.py:COLUMNS, YEARS, METRICS, checks, expected]:
  - The columns are exactly `city_id,year,metric,predicted_value`, in that order.
  - Every `city_id` is in the Hub `city_info` `ID` set.
  - `year` is between 2019 and 2025.
  - `metric` is one of `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, or `cdd`.
  - `predicted_value` is numeric and finite.
  - No `(city_id, year, metric)` row is duplicated.
  - The row count equals cities x 7 x 4. This is checked only when no other problem was found.

  A column mismatch exits first with `Columns must be exactly: ... (found: ...)` and skips
  the other checks. Other failures are collected and exit with a `Not ready:` message. Both
  print to stderr and exit with status 1 via `sys.exit`. On success it prints an `OK:` line
  [check_submission.py:sys.exit].
- **Backtest folds.** `compare_baselines.py` uses the default `DEFAULT_CUTOFFS = (1980, 1995,
  2011)` and summarizes against `current_best = ensemble_forecaster()` [compare_baselines.py:main;
  src/proto_star/backtest.py:compare_forecasters; src/proto_star/climate.py:DEFAULT_CUTOFFS].
  `robustness_origins.py` adds the origins 1985, 1990, 2000, and 2005, giving `ORIGINS` =
  1980, 1985, 1990, 1995, 2000, 2005, 2011. It reports `mean_official` over `DEFAULT_CUTOFFS`
  separately from `mean_all`. The official folds stay as they are (ADR 0004)
  [robustness_origins.py:ORIGINS, main; robustness_origins.py:module docstring].
- **Ensemble selection.** `evaluate_metric_ensemble.py` picks per-metric methods with
  `select_metric_methods`, using backtests on `DEFAULT_CUTOFFS`, then scores the ensemble on
  the same `DEFAULT_CUTOFFS` [evaluate_metric_ensemble.py:main].
- **Keep the external entry points stable.** The three CLI-linked scripts must keep a `main`
  that works with no arguments [src/proto_star/cli.py:download_climate_data,
  download_station_metadata, climate_metadata_report]. The five packaged scripts must keep
  their file names [src/proto_star/submission_package.py:PIPELINE_SCRIPTS, EVIDENCE_SCRIPTS,
  _copy_code].
- **Seeds.** `make_synthetic_data.py` is deterministic, with `seed=0` by default
  [src/proto_star/data/synthetic.py:make_weather]. `hf_pipeline_demo.py`'s `generate` task
  uses `do_sample=True` with no seed, so its output varies between runs
  [hf_pipeline_demo.py:run_once].
- **Static checks.** mypy is configured with `files = ["src"]` [pyproject.toml:tool.mypy] and
  follows imports. It therefore also checks the three scripts that `cli.py` imports:
  `download_protostar_data`, `download_ghcn_station_metadata` and
  `build_station_metadata_report`, which appear in `.mypy_cache`. The other seven scripts are
  not type-checked. Ruff lints the whole repository [Makefile:lint]. `hf_pipeline_demo.py`
  has no type hints [hf_pipeline_demo.py:parse_args, run_once, main].
- **Run order is partly enforced.** `build_master_dataset.py`, `compare_baselines.py` and
  `robustness_origins.py` read through `load_master` or `_path`. When an input is missing,
  those raise `FileNotFoundError` naming the script to run first
  [src/proto_star/data/master.py:load_master; src/proto_star/data/protostar.py:_path].
  `evaluate_metric_ensemble.py` and `build_station_metadata_report.py` read with
  `pd.read_parquet` / `read_fwf` directly, so their errors name no script.
- **`robustness_origins.py` needs its argument.** Without one, `sys.argv[1]` raises
  `IndexError` and no usage message is printed [robustness_origins.py:main].

## Side Effects

| Script | Reads | Writes | Network |
|---|---|---|---|
| `download_protostar_data.py` | Checks whether `data/raw/protostar/<table>.parquet` and `SOURCE.txt` exist [download_protostar_data.py:download_missing] | `data/raw/protostar/<table>.parquet`, only for missing tables. `data/raw/protostar/SOURCE.txt`, only if absent, even when no table was missing [download_protostar_data.py:download_missing] | Downloads Hub dataset `CMU-OSPO/protostar-climate-train-to-2018` (configs `annual_indices`, `city_info`, `daily`, `coverage_and_stations`, split `train`), only for missing tables [download_protostar_data.py:_load_hub_table, REPO, TABLES] |
| `download_ghcn_station_metadata.py` | Parses the downloaded file to validate it [download_ghcn_station_metadata.py:main] | `data/external/noaa_ghcn_stations/ghcnd-stations.txt` and `SOURCE.txt` [download_ghcn_station_metadata.py:main] | HTTPS GET of `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt` via `urlretrieve` [download_ghcn_station_metadata.py:URL] |
| `build_master_dataset.py` | `data/raw/protostar/annual_indices.parquet`, `coverage_and_stations.parquet`, and `daily.parquet`. The `load_daily` docstring puts the full daily table at about 10M rows. Re-reads all three to SHA-256 them [build_master_dataset.py:main, _sha256; src/proto_star/data/protostar.py:load_daily] | Overwrites `data/processed/protostar/annual_master.parquet` and `annual_master.manifest.json`, with no existence check. Prints the manifest. Its keys are `rows`, `cities`, `first_year`, `last_year`, `content_hash`, `cells_blanked`, `valid_rows`, `sources_sha256` and `built_by`. `submission_package._data_card` reads `content_hash` and `sources_sha256` [build_master_dataset.py:main; src/proto_star/data/master.py:MASTER_DIR, MASTER_FILE, MANIFEST_FILE] | None |
| `build_station_metadata_report.py` | `data/raw/protostar/city_info.parquet`, `data/external/noaa_ghcn_stations/ghcnd-stations.txt` [build_station_metadata_report.py:main] | Overwrites `data/interim/protostar_station_metadata.parquet` [build_station_metadata_report.py:main] | None |
| `compare_baselines.py` | `data/processed/protostar/annual_master.parquet` via `load_master` [compare_baselines.py:main] | None. Prints to stdout only | None |
| `evaluate_metric_ensemble.py` | `data/raw/protostar/annual_indices.parquet` via `pd.read_parquet` [evaluate_metric_ensemble.py:main] | None. Prints methods and CSV to stdout | None |
| `robustness_origins.py` | The trial YAML at `sys.argv[1]` via `load_trial_config`, and `annual_master.parquet` via `load_master` [robustness_origins.py:main] | None. Prints two raw-score tables to stdout, for windows `all` and `years_4_7` [robustness_origins.py:main] | None |
| `check_submission.py` | The CSV at `sys.argv[1]`, or `./submission.csv` [check_submission.py:path, df] | None | Reads `hf://datasets/CMU-OSPO/protostar-climate-train-to-2018/city_info` at import time [check_submission.py:TRAIN, cities] |
| `hf_pipeline_demo.py` | The `HF_TOKEN` environment variable, and stdin in interactive mode [hf_pipeline_demo.py:main] | No file writes in the script itself. Library side effects: `huggingface_hub.login` stores the token in the local Hugging Face token file, which AGENTS.md's secrets rule applies to, and `transformers` caches downloaded models outside the repo | Calls `huggingface_hub.login(token=...)` only if `HF_TOKEN` is set, which also validates the token with the Hub. `transformers.pipeline(...)` downloads the selected Hub model; the defaults are in `TASKS` [hf_pipeline_demo.py:main, TASKS] |
| `make_synthetic_data.py` | None | Overwrites `data/raw/synthetic/train.parquet` and `test.parquet`, with no existence check [make_synthetic_data.py:main]. The rows are daily from 2018-01-01 for 1,500 days, which runs past 2018-12-31 [src/proto_star/data/synthetic.py:make_weather] | None |

- No script uploads to or modifies the Hugging Face Hub. There are no `push_to_hub`,
  `upload_file`, `upload_folder`, `create_repo`, `HfApi`, or `create_commit` calls in
  `scripts/`.
- Every script that writes creates its output directory with `mkdir(parents=True, ...)`
  [build_master_dataset.py:main; build_station_metadata_report.py:main;
  download_protostar_data.py:download_missing; download_ghcn_station_metadata.py:main;
  make_synthetic_data.py:main].
- Three scripts write under `data/raw/` or `data/external/`, which AGENTS.md treats as
  immutable:
  - `download_protostar_data.py` skips existing files.
  - `download_ghcn_station_metadata.py` refuses a non-empty destination.
  - `make_synthetic_data.py` overwrites without checking.

## Verification

- Run: `make check` (ruff lint, mypy on `src/`, pytest)
- Targeted: `uv run pytest tests/test_download_protostar.py -q`. It loads
  `download_protostar_data.py` with `importlib` and runs `download_missing` on `tmp_path` with a
  fake loader, so it needs no network. It checks that existing tables are untouched and that
  post-cutoff rows are rejected before any write [tests/test_download_protostar.py:test_download_missing_writes_only_absent_tables,
  test_download_missing_rejects_post_cutoff_rows_before_writing].
- Targeted: `uv run pytest tests/test_trial.py::test_package_has_the_layout_the_challenge_asks_for -q`.
  It checks only that the packaged copies of the five scripts exist. It does not run them.
- No other script in this directory has a test.
