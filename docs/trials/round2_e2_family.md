# Trial: round2_e2_family

Shrinking the city-specific part of the candidate's recent temperature and CDD anomaly, with coefficients fitted on in-fold pseudo-origins: one coefficient (E2), separate regional and local coefficients (H21), and separate Tmax and Tmin coefficients for temperature (H23/H32).


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round2_e2_family.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round2_e2_family.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| e2_temp_city_shrink | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], window=15) |
| h21_region_split | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp'], window=15, split=region) |
| h23_diurnal_split | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp'], window=15, split=diurnal) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 4.35 | 9.12 | 0.0 | 0.0 | 8.29 | 2 | 3 |
| h21_region_split | 4.21 | 9.02 | 0.0 | 0.0 | 7.8 | 2 | 3 |
| h23_diurnal_split | 4.26 | 9.22 | 0.0 | 0.0 | 7.8 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 0.34 | -2.33 | 0.0 | 0.0 | 3.67 | 2 | 3 |
| h21_region_split | 0.3 | -2.67 | 0.0 | 0.0 | 3.87 | 1 | 3 |
| h23_diurnal_split | 0.38 | -2.36 | 0.0 | 0.0 | 3.87 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e2_temp_city_shrink | 7.29 | 18.19 | 0.0 | 0.0 | 10.97 | 3 | 3 |
| h21_region_split | 7.05 | 18.28 | 0.0 | 0.0 | 9.94 | 2 | 3 |
| h23_diurnal_split | 7.08 | 18.39 | 0.0 | 0.0 | 9.94 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| e2_temp_city_shrink | -0.68 | 3.75 | 9.99 |
| h21_region_split | -1.08 | 3.73 | 9.97 |
| h23_diurnal_split | -0.99 | 3.73 | 10.02 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
