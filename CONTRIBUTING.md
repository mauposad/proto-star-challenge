# Contributing

## Workflow

1. **Pick up or open an issue** (use the Experiment template for modeling ideas).
2. **Branch from `main`**: `<initials>/<short-topic>`, e.g. `mp/lag-features`.
3. **Commit small, focused changes.** Message format: imperative summary line
   (`Add lag features for max_temp`), optional body explaining *why*.
4. **Open a PR** and fill in the template. At least one teammate reviews before merge.
   Squash-merge into `main`.
5. `main` must always pass `make check`. CI enforces this.

Never commit: data files, model weights, `.env` / tokens, notebook outputs. The `.gitignore` and
pre-commit hooks guard against this, so don't bypass them with `--no-verify`.

## Environment

- **uv is the only package manager.** Don't `pip install` into `.venv`.
- Add a dependency: `uv add <pkg>` (or `uv add --group dev <pkg>` for tooling). Commit
  `pyproject.toml` **and** `uv.lock` together.
- After pulling: `uv sync`.
- Run anything through the env: `uv run <cmd>`, or activate `.venv` yourself.

## Coding standards

- **Python 3.12, type hints on all public functions.** `mypy` runs in CI.
- **ruff** handles formatting and linting (line length 100). `make format` fixes most issues.
- **Reusable code goes in `src/proto_star/`, not notebooks.** If two notebooks need the same
  function, move it into the package and add a test.
- **No hard-coded paths.** Use `proto_star.paths` and config files.
- **No magic numbers in training code.** Hyperparameters belong in `configs/*.yaml`.
- **Tests:** every new data transform or model gets at least one test in `tests/`. Keep
  tests fast (seconds) with small synthetic data. Mark anything slow with `@pytest.mark.slow`.
- **Docstrings** explain *why* or *what the contract is*, not a restatement of the code.

## Data engineering practices

See [docs/data.md](docs/data.md). The essentials:

- `data/raw/` is **immutable**. Never edit it by hand; write a script that reads raw and
  writes to `interim/` or `processed/`.
- Every dataset gets an entry in `docs/data.md`: source, download command, license, schema.
- Data processing must be **reproducible from a script** in `scripts/` or the package.
- `proto_star.data.validate` runs before every training and prediction. When you discover a
  new failure mode in the data, add a check for it.

## Model building practices

- **Baselines first.** Every new model is compared against `mean_baseline` and the current
  best on the same validation split.
- **Validate like the leaderboard.** Forecasting uses a **time-based split** (train on the
  past, validate on the future). Don't use a random split without a written reason.
- **No leakage.** Features can only use information available at prediction time. No
  centered rolling windows, no statistics computed over train + validation together, no
  future values.
- **One experiment = one config file** in `configs/` named `<initials>_<description>.yaml`.
  Copy `configs/baseline.yaml` to start.
- **Fix seeds.** `seed` is in every config; `set_seed` is called for you.
- **Log every result worth sharing** in `docs/experiments.md`, including negative results.
  Runs record their git commit, so commit before a run you plan to report.
- **Add models via the registry** (`src/proto_star/models/registry.py`) so train/predict code
  never changes.
- **Leaderboard submissions:** generate with `proto-star predict` (it validates format), and
  record each submission and its public score in `docs/experiments.md`. Don't tune against
  the public leaderboard; trust the validation split.

## Notebooks

Exploration only. Name them `NN_initials_topic.ipynb` (e.g. `01_mp_eda.ipynb`). Outputs are
stripped automatically on commit. Start each notebook with:

```python
%load_ext autoreload
%autoreload 2
from proto_star.paths import RAW_DIR
```

## Documenting decisions

Non-obvious team decisions (metric choice, validation scheme, dropping a data source) get a
short ADR in `docs/decisions/`. Copy `0000-template.md`.
