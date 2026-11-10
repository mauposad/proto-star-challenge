# Trial: family_hottest_summer

Hottest day from the 30-year mean plus a June-August-based shift: the pooled June-August Tmax slope (H2), the annual-temperature slope, the hottest day's own slope, a constant-shift control, and the recent June-August level without (H14) and with the slope. Other metrics stay as trend_level10_15_sensitivity.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_family_hottest_summer.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `ba7f8622cf57d1a538455dc84d48a89b94feac93a386a787f67973c88979b663` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_family_hottest_summer.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| h2_jja_slope | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=jja_slope) |
| h2_annual_slope | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=annual_slope) |
| h2_own_slope | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=own_slope) |
| h2_constant_shift | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=constant_shift) |
| h14_summer_level | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=summer_level) |
| h14_summer_level_slope | Hottest day = 30-year mean + a June-August-based shift (base=trend_level10_15_sensitivity, arm=summer_level_slope) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h14_summer_level | 3.98 | 8.74 | 0.0 | -0.64 | 7.8 | 1 | 3 |
| h14_summer_level_slope | 3.8 | 8.74 | 0.0 | -1.36 | 7.8 | 0 | 3 |
| h2_annual_slope | 3.64 | 8.74 | 0.0 | -1.99 | 7.8 | 0 | 3 |
| h2_constant_shift | 3.91 | 8.74 | 0.0 | -0.9 | 7.8 | 0 | 3 |
| h2_jja_slope | 3.9 | 8.74 | 0.0 | -0.94 | 7.8 | 0 | 3 |
| h2_own_slope | 3.89 | 8.74 | 0.0 | -0.99 | 7.8 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h14_summer_level | 0.33 | -2.56 | 0.0 | 0.02 | 3.87 | 2 | 3 |
| h14_summer_level_slope | 0.17 | -2.56 | 0.0 | -0.62 | 3.87 | 2 | 3 |
| h2_annual_slope | -0.19 | -2.56 | 0.0 | -2.09 | 3.87 | 0 | 3 |
| h2_constant_shift | 0.09 | -2.56 | 0.0 | -0.94 | 3.87 | 0 | 3 |
| h2_jja_slope | 0.11 | -2.56 | 0.0 | -0.89 | 3.87 | 0 | 3 |
| h2_own_slope | -0.06 | -2.56 | 0.0 | -1.56 | 3.87 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h14_summer_level | 6.57 | 17.73 | 0.0 | -1.4 | 9.94 | 0 | 3 |
| h14_summer_level_slope | 6.34 | 17.73 | 0.0 | -2.32 | 9.94 | 0 | 3 |
| h2_annual_slope | 6.32 | 17.73 | 0.0 | -2.39 | 9.94 | 0 | 3 |
| h2_constant_shift | 6.63 | 17.73 | 0.0 | -1.14 | 9.94 | 1 | 3 |
| h2_jja_slope | 6.61 | 17.73 | 0.0 | -1.23 | 9.94 | 1 | 3 |
| h2_own_slope | 6.72 | 17.73 | 0.0 | -0.81 | 9.94 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| h14_summer_level | -1.32 | 3.23 | 10.02 |
| h14_summer_level_slope | -1.32 | 3.12 | 9.59 |
| h2_annual_slope | -1.26 | 3.26 | 8.92 |
| h2_constant_shift | -1.26 | 3.54 | 9.46 |
| h2_jja_slope | -1.26 | 3.59 | 9.38 |
| h2_own_slope | -1.26 | 3.35 | 9.58 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
