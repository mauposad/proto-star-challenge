# Trial: round3_h37

E1's damped city anomaly for the hottest day with one coefficient (parent), against the same correction with separate coefficients for leads 1-3 and 4-7 (H37).


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round3_h37.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `e1_hottest` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round3_h37.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| e1_hottest | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['hottest_day_temp'], window=15, clip=[0.0, 1.0]) |
| h37_lead_groups | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['hottest_day_temp'], window=15, clip=[0.0, 1.0], lead_split=3) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `e1_hottest`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_hottest | 4.16 | 8.74 | 0.0 | 0.1 | 7.8 | 0 | 3 |
| h37_lead_groups | 4.17 | 8.74 | 0.0 | 0.14 | 7.8 | 1 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_hottest | 0.54 | -2.56 | 0.0 | 0.83 | 3.87 | 0 | 3 |
| h37_lead_groups | 0.55 | -2.56 | 0.0 | 0.88 | 3.87 | 2 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_hottest | 6.81 | 17.73 | 0.0 | -0.44 | 9.94 | 0 | 3 |
| h37_lead_groups | 6.81 | 17.73 | 0.0 | -0.42 | 9.94 | 1 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| e1_hottest | -1.26 | 3.66 | 10.09 |
| h37_lead_groups | -1.27 | 3.7 | 10.08 |
