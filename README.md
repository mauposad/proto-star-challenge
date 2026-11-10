# proto-star-challenge

AI systems to analyze extreme weather trends and recommend climate adaptation strategies.
Challenge to build a forecast AI model in collaboration with CMU OSPO and Hugging Face.

## Quickstart

```bash
# 1. Install uv (once per machine): https://docs.astral.sh/uv/
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and set up (creates .venv with pinned Python 3.12 + all deps, installs git hooks)
git clone git@github.com:mauposad/proto-star-challenge.git
cd proto-star-challenge
make setup            # = uv sync && uv run pre-commit install
cp .env.example .env  # then add your HF_TOKEN

# 3. Smoke-test the pipeline on synthetic data
uv run python scripts/make_synthetic_data.py
uv run proto-star train configs/baseline.yaml
uv run proto-star predict runs/<run-dir-printed-above>
```

Optional extras: `uv sync --extra hf` (torch + transformers), `uv sync --extra geo`
(xarray/NetCDF/Zarr for gridded climate data).

## Repository layout

```
configs/            One YAML per experiment. The config *is* the experiment.
data/               Git-ignored. raw/ (immutable) -> interim/ -> processed/. See docs/data.md
docs/               Data card, experiment log, trial write-ups, design decisions (ADRs)
notebooks/          Exploration only. Naming: NN_initials_topic.ipynb
papers/             Research papers we reproduce: paper cards, index of architectures and scores
runs/               Git-ignored. One folder per training run (model, metrics, config, git sha)
scripts/            One-off utilities (data download, synthetic data, demos)
src/proto_star/     The package. Reusable code lives here, not in notebooks
  data/             load -> validate -> features -> split
  models/           Model registry (sklearn-style fit/predict)
  train.py          config -> fitted model + metrics in runs/
  predict.py        run -> validated leaderboard submission in submissions/
  evaluate.py       Metrics
submissions/        Git-ignored. Leaderboard CSVs
tests/              pytest suite, run in CI on every PR
```

## Common commands

| Command | What it does |
|---|---|
| `make check` | Lint, type-check, test (same as CI) |
| `make format` | Auto-fix lint and formatting |
| `uv run proto-star models` | List registered models |
| `uv run proto-star validate-data <config>` | Check data without training |
| `uv run proto-star train <config>` | Train, evaluate on validation split, save run |
| `uv run proto-star predict <run-dir>` | Write a validated submission CSV |
| `uv add <pkg>` | Add a dependency (updates `pyproject.toml` + `uv.lock`; commit both) |
| `uv run jupyter lab` | Notebooks, using the project environment |

## AI coding agents

Agents (Claude Code, Codex, Cursor, Copilot, ...) must follow [AGENTS.md](AGENTS.md).
Claude Code also enforces the hard guardrails in `.claude/settings.json`; put personal
overrides in `.claude/settings.local.json` (git-ignored).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first PR. In short: branch from `main`,
one config per experiment, log results in [docs/experiments.md](docs/experiments.md), and
`make check` must pass.

## Climate challenge workflow

The official CMU climate dataset and scoring rule are now supported alongside the
generic synthetic workflow:

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # shared cleaned table, see docs/data.md
uv run python scripts/compare_baselines.py      # numbers to beat, see notebooks/README.md
uv run proto-star climate-backtest data/raw/protostar/annual_indices.parquet
uv run proto-star climate-submission `
  data/raw/protostar/annual_indices.parquet data/raw/protostar/city_info.parquet
uv run proto-star climate-ensemble-submission `
  data/raw/protostar/annual_indices.parquet data/raw/protostar/city_info.parquet
uv run python scripts/download_ghcn_station_metadata.py
uv run python scripts/build_station_metadata_report.py
```

The final candidate selects a method per metric from rolling historical
backtests: 10-year mean for average temperature and CDD, 30-year climatology
for precipitation and hottest-day temperature. Never use the leaderboard or
post-2018 weather to tune a forecast.

### Trial -> submission, step by step

Full map of where everything lives: [docs/workflow.md](docs/workflow.md).

```bash
uv run proto-star climate-trial configs/<initials>_<name>.yaml --record   # backtest + write-up
uv run proto-star climate-package configs/<initials>_<name>.yaml          # submission folder
```

## System Overview

This is the architecture contract for agents and reviewers. Each code directory's README holds
its detailed contract: interface, invariants, side effects.

The challenge forecast is the main data flow. Each step names the function that does it:

```text
HF Hub dataset ──download_missing──▶ data/raw/protostar/*.parquet
    ──build_annual_master + verify_master──▶ data/processed/protostar/annual_master.parquet
    ──load_master──▶ backtest_forecaster (cut-offs 1980/1995/2011, official_score vs 30-yr mean)
    ──run_trial──▶ runs/trials/<stamp>_<name>/  (+ docs/trials/<name>.md with --record)

trial config + annual_master (+ manifest)
    ──build_package (re-runs the forecast and README backtest) + verify_package──▶
      submissions/<stamp>_<name>/
    ──▶ Hub dataset repo: uploaded by a person, or by the manually dispatched
        .github/workflows/publish.yml with upload=true
```

There is a second, separate generic tabular pipeline: `load_config` → `train` →
`runs/<stamp>_<name>/` → `predict` → `submissions/<run>.csv`. It uses sklearn models from the
registry. So far it has only been run on synthetic data.

## Subdirectories & System Boundaries

- `src`: [./src/README.md](./src/README.md). Source root of the `proto-star` package.
  - `src/proto_star`: [./src/proto_star/README.md](./src/proto_star/README.md). The climate
    workflow and the generic pipeline: cut-off, quality screen, score, backtests, pooled trend,
    trials, packaging.
  - `src/proto_star/data`: [./src/proto_star/data/README.md](./src/proto_star/data/README.md).
    Raw ProtoStar loaders and the annual master table, plus generic
    load/validate/features/split and synthetic data.
  - `src/proto_star/models`: [./src/proto_star/models/README.md](./src/proto_star/models/README.md).
    sklearn-API model registry: `mean_baseline`, `ridge`, `random_forest`, `hist_gbm`.
  - `src/proto_star/utils`: [./src/proto_star/utils/README.md](./src/proto_star/utils/README.md).
    `get_logger` and `set_seed`.
- `scripts`: [./scripts/README.md](./scripts/README.md). Standalone CLIs:
  - downloads of the ProtoStar data and NOAA station metadata
  - the master-table build and the station-metadata report (writes `data/interim/`)
  - baseline, ensemble and robustness reports
  - the submission check
  - the synthetic-data writer (`data/raw/synthetic/`)
  - an HF transformers demo
- `.github/`: `workflows/ci.yml` runs ruff, mypy and `pytest -m "not slow"`.
  `workflows/publish.yml` is manual only. It builds and checks a package, and uploads it
  when `upload=true`.
- Non-code directories:
  - `code/`: `code/AGENTS.md`, the team data rule that AGENTS.md refers to.
  - `reports/figures/`: figures.
  - `configs/`: one YAML per experiment or trial.
  - `docs/`: data card, experiment log, trials, ADRs, literature.
  - `notebooks/`: [./notebooks/README.md](./notebooks/README.md). EDA and the forecaster recipe.
  - `papers/`: [./papers/README.md](./papers/README.md). Replication index.
  - `tests/`: pytest suite.
  - `data/`, `runs/`, `submissions/`, `models/`: git-ignored artifacts.

## Global Invariants

- **2018 weather cut-off (ProtoStar data).** The raw loaders, `load_master` and `verify_master`
  call `assert_weather_cutoff`. `annual_indices` is checked by `annual_to_long`, which
  rejects years after 2018 instead of filtering them out. The ProtoStar download checks the
  cut-off before writing anything [src/proto_star/climate.py:assert_weather_cutoff,
  src/proto_star/climate.py:annual_to_long, scripts/download_protostar_data.py:download_missing].
  The generic tabular loaders (`data/load.py`) and the NOAA metadata download (static,
  non-weather) apply no cut-off check.
- **Raw ProtoStar and external data are not overwritten.** Existing ProtoStar tables are
  skipped, and the NOAA download refuses a non-empty destination
  [scripts/download_protostar_data.py:download_missing, scripts/download_ghcn_station_metadata.py:main].
  The exception is `scripts/make_synthetic_data.py`, which rewrites `data/raw/synthetic/` on
  every run.
- **Fixed validation scheme for trials.** Trial configs cannot change the backtest origins,
  `DEFAULT_CUTOFFS = (1980, 1995, 2011)`, or the 7-year horizon (ADR 0004)
  [src/proto_star/climate.py:DEFAULT_CUTOFFS, src/proto_star/trial.py:run_trial]. Diagnostics
  can use other origins: `climate-backtest --cutoff` [src/proto_star/cli.py:climate_backtest]
  and the 7 origins of `scripts/robustness_origins.py`.
- **Official score.** Skill per metric = 1 − MAE / MAE(reference). Score =
  100 × max(0, mean of the 4 skills) [src/proto_star/climate.py:official_score]. Every caller
  passes `thirty_year_mean` as the reference: the calendar window ending at the cut-off, or
  the last 30 valid years if that window is empty [src/proto_star/backtest.py:backtest_forecaster,
  src/proto_star/climate.py:_predict_group].
- **Forecaster contract.** A forecaster `(train, cutoff_year, forecast_years)` must compute
  everything from `train` and must cover every scored row [src/proto_star/backtest.py:_check_coverage].
- **Master table is leakage-free by construction.** It has no imputation, station adjustment or
  per-city statistics. `verify_master` checks the following against the raw table: the
  cut-off, equal row counts, no duplicate `ID`/`Year` rows, no ±inf values, and an identical
  quality-screened long table [src/proto_star/data/master.py:verify_master].
- **Submission contract.** Columns are `city_id, year, metric, predicted_value`. The file covers
  the official city set × 2019–2025 × 4 metrics, has no duplicates, and all values are finite
  [src/proto_star/climate.py:validate_submission, scripts/check_submission.py].

## Global Side Effects

- **Hugging Face Hub reads:**
  - `CMU-OSPO/protostar-climate-train-to-2018` [scripts/download_protostar_data.py:_load_hub_table].
  - `city_info`, when `check_submission.py` is imported [scripts/check_submission.py:TRAIN].
  - HF dataset configs [src/proto_star/data/load.py:read_hf].
  - The transformers demo [scripts/hf_pipeline_demo.py:main].
- **Hugging Face Hub writes:** only `.github/workflows/publish.yml`, when someone dispatches it
  manually with `upload=true`. It calls `HfApi.create_repo` and `upload_folder` with
  `delete_patterns=["code/*", "data/*"]`, using the `HF_TOKEN` repository secret. Nothing in
  `src/` or `scripts/` uploads.
- **Writes outside the repo:**
  - `datasets.load_dataset` and `transformers.pipeline` fill the local Hugging Face cache.
  - `huggingface_hub.login` in `hf_pipeline_demo.py` stores the token locally.
- **NOAA download** of `ghcnd-stations.txt` [scripts/download_ghcn_station_metadata.py:URL].
- **Local writes:**
  - `data/raw/protostar/`, `data/external/noaa_ghcn_stations/`, `data/processed/protostar/`,
    `data/interim/`, `data/raw/synthetic/` (all from scripts).
  - `runs/` [src/proto_star/train.py:train].
  - `runs/trials/` and `docs/trials/<name>.md` [src/proto_star/trial.py:run_trial].
  - `submissions/` [src/proto_star/predict.py:predict, src/proto_star/submission_package.py:build_package].
  - `submissions/protostar_baseline.csv` and `submissions/protostar_metric_ensemble.csv`,
    relative to the current directory [src/proto_star/cli.py:climate_submission,
    climate_ensemble_submission].
- **Environment:**
  - Importing the CLI loads `.env` [src/proto_star/cli.py].
  - `train` → `set_seed` seeds the global RNGs and sets `PYTHONHASHSEED`
    [src/proto_star/utils/seed.py:set_seed].
  - `git_info` runs read-only `git` subprocesses [src/proto_star/tracking.py:git_info].
- **Known defect (documented, not fixed):** the CLI commands `download-climate-data`,
  `download-station-metadata` and `climate-metadata-report` import the top-level
  `scripts` namespace. That package is not importable from the `proto-star` console script,
  so expect `ModuleNotFoundError` and use `uv run python scripts/<name>.py`. See
  [./scripts/README.md](./scripts/README.md).

## System Verification

- Run: `make check` (ruff lint and format check, mypy on `src/`, pytest with coverage)

## Method

TODO: describe the forecasting method and the backtest results that justify it.

## AI tools

TODO: list every AI tool used and what it was used for (code only, never forecast values).

## Policy idea

TODO: describe the climate adaptation policy idea.

## Feedback to the Ecosystem

TODO: feedback for the organizers, datasets, and tools used.
