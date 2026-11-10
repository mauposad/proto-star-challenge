# Trial: family_neighbours

Precipitation and hottest-day levels moved from the 30-year mean toward a neighbour-anchored value (the city's offset from its 5 nearest neighbours over its current station segment), by a pooled weight. Controls: the city's own current-segment mean, all cities as neighbours, and 20 placebo draws of distant neighbours.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_family_neighbours.yaml` |
| Code version | `aa8e869` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `trend_level10_15_sensitivity` |
| Submit candidate | none |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_family_neighbours.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| trend_level10_15_sensitivity | Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day |
| h1_anchored | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=anchored) |
| h1_own_segment | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=own_segment) |
| h1_all_cities | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=all_cities) |
| h1_placebo_00 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=0) |
| h1_placebo_01 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=1) |
| h1_placebo_02 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=2) |
| h1_placebo_03 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=3) |
| h1_placebo_04 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=4) |
| h1_placebo_05 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=5) |
| h1_placebo_06 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=6) |
| h1_placebo_07 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=7) |
| h1_placebo_08 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=8) |
| h1_placebo_09 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=9) |
| h1_placebo_10 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=10) |
| h1_placebo_11 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=11) |
| h1_placebo_12 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=12) |
| h1_placebo_13 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=13) |
| h1_placebo_14 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=14) |
| h1_placebo_15 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=15) |
| h1_placebo_16 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=16) |
| h1_placebo_17 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=17) |
| h1_placebo_18 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=18) |
| h1_placebo_19 | Level moved toward a neighbour-anchored value by a pooled weight (base=trend_level10_15_sensitivity, arm=placebo, seed=19) |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `trend_level10_15_sensitivity`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_all_cities | 3.85 | 8.74 | 0.07 | -1.22 | 7.8 | 0 | 3 |
| h1_anchored | 4.15 | 8.74 | 0.27 | -0.22 | 7.8 | 2 | 3 |
| h1_own_segment | 3.84 | 8.74 | -0.02 | -1.18 | 7.8 | 1 | 3 |
| h1_placebo_00 | 4.0 | 8.74 | 0.63 | -1.16 | 7.8 | 1 | 3 |
| h1_placebo_01 | 3.96 | 8.74 | 0.33 | -1.06 | 7.8 | 1 | 3 |
| h1_placebo_02 | 3.95 | 8.74 | 0.34 | -1.1 | 7.8 | 1 | 3 |
| h1_placebo_03 | 3.98 | 8.74 | 0.49 | -1.11 | 7.8 | 1 | 3 |
| h1_placebo_04 | 3.88 | 8.74 | 0.2 | -1.24 | 7.8 | 0 | 3 |
| h1_placebo_05 | 3.92 | 8.74 | 0.17 | -1.04 | 7.8 | 1 | 3 |
| h1_placebo_06 | 3.95 | 8.74 | 0.33 | -1.1 | 7.8 | 1 | 3 |
| h1_placebo_07 | 3.97 | 8.74 | 0.47 | -1.15 | 7.8 | 1 | 3 |
| h1_placebo_08 | 3.94 | 8.74 | 0.33 | -1.1 | 7.8 | 1 | 3 |
| h1_placebo_09 | 3.94 | 8.74 | 0.36 | -1.15 | 7.8 | 1 | 3 |
| h1_placebo_10 | 3.84 | 8.74 | 0.16 | -1.35 | 7.8 | 1 | 3 |
| h1_placebo_11 | 4.0 | 8.74 | 0.45 | -1.02 | 7.8 | 1 | 3 |
| h1_placebo_12 | 4.0 | 8.74 | 0.51 | -1.06 | 7.8 | 1 | 3 |
| h1_placebo_13 | 3.93 | 8.74 | 0.46 | -1.28 | 7.8 | 1 | 3 |
| h1_placebo_14 | 3.9 | 8.74 | 0.28 | -1.23 | 7.8 | 1 | 3 |
| h1_placebo_15 | 4.01 | 8.74 | 0.53 | -1.02 | 7.8 | 1 | 3 |
| h1_placebo_16 | 3.99 | 8.74 | 0.68 | -1.28 | 7.8 | 1 | 3 |
| h1_placebo_17 | 3.99 | 8.74 | 0.52 | -1.09 | 7.8 | 1 | 3 |
| h1_placebo_18 | 3.9 | 8.74 | 0.22 | -1.16 | 7.8 | 1 | 3 |
| h1_placebo_19 | 3.97 | 8.74 | 0.53 | -1.21 | 7.8 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 4.14 | 8.74 | 0.0 | 0.0 | 7.8 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_all_cities | 0.22 | -2.56 | 0.75 | -1.2 | 3.87 | 1 | 3 |
| h1_anchored | 0.4 | -2.56 | 0.64 | -0.34 | 3.87 | 1 | 3 |
| h1_own_segment | 0.09 | -2.56 | 0.43 | -1.38 | 3.87 | 1 | 3 |
| h1_placebo_00 | 0.37 | -2.56 | 1.28 | -1.11 | 3.87 | 2 | 3 |
| h1_placebo_01 | 0.35 | -2.56 | 1.18 | -1.08 | 3.87 | 1 | 3 |
| h1_placebo_02 | 0.34 | -2.56 | 1.32 | -1.27 | 3.87 | 1 | 3 |
| h1_placebo_03 | 0.34 | -2.56 | 1.3 | -1.24 | 3.87 | 1 | 3 |
| h1_placebo_04 | 0.3 | -2.56 | 1.22 | -1.32 | 3.87 | 1 | 3 |
| h1_placebo_05 | 0.22 | -2.56 | 0.63 | -1.08 | 3.87 | 1 | 3 |
| h1_placebo_06 | 0.31 | -2.56 | 1.07 | -1.14 | 3.87 | 1 | 3 |
| h1_placebo_07 | 0.32 | -2.56 | 1.04 | -1.08 | 3.87 | 1 | 3 |
| h1_placebo_08 | 0.3 | -2.56 | 1.03 | -1.14 | 3.87 | 1 | 3 |
| h1_placebo_09 | 0.31 | -2.56 | 1.23 | -1.3 | 3.87 | 1 | 3 |
| h1_placebo_10 | 0.24 | -2.56 | 0.87 | -1.22 | 3.87 | 1 | 3 |
| h1_placebo_11 | 0.31 | -2.56 | 1.07 | -1.16 | 3.87 | 1 | 3 |
| h1_placebo_12 | 0.33 | -2.56 | 1.28 | -1.29 | 3.87 | 1 | 3 |
| h1_placebo_13 | 0.34 | -2.56 | 1.22 | -1.19 | 3.87 | 2 | 3 |
| h1_placebo_14 | 0.28 | -2.56 | 1.02 | -1.22 | 3.87 | 1 | 3 |
| h1_placebo_15 | 0.37 | -2.56 | 1.38 | -1.19 | 3.87 | 2 | 3 |
| h1_placebo_16 | 0.36 | -2.56 | 1.5 | -1.37 | 3.87 | 1 | 3 |
| h1_placebo_17 | 0.24 | -2.56 | 0.93 | -1.27 | 3.87 | 1 | 3 |
| h1_placebo_18 | 0.29 | -2.56 | 1.07 | -1.24 | 3.87 | 1 | 3 |
| h1_placebo_19 | 0.35 | -2.56 | 1.28 | -1.18 | 3.87 | 1 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 0.33 | -2.56 | 0.0 | 0.0 | 3.87 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_all_cities | 6.47 | 17.73 | -0.4 | -1.38 | 9.94 | 0 | 3 |
| h1_anchored | 6.88 | 17.73 | -0.01 | -0.12 | 9.94 | 2 | 3 |
| h1_own_segment | 6.55 | 17.73 | -0.28 | -1.18 | 9.94 | 1 | 3 |
| h1_placebo_00 | 6.58 | 17.73 | 0.04 | -1.38 | 9.94 | 0 | 3 |
| h1_placebo_01 | 6.52 | 17.73 | -0.4 | -1.2 | 9.94 | 0 | 3 |
| h1_placebo_02 | 6.51 | 17.73 | -0.49 | -1.14 | 9.94 | 0 | 3 |
| h1_placebo_03 | 6.57 | 17.73 | -0.2 | -1.17 | 9.94 | 0 | 3 |
| h1_placebo_04 | 6.42 | 17.73 | -0.65 | -1.34 | 9.94 | 0 | 3 |
| h1_placebo_05 | 6.54 | 17.73 | -0.32 | -1.17 | 9.94 | 0 | 3 |
| h1_placebo_06 | 6.53 | 17.73 | -0.31 | -1.23 | 9.94 | 0 | 3 |
| h1_placebo_07 | 6.56 | 17.73 | -0.03 | -1.38 | 9.94 | 0 | 3 |
| h1_placebo_08 | 6.53 | 17.73 | -0.32 | -1.23 | 9.94 | 0 | 3 |
| h1_placebo_09 | 6.52 | 17.73 | -0.38 | -1.22 | 9.94 | 0 | 3 |
| h1_placebo_10 | 6.39 | 17.73 | -0.46 | -1.65 | 9.94 | 0 | 3 |
| h1_placebo_11 | 6.62 | 17.73 | -0.08 | -1.11 | 9.94 | 0 | 3 |
| h1_placebo_12 | 6.61 | 17.73 | -0.16 | -1.04 | 9.94 | 0 | 3 |
| h1_placebo_13 | 6.48 | 17.73 | -0.2 | -1.53 | 9.94 | 0 | 3 |
| h1_placebo_14 | 6.46 | 17.73 | -0.37 | -1.45 | 9.94 | 0 | 3 |
| h1_placebo_15 | 6.61 | 17.73 | -0.21 | -1.04 | 9.94 | 0 | 3 |
| h1_placebo_16 | 6.57 | 17.73 | 0.02 | -1.4 | 9.94 | 0 | 3 |
| h1_placebo_17 | 6.66 | 17.73 | 0.11 | -1.14 | 9.94 | 1 | 3 |
| h1_placebo_18 | 6.46 | 17.73 | -0.53 | -1.29 | 9.94 | 0 | 3 |
| h1_placebo_19 | 6.53 | 17.73 | -0.14 | -1.42 | 9.94 | 0 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 3 |
| trend_level10_15_sensitivity | 6.92 | 17.73 | 0.0 | 0.0 | 9.94 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| h1_all_cities | -1.32 | 3.72 | 9.16 |
| h1_anchored | -1.01 | 3.78 | 9.69 |
| h1_own_segment | -1.27 | 3.98 | 8.81 |
| h1_placebo_00 | -1.13 | 3.53 | 9.61 |
| h1_placebo_01 | -1.16 | 3.38 | 9.66 |
| h1_placebo_02 | -1.07 | 3.28 | 9.62 |
| h1_placebo_03 | -1.06 | 3.33 | 9.67 |
| h1_placebo_04 | -1.28 | 3.43 | 9.49 |
| h1_placebo_05 | -1.06 | 3.42 | 9.39 |
| h1_placebo_06 | -1.03 | 3.39 | 9.48 |
| h1_placebo_07 | -1.01 | 3.37 | 9.54 |
| h1_placebo_08 | -1.09 | 3.31 | 9.62 |
| h1_placebo_09 | -1.04 | 3.34 | 9.52 |
| h1_placebo_10 | -1.23 | 3.36 | 9.39 |
| h1_placebo_11 | -1.04 | 3.4 | 9.63 |
| h1_placebo_12 | -1.11 | 3.45 | 9.66 |
| h1_placebo_13 | -1.08 | 3.43 | 9.45 |
| h1_placebo_14 | -1.17 | 3.27 | 9.6 |
| h1_placebo_15 | -1.12 | 3.42 | 9.74 |
| h1_placebo_16 | -1.1 | 3.45 | 9.61 |
| h1_placebo_17 | -1.04 | 3.39 | 9.63 |
| h1_placebo_18 | -1.12 | 3.34 | 9.48 |
| h1_placebo_19 | -1.04 | 3.42 | 9.53 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
| trend_level10_15_sensitivity | -1.26 | 3.76 | 9.91 |
