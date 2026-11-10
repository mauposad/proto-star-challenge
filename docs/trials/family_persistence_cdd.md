# Trial: family_persistence_cdd

H16 (lead 1-3 persistence of last year's error), H5 (CDD from its 30-year mean plus CDD per degree times the temperature forecast's departure) and both combined, each on top of trend_level10_15_sensitivity.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_family_persistence_cdd.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_family_persistence_cdd.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| h16_persistence | Base forecast plus an in-fold fraction of last year's error (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], max_lead=3) |
| h5_cdd_from_temp | CDD 30-year mean plus CDD per degree x temperature departure (base=trend_level10_15_sensitivity) |
| h5_h16_combined | Base forecast plus an in-fold fraction of last year's error (base=h5_cdd_from_temp, metrics=['annual_avg_temp', 'cdd'], max_lead=3) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h16_persistence | 4.47 | 9.64 | 0.0 | 0.0 | 8.23 | 2 | 3 |
| h5_cdd_from_temp | 4.08 | 8.74 | 0.0 | 0.0 | 7.59 | 1 | 3 |
| h5_h16_combined | 4.36 | 9.64 | 0.0 | 0.0 | 7.82 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h16_persistence | 1.1 | -0.39 | 0.0 | 0.0 | 4.79 | 2 | 3 |
| h5_cdd_from_temp | 0.15 | -2.56 | 0.0 | 0.0 | 3.14 | 1 | 3 |
| h5_h16_combined | 0.82 | -0.39 | 0.0 | 0.0 | 3.66 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h16_persistence | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |
| h5_cdd_from_temp | 7.0 | 17.73 | 0.0 | 0.0 | 10.27 | 2 | 3 |
| h5_h16_combined | 7.0 | 17.73 | 0.0 | 0.0 | 10.27 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| h16_persistence | -0.42 | 3.74 | 10.08 |
| h5_cdd_from_temp | -0.67 | 3.75 | 9.18 |
| h5_h16_combined | 0.01 | 3.73 | 9.36 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
