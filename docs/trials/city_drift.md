# Trial: city_drift

The final-round winner plus a robust, city-relative correction learned in-fold from each city's drift against its nearest neighbours. Compared with r4_winners.


## Report (2026-11-10)

**Result.** Three of the four candidates pass the pre-registered rule against `r4_winners`.
The rule picks `cd4_all_metrics`, which has the highest 27-origin mean. **The gain fades with
time**: it is about zero over the nine most recent origins. So the expected gain on 2019–2025
is small, and whether to submit it is the human's call.

No 2019–2025 data and no leaderboard score was used. All four candidates and the rule were
written into the config before any of them ran. The settings are the ones DragonDare
published (10 neighbours, windows 1/3/5/10/15); none was tuned here.

### Selection rule

The rule compares raw score on all years with `r4_winners` as the default. Figures for
`r4_winners`: official mean 4.85, 27-origin mean 4.99.

| candidate | (1) official mean | (2) 27-origin mean | (3) wins at ≥ 60% of 27 | passes |
| :-------- | :---------------- | :----------------- | :---------------------- | :----- |
| cd1_temp_cdd (primary) | 5.10 yes | 5.24 yes | 20 of 27 = 74% yes | **yes** |
| cd2_one_group | 5.07 yes | 5.24 yes | 19 of 27 = 70% yes | **yes** |
| cd3_national (control) | 4.57 no | 5.00 yes | 12 of 27 = 44% no | **no** |
| cd4_all_metrics | 5.04 yes | 5.34 yes | 21 of 27 = 78% yes | **yes** |

**Rule result: `cd4_all_metrics`** (three pass; cd4 has the highest 27-origin mean).

### Paired year-block bootstrap on the official folds

Each cell is the method minus `r4_winners`, with a 95% interval (`scripts/paired_bootstrap.py`).

| method | raw, all years | raw, years 1–3 | raw, years 4–7 | temperature skill (pp) | CDD skill (pp) |
| :----- | :------------- | :------------- | :------------- | :--------------------- | :------------- |
| cd1_temp_cdd | +0.24 [+0.06, +0.46] | +0.35 [+0.00, +0.75] | +0.17 [−0.02, +0.33] | +0.73 [+0.27, +1.29] | +0.25 [−0.11, +0.59] |
| cd2_one_group | +0.22 [+0.02, +0.43] | +0.33 [+0.01, +0.71] | +0.15 [−0.08, +0.33] | +0.67 [+0.19, +1.22] | +0.21 [−0.15, +0.56] |
| cd3_national | −0.28 [−0.57, −0.03] | −0.19 [−0.51, +0.14] | −0.37 [−0.75, −0.03] | −0.57 [−1.32, +0.29] | −0.57 [−1.32, +0.17] |
| cd4_all_metrics | +0.19 [−0.02, +0.43] | +0.36 [−0.07, +0.79] | +0.06 [−0.12, +0.24] | +0.73 [+0.27, +1.29] | +0.25 [−0.11, +0.59] |

On the official folds, cd4's two extra metrics lose slightly: precipitation −0.09 [−0.33,
+0.15] pp and hottest day −0.15 [−0.47, +0.17] pp. Over the 27 origins they gain:
precipitation skill 0.54 against 0.45, hottest day 0.95 against 0.64.

### Where the gain is, by era (27 rolling origins, method minus `r4_winners`, raw score)

| origins | cd1_temp_cdd | cd4_all_metrics | cd3_national | origins won (cd1 / cd4) |
| :------ | :----------- | :-------------- | :----------- | :---------------------- |
| 1985–1993 | +0.46 | +0.58 | +0.06 | 9 / 9 of 9 |
| 1994–2002 | +0.26 | +0.38 | +0.10 | 7 / 7 of 9 |
| 2003–2011 | +0.02 | +0.08 | −0.14 | 4 / 5 of 9 |
| 2005–2011 | −0.02 | +0.02 | −0.08 | 2 / 3 of 7 |

Official folds per origin, raw score: at 1980, cd1 0.84 against −0.05; at 1995, 5.23 against
5.24; at 2011, 9.22 against 9.36.

**Reading it.**

*   **Neighbours are the active ingredient.** The same model with the national mean as its
    reference (cd3) fails the rule and is worse on the official folds.
*   **It fills the years 1–3 gap.** Over 27 origins cd1 gains +0.35 in years 1–3 and +0.19 in
    years 4–7.
*   **The gain is concentrated before about 2003.** The pattern matches E2 (2011 fold alone
    +0.07) and DragonDare's own bench (95% of their gain from origins 1990–2003). A likely
    reason is that station drift against neighbours was larger in earlier decades; this was
    not tested.
*   **Expected effect on 2019–2025:** about zero, with no sign of harm at recent origins.

### Limits

*   No untouched holdout: the 27 origins overlap the official folds, and consecutive origins
    share target years, so 27 origins are worth about five independent seven-year blocks.
*   The replication origins (1934/1941/1948) were not run for these candidates.
*   Built and evaluated in about 20 minutes on the deadline day. A person should review
    `src/proto_star/forecasters/city_drift.py` before relying on it.

### Runs

Official folds: the newest `runs/trials/*_city_drift`. 27 origins: `runs/robustness/city_drift`.
Paired rows: `runs/paired/city_drift`.

## Appendix: record written by `climate-trial --record` (official folds)

### What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_city_drift.yaml` |
| Code version | `07af4ea` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `r4_winners` |

### Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_city_drift.yaml
```

### Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| r2_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| r4_winners | hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]] |
| cd1_temp_cdd | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a Huber-regression correction for annual_avg_temp, cdd on each city's drift against its 10 nearest cities over the last 1/3/5/10/15 years (lead groups 1-3, 4-7; 30 in-fold pseudo-origins; shrink 1.0) |
| cd2_one_group | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a Huber-regression correction for annual_avg_temp, cdd on each city's drift against its 10 nearest cities over the last 1/3/5/10/15 years (lead groups 1-7; 30 in-fold pseudo-origins; shrink 1.0) |
| cd3_national | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a Huber-regression correction for annual_avg_temp, cdd on each city's drift against all cities over the last 1/3/5/10/15 years (lead groups 1-3, 4-7; 30 in-fold pseudo-origins; shrink 1.0) |
| cd4_all_metrics | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a Huber-regression correction for annual_avg_temp, cdd, total_precip_in, hottest_day_temp on each city's drift against its 10 nearest cities over the last 1/3/5/10/15 years (lead groups 1-3, 4-7; 30 in-fold pseudo-origins; shrink 1.0) |

### Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

#### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| cd1_temp_cdd | 5.1 | 10.59 | 0.21 | 0.43 | 9.15 | 3 | 3 |
| cd2_one_group | 5.07 | 10.53 | 0.21 | 0.43 | 9.12 | 3 | 3 |
| cd3_national | 4.57 | 9.29 | 0.21 | 0.43 | 8.34 | 2 | 3 |
| cd4_all_metrics | 5.04 | 10.59 | 0.12 | 0.28 | 9.15 | 3 | 3 |
| r2_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| r4_winners | 4.85 | 9.86 | 0.21 | 0.43 | 8.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| cd1_temp_cdd | 1.81 | 0.81 | -0.15 | 0.73 | 5.86 | 3 | 3 |
| cd2_one_group | 1.79 | 0.76 | -0.15 | 0.73 | 5.83 | 3 | 3 |
| cd3_national | 1.27 | 0.05 | -0.15 | 0.73 | 4.46 | 3 | 3 |
| cd4_all_metrics | 1.82 | 0.81 | -0.26 | 0.89 | 5.86 | 3 | 3 |
| r2_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| r4_winners | 1.46 | -0.09 | -0.15 | 0.73 | 5.35 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| cd1_temp_cdd | 7.48 | 18.38 | 0.51 | 0.23 | 10.79 | 2 | 3 |
| cd2_one_group | 7.45 | 18.3 | 0.51 | 0.23 | 10.76 | 2 | 3 |
| cd3_national | 6.93 | 16.63 | 0.51 | 0.23 | 10.36 | 2 | 3 |
| cd4_all_metrics | 7.37 | 18.38 | 0.44 | -0.14 | 10.79 | 2 | 3 |
| r2_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| r4_winners | 7.3 | 17.73 | 0.51 | 0.23 | 10.74 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| cd1_temp_cdd | 0.84 | 5.23 | 9.22 |
| cd2_one_group | 0.83 | 5.19 | 9.2 |
| cd3_national | -0.19 | 4.87 | 9.02 |
| cd4_all_metrics | 0.73 | 5.16 | 9.22 |
| r2_lead_split3 | 0.05 | 4.83 | 9.2 |
| r4_winners | -0.05 | 5.24 | 9.36 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
