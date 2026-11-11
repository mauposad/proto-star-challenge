"""National-mean forecast path of each forecaster in a trial config, at the 2018 cut-off.

Usage:
    uv run python scripts/national_path.py configs/at_city_drift.yaml

For each forecaster and metric, prints the mean over cities of (forecast minus the city's
1989-2018 average), for 2019-2021 and for 2022-2025. It reads no observation after 2018: it
compares forecasts with the official 30-year-average baseline, so it shows how much national
change a forecaster assumes, not how accurate it is.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from proto_star.backtest import build_submission
from proto_star.climate import FORECAST_CUTOFF, FORECAST_YEARS, annual_to_long, baseline_forecast
from proto_star.data.master import load_master
from proto_star.trial import build_forecasters, load_trial_config

KEY = ["city_id", "year", "metric"]


def national_path(submission: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Mean departure from the reference by metric and forecast block."""
    joined = submission.assign(city_id=submission["city_id"].astype(str)).merge(
        reference.rename(columns={"predicted_value": "reference"})[[*KEY, "reference"]], on=KEY
    )
    joined["departure"] = joined["predicted_value"] - joined["reference"]
    joined["block"] = (joined["year"] >= 2022).map({False: "2019-2021", True: "2022-2025"})
    table = joined.pivot_table(index="metric", columns="block", values="departure", aggfunc="mean")
    return table.round(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    master = load_master()
    reference = baseline_forecast(
        annual_to_long(master),
        cutoff_year=FORECAST_CUTOFF,
        forecast_years=list(FORECAST_YEARS),
        method="thirty_year_mean",
    )
    for name, forecaster in build_forecasters(load_trial_config(args.config)).items():
        print(f"\n{name}\n{national_path(build_submission(forecaster, master), reference)}")


if __name__ == "__main__":
    main()
