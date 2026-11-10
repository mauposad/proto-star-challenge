# Trial: family_levels

Level adjustments to the candidate's temperature and CDD: remove the shared national residual from the pooled trend (H4); shrink city anomalies toward their region's leave-one-out mean (H11); both; and the same shrinkage toward zero as a control.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_family_levels.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_family_levels.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| h4_common_residual | Base forecast with H4 common-residual and/or H11 shrunk levels (base=trend_level10_15_sensitivity, common_residual=True) |
| h11_region_shrink | Base forecast with H4 common-residual and/or H11 shrunk levels (base=trend_level10_15_sensitivity, shrink=region) |
| h4_h11 | Base forecast with H4 common-residual and/or H11 shrunk levels (base=trend_level10_15_sensitivity, common_residual=True, shrink=region) |
| h11_zero_control | Base forecast with H4 common-residual and/or H11 shrunk levels (base=trend_level10_15_sensitivity, shrink=zero) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h11_region_shrink | 4.14 | 8.81 | 0.0 | 0.0 | 7.74 | 1 | 3 |
| h11_zero_control | 3.87 | 8.51 | 0.0 | 0.0 | 6.96 | 1 | 3 |
| h4_common_residual | 4.86 | 10.47 | 0.0 | 0.0 | 8.97 | 3 | 3 |
| h4_h11 | 4.83 | 10.56 | 0.0 | 0.0 | 8.74 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h11_region_shrink | 0.09 | -2.58 | 0.0 | 0.0 | 2.93 | 1 | 3 |
| h11_zero_control | 0.64 | -0.7 | 0.0 | 0.0 | 3.28 | 2 | 3 |
| h4_common_residual | 1.0 | -1.04 | 0.0 | 0.0 | 5.03 | 2 | 3 |
| h4_h11 | 0.74 | -1.03 | 0.0 | 0.0 | 3.98 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h11_region_shrink | 7.09 | 17.85 | 0.0 | 0.0 | 10.52 | 2 | 3 |
| h11_zero_control | 6.23 | 15.79 | 0.0 | 0.0 | 9.12 | 1 | 3 |
| h4_common_residual | 7.63 | 19.35 | 0.0 | 0.0 | 11.19 | 2 | 3 |
| h4_h11 | 7.76 | 19.5 | 0.0 | 0.0 | 11.54 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| h11_region_shrink | -0.83 | 3.63 | 9.61 |
| h11_zero_control | -0.14 | 3.76 | 7.98 |
| h4_common_residual | 0.81 | 3.81 | 9.96 |
| h4_h11 | 1.14 | 3.68 | 9.65 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
