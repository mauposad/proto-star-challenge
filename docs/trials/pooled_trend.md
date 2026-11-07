# Trial: pooled_trend

Add a non-negative pooled warming trend to each city's recent level, for temperature and CDD. Compare one level window against two, and a CDD trend shared by all cities against one scaled by each city's own CDD per degree. Precipitation and hottest day stay on the 30-year mean.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs\lc_pooled_trend.yaml` |
| Code version | `60f00c5` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `trend_level10_15_sensitivity` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs\lc_pooled_trend.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| trend_level10 | Mean of last-[10]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled CDD slope; 30-year mean for precipitation and hottest day |
| trend_level10_15 | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled CDD slope; 30-year mean for precipitation and hottest day |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10 | 4.15 | 8.86 | 0.0 | 0.0 | 7.74 | 2 | 3 |
| trend_level10_15 | 4.02 | 8.74 | 0.0 | 0.0 | 7.33 | 2 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 2 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10 | 0.18 | -2.82 | 0.0 | 0.0 | 3.54 | 2 | 3 |
| trend_level10_15 | 0.29 | -2.56 | 0.0 | 0.0 | 3.71 | 2 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 2 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10 | 7.06 | 18.19 | 0.0 | 0.0 | 10.06 | 2 | 3 |
| trend_level10_15 | 6.76 | 17.73 | 0.0 | 0.0 | 9.32 | 2 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 2 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10 | -0.75 | 3.4 | 9.79 |
| trend_level10_15 | -1.26 | 3.73 | 9.59 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
