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
docs/               Data card, experiment log, design decisions (ADRs)
notebooks/          Exploration only. Naming: NN_initials_topic.ipynb
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
