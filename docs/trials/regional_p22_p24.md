# Trial: regional_p22_p24

P22: each city's 30-year trend shrunk toward its region's (or elevation band's) trend by empirical-Bayes partial pooling, added (damped) to the 10-year level, for temperature and CDD. P24: the round-1 pooled ridge for CDD with pooling groups (region, elevation band, population band, NLCD 2016 land cover) as group interactions, separate models or one-hots. Precipitation and hottest day keep current_best everywhere.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_regional_p22_p24.yaml` |
| Code version | `913aedf` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `hybrid_ridge_all_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_regional_p22_p24.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| hybrid_ridge_all_cdd | Pooled global model (P14; loss set by estimator, P09 median or ridge) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |
| p22_eb_region | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; damping=1.0, group_by=region, level_years=10, shrink=eb, trend_years=30) |
| p22_eb_region_damped | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; damping=0.5, group_by=region, level_years=10, shrink=eb, trend_years=30) |
| p22_eb_region_flat | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; damping=1.0, extrapolate_lead=False, group_by=region, level_years=10, shrink=eb, trend_years=30) |
| p22_region_trend_damped | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; damping=0.5, group_by=region, level_years=10, shrink=group, trend_years=30) |
| p22_eb_elevation_damped | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; bands={'elevation': [130.0, 310.0]}, damping=0.5, group_by=elevation, level_years=10, shrink=eb, trend_years=30) |
| p22_eb_region_long_damped | Recent level plus a city trend shrunk toward its group's trend by empirical-Bayes partial pooling (P22), damped; current_best for metrics not modelled (`regional_trend_p22`; damping=0.5, group_by=region, level_years=10, shrink=eb, trend_years=50) |
| p24_ridge_region_interact | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, group_by=['region'], mode=interact, model_metrics=['cdd'], train_years=None) |
| p24_ridge_elevation_interact | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, bands={'elevation': [130.0, 310.0]}, group_by=['elevation'], mode=interact, model_metrics=['cdd'], train_years=None) |
| p24_ridge_population_interact | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, bands={'population': [50000.0, 175000.0]}, group_by=['population'], mode=interact, model_metrics=['cdd'], train_years=None) |
| p24_ridge_landcover_interact | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, group_by=['land_cover'], mode=interact, model_metrics=['cdd'], train_years=None) |
| p24_ridge_region_separate | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, group_by=['region'], mode=separate, model_metrics=['cdd'], train_years=None) |
| p24_ridge_all_groups_additive | Round-1 pooled model (P14/P09 features) with pooling groups (P24): region, elevation, population or land cover as separate models, one-hots or interactions (`pooled_groups_p24`; alpha=1.0, bands={'elevation': [130.0, 310.0], 'population': [50000.0, 175000.0]}, group_by=['elevation', 'population', 'land_cover'], mode=additive, model_metrics=['cdd'], train_years=None) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| hybrid_ridge_all_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| p22_eb_elevation_damped | 2.68 | 5.19 | 0.0 | 0.0 | 5.52 | 1 | 3 |
| p22_eb_region | 1.75 | 2.95 | 0.0 | 0.0 | 4.04 | 1 | 3 |
| p22_eb_region_damped | 2.73 | 5.18 | 0.0 | 0.0 | 5.75 | 1 | 3 |
| p22_eb_region_flat | 2.63 | 4.93 | 0.0 | 0.0 | 5.57 | 1 | 3 |
| p22_eb_region_long_damped | 2.68 | 4.78 | 0.0 | 0.0 | 5.93 | 1 | 3 |
| p22_region_trend_damped | 3.08 | 5.88 | 0.0 | 0.0 | 6.42 | 2 | 3 |
| p24_ridge_all_groups_additive | 3.59 | 5.76 | 0.0 | 0.0 | 8.6 | 3 | 3 |
| p24_ridge_elevation_interact | 3.43 | 5.76 | 0.0 | 0.0 | 7.95 | 3 | 3 |
| p24_ridge_landcover_interact | 3.52 | 5.76 | 0.0 | 0.0 | 8.3 | 3 | 3 |
| p24_ridge_population_interact | 3.61 | 5.76 | 0.0 | 0.0 | 8.69 | 3 | 3 |
| p24_ridge_region_interact | 3.56 | 5.76 | 0.0 | 0.0 | 8.47 | 3 | 3 |
| p24_ridge_region_separate | 3.54 | 5.76 | 0.0 | 0.0 | 8.4 | 3 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| hybrid_ridge_all_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| p22_eb_elevation_damped | 0.03 | -3.18 | 0.0 | 0.0 | 3.3 | 0 | 3 |
| p22_eb_region | -0.92 | -5.34 | 0.0 | 0.0 | 1.66 | 0 | 3 |
| p22_eb_region_damped | 0.05 | -3.14 | 0.0 | 0.0 | 3.35 | 0 | 3 |
| p22_eb_region_flat | -0.24 | -3.96 | 0.0 | 0.0 | 3.0 | 1 | 3 |
| p22_eb_region_long_damped | 0.42 | -2.52 | 0.0 | 0.0 | 4.19 | 1 | 3 |
| p22_region_trend_damped | 0.19 | -2.79 | 0.0 | 0.0 | 3.54 | 0 | 3 |
| p24_ridge_all_groups_additive | 0.95 | -1.56 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| p24_ridge_elevation_interact | 0.98 | -1.56 | 0.0 | 0.0 | 5.47 | 2 | 3 |
| p24_ridge_landcover_interact | 0.89 | -1.56 | 0.0 | 0.0 | 5.14 | 2 | 3 |
| p24_ridge_population_interact | 0.95 | -1.56 | 0.0 | 0.0 | 5.38 | 2 | 3 |
| p24_ridge_region_interact | 1.18 | -1.56 | 0.0 | 0.0 | 6.28 | 2 | 3 |
| p24_ridge_region_separate | 1.19 | -1.56 | 0.0 | 0.0 | 6.31 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| hybrid_ridge_all_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| p22_eb_elevation_damped | 4.65 | 12.2 | 0.0 | 0.0 | 6.42 | 2 | 3 |
| p22_eb_region | 3.66 | 9.93 | 0.0 | 0.0 | 4.71 | 1 | 3 |
| p22_eb_region_damped | 4.73 | 12.15 | 0.0 | 0.0 | 6.77 | 2 | 3 |
| p22_eb_region_flat | 4.79 | 12.37 | 0.0 | 0.0 | 6.79 | 2 | 3 |
| p22_eb_region_long_damped | 4.34 | 10.88 | 0.0 | 0.0 | 6.47 | 1 | 3 |
| p22_region_trend_damped | 5.24 | 13.13 | 0.0 | 0.0 | 7.82 | 2 | 3 |
| p24_ridge_all_groups_additive | 5.52 | 11.9 | 0.0 | 0.0 | 10.18 | 3 | 3 |
| p24_ridge_elevation_interact | 5.18 | 11.9 | 0.0 | 0.0 | 8.83 | 3 | 3 |
| p24_ridge_landcover_interact | 5.43 | 11.9 | 0.0 | 0.0 | 9.81 | 3 | 3 |
| p24_ridge_population_interact | 5.55 | 11.9 | 0.0 | 0.0 | 10.3 | 3 | 3 |
| p24_ridge_region_interact | 5.23 | 11.9 | 0.0 | 0.0 | 9.03 | 2 | 3 |
| p24_ridge_region_separate | 5.2 | 11.9 | 0.0 | 0.0 | 8.9 | 2 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| p22_eb_elevation_damped | -2.85 | 3.13 | 7.76 |
| p22_eb_region | -5.44 | 1.6 | 9.09 |
| p22_eb_region_damped | -2.78 | 3.19 | 7.79 |
| p22_eb_region_flat | -2.7 | 2.75 | 7.83 |
| p22_eb_region_long_damped | -3.08 | 3.04 | 8.06 |
| p22_region_trend_damped | -2.21 | 3.58 | 7.86 |
| p24_ridge_all_groups_additive | 0.24 | 4.11 | 6.43 |
| p24_ridge_elevation_interact | -0.24 | 4.17 | 6.36 |
| p24_ridge_landcover_interact | 0.14 | 4.01 | 6.4 |
| p24_ridge_population_interact | 0.17 | 4.21 | 6.45 |
| p24_ridge_region_interact | -0.32 | 4.35 | 6.65 |
| p24_ridge_region_separate | -0.36 | 4.35 | 6.64 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
