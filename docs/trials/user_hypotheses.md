# Trial: user_hypotheses

U1 pooled direct multi-horizon median model (linear and boosted), U2 equal-weight blend of the pooled trend and current_best, U3 pooled trend with the slope fitted within station segments. All are compared with the current candidate trend_level10_15_sensitivity.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-09 |
| Config | `configs/at_user_hypotheses.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_user_hypotheses.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| u1_direct_linear | Pooled direct multi-horizon median model on 30-year-mean anomalies (model=linear, metrics=['annual_avg_temp', 'cdd'], seed=0) |
| u1_direct_gbm | Pooled direct multi-horizon median model on 30-year-mean anomalies (model=gbm, metrics=['annual_avg_temp', 'cdd'], seed=0) |
| u2_blend_trend_current | Weighted mean of other forecasters, row by row (members=['trend_level10_15_sensitivity', 'current_best']) |
| u3_trend_segment_slope | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; slope fitted within city x station segment; 30-year mean for precipitation and hottest day |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |
| u1_direct_gbm | 1.67 | 0.23 | 0.0 | 0.0 | 6.44 | 0 | 3 |
| u1_direct_linear | 3.19 | 4.42 | 0.0 | 0.0 | 8.32 | 1 | 3 |
| u2_blend_trend_current | 3.67 | 7.61 | 0.0 | 0.0 | 7.07 | 2 | 3 |
| u3_trend_segment_slope | 4.16 | 8.83 | 0.0 | 0.0 | 7.81 | 1 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |
| u1_direct_gbm | -0.33 | -4.11 | 0.0 | 0.0 | 2.78 | 1 | 3 |
| u1_direct_linear | 1.15 | 0.36 | 0.0 | 0.0 | 4.25 | 2 | 3 |
| u2_blend_trend_current | 0.56 | -1.9 | 0.0 | 0.0 | 4.14 | 3 | 3 |
| u3_trend_segment_slope | 0.22 | -2.79 | 0.0 | 0.0 | 3.68 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |
| u1_direct_gbm | 3.08 | 3.89 | 0.0 | 0.0 | 8.42 | 0 | 3 |
| u1_direct_linear | 4.57 | 7.89 | 0.0 | 0.0 | 10.4 | 0 | 3 |
| u2_blend_trend_current | 5.99 | 15.34 | 0.0 | 0.0 | 8.63 | 2 | 3 |
| u3_trend_segment_slope | 7.03 | 18.04 | 0.0 | 0.0 | 10.07 | 1 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
| u1_direct_gbm | -4.82 | 2.77 | 7.05 |
| u1_direct_linear | -1.26 | 3.07 | 7.75 |
| u2_blend_trend_current | -0.95 | 3.86 | 8.1 |
| u3_trend_segment_slope | -1.26 | 3.57 | 10.17 |
