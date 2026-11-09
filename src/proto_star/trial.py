"""Run one named research trial and leave a complete record of what was used.

A trial is a YAML file in ``configs/`` (see ``configs/mp_baselines_round1.yaml``).  Running it
scores the listed forecasters on the team's fixed backtest folds (ADR 0004) and writes:

* ``runs/trials/<stamp>_<name>/``: config copy, results, summary, metadata (git-ignored)
* ``docs/trials/<name>.md`` with ``record=True``: the committed write-up of that run

Cut-offs are deliberately not configurable.  Changing validation needs an ADR.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.backtest import (
    CURRENT_BEST,
    CURRENT_BEST_METHODS,
    Forecaster,
    compare_forecasters,
    resolve_forecaster,
    summarize_backtest,
)
from proto_star.climate import BASELINE_DESCRIPTIONS, DEFAULT_CUTOFFS, METRICS
from proto_star.data.master import content_hash, load_master
from proto_star.forecasters import get_kind
from proto_star.paths import PROJECT_ROOT, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.tracking import git_info, write_json
from proto_star.trend import PooledTrendSpec, describe_pooled_trend


class ModelEntry(BaseModel):
    """A plug-in model: a kind registered in ``proto_star.forecasters`` and its settings."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    params: dict[str, Any] = Field(default_factory=dict)


class TrialConfig(BaseModel):
    """What a trial compares.  Forecasting logic lives in code, not here."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9_]+$")
    description: str
    forecasters: list[str] = Field(min_length=1)
    ensembles: dict[str, dict[str, str]] = Field(default_factory=dict)
    pooled_trends: dict[str, PooledTrendSpec] = Field(default_factory=dict)
    models: dict[str, ModelEntry] = Field(default_factory=dict)
    reference: str = CURRENT_BEST  # what "beats the baseline" is counted against
    submit: str | None = None  # forecaster to package; pick it from validation results only

    @model_validator(mode="after")
    def _check_names(self) -> TrialConfig:
        known = set(self.forecasters)
        if self.reference not in known:
            raise ValueError(f"reference {self.reference!r} must be one of the forecasters")
        if self.submit is not None and self.submit not in known:
            raise ValueError(f"submit {self.submit!r} must be one of the forecasters")
        blocks: dict[str, set[str]] = {
            "ensembles": set(self.ensembles),
            "pooled_trends": set(self.pooled_trends),
        }
        for block, names in blocks.items():
            clash = sorted(names & set(self.models))
            if clash:
                raise ValueError(f"names {clash} are defined in both `models` and `{block}`")
        builtin = sorted(set(self.models) & {*BASELINE_DESCRIPTIONS, CURRENT_BEST})
        if builtin:
            raise ValueError(f"`models` names {builtin} shadow built-in forecasters")
        for name, entry in self.models.items():  # fail at load time, not mid-backtest
            try:
                get_kind(entry.kind).make_spec(entry.params)
            except ValueError as error:
                raise ValueError(f"model {name!r}: {error}") from error
        return self


def load_trial_config(path: Path) -> TrialConfig:
    """Read and validate a trial config."""
    return TrialConfig.model_validate(yaml.safe_load(path.read_text()))


def build_forecasters(cfg: TrialConfig) -> dict[str, Forecaster]:
    """Turn the names in a config into callable forecasters."""
    models = {name: (entry.kind, entry.params) for name, entry in cfg.models.items()}
    return {
        name: resolve_forecaster(name, cfg.ensembles, cfg.pooled_trends, models)
        for name in cfg.forecasters
    }


def describe_forecaster(name: str, cfg: TrialConfig) -> str:
    """One line saying what a forecaster does, for notes and READMEs."""
    if name in cfg.models:
        entry = cfg.models[name]
        return get_kind(entry.kind).make_spec(entry.params).describe()
    if name in cfg.pooled_trends:
        return describe_pooled_trend(cfg.pooled_trends[name])
    if name in cfg.ensembles:
        return "Per metric: " + ", ".join(f"{m}={cfg.ensembles[name][m]}" for m in METRICS)
    if name == CURRENT_BEST:
        return "Per metric: " + ", ".join(f"{m}={CURRENT_BEST_METHODS[m]}" for m in METRICS)
    return BASELINE_DESCRIPTIONS[name]


def markdown_table(frame: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub table."""
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    divider = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in frame.to_numpy().tolist()]
    return "\n".join([header, divider, *rows])


def _summary_markdown(
    cfg: TrialConfig, config_path: Path, results: pd.DataFrame, meta: dict[str, Any]
) -> str:
    summary = summarize_backtest(results, baseline=cfg.reference)
    per_origin = (
        results.loc[results["window"] == "all"]
        .pivot_table(index="method", columns="cutoff_year", values="raw_score")
        .round(2)
        .reset_index()
    )
    definitions = pd.DataFrame(
        {
            "forecaster": cfg.forecasters,
            "definition": [describe_forecaster(n, cfg) for n in cfg.forecasters],
        }
    )
    window_tables = "\n\n".join(
        f"### {window}\n\n{markdown_table(frame.drop(columns='window'))}"
        for window, frame in summary.groupby("window", sort=False)
    )
    resolved = config_path.resolve()
    config_rel = (
        resolved.relative_to(PROJECT_ROOT) if resolved.is_relative_to(PROJECT_ROOT) else config_path
    )
    return f"""# Trial: {cfg.name}

{cfg.description}

## What was used

| Item | Value |
|---|---|
| Date | {meta["date"]} |
| Config | `{config_rel}` |
| Code version | `{meta["commit"]}`{" (uncommitted changes)" if meta["dirty"] else ""} |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `{meta["master_hash"]}` |
| Folds | cut-offs {list(DEFAULT_CUTOFFS)}, 7-year horizon (ADR 0004) |
| Reference | `{cfg.reference}` |
| Submit candidate | {f"`{cfg.submit}`" if cfg.submit else "none"} |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial {config_rel}
```

## Forecasters

{markdown_table(definitions)}

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `{cfg.reference}`.
`years_4_7` matches the Final Score; give it the most weight.

{window_tables}

### Raw score per origin (all forecast years)

{markdown_table(per_origin)}
"""


def run_trial(
    config_path: Path,
    *,
    master: pd.DataFrame | None = None,
    trials_dir: Path = TRIALS_DIR,
    notes_dir: Path = TRIAL_NOTES_DIR,
    record: bool = False,
) -> Path:
    """Score a trial config and return the run directory holding its record."""
    cfg = load_trial_config(config_path)
    data = load_master() if master is None else master
    results = compare_forecasters(build_forecasters(cfg), data, cutoffs=DEFAULT_CUTOFFS)

    now = datetime.now()
    meta: dict[str, Any] = {
        **git_info(),
        "date": now.strftime("%Y-%m-%d"),
        "master_hash": content_hash(data),
        "trial": cfg.name,
    }
    run_dir = trials_dir / f"{now.strftime('%Y%m%d-%H%M%S')}_{cfg.name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(config_path, run_dir / "config.yaml")
    results.to_csv(run_dir / "results.csv", index=False)
    write_json(run_dir / "meta.json", meta)
    summary = _summary_markdown(cfg, config_path, results, meta)
    (run_dir / "summary.md").write_text(summary)
    if record:
        notes_dir.mkdir(parents=True, exist_ok=True)
        (notes_dir / f"{cfg.name}.md").write_text(summary)
    return run_dir


def read_meta(run_dir: Path) -> dict[str, Any]:
    """Read the metadata saved by :func:`run_trial`."""
    meta: dict[str, Any] = json.loads((run_dir / "meta.json").read_text())
    return meta
