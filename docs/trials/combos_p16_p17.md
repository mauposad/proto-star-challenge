# Trial: combos_p16_p17

Equal-weight forecast combinations of round-1 forecasters (P16/P17): for CDD the pooled ridge, DeepAR, the hindcast-chosen EWMA and ARIMA; for temperature the 10-year mean, EWMA, DeepAR and ARIMA; current_best for precipitation and the hottest day. Mean, median and a trimmed mean, ablations without the neural member and with CDD combined only, inverse-MSE weights from in-train hindcasts as the P17 contrast, and a second DeepAR seed as a robustness replica.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_combos_p16_p17.yaml` |
| Code version | `b7d52b3` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `hybrid_ridge_all_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_combos_p16_p17.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| hybrid_ridge_all_cdd | Pooled global model (P14; loss set by estimator, P09 median or ridge) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |
| member_deepar | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['deepar'], 'annual_avg_temp': ['deepar']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}) |
| member_ewma | Per-metric combination of registered forecasters (P16/P17): equal-weight mean, median, trimmed mean or in-train inverse-MSE weights; current_best for the rest (`forecast_combination`; combine={'cdd': ['ewma'], 'annual_avg_temp': ['ewma']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}) |
| member_arima | Per-metric combination of registered forecasters (P16/P17): equal-weight mean, median, trimmed mean or in-train inverse-MSE weights; current_best for the rest (`forecast_combination`; combine={'cdd': ['arima'], 'annual_avg_temp': ['arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}) |
| combo_mean | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'deepar', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |
| combo_median | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'deepar', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=median) |
| combo_trimmed | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'deepar', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=trimmed) |
| combo_inv_mse | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'deepar', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=inverse_mse, n_origins=2, step=7) |
| combo_mean_no_neural | Per-metric combination of registered forecasters (P16/P17): equal-weight mean, median, trimmed mean or in-train inverse-MSE weights; current_best for the rest (`forecast_combination`; combine={'cdd': ['ridge', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |
| combo_mean_cdd_only | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |
| combo_median_cdd_only | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar', 'ewma', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=median) |
| combo_mean_cdd_only_no_neural | Per-metric combination of registered forecasters (P16/P17): equal-weight mean, median, trimmed mean or in-train inverse-MSE weights; current_best for the rest (`forecast_combination`; combine={'cdd': ['ridge', 'ewma', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |
| combo_mean_seed7 | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar7', 'ewma', 'arima'], 'annual_avg_temp': ['ten', 'ewma', 'deepar7', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |
| combo_mean_cdd_only_seed7 | Per-metric combination of registered forecasters (P16/P17) with a torch member: equal-weight mean, median, trimmed mean or in-train inverse-MSE weights (`forecast_combination_torch`; combine={'cdd': ['ridge', 'deepar7', 'ewma', 'arima']}, members={'ridge': {'forecaster': 'pooled_hybrid_p09_p14', 'params': {'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}}, 'deepar': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 20170411, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'deepar7': {'forecaster': 'deepar_p08', 'params': {'context': 21, 'hidden': 32, 'layers': 2, 'dropout': 0.1, 'metric_dim': 4, 'city_dim': 4, 'seeds': 3, 'seed': 7, 'samples': 100, 'max_epochs': 40, 'patience': 6, 'batch_size': 512, 'learning_rate': 0.001, 'weight_decay': 0.0, 'min_obs_fraction': 0.5, 'holdout': 7, 'threads': 2, 'neural_metrics': ['annual_avg_temp', 'cdd']}}, 'ewma': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'arima': {'forecaster': 'arima_lai2020', 'params': {'metrics': ['annual_avg_temp', 'cdd'], 'n_jobs': 3}}, 'ten': {'forecaster': 'ten_year_mean'}}, method=mean) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| combo_inv_mse | 3.48 | 5.69 | 0.0 | 0.0 | 8.21 | 3 | 3 |
| combo_mean | 3.47 | 5.69 | 0.0 | 0.0 | 8.2 | 3 | 3 |
| combo_mean_cdd_only | 3.49 | 5.76 | 0.0 | 0.0 | 8.2 | 3 | 3 |
| combo_mean_cdd_only_no_neural | 3.51 | 5.76 | 0.0 | 0.0 | 8.27 | 3 | 3 |
| combo_mean_cdd_only_seed7 | 3.45 | 5.76 | 0.0 | 0.0 | 8.04 | 3 | 3 |
| combo_mean_no_neural | 3.34 | 5.08 | 0.0 | 0.0 | 8.27 | 2 | 3 |
| combo_mean_seed7 | 3.39 | 5.54 | 0.0 | 0.0 | 8.04 | 3 | 3 |
| combo_median | 3.43 | 5.61 | 0.0 | 0.0 | 8.12 | 3 | 3 |
| combo_median_cdd_only | 3.47 | 5.76 | 0.0 | 0.0 | 8.12 | 3 | 3 |
| combo_trimmed | 3.37 | 5.47 | 0.0 | 0.0 | 8.02 | 3 | 3 |
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| hybrid_ridge_all_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| member_arima | 2.21 | 2.87 | 0.0 | 0.0 | 5.97 | 0 | 3 |
| member_deepar | 3.36 | 6.51 | 0.0 | 0.0 | 6.91 | 2 | 3 |
| member_ewma | 2.73 | 3.9 | 0.0 | 0.0 | 7.02 | 1 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| combo_inv_mse | 1.51 | 0.52 | 0.0 | 0.0 | 5.54 | 2 | 3 |
| combo_mean | 1.51 | 0.55 | 0.0 | 0.0 | 5.51 | 2 | 3 |
| combo_mean_cdd_only | 0.99 | -1.56 | 0.0 | 0.0 | 5.51 | 2 | 3 |
| combo_mean_cdd_only_no_neural | 1.04 | -1.56 | 0.0 | 0.0 | 5.74 | 2 | 3 |
| combo_mean_cdd_only_seed7 | 0.95 | -1.56 | 0.0 | 0.0 | 5.37 | 2 | 3 |
| combo_mean_no_neural | 1.59 | 0.6 | 0.0 | 0.0 | 5.74 | 2 | 3 |
| combo_mean_seed7 | 1.49 | 0.58 | 0.0 | 0.0 | 5.37 | 2 | 3 |
| combo_median | 1.51 | 0.45 | 0.0 | 0.0 | 5.59 | 2 | 3 |
| combo_median_cdd_only | 1.01 | -1.56 | 0.0 | 0.0 | 5.59 | 2 | 3 |
| combo_trimmed | 1.49 | 0.26 | 0.0 | 0.0 | 5.7 | 2 | 3 |
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| hybrid_ridge_all_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| member_arima | 1.11 | 0.82 | 0.0 | 0.0 | 3.62 | 2 | 3 |
| member_deepar | 0.96 | -0.43 | 0.0 | 0.0 | 4.27 | 2 | 3 |
| member_ewma | 1.49 | 0.51 | 0.0 | 0.0 | 5.46 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| combo_inv_mse | 4.92 | 10.07 | 0.0 | 0.0 | 9.59 | 2 | 3 |
| combo_mean | 4.91 | 10.06 | 0.0 | 0.0 | 9.59 | 2 | 3 |
| combo_mean_cdd_only | 5.37 | 11.9 | 0.0 | 0.0 | 9.59 | 3 | 3 |
| combo_mean_cdd_only_no_neural | 5.36 | 11.9 | 0.0 | 0.0 | 9.55 | 3 | 3 |
| combo_mean_cdd_only_seed7 | 5.33 | 11.9 | 0.0 | 0.0 | 9.44 | 3 | 3 |
| combo_mean_no_neural | 4.63 | 8.96 | 0.0 | 0.0 | 9.55 | 1 | 3 |
| combo_mean_seed7 | 4.8 | 9.74 | 0.0 | 0.0 | 9.44 | 2 | 3 |
| combo_median | 4.83 | 9.98 | 0.0 | 0.0 | 9.35 | 2 | 3 |
| combo_median_cdd_only | 5.31 | 11.9 | 0.0 | 0.0 | 9.35 | 3 | 3 |
| combo_trimmed | 4.73 | 9.86 | 0.0 | 0.0 | 9.07 | 2 | 3 |
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| hybrid_ridge_all_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| member_arima | 2.98 | 4.77 | 0.0 | 0.0 | 7.16 | 0 | 3 |
| member_deepar | 5.08 | 12.15 | 0.0 | 0.0 | 8.18 | 1 | 3 |
| member_ewma | 3.64 | 6.91 | 0.0 | 0.0 | 7.65 | 0 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| combo_inv_mse | 0.24 | 3.88 | 6.3 |
| combo_mean | 0.25 | 3.87 | 6.3 |
| combo_mean_cdd_only | 0.16 | 4.14 | 6.18 |
| combo_mean_cdd_only_no_neural | 0.2 | 4.21 | 6.11 |
| combo_mean_cdd_only_seed7 | 0.13 | 4.11 | 6.11 |
| combo_mean_no_neural | 0.39 | 3.83 | 5.8 |
| combo_mean_seed7 | 0.32 | 3.73 | 6.13 |
| combo_median | 0.17 | 3.84 | 6.29 |
| combo_median_cdd_only | 0.19 | 4.07 | 6.15 |
| combo_trimmed | 0.06 | 3.75 | 6.3 |
| current_best | -0.75 | 3.56 | 5.95 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| member_arima | -0.86 | 2.7 | 4.79 |
| member_deepar | -0.91 | 3.58 | 7.4 |
| member_ewma | -0.23 | 3.21 | 5.21 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
