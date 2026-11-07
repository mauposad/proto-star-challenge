# Trial: paper_neural

Neural forecasters from P05 (N-BEATS, generic and trend+generic stacks, median ensemble over lookbacks 14/21/28 and 3 seeds) and P08 (DeepAR, one global Gaussian LSTM over all series, median of sample paths over 3 seeds), each on all four metrics and as a hybrid that applies the network to temperature and CDD only and keeps current_best for precipitation and the hottest day.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_neural.yaml` |
| Code version | `e507f5e` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `current_best` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_neural.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| nbeats_generic | N-BEATS (P05): per-metric MLP residual blocks, median of an ensemble (`nbeats_p05`; architecture=generic, batch_size=1024, degree=2, generic_blocks=3, holdout=7, layers=2, learning_rate=0.001, lookbacks=[14, 21, 28], losses=['l1'], max_epochs=200, min_obs_fraction=0.5, patience=20, seed=20190510, seeds=3, threads=2, trend_blocks=2, weight_decay=0.0, width=64) |
| nbeats_interpretable | N-BEATS (P05): per-metric MLP residual blocks, median of an ensemble (`nbeats_p05`; architecture=interpretable, batch_size=1024, degree=2, generic_blocks=1, holdout=7, layers=2, learning_rate=0.001, lookbacks=[14, 21, 28], losses=['l1'], max_epochs=200, min_obs_fraction=0.5, patience=20, seed=20190510, seeds=3, threads=2, trend_blocks=2, weight_decay=0.0, width=64) |
| nbeats_hybrid | N-BEATS (P05): per-metric MLP residual blocks, median of an ensemble (`nbeats_p05`; architecture=generic, batch_size=1024, degree=2, generic_blocks=3, holdout=7, layers=2, learning_rate=0.001, lookbacks=[14, 21, 28], losses=['l1'], max_epochs=200, min_obs_fraction=0.5, neural_metrics=['annual_avg_temp', 'cdd'], patience=20, seed=20190510, seeds=3, threads=2, trend_blocks=2, weight_decay=0.0, width=64) |
| deepar_global | DeepAR (P08): global Gaussian LSTM over all series, median of sample paths (`deepar_p08`; batch_size=512, city_dim=4, context=21, dropout=0.1, hidden=32, holdout=7, layers=2, learning_rate=0.001, max_epochs=40, metric_dim=4, min_obs_fraction=0.5, patience=6, samples=100, seed=20170411, seeds=3, threads=2, weight_decay=0.0) |
| deepar_hybrid | DeepAR (P08): global Gaussian LSTM over all series, median of sample paths (`deepar_p08`; batch_size=512, city_dim=4, context=21, dropout=0.1, hidden=32, holdout=7, layers=2, learning_rate=0.001, max_epochs=40, metric_dim=4, min_obs_fraction=0.5, neural_metrics=['annual_avg_temp', 'cdd'], patience=6, samples=100, seed=20170411, seeds=3, threads=2, weight_decay=0.0) |
| nbeats_hybrid_seed7 | N-BEATS (P05): per-metric MLP residual blocks, median of an ensemble (`nbeats_p05`; architecture=generic, batch_size=1024, degree=2, generic_blocks=3, holdout=7, layers=2, learning_rate=0.001, lookbacks=[14, 21, 28], losses=['l1'], max_epochs=200, min_obs_fraction=0.5, neural_metrics=['annual_avg_temp', 'cdd'], patience=20, seed=7, seeds=3, threads=2, trend_blocks=2, weight_decay=0.0, width=64) |
| deepar_hybrid_seed7 | DeepAR (P08): global Gaussian LSTM over all series, median of sample paths (`deepar_p08`; batch_size=512, city_dim=4, context=21, dropout=0.1, hidden=32, holdout=7, layers=2, learning_rate=0.001, max_epochs=40, metric_dim=4, min_obs_fraction=0.5, neural_metrics=['annual_avg_temp', 'cdd'], patience=6, samples=100, seed=7, seeds=3, threads=2, weight_decay=0.0) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| deepar_global | 2.39 | 6.39 | -1.3 | -2.16 | 6.63 | 0 | 3 |
| deepar_hybrid | 3.36 | 6.51 | 0.0 | 0.0 | 6.91 | 2 | 3 |
| deepar_hybrid_seed7 | 3.03 | 5.88 | 0.0 | 0.0 | 6.25 | 1 | 3 |
| nbeats_generic | 2.32 | 5.83 | -1.89 | -1.13 | 6.48 | 1 | 3 |
| nbeats_hybrid | 3.08 | 5.83 | 0.0 | 0.0 | 6.48 | 2 | 3 |
| nbeats_hybrid_seed7 | 2.88 | 5.38 | 0.0 | 0.0 | 6.16 | 1 | 3 |
| nbeats_interpretable | 2.25 | 5.76 | -1.37 | -1.84 | 6.43 | 0 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| deepar_global | 0.25 | 0.35 | -2.17 | -1.94 | 4.76 | 1 | 3 |
| deepar_hybrid | 0.96 | -0.43 | 0.0 | 0.0 | 4.27 | 2 | 3 |
| deepar_hybrid_seed7 | 0.83 | -0.29 | 0.0 | 0.0 | 3.6 | 2 | 3 |
| nbeats_generic | 0.52 | 2.29 | -1.62 | 0.59 | 0.82 | 2 | 3 |
| nbeats_hybrid | 0.78 | 2.29 | 0.0 | 0.0 | 0.82 | 2 | 3 |
| nbeats_hybrid_seed7 | 1.23 | 1.26 | 0.0 | 0.0 | 3.66 | 2 | 3 |
| nbeats_interpretable | 0.92 | 1.06 | -0.88 | -0.07 | 3.57 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| deepar_global | 3.87 | 11.28 | -0.81 | -2.63 | 7.63 | 1 | 3 |
| deepar_hybrid | 5.08 | 12.15 | 0.0 | 0.0 | 8.18 | 1 | 3 |
| deepar_hybrid_seed7 | 4.63 | 10.89 | 0.0 | 0.0 | 7.61 | 1 | 3 |
| nbeats_generic | 3.39 | 8.85 | -2.09 | -2.64 | 9.44 | 1 | 3 |
| nbeats_hybrid | 4.57 | 8.85 | 0.0 | 0.0 | 9.44 | 1 | 3 |
| nbeats_hybrid_seed7 | 4.03 | 8.73 | 0.0 | 0.0 | 7.37 | 1 | 3 |
| nbeats_interpretable | 3.04 | 9.68 | -1.74 | -3.48 | 7.69 | 0 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| deepar_global | -0.79 | 2.22 | 5.75 |
| deepar_hybrid | -0.91 | 3.58 | 7.4 |
| deepar_hybrid_seed7 | -0.75 | 3.0 | 6.85 |
| nbeats_generic | -0.64 | 2.91 | 4.69 |
| nbeats_hybrid | -0.74 | 4.1 | 5.87 |
| nbeats_hybrid_seed7 | -1.05 | 4.14 | 5.57 |
| nbeats_interpretable | -0.88 | 2.85 | 4.77 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
