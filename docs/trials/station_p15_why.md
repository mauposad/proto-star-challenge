# Why analysis: station_p15

Source run: `runs/trials/20261107-171054_station_p15` (results.csv), plus forecasts
recomputed on the same ADR 0004 folds (1980, 1995, 2011; 7-year horizon) for the
per-city split. Made by `scripts/analyze_station_p15.py`. Raw score = official score
without its floor at zero. Nothing here uses leaderboard numbers.

## 1. Score table

Mean raw score over the three origins, and the origins (of 3) where the method beats
each reference, per window (all / years 1-3 / years 4-7). Years 4-7 match the Final
Score.

| method | all | years_1_3 | years_4_7 | wins vs current_best (all/1-3/4-7) | wins vs hybrid_ridge_all_cdd (all/1-3/4-7) |
|---|---|---|---|---|---|
| hybrid_ridge_all_cdd | 3.60 | 0.94 | 5.54 | 3/2/3 | 0/0/0 |
| adj_temp_k5_w5_ridge_cdd | 3.61 | 0.97 | 5.53 | 3/2/3 | 2/2/2 |
| seg_temp_cdd_min3 | 3.01 | 0.73 | 4.77 | 3/2/2 | 0/1/0 |
| adj_temp_cdd_k10_w10 | 2.99 | 0.71 | 4.75 | 3/2/3 | 0/1/0 |
| seg_temp_cdd | 2.96 | 0.67 | 4.73 | 2/1/3 | 0/1/0 |
| current_best | 2.92 | 0.63 | 4.68 | 0/0/0 | 0/1/0 |
| adj_temp_cdd_k5_w5_t2 | 2.93 | 0.67 | 4.68 | 3/2/2 | 0/1/0 |
| adj_temp_cdd_k5_w5 | 2.94 | 0.69 | 4.68 | 3/3/2 | 0/1/0 |
| adj_all_k5_w10 | 2.91 | 0.63 | 4.67 | 2/2/2 | 0/1/0 |
| seg_all_min10 | 2.79 | 0.68 | 4.41 | 1/2/1 | 0/1/0 |
| ten_year_mean | 1.34 | -0.62 | 2.78 | 0/0/0 | 0/0/0 |
| seg_temp_cdd_cap15 | 1.62 | 0.37 | 2.61 | 0/1/0 | 0/1/0 |

## 2. How many city-origins have a station switch in the averaging window

A switch counts when a new `Station Segment` starts after the first year of the window
that `current_best` averages: last 10 valid years (temperature/CDD) or the 30 calendar
years to the cut-off (precipitation/hottest day). `temp_step_applied` counts cities where
the k=5, ±5-year pairwise estimate could be made and was applied to temperature (it needs
3 clean years on both sides of the switch, so switches in the last 2 years are skipped).

| cutoff_year | cities | switch_in_10y | switch_in_30y | temp_step_applied |
|---|---|---|---|---|
| 1980 | 210 | 18 | 45 | 11 |
| 1995 | 210 | 13 | 26 | 6 |
| 2011 | 210 | 8 | 35 | 2 |

Total over the three origins: 39 of 630 city-origins for the 10-year window and 106 for the 30-year window. Every other city-origin gets exactly the reference forecast, by construction.

## 3. Per-metric skill (percent), by window

`x vs current` / `x vs hybrid` are the skill change against `current_best` and
`hybrid_ridge_all_cdd` in percentage points.

| method | window | temp | temp vs current | temp vs hybrid | precip | precip vs current | precip vs hybrid | hottest | hottest vs current | hottest vs hybrid | cdd | cdd vs current | cdd vs hybrid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adj_temp_k5_w5_ridge_cdd | all | 5.77 | 0.01 | 0.01 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 8.65 | 2.74 | 0.00 |
| adj_temp_k5_w5_ridge_cdd | years_1_3 | -1.48 | 0.08 | 0.08 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 5.34 | 1.27 | 0.00 |
| adj_temp_k5_w5_ridge_cdd | years_4_7 | 11.85 | -0.05 | -0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 10.27 | 3.43 | 0.00 |
| adj_temp_cdd_k10_w10 | all | 5.89 | 0.13 | 0.13 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 6.07 | 0.16 | -2.58 |
| adj_temp_cdd_k10_w10 | years_1_3 | -1.40 | 0.16 | 0.16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.23 | 0.16 | -1.11 |
| adj_temp_cdd_k10_w10 | years_4_7 | 12.01 | 0.11 | 0.11 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 7.00 | 0.16 | -3.27 |
| seg_temp_cdd_min3 | all | 5.89 | 0.12 | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 6.16 | 0.25 | -2.49 |
| seg_temp_cdd_min3 | years_1_3 | -1.35 | 0.21 | 0.21 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.26 | 0.19 | -1.08 |
| seg_temp_cdd_min3 | years_4_7 | 11.96 | 0.07 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 7.13 | 0.29 | -3.14 |

## 4. Per-origin raw score

| method | all 1980 | all 1995 | all 2011 | years_1_3 1980 | years_1_3 1995 | years_1_3 2011 | years_4_7 1980 | years_4_7 1995 | years_4_7 2011 |
|---|---|---|---|---|---|---|---|---|---|
| adj_temp_cdd_k10_w10 | -0.57 | 3.60 | 5.95 | 0.99 | -1.68 | 2.82 | -1.81 | 8.10 | 7.96 |
| adj_temp_k5_w5_ridge_cdd | 0.23 | 4.15 | 6.44 | 1.75 | -0.66 | 1.80 | -0.97 | 8.29 | 9.27 |
| current_best | -0.75 | 3.56 | 5.95 | 0.74 | -1.68 | 2.82 | -1.93 | 8.02 | 7.95 |
| hybrid_ridge_all_cdd | 0.24 | 4.13 | 6.44 | 1.69 | -0.66 | 1.80 | -0.90 | 8.27 | 9.26 |
| seg_temp_cdd_min3 | -0.67 | 3.57 | 6.14 | 0.94 | -1.72 | 2.96 | -1.93 | 8.07 | 8.18 |

## 5. Per city: `adj_temp_k5_w5_ridge_cdd` vs `hybrid_ridge_all_cdd`

**all**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | 0.001 | 10 | 5 |

**years_4_7**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | -0.012 | 7 | 5 |

Years 4-7, 12 cities change at all. Top 10 (largest gain) and bottom 10:

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00094040 | McCook | North Central | 2 | 0.494 | 0.010 | 0.010 | 0.000 |
| USW00012815 | Orlando | Southeast | 1 | -0.779 | 0.003 | 0.003 | 0.000 |
| USW00014920 | LaCrosse | North Central | 1 | 0.781 | 0.003 | 0.003 | 0.000 |
| USW00003927 | DallasFortWorth | South Central | 1 | -0.976 | 0.002 | 0.002 | 0.000 |
| USW00094949 | Hastings | North Central | 1 | 0.852 | 0.001 | 0.001 | 0.000 |
| USW00014711 | MiddletownHarrisburg | Northeast | 1 | 0.022 | 0.000 | 0.000 | 0.000 |
| USW00014895 | Akron | Northeast | 1 | 0.009 | 0.000 | 0.000 | 0.000 |
| USW00003856 | Huntsville | Southeast | 1 | -0.021 | -0.000 | -0.000 | 0.000 |
| USC00356749 | Portland | Northwest | 1 | -0.900 | -0.004 | -0.004 | 0.000 |
| USW00014894 | Wheeling | Northeast | 1 | -0.458 | -0.005 | -0.005 | 0.000 |

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00013971 | Harrison | South Central | 1 | -0.969 | -0.018 | -0.018 | 0.000 |
| USW00014942 | Omaha | North Central | 2 | -1.127 | -0.005 | -0.005 | 0.000 |
| USW00014894 | Wheeling | Northeast | 1 | -0.458 | -0.005 | -0.005 | 0.000 |
| USC00356749 | Portland | Northwest | 1 | -0.900 | -0.004 | -0.004 | 0.000 |
| USW00003856 | Huntsville | Southeast | 1 | -0.021 | -0.000 | -0.000 | 0.000 |
| USW00014895 | Akron | Northeast | 1 | 0.009 | 0.000 | 0.000 | 0.000 |
| USW00014711 | MiddletownHarrisburg | Northeast | 1 | 0.022 | 0.000 | 0.000 | 0.000 |
| USW00094949 | Hastings | North Central | 1 | 0.852 | 0.001 | 0.001 | 0.000 |
| USW00003927 | DallasFortWorth | South Central | 1 | -0.976 | 0.002 | 0.002 | 0.000 |
| USW00014920 | LaCrosse | North Central | 1 | 0.781 | 0.003 | 0.003 | 0.000 |

Region totals (years 4-7):

| region | cities | change |
|---|---|---|
| South Central | 32 | -0.015 |
| Northeast | 50 | -0.004 |
| Northwest | 34 | -0.004 |
| Southwest | 14 | 0.000 |
| Southeast | 28 | 0.003 |
| North Central | 52 | 0.009 |

Years 4-7 total change -0.012 points; the largest single city (McCook) contributes 0.010.

City-origins with an applied temperature step: 15. Spearman correlation of |temperature step| with the temperature contribution: -0.19. Spearman of 30-year warming rate (all city-origins) with the total contribution: 0.03.

## 5. Per city: `adj_temp_cdd_k10_w10` vs `current_best`

**all**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | 0.073 | 12 | 6 |

**years_4_7**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | 0.069 | 12 | 5 |

Years 4-7, 16 cities change at all. Top 10 (largest gain) and bottom 10:

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00094040 | McCook | North Central | 2 | 0.494 | 0.070 | 0.035 | 0.034 |
| USW00003927 | DallasFortWorth | South Central | 1 | -0.976 | 0.007 | 0.003 | 0.004 |
| USW00014895 | Akron | Northeast | 1 | 0.009 | 0.006 | 0.002 | 0.004 |
| USW00014710 | Manchester | Northeast | 1 | 0.000 | 0.006 | 0.004 | 0.002 |
| USW00014942 | Omaha | North Central | 2 | -1.127 | 0.005 | -0.006 | 0.011 |
| USW00012815 | Orlando | Southeast | 1 | -0.779 | 0.003 | 0.003 | 0.000 |
| USW00093988 | PineBluff | South Central | 2 | -0.303 | 0.003 | 0.003 | 0.000 |
| USW00003947 | KansasCity | North Central | 1 | -2.513 | 0.003 | -0.000 | 0.003 |
| USW00003856 | Huntsville | Southeast | 1 | -0.021 | 0.002 | 0.000 | 0.002 |
| USW00014920 | LaCrosse | North Central | 1 | 0.781 | 0.001 | 0.001 | 0.000 |

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00013971 | Harrison | South Central | 1 | -0.969 | -0.013 | -0.012 | -0.002 |
| USW00023009 | Roswell | Southwest | 1 | 1.829 | -0.010 | 0.000 | -0.010 |
| USW00014894 | Wheeling | Northeast | 1 | -0.458 | -0.006 | -0.001 | -0.005 |
| USC00356749 | Portland | Northwest | 1 | -0.900 | -0.005 | -0.004 | -0.002 |
| USW00014711 | MiddletownHarrisburg | Northeast | 1 | 0.022 | -0.001 | -0.001 | 0.000 |
| USW00094949 | Hastings | North Central | 1 | 0.852 | 0.000 | 0.000 | 0.000 |
| USW00014920 | LaCrosse | North Central | 1 | 0.781 | 0.001 | 0.001 | 0.000 |
| USW00003856 | Huntsville | Southeast | 1 | -0.021 | 0.002 | 0.000 | 0.002 |
| USW00003947 | KansasCity | North Central | 1 | -2.513 | 0.003 | -0.000 | 0.003 |
| USW00093988 | PineBluff | South Central | 2 | -0.303 | 0.003 | 0.003 | 0.000 |

Region totals (years 4-7):

| region | cities | change |
|---|---|---|
| Southwest | 14 | -0.010 |
| Northwest | 34 | -0.005 |
| South Central | 32 | -0.003 |
| Northeast | 50 | 0.004 |
| Southeast | 28 | 0.005 |
| North Central | 52 | 0.078 |

Years 4-7 total change 0.069 points; the largest single city (McCook) contributes 0.070.

City-origins with an applied temperature step: 15. Spearman correlation of |temperature step| with the temperature contribution: -0.29. Spearman of 30-year warming rate (all city-origins) with the total contribution: -0.02.

## 5. Per city: `seg_temp_cdd_min3` vs `current_best`

**all**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | 0.094 | 12 | 11 |

**years_4_7**: mean raw-score change over origins split by switch in the 10-year window (sums to the score difference).

| switch_in_10y | city_origins | raw_score_change | improved | worse |
|---|---|---|---|---|
| False | 588 | 0.000 | 0 | 0 |
| True | 34 | 0.089 | 11 | 10 |

Years 4-7, 20 cities change at all. Top 10 (largest gain) and bottom 10:

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00094040 | McCook | North Central | 2 | 0.494 | 0.078 | 0.047 | 0.031 |
| USC00042863 | Escondido | Southwest | 3 | 0.000 | 0.066 | 0.033 | 0.033 |
| USW00093821 | Louisville | Northeast | 1 | 0.000 | 0.021 | 0.009 | 0.012 |
| USW00014920 | LaCrosse | North Central | 1 | 0.781 | 0.006 | 0.004 | 0.003 |
| USC00280734 | Belvidere | Northeast | 2 | 0.000 | 0.005 | 0.003 | 0.002 |
| USW00093988 | PineBluff | South Central | 2 | -0.303 | 0.003 | 0.003 | 0.000 |
| USW00003947 | KansasCity | North Central | 1 | -2.513 | 0.003 | 0.000 | 0.003 |
| USW00014894 | Wheeling | Northeast | 1 | -0.458 | 0.002 | 0.001 | 0.001 |
| USW00014895 | Akron | Northeast | 1 | 0.009 | 0.001 | 0.002 | -0.001 |
| USW00003927 | DallasFortWorth | South Central | 1 | -0.976 | 0.000 | -0.001 | 0.001 |

| city_id | name | region | switch_origins | temp_step | total | annual_avg_temp | cdd |
|---|---|---|---|---|---|---|---|
| USW00014942 | Omaha | North Central | 2 | -1.127 | -0.018 | -0.022 | 0.004 |
| USW00014710 | Manchester | Northeast | 1 | 0.000 | -0.017 | -0.020 | 0.003 |
| USW00003171 | Riverside | Southwest | 1 | 0.000 | -0.016 | -0.008 | -0.009 |
| USW00023009 | Roswell | Southwest | 1 | 1.829 | -0.014 | 0.000 | -0.014 |
| USW00014711 | MiddletownHarrisburg | Northeast | 1 | 0.022 | -0.007 | -0.007 | 0.000 |
| USW00013971 | Harrison | South Central | 1 | -0.969 | -0.007 | -0.015 | 0.008 |
| USC00356749 | Portland | Northwest | 1 | -0.900 | -0.006 | -0.003 | -0.004 |
| USW00012815 | Orlando | Southeast | 1 | -0.779 | -0.004 | -0.003 | -0.002 |
| USW00014939 | Lincoln | North Central | 1 | 0.000 | -0.004 | -0.006 | 0.002 |
| USW00094949 | Hastings | North Central | 1 | 0.852 | -0.002 | -0.000 | -0.001 |

Region totals (years 4-7):

| region | cities | change |
|---|---|---|
| Northwest | 34 | -0.006 |
| Southeast | 28 | -0.004 |
| South Central | 32 | -0.004 |
| Northeast | 50 | 0.005 |
| Southwest | 14 | 0.036 |
| North Central | 52 | 0.063 |

Years 4-7 total change 0.089 points; the largest single city (McCook) contributes 0.078.

City-origins with an applied temperature step: 15. Spearman correlation of |temperature step| with the temperature contribution: -0.34. Spearman of 30-year warming rate (all city-origins) with the total contribution: 0.04.

## 6. Mechanism and check

**Hypothesis.** A station switch inside the 10-year window mixes two sites in the mean. If
the old site reads differently by a step *s*, the mean is off by about *s* times the share
of old-station years, while the forecast years are measured at the new site. Removing the
step (pairwise neighbor estimate, P15) or dropping the old years (current segment) should
then help at the switched city-origins, more so for larger steps.

**Check.**

- Where the change lives: only city-origins with a switch inside the window change, by
  construction (section 5). That is 39 of 630 city-origins (6 %), and a temperature step
  could be estimated and applied at only 19 of them; switches in the last two years before
  the cut-off have too few clean years on the new side.
- Direction: supported weakly. More switched city-origins improve than worsen for the
  adjusted variant on its own (`adj_temp_cdd_k10_w10`, years 4-7: 12 better, 5 worse) but
  the segment variant is close to a coin flip (11 vs 10).
- Size of the step: **not supported.** The Spearman correlation between |estimated step|
  and the temperature gain is near zero or negative in every pair (section 5), so larger
  steps did not give larger gains.
- Concentration: the gains of the P15-only variants (+0.07 to +0.09 raw points) come mostly
  from one city, McCook (NE), which switched inside the window at two origins (plus
  Escondido for the segment variant).
- Against the submitted `hybrid_ridge_all_cdd`, the best variant only changes temperature at
  the switched cities: -0.05 skill points for temperature in years 4-7 and a raw score of
  5.53 vs 5.54. CDD is identical (ridge) and precipitation/hottest day are unchanged.
- Warming rate, region: no relation (Spearman of the 30-year warming rate with the change
  is about 0; the region totals are within +-0.08). Elevation: TBD (not in the master
  table, and this track uses no external data).

**Verdict.** The mechanism is real but tiny for this score: few switches fall inside the
averaging window, the step estimates from five neighbours over +-5 years are noisy (the
standard error of an applied step was about 0.2-0.7 degF for steps of 0.3-2.5 degF), and a 10-year
mean already keeps half its years on the new station. The station effect is far below the
fold-to-fold noise (differences under about 1 point are not distinguishable on 3 origins).

## 7. Caveats

- 9 station variants plus 3 references, all fixed in the config before the first run. No
  variant was added after seeing results. Every method is deterministic (no seeds).
- `seg_temp_cdd_cap15` was meant as "segment capped at 15 years", but the cap also widens
  the fallback window to 15 years, so it mostly measures a 15-year mean. It lost badly
  (2.61 in years 4-7), as the 15-year mean did in `baselines_round1`.
- Selection optimism: the best P15-only variant is the best of 8 on 3 origins; its +0.07
  over `current_best` is well inside noise.
- Deviations from P15 (Menne & Williams 2009): break dates come from our station metadata
  instead of the SNHT pairwise break search; steps use simple before/after means of the
  city-minus-neighbor-mean difference over +-5 or +-10 years, not the paper's
  multi-pair attribution and median of pairwise estimates; annual, not monthly, values; one
  additive step for every metric (precipitation and CDD included); neighbours chosen by
  distance only, not by correlation. Paper full text was not read here (journal page); the
  method follows its abstract and the standard description of the pairwise algorithm.
- 5 of the 39 switched city-origins have no scored rows in the test years, so section 5
  counts 34.

## 8. Variants in this trial

`seg_temp_cdd`, `seg_temp_cdd_min3`, `seg_temp_cdd_cap15`, `seg_all_min10`, `adj_temp_cdd_k5_w5`, `adj_temp_cdd_k10_w10`, `adj_temp_cdd_k5_w5_t2`, `adj_all_k5_w10`, `adj_temp_k5_w5_ridge_cdd` (9 station variants, all fixed before the first run).
