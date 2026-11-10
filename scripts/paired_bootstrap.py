"""Paired year-block bootstrap of each trial forecaster against the trial's reference.

Prints, for each forecaster: the difference in mean raw score (forecaster minus reference),
with a 95% interval, for each lead window and for each metric's share of the all-years score.
Fold-count rules ("better on 2 of 3 folds") cannot separate small effects from noise; this
paired interval over forecast years can.  Nothing is written.

Usage:
    uv run python scripts/paired_bootstrap.py configs/<trial>.yaml [--origins NAME]

NAME is one of official (default), seven, early, replication.

``early`` (1955, 1962, 1969) is a diagnostic confirmation set that no logged run has scored;
the official folds stay 1980, 1995, 2011 (ADR 0004).
"""

import argparse
from pathlib import Path

import pandas as pd

from proto_star.backtest import WINDOWS, fold_rows, paired_year_bootstrap
from proto_star.climate import DEFAULT_CUTOFFS, METRICS
from proto_star.trial import build_forecasters, load_trial_config, markdown_table, trial_master

ORIGINS = {
    "official": list(DEFAULT_CUTOFFS),
    "seven": sorted({*DEFAULT_CUTOFFS, 1985, 1990, 2000, 2005}),
    "early": [1955, 1962, 1969],
    # Targets 1935-1955: never used as forecast targets by the error analysis (methodologist
    # R2-X1). Less contaminated, not clean: some of these years entered its 1955/1962 inputs.
    "replication": [1934, 1941, 1948],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("--origins", choices=sorted(ORIGINS), default="official")
    args = parser.parse_args()
    cfg = load_trial_config(args.config)
    master = trial_master(cfg)
    cutoffs = ORIGINS[args.origins]
    forecasters = build_forecasters(cfg)
    rows = {
        name: fold_rows(fn, master, name=name, cutoffs=cutoffs) for name, fn in forecasters.items()
    }
    reference = rows[cfg.reference]

    def cell(result: dict[str, float]) -> str:
        return f"{result['difference']:+.2f} [{result['low']:+.2f}, {result['high']:+.2f}]"

    raw, by_metric = [], []
    for name, frame in rows.items():
        if name == cfg.reference:
            continue
        raw.append(
            {
                "forecaster": name,
                **{w: cell(paired_year_bootstrap(reference, frame, window=w)) for w in WINDOWS},
            }
        )
        for metric in METRICS:
            by_metric.append(
                {
                    "forecaster": name,
                    "metric": metric,
                    **{
                        w: cell(paired_year_bootstrap(reference, frame, window=w, metrics=[metric]))
                        for w in WINDOWS
                    },
                }
            )
    print(
        f"Origins {cutoffs}; reference {cfg.reference}. Differences are forecaster minus "
        "reference, with a 95% year-block bootstrap interval.\n\nRaw score:\n"
    )
    print(markdown_table(pd.DataFrame(raw)))
    print("\nPer-metric skill, percentage points (rows that differ from the reference only):\n")
    table = pd.DataFrame(by_metric)
    unchanged = table[list(WINDOWS)].eq("+0.00 [+0.00, +0.00]").all(axis=1)
    print(markdown_table(table.loc[~unchanged]))


if __name__ == "__main__":
    main()
