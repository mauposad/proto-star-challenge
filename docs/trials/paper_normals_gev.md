# Trial: paper_normals_gev

Alternative climate normals from P02-P04 (optimal climate normal with the window picked by in-train hindcast, exponentially weighted moving averages, damped trend) and P23's nonstationary GEV median for the hottest day, against current_best and ten_year_mean.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-06 |
| Config | `configs/agent_paper_normals_gev.yaml` |
| Code version | `e507f5e` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `current_best` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_normals_gev.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| ocn | Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03) (`ocn_normal`; n_origins=4, scope=metric, windows=[5, 7, 10, 12, 15, 20, 25, 30]) |
| ocn_region | Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03) (`ocn_normal`; scope=region) |
| ocn_city | Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03) (`ocn_normal`; scope=city) |
| ocn_o8 | Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03) (`ocn_normal`; n_origins=8) |
| ocn_lead47 | Optimal climate normal: last-k-year mean, k picked by in-train hindcast (P02/P03) (`ocn_normal`; leads=[4, 5, 6, 7], n_origins=8) |
| ewma_a01 | Exponentially weighted moving average; alpha fixed or picked by hindcast (P04) (`ewma_normal`; alpha=0.1) |
| ewma_opt | Exponentially weighted moving average; alpha fixed or picked by hindcast (P04) (`ewma_normal`; alphas=[0.03, 0.05, 0.1, 0.15, 0.2, 0.3]) |
| ewma_opt_o8 | Exponentially weighted moving average; alpha fixed or picked by hindcast (P04) (`ewma_normal`; alphas=[0.02, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2, 0.3], n_origins=8) |
| optimal_o4 | Picks among k-year means and EWMAs per metric by in-train hindcast (P02/P04) (`optimal_normal`; alphas=[0.03, 0.05, 0.1, 0.2], n_origins=4, windows=[5, 10, 15, 20, 30]) |
| optimal_o8 | Picks among k-year means and EWMAs per metric by in-train hindcast (P02/P04) (`optimal_normal`; alphas=[0.03, 0.05, 0.1, 0.2], n_origins=8, windows=[5, 10, 15, 20, 30]) |
| damped_trend | Recent k-year mean plus a damped OLS slope, damping picked by hindcast (P04) (`damped_trend_normal`; phis=[0.0, 0.25, 0.5, 1.0], trend_window=30, window=10) |
| gev_trend_opt | Nonstationary GEV (location trend, shrunk) median for hottest day; other metrics from a fallback (P23) (`gev_hottest_day`; fallback=current_best, trend_shrink=[0.0, 0.25, 0.5, 1.0], window=30) |
| gev_shrink25 | Nonstationary GEV (location trend, shrunk) median for hottest day; other metrics from a fallback (P23) (`gev_hottest_day`; fallback=current_best, trend_shrink=0.25, window=30) |
| gev_stationary | Nonstationary GEV (location trend, shrunk) median for hottest day; other metrics from a fallback (P23) (`gev_hottest_day`; fallback=current_best, trend=False, window=30) |
| gev_stationary_w40 | Nonstationary GEV (location trend, shrunk) median for hottest day; other metrics from a fallback (P23) (`gev_hottest_day`; fallback=current_best, trend=False, window=40) |
| hybrid_a | Per metric: any registered forecaster or baseline, e.g. OCN + GEV (P02/P04/P23) (`normals_hybrid`; components={'annual_avg_temp': {'forecaster': 'ten_year_mean'}, 'total_precip_in': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}, 'hottest_day_temp': {'forecaster': 'gev_hottest_day', 'params': {'trend': False}}, 'cdd': {'forecaster': 'ewma_normal', 'params': {'alphas': [0.03, 0.05, 0.1, 0.15, 0.2, 0.3]}}}) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| damped_trend | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |
| ewma_a01 | 1.9 | 3.79 | -1.17 | -0.16 | 5.17 | 1 | 3 |
| ewma_opt | 2.71 | 3.9 | 0.19 | -0.26 | 7.02 | 1 | 3 |
| ewma_opt_o8 | 2.69 | 3.9 | -0.14 | 0.21 | 6.77 | 1 | 3 |
| gev_shrink25 | 2.84 | 5.76 | 0.0 | -0.33 | 5.91 | 1 | 3 |
| gev_stationary | 2.92 | 5.76 | 0.0 | 0.02 | 5.91 | 1 | 3 |
| gev_stationary_w40 | 2.84 | 5.76 | 0.0 | -0.32 | 5.91 | 1 | 3 |
| gev_trend_opt | 2.55 | 5.76 | 0.0 | -1.47 | 5.91 | 0 | 3 |
| hybrid_a | 3.25 | 5.76 | 0.19 | 0.02 | 7.02 | 2 | 3 |
| ocn | 2.35 | 5.42 | -0.39 | -1.94 | 6.32 | 1 | 3 |
| ocn_city | 0.55 | 2.45 | -3.19 | -2.19 | 5.11 | 0 | 3 |
| ocn_lead47 | 1.86 | 3.88 | -0.39 | -0.72 | 4.66 | 1 | 3 |
| ocn_o8 | 1.32 | 0.4 | -0.39 | -1.38 | 6.66 | 1 | 3 |
| ocn_region | 1.22 | 1.18 | -0.48 | -1.8 | 5.99 | 1 | 3 |
| optimal_o4 | 1.85 | 4.01 | -0.29 | -1.49 | 5.18 | 0 | 3 |
| optimal_o8 | 1.99 | 3.08 | -0.29 | -0.41 | 5.58 | 1 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| damped_trend | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |
| ewma_a01 | 1.12 | 0.78 | -0.55 | 0.36 | 3.88 | 2 | 3 |
| ewma_opt | 1.69 | 0.51 | 0.48 | 0.3 | 5.46 | 2 | 3 |
| ewma_opt_o8 | 1.75 | 0.51 | 0.49 | 0.53 | 5.46 | 2 | 3 |
| gev_shrink25 | 0.81 | -1.56 | 0.0 | 0.75 | 4.07 | 2 | 3 |
| gev_stationary | 0.67 | -1.56 | 0.0 | 0.19 | 4.07 | 2 | 3 |
| gev_stationary_w40 | 0.58 | -1.56 | 0.0 | -0.19 | 4.07 | 1 | 3 |
| gev_trend_opt | 0.69 | -1.56 | 0.0 | 0.24 | 4.07 | 2 | 3 |
| hybrid_a | 1.14 | -1.56 | 0.48 | 0.19 | 5.46 | 2 | 3 |
| ocn | 0.49 | -1.61 | 0.03 | -0.7 | 4.24 | 2 | 3 |
| ocn_city | -0.54 | -1.91 | -3.06 | -1.22 | 4.04 | 0 | 3 |
| ocn_lead47 | 0.24 | -1.64 | 0.03 | 0.33 | 2.23 | 1 | 3 |
| ocn_o8 | 0.17 | -1.98 | 0.03 | -0.66 | 3.31 | 1 | 3 |
| ocn_region | 0.11 | -2.75 | -0.19 | -1.15 | 4.52 | 0 | 3 |
| optimal_o4 | 1.19 | 0.09 | 0.18 | -0.21 | 4.69 | 2 | 3 |
| optimal_o8 | 1.43 | 0.47 | 0.18 | 0.13 | 4.94 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| damped_trend | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |
| ewma_a01 | 2.5 | 6.41 | -1.66 | -0.64 | 5.88 | 1 | 3 |
| ewma_opt | 3.46 | 6.91 | 0.02 | -0.75 | 7.65 | 0 | 3 |
| ewma_opt_o8 | 3.35 | 6.91 | -0.57 | -0.09 | 7.17 | 0 | 3 |
| gev_shrink25 | 4.43 | 11.9 | 0.0 | -1.01 | 6.84 | 1 | 3 |
| gev_stationary | 4.69 | 11.9 | 0.0 | 0.05 | 6.84 | 2 | 3 |
| gev_stationary_w40 | 4.62 | 11.9 | 0.0 | -0.25 | 6.84 | 1 | 3 |
| gev_trend_opt | 4.0 | 11.9 | 0.0 | -2.73 | 6.84 | 1 | 3 |
| hybrid_a | 4.9 | 11.9 | 0.02 | 0.05 | 7.65 | 2 | 3 |
| ocn | 3.68 | 11.35 | -0.69 | -3.0 | 7.08 | 1 | 3 |
| ocn_city | 1.32 | 6.21 | -3.4 | -2.85 | 5.32 | 0 | 3 |
| ocn_lead47 | 2.99 | 8.53 | -0.69 | -1.62 | 5.73 | 1 | 3 |
| ocn_o8 | 2.1 | 2.75 | -0.69 | -2.08 | 8.41 | 1 | 3 |
| ocn_region | 1.97 | 4.66 | -0.67 | -2.43 | 6.32 | 1 | 3 |
| optimal_o4 | 2.37 | 7.42 | -0.59 | -2.56 | 5.21 | 0 | 3 |
| optimal_o8 | 2.45 | 5.57 | -0.59 | -0.88 | 5.72 | 0 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| damped_trend | -2.53 | 1.39 | 5.16 |
| ewma_a01 | 0.52 | 2.27 | 2.93 |
| ewma_opt | 0.13 | 3.06 | 4.96 |
| ewma_opt_o8 | -0.11 | 3.04 | 5.13 |
| gev_shrink25 | -1.02 | 3.4 | 6.13 |
| gev_stationary | -0.68 | 3.53 | 5.92 |
| gev_stationary_w40 | -0.85 | 3.58 | 5.79 |
| gev_trend_opt | -1.74 | 3.51 | 5.89 |
| hybrid_a | 0.45 | 3.99 | 5.31 |
| ocn | -1.41 | 2.25 | 6.22 |
| ocn_city | -2.7 | 0.63 | 3.71 |
| ocn_lead47 | -2.55 | 1.79 | 6.33 |
| ocn_o8 | -4.2 | 1.83 | 6.33 |
| ocn_region | -3.47 | 0.98 | 6.15 |
| optimal_o4 | -0.89 | 2.54 | 3.92 |
| optimal_o8 | -0.06 | 2.84 | 3.19 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
