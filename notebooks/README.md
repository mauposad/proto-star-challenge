# Notebooks

Exploration and visualization only. Anything reused moves into `src/proto_star/`.

- Naming: `NN_initials_topic.ipynb` (e.g. `01_mp_eda.ipynb`)
- Launch: `uv run jupyter lab`
- Outputs are stripped on commit (nbstripout pre-commit hook)
- Load data through the package so everyone sees the same data: `load_master()` for annual work,
  `proto_star.data.protostar.load_daily()` for daily work

## Trying a forecasting idea

Everyone scores ideas the same way, so results can be compared. Write your idea as a function
that takes the training rows and returns forecasts:

```python
import pandas as pd

from proto_star.backtest import (
    baseline_forecaster,
    build_submission,
    compare_forecasters,
    ensemble_forecaster,
    summarize_backtest,
)
from proto_star.climate import annual_to_long
from proto_star.data.master import load_master

master = load_master()


def my_forecaster(train, cutoff_year, forecast_years):
    """Example: each city's mean over the last 15 years."""
    history = annual_to_long(train, cutoff_year=cutoff_year)
    recent = history[history["year"] > cutoff_year - 15]
    level = recent.groupby(["city_id", "metric"], as_index=False)["actual_value"].mean()
    level = level.rename(columns={"actual_value": "predicted_value"})
    forecast = level.merge(pd.DataFrame({"year": forecast_years}), how="cross")

    # Sparse cities can have no recent years, but every scored row needs a forecast.
    backup = baseline_forecaster("thirty_year_mean")(train, cutoff_year, forecast_years)
    keys = ["city_id", "year", "metric"]
    extra = backup.merge(forecast[keys], on=keys, how="left", indicator=True)
    extra = extra.loc[extra["_merge"] == "left_only"].drop(columns="_merge")
    return pd.concat([forecast, extra], ignore_index=True)


results = compare_forecasters(
    {"current_best": ensemble_forecaster(), "my_idea": my_forecaster}, master
)
summarize_backtest(results, baseline="current_best")
```

**Rules for a forecaster**

- Compute everything from `train`, inside the function. It only holds years up to that fold's
  cutoff, so gap-filling, station adjustments, and per-city averages are safe there. Do **not**
  load data inside the function or use anything calculated from the full `master`, because that
  leaks later years and the scorer cannot detect it.
- Return `city_id, year, metric, predicted_value`. Every scored row needs a value, including hard
  cities. The scorer rejects forecasts that skip rows.
- Filter on the `valid_*` columns if you use `train` directly. `annual_to_long` does this for you.

**Reading the results**

- `years_4_7` matches the Final Score (2022–2025), so give it the most weight. `years_1_3`
  matches the Live Score.
- `raw_score` is the official score without its floor at zero, so losing methods stay comparable.
- Read the per-metric skill columns too. A method can help one metric and hurt another, and the
  final model can use different methods per metric.
- `origins_beating_baseline` counts wins out of 4 test periods. A higher mean from one lucky
  period is not a real win, and with 4 overlapping periods small gaps should count as ties.
- Trying many ideas and keeping the best one inflates its score, so log every attempt in
  `docs/experiments.md`, including failures.

**Numbers to beat** (mean `raw_score` over 4 origins; run `scripts/compare_baselines.py` to reproduce):

| Method | All years | Years 1–3 | Years 4–7 |
|---|---|---|---|
| `current_best` (metric ensemble) | 3.40 | 0.77 | 4.92 |
| `ten_year_mean` | 2.48 | -0.35 | 4.15 |
| `thirty_year_mean` | 0.00 | 0.00 | 0.00 |
| `linear_trend` | -3.84 | -5.75 | -3.35 |

**When an idea wins:** move the function into `src/proto_star/` with a test, so the team can review
it, then create the forecast with `build_submission(my_forecaster, master)`. It runs on all data
through 2018 and checks all 5,880 rows. Only a person submits to the challenge.
