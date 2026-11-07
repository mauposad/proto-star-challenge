# Trial: paper_p09_p14_pooled

One model pooled across all 210 cities, per metric (or across metrics), on per-series normalized lags and trailing means plus Lat/Lon/region, direct multi-horizon for leads 1-7. Median (pinball 0.5) linear and boosted variants, with a squared-loss ridge ablation, and per-metric hybrids that use the pooled model for CDD only.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_p09_p14_pooled.yaml` |
| Code version | `0039788` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `hybrid_ridge_all_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_p09_p14_pooled.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| pooled_ql | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=0.0, estimator=quantile_linear, n_lags=10, quantile=0.5, train_years=60) |
| pooled_ql_lags20 | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; estimator=quantile_linear, n_lags=20, quantile=0.5, train_years=60) |
| pooled_ql_all_history | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; estimator=quantile_linear, origin_stride=2, quantile=0.5, train_years=None) |
| pooled_ridge | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=1.0, estimator=ridge, train_years=60) |
| pooled_ridge_all_history | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=1.0, estimator=ridge, train_years=None) |
| pooled_ridge_all_alpha100 | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=100.0, estimator=ridge, train_years=None) |
| pooled_ridge_all_lags20 | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=1.0, estimator=ridge, n_lags=20, train_years=None) |
| pooled_ridge_all_nostatic | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=1.0, estimator=ridge, train_years=None, use_static=False) |
| pooled_ridge_pool_metrics | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; alpha=1.0, estimator=ridge, pool_metrics=True, train_years=60) |
| pooled_hgb | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; estimator=hgb_quantile, hgb={'max_iter': 300, 'learning_rate': 0.05, 'max_leaf_nodes': 15, 'min_samples_leaf': 100}, per_lead=False, quantile=0.5, seed=0, train_years=60) |
| pooled_hgb_pool_metrics | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; estimator=hgb_quantile, hgb={'max_iter': 300, 'learning_rate': 0.05, 'max_leaf_nodes': 15, 'min_samples_leaf': 100}, per_lead=False, pool_metrics=True, quantile=0.5, seed=0, train_years=60) |
| pooled_hgb_all_pool_metrics | Global (pooled over cities) direct multi-horizon median model on per-series normalized lags, trailing means, Lat/Lon, region (P14 + P09) (`pooled_median_p09_p14`; estimator=hgb_quantile, hgb={'max_iter': 200, 'learning_rate': 0.05, 'max_leaf_nodes': 7, 'min_samples_leaf': 200}, per_lead=False, pool_metrics=True, quantile=0.5, seed=0, train_years=None) |
| hybrid_ql_cdd | Pooled median model (P14 + P09) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; estimator=quantile_linear, model_metrics=['cdd'], quantile=0.5, train_years=60) |
| hybrid_ql_all_cdd | Pooled median model (P14 + P09) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; estimator=quantile_linear, model_metrics=['cdd'], origin_stride=2, quantile=0.5, train_years=None) |
| hybrid_ridge_all_cdd | Pooled median model (P14 + P09) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| hybrid_ql_all_cdd | 2.34 | 5.76 | 0.0 | 0.0 | 3.59 | 1 | 3 |
| hybrid_ql_cdd | 3.2 | 5.76 | 0.0 | 0.0 | 7.02 | 2 | 3 |
| hybrid_ridge_all_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| pooled_hgb | 0.93 | 2.02 | -1.71 | -1.27 | 4.66 | 0 | 3 |
| pooled_hgb_all_pool_metrics | 2.19 | 4.45 | -1.4 | -1.36 | 7.08 | 1 | 3 |
| pooled_hgb_pool_metrics | 1.77 | 3.28 | -1.21 | -0.77 | 5.8 | 1 | 3 |
| pooled_ql | 2.22 | 2.57 | -1.17 | 0.44 | 7.02 | 1 | 3 |
| pooled_ql_all_history | 0.69 | 2.79 | -1.43 | -2.19 | 3.59 | 1 | 3 |
| pooled_ql_lags20 | 1.37 | 0.93 | -1.28 | -0.94 | 6.75 | 0 | 3 |
| pooled_ridge | 2.24 | 2.47 | -1.15 | -0.14 | 7.78 | 2 | 3 |
| pooled_ridge_all_alpha100 | 2.78 | 4.92 | -0.89 | -1.61 | 8.69 | 1 | 3 |
| pooled_ridge_all_history | 2.75 | 4.87 | -0.9 | -1.63 | 8.65 | 1 | 3 |
| pooled_ridge_all_lags20 | 2.34 | 3.84 | -0.99 | -2.46 | 8.96 | 0 | 3 |
| pooled_ridge_all_nostatic | 2.7 | 5.18 | -0.82 | -1.84 | 8.28 | 1 | 3 |
| pooled_ridge_pool_metrics | 1.58 | 3.77 | -4.05 | -1.4 | 7.98 | 1 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| hybrid_ql_all_cdd | -0.96 | -1.56 | 0.0 | 0.0 | -2.3 | 1 | 3 |
| hybrid_ql_cdd | 0.85 | -1.56 | 0.0 | 0.0 | 4.97 | 2 | 3 |
| hybrid_ridge_all_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| pooled_hgb | 1.13 | 0.17 | -0.95 | 1.16 | 4.13 | 2 | 3 |
| pooled_hgb_all_pool_metrics | 1.22 | 0.92 | -1.33 | 0.13 | 5.16 | 2 | 3 |
| pooled_hgb_pool_metrics | 1.83 | 0.93 | -0.67 | 1.38 | 5.69 | 2 | 3 |
| pooled_ql | 1.79 | 2.12 | -1.39 | 1.46 | 4.97 | 2 | 3 |
| pooled_ql_all_history | -2.04 | -1.82 | -2.21 | -1.82 | -2.3 | 0 | 3 |
| pooled_ql_lags20 | 1.65 | 1.33 | -1.48 | 1.44 | 5.3 | 1 | 3 |
| pooled_ridge | 1.64 | 1.49 | -0.84 | 0.1 | 5.78 | 2 | 3 |
| pooled_ridge_all_alpha100 | 1.06 | 1.64 | -1.24 | -1.54 | 5.37 | 2 | 3 |
| pooled_ridge_all_history | 1.03 | 1.63 | -1.27 | -1.57 | 5.34 | 2 | 3 |
| pooled_ridge_all_lags20 | 1.24 | 1.33 | -1.23 | -1.19 | 6.04 | 2 | 3 |
| pooled_ridge_all_nostatic | 0.76 | 1.3 | -1.02 | -1.81 | 4.55 | 2 | 3 |
| pooled_ridge_pool_metrics | 1.17 | 1.44 | -2.47 | -0.61 | 6.3 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| hybrid_ql_all_cdd | 4.73 | 11.9 | 0.0 | 0.0 | 7.04 | 1 | 3 |
| hybrid_ql_cdd | 4.9 | 11.9 | 0.0 | 0.0 | 7.7 | 2 | 3 |
| hybrid_ridge_all_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| pooled_hgb | 0.56 | 3.34 | -2.23 | -3.11 | 4.24 | 1 | 3 |
| pooled_hgb_all_pool_metrics | 2.8 | 7.38 | -1.36 | -2.73 | 7.92 | 0 | 3 |
| pooled_hgb_pool_metrics | 1.58 | 5.01 | -1.56 | -2.36 | 5.22 | 1 | 3 |
| pooled_ql | 2.21 | 2.71 | -1.04 | -0.55 | 7.7 | 1 | 3 |
| pooled_ql_all_history | 2.43 | 6.33 | -0.88 | -2.78 | 7.04 | 1 | 3 |
| pooled_ql_lags20 | 0.9 | 0.56 | -1.19 | -2.89 | 7.12 | 1 | 3 |
| pooled_ridge | 2.38 | 3.08 | -1.5 | -0.56 | 8.49 | 1 | 3 |
| pooled_ridge_all_alpha100 | 3.8 | 7.6 | -0.7 | -2.03 | 10.32 | 1 | 3 |
| pooled_ridge_all_history | 3.76 | 7.51 | -0.69 | -2.03 | 10.27 | 1 | 3 |
| pooled_ridge_all_lags20 | 2.9 | 6.03 | -0.88 | -3.81 | 10.27 | 1 | 3 |
| pooled_ridge_all_nostatic | 3.87 | 8.31 | -0.73 | -2.29 | 10.19 | 2 | 3 |
| pooled_ridge_pool_metrics | 1.73 | 5.59 | -5.3 | -2.06 | 8.7 | 1 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| hybrid_ql_all_cdd | 0.46 | 2.26 | 4.29 |
| hybrid_ql_cdd | 0.53 | 3.57 | 5.49 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| pooled_hgb | -2.48 | -0.66 | 5.92 |
| pooled_hgb_all_pool_metrics | -0.43 | 2.22 | 4.8 |
| pooled_hgb_pool_metrics | -0.96 | 0.27 | 6.02 |
| pooled_ql | -0.25 | 1.44 | 5.47 |
| pooled_ql_all_history | -0.6 | 0.88 | 1.79 |
| pooled_ql_lags20 | -2.67 | 1.23 | 5.53 |
| pooled_ridge | -0.03 | 0.67 | 6.1 |
| pooled_ridge_all_alpha100 | 0.08 | 2.92 | 5.33 |
| pooled_ridge_all_history | 0.03 | 2.89 | 5.32 |
| pooled_ridge_all_lags20 | -1.42 | 2.83 | 5.6 |
| pooled_ridge_all_nostatic | 0.1 | 3.13 | 4.87 |
| pooled_ridge_pool_metrics | 0.22 | 0.34 | 4.17 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
