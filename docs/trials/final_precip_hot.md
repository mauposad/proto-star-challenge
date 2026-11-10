# Trial: final_precip_hot (agent P, final round)

Precipitation and hottest-day components of Tatakae, PstarAlu and the CRM. Each candidate is a
`swap_metric` over lead_split3 (`lead_blend`, the current submission) that replaces one metric
only; the other three metrics stay identical to lead_split3 (metric-isolation tests in
`tests/test_final_precip.py` and `tests/test_final_hottest.py`).

## Pre-registration (written before any candidate ran)

This section was written, with the config rows, before the first run. Results come after it.

### Sources (re-implemented from README text only; no code downloaded)

| Team | Dataset (CC BY 4.0) | Commit read | README sections used |
|---|---|---|---|
| PstarAlu (Nibedita Biswal) | `nbiswal-star/protostar-climate-submission` | `9e51c3ef5d3178ca194f28e2c4134201c1bf9675` | Method > Precipitation, Hottest day; Validation |
| Tatakae (Mashrafi Mahmud Rafi) | `ironMan334/protostar-climate-team-tatakae` | `f18c1178c1b97566c75facc94c886184ebaa2a10` | Method: "Rain and the hottest day" nudge; What did not work |

Both READMEs quote leaderboard / Live Score numbers. They were not used for anything. PstarAlu
cites Fay & Herriot (1979), JASA 74(366), 269-277, doi 10.1080/01621459.1979.10482505.

### Common definitions

- **30-year mean (M30)**: the official `thirty_year_mean` baseline (valid years, i.e. at most 10
  missing days by the organizer rule, in the 30 calendar years to the cut-off; the last 30
  valid years if that window is empty). Every component falls back to M30 where it is not
  defined, so it covers exactly the rows of the base forecast.
- **Neighbors**: great-circle distance from each city's `Lat`/`Lon` in `train`
  (`proto_star.neighbors`). Gaussian kernel `exp(-0.5 (d / 300 km)^2)`.
- **Complete precipitation year**: `ToT Prcp` finite and `days_in_year - Miss Prcp >= 360`
  (365 or 366 days).
- **Complete daily-maximum year** (H2): at least 360 days with a non-missing `tmax` in the daily
  table (same 360-day threshold as precipitation), read through `daily_to_cutoff` at the fold
  cut-off.

### Interpretation of each row (one reading each; no alternatives will be run)

| ID | Interpretation and fixed parameters |
|---|---|
| P0 / H0 | lead_split3 (M30 for both metrics). Named `p0_lead_split3`. |
| P1 | Ratio anomaly `a_ct = P_ct / M30_c - 1` (`own_anomalies`, window 30, at least 10 valid years). Departure `d_ct = a_ct - mean of a_jt over the 31 nearest cities j with data in year t` (equal weights, leave-one-out). `D_c` = mean of `d_ct` over the valid years in the last 10 calendar years (cut-off - 9 ... cut-off); no such year gives `D_c = 0`. Forecast `M30_c x (1 + 0.3 D_c)`, floored at 0, all leads. Cities without an anomaly keep M30. |
| P2 | Level `A = 0.5 x shrunk median + 0.5 x mean half`. **Shrunk 30-year median**: `r_c` = median / mean of the valid years in the 30-year window; `rbar_c` = 300 km Gaussian-kernel mean (leave-one-out) of the other cities' `r_j`; shrunk median = `M30_c x (0.5 r_c + 0.5 rbar_c)` (the city's median-to-mean ratio shrunk halfway toward its neighbors'; own median if no neighbor has `r`). **Mean half**: mean of complete years in the last 30 calendar years (C30) for leads 1-3; for leads 4-7 the mean of complete years in the last 45 years (C45) if the city has >= 10 complete years in the 30-year window and >= 15 in the 45-year window, else C30. A city with < 10 complete years in the 30-year window uses M30 as its mean half. A city with < 10 valid years in the 30-year window gets M30 for the whole level. |
| P3 | P2, then for leads 4-7 and only for cities that use C45, the Fay-Herriot correction `c`. Record R = last 90 calendar years, window W = last 45, complete years only. `y_ct = P_ct / mean_R(P_c) - 1`. Regional reference `g_ct` = 300 km Gaussian-kernel mean of the other cities' `y_jt` in the same year (leave-one-out, cities with data that year). A year counts only if the summed raw kernel weight of those neighbors is >= 0.5 ("enough neighbour weight", about one neighbor within 353 km). Residual `e_ct = y_ct - g_ct`. Local deviation `D_c = mean_W(e) - mean_R(e)`; sampling variance `V_c = s_c^2 (1/n_W - 1/n_R)` with `s_c^2` the variance (ddof 1) of `e` over R (exact for a sub-window mean of independent years). Eligible: `n_W >= 15`, `n_R >= 30`, and the city uses C45. `tau^2 = max(0, mean(D^2) - mean(V))` over eligible cities (0 if fewer than 2). Precision weight `B_c = tau^2 / (tau^2 + V_c)`. The observed deviation `D_c` is replaced by `B_c D_c`, so `c = (B_c - 1) D_c x mean_R(P_c)` inches ("regional part and long-record local mean untouched"). Written value `round(max(0, A + c), 4)`, as the README states. Non-eligible cities: `c = 0`. Note: with `tau^2` floored at 0 the weight is 0 and the window deviation is removed entirely (a change); "no change" holds for sparse / non-eligible cities. This is the README's estimator; the brief's test wording ("tau^2 floored at 0 gives no change") reads it differently, see Deviations. |
| P4 | CRM regional_eb level: `{kind: crm, params: {regions: spectral, n_clusters: 6, flat_level: regional_eb, urban: true}}` (the `crm_s6_eb_urban` row), precipitation only. |
| P5 | Equal-weight mean of P1 and P3 (`swap_metric` with two components). |
| H1 | Same as P1 with difference anomalies `a_ct = H_ct - M30_c`; forecast `M30_c + 0.3 D_c`. |
| H2 | Daily `tmax` of complete daily-maximum years in the 30-year window (cut-off - 29 ... cut-off). Per year: highest and second-highest daily maximum (ties count: if the maximum occurs on two days, the second-highest equals it). City level `L_c` = mean second-highest; city spacing `S_c` = mean (highest - second-highest); both need >= 10 complete years. **Pooled with nearby cities**: `S~_c` = 300 km Gaussian-kernel mean of `S_j` over cities with a spacing, the city itself included (weight 1). Forecast `L_c + S~_c`, all leads. Cities with < 10 complete years (or no daily rows) keep M30. |
| H3 | CRM regional_eb level (same entry as P4), hottest day only. |
| H4 | Equal-weight mean of H1 and H2. |

All numbers above (0.3, 31, 10, 30, 45, 90, 300 km, 360 days, 10 / 15 / 30 year thresholds,
0.5 kernel weight, 0.5 shrinkage) are fixed here and set in `configs/mp_final_precip_hot.yaml`.
The thresholds come from the READMEs where they give one; the shrunk-median rule (0.5), the
0.5 minimum kernel weight, the H2 10-year minimum and the "M30 mean half below 10 complete
years" fallback are my choices, made before any run.

### Not run, and why

- PstarAlu's precipitation harmonic (8-30 year band, national and regional LAD amplitudes): many
  fitted parameters, and the brief excludes it.
- PstarAlu's hottest-day summer-state term (June-August projections at three endpoints): their
  own audit reports negative long-span skill since 1920 for years 4-7.
- PstarAlu's years 1-3 hottest-day residual layer (forward-calibrated LAD weights per lead):
  many fitted parameters.
- Alternative readings of the shrunk median, the Fay-Herriot correction or the H2 pooling: one
  reading each, fixed above.

### Selection rule

As written in the config header (Section 4), applied with
`proto_star.robustness.apply_selection_rule` on window `all`: once for `total_precip_in`
(P1-P5) and once for `hottest_day_temp` (H1-H4), default `p0_lead_split3`.

## Runs (every variant tried)

Variants tried: **9 candidates** (P1-P5, H1-H4) plus the default `p0_lead_split3` and the
reference `thirty_year_mean`; each was run once. No failed or buggy runs, no reruns, and no
variant was added or changed after results were seen.

| Run | Command | Output | Wall time |
|---|---|---|---|
| Official folds 1980, 1995, 2011 | `uv run proto-star climate-trial configs/mp_final_precip_hot.yaml --record` | `runs/trials/20261109-222359_final_precip_hot/` | 125 s |
| 27 rolling origins 1985-2011 | `uv run python scripts/robustness_origins.py configs/mp_final_precip_hot.yaml --origins rolling27 --default p0_lead_split3 --out runs/robustness/final_precip_hot` | `runs/robustness/final_precip_hot/` | 1723 s |

Checks done before the runs (not used to choose anything):

- Implementation check of P3 against PstarAlu's own README description of its 2018-origin
  step (data through 2018 only): our code puts 207 of 210 cities on the 45-year level and
  adjusts 206, mean absolute change 0.262 inch, at most 5.56% of a city's level. The README
  states 207, 206, 0.26 inch and 5.6%. This confirms the `(B - 1) D` reading of the correction.
- Metric isolation on the real official folds: for every candidate only its own metric's MAE
  differs from `p0_lead_split3` (the other three are identical), besides the unit tests.

## Results and selection rule

Skill is in percent against `thirty_year_mean`; raw score is the official score without its
floor (mean over folds / origins). The default has 0 skill on both metrics (it is the
30-year mean there). Win rate = share of the 27 origins where the candidate's skill on its
metric beats the default's (paired, window `all`). Selection uses `all`
(`proto_star.robustness.apply_selection_rule`, ADR 0009); years 1-3 and 4-7 are reported only.

#### total_precip_in: skill (%) and raw score, mean over folds

| method | set | skill all | skill years_1_3 | skill years_4_7 | raw all | raw years_1_3 | raw years_4_7 | win rate all (27) |
|---|---|---|---|---|---|---|---|---|
| p0_lead_split3 | official 3 | 0.000 | 0.000 | 0.000 | 4.691 | 1.316 | 7.117 |  |
| p0_lead_split3 | rolling 27 | 0.000 | 0.000 | 0.000 | 4.721 | 3.468 | 5.387 |  |
| p1_nudge | official 3 | -0.161 | -0.347 | -0.001 | 4.651 | 1.229 | 7.117 |  |
| p1_nudge | rolling 27 | 0.286 | 0.397 | 0.201 | 4.793 | 3.567 | 5.438 | 70% (19/27) |
| p2_two_half | official 3 | 0.217 | -0.103 | 0.506 | 4.745 | 1.290 | 7.244 |  |
| p2_two_half | rolling 27 | 0.179 | 0.201 | 0.149 | 4.766 | 3.518 | 5.425 | 48% (13/27) |
| p3_two_half_fh | official 3 | 0.320 | -0.103 | 0.670 | 4.771 | 1.290 | 7.285 |  |
| p3_two_half_fh | rolling 27 | 0.313 | 0.201 | 0.383 | 4.799 | 3.518 | 5.483 | 52% (14/27) |
| p4_crm_eb | official 3 | 0.064 | 0.066 | 0.069 | 4.707 | 1.332 | 7.135 |  |
| p4_crm_eb | rolling 27 | 0.039 | 0.024 | 0.052 | 4.731 | 3.474 | 5.400 | 63% (17/27) |
| p5_mean_p1_p3 | official 3 | 0.214 | -0.152 | 0.514 | 4.744 | 1.278 | 7.246 |  |
| p5_mean_p1_p3 | rolling 27 | 0.447 | 0.388 | 0.486 | 4.833 | 3.565 | 5.509 | 96% (26/27) |

#### Rule for total_precip_in (window all, skill in %)

| candidate | 1. official mean vs default | 2. 27-origin mean vs default | 3. win rate >= 60% | passes |
|---|---|---|---|---|
| p1_nudge | -0.161 vs 0.000 (no) | 0.286 vs 0.000 (yes) | 70% (yes) | no |
| p2_two_half | 0.217 vs 0.000 (yes) | 0.179 vs 0.000 (yes) | 48% (no) | no |
| p3_two_half_fh | 0.320 vs 0.000 (yes) | 0.313 vs 0.000 (yes) | 52% (no) | no |
| p4_crm_eb | 0.064 vs 0.000 (yes) | 0.039 vs 0.000 (yes) | 63% (yes) | yes |
| p5_mean_p1_p3 | 0.214 vs 0.000 (yes) | 0.447 vs 0.000 (yes) | 96% (yes) | yes |

Chosen for total_precip_in: **p5_mean_p1_p3**

#### hottest_day_temp: skill (%) and raw score, mean over folds

| method | set | skill all | skill years_1_3 | skill years_4_7 | raw all | raw years_1_3 | raw years_4_7 | win rate all (27) |
|---|---|---|---|---|---|---|---|---|
| p0_lead_split3 | official 3 | 0.000 | 0.000 | 0.000 | 4.691 | 1.316 | 7.117 |  |
| p0_lead_split3 | rolling 27 | 0.000 | 0.000 | 0.000 | 4.721 | 3.468 | 5.387 |  |
| h1_nudge | official 3 | 0.183 | 0.606 | -0.096 | 4.737 | 1.467 | 7.093 |  |
| h1_nudge | rolling 27 | 0.474 | 0.591 | 0.415 | 4.840 | 3.616 | 5.491 | 93% (25/27) |
| h2_second_high | official 3 | 0.326 | 0.556 | 0.157 | 4.772 | 1.455 | 7.157 |  |
| h2_second_high | rolling 27 | 0.498 | 0.389 | 0.618 | 4.846 | 3.565 | 5.542 | 93% (25/27) |
| h3_crm_eb | official 3 | 0.059 | 0.061 | 0.054 | 4.706 | 1.331 | 7.131 |  |
| h3_crm_eb | rolling 27 | 0.075 | 0.075 | 0.069 | 4.740 | 3.486 | 5.405 | 96% (26/27) |
| h4_mean_h1_h2 | official 3 | 0.425 | 0.729 | 0.234 | 4.797 | 1.498 | 7.176 |  |
| h4_mean_h1_h2 | rolling 27 | 0.644 | 0.646 | 0.683 | 4.882 | 3.629 | 5.558 | 100% (27/27) |

#### Rule for hottest_day_temp (window all, skill in %)

| candidate | 1. official mean vs default | 2. 27-origin mean vs default | 3. win rate >= 60% | passes |
|---|---|---|---|---|
| h1_nudge | 0.183 vs 0.000 (yes) | 0.474 vs 0.000 (yes) | 93% (yes) | yes |
| h2_second_high | 0.326 vs 0.000 (yes) | 0.498 vs 0.000 (yes) | 93% (yes) | yes |
| h3_crm_eb | 0.059 vs 0.000 (yes) | 0.075 vs 0.000 (yes) | 96% (yes) | yes |
| h4_mean_h1_h2 | 0.425 vs 0.000 (yes) | 0.644 vs 0.000 (yes) | 100% (yes) | yes |

Chosen for hottest_day_temp: **h4_mean_h1_h2**

### Reading

- Precipitation: P1 loses on the official folds (fails condition 1); P2 and P3 gain on average
  but win at only 48% / 52% of origins (fail condition 3). P4 and P5 pass; the rule picks
  **P5** (highest 27-origin mean, +0.45 skill points, 26 of 27 origins). P5's years 1-3 skill
  on the official folds is negative (-0.15), inherited from P1; it is not used for selection.
- Hottest day: all four pass; the rule picks **H4** (+0.64 skill points over 27 origins, 27 of
  27 origins; +0.43 on the official folds). H1 is slightly negative in official years 4-7.
- Gains are small: 1% of one metric's skill is 0.25 score points, so P5 adds about 0.11 and
  H4 about 0.16 raw-score points over 27 origins. Consecutive origins share target years, so
  the win rates are screening evidence, not independent tests.

## Deviations

- Fay-Herriot with `tau^2` floored at 0: by the README's estimator the precision weight is 0
  and the window deviation is removed fully (a change). The brief expected "no change" there;
  I kept the README reading (fixed before the runs, and matched by the 2018-origin check
  above). The tests assert: `tau^2` is floored at 0 (and is 0 with fewer than 2 cities);
  weight 0 at `tau^2 = 0`; no correction for sparse cities or without neighbour weight.

## Recorded run (written by `climate-trial --record`)

Final round, agent P: precipitation and hottest-day components of Tatakae, PstarAlu and the CRM; each replaces one metric of lead_split3 only.


### What was used

| Item | Value |
|---|---|
| Date | 2026-11-09 |
| Config | `configs/mp_final_precip_hot.yaml` |
| Code version | `965e1c8` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `p0_lead_split3` |

### Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_final_precip_hot.yaml
```

### Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| p0_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| p1_nudge | total_precip_in = 1 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| p2_two_half | total_precip_in = 1 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| p3_two_half_fh | total_precip_in = 1 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| p4_crm_eb | total_precip_in = 1 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| p5_mean_p1_p3 | total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| h1_nudge | hottest_day_temp = 1 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| h2_second_high | hottest_day_temp = 1 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| h3_crm_eb | hottest_day_temp = 1 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| h4_mean_h1_h2 | hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |

### Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

#### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_nudge | 4.74 | 9.86 | 0.0 | 0.18 | 8.91 | 3 | 3 |
| h2_second_high | 4.77 | 9.86 | 0.0 | 0.33 | 8.91 | 2 | 3 |
| h3_crm_eb | 4.71 | 9.86 | 0.0 | 0.06 | 8.91 | 3 | 3 |
| h4_mean_h1_h2 | 4.8 | 9.86 | 0.0 | 0.43 | 8.91 | 3 | 3 |
| p0_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| p1_nudge | 4.65 | 9.86 | -0.16 | 0.0 | 8.91 | 2 | 3 |
| p2_two_half | 4.75 | 9.86 | 0.22 | 0.0 | 8.91 | 2 | 3 |
| p3_two_half_fh | 4.77 | 9.86 | 0.32 | 0.0 | 8.91 | 2 | 3 |
| p4_crm_eb | 4.71 | 9.86 | 0.06 | 0.0 | 8.91 | 3 | 3 |
| p5_mean_p1_p3 | 4.74 | 9.86 | 0.21 | 0.0 | 8.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_nudge | 1.47 | -0.09 | 0.0 | 0.61 | 5.35 | 3 | 3 |
| h2_second_high | 1.46 | -0.09 | 0.0 | 0.56 | 5.35 | 3 | 3 |
| h3_crm_eb | 1.33 | -0.09 | 0.0 | 0.06 | 5.35 | 3 | 3 |
| h4_mean_h1_h2 | 1.5 | -0.09 | 0.0 | 0.73 | 5.35 | 3 | 3 |
| p0_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| p1_nudge | 1.23 | -0.09 | -0.35 | 0.0 | 5.35 | 3 | 3 |
| p2_two_half | 1.29 | -0.09 | -0.1 | 0.0 | 5.35 | 3 | 3 |
| p3_two_half_fh | 1.29 | -0.09 | -0.1 | 0.0 | 5.35 | 3 | 3 |
| p4_crm_eb | 1.33 | -0.09 | 0.07 | 0.0 | 5.35 | 3 | 3 |
| p5_mean_p1_p3 | 1.28 | -0.09 | -0.15 | 0.0 | 5.35 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| h1_nudge | 7.09 | 17.73 | 0.0 | -0.1 | 10.74 | 2 | 3 |
| h2_second_high | 7.16 | 17.73 | 0.0 | 0.16 | 10.74 | 2 | 3 |
| h3_crm_eb | 7.13 | 17.73 | 0.0 | 0.05 | 10.74 | 2 | 3 |
| h4_mean_h1_h2 | 7.18 | 17.73 | 0.0 | 0.23 | 10.74 | 2 | 3 |
| p0_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| p1_nudge | 7.12 | 17.73 | -0.0 | 0.0 | 10.74 | 2 | 3 |
| p2_two_half | 7.24 | 17.73 | 0.51 | 0.0 | 10.74 | 2 | 3 |
| p3_two_half_fh | 7.28 | 17.73 | 0.67 | 0.0 | 10.74 | 2 | 3 |
| p4_crm_eb | 7.13 | 17.73 | 0.07 | 0.0 | 10.74 | 2 | 3 |
| p5_mean_p1_p3 | 7.25 | 17.73 | 0.51 | 0.0 | 10.74 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

#### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| h1_nudge | 0.06 | 4.85 | 9.3 |
| h2_second_high | -0.04 | 5.05 | 9.31 |
| h3_crm_eb | 0.05 | 4.85 | 9.21 |
| h4_mean_h1_h2 | 0.05 | 4.99 | 9.35 |
| p0_lead_split3 | 0.05 | 4.83 | 9.2 |
| p1_nudge | -0.03 | 4.77 | 9.21 |
| p2_two_half | -0.11 | 5.25 | 9.1 |
| p3_two_half_fh | -0.14 | 5.3 | 9.15 |
| p4_crm_eb | 0.07 | 4.82 | 9.23 |
| p5_mean_p1_p3 | -0.05 | 5.08 | 9.2 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
