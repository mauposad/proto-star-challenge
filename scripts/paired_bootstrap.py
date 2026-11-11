"""Paired year-block bootstrap of every forecaster in a trial config against one default.

Usage:
    uv run python scripts/paired_bootstrap.py configs/at_ml_challengers.yaml \
        --default r4_winners [--origins official|replication] [--out runs/paired/ml_challengers]

Prints, per window, each method's raw-score difference from the default (method minus
default) with a 95% interval from resampling forecast years within each fold, and the same for
each metric's skill (percentage points). "official" is ADR 0004's folds; "replication" is
1934/1941/1948, never used for selection. Evaluation only: folds, scorer and metric unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from proto_star.climate import DEFAULT_CUTOFFS, METRICS
from proto_star.data.master import load_master
from proto_star.paired import fold_rows, paired_year_bootstrap
from proto_star.trial import build_forecasters, load_trial_config

ORIGINS = {"official": DEFAULT_CUTOFFS, "replication": (1934, 1941, 1948)}
WINDOW_NAMES = ("all", "years_1_3", "years_4_7")


def _cell(result: dict[str, float]) -> str:
    return f"{result['difference']:+.2f} [{result['low']:+.2f}, {result['high']:+.2f}]"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("--default", required=True)
    parser.add_argument("--origins", choices=sorted(ORIGINS), default="official")
    parser.add_argument("--out", type=Path, help="directory for the per-row CSV")
    args = parser.parse_args()

    cfg = load_trial_config(args.config)
    forecasters = build_forecasters(cfg)
    if args.default not in forecasters:
        raise SystemExit(f"--default {args.default!r} is not a forecaster in {args.config}")
    master = load_master()
    cutoffs = ORIGINS[args.origins]
    rows = {
        name: fold_rows(forecaster, master, name=name, cutoffs=cutoffs)
        for name, forecaster in forecasters.items()
    }
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        long = pd.concat([frame.assign(method=name) for name, frame in rows.items()])
        long.to_csv(args.out / f"rows_{args.origins}.csv", index=False)

    others = [name for name in forecasters if name != args.default]
    print(f"Origins {list(cutoffs)}; method minus {args.default}; 95% year-block intervals.\n")
    print("Raw score:\n")
    print("| method | " + " | ".join(WINDOW_NAMES) + " |")
    print("|---|" + "---|" * len(WINDOW_NAMES))
    for name in others:
        cells = [
            _cell(paired_year_bootstrap(rows[args.default], rows[name], window=window))
            for window in WINDOW_NAMES
        ]
        print(f"| {name} | " + " | ".join(cells) + " |")
    print("\nPer-metric skill, percentage points (window all):\n")
    print("| method | " + " | ".join(METRICS) + " |")
    print("|---|" + "---|" * len(METRICS))
    for name in others:
        cells = []
        for metric in METRICS:
            result = paired_year_bootstrap(rows[args.default], rows[name], metrics=[metric])
            cells.append(_cell(result))  # one metric: already that metric's skill in pp
        print(f"| {name} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
