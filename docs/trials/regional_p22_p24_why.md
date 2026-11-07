# Why analysis: regional_p22_p24 (P22 regional trends, P24 pooling groups)

Source: `runs/trials/20261107-170322_regional_p22_p24/results.csv`; per-city numbers recomputed with the backtest API by `scripts/analyze_regional_p22_p24.py`. Folds 1980/1995/2011 (ADR 0004). Raw score = mean of the four skills x 100, without the floor at 0.

Best variant by mean years 4-7 raw score: P22 `p22_region_trend_damped`, P24 `p24_ridge_population_interact`; overall `p24_ridge_population_interact`. All 12 variants are listed; none were added after the first run.

## 1. Score table

| method | all | yrs 1-3 | yrs 4-7 | wins vs current_best (all, 1-3, 4-7) | wins vs hybrid_ridge_all_cdd (all, 1-3, 4-7) |
|---|---|---|---|---|---|
| p24_ridge_population_interact | 3.61 | 0.95 | 5.55 | 3/3, 2/3, 3/3 | 2/3, 2/3, 2/3 |
| hybrid_ridge_all_cdd | 3.6 | 0.94 | 5.54 | 3/3, 2/3, 3/3 | 0/3, 0/3, 0/3 |
| p24_ridge_all_groups_additive | 3.59 | 0.95 | 5.52 | 3/3, 2/3, 3/3 | 0/3, 2/3, 0/3 |
| p24_ridge_landcover_interact | 3.52 | 0.89 | 5.43 | 3/3, 2/3, 3/3 | 0/3, 0/3, 0/3 |
| p22_region_trend_damped | 3.08 | 0.19 | 5.24 | 2/3, 0/3, 2/3 | 1/3, 1/3, 2/3 |
| p24_ridge_region_interact | 3.56 | 1.18 | 5.23 | 3/3, 2/3, 2/3 | 2/3, 3/3, 2/3 |
| p24_ridge_region_separate | 3.54 | 1.19 | 5.2 | 3/3, 2/3, 2/3 | 2/3, 3/3, 2/3 |
| p24_ridge_elevation_interact | 3.43 | 0.98 | 5.18 | 3/3, 2/3, 3/3 | 1/3, 2/3, 0/3 |
| p22_eb_region_flat | 2.63 | -0.24 | 4.79 | 1/3, 1/3, 2/3 | 1/3, 1/3, 1/3 |
| p22_eb_region_damped | 2.73 | 0.05 | 4.73 | 1/3, 0/3, 2/3 | 1/3, 1/3, 1/3 |
| current_best | 2.92 | 0.63 | 4.68 | 0/3, 0/3, 0/3 | 0/3, 1/3, 0/3 |
| p22_eb_elevation_damped | 2.68 | 0.03 | 4.65 | 1/3, 0/3, 2/3 | 1/3, 1/3, 1/3 |
| p22_eb_region_long_damped | 2.68 | 0.42 | 4.34 | 1/3, 1/3, 1/3 | 1/3, 1/3, 1/3 |
| p22_eb_region | 1.75 | -0.92 | 3.66 | 1/3, 0/3, 1/3 | 1/3, 1/3, 1/3 |
| ten_year_mean | 1.34 | -0.62 | 2.78 | 0/3, 0/3, 0/3 | 0/3, 0/3, 0/3 |

## 2. Per-metric skill (%) and difference to the references

Mean over the three origins. Metrics: temp = annual_avg_temp, precip = total_precip_in, hottest = hottest_day_temp.

| window | method | temp | precip | hottest | cdd | Δ vs current_best | Δ vs hybrid_ridge_all_cdd |
|---|---|---|---|---|---|---|---|
| all | current_best | 5.76 | 0.0 | 0.0 | 5.91 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 | temp +0.00, precip +0.00, hottest +0.00, cdd -2.74 |
| all | ten_year_mean | 5.76 | -3.94 | -2.39 | 5.91 | temp +0.00, precip -3.94, hottest -2.39, cdd +0.00 | temp +0.00, precip -3.94, hottest -2.39, cdd -2.74 |
| all | hybrid_ridge_all_cdd | 5.76 | 0.0 | 0.0 | 8.65 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.74 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 |
| all | p22_eb_region | 2.95 | 0.0 | 0.0 | 4.04 | temp -2.81, precip +0.00, hottest +0.00, cdd -1.87 | temp -2.81, precip +0.00, hottest +0.00, cdd -4.61 |
| all | p22_eb_region_damped | 5.18 | 0.0 | 0.0 | 5.75 | temp -0.58, precip +0.00, hottest +0.00, cdd -0.16 | temp -0.58, precip +0.00, hottest +0.00, cdd -2.90 |
| all | p22_eb_region_flat | 4.93 | 0.0 | 0.0 | 5.57 | temp -0.83, precip +0.00, hottest +0.00, cdd -0.34 | temp -0.83, precip +0.00, hottest +0.00, cdd -3.08 |
| all | p22_region_trend_damped | 5.88 | 0.0 | 0.0 | 6.42 | temp +0.12, precip +0.00, hottest +0.00, cdd +0.51 | temp +0.12, precip +0.00, hottest +0.00, cdd -2.23 |
| all | p22_eb_elevation_damped | 5.19 | 0.0 | 0.0 | 5.52 | temp -0.58, precip +0.00, hottest +0.00, cdd -0.39 | temp -0.58, precip +0.00, hottest +0.00, cdd -3.13 |
| all | p22_eb_region_long_damped | 4.78 | 0.0 | 0.0 | 5.93 | temp -0.98, precip +0.00, hottest +0.00, cdd +0.02 | temp -0.98, precip +0.00, hottest +0.00, cdd -2.72 |
| all | p24_ridge_region_interact | 5.76 | 0.0 | 0.0 | 8.47 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.56 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.19 |
| all | p24_ridge_elevation_interact | 5.76 | 0.0 | 0.0 | 7.95 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.04 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.70 |
| all | p24_ridge_population_interact | 5.76 | 0.0 | 0.0 | 8.69 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.78 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.03 |
| all | p24_ridge_landcover_interact | 5.76 | 0.0 | 0.0 | 8.3 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.39 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.35 |
| all | p24_ridge_region_separate | 5.76 | 0.0 | 0.0 | 8.4 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.49 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.25 |
| all | p24_ridge_all_groups_additive | 5.76 | 0.0 | 0.0 | 8.6 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.69 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.05 |
| years_1_3 | current_best | -1.56 | 0.0 | 0.0 | 4.07 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 | temp +0.00, precip +0.00, hottest +0.00, cdd -1.27 |
| years_1_3 | ten_year_mean | -1.56 | -3.47 | -1.5 | 4.07 | temp +0.00, precip -3.47, hottest -1.50, cdd +0.00 | temp +0.00, precip -3.47, hottest -1.50, cdd -1.27 |
| years_1_3 | hybrid_ridge_all_cdd | -1.56 | 0.0 | 0.0 | 5.34 | temp +0.00, precip +0.00, hottest +0.00, cdd +1.27 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 |
| years_1_3 | p22_eb_region | -5.34 | 0.0 | 0.0 | 1.66 | temp -3.77, precip +0.00, hottest +0.00, cdd -2.41 | temp -3.77, precip +0.00, hottest +0.00, cdd -3.68 |
| years_1_3 | p22_eb_region_damped | -3.14 | 0.0 | 0.0 | 3.35 | temp -1.57, precip +0.00, hottest +0.00, cdd -0.72 | temp -1.57, precip +0.00, hottest +0.00, cdd -1.99 |
| years_1_3 | p22_eb_region_flat | -3.96 | 0.0 | 0.0 | 3.0 | temp -2.39, precip +0.00, hottest +0.00, cdd -1.08 | temp -2.39, precip +0.00, hottest +0.00, cdd -2.34 |
| years_1_3 | p22_region_trend_damped | -2.79 | 0.0 | 0.0 | 3.54 | temp -1.22, precip +0.00, hottest +0.00, cdd -0.53 | temp -1.22, precip +0.00, hottest +0.00, cdd -1.80 |
| years_1_3 | p22_eb_elevation_damped | -3.18 | 0.0 | 0.0 | 3.3 | temp -1.61, precip +0.00, hottest +0.00, cdd -0.78 | temp -1.61, precip +0.00, hottest +0.00, cdd -2.05 |
| years_1_3 | p22_eb_region_long_damped | -2.52 | 0.0 | 0.0 | 4.19 | temp -0.95, precip +0.00, hottest +0.00, cdd +0.11 | temp -0.95, precip +0.00, hottest +0.00, cdd -1.15 |
| years_1_3 | p24_ridge_region_interact | -1.56 | 0.0 | 0.0 | 6.28 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.21 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.94 |
| years_1_3 | p24_ridge_elevation_interact | -1.56 | 0.0 | 0.0 | 5.47 | temp +0.00, precip +0.00, hottest +0.00, cdd +1.39 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.12 |
| years_1_3 | p24_ridge_population_interact | -1.56 | 0.0 | 0.0 | 5.38 | temp +0.00, precip +0.00, hottest +0.00, cdd +1.31 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.04 |
| years_1_3 | p24_ridge_landcover_interact | -1.56 | 0.0 | 0.0 | 5.14 | temp +0.00, precip +0.00, hottest +0.00, cdd +1.07 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.20 |
| years_1_3 | p24_ridge_region_separate | -1.56 | 0.0 | 0.0 | 6.31 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.24 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.97 |
| years_1_3 | p24_ridge_all_groups_additive | -1.56 | 0.0 | 0.0 | 5.35 | temp +0.00, precip +0.00, hottest +0.00, cdd +1.28 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.01 |
| years_4_7 | current_best | 11.9 | 0.0 | 0.0 | 6.84 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 | temp +0.00, precip +0.00, hottest +0.00, cdd -3.43 |
| years_4_7 | ten_year_mean | 11.9 | -4.44 | -3.16 | 6.84 | temp +0.00, precip -4.44, hottest -3.16, cdd +0.00 | temp +0.00, precip -4.44, hottest -3.16, cdd -3.43 |
| years_4_7 | hybrid_ridge_all_cdd | 11.9 | 0.0 | 0.0 | 10.27 | temp +0.00, precip +0.00, hottest +0.00, cdd +3.43 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.00 |
| years_4_7 | p22_eb_region | 9.93 | 0.0 | 0.0 | 4.71 | temp -1.96, precip +0.00, hottest +0.00, cdd -2.13 | temp -1.96, precip +0.00, hottest +0.00, cdd -5.56 |
| years_4_7 | p22_eb_region_damped | 12.15 | 0.0 | 0.0 | 6.77 | temp +0.26, precip +0.00, hottest +0.00, cdd -0.06 | temp +0.26, precip +0.00, hottest +0.00, cdd -3.50 |
| years_4_7 | p22_eb_region_flat | 12.37 | 0.0 | 0.0 | 6.79 | temp +0.47, precip +0.00, hottest +0.00, cdd -0.04 | temp +0.47, precip +0.00, hottest +0.00, cdd -3.48 |
| years_4_7 | p22_region_trend_damped | 13.13 | 0.0 | 0.0 | 7.82 | temp +1.23, precip +0.00, hottest +0.00, cdd +0.98 | temp +1.23, precip +0.00, hottest +0.00, cdd -2.45 |
| years_4_7 | p22_eb_elevation_damped | 12.2 | 0.0 | 0.0 | 6.42 | temp +0.30, precip +0.00, hottest +0.00, cdd -0.42 | temp +0.30, precip +0.00, hottest +0.00, cdd -3.85 |
| years_4_7 | p22_eb_region_long_damped | 10.88 | 0.0 | 0.0 | 6.47 | temp -1.02, precip +0.00, hottest +0.00, cdd -0.37 | temp -1.02, precip +0.00, hottest +0.00, cdd -3.80 |
| years_4_7 | p24_ridge_region_interact | 11.9 | 0.0 | 0.0 | 9.03 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.19 | temp +0.00, precip +0.00, hottest +0.00, cdd -1.24 |
| years_4_7 | p24_ridge_elevation_interact | 11.9 | 0.0 | 0.0 | 8.83 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.00 | temp +0.00, precip +0.00, hottest +0.00, cdd -1.44 |
| years_4_7 | p24_ridge_population_interact | 11.9 | 0.0 | 0.0 | 10.3 | temp +0.00, precip +0.00, hottest +0.00, cdd +3.46 | temp +0.00, precip +0.00, hottest +0.00, cdd +0.03 |
| years_4_7 | p24_ridge_landcover_interact | 11.9 | 0.0 | 0.0 | 9.81 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.98 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.46 |
| years_4_7 | p24_ridge_region_separate | 11.9 | 0.0 | 0.0 | 8.9 | temp +0.00, precip +0.00, hottest +0.00, cdd +2.06 | temp +0.00, precip +0.00, hottest +0.00, cdd -1.37 |
| years_4_7 | p24_ridge_all_groups_additive | 11.9 | 0.0 | 0.0 | 10.18 | temp +0.00, precip +0.00, hottest +0.00, cdd +3.34 | temp +0.00, precip +0.00, hottest +0.00, cdd -0.09 |

## 3. Per-origin raw score

| window | method | 1980 | 1995 | 2011 |
|---|---|---|---|---|
| all | current_best | -0.75 | 3.56 | 5.95 |
| all | hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 |
| all | p22_region_trend_damped | -2.21 | 3.58 | 7.86 |
| all | p24_ridge_population_interact | 0.17 | 4.21 | 6.45 |
| all | ten_year_mean | -2.53 | 1.39 | 5.16 |
| years_1_3 | current_best | 0.74 | -1.68 | 2.82 |
| years_1_3 | hybrid_ridge_all_cdd | 1.69 | -0.66 | 1.8 |
| years_1_3 | p22_region_trend_damped | 0.55 | -2.56 | 2.59 |
| years_1_3 | p24_ridge_population_interact | 1.63 | -0.57 | 1.81 |
| years_1_3 | ten_year_mean | 0.5 | -4.12 | 1.77 |
| years_4_7 | current_best | -1.93 | 8.02 | 7.95 |
| years_4_7 | hybrid_ridge_all_cdd | -0.9 | 8.27 | 9.26 |
| years_4_7 | p22_region_trend_damped | -4.33 | 8.82 | 11.22 |
| years_4_7 | p24_ridge_population_interact | -0.98 | 8.34 | 9.28 |
| years_4_7 | ten_year_mean | -5.06 | 6.04 | 7.37 |

## 4. Per-city and per-region breakdown

Contribution to the raw-score difference (raw-score points, mean over origins). Positive = the variant is better than the comparison for that city. Warming rate is the 1982-2011 OLS temperature trend (data before the last cutoff only); station changes = `Station Changes` by 2018.

### `p24_ridge_population_interact` vs `hybrid_ridge_all_cdd`, years 4-7

Top 10 cities (gain):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00053920 | Russellville | South Central | 0.017 | 0.0 | 0.0 | 0.0 | 0.017 |
| USW00023183 | Phoenix | Southwest | 0.008 | 0.0 | 0.0 | 0.0 | 0.008 |
| USW00013876 | Birmingham | Southeast | 0.007 | 0.0 | 0.0 | 0.0 | 0.007 |
| USW00023185 | Reno | Northwest | 0.007 | 0.0 | 0.0 | 0.0 | 0.007 |
| USW00013963 | LittleRock | South Central | 0.006 | 0.0 | 0.0 | 0.0 | 0.006 |
| USW00012835 | FortMyers | Southeast | 0.006 | 0.0 | 0.0 | 0.0 | 0.006 |
| USW00012816 | Gainesville | Southeast | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |
| USW00013970 | BatonRouge | South Central | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |
| USW00013897 | Nashville | Southeast | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |
| USW00013893 | Memphis | South Central | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |

Bottom 10 cities (loss):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00013882 | Chattanooga | Southeast | -0.012 | 0.0 | 0.0 | 0.0 | -0.012 |
| USW00003940 | Jackson | South Central | -0.007 | 0.0 | 0.0 | 0.0 | -0.007 |
| USW00013873 | Athens | Southeast | -0.007 | 0.0 | 0.0 | 0.0 | -0.007 |
| USW00023009 | Roswell | Southwest | -0.007 | 0.0 | 0.0 | 0.0 | -0.007 |
| USW00024257 | Redding | Northwest | -0.006 | 0.0 | 0.0 | 0.0 | -0.006 |
| USW00013886 | GreenvilleSpartanburg | Southeast | -0.006 | 0.0 | 0.0 | 0.0 | -0.006 |
| USC00166584 | Natchitoches | South Central | -0.005 | 0.0 | 0.0 | 0.0 | -0.005 |
| USW00013995 | SpringfieldMO | North Central | -0.005 | 0.0 | 0.0 | 0.0 | -0.005 |
| USW00013883 | ColumbiaSC | Southeast | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USW00014711 | MiddletownHarrisburg | Northeast | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |

Region totals (sum of city contributions, raw-score points):

| region | total | temp | precip | hottest | cdd | cities |
|---|---|---|---|---|---|---|
| North Central | -0.025 | 0.0 | 0.0 | 0.0 | -0.025 | 52 |
| Northeast | -0.005 | 0.0 | 0.0 | 0.0 | -0.005 | 50 |
| Northwest | 0.02 | 0.0 | 0.0 | 0.0 | 0.02 | 34 |
| South Central | 0.008 | 0.0 | 0.0 | 0.0 | 0.008 | 32 |
| Southeast | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 | 28 |
| Southwest | 0.011 | 0.0 | 0.0 | 0.0 | 0.011 | 14 |

Spearman correlation of the per-city total with: warming_F_per_decade_1982_2011 -0.01, elevation_m -0.04, pop_2010 +0.35, station_changes +0.08 (n = 210; |rho| > 0.14 is about p < 0.05).

By NLCD 2016 land-cover group:

| land_cover | sum | mean | size |
|---|---|---|---|
| developed_high | 0.043 | 0.001 | 78 |
| developed_low | -0.016 | -0.0 | 83 |
| undeveloped | -0.021 | -0.0 | 49 |

### `p24_ridge_population_interact` vs `hybrid_ridge_all_cdd`, all years

Top 10 cities (gain):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00053920 | Russellville | South Central | 0.009 | 0.0 | 0.0 | 0.0 | 0.009 |
| USW00023185 | Reno | Northwest | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |
| USW00023183 | Phoenix | Southwest | 0.005 | 0.0 | 0.0 | 0.0 | 0.005 |
| USW00012835 | FortMyers | Southeast | 0.004 | 0.0 | 0.0 | 0.0 | 0.004 |
| USW00013876 | Birmingham | Southeast | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |
| USW00013970 | BatonRouge | South Central | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |
| USW00023155 | Bakersfield | Southwest | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |
| USW00013963 | LittleRock | South Central | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |
| USW00012842 | Tampa | Southeast | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |
| USC00356749 | Portland | Northwest | 0.003 | 0.0 | 0.0 | 0.0 | 0.003 |

Bottom 10 cities (loss):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00013882 | Chattanooga | Southeast | -0.006 | 0.0 | 0.0 | 0.0 | -0.006 |
| USW00024257 | Redding | Northwest | -0.005 | 0.0 | 0.0 | 0.0 | -0.005 |
| USW00013873 | Athens | Southeast | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USC00166584 | Natchitoches | South Central | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USW00013995 | SpringfieldMO | North Central | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USW00003940 | Jackson | South Central | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USW00023009 | Roswell | Southwest | -0.004 | 0.0 | 0.0 | 0.0 | -0.004 |
| USW00013883 | ColumbiaSC | Southeast | -0.003 | 0.0 | 0.0 | 0.0 | -0.003 |
| USW00013967 | Oklahoma | South Central | -0.003 | 0.0 | 0.0 | 0.0 | -0.003 |
| USW00094040 | McCook | North Central | -0.003 | 0.0 | 0.0 | 0.0 | -0.003 |

Region totals (sum of city contributions, raw-score points):

| region | total | temp | precip | hottest | cdd | cities |
|---|---|---|---|---|---|---|
| North Central | 0.002 | 0.0 | 0.0 | 0.0 | 0.002 | 52 |
| Northeast | -0.006 | 0.0 | 0.0 | 0.0 | -0.006 | 50 |
| Northwest | 0.013 | 0.0 | 0.0 | 0.0 | 0.013 | 34 |
| South Central | 0.001 | 0.0 | 0.0 | 0.0 | 0.001 | 32 |
| Southeast | -0.008 | 0.0 | 0.0 | 0.0 | -0.008 | 28 |
| Southwest | 0.007 | 0.0 | 0.0 | 0.0 | 0.007 | 14 |

Spearman correlation of the per-city total with: warming_F_per_decade_1982_2011 -0.02, elevation_m +0.06, pop_2010 +0.04, station_changes -0.06 (n = 210; |rho| > 0.14 is about p < 0.05).

By NLCD 2016 land-cover group:

| land_cover | sum | mean | size |
|---|---|---|---|
| developed_high | 0.022 | 0.0 | 78 |
| developed_low | -0.005 | -0.0 | 83 |
| undeveloped | -0.008 | -0.0 | 49 |

### `p22_region_trend_damped` vs `hybrid_ridge_all_cdd`, years 4-7

Top 10 cities (gain):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00014710 | Manchester | Northeast | 0.048 | 0.035 | 0.0 | 0.0 | 0.012 |
| USW00023183 | Phoenix | Southwest | 0.038 | 0.009 | 0.0 | 0.0 | 0.029 |
| USW00023044 | ElPaso | Southwest | 0.036 | 0.015 | 0.0 | 0.0 | 0.021 |
| USW00013882 | Chattanooga | Southeast | 0.034 | 0.009 | 0.0 | 0.0 | 0.026 |
| USW00012923 | Galveston | South Central | 0.031 | 0.008 | 0.0 | 0.0 | 0.024 |
| USC00042863 | Escondido | Southwest | 0.03 | 0.011 | 0.0 | 0.0 | 0.019 |
| USW00003947 | KansasCity | North Central | 0.028 | 0.008 | 0.0 | 0.0 | 0.02 |
| USW00023185 | Reno | Northwest | 0.027 | 0.008 | 0.0 | 0.0 | 0.019 |
| USW00003927 | DallasFortWorth | South Central | 0.027 | 0.003 | 0.0 | 0.0 | 0.024 |
| USC00380072 | Aiken | Southeast | 0.023 | 0.007 | 0.0 | 0.0 | 0.016 |

Bottom 10 cities (loss):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00013881 | Charlotte | Southeast | -0.079 | -0.014 | 0.0 | 0.0 | -0.065 |
| USW00013874 | Atlanta | Southeast | -0.073 | -0.014 | 0.0 | 0.0 | -0.059 |
| USW00012960 | Houston | South Central | -0.062 | -0.006 | 0.0 | 0.0 | -0.057 |
| USW00003145 | Yuma | Southwest | -0.061 | -0.005 | 0.0 | 0.0 | -0.055 |
| USW00053920 | Russellville | South Central | -0.052 | -0.016 | 0.0 | 0.0 | -0.036 |
| USW00012835 | FortMyers | Southeast | -0.05 | -0.013 | 0.0 | 0.0 | -0.036 |
| USW00003820 | Augusta | Southeast | -0.046 | -0.014 | 0.0 | 0.0 | -0.032 |
| USW00013957 | Shreveport | South Central | -0.044 | -0.003 | 0.0 | 0.0 | -0.041 |
| USW00003859 | Bluefield | Northeast | -0.035 | -0.015 | 0.0 | 0.0 | -0.019 |
| USW00012921 | SanAntonio | South Central | -0.034 | -0.004 | 0.0 | 0.0 | -0.03 |

Region totals (sum of city contributions, raw-score points):

| region | total | temp | precip | hottest | cdd | cities |
|---|---|---|---|---|---|---|
| North Central | 0.182 | 0.217 | 0.0 | 0.0 | -0.034 | 52 |
| Northeast | -0.11 | 0.065 | 0.0 | 0.0 | -0.175 | 50 |
| Northwest | 0.104 | 0.026 | 0.0 | 0.0 | 0.078 | 34 |
| South Central | -0.173 | 0.014 | 0.0 | 0.0 | -0.187 | 32 |
| Southeast | -0.388 | -0.08 | 0.0 | 0.0 | -0.307 | 28 |
| Southwest | 0.08 | 0.066 | 0.0 | 0.0 | 0.013 | 14 |

Spearman correlation of the per-city total with: warming_F_per_decade_1982_2011 +0.30, elevation_m +0.19, pop_2010 -0.00, station_changes -0.10 (n = 210; |rho| > 0.14 is about p < 0.05).

By NLCD 2016 land-cover group:

| land_cover | sum | mean | size |
|---|---|---|---|
| developed_high | -0.221 | -0.003 | 78 |
| developed_low | -0.13 | -0.002 | 83 |
| undeveloped | 0.046 | 0.001 | 49 |

### `p22_region_trend_damped` vs `hybrid_ridge_all_cdd`, all years

Top 10 cities (gain):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USC00042863 | Escondido | Southwest | 0.032 | 0.011 | 0.0 | 0.0 | 0.021 |
| USW00003927 | DallasFortWorth | South Central | 0.031 | 0.003 | 0.0 | 0.0 | 0.027 |
| USW00014710 | Manchester | Northeast | 0.026 | 0.018 | 0.0 | 0.0 | 0.008 |
| USW00023185 | Reno | Northwest | 0.024 | 0.004 | 0.0 | 0.0 | 0.02 |
| USW00023183 | Phoenix | Southwest | 0.022 | 0.004 | 0.0 | 0.0 | 0.018 |
| USW00003953 | Jonesboro | South Central | 0.018 | 0.006 | 0.0 | 0.0 | 0.012 |
| USW00023179 | Needles | Southwest | 0.018 | 0.014 | 0.0 | 0.0 | 0.004 |
| USW00024011 | Bismarck | North Central | 0.016 | 0.003 | 0.0 | 0.0 | 0.013 |
| USW00003963 | Jefferson | North Central | 0.016 | 0.005 | 0.0 | 0.0 | 0.011 |
| USW00012923 | Galveston | South Central | 0.016 | 0.002 | 0.0 | 0.0 | 0.014 |

Bottom 10 cities (loss):

| city_id | name | region | total | temp | precip | hottest | cdd |
|---|---|---|---|---|---|---|---|
| USW00013881 | Charlotte | Southeast | -0.053 | -0.008 | 0.0 | 0.0 | -0.045 |
| USW00013874 | Atlanta | Southeast | -0.045 | -0.01 | 0.0 | 0.0 | -0.035 |
| USW00012960 | Houston | South Central | -0.041 | -0.005 | 0.0 | 0.0 | -0.036 |
| USW00003145 | Yuma | Southwest | -0.035 | 0.0 | 0.0 | 0.0 | -0.036 |
| USW00003820 | Augusta | Southeast | -0.032 | -0.008 | 0.0 | 0.0 | -0.024 |
| USW00053920 | Russellville | South Central | -0.031 | -0.01 | 0.0 | 0.0 | -0.021 |
| USW00013962 | Abilene | South Central | -0.03 | 0.003 | 0.0 | 0.0 | -0.033 |
| USW00012835 | FortMyers | Southeast | -0.029 | -0.007 | 0.0 | 0.0 | -0.022 |
| USW00013873 | Athens | Southeast | -0.029 | -0.007 | 0.0 | 0.0 | -0.022 |
| USW00013733 | Lynchburg | Northeast | -0.029 | -0.01 | 0.0 | 0.0 | -0.018 |

Region totals (sum of city contributions, raw-score points):

| region | total | temp | precip | hottest | cdd | cities |
|---|---|---|---|---|---|---|
| North Central | 0.009 | 0.047 | 0.0 | 0.0 | -0.038 | 52 |
| Northeast | -0.214 | -0.037 | 0.0 | 0.0 | -0.177 | 50 |
| Northwest | 0.126 | 0.02 | 0.0 | 0.0 | 0.106 | 34 |
| South Central | -0.161 | -0.008 | 0.0 | 0.0 | -0.154 | 32 |
| Southeast | -0.324 | -0.048 | 0.0 | 0.0 | -0.276 | 28 |
| Southwest | 0.036 | 0.056 | 0.0 | 0.0 | -0.02 | 14 |

Spearman correlation of the per-city total with: warming_F_per_decade_1982_2011 +0.19, elevation_m +0.15, pop_2010 -0.07, station_changes -0.13 (n = 210; |rho| > 0.14 is about p < 0.05).

By NLCD 2016 land-cover group:

| land_cover | sum | mean | size |
|---|---|---|---|
| developed_high | -0.268 | -0.003 | 78 |
| developed_low | -0.239 | -0.003 | 83 |
| undeveloped | -0.02 | -0.0 | 49 |

## 5. Mechanism

**Mechanism (hypothesis).** P22: the 10-year mean lags the cutoff by about 5.5 years and the
forecast years by 5.5 + lead years, so on a warming series it is biased low; a city trend shrunk
toward its region's trend is far less noisy than a raw city trend, so adding it removes part of
that lag bias without the variance that sank raw extrapolation in round 1. P24: pooling groups
give the pooled ridge a group-specific relation between recent anomalies and the future CDD
anomaly, which helps only if the groups really differ in that relation; with about 12k rows per
lead the ridge already pools well, so we expect little from it.

**Check.** Partly supported for P22, supported for P24.

- Lag bias is real: `current_best` under-forecasts temperature in years 4-7 at every origin
  (mean actual - forecast +0.71 / +0.31 / +1.40 F at 1980 / 1995 / 2011; CDD +41 / +26 / +160).
- Less noise helps, as predicted: with damping 0.5, the fully pooled regional trend
  (`p22_region_trend_damped`, 5.24 years 4-7) beats the empirical-Bayes city trend
  (`p22_eb_region_damped`, 4.73) and the elevation-band version (4.65); undamped EB loses badly
  (3.66), and so does a 50-year window (4.34).
- But the sign of a 30-year trend is not stable across regimes. At the 1980 cutoff the 1951-1980
  regional temperature trends were negative in 4 of 6 regions (North Central -0.35, Northeast
  -0.44, South Central -0.52, Southeast -0.27 F/decade), so the trend pushed forecasts down while
  the truth went up: `p22_region_trend_damped` scores -4.33 in years 4-7 at 1980 vs -1.93 for
  `current_best`. At 1995 and 2011 the trends were positive and it wins (8.82 vs 8.02, 11.22 vs
  7.95), though at 2011 the damped trend adds only about 0.17 F against a 1.40 F bias.
- Per city (years 4-7, vs `hybrid_ridge_all_cdd`) the P22 gain rises with the city's 1982-2011
  warming rate (Spearman +0.30) and the Southeast, the slowest-warming region, loses most
  (-0.39 points, mostly CDD): the trend pays where warming persisted.
- P24: pooling groups change CDD skill by at most +0.03 points in years 4-7 (population bands),
  far below noise. More flexible group models (region interactions, separate region models) gain
  in years 1-3 (+0.94 CDD skill) and lose in years 4-7 (-1.24), the pattern of fitting short-lead
  structure that does not carry to longer leads. The population-band gain lines up with city size
  (Spearman +0.35 with 2010 population) but totals only about +0.01 raw-score points.


## 6. Caveats

- 12 variants (6 P22, 6 P24), fixed in the config before the first run; no variant was added or
  changed after seeing results. The best of 12 on three origins carries selection optimism.
- All forecasters are deterministic (closed-form trends, ridge), so there are no seed replicas.
- Three origins only: differences under about 1 raw-score point are not distinguishable from noise.
- P22 is a hierarchical Bayesian space-time model on gridded data with a latent Gaussian random
  field for the trend; we replace it with method-of-moments empirical-Bayes shrinkage within
  discrete groups (no spatial field, no MCMC/INLA), on 210 station series, and use it for
  forecasting rather than trend significance.
- P24 classifies USHCN stations as urban/rural to measure the urban share of warming; we use
  population, land cover and elevation only as pooling groups. Its full text was not machine-read
  here (PDF text not extractable without a PDF library); we rely on the Crossref abstract.
- The 2010 Census and NLCD 2016 postdate the 1980 and 1995 cutoffs. They are static attributes,
  not weather, but a city's 2010 size partly reflects growth after those cutoffs (mild look-ahead
  in the group assignment for early folds only).
- NLCD land cover is read at 5 pixels per station (centre and +-~500 m), not a full buffer, and
  GHCN elevation comes from the current station inventory (station elevation is static metadata;
  an archived pre-2019 copy was not used).
