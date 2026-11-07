"""Assemble a Hugging Face submission dataset from a trial config, and check it reproduces.

``build_package`` writes one folder in the layout the challenge asks for::

    submissions/<stamp>_<name>/
      submission.csv     5,880 validated forecasts
      README.md          method, backtest evidence, policy idea, feedback, how to reproduce
      code/              the pipeline, the trial config, requirements.txt, reproduce.py
      data/              the curated inputs and their data card (README.md)

Everything in it is generated from the trial config, so the folder can be rebuilt at any time.
Only a person uploads it to the Hub and submits the link.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from importlib import metadata
from pathlib import Path

import pandas as pd
import yaml

from proto_star.backtest import build_submission, compare_forecasters, summarize_backtest
from proto_star.climate import DEFAULT_CUTOFFS, METRICS, ClimateSubmissionError
from proto_star.data.master import MANIFEST_FILE, MASTER_FILE, load_master
from proto_star.data.protostar import PROTOSTAR_DIR
from proto_star.paths import PROJECT_ROOT, SUBMISSIONS_DIR
from proto_star.tracking import git_info
from proto_star.trial import (
    TrialConfig,
    build_forecasters,
    describe_forecaster,
    load_trial_config,
    markdown_table,
    registered_entry,
)

RAW_INPUTS = ("annual_indices.parquet", "city_info.parquet")
# Scripts shipped in code/scripts: the data pipeline, plus the ones that produced the evidence.
PIPELINE_SCRIPTS = ("download_protostar_data.py", "build_master_dataset.py")
EVIDENCE_SCRIPTS = ("compare_baselines.py", "evaluate_metric_ensemble.py")
DOWNLOAD = "`python code/scripts/download_protostar_data.py`"
TEAM_FILE = PROJECT_ROOT / "docs" / "submission" / "team.yaml"
SUBMISSION_DOCS = ("policy-idea.md", "ecosystem-feedback.md")
PLACEHOLDER = re.compile(r"<[^<>\n]*(?:team|username|institution|Name)[^<>\n]*>")
REPRODUCE_SCRIPT = '''"""Rebuild submission.csv from ../data and compare it with the shipped file.

    pip install -r code/requirements.txt
    python code/reproduce.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "src"))

from proto_star.submission_package import verify_package  # noqa: E402

if __name__ == "__main__":
    verify_package(ROOT)
'''


CODE_README = """# Code

Everything here rebuilds `../submission.csv` from `../data`.

| Path | Purpose |
|---|---|
| `reproduce.py` | Rebuilds the forecasts from `../data` and compares them with `submission.csv` |
| `check_submission.py` | Official format check (same as the challenge Space) |
| `trial.yaml` | Trial config: candidate forecasters, reference, and the one submitted |
| `src/proto_star/` | The pipeline: loading, backtest, forecasters, packaging |
| `scripts/download_protostar_data.py` | Downloads the public CMU training tables |
| `scripts/build_master_dataset.py` | Builds the cleaned annual master table |
| `scripts/compare_baselines.py` | Prints the backtest table behind the method choice |
| `scripts/evaluate_metric_ensemble.py` | Prints the per-metric ensemble backtest |
| `requirements.txt` | Pinned versions the package was built with |
| `AGENTS.md` | Rules the AI agents followed (2018-12-31 data cut-off) |

```bash
pip install -r code/requirements.txt
python code/reproduce.py
python code/check_submission.py submission.csv
```
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_code(code_dir: Path, config_path: Path, extra: tuple[str, ...] = ()) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(
        PROJECT_ROOT / "src" / "proto_star", code_dir / "src" / "proto_star", ignore=ignore
    )
    scripts = code_dir / "scripts"
    scripts.mkdir()
    for name in PIPELINE_SCRIPTS + EVIDENCE_SCRIPTS:
        shutil.copyfile(PROJECT_ROOT / "scripts" / name, scripts / name)
    shutil.copyfile(PROJECT_ROOT / "AGENTS.md", code_dir / "AGENTS.md")
    check = "check_submission.py"
    shutil.copyfile(PROJECT_ROOT / "scripts" / check, code_dir / check)
    shutil.copyfile(config_path, code_dir / "trial.yaml")
    (code_dir / "reproduce.py").write_text(REPRODUCE_SCRIPT)
    (code_dir / "README.md").write_text(CODE_README)
    (code_dir / "requirements.txt").write_text("\n".join(_runtime_pins(extra)) + "\n")


# Wheel indexes a reader needs for some optional packages (local versions like 2.5.1+cpu).
EXTRA_INDEXES = {"torch": "https://download.pytorch.org/whl/cpu"}


def _runtime_pins(extra: tuple[str, ...] = ()) -> list[str]:
    """Pin proto-star's core dependencies plus ``extra`` (what the submitted forecaster
    declares in the registry) to the installed versions."""
    names = [
        re.split(r"[<>=!~;\s\[(]", req, maxsplit=1)[0]
        for req in metadata.requires("proto-star") or []
        if "extra ==" not in req
    ]
    pins = sorted(f"{name}=={metadata.version(name)}" for name in {*names, *extra})
    indexes = sorted({EXTRA_INDEXES[name] for name in extra if name in EXTRA_INDEXES})
    return [f"--extra-index-url {url}" for url in indexes] + pins


def _copy_data(data_dir: Path, master_dir: Path, raw_dir: Path) -> list[Path]:
    data_dir.mkdir()
    sources = [master_dir / MASTER_FILE, master_dir / MANIFEST_FILE]
    sources += [raw_dir / name for name in RAW_INPUTS]
    for source in sources:
        shutil.copyfile(source, data_dir / source.name)
    return [data_dir / source.name for source in sources]


def _data_card(files: list[Path], manifest: dict[str, object]) -> str:
    descriptions = {
        MASTER_FILE: (
            "Cleaned annual table: one row per city-year, all columns of `annual_indices` plus "
            "`valid_*` flags and station fields. Nothing imputed.",
            "`scripts/build_master_dataset.py` from the three CMU tables below",
        ),
        MANIFEST_FILE: (
            "Build manifest: row counts, content hash, source checksums",
            "same script",
        ),
        "annual_indices.parquet": ("CMU annual indices, as downloaded", "unchanged copy"),
        "city_info.parquet": (
            "CMU city list: station ID, name, latitude, longitude",
            "unchanged copy",
        ),
    }
    rows = pd.DataFrame(
        {
            "file": [f"`{f.name}`" for f in files],
            "what it holds": [descriptions[f.name][0] for f in files],
            "how prepared": [descriptions[f.name][1] for f in files],
            "sha256": [f"`{_sha256(f)[:16]}...`" for f in files],
        }
    )
    sources = manifest.get("sources_sha256", {})
    return f"""# Data card

Weather inputs end on 2018-12-31. No later observation is read, and the code stops with an
error if it finds one (`assert_weather_cutoff`).

## Files in this folder

Source for all of them: `CMU-OSPO/protostar-climate-train-to-2018` on Hugging Face (original
records: Lai & Dzombak 2019, DOI 10.1184/R1/7890488.v6). License: CC0-1.0.

{markdown_table(rows)}

## Not copied (download instead)

| Source | Why not copied | How to download |
|---|---|---|
| `daily`, `coverage_and_stations` (parquet) | ~50 MB; only to rebuild the master | {DOWNLOAD} |

SHA-256 of the sources the master table was built from: `{json.dumps(sources)}`.

## Rebuilding the master table

Run {DOWNLOAD}, then
`python code/scripts/build_master_dataset.py`.
Its printed `content_hash` must equal `{manifest.get("content_hash")}`.

## Known limitations

Stations are mostly airports and some change location (about 0.5 °F shift in temperature on
a switch); incomplete years can bias annual values, so each metric is only used when its
missing-day columns are at most 10.
"""


def _team_sections(team: dict[str, object]) -> tuple[str, str]:
    """Render the team table and the AI-tools section from ``team.yaml``."""
    members = pd.DataFrame(
        [
            {
                "Name": m["name"],
                "Hugging Face username": m["hf_username"],
                "University, Program": m["affiliation"],
            }
            for m in team["members"]  # type: ignore[attr-defined] # yaml gives untyped lists
        ]
    )
    ai = f"""- Tools and models: {team["ai_tools"]}
- What they did: {team["ai_work"]}
- What a person reviewed: {team["human_review"]}"""
    return markdown_table(members), ai


def _readme(
    cfg: TrialConfig,
    forecaster: str,
    master: pd.DataFrame,
    config_name: str,
    meta: dict[str, object],
    team: dict[str, object],
) -> str:
    results = compare_forecasters(
        {n: f for n, f in build_forecasters(cfg).items() if n in {forecaster, cfg.reference}},
        master,
    )
    summary = summarize_backtest(results, baseline=cfg.reference)
    team_table, ai_section = _team_sections(team)
    dirty = " (with uncommitted changes)" if meta["dirty"] else ""
    docs = {
        name: (PROJECT_ROOT / "docs" / "submission" / name).read_text().strip()
        for name in SUBMISSION_DOCS
    }
    return f"""---
pretty_name: "ProtoStar Climate Risk Intelligence - {team["team_name"]}"
license: cc-by-4.0
task_categories:
  - time-series-forecasting
tags:
  - climate
  - forecasting
  - protostar-climate-2026
configs:
  - config_name: default
    data_files:
      - split: test
        path: submission.csv
---

# {team["team_name"]}: ProtoStar Climate Challenge Submission

Forecasts of annual average temperature, total precipitation, hottest-day temperature and
cooling degree days for 210 U.S. cities, 2019-2025, built only from observations through
2018-12-31.

## Team

{team_table}

## Method

Forecaster `{forecaster}`: {describe_forecaster(forecaster, cfg)}.

Chosen from the candidates in `{config_name}` using only backtests on the team's fixed
folds: seven-year forecasts from cut-offs {list(DEFAULT_CUTOFFS)}, scored with the official
skill score against the 30-year average. Test and leaderboard data were not used for selection.
Mean `raw_score` (the official score without its floor at zero) and per-metric skill in percent:

{markdown_table(summary.drop(columns="origins"))}

`origins_beating_baseline` counts the folds (out of {len(DEFAULT_CUTOFFS)}) where the method beats
`{cfg.reference}`. `years_4_7` matches the Final Score window.

## AI tools and agents

{ai_section}

Agent rules for this project are in `code/AGENTS.md`: they enforce the
2018-12-31 cut-off and forbid agents from submitting or supplying forecast values.

## Policy idea

{docs["policy-idea.md"]}

## Feedback to the ecosystem

{docs["ecosystem-feedback.md"]}

## Files

| File | Content |
|---|---|
| `submission.csv` | 5,880 forecasts: 210 cities x 7 years x 4 metrics |
| `code/` | Pipeline, trial config `trial.yaml`, `requirements.txt`, `reproduce.py` |
| `data/` | Curated inputs; each file is described in `data/README.md` |

## How to reproduce

```bash
pip install -r code/requirements.txt
python code/reproduce.py        # rebuilds the forecasts from data/ and compares with submission.csv
```

Built from commit `{meta["commit"]}`{dirty} on {meta["date"]}.
In the repository the same folder is produced by
`uv run proto-star climate-package {config_name}`.
"""


def build_package(
    config_path: Path,
    *,
    forecaster: str | None = None,
    master: pd.DataFrame | None = None,
    master_dir: Path | None = None,
    raw_dir: Path = PROTOSTAR_DIR,
    out_root: Path = SUBMISSIONS_DIR,
    team_path: Path = TEAM_FILE,
) -> Path:
    """Write the submission folder for one forecaster and return its path."""
    cfg = load_trial_config(config_path)
    name = forecaster or cfg.submit
    if name is None:
        raise ValueError("pass a forecaster or set `submit` in the trial config")
    if name not in cfg.forecasters:
        raise ValueError(f"{name!r} is not in the trial config's forecasters")

    from proto_star.data.master import MASTER_DIR

    master_dir = master_dir or MASTER_DIR
    data = load_master(master_dir) if master is None else master
    submission = build_submission(build_forecasters(cfg)[name], data)

    now = datetime.now()
    out_dir = out_root / f"{now.strftime('%Y%m%d-%H%M%S')}_{cfg.name}"
    out_dir.mkdir(parents=True, exist_ok=False)
    submission.to_csv(out_dir / "submission.csv", index=False)
    entry = registered_entry(name, cfg)
    _copy_code(out_dir / "code", config_path, entry.requires if entry else ())
    files = _copy_data(out_dir / "data", master_dir, raw_dir)
    manifest = json.loads((master_dir / MANIFEST_FILE).read_text())
    (out_dir / "data" / "README.md").write_text(_data_card(files, manifest))
    meta = {**git_info(), "date": now.strftime("%Y-%m-%d")}
    (out_dir / "README.md").write_text(
        _readme(cfg, name, data, config_path.name, meta, yaml.safe_load(team_path.read_text()))
    )
    return out_dir


def open_placeholders(package_dir: Path) -> list[str]:
    """Placeholders a person must still fill in before uploading."""
    found: list[str] = []
    for path in (package_dir / "README.md", package_dir / "data" / "README.md"):
        relative = path.relative_to(package_dir)
        found += [f"{relative}: {match}" for match in PLACEHOLDER.findall(path.read_text())]
    return found


def verify_package(root: Path, *, tolerance: float = 1e-9) -> None:
    """Rebuild the forecasts from ``root/data`` and fail unless they match ``submission.csv``."""
    cfg = load_trial_config(root / "code" / "trial.yaml")
    if cfg.submit is None:
        raise ValueError("code/trial.yaml has no `submit` forecaster")
    master = load_master(root / "data")
    rebuilt = build_submission(build_forecasters(cfg)[cfg.submit], master)
    shipped = pd.read_csv(root / "submission.csv")
    key = ["city_id", "year", "metric"]
    if len(shipped) != len(rebuilt):
        raise ClimateSubmissionError(
            f"shipped file has {len(shipped)} rows, rebuild {len(rebuilt)}"
        )
    merged = shipped.merge(rebuilt, on=key, suffixes=("_shipped", "_rebuilt"), validate="1:1")
    worst = float(
        (merged["predicted_value_shipped"] - merged["predicted_value_rebuilt"]).abs().max()
    )
    if len(merged) != len(rebuilt) or worst > tolerance:
        raise ClimateSubmissionError(
            f"rebuild differs from submission.csv (max difference {worst})"
        )
    print(f"OK: {len(rebuilt)} rows over {len(METRICS)} metrics reproduce submission.csv")
