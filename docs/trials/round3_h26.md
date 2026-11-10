# Trial: round3_h26

E2 with a lead-dependent city-part coefficient (H26), against E2 with a single coefficient.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round3_h26.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `e2_temp_city_shrink` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round3_h26.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| e2_temp_city_shrink | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], window=15) |
| h26_lead_slope | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], window=15, lead_slope=True) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `e2_temp_city_shrink`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 4.35 | 9.12 | 0.0 | 0.0 | 8.29 | 0 | 3 |
| h26_lead_slope | 4.38 | 9.11 | 0.0 | 0.0 | 8.41 | 3 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 0.34 | -2.33 | 0.0 | 0.0 | 3.67 | 0 | 3 |
| h26_lead_slope | 0.39 | -2.33 | 0.0 | 0.0 | 3.88 | 2 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 7.29 | 18.19 | 0.0 | 0.0 | 10.97 | 0 | 3 |
| h26_lead_slope | 7.3 | 18.18 | 0.0 | 0.0 | 11.03 | 3 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| e2_temp_city_shrink | -0.68 | 3.75 | 9.99 |
| h26_lead_slope | -0.67 | 3.81 | 10.0 |
