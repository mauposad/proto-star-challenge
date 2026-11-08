# Why analysis: paper_cdd_forcing_p06_p21

Run dir `runs/trials/20261107-171827_paper_cdd_forcing_p06_p21`. Written by `scripts/analyze_cdd_forcing_p06_p21.py`. Mean raw score over the three ADR 0004 origins (1980, 1995, 2011); `years_4_7` matches the Final Score. Best new variant by mean years 4-7 raw score: **`hybrid_ridge_shift30_avg`** (best of 11 new variants, so its edge carries selection optimism).

## Score table

| method | mean all | mean years_1_3 | mean years_4_7 | wins vs current_best all | wins vs current_best years_1_3 | wins vs current_best years_4_7 | wins vs hybrid_ridge_all_cdd all | wins vs hybrid_ridge_all_cdd years_1_3 | wins vs hybrid_ridge_all_cdd years_4_7 |
|---|---|---|---|---|---|---|---|---|---|
| current_best | 2.92 | 0.63 | 4.68 | 0/3 | 0/3 | 0/3 | 0/3 | 1/3 | 0/3 |
| ten_year_mean | 1.34 | -0.62 | 2.78 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| hybrid_ridge_all_cdd | 3.6 | 0.94 | 5.54 | 3/3 | 2/3 | 3/3 | 0/3 | 0/3 | 0/3 |
| shift30_recent | 2.63 | 0.05 | 4.65 | 1/3 | 1/3 | 2/3 | 0/3 | 1/3 | 1/3 |
| shift30_recent_linear | 2.63 | 0.08 | 4.63 | 1/3 | 1/3 | 2/3 | 0/3 | 1/3 | 1/3 |
| shift10_trend | 2.62 | 0.33 | 4.29 | 1/3 | 0/3 | 1/3 | 1/3 | 1/3 | 0/3 |
| shift10_trend_linear | 2.62 | 0.33 | 4.29 | 1/3 | 0/3 | 1/3 | 1/3 | 1/3 | 0/3 |
| shift10_co2 | 2.61 | 0.55 | 3.96 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 | 1/3 |
| eia_trend30 | -0.33 | -1.84 | 0.65 | 1/3 | 0/3 | 1/3 | 0/3 | 1/3 | 0/3 |
| eia_cdd_on_temp_recent | 2.82 | 0.47 | 4.68 | 2/3 | 1/3 | 2/3 | 0/3 | 1/3 | 1/3 |
| eia_cdd_on_temp_trend | 2.65 | 0.34 | 4.4 | 0/3 | 1/3 | 1/3 | 0/3 | 1/3 | 1/3 |
| p21_co2_ar1 | 1.95 | -0.02 | 3.25 | 1/3 | 1/3 | 1/3 | 1/3 | 0/3 | 1/3 |
| p21_regional_ar1 | 1.38 | -0.48 | 2.78 | 1/3 | 0/3 | 2/3 | 1/3 | 1/3 | 2/3 |
| hybrid_ridge_shift30_avg | 3.37 | 0.76 | 5.36 | 2/3 | 1/3 | 3/3 | 1/3 | 1/3 | 2/3 |

## Per-metric skill (%), all

Mean skill over origins; the `vs` columns are the difference in skill points.

| method | annual_avg_temp | total_precip_in | hottest_day_temp | cdd | cdd vs current_best | temp vs current_best | cdd vs hybrid_ridge_all_cdd | temp vs hybrid_ridge_all_cdd |
|---|---|---|---|---|---|---|---|---|
| current_best | 5.76 | 0.0 | 0.0 | 5.91 | 0.0 | 0.0 | -2.74 | 0.0 |
| ten_year_mean | 5.76 | -3.94 | -2.39 | 5.91 | 0.0 | 0.0 | -2.74 | 0.0 |
| hybrid_ridge_all_cdd | 5.76 | 0.0 | 0.0 | 8.65 | 2.74 | 0.0 | 0.0 | 0.0 |
| shift30_recent | 5.76 | 0.0 | 0.0 | 4.74 | -1.17 | 0.0 | -3.91 | 0.0 |
| shift30_recent_linear | 5.76 | 0.0 | 0.0 | 4.75 | -1.16 | 0.0 | -3.9 | 0.0 |
| shift10_trend | 5.76 | 0.0 | 0.0 | 4.73 | -1.18 | 0.0 | -3.92 | 0.0 |
| shift10_trend_linear | 5.76 | 0.0 | 0.0 | 4.73 | -1.18 | 0.0 | -3.92 | 0.0 |
| shift10_co2 | 5.76 | 0.0 | 0.0 | 4.67 | -1.24 | 0.0 | -3.98 | 0.0 |
| eia_trend30 | 5.76 | 0.0 | 0.0 | -7.08 | -12.99 | 0.0 | -15.73 | 0.0 |
| eia_cdd_on_temp_recent | 5.76 | 0.0 | 0.0 | 5.5 | -0.41 | 0.0 | -3.15 | 0.0 |
| eia_cdd_on_temp_trend | 5.76 | 0.0 | 0.0 | 4.82 | -1.09 | 0.0 | -3.83 | 0.0 |
| p21_co2_ar1 | 3.94 | 0.0 | 0.0 | 3.86 | -2.05 | -1.83 | -4.79 | -1.83 |
| p21_regional_ar1 | 1.88 | 0.0 | 0.0 | 3.62 | -2.29 | -3.88 | -5.03 | -3.88 |
| hybrid_ridge_shift30_avg | 5.76 | 0.0 | 0.0 | 7.72 | 1.81 | 0.0 | -0.93 | 0.0 |

## Per-metric skill (%), years_1_3

Mean skill over origins; the `vs` columns are the difference in skill points.

| method | annual_avg_temp | total_precip_in | hottest_day_temp | cdd | cdd vs current_best | temp vs current_best | cdd vs hybrid_ridge_all_cdd | temp vs hybrid_ridge_all_cdd |
|---|---|---|---|---|---|---|---|---|
| current_best | -1.56 | 0.0 | 0.0 | 4.07 | 0.0 | 0.0 | -1.27 | 0.0 |
| ten_year_mean | -1.56 | -3.47 | -1.5 | 4.07 | 0.0 | 0.0 | -1.27 | 0.0 |
| hybrid_ridge_all_cdd | -1.56 | 0.0 | 0.0 | 5.34 | 1.27 | 0.0 | 0.0 | 0.0 |
| shift30_recent | -1.56 | 0.0 | 0.0 | 1.75 | -2.33 | 0.0 | -3.6 | 0.0 |
| shift30_recent_linear | -1.56 | 0.0 | 0.0 | 1.89 | -2.19 | 0.0 | -3.45 | 0.0 |
| shift10_trend | -1.56 | 0.0 | 0.0 | 2.87 | -1.2 | 0.0 | -2.47 | 0.0 |
| shift10_trend_linear | -1.56 | 0.0 | 0.0 | 2.9 | -1.17 | 0.0 | -2.44 | 0.0 |
| shift10_co2 | -1.56 | 0.0 | 0.0 | 3.75 | -0.32 | 0.0 | -1.59 | 0.0 |
| eia_trend30 | -1.56 | 0.0 | 0.0 | -5.78 | -9.85 | 0.0 | -11.12 | 0.0 |
| eia_cdd_on_temp_recent | -1.56 | 0.0 | 0.0 | 3.44 | -0.64 | 0.0 | -1.9 | 0.0 |
| eia_cdd_on_temp_trend | -1.56 | 0.0 | 0.0 | 2.91 | -1.17 | 0.0 | -2.43 | 0.0 |
| p21_co2_ar1 | -3.62 | 0.0 | 0.0 | 3.54 | -0.53 | -2.06 | -1.8 | -2.06 |
| p21_regional_ar1 | -4.55 | 0.0 | 0.0 | 2.64 | -1.43 | -2.99 | -2.7 | -2.99 |
| hybrid_ridge_shift30_avg | -1.56 | 0.0 | 0.0 | 4.6 | 0.53 | 0.0 | -0.74 | 0.0 |

## Per-metric skill (%), years_4_7

Mean skill over origins; the `vs` columns are the difference in skill points.

| method | annual_avg_temp | total_precip_in | hottest_day_temp | cdd | cdd vs current_best | temp vs current_best | cdd vs hybrid_ridge_all_cdd | temp vs hybrid_ridge_all_cdd |
|---|---|---|---|---|---|---|---|---|
| current_best | 11.9 | 0.0 | 0.0 | 6.84 | 0.0 | 0.0 | -3.43 | 0.0 |
| ten_year_mean | 11.9 | -4.44 | -3.16 | 6.84 | 0.0 | 0.0 | -3.43 | 0.0 |
| hybrid_ridge_all_cdd | 11.9 | 0.0 | 0.0 | 10.27 | 3.43 | 0.0 | 0.0 | 0.0 |
| shift30_recent | 11.9 | 0.0 | 0.0 | 6.71 | -0.13 | 0.0 | -3.56 | 0.0 |
| shift30_recent_linear | 11.9 | 0.0 | 0.0 | 6.63 | -0.21 | 0.0 | -3.64 | 0.0 |
| shift10_trend | 11.9 | 0.0 | 0.0 | 5.28 | -1.55 | 0.0 | -4.99 | 0.0 |
| shift10_trend_linear | 11.9 | 0.0 | 0.0 | 5.26 | -1.57 | 0.0 | -5.01 | 0.0 |
| shift10_co2 | 11.9 | 0.0 | 0.0 | 3.95 | -2.89 | 0.0 | -6.32 | 0.0 |
| eia_trend30 | 11.9 | 0.0 | 0.0 | -9.31 | -16.14 | 0.0 | -19.58 | 0.0 |
| eia_cdd_on_temp_recent | 11.9 | 0.0 | 0.0 | 6.82 | -0.02 | 0.0 | -3.45 | 0.0 |
| eia_cdd_on_temp_trend | 11.9 | 0.0 | 0.0 | 5.7 | -1.14 | 0.0 | -4.57 | 0.0 |
| p21_co2_ar1 | 10.04 | 0.0 | 0.0 | 2.94 | -3.89 | -1.86 | -7.33 | -1.86 |
| p21_regional_ar1 | 7.44 | 0.0 | 0.0 | 3.66 | -3.18 | -4.45 | -6.61 | -4.45 |
| hybrid_ridge_shift30_avg | 11.9 | 0.0 | 0.0 | 9.53 | 2.69 | 0.0 | -0.74 | 0.0 |

## Raw score per origin, all

| method | 1980 | 1995 | 2011 | origins > current_best | origins > hybrid_ridge_all_cdd |
|---|---|---|---|---|---|
| current_best | -0.75 | 3.56 | 5.95 | 0 | 0 |
| ten_year_mean | -2.53 | 1.39 | 5.16 | 0 | 0 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 | 3 | 0 |
| shift30_recent | -0.15 | 3.08 | 4.96 | 1 | 0 |
| shift30_recent_linear | -0.18 | 3.2 | 4.86 | 1 | 0 |
| shift10_trend | -1.74 | 2.91 | 6.69 | 1 | 1 |
| shift10_trend_linear | -1.74 | 2.93 | 6.68 | 1 | 1 |
| shift10_co2 | -2.04 | 2.54 | 7.32 | 1 | 1 |
| eia_trend30 | -4.23 | -3.01 | 6.25 | 1 | 0 |
| eia_cdd_on_temp_recent | -0.11 | 3.89 | 4.67 | 2 | 0 |
| eia_cdd_on_temp_trend | -0.94 | 3.42 | 5.46 | 0 | 0 |
| p21_co2_ar1 | -4.26 | 1.53 | 8.58 | 1 | 1 |
| p21_regional_ar1 | -6.73 | 3.48 | 7.38 | 1 | 1 |
| hybrid_ridge_shift30_avg | 0.33 | 3.89 | 5.89 | 2 | 1 |

## Raw score per origin, years_4_7

| method | 1980 | 1995 | 2011 | origins > current_best | origins > hybrid_ridge_all_cdd |
|---|---|---|---|---|---|
| current_best | -1.93 | 8.02 | 7.95 | 0 | 0 |
| ten_year_mean | -5.06 | 6.04 | 7.37 | 0 | 0 |
| hybrid_ridge_all_cdd | -0.9 | 8.27 | 9.26 | 3 | 0 |
| shift30_recent | -1.16 | 8.41 | 6.71 | 2 | 1 |
| shift30_recent_linear | -1.2 | 8.48 | 6.61 | 2 | 1 |
| shift10_trend | -3.75 | 7.5 | 9.13 | 1 | 0 |
| shift10_trend_linear | -3.76 | 7.52 | 9.11 | 1 | 0 |
| shift10_co2 | -5.04 | 6.46 | 10.46 | 1 | 1 |
| eia_trend30 | -7.49 | 0.48 | 8.95 | 1 | 0 |
| eia_cdd_on_temp_recent | -1.11 | 8.8 | 6.35 | 2 | 1 |
| eia_cdd_on_temp_trend | -2.6 | 8.29 | 7.5 | 1 | 1 |
| p21_co2_ar1 | -8.49 | 4.76 | 13.46 | 1 | 1 |
| p21_regional_ar1 | -11.12 | 8.4 | 11.05 | 2 | 2 |
| hybrid_ridge_shift30_avg | -0.72 | 8.68 | 8.11 | 3 | 2 |

## Per city: `hybrid_ridge_shift30_avg` vs `hybrid_ridge_all_cdd`, CDD, years 4-7

`points` = the city's contribution to the raw-score gap (positive: the new variant is better), averaged over the 3 origins; the column sums to the mean CDD part of the raw-score gap. `warming` is the 30-year Avg Temp trend at the fold (°F/decade), `station_changes` the switches in the 30-year window, both averaged over folds. Elevation is not in the master table, so it is not checked (TBD).

Total: -0.184 points. Spearman correlation of `points` with city traits: warming +0.04, station_changes -0.10, cdd_level -0.09, lat +0.09.

### Top 10

| city_id | name | region | points | warming | station_changes | cdd_level | lat |
|---|---|---|---|---|---|---|---|
| USW00013968 | Tulsa | South Central | 0.0169 | 0.18 | 0.0 | 2058.0 | 36.2 |
| USW00023188 | SanDiego | Southwest | 0.0163 | 0.11 | 0.0 | 792.0 | 32.7 |
| USW00003947 | KansasCity | North Central | 0.0144 | -0.38 | 0.7 | 1442.0 | 39.3 |
| USW00013985 | DodgeCity | North Central | 0.0143 | 0.11 | 0.0 | 1493.0 | 37.8 |
| USW00013967 | Oklahoma | South Central | 0.014 | 0.21 | 0.3 | 1933.0 | 35.4 |
| USW00093842 | ColumbusGA | Southeast | 0.0128 | 0.32 | 0.0 | 2264.0 | 32.5 |
| USW00013984 | Concordia | North Central | 0.0122 | 0.06 | 0.0 | 1362.0 | 39.6 |
| USW00014939 | Lincoln | North Central | 0.0121 | 0.08 | 1.3 | 1186.0 | 40.9 |
| USW00013962 | Abilene | South Central | 0.0119 | 0.02 | 0.0 | 2433.0 | 32.4 |
| USW00023051 | Clayton | South Central | 0.0113 | 0.44 | 0.0 | 841.0 | 36.4 |

### Bottom 10

| city_id | name | region | points | warming | station_changes | cdd_level | lat |
|---|---|---|---|---|---|---|---|
| USW00012960 | Houston | South Central | -0.034 | -0.04 | 0.7 | 2978.0 | 30.0 |
| USW00003145 | Yuma | Southwest | -0.027 | 0.38 | 0.7 | 4363.0 | 32.6 |
| USW00012816 | Gainesville | Southeast | -0.0235 | -0.1 | 2.0 | 2747.0 | 29.7 |
| USW00013881 | Charlotte | Southeast | -0.0211 | 0.1 | 0.0 | 1639.0 | 35.2 |
| USW00013874 | Atlanta | Southeast | -0.0194 | 0.36 | 0.0 | 1781.0 | 33.6 |
| USW00093193 | Fresno | Southwest | -0.0183 | 0.51 | 0.0 | 1938.0 | 36.8 |
| USW00012815 | Orlando | Southeast | -0.0179 | 0.19 | 0.7 | 3395.0 | 28.4 |
| USW00012835 | FortMyers | Southeast | -0.0169 | 0.35 | 0.0 | 3824.0 | 26.6 |
| USW00093134 | LosAngeles | Southwest | -0.0155 | 0.12 | 0.0 | 1387.0 | 34.1 |
| USW00013889 | Jacksonville | Southeast | -0.0139 | -0.28 | 0.3 | 2697.0 | 30.5 |

### Regions

| region | cities | points | warming |
|---|---|---|---|
| North Central | 52 | 0.092 | 0.15 |
| South Central | 32 | 0.001 | 0.11 |
| Northwest | 34 | -0.043 | 0.17 |
| Southwest | 14 | -0.064 | 0.41 |
| Northeast | 50 | -0.071 | 0.16 |
| Southeast | 28 | -0.1 | 0.2 |

## Mechanism

Hypothesis (fixed before the run): CDD is convex in daily temperature, so recomputing it from a warmed daily climatology raises the forecast above a mean of past CDD, which under-forecasts CDD under warming.

Check 1, convexity (daily recomputation vs its first-order twin with the same shift). Sign supported; size not supported (needs at least 0.5 skill points).

- `shift30_recent` vs `shift30_recent_linear`: CDD skill years 4-7 higher at 2/3 origins, mean gap +0.08 skill points. Mean convexity lift of the forecast (daily - linear, °F-days, years 4-7) by origin: 1980: +0.8, 1995: +3.2, 2011: +1.6.
- `shift10_trend` vs `shift10_trend_linear`: CDD skill years 4-7 higher at 2/3 origins, mean gap +0.02 skill points. Mean convexity lift of the forecast (daily - linear, °F-days, years 4-7) by origin: 1980: +0.2, 1995: +0.9, 2011: +0.7.

Check 2, the 10-year mean of CDD is biased low (mean truth - forecast, °F-days, years 4-7, per origin): `current_best` under-forecasts at 3/3 origins, supported.

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| current_best | 41.1 | 25.8 | 159.7 |
| hybrid_ridge_all_cdd | 21.8 | 30.3 | 138.8 |
| hybrid_ridge_shift30_avg | 31.6 | 10.5 | 155.3 |
| shift10_trend | 59.3 | -6.7 | 134.9 |
| shift10_trend_linear | 59.5 | -5.8 | 135.6 |
| shift30_recent | 41.3 | -9.3 | 171.7 |
| shift30_recent_linear | 42.1 | -6.1 | 173.3 |

Check 3, the gain grows with the city's 30-year warming rate (Spearman over city-folds, needs rho >= 0.2 and p < 0.05): `shift30_recent` vs `current_best` rho -0.15 (p 0.00), not supported; `hybrid_ridge_shift30_avg` vs `hybrid_ridge_all_cdd` (per city) rho +0.04 (p 0.54), not supported.

**Conclusion.** The convexity is real (the exact recomputation sits above its tangent by 0.6 to 1.9 °F-days on average) but it is second order: the temperature shifts are a few tenths of a °F, while `current_best` under-forecasts CDD by 76 °F-days on average in years 4-7. A uniform annual-mean shift of the daily climatology does not recover that bias, and its gain does not follow the city warming rate, so the step-9 mechanism does not explain the CDD headroom. The pooled ridge captures more of it.

## Caveats

- Variants: 11 new variants plus 3 references, all fixed in the config before the first run.
  No variant was added or changed after the results were read. Three origins only; gaps under
  about 1 raw-score point are within noise. The best new variant is the best of 11 (selection
  optimism). Every method is deterministic (no seeds, no replicas needed).
- The mechanism checks' size thresholds were added after the first read of the results (see
  the code); the sign rules were fixed before.
- P06: the EIA note (Oct 2025 handbook) fits a 30-year OLS *time* trend per state to annual
  degree days; `eia_trend30` is that, per city. The CDD-on-temperature regression is the
  brief's adaptation, not the note's method. Population weighting and NOAA's short-range
  forecasts are not applicable here.
- P21 (Ho, Hawkins, Shaffrey and Underwood 2013): full text paywalled, only the abstract was
  read. They regress gridded SST on equivalent global-mean CO2 and fit AR(1) to the residual;
  we use Mauna Loa CO2 (log), extrapolated linearly from the last 10 years before each fold's
  cut-off (never observed later values), fit on at most 40 years (from 1959 only, so the 1980
  fold fits on 1959-1980), on city temperature and CDD instead of SST. P20 was not read.
- Step 9: the shift is uniform over all days of the year (an annual-mean anomaly); seasonal
  or variance changes are not modelled. Climatology = each city's last N years where both
  temperature and CDD pass the missing-days rule.
- Per-city traits: elevation is not in the master table (TBD); station changes are counted
  from `coverage_and_stations`. Correlations are descriptive, not causal.
- Packaging: step-9 variants read `daily.parquet`, which the submission package does not ship
  (`RAW_INPUTS`), and the CO2 variants read `data/external/noaa_co2`, which CI does not
  download, so neither could be submitted without changing shared packaging code.
