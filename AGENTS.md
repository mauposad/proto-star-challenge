# AGENTS.md

Rules for AI coding agents working in this repo. Humans: see CONTRIBUTING.md.
**MUST / NEVER rules are mandatory.** If a task conflicts with one, stop and ask the human.
Keep this file under 200 lines (CI enforces it).

## Project in one paragraph

Forecasting model for an extreme-weather challenge (CMU OSPO x Hugging Face), scored by a
leaderboard submission. Python 3.12 package `proto_star` in `src/`, managed with **uv**.
Pipeline: YAML config → load → validate → features → time split → fit → metrics → `runs/`,
then `predict` → validated CSV in `submissions/`. Real dataset and metric: see docs/data.md.
The challenge workflow lives in `src/proto_star/climate.py` and the `climate-*` CLI commands.

## Commands

```bash
uv sync                                    # install / update env after pulling
make check                                 # lint + mypy + tests. MUST pass before you finish
make format                                # auto-fix formatting and lint
uv run pytest tests/test_data.py -q        # run a subset
uv run proto-star models                   # list registered models
uv run proto-star validate-data <config>
uv run proto-star train <config>           # prints the run dir
uv run proto-star predict <run-dir>
uv run python scripts/make_synthetic_data.py   # dev data if data/raw/ is empty
```

## Where things go

| Change | Location |
|---|---|
| Data loading / cleaning | `src/proto_star/data/load.py`, scripts in `scripts/` |
| Data quality checks | `src/proto_star/data/validate.py` |
| Features | `src/proto_star/data/features.py` |
| New model | register in `src/proto_star/models/registry.py` (sklearn fit/predict API) |
| Metric | `src/proto_star/evaluate.py` |
| Scoring a climate forecast | `src/proto_star/backtest.py`, usage in `notebooks/README.md` |
| Hyperparameters / experiment | new file `configs/<initials>_<desc>.yaml` |
| Paths | `src/proto_star/paths.py`. Never hard-code paths |
| Tests | `tests/`, mirroring the module tested |
| Results | `docs/experiments.md` (append a row) |
| Team-level decisions | `docs/decisions/NNNN-title.md` (ADR) |

## Workflow (every task)

1. Read the relevant module(s) and their tests before editing. Match existing style.
2. Make the smallest change that solves the task. One concern per change.
3. Add or update tests for any new logic.
4. Run `make check`. Fix every failure. Do not finish with failing checks.
5. Report what you changed, what you ran, and the actual output (metrics, test results).
   If you skipped something or something failed, say so plainly.

## Guardrails: Git & collaboration

- **NEVER** push to `main`, force-push, rewrite published history, or delete branches.
  Work on a branch named `agent/<short-topic>` or the human's branch.
- **NEVER** commit or push unless the human asked. Never use `--no-verify`.
- **NEVER** modify another teammate's config, notebook, or ADR without being asked.
  Copy it into a new file instead.
- **NEVER** open/merge PRs, create releases, or post comments without explicit instruction.
- Commit messages: imperative summary (`Add lag features for max_temp`) + why in the body.

## Guardrails: Secrets & external actions

- **NEVER** read, print, log, or commit `.env`, tokens, or credentials. Use `HF_TOKEN` via
  environment only; never hard-code or echo it.
- **NEVER** submit to the leaderboard, push models/datasets to the Hugging Face Hub, or
  change Hub repo settings. These are outward-facing and human-only.
- **ASK FIRST** before downloading anything > 1 GB, starting training expected to run
  > 15 minutes, or using a GPU that teammates share.

## Guardrails: Environment & dependencies

- **uv only.** NEVER `pip install`, `conda install`, or create another venv.
- Add deps with `uv add <pkg>` (dev tools: `uv add --group dev <pkg>`). NEVER edit
  `uv.lock` by hand. Commit `pyproject.toml` and `uv.lock` together.
- **ASK FIRST** before adding any new dependency. Prefer what is already installed.
- Heavy deps (torch, transformers, xarray) belong in optional extras, not core deps.

## Guardrails: Data

- `data/raw/` and `data/external/` are **immutable**. NEVER edit, overwrite, or delete files
  there. Write transforms that read raw and output to `data/interim/` or `data/processed/`.
- **NEVER** commit data files, model weights (`*.joblib`, `*.pt`, `*.safetensors`), `runs/`,
  or `submissions/`. They are git-ignored. Do not force-add them.
- **NEVER** delete anything in `runs/` or `submissions/`. They are other people's results.
- Every data transform must be reproducible from code (no manual edits, no one-off shell
  pipelines that aren't saved as a script).
- When you find a new data problem, add a check in `validate.py` and a test for it.
- New datasets: document source, license, schema, and download command in docs/data.md.

## Guardrails: Challenge data rule (honor code)

- Forecasts are made as of 2018-12-31. Weather used as a forecast input MUST be dated on or
  before that day.
- **NEVER** download, query, or use weather observations dated 2019-01-01 or later from any
  source (NOAA, ACIS/ThreadEx, Meteostat, Open-Meteo, ERA5, weather sites).
- **NEVER** use 2019–2025 data driven by the weather (streamflow, air quality, energy demand,
  plant or disease data) as a forecast input. It may be used for analysis and policy only,
  marked "Analysis only" in the data card, and forecasting code must not read it.
- **NEVER** download the original source records (DOIs `10.1184/R1/7890488` and
  `10.1184/R1/7961012`, or their `CMU-OSPO` Hub copies). They run past 2018. Cite them only.
- Set an end date of 2018-12-31 or earlier on every weather download, and pass every weather
  input through `proto_star.climate.assert_weather_cutoff`.
- **NEVER** write or adjust `predicted_value` from memory, a web search, or an LLM, and never
  tune a method using knowledge of how 2019–2025 turned out. Every value comes from the code's
  model, and every modeling choice must be justified by a backtest on data through 2018.
- **NEVER** use a pretrained model unless its card shows training data ending before 2019.
  Declare its name, version, and cutoff in the submission README.
- If a task seems to need post-2018 weather, stop and ask a team member.

## Guardrails: Modeling (correctness over score)

- **No leakage.** Features may only use information available at prediction time:
  - rolling/lag features look backward only (`shift(k)` with k ≥ 1, no `center=True`)
  - fit scalers/imputers/encoders on train only. Put them inside the sklearn pipeline
  - never use the target, test rows, or future timestamps to build features
  - group-wise stats (per station, etc.) are computed on training rows only
- **NEVER** change the validation scheme (`split.strategy`, `valid_fraction`), the official
  metric, or the evaluation code to improve a score. These changes need an ADR and human
  approval.
- **NEVER** tune hyperparameters or select models using test data or leaderboard scores.
  Select on the validation split only.
- Every new model must be compared against `mean_baseline` and the current best in
  docs/experiments.md, on the same config/split. Report the numbers, including when worse.
- Seeds come from config (`seed`). Don't introduce unseeded randomness.
- Hyperparameters live in YAML configs, not in Python code.
- New models go through the registry. Do not special-case models in `train.py`/`predict.py`.
- Run training only through `proto-star train` so runs are tracked with config + git commit.

## Guardrails: Code quality

- Type hints on all public functions; mypy must pass. Don't add `# type: ignore` or
  `# noqa` without a short reason comment.
- Reusable logic goes in `src/proto_star/`, never only in a notebook or script.
- Match surrounding code: naming, docstring density, error style (raise specific errors
  with actionable messages; never silently swallow exceptions).
- Do not reformat or refactor unrelated code in the same change.
- Keep functions pure where possible (data in → data out). No global state.
- Do not change public interfaces (`train`, `predict`, config schema, model registry API)
  without updating every caller, tests, and docs in the same change.

## Guardrails: Tests

- **NEVER** delete, skip, weaken, or loosen tolerances on an existing test to make it pass.
  If a test is wrong, explain why and ask.
- Tests use small synthetic data (`proto_star.data.synthetic`), `tmp_path` for outputs,
  and run in seconds. Mark slow/network tests `@pytest.mark.slow`.
- Tests must never write to `data/`, `runs/`, or `submissions/`. Use `tmp_path`.

## Guardrails: Notebooks & docs

- Prefer editing `.py` modules over notebooks. If you create a notebook, name it
  `notebooks/NN_agent_topic.ipynb` and keep logic in the package.
- Update docs (README, docs/data.md, docs/experiments.md) when behavior changes.
- Never fabricate results, citations, dataset facts, or metric values. Unknown → write TBD.
- Agent instruction files (`AGENTS.md`, `CLAUDE.md`) stay under 200 lines. Edit them only
  when the human asks.

## When to stop and ask

- The task is ambiguous, or the requirement conflicts with a rule above.
- A fix would require changing validation, metrics, tests, or a public interface.
- You'd need to delete files, touch someone else's work, or take an external action.
- `make check` fails for reasons unrelated to your change.
- The same approach has failed twice. Don't loop; report what you tried.

## Definition of done

- [ ] `make check` passes (paste the summary line)
- [ ] Tests cover the new behavior
- [ ] No data, weights, secrets, or notebook outputs staged (`git status` clean of them)
- [ ] Docs / experiments log updated if relevant
- [ ] Summary to the human: what changed, why, commands run, real results, open risks
