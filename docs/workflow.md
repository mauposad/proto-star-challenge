# Workflow: from idea to leaderboard submission

One trial = one config file. Everything about it is found from that file's name.

| Step | Command | Where the result goes |
|---|---|---|
| 1. Define the trial | copy `configs/mp_baselines_round1.yaml` to `configs/<initials>_<name>.yaml` | the config *is* the record of what was compared |
| 2. Add logic (if new) | a new model kind is one module in `src/proto_star/forecasters/` (see below); baselines go in `climate.py`. Add a test | tests in `tests/` |
| 3. Run it | `uv run proto-star climate-trial configs/<initials>_<name>.yaml --record` | `runs/trials/<stamp>_<name>/` (git-ignored: config copy, `results.csv`, `summary.md`, `meta.json`) and **`docs/trials/<name>.md`** (committed write-up) |
| 4. Log it | append a row to [experiments.md](experiments.md), failures included | `docs/experiments.md` |
| 5. Pick the winner | set `submit:` in the config, from validation results only | the config |
| 6. Package it | `uv run proto-star climate-package configs/<initials>_<name>.yaml` | `submissions/<stamp>_<name>/` (git-ignored) |
| 7. Fill in the blanks | team names, AI-tool disclosure; the command prints each `TODO before upload` | the folder's `README.md` |
| 8. Upload and submit | a person copies the folder into the Hugging Face dataset and pastes the link in the Space | [release checklist](submission/release-checklist.md) |

## Adding a model kind

Write `src/proto_star/forecasters/<kind>.py` with a settings class (a `ForecasterSpec` with a
`describe()` method), a build function that returns `forecaster(train, cutoff_year,
forecast_years)`, and one `register_kind("<kind>", Spec, build)` call. The package finds the
module by itself, so no shared file is edited. Name it in a trial config:

```yaml
models:
  my_model_w15: {kind: my_kind, params: {window: 15}}
```

`params` are checked against the settings class when the config loads. See
`src/proto_star/forecasters/pooled_trend.py` for a complete example.

## What a trial note records (`docs/trials/<name>.md`)

Date, config path, git commit (and whether the tree was dirty), the master table's content
hash, the folds, every forecaster with a one-line definition, and the full results by
window. To redo a trial: build the master table, check the hash, run step 3.

## What the submission folder holds

```
submissions/<stamp>_<name>/
  submission.csv      5,880 rows, validated
  README.md           method, backtest evidence, policy idea, feedback, how to reproduce
  code/               src/proto_star, scripts/, trial.yaml, requirements.txt, reproduce.py, AGENTS.md
  data/               annual_master.parquet + manifest, annual_indices, city_info, data card
```

`climate-package` rebuilds `submission.csv` from `code/` and `data/` before it finishes and
fails if they differ. A reader can repeat that with `python code/reproduce.py`.

## Fixed rules

- Folds are 1980, 1995, 2011 with a 7-year horizon (ADR 0004). Trial configs cannot change them.
- Select on the backtest only. Never on leaderboard scores or post-2018 data.
- Only a person uploads to the Hub and submits the link.

## Where each piece of code lives

| Thing | File |
|---|---|
| Baselines and the official score | `src/proto_star/climate.py` |
| Fold runner, forecaster registry, `build_submission` | `src/proto_star/backtest.py` |
| Trial config, run record, write-up | `src/proto_star/trial.py` |
| Submission folder and reproduction check | `src/proto_star/submission_package.py` |
| CLI commands `climate-trial`, `climate-package` | `src/proto_star/cli.py` |
