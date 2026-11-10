# EGM Drift Report: 2026-11-09

Scope: the 7 contract files written or edited by `egm-bootstrap` on branch `agent/egm-contracts`.
Three read-only reviewers checked each contract against the source. Each bullet is a divergence
they found, and each was corrected in the contract the same day. Findings marked **(code)** are
real defects in the code. They are documented in the READMEs but not fixed, because the bootstrap
is documentation-only.

## README.md (root blueprint sections)

- [hallucination] The README said "No code uploads to the Hub". In fact
  `.github/workflows/publish.yml` calls `HfApi.create_repo` and `upload_folder` when it is
  dispatched manually with `upload=true`. Corrected in the System Overview and in Global Side
  Effects.
- [hallucination] The README said "Raw data is never overwritten". In fact
  `scripts/make_synthetic_data.py` rewrites `data/raw/synthetic/` on every run. Corrected.
- [imprecise] Cut-off: the README said every weather table goes through
  `assert_weather_cutoff`. Instead, `annual_indices` is checked by `annual_to_long`. The generic
  `data/load.py` loaders and the NOAA download apply no cut-off check. Corrected.
- [imprecise] Validation scheme: only trial configs are locked. `climate-backtest --cutoff`
  and `robustness_origins.py` use other origins. Corrected.
- [imprecise] `official_score` scores against whatever reference its caller passes. The
  reference is `thirty_year_mean` because every caller passes it. Corrected.
- [imprecise] `verify_master` does not compare every row; it checks counts, duplicates,
  infinite values, the cut-off, and the long table. The data-flow diagram also implied that
  `build_package` consumes the `runs/trials/` output, which it does not. Corrected.
- [missing] The README omitted `.github/`, `code/` and `reports/figures/`, three scripts, the
  cwd-relative submission CSVs, the HF cache and token writes, and the `set_seed` environment
  side effect. Added.

## src/README.md

- [missing] The README did not say that the package works only as an editable install inside
  the repo. The reasons are the `PROJECT_ROOT` derivation, the CLI imports of `scripts.*`, and
  `submission_package` reading `scripts/`, `AGENTS.md` and `docs/submission/`. Added.

## src/proto_star/README.md

- [missing] Undocumented constants: `HINGE_MIN_*` and the `linear_trend` and `hinge_fit`
  fallbacks; `TEMPERATURE`, `CDD`, `FLAT_METHOD`; the `Metric` alias; and the
  `submission_package` layout constants. Added.
- [missing] Undocumented validation: `PooledTrendSpec` and the forecast formula, the `TrialConfig`
  name pattern and non-empty `forecasters`, and the `exist_ok=False` collisions in run, trial
  and package directories. Added.
- [missing] Undocumented error cases in `official_score` and `_prediction_frame`, plus the
  `build_package` and `verify_package` failure modes and the `OK:` print. Added.
- [imprecise] The `build_package` side-effect list was incomplete. It also writes `trial.yaml`,
  `reproduce.py`, `check_submission.py`, `README.md` and the manifest; reads `team.yaml`, the
  policy docs and package metadata; and re-runs the backtest. Corrected.
- [imprecise] The README said "no network calls itself", which contradicts
  `data/load.py:read_hf` inside the package. Corrected.
- [imprecise] **(code)** `download-climate-data`, `download-station-metadata` and
  `climate-metadata-report` import top-level `scripts.*`. Through the `proto-star` console
  script that package is not on `sys.path`: `importlib.util.find_spec("scripts")` returns
  `None` once cwd is removed, and the editable `.pth` adds only `src/`. Expect
  `ModuleNotFoundError`. This finding comes from `find_spec`; the commands themselves were not
  run, and no test covers them. Documented as a known defect.

## src/proto_star/data/README.md

- [imprecise] The README said `MANIFEST_FILE` was "not referenced elsewhere". In fact
  `submission_package.py` and `scripts/build_master_dataset.py` use it. Corrected.
- [imprecise] The callers list was incomplete. It was missing `compare_baselines.py`,
  `robustness_origins.py`, the EDA notebooks, and `make_synthetic_data.py`. Corrected.
- [missing] The master table's `region` is stored as plain `str`, not as the categorical that
  `assign_region` returns. This affects the schema and `content_hash`. Added.

## src/proto_star/models/README.md

- [imprecise] The registry import happens at `__init__.py` line 1, not through `__all__`.
  Corrected.
- [imprecise] `test_train_then_predict_end_to_end` also runs a real fit and predict (only for
  `ridge`). Corrected.

## src/proto_star/utils/README.md

No drift detected.

## scripts/README.md

- [hallucination] The README said "mypy checks only `src/`, so these scripts are not
  type-checked". In fact mypy follows `cli.py`'s imports and checks the three CLI-linked
  scripts (confirmed in `.mypy_cache/3.12/scripts/`). Corrected.
- [imprecise] **(code)** The "Also run by `proto-star ...`" entries are subject to the
  `scripts` import defect above. Documented.
- [missing] Callers in `.github/workflows/publish.yml`, error messages and trial notes that
  depend on the script file names. Added.
- [missing] The manifest keys (`rows`, `cities`, `first_year`, `last_year`, `content_hash`,
  `cells_blanked`, `valid_rows`, `sources_sha256`, `built_by`), which
  `submission_package._data_card` reads. Added.
- [imprecise] The README said the scripts hold "no reusable logic". Some do: `check_cutoff`,
  `download_missing`, the manifest, and the vendored checks in `check_submission.py`.
  Corrected.
- [missing] The README left out the `verify_master` cut-off check and the cut-off checks the
  loaders run first. Added.
- [imprecise] `check_submission.py` exits with a separate `Columns must be exactly ...`
  message before the `Not ready:` path. Corrected.
- [imprecise] Run order is enforced only for scripts that use `load_master` or `_path`. The
  station-metadata report also needs `city_info.parquet`. Corrected.
- [missing] Side effects of `hf_pipeline_demo.py`: `login` stores the token locally, and
  models go to the HF cache. Also missing: `robustness_origins.py` prints two tables and
  raises `IndexError` when called without an argument. Added.
- [imprecise] NOAA cleanup catches only `Exception`, so a Ctrl-C leaves a partial file that
  blocks the next run. Added.
- [missing] How the packaged copies behave: `sys.path`, `PROJECT_ROOT` and the flat `data/`
  layout. Added.

## Suggested follow-ups (human decision)

- Fix the `scripts.*` imports in `src/proto_star/cli.py`, for example by moving the three
  `main()` functions into the package. Add a CLI test for those commands.
- Decide whether `make_synthetic_data.py` should write under `data/raw/`, given the
  immutability rule in AGENTS.md.
