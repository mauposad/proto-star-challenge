# Trial: final_temp (final round, agent T, average temperature)

Status: DONE; rule result T0 (no component passes). Pre-registration written 2026-11-09 22:15 ET, before any candidate code ran. The
sections "Sources", "Interpretations and fixed parameters" and "Not run" below were fixed
before any result was seen; results are appended below them later and do not edit them.

Config: `configs/mp_final_temp.yaml`. Each candidate replaces `annual_avg_temp` only (kind
`swap_metric`, base `lead_blend` = lead_split3); the other three metrics stay lead_split3's
(metric-isolation test in `tests/test_final_temp.py`). Selection rule: Section 4, written in
the config header, applied with `proto_star.robustness.apply_selection_rule(...,
metric="annual_avg_temp")`; primary window `all` (ADR 0009). No leaderboard score, Live Score
or 2019-2025 value is used for anything; the numbers quoted in the two READMEs are ignored.

## Sources (methods re-implemented from README text only; no code downloaded)

| Team | Dataset (CC BY 4.0) | Commit read | Sections used |
|---|---|---|---|
| Tatakae (Mashrafi Mahmud Rafi, @ironMan334) | `ironMan334/protostar-climate-team-tatakae` | `f18c1178c1b97566c75facc94c886184ebaa2a10` | Method ("recent normal + regional warming", "region + departure"), What did not work |
| PstarAlu (Nibedita Biswal, @nbiswal-star) | `nbiswal-star/protostar-climate-submission` | `9e51c3ef5d3178ca194f28e2c4134201c1bf9675` | Method (Average temperature), Validation |

External data (T7 only): HadCRUT4 annual global mean, version HadCRUT.4.6.0.0
(`HadCRUT.4.6.0.0.annual_ns_avg.txt`), from the Internet Archive snapshot of the Met Office
file taken 2019-02-09 18:08:36 UTC (the file date PstarAlu cites). Rows after 2018 are
dropped in memory before anything is written or shown. Morice et al. (2012), J. Geophys.
Res. 117, D08101, doi:10.1029/2011JD017187. Details in docs/data.md.

## Interpretations and fixed parameters (fixed before running)

Common: "valid year" = the organizer's missing-days rule (`annual_to_long`). All windows end
at the fold cut-off. "The 32 nearest cities" = the city itself plus its 31 nearest other
cities by great-circle distance (Tatakae uses "32 closest cities" for the region and "31
nearest neighbours" for the rain nudge, which reads as 31 neighbours + the city). Any city a
component cannot forecast (too few valid years) falls back to the pooled-trend temperature
(levels 10/15, non-negative pooled 40-year slope), so every scored row gets a value.

- **T0 `t0_lead_split3`**: lead_split3 unchanged (`lead_blend`, defaults).
- **T1 `t1_recent_normal`** (Tatakae, view 1): level = mean of the city's last 15 valid
  years; mid-year = mean of those 15 years. City slope = OLS slope of annual temperature on
  year over the 40 calendar years ending at the cut-off (>= 10 valid years). Regional rate =
  mean slope of the 32 nearest cities (self + 31) that have a slope. Forecast = level + rate
  x (year - mid-year). No floor on the rate (Tatakae sets none), so at the 1980 cut-off the
  rate can be negative.
- **T2 `t2_region_dep`** (Tatakae, view 2): anomaly = value - city mean of the 30 years
  ending at the cut-off (>= 10 valid years, `own_anomalies`). Region anomaly R(t) = equal-
  weight mean of the anomalies of the 32 nearest cities (self + 31) with data that year.
  Departure D(t) = city anomaly - R(t); departure forecast = mean of D over the city's last
  5 valid years. R is carried forward by an OLS line fitted to R(t) over the 30 years ending
  at the cut-off. View = city 30-year mean + R_line(year) + departure. T2 = 0.75 x view +
  0.25 x T1.
- **T3 `t3_two_scale`** (PstarAlu two-scale departure decay). Base = pooled-trend
  temperature (levels 10/15, non-negative pooled 40-year slope; the champion's trend
  member). Anomaly a(c,t) = value - city 30-year mean (as T2). National pattern n(t) =
  area-weighted median of a(.,t) over cities with data. **Area weights (PstarAlu does not
  define them):** declustering by inverse local density, w_c = 1 / (number of cities within
  300 km of c, the city included), normalized; weighted median = smallest value whose
  cumulative weight reaches half the total. Departure d = a - n. Regional part R(c,t) =
  area-weighted mean of d over the cities within 300 km (the city included); local part
  L = d - R. Persistence per part: demean each city's part over its valid years in the
  30-year window; pooled lag-1 OLS phi_hat = sum x_t x_{t-1} / sum x_{t-1}^2 over all
  cities and consecutive valid pairs; bias correction (Kendall 1954, AR(1) with estimated
  mean) phi = phi_hat + (1 + 3 phi_hat) / n, n = mean number of valid years per city series;
  phi clipped to [0, 0.99]. Recent departure to decay, per part: its value in the city's last
  valid year T minus its mean over the years the base level uses (0.5 x mean over the last
  10 valid years + 0.5 x mean over the last 15), so the departure already inside the level
  is not counted twice. Forecast = base + phi_R^h x e_R + phi_L^h x e_L, h = year - T.
  Reading of the brief: both parts decay in every lead 1-7. PstarAlu's README uses one
  single persistence in years 1-3 and the split only in years 4-7; that variant is recorded
  under "Not run".
- **T4 `t4_mean_t0_t2`**: equal-weight mean of T0's and T2's temperature.
- **T5 `t5_mean_t0_t2_t3`**: equal-weight mean of T0, T2, T3 temperature.
- **T6 `t6_t5_ridge13`** (reading 1, the one run): leads 1-3 = lead_split3 temperature
  (0.5 trend + 0.5 ridge), leads 4-7 = T5. Reading 2 (not run): leads 1-3 = 0.5 x ridge +
  0.5 x mean(trend, T2, T3), i.e. the ridge replaces half of T5 in years 1-3.
- **T7 `t7_gmst_scaling`** (PstarAlu "global-pattern scaling"; ONE specification, the only
  one run): GMST G(y) = HadCRUT4.6.0.0 annual median anomaly (column 2), years <= fold
  cut-off only, loaded through `load_hadcrut4_annual(cutoff_year)` (assert_weather_cutoff
  with the fold cut-off). Scaling window: the 40 calendar years ending at the cut-off; per
  city, OLS slope beta_c of valid annual temperature on G (>= 20 valid years) and its
  standard error s_c. Shrinkage toward the regional mean slope m_c (mean beta of the 32
  nearest cities, self + 31): empirical Bayes, tau^2 = max(0, var(beta_c - m_c) -
  mean(s_c^2)), beta*_c = m_c + tau^2 / (tau^2 + s_c^2) x (beta_c - m_c); cities without a
  slope get m_c. GMST forecast: OLS line on G over the 30 years ending at the cut-off,
  slope floored at 0 (the team's trend convention, trend.py), G_hat(y) = line value.
  City level: mean of the last 15 valid years, with G_bar_c = mean observed G over those
  same years. Forecast = level + beta*_c x (G_hat(year) - G_bar_c).
- **T7b `t7_mean_best`**: equal-weight mean of T7 and the component the Section 4 rule picks
  from T0-T6 (T0 if none passes). Its params are filled in mechanically after the T0-T6 runs.

## Not run (ideas recorded, not tested)

- T3 with PstarAlu's exact lead split (one persistence in years 1-3, two-scale in 4-7).
- T6 reading 2 (above).
- T7 with other windows, a pooled (not shrunk) slope, or an unfloored GMST trend.
- Tatakae's daily-shape CDD and rain/hottest-day nudges (other metrics, not agent T's).

## Runs log (appended after the runs; the sections above are unchanged)

Variants tried: **9 candidate rows (T1-T7, T7b) plus T0, every one run once with its
pre-registered specification. No failed or buggy run, nothing re-run with changed code.**
Runs, in order:

1. Run 1 (2026-11-09 22:23 ET), T0-T7 without T7b: official folds `runs/trials/20261109-222330_final_temp`
   (110 s); 27 origins `runs/robustness/final_temp` (1,652 s). Rule on T1-T6 alone: no
   component passes, so "best of T0-T6" = **T0**.
2. `t7_mean_best` row added mechanically = equal-weight mean of T0 and T7 (config comment
   says so). Run 2 (22:53 ET), all rows: official folds `runs/trials/20261109-225348_final_temp`
   (116 s); 27 origins rewritten to `runs/robustness/final_temp` (1,581 s). Rows T0-T7 are
   identical in run 1 and run 2 (checked by diff of the recorded tables).

Finding from a unit test, before any run (not a code change): the pre-registered Kendall
correction `phi_hat + (1 + 3 phi_hat)/n` slightly over-corrects the *pooled* ratio
estimator. In a simulation (phi 0.5, 30 years) raw is about 0.45 and corrected about 0.52.
The formula was kept as registered; it is still closer to the truth than the raw estimate.
In-fold persistence: regional 0.165 / local 0.654 at the 1980 cut-off, 0.176 / 0.628 at 2011.

HadCRUT4 license (found while writing docs/data.md): Crown copyright, "private study and
scientific research" use; not the Open Government Licence. The file stays local (git-ignored).

### Selection rule (Section 4, `apply_selection_rule`, metric annual_avg_temp, window all)

Skill in percent. c1 = official mean above T0's, c2 = 27-origin mean above T0's, c3 = paired win rate >= 0.6.

| candidate | official mean | T0 | 27-origin mean | T0 | win rate | c1 | c2 | c3 | passes |
|---|---|---|---|---|---|---|---|---|---|
| t1_recent_normal | 2.45 | 9.86 | 9.33 | 11.48 | 0.26 | no | no | no | no |
| t2_region_dep | 2.44 | 9.86 | 11.36 | 11.48 | 0.41 | no | no | no | no |
| t3_two_scale | 9.75 | 9.86 | 12.16 | 11.48 | 0.67 | no | yes | yes | no |
| t4_mean_t0_t2 | 6.87 | 9.86 | 11.95 | 11.48 | 0.63 | no | yes | yes | no |
| t5_mean_t0_t2_t3 | 8.04 | 9.86 | 12.19 | 11.48 | 0.74 | no | yes | yes | no |
| t6_t5_ridge13 | 8.40 | 9.86 | 11.70 | 11.48 | 0.52 | no | yes | no | no |
| t7_gmst_scaling | 7.31 | 9.86 | 10.72 | 11.48 | 0.33 | no | no | no | no |
| t7_mean_best | 8.83 | 9.86 | 11.58 | 11.48 | 0.52 | no | yes | no | no |

**Rule result: no component passes; temperature stays T0 (lead_split3).**

### Temperature skill (%) and raw score, official folds (mean of 1980, 1995, 2011)

| method | temp all | temp 1-3 | temp 4-7 | raw all | raw 1-3 | raw 4-7 |
|---|---|---|---|---|---|---|
| t0_lead_split3 | 9.86 | -0.09 | 17.73 | 4.69 | 1.32 | 7.12 |
| t1_recent_normal | 2.45 | -5.31 | 8.82 | 2.84 | 0.01 | 4.89 |
| t2_region_dep | 2.44 | -4.04 | 8.01 | 2.84 | 0.33 | 4.69 |
| t3_two_scale | 9.75 | -0.51 | 18.00 | 4.66 | 1.21 | 7.19 |
| t4_mean_t0_t2 | 6.87 | -1.37 | 13.62 | 3.95 | 1.00 | 6.09 |
| t5_mean_t0_t2_t3 | 8.04 | -0.82 | 15.24 | 4.24 | 1.13 | 6.50 |
| t6_t5_ridge13 | 8.40 | -0.09 | 15.24 | 4.33 | 1.32 | 6.50 |
| t7_gmst_scaling | 7.31 | -3.89 | 16.14 | 4.05 | 0.36 | 6.72 |
| t7_mean_best | 8.83 | -1.76 | 17.21 | 4.43 | 0.90 | 6.99 |

Temperature skill (%) per official fold, window all:

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| t0_lead_split3 | -1.67 | 14.82 | 16.42 |
| t1_recent_normal | -19.78 | 10.89 | 16.24 |
| t2_region_dep | -19.47 | 11.21 | 15.59 |
| t3_two_scale | -0.85 | 12.60 | 17.50 |
| t4_mean_t0_t2 | -8.85 | 13.31 | 16.16 |
| t5_mean_t0_t2_t3 | -5.72 | 13.17 | 16.67 |
| t6_t5_ridge13 | -5.51 | 14.61 | 16.09 |
| t7_gmst_scaling | -5.55 | 11.49 | 15.97 |
| t7_mean_best | -3.36 | 13.44 | 16.41 |

### Temperature skill (%) and raw score, 27 rolling origins (1985-2011)

| method | temp all | temp 1-3 | temp 4-7 | raw all | raw 1-3 | raw 4-7 |
|---|---|---|---|---|---|---|
| t0_lead_split3 | 11.48 | 8.21 | 12.94 | 4.72 | 3.47 | 5.39 |
| t1_recent_normal | 9.33 | 6.49 | 10.34 | 4.18 | 3.04 | 4.74 |
| t2_region_dep | 11.36 | 8.11 | 12.44 | 4.69 | 3.44 | 5.26 |
| t3_two_scale | 12.16 | 9.15 | 13.28 | 4.89 | 3.70 | 5.47 |
| t4_mean_t0_t2 | 11.95 | 8.80 | 13.19 | 4.84 | 3.62 | 5.45 |
| t5_mean_t0_t2_t3 | 12.19 | 9.21 | 13.32 | 4.90 | 3.72 | 5.48 |
| t6_t5_ridge13 | 11.70 | 8.21 | 13.32 | 4.78 | 3.47 | 5.48 |
| t7_gmst_scaling | 10.72 | 7.69 | 11.68 | 4.53 | 3.34 | 5.07 |
| t7_mean_best | 11.58 | 8.63 | 12.68 | 4.75 | 3.57 | 5.32 |

Paired win rate vs T0 (temperature skill, 27 origins). The last column is the largest
absolute skill difference vs T0 on the other three metrics; it is 0 for every row, so metric
isolation holds on real data.

| method | all | 1-3 | 4-7 | other metrics max abs diff |
|---|---|---|---|---|
| t1_recent_normal | 0.26 | 0.41 | 0.19 | 0 |
| t2_region_dep | 0.41 | 0.48 | 0.44 | 0 |
| t3_two_scale | 0.67 | 0.59 | 0.96 | 0 |
| t4_mean_t0_t2 | 0.63 | 0.59 | 0.44 | 0 |
| t5_mean_t0_t2_t3 | 0.74 | 0.63 | 0.52 | 0 |
| t6_t5_ridge13 | 0.52 | 0.00 | 0.52 | 0 |
| t7_gmst_scaling | 0.33 | 0.48 | 0.26 | 0 |
| t7_mean_best | 0.52 | 0.52 | 0.37 | 0 |

### Reading (why)

- T3 and T5 beat T0 on the 27 origins (+0.68 and +0.71 skill points, win rates 0.67 and
  0.74). They fail condition 1 because of the 1995 official fold (T3 12.60 vs 14.82). T3
  wins at 1980 and 2011. Under the pre-registered rule they do not replace T0.
- T1 and T2 lose badly at the 1980 cut-off (about -19.5%), because Tatakae's unfloored
  regional 40-year rate is negative there (mid-century cooling). This was expected when
  the "no floor" choice was registered. On the 27 origins (1985 on) T2 is close to T0.
- T7 (GMST scaling) is weaker than the pooled trend in years 1-3 (the 15-year level with
  no ridge) and does not help years 4-7 either.
- T6 equals T0 in years 1-3 by construction (win rate 0.00 there = ties) and T5 in 4-7.


## Auto-generated climate-trial record (run 2, `--record`)

Final round, agent T: re-implemented temperature components of Tatakae and PstarAlu, each replacing lead_split3's annual_avg_temp only, with pre-registered combinations.


### What was used

| Item | Value |
|---|---|
| Date | 2026-11-09 |
| Config | `configs/mp_final_temp.yaml` |
| Code version | `965e1c8` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `t0_lead_split3` |

### Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_final_temp.yaml
```

### Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| t0_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| t1_recent_normal | annual_avg_temp = 1 x [final_temp_recent_normal: Tatakae recent normal: last-15-valid-year mean + regional warming rate (mean 40-year slope of the 32 nearest cities, self included) x years from the window mid-year]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t2_region_dep | annual_avg_temp = 1 x [final_temp_region_departure: Tatakae region + departure: 0.75 x [city 30-year mean + 32-city region anomaly on its 30-year line + last-5-year departure] + 0.25 x recent normal]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t3_two_scale | annual_avg_temp = 1 x [final_temp_two_scale: PstarAlu two-scale: pooled-trend temperature (levels [10, 15], 40-year slope) + regional (within 300 km) and local recent departures from the area-weighted national median, each decaying by its own pooled bias-corrected AR(1)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t4_mean_t0_t2 | annual_avg_temp = 0.5 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.5 x [final_temp_region_departure: Tatakae region + departure: 0.75 x [city 30-year mean + 32-city region anomaly on its 30-year line + last-5-year departure] + 0.25 x recent normal]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t5_mean_t0_t2_t3 | annual_avg_temp = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [final_temp_region_departure: Tatakae region + departure: 0.75 x [city 30-year mean + 32-city region anomaly on its 30-year line + last-5-year departure] + 0.25 x recent normal]; 0.33 x [final_temp_two_scale: PstarAlu two-scale: pooled-trend temperature (levels [10, 15], 40-year slope) + regional (within 300 km) and local recent departures from the area-weighted national median, each decaying by its own pooled bias-corrected AR(1)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t6_t5_ridge13 | annual_avg_temp = 1 x [final_temp_lead_switch: leads 1-3 from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; later leads from [swap_metric: annual_avg_temp = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [final_temp_region_departure: Tatakae region + departure: 0.75 x [city 30-year mean + 32-city region anomaly on its 30-year line + last-5-year departure] + 0.25 x recent normal]; 0.33 x [final_temp_two_scale: PstarAlu two-scale: pooled-trend temperature (levels [10, 15], 40-year slope) + regional (within 300 km) and local recent departures from the area-weighted national median, each decaying by its own pooled bias-corrected AR(1)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t7_gmst_scaling | annual_avg_temp = 1 x [final_temp_gmst_scaling: GMST scaling: city temperature on HadCRUT4 GMST over 40 years, slope shrunk (empirical Bayes) toward the 32-city regional mean; GMST from its non-negative 30-year line; level = last 15 valid years]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| t7_mean_best | annual_avg_temp = 0.5 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.5 x [final_temp_gmst_scaling: GMST scaling: city temperature on HadCRUT4 GMST over 40 years, slope shrunk (empirical Bayes) toward the 32-city regional mean; GMST from its non-negative 30-year line; level = last 15 valid years]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |

### Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| t0_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| t1_recent_normal | 2.84 | 2.45 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t2_region_dep | 2.84 | 2.44 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t3_two_scale | 4.66 | 9.75 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| t4_mean_t0_t2 | 3.95 | 6.87 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t5_mean_t0_t2_t3 | 4.24 | 8.04 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t6_t5_ridge13 | 4.33 | 8.4 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t7_gmst_scaling | 4.05 | 7.31 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| t7_mean_best | 4.43 | 8.83 | 0.0 | 0.0 | 8.91 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| t0_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| t1_recent_normal | 0.01 | -5.31 | 0.0 | 0.0 | 5.35 | 1 | 3 |
| t2_region_dep | 0.33 | -4.04 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| t3_two_scale | 1.21 | -0.51 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| t4_mean_t0_t2 | 1.0 | -1.37 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| t5_mean_t0_t2_t3 | 1.13 | -0.82 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| t6_t5_ridge13 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| t7_gmst_scaling | 0.36 | -3.89 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| t7_mean_best | 0.9 | -1.76 | 0.0 | 0.0 | 5.35 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| t0_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t1_recent_normal | 4.89 | 8.82 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t2_region_dep | 4.69 | 8.01 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t3_two_scale | 7.19 | 18.0 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t4_mean_t0_t2 | 6.09 | 13.62 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t5_mean_t0_t2_t3 | 6.5 | 15.24 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t6_t5_ridge13 | 6.5 | 15.24 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t7_gmst_scaling | 6.72 | 16.14 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| t7_mean_best | 6.99 | 17.21 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| t0_lead_split3 | 0.05 | 4.83 | 9.2 |
| t1_recent_normal | -4.48 | 3.84 | 9.16 |
| t2_region_dep | -4.4 | 3.92 | 8.99 |
| t3_two_scale | 0.25 | 4.27 | 9.47 |
| t4_mean_t0_t2 | -1.75 | 4.45 | 9.14 |
| t5_mean_t0_t2_t3 | -0.97 | 4.41 | 9.26 |
| t6_t5_ridge13 | -0.91 | 4.77 | 9.12 |
| t7_gmst_scaling | -0.92 | 3.99 | 9.09 |
| t7_mean_best | -0.38 | 4.48 | 9.2 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
