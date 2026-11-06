# Trial: baselines_round1

Compare every built-in baseline, including the new 15-year mean, hinge fit and median windows, with the current metric ensemble and a per-metric ensemble chosen from this trial's own validation results.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-06 |
| Config | `configs/mp_baselines_round1.yaml` |
| Code version | `d6247e4` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `current_best` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_baselines_round1.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| fifteen_year_mean | Mean of the last 15 valid years |
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| ten_year_median | Median of the last 10 valid years |
| fifteen_year_median | Median of the last 15 valid years |
| thirty_year_median | Median of valid years in the 30 calendar years before the cutoff |
| linear_trend | Least-squares line through the 30-calendar-year window, extrapolated |
| hinge_fit | Flat level then linear ramp over the 30-year window; hinge year fit per series |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| fifteen_year_mean | 0.88 | 3.32 | -2.11 | -0.8 | 3.12 | 0 | 3 |
| fifteen_year_median | -0.53 | 2.09 | -2.89 | -1.45 | 0.13 | 0 | 3 |
| hinge_fit | -19.83 | -8.59 | -29.09 | -31.38 | -10.26 | 0 | 3 |
| linear_trend | -12.76 | -5.14 | -26.62 | -12.19 | -7.08 | 0 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |
| ten_year_median | -0.23 | 4.94 | -5.72 | -4.07 | 3.92 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| thirty_year_median | -0.69 | -0.75 | -0.64 | 0.03 | -1.42 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| fifteen_year_mean | 0.1 | -1.48 | -1.08 | 0.11 | 2.87 | 1 | 3 |
| fifteen_year_median | -1.06 | -2.21 | -2.18 | -0.54 | 0.69 | 1 | 3 |
| hinge_fit | -13.96 | -11.23 | -19.64 | -16.62 | -8.33 | 0 | 3 |
| linear_trend | -10.12 | -8.97 | -19.18 | -6.53 | -5.78 | 0 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |
| ten_year_median | -1.97 | -1.91 | -5.05 | -2.82 | 1.89 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| thirty_year_median | -0.31 | -0.16 | -0.54 | 0.82 | -1.34 | 1 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| fifteen_year_mean | 1.49 | 7.35 | -2.87 | -1.6 | 3.09 | 0 | 3 |
| fifteen_year_median | -0.06 | 5.64 | -3.35 | -2.05 | -0.49 | 0 | 3 |
| hinge_fit | -25.27 | -6.08 | -36.6 | -44.59 | -13.81 | 0 | 3 |
| linear_trend | -15.15 | -1.76 | -32.24 | -17.3 | -9.31 | 0 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |
| ten_year_median | 1.06 | 10.62 | -6.32 | -5.08 | 5.03 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| thirty_year_median | -0.94 | -1.21 | -0.64 | -0.46 | -1.44 | 1 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| fifteen_year_mean | -2.43 | 1.79 | 3.3 |
| fifteen_year_median | -4.87 | 1.2 | 2.07 |
| hinge_fit | -26.26 | -21.34 | -11.89 |
| linear_trend | -15.43 | -24.85 | 2.0 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
| ten_year_median | -5.04 | 0.63 | 3.73 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| thirty_year_median | -0.75 | -0.12 | -1.21 |
