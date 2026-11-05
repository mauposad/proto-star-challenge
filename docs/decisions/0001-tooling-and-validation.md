# 0001: Tooling and validation scheme

- **Date:** 2026-11-05
- **Status:** accepted

## Context

Several teammates on different machines need identical environments, and the dataset and
metric weren't announced when the repo was set up.

## Decision

- **uv** with a committed `uv.lock` for environments (fast, cross-platform, reproducible).
  Heavy deps (torch, xarray) are opt-in extras.
- **Config-driven pipeline**: one YAML per experiment, validated by pydantic (unknown keys
  are errors).
- **sklearn estimator API** as the model contract, through a registry.
- **Time-based validation split** by default, since the task is forecasting.
- **Local run folders** (`runs/`) for experiment tracking, plus a shared markdown log.
  We can move to MLflow/W&B/Trackio if the team outgrows this.

## Consequences

Adding a model or feature never touches the train/predict code. Deep learning models need
a thin fit/predict wrapper. If the challenge needs a different validation scheme (e.g.
spatial holdout), add a `split.strategy` and record it in a new ADR.
