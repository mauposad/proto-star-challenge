# Trial: crm

Coupled Regional Model: the champion's levels and non-negative pooled trend, with regional slopes shrunk toward the pooled slope by empirical Bayes (fixed regions or spectral clusters recomputed per fold), an optional lasso VAR(1) of regional anomalies for the first years, and station-segment or regional empirical-Bayes levels for precipitation and hottest day.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-08 |
| Config | `configs/mp_crm.yaml` |
| Code version | `61b8035` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_crm.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| current_best | Per metric: annual_avg_temp=ten_year_mean, total_precip_in=thirty_year_mean, hottest_day_temp=thirty_year_mean, cdd=ten_year_mean |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| crm_fixed_k0 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 0.0); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_fixed_k05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 0.5); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_fixed | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_fixed_cdd_slope | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional CDD slope; 30-year mean for total_precip_in, hottest_day_temp |
| crm_fixed_cdd_rescaled | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional CDD slope spread by city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral4 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 4 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral5 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 5 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral6 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral4_cdd_rescaled | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 4 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional CDD slope spread by city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral5_cdd_rescaled | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 5 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional CDD slope spread by city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral6_cdd_rescaled | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional CDD slope spread by city CDD per degree; 30-year mean for total_precip_in, hottest_day_temp |
| crm_fixed_var05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 fixed regions by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha CV, 40 years, damping 0.5); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha CV, 40 years, damping 1.0); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha CV, 40 years, damping 0.5); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_a01 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha 0.1, 40 years, damping 1.0); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_cs | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha CV, 40 years, damping 1.0, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_cs05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha CV, 40 years, damping 0.5, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_a01_cs | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha 0.1, 40 years, damping 1.0, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_a01_cs05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions (alpha 0.1, 40 years, damping 0.5, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_hot | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions on ['hottest_day_temp'] (alpha 0.1, 40 years, damping 1.0, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_hot05 | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions on ['hottest_day_temp'] (alpha 0.1, 40 years, damping 0.5, city-scaled); 30-year mean for total_precip_in, hottest_day_temp |
| crm_spectral6_seg | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; current-station-segment mean (>= 15 years) for total_precip_in, hottest_day_temp |
| crm_spectral6_eb | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp |
| crm_s6_var_hot_seg | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions on ['hottest_day_temp'] (alpha 0.1, 40 years, damping 1.0, city-scaled); current-station-segment mean (>= 15 years) for total_precip_in, hottest_day_temp |
| crm_s6_var_hot_eb | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions on ['hottest_day_temp'] (alpha 0.1, 40 years, damping 1.0, city-scaled); regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp |
| crm_spectral6_urban | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; 30-year mean for total_precip_in, hottest_day_temp |
| crm_s6_var_hot_eb_urban | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; lasso VAR(1) regional interactions on ['hottest_day_temp'] (alpha 0.1, 40 years, damping 1.0, city-scaled); temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp |
| crm_s6_eb_urban | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| crm_fixed | 4.24 | 8.88 | 0.0 | 0.0 | 8.06 | 2 | 3 |
| crm_fixed_cdd_rescaled | 4.19 | 8.88 | 0.0 | 0.0 | 7.89 | 2 | 3 |
| crm_fixed_cdd_slope | 4.12 | 8.88 | 0.0 | 0.0 | 7.6 | 2 | 3 |
| crm_fixed_k0 | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 2 | 3 |
| crm_fixed_k05 | 4.19 | 8.82 | 0.0 | 0.0 | 7.94 | 2 | 3 |
| crm_fixed_var05 | 4.22 | 8.84 | -0.17 | 0.09 | 8.12 | 2 | 3 |
| crm_s6_eb_urban | 4.39 | 9.11 | 0.06 | 0.06 | 8.33 | 2 | 3 |
| crm_s6_var | 4.14 | 9.13 | -0.13 | -0.08 | 7.65 | 2 | 3 |
| crm_s6_var05 | 4.24 | 9.07 | -0.05 | -0.02 | 7.95 | 2 | 3 |
| crm_s6_var_a01 | 4.26 | 9.37 | -0.3 | 0.57 | 7.4 | 2 | 3 |
| crm_s6_var_a01_cs | 4.26 | 9.18 | -0.27 | 0.58 | 7.55 | 2 | 3 |
| crm_s6_var_a01_cs05 | 4.39 | 9.18 | -0.07 | 0.39 | 8.07 | 2 | 3 |
| crm_s6_var_cs | 4.17 | 9.09 | -0.04 | -0.09 | 7.73 | 2 | 3 |
| crm_s6_var_cs05 | 4.25 | 9.05 | -0.0 | -0.03 | 7.99 | 2 | 3 |
| crm_s6_var_hot | 4.45 | 9.01 | 0.0 | 0.58 | 8.2 | 2 | 3 |
| crm_s6_var_hot05 | 4.4 | 9.01 | 0.0 | 0.39 | 8.2 | 2 | 3 |
| crm_s6_var_hot_eb | 4.48 | 9.01 | 0.06 | 0.64 | 8.2 | 2 | 3 |
| crm_s6_var_hot_eb_urban | 4.53 | 9.11 | 0.06 | 0.6 | 8.33 | 2 | 3 |
| crm_s6_var_hot_seg | 4.45 | 9.01 | -0.05 | 0.67 | 8.2 | 2 | 3 |
| crm_spectral4 | 4.23 | 8.95 | 0.0 | 0.0 | 7.98 | 2 | 3 |
| crm_spectral4_cdd_rescaled | 4.3 | 8.95 | 0.0 | 0.0 | 8.25 | 2 | 3 |
| crm_spectral5 | 4.31 | 8.99 | 0.0 | 0.0 | 8.26 | 2 | 3 |
| crm_spectral5_cdd_rescaled | 4.31 | 8.99 | 0.0 | 0.0 | 8.25 | 2 | 3 |
| crm_spectral6 | 4.3 | 9.01 | 0.0 | 0.0 | 8.2 | 2 | 3 |
| crm_spectral6_cdd_rescaled | 4.23 | 9.01 | 0.0 | 0.0 | 7.91 | 2 | 3 |
| crm_spectral6_eb | 4.33 | 9.01 | 0.06 | 0.06 | 8.2 | 2 | 3 |
| crm_spectral6_seg | 4.31 | 9.01 | -0.05 | 0.09 | 8.2 | 2 | 3 |
| crm_spectral6_urban | 4.36 | 9.11 | 0.0 | 0.0 | 8.33 | 2 | 3 |
| current_best | 2.92 | 5.76 | 0.0 | 0.0 | 5.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 2 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| crm_fixed | 0.44 | -2.41 | 0.0 | 0.0 | 4.15 | 2 | 3 |
| crm_fixed_cdd_rescaled | 0.44 | -2.41 | 0.0 | 0.0 | 4.16 | 2 | 3 |
| crm_fixed_cdd_slope | 0.38 | -2.41 | 0.0 | 0.0 | 3.91 | 2 | 3 |
| crm_fixed_k0 | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 2 | 3 |
| crm_fixed_k05 | 0.38 | -2.48 | 0.0 | 0.0 | 4.01 | 2 | 3 |
| crm_fixed_var05 | 0.39 | -2.49 | -0.41 | 0.18 | 4.29 | 2 | 3 |
| crm_s6_eb_urban | 0.51 | -2.29 | 0.07 | 0.06 | 4.18 | 2 | 3 |
| crm_s6_var | 0.06 | -2.21 | -0.31 | -0.18 | 2.92 | 1 | 3 |
| crm_s6_var05 | 0.28 | -2.28 | -0.12 | -0.05 | 3.56 | 2 | 3 |
| crm_s6_var_a01 | 0.16 | -2.04 | -0.57 | 1.18 | 2.07 | 1 | 3 |
| crm_s6_var_a01_cs | 0.16 | -2.59 | -0.54 | 1.24 | 2.53 | 1 | 3 |
| crm_s6_var_a01_cs05 | 0.55 | -2.29 | -0.1 | 0.86 | 3.75 | 2 | 3 |
| crm_s6_var_cs | 0.14 | -2.26 | -0.08 | -0.25 | 3.13 | 1 | 3 |
| crm_s6_var_cs05 | 0.32 | -2.31 | -0.0 | -0.08 | 3.66 | 2 | 3 |
| crm_s6_var_hot | 0.73 | -2.39 | 0.0 | 1.24 | 4.09 | 2 | 3 |
| crm_s6_var_hot05 | 0.64 | -2.39 | 0.0 | 0.86 | 4.09 | 2 | 3 |
| crm_s6_var_hot_eb | 0.76 | -2.39 | 0.07 | 1.3 | 4.09 | 2 | 3 |
| crm_s6_var_hot_eb_urban | 0.8 | -2.29 | 0.07 | 1.22 | 4.18 | 2 | 3 |
| crm_s6_var_hot_seg | 0.77 | -2.39 | 0.05 | 1.31 | 4.09 | 2 | 3 |
| crm_spectral4 | 0.38 | -2.38 | 0.0 | 0.0 | 3.92 | 2 | 3 |
| crm_spectral4_cdd_rescaled | 0.43 | -2.38 | 0.0 | 0.0 | 4.1 | 2 | 3 |
| crm_spectral5 | 0.49 | -2.32 | 0.0 | 0.0 | 4.28 | 2 | 3 |
| crm_spectral5_cdd_rescaled | 0.5 | -2.32 | 0.0 | 0.0 | 4.31 | 2 | 3 |
| crm_spectral6 | 0.42 | -2.39 | 0.0 | 0.0 | 4.09 | 2 | 3 |
| crm_spectral6_cdd_rescaled | 0.37 | -2.39 | 0.0 | 0.0 | 3.87 | 2 | 3 |
| crm_spectral6_eb | 0.45 | -2.39 | 0.07 | 0.06 | 4.09 | 2 | 3 |
| crm_spectral6_seg | 0.46 | -2.39 | 0.05 | 0.09 | 4.09 | 2 | 3 |
| crm_spectral6_urban | 0.47 | -2.29 | 0.0 | 0.0 | 4.18 | 2 | 3 |
| current_best | 0.63 | -1.56 | 0.0 | 0.0 | 4.07 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 2 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| crm_fixed | 7.01 | 17.86 | 0.0 | 0.0 | 10.18 | 2 | 3 |
| crm_fixed_cdd_rescaled | 6.94 | 17.86 | 0.0 | 0.0 | 9.9 | 2 | 3 |
| crm_fixed_cdd_slope | 6.86 | 17.86 | 0.0 | 0.0 | 9.59 | 2 | 3 |
| crm_fixed_k0 | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 2 | 3 |
| crm_fixed_k05 | 6.97 | 17.8 | 0.0 | 0.0 | 10.07 | 2 | 3 |
| crm_fixed_var05 | 7.01 | 17.86 | 0.0 | -0.01 | 10.18 | 2 | 3 |
| crm_s6_eb_urban | 7.23 | 18.15 | 0.07 | 0.05 | 10.66 | 2 | 3 |
| crm_s6_var | 7.14 | 18.06 | -0.0 | 0.01 | 10.49 | 2 | 3 |
| crm_s6_var05 | 7.14 | 18.06 | -0.0 | 0.0 | 10.49 | 2 | 3 |
| crm_s6_var_a01 | 7.2 | 18.36 | -0.11 | 0.04 | 10.51 | 2 | 3 |
| crm_s6_var_a01_cs | 7.2 | 18.42 | -0.09 | -0.03 | 10.51 | 2 | 3 |
| crm_s6_var_a01_cs05 | 7.17 | 18.24 | -0.04 | -0.01 | 10.5 | 2 | 3 |
| crm_s6_var_cs | 7.14 | 18.05 | -0.0 | 0.02 | 10.49 | 2 | 3 |
| crm_s6_var_cs05 | 7.14 | 18.05 | -0.0 | 0.01 | 10.49 | 2 | 3 |
| crm_s6_var_hot | 7.13 | 18.05 | 0.0 | -0.03 | 10.49 | 2 | 3 |
| crm_s6_var_hot05 | 7.13 | 18.05 | 0.0 | -0.01 | 10.49 | 2 | 3 |
| crm_s6_var_hot_eb | 7.16 | 18.05 | 0.07 | 0.03 | 10.49 | 2 | 3 |
| crm_s6_var_hot_eb_urban | 7.22 | 18.15 | 0.07 | 0.02 | 10.66 | 2 | 3 |
| crm_s6_var_hot_seg | 7.12 | 18.05 | -0.15 | 0.08 | 10.49 | 2 | 3 |
| crm_spectral4 | 7.04 | 17.95 | 0.0 | 0.0 | 10.22 | 2 | 3 |
| crm_spectral4_cdd_rescaled | 7.13 | 17.95 | 0.0 | 0.0 | 10.58 | 2 | 3 |
| crm_spectral5 | 7.1 | 17.98 | 0.0 | 0.0 | 10.44 | 2 | 3 |
| crm_spectral5_cdd_rescaled | 7.09 | 17.98 | 0.0 | 0.0 | 10.39 | 2 | 3 |
| crm_spectral6 | 7.14 | 18.05 | 0.0 | 0.0 | 10.49 | 2 | 3 |
| crm_spectral6_cdd_rescaled | 7.06 | 18.05 | 0.0 | 0.0 | 10.19 | 2 | 3 |
| crm_spectral6_eb | 7.17 | 18.05 | 0.07 | 0.05 | 10.49 | 2 | 3 |
| crm_spectral6_seg | 7.12 | 18.05 | -0.15 | 0.1 | 10.49 | 2 | 3 |
| crm_spectral6_urban | 7.2 | 18.15 | 0.0 | 0.0 | 10.66 | 2 | 3 |
| current_best | 4.68 | 11.9 | 0.0 | 0.0 | 6.84 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 2 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| crm_fixed | -1.0 | 3.79 | 9.92 |
| crm_fixed_cdd_rescaled | -0.92 | 3.63 | 9.88 |
| crm_fixed_cdd_slope | -1.02 | 3.65 | 9.73 |
| crm_fixed_k0 | -1.26 | 3.76 | 9.91 |
| crm_fixed_k05 | -1.13 | 3.78 | 9.92 |
| crm_fixed_var05 | -1.01 | 3.73 | 9.95 |
| crm_s6_eb_urban | -0.61 | 3.74 | 10.04 |
| crm_s6_var | -1.33 | 3.95 | 9.81 |
| crm_s6_var05 | -1.03 | 3.88 | 9.87 |
| crm_s6_var_a01 | -1.65 | 4.55 | 9.88 |
| crm_s6_var_a01_cs | -1.56 | 4.5 | 9.84 |
| crm_s6_var_a01_cs05 | -0.97 | 4.24 | 9.92 |
| crm_s6_var_cs | -1.38 | 3.86 | 10.03 |
| crm_s6_var_cs05 | -1.05 | 3.83 | 9.98 |
| crm_s6_var_hot | -0.97 | 3.97 | 10.33 |
| crm_s6_var_hot05 | -0.85 | 3.91 | 10.14 |
| crm_s6_var_hot_eb | -0.94 | 3.99 | 10.37 |
| crm_s6_var_hot_eb_urban | -0.79 | 3.91 | 10.46 |
| crm_s6_var_hot_seg | -0.88 | 3.91 | 10.33 |
| crm_spectral4 | -0.97 | 3.76 | 9.91 |
| crm_spectral4_cdd_rescaled | -0.82 | 3.72 | 10.0 |
| crm_spectral5 | -0.88 | 3.91 | 9.9 |
| crm_spectral5_cdd_rescaled | -0.79 | 3.84 | 9.87 |
| crm_spectral6 | -0.79 | 3.78 | 9.92 |
| crm_spectral6_cdd_rescaled | -0.7 | 3.62 | 9.78 |
| crm_spectral6_eb | -0.76 | 3.8 | 9.96 |
| crm_spectral6_seg | -0.71 | 3.72 | 9.93 |
| crm_spectral6_urban | -0.64 | 3.72 | 10.0 |
| current_best | -0.75 | 3.56 | 5.95 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
