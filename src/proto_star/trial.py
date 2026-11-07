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
from proto_star.forecasters import RegisteredForecaster, load_all
from proto_star.paths import PROJECT_ROOT, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.tracking import git_info, write_json


class Variant(BaseModel):
    """A registered forecaster run with hyperparameters from the config."""

    model_config = ConfigDict(extra="forbid")

    forecaster: str  # name registered in proto_star.forecasters
    params: dict[str, Any] = Field(default_factory=dict)


class TrialConfig(BaseModel):
    """What a trial compares.  Forecasting logic lives in code, not here."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9_]+$")
    description: str
    forecasters: list[str] = Field(min_length=1)
    ensembles: dict[str, dict[str, str]] = Field(default_factory=dict)
    variants: dict[str, Variant] = Field(default_factory=dict)
    reference: str = CURRENT_BEST  # what "beats the baseline" is counted against
    submit: str | None = None  # forecaster to package; pick it from validation results only

    @model_validator(mode="after")
    def _check_names(self) -> TrialConfig:
        known = set(self.forecasters)
        if self.reference not in known:
            raise ValueError(f"reference {self.reference!r} must be one of the forecasters")
        if self.submit is not None and self.submit not in known:
            raise ValueError(f"submit {self.submit!r} must be one of the forecasters")
        clash = sorted(set(self.variants) & set(self.ensembles))
        if clash:
            raise ValueError(f"names {clash} are defined as both a variant and an ensemble")
        return self


def load_trial_config(path: Path) -> TrialConfig:
    """Read and validate a trial config."""
    return TrialConfig.model_validate(yaml.safe_load(path.read_text()))


def build_forecasters(cfg: TrialConfig) -> dict[str, Forecaster]:
    """Turn the names in a config into callable forecasters."""
    variants = {name: variant.model_dump() for name, variant in cfg.variants.items()}
    return {name: resolve_forecaster(name, cfg.ensembles, variants) for name in cfg.forecasters}


def registered_entry(name: str, cfg: TrialConfig) -> RegisteredForecaster | None:
    """The registry entry behind a config name, or None for baselines and ensembles."""
    registry = load_all()
    if name in cfg.variants:
        return registry.get(cfg.variants[name].forecaster)
    if name in cfg.ensembles or name == CURRENT_BEST or name in BASELINE_DESCRIPTIONS:
        return None
    return registry.get(name)


def describe_forecaster(name: str, cfg: TrialConfig) -> str:
    """One line saying what a forecaster does, for notes and READMEs."""
    if name in cfg.ensembles:
        return "Per metric: " + ", ".join(f"{m}={cfg.ensembles[name][m]}" for m in METRICS)
    if name == CURRENT_BEST:
        return "Per metric: " + ", ".join(f"{m}={CURRENT_BEST_METHODS[m]}" for m in METRICS)
    entry = registered_entry(name, cfg)
    if entry is not None:
        params = cfg.variants[name].params if name in cfg.variants else {}
        settings = ", ".join(f"{k}={v}" for k, v in sorted(params.items())) or "defaults"
        return f"{entry.description} (`{entry.name}`; {settings})"
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
