# Final round: other teams' methods as per-metric components (report)

Date 2026-11-09. Branch `agent/final-round` (from `origin/agent/crm` at `965e1c8`), nothing
committed. Master content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1`
(confirmed). No 2019-2025 data and no leaderboard score was used for any choice. The selection
column is `all` (all 7 forecast years, ADR 0009, status proposed).

**Result.** The pre-registered rule keeps lead_split3 for temperature (T0) and CDD (C0), and takes
two component means for the two metrics that had zero skill: precipitation P5 (mean of
Tatakae's neighbor nudge and PstarAlu's two-half level with Fay-Herriot shrinkage) and hottest
day H4 (mean of Tatakae's nudge and PstarAlu's second-highest anchor). The combined row R4
beats lead_split3 on the official folds (4.85 vs 4.69), over 27 origins (4.99 vs 4.72) and at
27 of 27 origins, so it is the new submission candidate. The gain is small (about +0.16 /
+0.27 points), and it comes entirely from two metrics that sit near zero skill.

## 1. References (Section 1, step 4)

Official folds (1980, 1995, 2011), raw score all / years 1-3 / years 4-7; all match the logged
values exactly.

| forecaster | official | logged | 27 origins |
|---|---|---|---|
| trend_level10_15_sensitivity | 4.14 / 0.33 / 6.92 | 4.14 / 0.33 / 6.92 | 4.64 / 3.21 / 5.35 |
| h2_mean_cdd | 4.41 / 0.70 / 7.12 | 4.41 / 0.70 / 7.12 | 4.67 / 3.27 / 5.39 |
| lead_split3 | 4.69 / 1.32 / 7.12 | 4.69 / 1.32 / 7.12 | 4.72 / 3.47 / 5.39 |
| crm_s6_eb_urban | 4.39 / 0.51 / 7.23 | 4.39 / 0.51 / 7.23 | 4.72 / 3.33 / 5.41 |

lead_split3 was not on GitHub or in any local branch or stash. It was ported from
`hf://datasets/corbe19/protostar-climate-MKDir-lead` (revision `0449d70`: `code/trial.yaml`,
`code/evidence/lead_blend.md`, `pooled_p09_p14.py`, `_pooled_features.py`) as one kind,
`lead_blend` (`src/proto_star/forecasters/lead_blend.py`, `_pooled_ridge.py`,
`_pooled_features.py`). It also reproduces every per-metric skill and per-fold score of the
logged table. Runs: `runs/trials/20261109-215713_final_references`,
`runs/robustness/final_references`.

Setup added: `--origins rolling27` / `--default` / `--out` in `scripts/robustness_origins.py`
(`proto_star.robustness`: 27 origins 1985-2011, paired differences, the Section 4 rule as
`apply_selection_rule`), `proto_star.neighbors` (k nearest by great-circle distance, Gaussian
kernel weights, train-only anomalies and departures), `proto_star.data.daily_fold` (daily rows
capped at the fold cut-off), and the `swap_metric` kind (one metric replaced, the others kept).

## 2. Components

Raw score = official score without its floor; skill per metric in %; "27 origins" = cut-offs
1985-2011, 7-year horizon, only target years up to 2018. Win rate = share of the 27 origins
where the candidate's skill on the tested metric is strictly above the default's. In every
row the other three metrics equal the default exactly (metric isolation, tested in code and
visible below).

### 2.1 Average temperature (agent T; default T0 = lead_split3)

| ID | set | raw all | raw y1-3 | raw y4-7 | temp % | precip % | hottest % | cdd % | win rate vs default (annual_avg_temp) |
|---|---|---|---|---|---|---|---|---|---|
| t0_lead_split3 | official | 4.69 | 1.32 | 7.12 | 9.86 | 0.00 | 0.00 | 8.91 |  |
| t0_lead_split3 | 27 origins | 4.72 | 3.47 | 5.39 | 11.48 | 0.00 | 0.00 | 7.41 |  |
| t1_recent_normal | official | 2.84 | 0.01 | 4.89 | 2.45 | 0.00 | 0.00 | 8.91 |  |
| t1_recent_normal | 27 origins | 4.18 | 3.04 | 4.74 | 9.33 | 0.00 | 0.00 | 7.41 | 7/27 = 26% |
| t2_region_dep | official | 2.84 | 0.33 | 4.69 | 2.44 | 0.00 | 0.00 | 8.91 |  |
| t2_region_dep | 27 origins | 4.69 | 3.44 | 5.26 | 11.36 | 0.00 | 0.00 | 7.41 | 11/27 = 41% |
| t3_two_scale | official | 4.66 | 1.21 | 7.19 | 9.75 | 0.00 | 0.00 | 8.91 |  |
| t3_two_scale | 27 origins | 4.89 | 3.70 | 5.47 | 12.16 | 0.00 | 0.00 | 7.41 | 18/27 = 67% |
| t4_mean_t0_t2 | official | 3.95 | 1.00 | 6.09 | 6.87 | 0.00 | 0.00 | 8.91 |  |
| t4_mean_t0_t2 | 27 origins | 4.84 | 3.62 | 5.45 | 11.95 | 0.00 | 0.00 | 7.41 | 17/27 = 63% |
| t5_mean_t0_t2_t3 | official | 4.24 | 1.13 | 6.50 | 8.04 | 0.00 | 0.00 | 8.91 |  |
| t5_mean_t0_t2_t3 | 27 origins | 4.90 | 3.72 | 5.48 | 12.19 | 0.00 | 0.00 | 7.41 | 20/27 = 74% |
| t6_t5_ridge13 | official | 4.33 | 1.32 | 6.50 | 8.40 | 0.00 | 0.00 | 8.91 |  |
| t6_t5_ridge13 | 27 origins | 4.78 | 3.47 | 5.48 | 11.70 | 0.00 | 0.00 | 7.41 | 14/27 = 52% |
| t7_gmst_scaling | official | 4.05 | 0.36 | 6.72 | 7.31 | 0.00 | 0.00 | 8.91 |  |
| t7_gmst_scaling | 27 origins | 4.53 | 3.34 | 5.07 | 10.72 | 0.00 | 0.00 | 7.41 | 9/27 = 33% |
| t7_mean_best | official | 4.43 | 0.90 | 6.99 | 8.83 | 0.00 | 0.00 | 8.91 |  |
| t7_mean_best | 27 origins | 4.75 | 3.57 | 5.32 | 11.58 | 0.00 | 0.00 | 7.41 | 14/27 = 52% |

Rule (temperature skill %, window all):

| candidate | (1) official mean vs default | (2) 27-origin mean vs default | (3) win rate | passes |
|---|---|---|---|---|
| t1_recent_normal | 2.448 vs 9.857 no | 9.327 vs 11.475 no | 26% no | **no** |
| t2_region_dep | 2.443 vs 9.857 no | 11.358 vs 11.475 no | 41% no | **no** |
| t3_two_scale | 9.751 vs 9.857 no | 12.160 vs 11.475 yes | 67% yes | **no** |
| t4_mean_t0_t2 | 6.873 vs 9.857 no | 11.948 vs 11.475 yes | 63% yes | **no** |
| t5_mean_t0_t2_t3 | 8.039 vs 9.857 no | 12.187 vs 11.475 yes | 74% yes | **no** |
| t6_t5_ridge13 | 8.396 vs 9.857 no | 11.696 vs 11.475 yes | 52% no | **no** |
| t7_gmst_scaling | 7.305 vs 9.857 no | 10.725 vs 11.475 no | 33% no | **no** |
| t7_mean_best | 8.830 vs 9.857 no | 11.580 vs 11.475 yes | 52% no | **no** |

**Rule result: T0 kept.** Every candidate fails condition 1. T3 and T5 are better over the 27
origins (+0.68 / +0.71 skill points, win rates 67% / 74%), but lose on the official folds,
mostly at 1995. T1 and T2 fail at 1980: Tatakae's regional rate has no floor and is negative
at that cut-off.

### 2.2 CDD (agent C; default C0 = lead_split3)

| ID | set | raw all | raw y1-3 | raw y4-7 | temp % | precip % | hottest % | cdd % | win rate vs default (cdd) |
|---|---|---|---|---|---|---|---|---|---|
| c0_lead_split3 | official | 4.69 | 1.32 | 7.12 | 9.86 | 0.00 | 0.00 | 8.91 |  |
| c0_lead_split3 | 27 origins | 4.72 | 3.47 | 5.39 | 11.48 | 0.00 | 0.00 | 7.41 |  |
| c1_map_t0 | official | 4.82 | 1.50 | 7.10 | 9.86 | 0.00 | 0.00 | 9.43 |  |
| c1_map_t0 | 27 origins | 4.82 | 3.59 | 5.47 | 11.48 | 0.00 | 0.00 | 7.80 | 15/27 = 56% |
| c2_map_base3010 | official | 4.73 | 1.30 | 7.14 | 9.86 | 0.00 | 0.00 | 9.08 |  |
| c2_map_base3010 | 27 origins | 4.88 | 3.59 | 5.55 | 11.48 | 0.00 | 0.00 | 8.05 | 12/27 = 44% |
| c3_half_c1_c0 | official | 4.83 | 1.47 | 7.19 | 9.86 | 0.00 | 0.00 | 9.45 |  |
| c3_half_c1_c0 | 27 origins | 4.82 | 3.56 | 5.49 | 11.48 | 0.00 | 0.00 | 7.81 | 15/27 = 56% |
| c4_three_way | official | 4.80 | 1.43 | 7.18 | 9.86 | 0.00 | 0.00 | 9.33 |  |
| c4_three_way | 27 origins | 4.80 | 3.54 | 5.47 | 11.48 | 0.00 | 0.00 | 7.72 | 15/27 = 56% |

Rule (CDD skill %, window all):

| candidate | (1) official mean vs default | (2) 27-origin mean vs default | (3) win rate | passes |
|---|---|---|---|---|
| c1_map_t0 | 9.428 vs 8.908 yes | 7.803 vs 7.410 yes | 56% no | **no** |
| c2_map_base3010 | 9.080 vs 8.908 yes | 8.048 vs 7.410 yes | 44% no | **no** |
| c3_half_c1_c0 | 9.449 vs 8.908 yes | 7.815 vs 7.410 yes | 56% no | **no** |
| c4_three_way | 9.329 vs 8.908 yes | 7.724 vs 7.410 yes | 56% no | **no** |

**Rule result: C0 kept.** All four maps beat C0 on both means but win at only 12-15 of 27
origins (they lose on average at origins 1985-1997 and win at 1998-2011). C1b (the map driven
by T's best component) equals `c1_map_t0`, because T kept T0, so it was not run separately.

### 2.3 Precipitation and hottest day (agent P; default = lead_split3, the 30-year mean)

Precipitation:

| ID | set | raw all | raw y1-3 | raw y4-7 | temp % | precip % | hottest % | cdd % | win rate vs default (total_precip_in) |
|---|---|---|---|---|---|---|---|---|---|
| p0_lead_split3 | official | 4.69 | 1.32 | 7.12 | 9.86 | 0.00 | 0.00 | 8.91 |  |
| p0_lead_split3 | 27 origins | 4.72 | 3.47 | 5.39 | 11.48 | 0.00 | 0.00 | 7.41 |  |
| p1_nudge | official | 4.65 | 1.23 | 7.12 | 9.86 | -0.16 | 0.00 | 8.91 |  |
| p1_nudge | 27 origins | 4.79 | 3.57 | 5.44 | 11.48 | 0.29 | 0.00 | 7.41 | 19/27 = 70% |
| p2_two_half | official | 4.75 | 1.29 | 7.24 | 9.86 | 0.22 | 0.00 | 8.91 |  |
| p2_two_half | 27 origins | 4.77 | 3.52 | 5.42 | 11.48 | 0.18 | 0.00 | 7.41 | 13/27 = 48% |
| p3_two_half_fh | official | 4.77 | 1.29 | 7.28 | 9.86 | 0.32 | 0.00 | 8.91 |  |
| p3_two_half_fh | 27 origins | 4.80 | 3.52 | 5.48 | 11.48 | 0.31 | 0.00 | 7.41 | 14/27 = 52% |
| p4_crm_eb | official | 4.71 | 1.33 | 7.13 | 9.86 | 0.06 | 0.00 | 8.91 |  |
| p4_crm_eb | 27 origins | 4.73 | 3.47 | 5.40 | 11.48 | 0.04 | 0.00 | 7.41 | 17/27 = 63% |
| p5_mean_p1_p3 | official | 4.74 | 1.28 | 7.25 | 9.86 | 0.21 | 0.00 | 8.91 |  |
| p5_mean_p1_p3 | 27 origins | 4.83 | 3.56 | 5.51 | 11.48 | 0.45 | 0.00 | 7.41 | 26/27 = 96% |

| candidate | (1) official mean vs default | (2) 27-origin mean vs default | (3) win rate | passes |
|---|---|---|---|---|
| p1_nudge | -0.161 vs 0.000 no | 0.286 vs 0.000 yes | 70% yes | **no** |
| p2_two_half | 0.217 vs 0.000 yes | 0.179 vs 0.000 yes | 48% no | **no** |
| p3_two_half_fh | 0.320 vs 0.000 yes | 0.313 vs 0.000 yes | 52% no | **no** |
| p4_crm_eb | 0.064 vs 0.000 yes | 0.039 vs 0.000 yes | 63% yes | **yes** |
| p5_mean_p1_p3 | 0.214 vs 0.000 yes | 0.447 vs 0.000 yes | 96% yes | **yes** |

**Rule result: P5** (two pass; P5 has the higher 27-origin mean). P5 has negative official
years 1-3 skill for precipitation, inherited from P1; it did not enter the rule.

Hottest day:

| ID | set | raw all | raw y1-3 | raw y4-7 | temp % | precip % | hottest % | cdd % | win rate vs default (hottest_day_temp) |
|---|---|---|---|---|---|---|---|---|---|
| p0_lead_split3 | official | 4.69 | 1.32 | 7.12 | 9.86 | 0.00 | 0.00 | 8.91 |  |
| p0_lead_split3 | 27 origins | 4.72 | 3.47 | 5.39 | 11.48 | 0.00 | 0.00 | 7.41 |  |
| h1_nudge | official | 4.74 | 1.47 | 7.09 | 9.86 | 0.00 | 0.18 | 8.91 |  |
| h1_nudge | 27 origins | 4.84 | 3.62 | 5.49 | 11.48 | 0.00 | 0.47 | 7.41 | 25/27 = 93% |
| h2_second_high | official | 4.77 | 1.46 | 7.16 | 9.86 | 0.00 | 0.33 | 8.91 |  |
| h2_second_high | 27 origins | 4.85 | 3.56 | 5.54 | 11.48 | 0.00 | 0.50 | 7.41 | 25/27 = 93% |
| h3_crm_eb | official | 4.71 | 1.33 | 7.13 | 9.86 | 0.00 | 0.06 | 8.91 |  |
| h3_crm_eb | 27 origins | 4.74 | 3.49 | 5.40 | 11.48 | 0.00 | 0.07 | 7.41 | 26/27 = 96% |
| h4_mean_h1_h2 | official | 4.80 | 1.50 | 7.18 | 9.86 | 0.00 | 0.43 | 8.91 |  |
| h4_mean_h1_h2 | 27 origins | 4.88 | 3.63 | 5.56 | 11.48 | 0.00 | 0.64 | 7.41 | 27/27 = 100% |

| candidate | (1) official mean vs default | (2) 27-origin mean vs default | (3) win rate | passes |
|---|---|---|---|---|
| h1_nudge | 0.183 vs 0.000 yes | 0.474 vs 0.000 yes | 93% yes | **yes** |
| h2_second_high | 0.326 vs 0.000 yes | 0.498 vs 0.000 yes | 93% yes | **yes** |
| h3_crm_eb | 0.059 vs 0.000 yes | 0.075 vs 0.000 yes | 96% yes | **yes** |
| h4_mean_h1_h2 | 0.425 vs 0.000 yes | 0.644 vs 0.000 yes | 100% yes | **yes** |

**Rule result: H4** (all four pass; H4 has the highest 27-origin mean and wins at all 27).

## 3. Combination (Section 3)

| metric | chosen by the rule |
|---|---|
| annual_avg_temp | T0 (default) |
| cdd | C0 (default) |
| total_precip_in | P5 = mean(P1, P3) |
| hottest_day_temp | H4 = mean(H1, H2) |

| ID | set | raw all | raw y1-3 | raw y4-7 | temp % | precip % | hottest % | cdd % | win rate vs default (raw_score) |
|---|---|---|---|---|---|---|---|---|---|
| r2_lead_split3 | official | 4.69 | 1.32 | 7.12 | 9.86 | 0.00 | 0.00 | 8.91 |  |
| r2_lead_split3 | 27 origins | 4.72 | 3.47 | 5.39 | 11.48 | 0.00 | 0.00 | 7.41 |  |
| r3_crm_s6_eb_urban | official | 4.39 | 0.51 | 7.23 | 9.11 | 0.06 | 0.06 | 8.33 |  |
| r3_crm_s6_eb_urban | 27 origins | 4.72 | 3.33 | 5.41 | 11.36 | 0.04 | 0.07 | 7.39 | 11/27 = 41% |
| r4_winners | official | 4.85 | 1.46 | 7.30 | 9.86 | 0.21 | 0.43 | 8.91 |  |
| r4_winners | 27 origins | 4.99 | 3.73 | 5.68 | 11.48 | 0.45 | 0.64 | 7.41 | 27/27 = 100% |
| r5_winners_t0_c0 | official | 4.85 | 1.46 | 7.30 | 9.86 | 0.21 | 0.43 | 8.91 |  |
| r5_winners_t0_c0 | 27 origins | 4.99 | 3.73 | 5.68 | 11.48 | 0.45 | 0.64 | 7.41 | 27/27 = 100% |
| r6_mean_r2_r3_r4 | official | 4.72 | 1.18 | 7.29 | 9.66 | 0.12 | 0.21 | 8.89 |  |
| r6_mean_r2_r3_r4 | 27 origins | 4.90 | 3.64 | 5.56 | 11.57 | 0.20 | 0.28 | 7.55 | 21/27 = 78% |

R1 (`thirty_year_mean`) is 0 by definition. **R5 equals R4** (the rule kept T0 and C0, so both
rows are the same forecaster). R6 is worse than R4 on every window.

R4 vs R2 under the same rule (raw score, window all):

| candidate | (1) official mean vs default | (2) 27-origin mean vs default | (3) win rate | passes |
|---|---|---|---|---|
| r4_winners | 4.851 vs 4.691 yes | 4.994 vs 4.721 yes | 100% yes | **yes** |

**R4 (`r4_winners`) is the new submission row** (`configs/mp_final_round.yaml`, `submit:
r4_winners`).

## 4. The other teams' methods: our interpretation and citations

Methods were re-implemented from README text only; no code of theirs was downloaded or copied.
Both datasets are CC BY 4.0. Their READMEs quote leaderboard / Live Score numbers; none was
used.

- **Tatakae** (Mashrafi Mahmud Rafi, @ironMan334), `ironMan334/protostar-climate-team-tatakae`,
  commit `f18c1178c1b97566c75facc94c886184ebaa2a10`.
- **PstarAlu** (Nibedita Biswal, @nbiswal-star), `nbiswal-star/protostar-climate-submission`,
  commit `9e51c3ef5d3178ca194f28e2c4134201c1bf9675`. PstarAlu cites Fay & Herriot (1979),
  JASA 74(366), doi 10.1080/01621459.1979.10482505.
- HadCRUT4 (T7 only): Morice et al. (2012), JGR 117, D08101, doi 10.1029/2011JD017187.

The interpretations were fixed before any run, in the agents' notes:
[final_temp.md](final_temp.md), [final_cdd.md](final_cdd.md),
[final_precip_hot.md](final_precip_hot.md). In short:

- **"32 nearest cities"** = the city plus its 31 nearest; **"31 nearest neighbours"** = the 31
  nearest others (leave-one-out).
- **T1**: last 15 valid years; rate = mean 40-year OLS slope of the 32 cities, no floor.
- **T2**: region anomaly = equal-weight mean of the 32 cities' 30-year anomalies, carried by a
  30-year OLS line; departure = mean of the last 5 valid years; 0.75 view + 0.25 T1.
- **T3**: "area-weighted" (not defined by PstarAlu) = inverse local density, i.e. 1 / (number
  of cities within 300 km); both parts decay at every lead (PstarAlu splits only in years 4-7;
  that variant was not run); pooled lag-1 OLS with Kendall's bias correction, clipped to
  [0, 0.99].
- **T6**: leads 1-3 = lead_split3 temperature, leads 4-7 = T5 (one reading run).
- **T7**: 40-year city OLS on GMST, shrunk to the 32-city mean slope by empirical Bayes; GMST
  forecast = non-negative 30-year OLS line fitted inside the fold.
- **C1**: the year's mean = the mean of daily means on days with both values; at least 5 base
  years (PstarAlu's rule, applied to C1 too). Annual `cdd` equals the daily recount exactly.
- **C2**: "complete" = valid and both temperatures on every day.
- **P2**: "shrunk 30-year median" (not defined by PstarAlu) = the city's median/mean ratio
  shrunk halfway toward the 300 km kernel mean ratio of the other cities.
- **P3**: Fay-Herriot as in the README (tau² floored at 0 gives weight 0, which removes the
  45-year local deviation; sparse cities get no change). Agent P compared its correction at the
  2018 origin with the README's description of that origin (207 cities on the 45-year level,
  206 adjusted, mean change 0.26 in, at most 5.6%): ours gave 207, 206, 0.262 and 5.56%.
- **H2**: complete year = at least 360 days with tmax; spacing pooled by a 300 km Gaussian kernel,
  the city included.

How these differ from our earlier delta test (which lost): C1-C4 map from a full temperature
forecast (lead_split3, ridge included) instead of the trend increment, use a recounted
10-year or 30/10-year base, and C3/C4 blend with C0. They still fail the win-rate condition.

**Not run, and why:** PstarAlu's precipitation harmonic, hottest-day summer-state term and
years 1-3 residual layer (many fitted parameters; their own audit shows negative long-span
skill for the summer-state term). Also, recorded as ideas: T3 with PstarAlu's exact lead split,
T6 reading 2, other T7 windows or an unfloored GMST trend, and alternative readings of P2, P3
and H2.

## 5. Count of variants, and rows chosen after results

- **Candidates scored: 24 distinct forecasters.** T1-T7 and T7b (8); C1-C4 (4); P1-P5 and H1-H4
  (9); R4, R6 (2); R5 is a duplicate of R4, plus R3. With the defaults and R1 this is 29 config
  rows.
- **Runs:** agent T ran its whole config twice (run 2 added T7b; T0-T7 were identical in both
  runs). C, P and the R rows ran once each. There were no failed model runs. Agent C had one
  wrong test (the positive control of a leak test) on its first run; no model code changed.
- **Rows chosen after seeing results: none by hand.** Three rows had their content filled in
  after earlier results, as the rule pre-registered: T7b (best of T0-T6 = T0), C1b (= C1,
  because T kept T0), and R4-R6 (per-metric winners). The reference `crm_s6_eb_urban` was
  assembled after results in an earlier round (as noted in `configs/mp_crm.yaml`); it is a
  reference here, not a candidate.

## 6. Submission

`uv run proto-star climate-package configs/mp_final_round.yaml` produced
`submissions/20261109-234814_final_round/`:
- "OK: 5880 rows over 4 metrics reproduce submission.csv"
- `scripts/check_submission.py`: "has all 5880 forecasts and can be scored"
- sha256 `e33a07d39d9bb17f019b208f126f73e8d05ce14642a6d6a59b4b5e64fbe3a5d7`

Compared with lead_split3, only precipitation (1,449 rows; mean -0.16 in) and hottest day
(1,463 rows; mean +0.002 F) change. Temperature and CDD are identical. It was not uploaded.

**Package fix (2026-11-10).** The first package did not reproduce on its own: H2 reads the
daily table, which the package did not ship, so the publish workflow's "reproduce from the
package alone" step would have failed (the local check passed only because the repo's
`data/raw` was found). Now `climate-package` ships `daily.parquet` (unchanged CMU copy,
49 MB) whenever the submitted forecaster contains a daily-reading kind
(`final_hottest_second_high`, `cdd_daily_map`), and `daily_fold` falls back to the packaged
copy. A test covers it. The rebuilt package `submissions/20261110-000932_final_round/`
reproduces from an isolated copy, and its `submission.csv` is byte-identical to the first
(sha256 `e33a07d3...`). The workflow's default `config` is now `configs/mp_final_round.yaml`.

## 7. Open points for the human

1. **HadCRUT4 licence.** Agent T found the Met Office terms: Crown copyright, use "for private
   study and scientific research" only; other use needs a Met Office licence (not the OGL). T7
   lost, so the submission does not use HadCRUT. The capped file
   (`data/external/hadcrut4/`, git-ignored) and its loader stay local. Rule on whether to keep
   them in the repo.
2. **ADR 0009** is proposed; it needs your acceptance.
3. **Small, correlated evidence.** Consecutive origins share target years, so the 27 paired
   comparisons are not independent. The precipitation gain is 0.45 skill points (27 origins)
   and 0.21 (official), and P5's official years 1-3 precipitation skill is negative.
4. **Nothing committed.** Because nothing could be committed, the agents' work was integrated
   by copying files, not by `git merge`. The branches `agent/final-temp`, `agent/final-cdd` and
   `agent/final-precip-hot` have no commits. Their worktrees were removed after their files and
   runs were copied here and checked. During the copy, the empty setup copies of
   `mp_final_temp.yaml` and `mp_final_cdd.yaml` first overwrote the agents' filled-in versions.
   This was caught by a byte comparison and restored from the worktrees; the restored files
   equal the configs saved with the recorded runs. `docs/experiments.md` is not updated
   (waiting for your approval).

## Appendix: record written by `climate-trial --record` (official folds)

Final round: per-metric components from the re-implemented Tatakae and PstarAlu methods, chosen by a pre-registered rule and combined with lead_split3 and the CRM.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-09 |
| Config | `configs/mp_final_round.yaml` |
| Code version | `965e1c8` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `r2_lead_split3` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_final_round.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| r2_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| r3_crm_s6_eb_urban | CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp |
| r4_winners | hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]] |
| r5_winners_t0_c0 | hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]] |
| r6_mean_r2_r3_r4 | cdd = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; 0.33 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; other metrics from [swap_metric: hottest_day_temp = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; 0.33 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; other metrics from [swap_metric: total_precip_in = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; 0.33 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; other metrics from [swap_metric: annual_avg_temp = 0.33 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; 0.33 x [crm: CRM: levels [10, 15], non-negative pooled 40-year trend for temperature and CDD shrunk toward 6 spectral clusters (geo weight 0.5) by empirical Bayes (k_scale 1.0); CDD trend = shrunk regional temperature trend x city CDD per degree; temperature slope + pooled gamma x census growth of the last decade; regional empirical-Bayes 30-year level for total_precip_in, hottest_day_temp]; 0.33 x [swap_metric: hottest_day_temp = 0.5 x [final_hottest_nudge: Hottest day: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae)]; 0.5 x [final_hottest_second_high: Hottest day: mean second-highest daily maximum over complete years (>= 360 days) of the 30-year window + tail spacing pooled by a 300 km Gaussian kernel (PstarAlu); 30-year mean if < 10 complete years]; other metrics from [swap_metric: total_precip_in = 0.5 x [final_precip_nudge: Precipitation: 30-year mean nudged by 0.3 x the city's mean departure over the last 10 years from its 31 nearest cities (Tatakae), as a ratio]; 0.5 x [final_precip_two_half: Precipitation: 0.5 x 30-year median (median/mean ratio shrunk 0.5 toward the 300 km kernel mean) + 0.5 x complete-year mean (30 years for leads 1-3, 45 for later leads if >= 10/15 complete years) (PstarAlu); leads > 3: Fay-Herriot shrinkage of the 45-year local deviation vs the 90-year record (300 km leave-one-out kernel)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]]]] |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| r2_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| r3_crm_s6_eb_urban | 4.39 | 9.11 | 0.06 | 0.06 | 8.33 | 2 | 3 |
| r4_winners | 4.85 | 9.86 | 0.21 | 0.43 | 8.91 | 2 | 3 |
| r5_winners_t0_c0 | 4.85 | 9.86 | 0.21 | 0.43 | 8.91 | 2 | 3 |
| r6_mean_r2_r3_r4 | 4.72 | 9.66 | 0.12 | 0.21 | 8.89 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| r2_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| r3_crm_s6_eb_urban | 0.51 | -2.29 | 0.07 | 0.06 | 4.18 | 2 | 3 |
| r4_winners | 1.46 | -0.09 | -0.15 | 0.73 | 5.35 | 3 | 3 |
| r5_winners_t0_c0 | 1.46 | -0.09 | -0.15 | 0.73 | 5.35 | 3 | 3 |
| r6_mean_r2_r3_r4 | 1.18 | -0.72 | -0.01 | 0.32 | 5.15 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| r2_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| r3_crm_s6_eb_urban | 7.23 | 18.15 | 0.07 | 0.05 | 10.66 | 2 | 3 |
| r4_winners | 7.3 | 17.73 | 0.51 | 0.23 | 10.74 | 2 | 3 |
| r5_winners_t0_c0 | 7.3 | 17.73 | 0.51 | 0.23 | 10.74 | 2 | 3 |
| r6_mean_r2_r3_r4 | 7.29 | 17.88 | 0.24 | 0.15 | 10.89 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| r2_lead_split3 | 0.05 | 4.83 | 9.2 |
| r3_crm_s6_eb_urban | -0.61 | 3.74 | 10.04 |
| r4_winners | -0.05 | 5.24 | 9.36 |
| r5_winners_t0_c0 | -0.05 | 5.24 | 9.36 |
| r6_mean_r2_r3_r4 | -0.08 | 4.67 | 9.59 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
