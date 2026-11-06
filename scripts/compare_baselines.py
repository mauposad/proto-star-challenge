"""Print the reference table that new forecasters are compared against.

Build the master table first with `uv run python scripts/build_master_dataset.py`.
"""

import pandas as pd

from proto_star.backtest import (
    baseline_forecaster,
    compare_forecasters,
    ensemble_forecaster,
    summarize_backtest,
)
from proto_star.data.master import load_master


def main() -> None:
    """Score the built-in baselines and the current best on the shared folds."""
    results = compare_forecasters(
        {
            "current_best": ensemble_forecaster(),
            "ten_year_mean": baseline_forecaster("ten_year_mean"),
            "thirty_year_mean": baseline_forecaster("thirty_year_mean"),
            "linear_trend": baseline_forecaster("linear_trend"),
        },
        load_master(),
    )
    pd.set_option("display.width", 200, "display.max_columns", None)
    print(summarize_backtest(results, baseline="current_best").to_string(index=False))
    print("\nPer-origin raw score, all forecast years")
    per_origin = results.loc[results["window"] == "all"]
    table = per_origin.pivot_table(index="method", columns="cutoff_year", values="raw_score")
    print(table.round(2))


if __name__ == "__main__":
    main()
