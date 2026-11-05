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

### challenge dataset (TBD)

- **Source / URL:**
- **Download:** `uv run python scripts/download_data.py` *(to write)*
- **License:**
- **Temporal / spatial coverage:**
- **Target & units:**
- **Official metric:**
- **Known issues:** (missing values, sensor errors, unit changes, ...)

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
