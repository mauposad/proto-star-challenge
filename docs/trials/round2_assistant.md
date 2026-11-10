# Trial: round2_assistant

E1 damped city anomaly for the hottest day and precipitation; E2 shrinking only the city-specific part of the temperature and CDD anomaly; E3 an in-fold multiplier on the pooled trend; E4 a pooled relative precipitation trend. All are fitted on in-fold pseudo-origins where needed and applied on top of trend_level10_15_sensitivity.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_round2_assistant.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_round2_assistant.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| e1_damped_hot_precip | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['hottest_day_temp', 'total_precip_in'], window=15) |
| e1_damped_hot_precip_national | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['hottest_day_temp', 'total_precip_in'], window=15, national=True) |
| e2_temp_city_shrink | Base forecast plus in-fold multiples of the recent anomaly (base=trend_level10_15_sensitivity, metrics=['annual_avg_temp', 'cdd'], window=15) |
| e3_trend_scale | Pooled-trend forecast with an in-fold trend multiplier kappa |
| e4_precip_relative_trend | Metric = 30-year mean x (1 + pooled relative slope x years) (base=trend_level10_15_sensitivity, trend_window=60) |
| e1_e2_combined | Base forecast plus in-fold multiples of the recent anomaly (base=e2_temp_city_shrink, metrics=['hottest_day_temp', 'total_precip_in'], window=15) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_damped_hot_precip | 4.11 | 8.74 | -0.21 | 0.1 | 7.8 | 1 | 3 |
| e1_damped_hot_precip_national | 3.62 | 8.74 | -2.12 | 0.08 | 7.8 | 0 | 3 |
| e1_e2_combined | 4.32 | 9.12 | -0.21 | 0.1 | 8.29 | 2 | 3 |
| e2_temp_city_shrink | 4.35 | 9.12 | 0.0 | 0.0 | 8.29 | 2 | 3 |
| e3_trend_scale | 3.94 | 7.69 | 0.0 | 0.0 | 8.07 | 0 | 3 |
| e4_precip_relative_trend | 4.18 | 8.74 | 0.17 | 0.0 | 7.8 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_damped_hot_precip | 0.44 | -2.56 | -0.38 | 0.83 | 3.87 | 3 | 3 |
| e1_damped_hot_precip_national | -0.04 | -2.56 | -1.98 | 0.52 | 3.87 | 1 | 3 |
| e1_e2_combined | 0.45 | -2.33 | -0.38 | 0.83 | 3.67 | 2 | 3 |
| e2_temp_city_shrink | 0.34 | -2.33 | 0.0 | 0.0 | 3.67 | 2 | 3 |
| e3_trend_scale | 0.22 | -2.62 | 0.0 | 0.0 | 3.48 | 1 | 3 |
| e4_precip_relative_trend | 0.49 | -2.56 | 0.64 | 0.0 | 3.87 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| e1_damped_hot_precip | 6.79 | 17.73 | -0.08 | -0.44 | 9.94 | 1 | 3 |
| e1_damped_hot_precip_national | 6.32 | 17.73 | -2.1 | -0.27 | 9.94 | 0 | 3 |
| e1_e2_combined | 7.16 | 18.19 | -0.08 | -0.44 | 10.97 | 2 | 3 |
| e2_temp_city_shrink | 7.29 | 18.19 | 0.0 | 0.0 | 10.97 | 3 | 3 |
| e3_trend_scale | 6.65 | 16.0 | 0.0 | 0.0 | 10.58 | 0 | 3 |
| e4_precip_relative_trend | 6.83 | 17.73 | -0.36 | 0.0 | 9.94 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| e1_damped_hot_precip | -1.34 | 3.63 | 10.04 |
| e1_damped_hot_precip_national | -2.39 | 3.41 | 9.85 |
| e1_e2_combined | -0.75 | 3.62 | 10.11 |
| e2_temp_city_shrink | -0.68 | 3.75 | 9.99 |
| e3_trend_scale | -1.26 | 3.36 | 9.72 |
| e4_precip_relative_trend | -0.97 | 2.98 | 10.53 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
