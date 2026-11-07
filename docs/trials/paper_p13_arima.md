# Trial: paper_p13_arima

Per-city ARIMA after Lai and Dzombak (2020): KPSS differencing, stepwise AICc order, drift when Mann-Kendall p < 0.2, Box-Cox when residuals are non-normal, full history. Variants beyond the paper: a 50-year history window, and ARIMA for temperature and CDD only with current_best for precipitation and hottest day.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-06 |
| Config | `configs/agent_paper_p13_arima.yaml` |
| Code version | `e507f5e` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `current_best` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_p13_arima.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| arima_paper | Lai & Dzombak 2020 (P13): per-series ARIMA, KPSS + stepwise AICc order, drift if Mann-Kendall p<0.2, Box-Cox if residuals non-normal; 30-year-mean fallback (`arima_lai2020`; n_jobs=5) |
| arima_window50 | Lai & Dzombak 2020 (P13): per-series ARIMA, KPSS + stepwise AICc order, drift if Mann-Kendall p<0.2, Box-Cox if residuals non-normal; 30-year-mean fallback (`arima_lai2020`; history_years=50, n_jobs=5) |
| arima_temp_cdd | Lai & Dzombak 2020 (P13): per-series ARIMA, KPSS + stepwise AICc order, drift if Mann-Kendall p<0.2, Box-Cox if residuals non-normal; 30-year-mean fallback (`arima_lai2020`; metrics=['annual_avg_temp', 'cdd'], n_jobs=5) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| arima_paper | 0.26 | 2.87 | -2.35 | -5.43 | 5.97 | 0 | 3 |
| arima_temp_cdd | 2.21 | 2.87 | 0.0 | 0.0 | 5.97 | 0 | 3 |
| arima_window50 | -2.25 | -3.08 | -4.11 | -4.54 | 2.74 | 0 | 3 |
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| arima_paper | -0.96 | 0.82 | -2.31 | -5.96 | 3.62 | 0 | 3 |
| arima_temp_cdd | 1.11 | 0.82 | 0.0 | 0.0 | 3.62 | 2 | 3 |
| arima_window50 | -2.6 | -4.49 | -3.27 | -3.01 | 0.39 | 0 | 3 |
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| arima_paper | 1.06 | 4.77 | -2.27 | -5.42 | 7.16 | 0 | 3 |
| arima_temp_cdd | 2.98 | 4.77 | 0.0 | 0.0 | 7.16 | 0 | 3 |
| arima_window50 | -2.32 | -1.79 | -4.72 | -6.02 | 3.27 | 1 | 3 |
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| arima_paper | -2.59 | 0.37 | 3.01 |
| arima_temp_cdd | -0.86 | 2.7 | 4.79 |
| arima_window50 | -9.3 | -1.37 | 3.91 |
| current_best | -0.75 | 3.56 | 5.95 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
