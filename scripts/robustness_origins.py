"""Score a trial's forecasters on extra cut-offs, as a robustness check.

The official folds stay 1980, 1995, 2011 (ADR 0004). Three folds are few, so this adds four more
to show whether a result depends on one period. Nothing is written; results are printed.

Usage: uv run python scripts/robustness_origins.py configs/<trial>.yaml
"""

import sys
from pathlib import Path

from proto_star.backtest import compare_forecasters
from proto_star.climate import DEFAULT_CUTOFFS
from proto_star.data.master import load_master
from proto_star.trial import build_forecasters, load_trial_config

ORIGINS = sorted({*DEFAULT_CUTOFFS, 1985, 1990, 2000, 2005})


def main() -> None:
    cfg = load_trial_config(Path(sys.argv[1]))
    results = compare_forecasters(build_forecasters(cfg), load_master(), cutoffs=ORIGINS)
    for window in ("all", "years_4_7"):
        table = results.loc[results["window"] == window].pivot_table(
            index="method", columns="cutoff_year", values="raw_score"
        )
        table["mean_official"] = table[list(DEFAULT_CUTOFFS)].mean(axis=1)
        table["mean_all"] = table[ORIGINS].mean(axis=1)
        print(f"\nRaw score, window={window}\n{table.round(2).to_string()}")


if __name__ == "__main__":
    main()
