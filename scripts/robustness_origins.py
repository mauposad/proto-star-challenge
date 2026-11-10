"""Score a trial's forecasters on extra cut-offs, as a robustness check.

The official folds stay 1980, 1995, 2011 (ADR 0004). ``--origins seven`` (default) adds four
more cut-offs. ``--origins rolling27`` scores every cut-off from 1985 to 2011 (27 origins,
7-year horizon, only target years up to 2018), the validation PstarAlu and Tatakae published.
``--default NAME`` adds a paired table: per origin, each method's score minus NAME's, per
metric. ``--out DIR`` writes ``origins.csv`` (every origin and window) and, with
``--default``, ``paired.csv`` and ``paired_summary.csv``. Without ``--out`` nothing is written.

Usage:
  uv run python scripts/robustness_origins.py configs/<trial>.yaml
  uv run python scripts/robustness_origins.py configs/<trial>.yaml --origins rolling27 \
      --default lead_split3 --out runs/robustness/<name>
"""

import argparse
from pathlib import Path

import pandas as pd

from proto_star.backtest import compare_forecasters
from proto_star.climate import DEFAULT_CUTOFFS, METRICS
from proto_star.data.master import load_master
from proto_star.robustness import (
    ROLLING_ORIGINS,
    SEVEN_ORIGINS,
    paired_differences,
    summarize_paired,
)
from proto_star.trial import build_forecasters, load_trial_config

ORIGIN_SETS = {"seven": SEVEN_ORIGINS, "rolling27": ROLLING_ORIGINS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("--origins", choices=sorted(ORIGIN_SETS), default="seven")
    parser.add_argument("--default", help="method to pair every other method against")
    parser.add_argument("--out", type=Path, help="directory for CSV outputs")
    args = parser.parse_args()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)

    origins = list(ORIGIN_SETS[args.origins])
    cfg = load_trial_config(args.config)
    results = compare_forecasters(build_forecasters(cfg), load_master(), cutoffs=origins)
    for window in ("all", "years_1_3", "years_4_7"):
        rows = results.loc[results["window"] == window]
        table = rows.pivot_table(index="method", columns="cutoff_year", values="raw_score")
        official = [c for c in DEFAULT_CUTOFFS if c in table.columns]
        summary = table[origins].mean(axis=1).rename("mean_origins").to_frame()
        if official:
            summary["mean_official_in_set"] = table[official].mean(axis=1)
        for metric in METRICS:
            skill = rows.groupby("method")[f"{metric}_skill"].mean() * 100.0
            summary[f"{metric}_skill_pct"] = skill
        print(f"\nMean over {len(origins)} origins, window={window}\n{summary.round(2)}")
        if args.origins == "seven":
            print(f"\nRaw score per origin, window={window}\n{table.round(2).to_string()}")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        results.to_csv(args.out / "origins.csv", index=False)
    if args.default:
        paired = paired_differences(results, args.default)
        summary = summarize_paired(paired)
        shown = summary.loc[summary["window"] == "all"].set_index("method")
        print(f"\nPaired vs {args.default}, window=all (diffs in skill points or score points)")
        print(shown.drop(columns=["default", "window"]).round(4).T.to_string())
        if args.out:
            paired.to_csv(args.out / "paired.csv", index=False)
            summary.to_csv(args.out / "paired_summary.csv", index=False)
    if args.out:
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
