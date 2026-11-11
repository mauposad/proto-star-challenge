# Trial: ml_challengers

Option 1, gradient-boosted error correction stacked on the final-round winner; option 2, zero-shot Chronos-T5-small, alone and averaged with the winner. Compared with r4_winners.


## Report (2026-11-10)

**Result.** No ML challenger replaces `r4_winners`. Every candidate fails condition 1 of the
pre-registered rule, and the official-fold paired intervals show that every candidate is worse
or no better.

*   **Gradient-boosted error correction (option 1):** loses at all three strengths. The more it
    is regularized, the closer it gets to the winner. The strongest-regularized variant, ml3,
    reaches 4.96 against 4.99 over 27 origins and wins at 14 of 27, but is still below it.
*   **Zero-shot Chronos-T5-small (option 2):** worse than the 30-year mean, alone and in an
    equal-weight mean with the winner.

The submission candidate stays `r4_winners` (`configs/mp_final_round.yaml`). No 2019–2025 data
and no leaderboard score was used.

### Selection rule (from the config, written before the runs)

The rule compares raw score on all years with `r4_winners` as the default. A candidate passes
only if all three conditions hold. Figures for `r4_winners`: official mean 4.85, 27-origin
mean 4.99.

| candidate | (1) official mean | (2) 27-origin mean | (3) wins at ≥ 60% of 27 | passes |
| :-------- | :---------------- | :----------------- | :---------------------- | :----- |
| ml1_rb_raw | −0.62 no | 0.65 no | 7% no | **no** |
| ml2_rb_city | 2.64 no | 3.75 no | 11% no | **no** |
| ml3_rb_city_strong (*) | 4.53 no | 4.96 no | 52% no | **no** |
| ml4_chronos64 | −2.94 no | −2.05 no | 0% no | **no** |
| ml5_chronos30 (*) | −4.83 no | −3.23 no | 0% no | **no** |
| ml6_r4_chronos_mean | 2.94 no | 3.50 no | 19% no | **no** |

(*) Added after a one-fold smoke test at the 2011 cut-off (see the config header). These rows
are exploratory.

For comparison, `r2_lead_split3` scores 4.69 on the official folds and 4.72 over 27 origins.

### Paired year-block bootstrap on the official folds

Each cell is the method minus `r4_winners`, with a 95% interval from resampling forecast years
within each fold (`scripts/paired_bootstrap.py`, `proto_star.paired`; 4,000 draws, seed 0).

| method | raw, all years | raw, years 1–3 | raw, years 4–7 |
| :----- | :------------- | :------------- | :------------- |
| r2_lead_split3 | −0.16 [−0.29, −0.04] | −0.14 [−0.33, +0.03] | −0.19 [−0.33, −0.04] |
| ml1_rb_raw | −5.47 [−6.90, −3.94] | −4.65 [−6.40, −2.66] | −6.30 [−7.98, −4.30] |
| ml2_rb_city | −2.21 [−3.10, −1.13] | −1.96 [−3.40, +0.12] | −2.53 [−3.43, −1.76] |
| ml3_rb_city_strong | −0.32 [−0.67, +0.08] | −0.23 [−0.77, +0.50] | −0.42 [−0.79, −0.08] |
| ml4_chronos64 | −7.79 [−10.62, −4.87] | −4.69 [−7.98, −1.57] | −9.97 [−12.63, −7.31] |
| ml5_chronos30 | −9.68 [−11.64, −7.67] | −8.38 [−11.36, −5.39] | −10.92 [−12.78, −9.14] |
| ml6_r4_chronos_mean | −1.91 [−3.36, −0.45] | −0.74 [−2.53, +0.99] | −2.68 [−4.04, −1.32] |

Per-metric skill, all years, in percentage points:

| method | temperature | precipitation | hottest day | CDD |
| :----- | :---------- | :------------ | :---------- | :-- |
| ml1_rb_raw | −9.30 [−13.07, −5.58] | −4.32 [−5.86, −2.79] | −3.81 [−7.02, −0.17] | −4.46 [−8.41, −1.08] |
| ml2_rb_city | −2.55 [−4.45, −0.39] | −2.21 [−3.46, −0.92] | −1.20 [−3.60, +1.19] | −2.89 [−4.19, −1.59] |
| ml3_rb_city_strong | −0.40 [−1.03, +0.34] | −0.45 [−0.98, +0.09] | +0.07 [−0.89, +1.04] | −0.50 [−1.05, +0.03] |
| ml4_chronos64 | −7.63 [−14.33, −0.65] | −7.19 [−9.19, −5.22] | −7.36 [−9.48, −4.82] | −8.97 [−14.17, −3.78] |
| ml5_chronos30 | −6.98 [−11.67, −2.41] | −10.27 [−11.95, −8.48] | −12.52 [−16.27, −7.83] | −8.97 [−12.43, −5.51] |
| ml6_r4_chronos_mean | −1.81 [−5.13, +1.59] | −2.25 [−3.33, −1.16] | −1.43 [−2.50, −0.16] | −2.17 [−4.92, +0.57] |

### What the two options are

*   **Option 1, `residual_boost`** (`src/proto_star/forecasters/residual_boost.py`).
    *   `r4_winners` is refit at 30 in-fold pseudo-origins.
    *   One `HistGradientBoostingRegressor` per metric (absolute-error loss) learns its errors
        from features that use only rows up to each origin: the lead, the base forecast's
        departure from the 30-year mean, the 30-year mean, standard deviation and slope,
        recent anomalies split into national and city parts, location, and years since the
        latest station switch.
    *   `target: city` centres targets and corrections across cities, so no common shift can
        be learned.
    *   Reading: the boosted correction mostly fits noise. Annual errors are shared across
        cities within a year, so 30 pseudo-origins give few independent cases, and the
        correction transfers worse than none. This matches U1 on `agent/hypothesis-trials`
        (direct boosting, years 4–7 −3.84 raw against the pooled trend).
*   **Option 2, `chronos_zero_shot`** (`src/proto_star/forecasters/chronos_zero_shot.py`).
    *   `amazon/chronos-t5-small` at revision `a971ba21945c4f1796b17a91fe69214b5f4ad472`
        (46M parameters, Apache-2.0), run on CPU.
    *   The forecast is the median of 20 sample paths per city series, from organizer-valid
        annual values only.
    *   Reading: Chronos forecasts a smoothed recent level. It misses the slow warming trend
        that the pooled trend captures, and it is noisier than the 30-year mean for
        precipitation and the hottest day.

### The 2018 data cut-off and the pretrained model

*   **Model choice:** Chronos-T5 was chosen over Chronos-Bolt because its training corpus is
    published (Ansari et al. 2024, arXiv 2403.07815, Appendix B; `autogluon/chronos_datasets`).
    The Chronos-Bolt maintainers state that its training data will not be released.
*   **Weather data in that corpus:**
    *   USHCN daily ("climate stations located in 48 states in the USA"): the published file
        checked here (`ushcn_daily`, `train/0.parquet`, 406 stations) ends on 2014-12-31;
    *   WeatherBench: 1979–2018.
*   **Why it is still exploratory:** no 2019–2025 weather is known to be in the weights. But the
    weights are an input the team did not fit, and the other two USHCN files were not
    checked. Since Chronos lost by a wide margin, this does not affect any choice.

### Dependency

`chronos-forecasting>=2` was added to the optional `hf` extra (`uv sync --extra hf`). It adds
`chronos-forecasting` 2.3.2, `accelerate` and `einops` to `uv.lock` and changes no other
package. Version 1.5 was tried first and rejected: it would have downgraded `transformers`,
`huggingface-hub` and `datasets` for everyone.

### Runs

*   Official folds: `runs/trials/20261110-160757_ml_challengers`.
*   27 origins: `runs/robustness/ml_challengers`.
*   Paired rows: `runs/paired/ml_challengers`.

`r4_winners` reproduces its logged scores exactly: 4.85 / 1.46 / 7.30 official, and 4.99 over
27 origins.

## Appendix: record written by `climate-trial --record` (official folds)

### What was used

| Item | Value |
|---|---|
| Date | 2026-11-10 |
| Config | `configs/at_ml_challengers.yaml` |
| Code version | `07af4ea` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `r4_winners` |

### Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/at_ml_challengers.yaml
```

### Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| r2_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| r4_winners | hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]] |
| ml1_rb_raw | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a gradient-boosted correction of its errors for annual_avg_temp, total_precip_in, hottest_day_temp, cdd, learned at 30 in-fold pseudo-origins (depth 3, 200 trees, lr 0.05, leaf 200, shrink 1.0) |
| ml2_rb_city | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a gradient-boosted city-relative correction of its errors for annual_avg_temp, total_precip_in, hottest_day_temp, cdd, learned at 30 in-fold pseudo-origins (depth 3, 200 trees, lr 0.05, leaf 200, shrink 1.0) |
| ml3_rb_city_strong | [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]] plus a gradient-boosted city-relative correction of its errors for annual_avg_temp, total_precip_in, hottest_day_temp, cdd, learned at 30 in-fold pseudo-origins (depth 2, 100 trees, lr 0.05, leaf 1000, shrink 0.5) |
| ml4_chronos64 | Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 64 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere |
| ml5_chronos30 | Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 30 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere |
| ml6_r4_chronos_mean | cdd = 0.5 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; 0.5 x [chronos_zero_shot: Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 64 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere]; other metrics from [swap_metric: hottest_day_temp = 0.5 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; 0.5 x [chronos_zero_shot: Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 64 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere]; other metrics from [swap_metric: total_precip_in = 0.5 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; 0.5 x [chronos_zero_shot: Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 64 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere]; other metrics from [swap_metric: annual_avg_temp = 0.5 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; 0.5 x [chronos_zero_shot: Chronos zero-shot (amazon/chronos-t5-small@a971ba2), median of 20 samples from the last 64 years, for annual_avg_temp, total_precip_in, hottest_day_temp, cdd; 30-year mean elsewhere]; other metrics from [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]]]] |

### Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

#### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| ml1_rb_raw | -0.62 | 0.55 | -4.1 | -3.38 | 4.44 | 2 | 3 |
| ml2_rb_city | 2.64 | 7.3 | -2.0 | -0.77 | 6.02 | 2 | 3 |
| ml3_rb_city_strong | 4.53 | 9.46 | -0.24 | 0.5 | 8.41 | 2 | 3 |
| ml4_chronos64 | -2.94 | 2.23 | -6.97 | -6.94 | -0.06 | 0 | 3 |
| ml5_chronos30 | -4.83 | 2.88 | -10.06 | -12.1 | -0.06 | 0 | 3 |
| ml6_r4_chronos_mean | 2.94 | 8.05 | -2.03 | -1.0 | 6.74 | 2 | 3 |
| r2_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| r4_winners | 4.85 | 9.86 | 0.21 | 0.43 | 8.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| ml1_rb_raw | -3.19 | -6.0 | -3.29 | -1.14 | -2.32 | 0 | 3 |
| ml2_rb_city | -0.5 | -1.66 | -2.86 | 0.87 | 1.65 | 1 | 3 |
| ml3_rb_city_strong | 1.23 | -0.28 | -0.78 | 1.37 | 4.62 | 3 | 3 |
| ml4_chronos64 | -3.23 | -0.47 | -7.46 | -5.88 | 0.9 | 0 | 3 |
| ml5_chronos30 | -6.92 | -1.81 | -11.42 | -12.43 | -2.0 | 0 | 3 |
| ml6_r4_chronos_mean | 0.72 | 0.92 | -2.43 | -0.62 | 5.0 | 2 | 3 |
| r2_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| r4_winners | 1.46 | -0.09 | -0.15 | 0.73 | 5.35 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| ml1_rb_raw | 1.01 | 5.96 | -4.54 | -5.49 | 8.1 | 2 | 3 |
| ml2_rb_city | 4.77 | 14.37 | -1.33 | -2.08 | 8.13 | 2 | 3 |
| ml3_rb_city_strong | 6.88 | 17.17 | 0.18 | -0.15 | 10.31 | 2 | 3 |
| ml4_chronos64 | -2.67 | 4.66 | -6.44 | -8.08 | -0.8 | 1 | 3 |
| ml5_chronos30 | -3.61 | 6.6 | -9.2 | -12.58 | 0.73 | 0 | 3 |
| ml6_r4_chronos_mean | 4.62 | 13.84 | -1.63 | -1.37 | 7.65 | 2 | 3 |
| r2_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| r4_winners | 7.3 | 17.73 | 0.51 | 0.23 | 10.74 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| ml1_rb_raw | -6.39 | 0.98 | 3.54 |
| ml2_rb_city | -1.54 | 2.37 | 7.09 |
| ml3_rb_city_strong | -0.16 | 4.78 | 8.97 |
| ml4_chronos64 | -4.68 | -0.69 | -3.44 |
| ml5_chronos30 | -7.0 | -4.22 | -3.28 |
| ml6_r4_chronos_mean | -0.09 | 4.24 | 4.67 |
| r2_lead_split3 | 0.05 | 4.83 | 9.2 |
| r4_winners | -0.05 | 5.24 | 9.36 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
