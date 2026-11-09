# Trial: hybrid

Per-metric combinations of the team's two best models: the pooled trend (better on temperature) and the pooled ridge (better on CDD). Also tests a new idea: a damped hottest-day trend scaled by each city's hottest-day change per degree of warming.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-08 |
| Config | `configs\lc_hybrid.yaml` |
| Code version | `add4c06` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `h2_mean_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs\lc_hybrid.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| trend | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for hottest day; 30-year mean for precipitation |
| ridge_cdd | Pooled global model (P14; loss set by estimator, P09 median or ridge) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |
| h1_trend_temp_ridge_cdd | Per metric, equal-weight blend: annual_avg_temp=mean(trend); total_precip_in=mean(trend); hottest_day_temp=mean(trend); cdd=mean(ridge_cdd) |
| h2_mean_cdd | Per metric, equal-weight blend: annual_avg_temp=mean(trend); total_precip_in=mean(trend); hottest_day_temp=mean(trend); cdd=mean(trend, ridge_cdd) |
| h3_mean_temp_cdd | Per metric, equal-weight blend: annual_avg_temp=mean(trend, ridge_temp_cdd); total_precip_in=mean(trend); hottest_day_temp=mean(trend); cdd=mean(trend, ridge_cdd) |
| h4_mean_cdd_hot50 | Per metric, equal-weight blend: annual_avg_temp=mean(trend); total_precip_in=mean(trend); hottest_day_temp=mean(trend_hot50); cdd=mean(trend, ridge_cdd) |
| h5_mean_cdd_hot100 | Per metric, equal-weight blend: annual_avg_temp=mean(trend); total_precip_in=mean(trend); hottest_day_temp=mean(trend_hot100); cdd=mean(trend, ridge_cdd) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 2 | 3 |
| h1_trend_temp_ridge_cdd | 4.35 | 8.74 | 0.0 | 0.0 | 8.65 | 2 | 3 |
| h2_mean_cdd | 4.41 | 8.74 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| h3_mean_temp_cdd | 4.08 | 7.43 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| h4_mean_cdd_hot50 | 4.27 | 8.74 | 0.0 | -0.57 | 8.91 | 2 | 3 |
| h5_mean_cdd_hot100 | 4.01 | 8.74 | 0.0 | -1.59 | 8.91 | 2 | 3 |
| ridge_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 2 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 2 | 3 |
| h1_trend_temp_ridge_cdd | 0.7 | -2.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| h2_mean_cdd | 0.7 | -2.56 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| h3_mean_temp_cdd | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| h4_mean_cdd_hot50 | 0.58 | -2.56 | 0.0 | -0.47 | 5.35 | 2 | 3 |
| h5_mean_cdd_hot100 | 0.37 | -2.56 | 0.0 | -1.29 | 5.35 | 2 | 3 |
| ridge_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 2 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 2 | 3 |
| h1_trend_temp_ridge_cdd | 7.0 | 17.73 | 0.0 | 0.0 | 10.27 | 2 | 3 |
| h2_mean_cdd | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| h3_mean_temp_cdd | 6.05 | 13.47 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| h4_mean_cdd_hot50 | 6.91 | 17.73 | 0.0 | -0.82 | 10.74 | 2 | 3 |
| h5_mean_cdd_hot100 | 6.56 | 17.73 | 0.0 | -2.23 | 10.74 | 2 | 3 |
| ridge_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 2 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| h1_trend_temp_ridge_cdd | -0.08 | 4.37 | 8.76 |
| h2_mean_cdd | -0.38 | 4.19 | 9.43 |
| h3_mean_temp_cdd | -0.12 | 4.26 | 8.11 |
| h4_mean_cdd_hot50 | -0.38 | 4.1 | 9.09 |
| h5_mean_cdd_hot100 | -0.38 | 3.92 | 8.5 |
| ridge_cdd | 0.24 | 4.13 | 6.44 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend | -1.26 | 3.76 | 9.91 |
