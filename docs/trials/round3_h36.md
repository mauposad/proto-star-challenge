# Trial: round3_h36

E2's CDD shrinkage plus a coefficient on the city part of the (Tmin - Tmax)/2 temperature anomaly scaled by each city's CDD per degree (H36), against E2's CDD shrinkage alone.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round3_h36.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `e2_cdd_only` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round3_h36.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| e2_cdd_only | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['cdd'], window=15) |
| h36_cdd_contrast | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['cdd'], window=15, split=diurnal_contrast) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `e2_cdd_only`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_cdd_only | 4.26 | 8.74 | 0.0 | 0.0 | 8.29 | 0 | 3 |
| h36_cdd_contrast | 4.31 | 8.74 | 0.0 | 0.0 | 8.51 | 3 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_cdd_only | 0.28 | -2.56 | 0.0 | 0.0 | 3.67 | 0 | 3 |
| h36_cdd_contrast | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 3 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_cdd_only | 7.17 | 17.73 | 0.0 | 0.0 | 10.97 | 0 | 3 |
| h36_cdd_contrast | 7.24 | 17.73 | 0.0 | 0.0 | 11.21 | 3 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| e2_cdd_only | -0.93 | 3.79 | 9.92 |
| h36_cdd_contrast | -0.87 | 3.83 | 9.98 |
