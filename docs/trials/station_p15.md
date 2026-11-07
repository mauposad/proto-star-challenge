# Trial: station_p15

Levels from the current station segment only (capped at the current_best window, with a fallback to the full window when the segment is short), or window means after adjusting earlier station segments by a pairwise neighbor step estimate (P15): the change in the city-minus-neighbors difference series across each station switch inside the window. Neighbors are the nearest cities without a switch of their own around it. Data up to the cut-off only. References: current_best, ten_year_mean and the submitted hybrid_ridge_all_cdd.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_station_p15.yaml` |
| Code version | `725a6f4` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `hybrid_ridge_all_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_station_p15.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| hybrid_ridge_all_cdd | Pooled global model (P14; loss set by estimator, P09 median or ridge) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |
| seg_temp_cdd | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; metrics=['annual_avg_temp', 'cdd'], min_years=5, mode=segment) |
| seg_temp_cdd_min3 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; metrics=['annual_avg_temp', 'cdd'], min_years=3, mode=segment) |
| seg_temp_cdd_cap15 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; metrics=['annual_avg_temp', 'cdd'], min_years=5, mode=segment, windows={'annual_avg_temp': 15, 'cdd': 15}) |
| seg_all_min10 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; metrics=['annual_avg_temp', 'total_precip_in', 'hottest_day_temp', 'cdd'], min_years=10, mode=segment) |
| adj_temp_cdd_k5_w5 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; max_km=1000.0, metrics=['annual_avg_temp', 'cdd'], min_side_years=3, min_t=0.0, mode=adjusted, n_neighbors=5, side_years=5) |
| adj_temp_cdd_k10_w10 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; max_km=1000.0, metrics=['annual_avg_temp', 'cdd'], min_side_years=3, min_t=0.0, mode=adjusted, n_neighbors=10, side_years=10) |
| adj_temp_cdd_k5_w5_t2 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; max_km=1000.0, metrics=['annual_avg_temp', 'cdd'], min_side_years=3, min_t=2.0, mode=adjusted, n_neighbors=5, side_years=5) |
| adj_all_k5_w10 | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; max_km=1000.0, metrics=['annual_avg_temp', 'total_precip_in', 'hottest_day_temp', 'cdd'], min_side_years=3, min_t=0.0, mode=adjusted, n_neighbors=5, side_years=10) |
| adj_temp_k5_w5_ridge_cdd | P15: level from the current station segment only (mode=segment), or window mean after adjusting earlier segments by a pairwise neighbor step estimate (mode=adjusted); base_forecaster for the other metrics (`station_p15`; base_forecaster=pooled_hybrid_p09_p14, base_params={'model_metrics': ['cdd'], 'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}, max_km=1000.0, metrics=['annual_avg_temp'], min_side_years=3, min_t=0.0, mode=adjusted, n_neighbors=5, side_years=5) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| adj_all_k5_w10 | 2.91 | 5.88 | -0.14 | -0.17 | 6.05 | 2 | 3 |
| adj_temp_cdd_k10_w10 | 2.99 | 5.89 | 0.0 | 0.0 | 6.07 | 3 | 3 |
| adj_temp_cdd_k5_w5 | 2.94 | 5.77 | 0.0 | 0.0 | 6.01 | 3 | 3 |
| adj_temp_cdd_k5_w5_t2 | 2.93 | 5.75 | 0.0 | 0.0 | 5.99 | 3 | 3 |
| adj_temp_k5_w5_ridge_cdd | 3.61 | 5.77 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| hybrid_ridge_all_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| seg_all_min10 | 2.79 | 5.76 | -0.47 | -0.03 | 5.91 | 1 | 3 |
| seg_temp_cdd | 2.96 | 5.84 | 0.0 | 0.0 | 6.02 | 2 | 3 |
| seg_temp_cdd_cap15 | 1.62 | 3.34 | 0.0 | 0.0 | 3.16 | 0 | 3 |
| seg_temp_cdd_min3 | 3.01 | 5.89 | 0.0 | 0.0 | 6.16 | 3 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| adj_all_k5_w10 | 0.63 | -1.41 | -0.16 | -0.16 | 4.23 | 2 | 3 |
| adj_temp_cdd_k10_w10 | 0.71 | -1.4 | 0.0 | 0.0 | 4.23 | 2 | 3 |
| adj_temp_cdd_k5_w5 | 0.69 | -1.48 | 0.0 | 0.0 | 4.25 | 3 | 3 |
| adj_temp_cdd_k5_w5_t2 | 0.67 | -1.5 | 0.0 | 0.0 | 4.17 | 2 | 3 |
| adj_temp_k5_w5_ridge_cdd | 0.97 | -1.48 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| hybrid_ridge_all_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| seg_all_min10 | 0.68 | -1.56 | -0.03 | 0.23 | 4.07 | 2 | 3 |
| seg_temp_cdd | 0.67 | -1.45 | 0.0 | 0.0 | 4.11 | 1 | 3 |
| seg_temp_cdd_cap15 | 0.37 | -1.36 | 0.0 | 0.0 | 2.83 | 1 | 3 |
| seg_temp_cdd_min3 | 0.73 | -1.35 | 0.0 | 0.0 | 4.26 | 2 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| adj_all_k5_w10 | 4.67 | 12.0 | -0.06 | -0.2 | 6.96 | 2 | 3 |
| adj_temp_cdd_k10_w10 | 4.75 | 12.01 | 0.0 | 0.0 | 7.0 | 3 | 3 |
| adj_temp_cdd_k5_w5 | 4.68 | 11.85 | 0.0 | 0.0 | 6.86 | 2 | 3 |
| adj_temp_cdd_k5_w5_t2 | 4.68 | 11.83 | 0.0 | 0.0 | 6.9 | 2 | 3 |
| adj_temp_k5_w5_ridge_cdd | 5.53 | 11.85 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| hybrid_ridge_all_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| seg_all_min10 | 4.41 | 11.9 | -0.76 | -0.32 | 6.84 | 1 | 3 |
| seg_temp_cdd | 4.73 | 11.95 | 0.0 | 0.0 | 6.99 | 3 | 3 |
| seg_temp_cdd_cap15 | 2.61 | 7.31 | 0.0 | 0.0 | 3.13 | 0 | 3 |
| seg_temp_cdd_min3 | 4.77 | 11.96 | 0.0 | 0.0 | 7.13 | 2 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| adj_all_k5_w10 | -0.57 | 3.57 | 5.71 |
| adj_temp_cdd_k10_w10 | -0.57 | 3.6 | 5.95 |
| adj_temp_cdd_k5_w5 | -0.7 | 3.58 | 5.95 |
| adj_temp_cdd_k5_w5_t2 | -0.71 | 3.56 | 5.95 |
| adj_temp_k5_w5_ridge_cdd | 0.23 | 4.15 | 6.44 |
| current_best | -0.75 | 3.56 | 5.95 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| seg_all_min10 | -0.63 | 3.49 | 5.52 |
| seg_temp_cdd | -0.64 | 3.56 | 5.98 |
| seg_temp_cdd_cap15 | -2.39 | 3.17 | 4.09 |
| seg_temp_cdd_min3 | -0.67 | 3.57 | 6.14 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
