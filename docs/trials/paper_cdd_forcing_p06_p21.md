# Trial: paper_cdd_forcing_p06_p21

Step 9: each city's last N valid years of daily Tmean, shifted by a temperature forecast anomaly, CDD recomputed with the challenge definition (sum of max(0, Tmean - 65 F)), with a first-order (linear) ablation that removes the convexity. P06: EIA's 30-year CDD trend line, and CDD regressed on annual mean temperature evaluated at a temperature forecast. P21: forced trend on log CO2 (NOAA Mauna Loa, extrapolated linearly from the last 10 years before each cut-off) or on a regional-mean temperature, plus an AR(1) residual.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-07 |
| Config | `configs/agent_paper_cdd_forcing_p06_p21.yaml` |
| Code version | `be6f0d7` |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `current_best` |
| Submit candidate | `hybrid_ridge_all_cdd` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/agent_paper_cdd_forcing_p06_p21.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| ten_year_mean | Mean of the last 10 valid years |
| hybrid_ridge_all_cdd | Pooled global model (P14; loss set by estimator, P09 median or ridge) for the metrics in model_metrics, current_best for the rest (`pooled_hybrid_p09_p14`; alpha=1.0, estimator=ridge, model_metrics=['cdd'], train_years=None) |
| shift30_recent | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=recent, clim_years=30, mode=daily) |
| shift30_recent_linear | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=recent, clim_years=30, mode=linear) |
| shift10_trend | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=trend, clim_years=10, mode=daily, trend_shrink=0.5) |
| shift10_trend_linear | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=trend, clim_years=10, mode=linear, trend_shrink=0.5) |
| shift10_co2 | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=co2, clim_years=10, extrap_years=10, fit_years=40, min_points=15, mode=daily, phi_max=0.95) |
| eia_trend30 | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=linear_trend |
| eia_cdd_on_temp_recent | P06 (EIA, adapted): per-city OLS of annual CDD on annual mean temperature, evaluated at a temperature forecast; current_best for the other metrics (`cdd_on_temp_p06`; fit_years=30, min_points=10, temp_source=recent) |
| eia_cdd_on_temp_trend | P06 (EIA, adapted): per-city OLS of annual CDD on annual mean temperature, evaluated at a temperature forecast; current_best for the other metrics (`cdd_on_temp_p06`; fit_years=30, min_points=10, temp_source=trend, trend_shrink=0.5) |
| p21_co2_ar1 | P21: per-city OLS on a forcing (log NOAA CO2 or regional-mean temperature, extrapolated past the cut-off by a fixed linear rule) plus AR(1) residual (`forced_trend_ar1_p21`; extrap_years=10, fit_years=40, forcing=co2, metrics=['annual_avg_temp', 'cdd'], min_points=15, phi_max=0.95) |
| p21_regional_ar1 | P21: per-city OLS on a forcing (log NOAA CO2 or regional-mean temperature, extrapolated past the cut-off by a fixed linear rule) plus AR(1) residual (`forced_trend_ar1_p21`; extrap_years=30, fit_years=40, forcing=regional, metrics=['annual_avg_temp', 'cdd'], min_points=15, phi_max=0.95) |
| hybrid_ridge_shift30_avg | Step 9: recent daily Tmean climatology shifted by a temperature forecast, CDD recomputed (sum of max(0, Tmean-65F)); current_best for the other metrics (`cdd_daily_shift`; anomaly=recent, blend_ridge_weight=0.5, clim_years=30, mode=daily, ridge_params={'estimator': 'ridge', 'alpha': 1.0, 'train_years': None}) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `current_best`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 0 | 3 |
| eia_cdd_on_temp_recent | 2.82 | 5.76 | 0.0 | 0.0 | 5.5 | 2 | 3 |
| eia_cdd_on_temp_trend | 2.65 | 5.76 | 0.0 | 0.0 | 4.82 | 0 | 3 |
| eia_trend30 | -0.33 | 5.76 | 0.0 | 0.0 | -7.08 | 1 | 3 |
| hybrid_ridge_all_cdd | 3.6 | 5.76 | 0.0 | 0.0 | 8.65 | 3 | 3 |
| hybrid_ridge_shift30_avg | 3.37 | 5.76 | 0.0 | 0.0 | 7.72 | 2 | 3 |
| p21_co2_ar1 | 1.95 | 3.94 | 0.0 | 0.0 | 3.86 | 1 | 3 |
| p21_regional_ar1 | 1.38 | 1.88 | 0.0 | 0.0 | 3.62 | 1 | 3 |
| shift10_co2 | 2.61 | 5.76 | 0.0 | 0.0 | 4.67 | 1 | 3 |
| shift10_trend | 2.62 | 5.76 | 0.0 | 0.0 | 4.73 | 1 | 3 |
| shift10_trend_linear | 2.62 | 5.76 | 0.0 | 0.0 | 4.73 | 1 | 3 |
| shift30_recent | 2.63 | 5.76 | 0.0 | 0.0 | 4.74 | 1 | 3 |
| shift30_recent_linear | 2.63 | 5.76 | 0.0 | 0.0 | 4.75 | 1 | 3 |
| ten_year_mean | 1.34 | 5.76 | -3.94 | -2.39 | 5.91 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 0 | 3 |
| eia_cdd_on_temp_recent | 0.47 | -1.56 | 0.0 | 0.0 | 3.44 | 1 | 3 |
| eia_cdd_on_temp_trend | 0.34 | -1.56 | 0.0 | 0.0 | 2.91 | 1 | 3 |
| eia_trend30 | -1.84 | -1.56 | 0.0 | 0.0 | -5.78 | 0 | 3 |
| hybrid_ridge_all_cdd | 0.94 | -1.56 | 0.0 | 0.0 | 5.34 | 2 | 3 |
| hybrid_ridge_shift30_avg | 0.76 | -1.56 | 0.0 | 0.0 | 4.6 | 1 | 3 |
| p21_co2_ar1 | -0.02 | -3.62 | 0.0 | 0.0 | 3.54 | 1 | 3 |
| p21_regional_ar1 | -0.48 | -4.55 | 0.0 | 0.0 | 2.64 | 0 | 3 |
| shift10_co2 | 0.55 | -1.56 | 0.0 | 0.0 | 3.75 | 1 | 3 |
| shift10_trend | 0.33 | -1.56 | 0.0 | 0.0 | 2.87 | 0 | 3 |
| shift10_trend_linear | 0.33 | -1.56 | 0.0 | 0.0 | 2.9 | 0 | 3 |
| shift30_recent | 0.05 | -1.56 | 0.0 | 0.0 | 1.75 | 1 | 3 |
| shift30_recent_linear | 0.08 | -1.56 | 0.0 | 0.0 | 1.89 | 1 | 3 |
| ten_year_mean | -0.62 | -1.56 | -3.47 | -1.5 | 4.07 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 0 | 3 |
| eia_cdd_on_temp_recent | 4.68 | 11.9 | 0.0 | 0.0 | 6.82 | 2 | 3 |
| eia_cdd_on_temp_trend | 4.4 | 11.9 | 0.0 | 0.0 | 5.7 | 1 | 3 |
| eia_trend30 | 0.65 | 11.9 | 0.0 | 0.0 | -9.31 | 1 | 3 |
| hybrid_ridge_all_cdd | 5.54 | 11.9 | 0.0 | 0.0 | 10.27 | 3 | 3 |
| hybrid_ridge_shift30_avg | 5.36 | 11.9 | 0.0 | 0.0 | 9.53 | 3 | 3 |
| p21_co2_ar1 | 3.25 | 10.04 | 0.0 | 0.0 | 2.94 | 1 | 3 |
| p21_regional_ar1 | 2.78 | 7.44 | 0.0 | 0.0 | 3.66 | 2 | 3 |
| shift10_co2 | 3.96 | 11.9 | 0.0 | 0.0 | 3.95 | 1 | 3 |
| shift10_trend | 4.29 | 11.9 | 0.0 | 0.0 | 5.28 | 1 | 3 |
| shift10_trend_linear | 4.29 | 11.9 | 0.0 | 0.0 | 5.26 | 1 | 3 |
| shift30_recent | 4.65 | 11.9 | 0.0 | 0.0 | 6.71 | 2 | 3 |
| shift30_recent_linear | 4.63 | 11.9 | 0.0 | 0.0 | 6.63 | 2 | 3 |
| ten_year_mean | 2.78 | 11.9 | -4.44 | -3.16 | 6.84 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 |
| eia_cdd_on_temp_recent | -0.11 | 3.89 | 4.67 |
| eia_cdd_on_temp_trend | -0.94 | 3.42 | 5.46 |
| eia_trend30 | -4.23 | -3.01 | 6.25 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| hybrid_ridge_shift30_avg | 0.33 | 3.89 | 5.89 |
| p21_co2_ar1 | -4.26 | 1.53 | 8.58 |
| p21_regional_ar1 | -6.73 | 3.48 | 7.38 |
| shift10_co2 | -2.04 | 2.54 | 7.32 |
| shift10_trend | -1.74 | 2.91 | 6.69 |
| shift10_trend_linear | -1.74 | 2.93 | 6.68 |
| shift30_recent | -0.15 | 3.08 | 4.96 |
| shift30_recent_linear | -0.18 | 3.2 | 4.86 |
| ten_year_mean | -2.53 | 1.39 | 5.16 |
