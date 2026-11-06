"""Evaluate the backtest-selected metric ensemble across all historical folds."""

from pathlib import Path

import pandas as pd

from proto_star.climate import (
    DEFAULT_CUTOFFS,
    annual_to_long,
    backtest_baselines,
    backtest_metric_ensemble,
    select_metric_methods,
)
from proto_star.paths import RAW_DIR


def main(annual_path: Path = RAW_DIR / "protostar" / "annual_indices.parquet") -> None:
    """Print selected methods and historical scores for the reproducible ensemble."""
    history = annual_to_long(pd.read_parquet(annual_path))
    baselines = backtest_baselines(history, cutoffs=DEFAULT_CUTOFFS)
    methods = select_metric_methods(baselines)
    ensemble = backtest_metric_ensemble(history, cutoffs=DEFAULT_CUTOFFS, methods_by_metric=methods)
    print(f"methods={methods}")
    print(ensemble.to_csv(index=False))


if __name__ == "__main__":
    main()
