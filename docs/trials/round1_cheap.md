# Trial: round1_cheap

H3 (closed-form gamma shift of the precipitation 30-year mean, q = 1/3), H13 (the same shift with q fitted in-fold), H5 (CDD from its 30-year mean plus CDD per degree times the temperature forecast's departure) and H16 (lead 1-3 persistence of last year's error), each on top of trend_level10_15_sensitivity.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round1_cheap.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round1_cheap.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| h3_precip_gamma_shift | Base forecast times 1 - q * CV^2, q fitted in-fold by MAE (base=trend_level10_15_sensitivity, metrics=['total_precip_in'], q=0.3333333) |
| h13_precip_fitted_shift | Base forecast times 1 - q * CV^2, q fitted in-fold by MAE (base=trend_level10_15_sensitivity, metrics=['total_precip_in']) |
| h5_cdd_from_temp | CDD 30-year mean plus CDD per degree x temperature departure (base=trend_level10_15_sensitivity) |
| h16_persistence | Base forecast plus an in-fold fraction of last year's error (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], max_lead=3) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 1 | 3 |
| h13_precip_fitted_shift | 3.8 | 8.74 | -1.34 | 0.0 | 7.8 | 0 | 3 |
| h16_persistence | 4.47 | 9.64 | 0.0 | 0.0 | 8.23 | 2 | 3 |
| h3_precip_gamma_shift | 3.96 | 8.74 | -0.73 | 0.0 | 7.8 | 1 | 3 |
| h5_cdd_from_temp | 4.08 | 8.74 | 0.0 | 0.0 | 7.59 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 3 | 3 |
| h13_precip_fitted_shift | 0.47 | -2.56 | 0.56 | 0.0 | 3.87 | 2 | 3 |
| h16_persistence | 1.1 | -0.39 | 0.0 | 0.0 | 4.79 | 2 | 3 |
| h3_precip_gamma_shift | 0.09 | -2.56 | -0.96 | 0.0 | 3.87 | 1 | 3 |
| h5_cdd_from_temp | 0.15 | -2.56 | 0.0 | 0.0 | 3.14 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 1 | 3 |
| h13_precip_fitted_shift | 6.26 | 17.73 | -2.62 | 0.0 | 9.94 | 0 | 3 |
| h16_persistence | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |
| h3_precip_gamma_shift | 6.8 | 17.73 | -0.46 | 0.0 | 9.94 | 1 | 3 |
| h5_cdd_from_temp | 7.0 | 17.73 | 0.0 | 0.0 | 10.27 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| h13_precip_fitted_shift | -1.26 | 3.19 | 9.48 |
| h16_persistence | -0.42 | 3.74 | 10.08 |
| h3_precip_gamma_shift | -1.8 | 4.01 | 9.66 |
| h5_cdd_from_temp | -0.67 | 3.75 | 9.18 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
