# Final round, agent C: CDD from a daily temperature map (trial note)

Branch `agent/final-cdd`, config `configs/mp_final_cdd.yaml`. Each candidate replaces the CDD
forecast only (kind `swap_metric`, base `lead_blend` = lead_split3); the other three metrics stay
identical to the default (tested in `tests/test_final_cdd.py`). Selection rule: Section 4,
written in the config header before any run, applied with
`proto_star.robustness.apply_selection_rule(..., metric="cdd")` on the `all` window (ADR 0009).

## 1. Pre-registration (written before any candidate ran)

### Sources (methods re-implemented from README text only; no code downloaded or copied)

| Team | Dataset (CC BY 4.0) | Commit read | Section used |
|---|---|---|---|
| PstarAlu (Nibedita Biswal) | [nbiswal-star/protostar-climate-submission](https://huggingface.co/datasets/nbiswal-star/protostar-climate-submission) | `9e51c3ef5d3178ca194f28e2c4134201c1bf9675` | README "Method > Cooling degree days", "Validation" |
| Tatakae (Mashrafi Mahmud Rafi) | [ironMan334/protostar-climate-team-tatakae](https://huggingface.co/datasets/ironMan334/protostar-climate-team-tatakae) | `f18c1178c1b97566c75facc94c886184ebaa2a10` | README "Method" (third view, "daily shape"), "What did not work" |

Both READMEs quote leaderboard / Live Score numbers. None of them was used for anything here.
Both teams build on the Lai and Dzombak (2019) records (doi 10.1184/R1/7890488.v6 and
10.1184/R1/7961012.v6), cited only, not downloaded.

### Data check: how annual `cdd` relates to the daily table (done before building on it)

On 4 cities (USW00094823 Pittsburgh, USW00012839 Miami, USW00024233 Seattle, USW00023183
Phoenix), all 503 valid years (Miss Tmax and Miss Tmin <= 10) in the raw tables:

* annual `cdd` = sum over the days with both tmax and tmin of max(0, (tmax + tmin) / 2 - 65),
  unrounded: the absolute difference is 0.000 in every one of the 503 years.
* `Avg Temp` = (mean of the year's tmax + mean of the year's tmin) / 2, each mean over its own
  available days, rounded to 2 decimals (max |difference| 0.0096 F). The mean of the daily means
  over the days with both values differs from `Avg Temp` by up to 0.118 F (mean 0.005 F), only
  in years where tmax and tmin miss different days.
* Valid years have 350 to 366 days with both values; 93.4% have every day of the year.

### Fixed definitions and parameters (all candidates)

* Daily mean temperature of a day: (tmax + tmin) / 2, days with both values only (the days the
  annual `cdd` counts). Daily data is read only through
  `proto_star.data.daily_fold.daily_to_cutoff(cutoff, columns=["tmax", "tmin"])`.
* A valid year: the year has an annual `cdd` value that passes the organizer's missing-days rule
  (`metric_valid_mask`, = the master's `valid_cdd`), taken from `train` via `annual_to_long`.
* The "year's mean" that is shifted: the mean of that year's daily mean temperatures over the
  days with both values. This is **not** forced to match `annual_avg_temp`'s definition
  (mean tmax and mean tmin over their own days); the two agree exactly when tmax and tmin miss
  the same days, and differ by at most about 0.12 F otherwise (check above). Chosen because it
  keeps the shift consistent with the days that are recounted.
* Map of one base year k to a forecast temperature T: shift = T - mean_k; CDD_k(T) = sum over
  that year's days of max(0, tm_i + shift - 65). The recount uses the base year's own days (365
  or 366; a valid year with up to 10 missing days is recounted over its present days, as the
  annual `cdd` is). With T = mean_k (no shift) the map reproduces that year's annual `cdd`.
* Temperature forecast T(city, year): the `annual_avg_temp` forecast of the model entry in the
  spec's `temperature` field, computed on the same fold with
  `swap_metric.cached_forecast`. T0 = `{kind: lead_blend, params: {}}` (lead_split3:
  0.5 trend + 0.5 ridge in leads 1-3, trend in leads 4-7).
* Fallback: a city with fewer than **5** usable base years (in every window) keeps the CDD
  forecast of the temperature model entry (for T0 that is exactly C0). The threshold 5 is
  PstarAlu's stated rule ("fewer than five usable base years ... keeps its CDD"); Tatakae states
  no minimum, so it is applied to C1 too.
* Kinds: `cdd_daily_map` (`src/proto_star/forecasters/final_cdd.py`), `cdd_ridge`
  (`src/proto_star/forecasters/final_cdd_ridge.py`, the pooled P09/P14 ridge for CDD alone via
  `make_pooled_ridge(model_metrics=["cdd"])`, alpha 1.0, all training years, the lead_split3
  settings). The scaled trend alone is `pooled_trend {level_years: [10, 15], trend_window: 40,
  cdd_sensitivity: true}`.

### Interpretation of each candidate

* **C0 `c0_lead_split3`**: default, lead_split3 unchanged (CDD = 0.5 scaled trend + 0.5 ridge).
* **C1 `c1_map_t0`** (Tatakae "daily shape"; PstarAlu has a similar map): base years = the
  city's last 10 valid years up to the cut-off (count-based, any gap allowed); CDD = mean over
  those years of CDD_k(T0). `cdd_daily_map {base: last_valid, windows: [10]}`.
* **C1b `c1_map_tbest`**: the same map driven by the temperature component agent T reports as
  chosen by its rule. Agent T's code is on another branch, so this row cannot run in this
  worktree. It is pure config (only the `temperature` entry changes) and is written commented out
  in the config, with a placeholder; the main session runs it after integration. If T keeps T0,
  this row equals `c1_map_t0`.
* **C2 `c2_map_base3010`** (PstarAlu): "complete year" = a valid year (above) **and** both tmax
  and tmin present on every day of the calendar year (365 or 366 days with both values). Two
  calendar windows ending at the cut-off: 30 years (cut-off - 29 .. cut-off) and 10 years
  (cut-off - 9 .. cut-off). Each window's map = mean over its complete years of CDD_k(T0); a
  window is used only if it has at least 5 complete years. CDD = mean of the two windows' maps
  (one window if only one qualifies; the fallback if none). The calendar-window reading follows
  PstarAlu's precipitation text, which counts complete years inside a "30-year window".
  `cdd_daily_map {base: complete_calendar, windows: [30, 10]}`.
* **C3 `c3_half_c1_c0`** (Tatakae weighting: "the final CDD is 50 % this + 50 % the first two"):
  0.5 x C1 + 0.5 x C0, with C0's CDD in place of Tatakae's first two views. `swap_metric`
  components [C1 map, lead_blend], weights [0.5, 0.5].
* **C4 `c4_three_way`**: equal-weight mean (1/3 each) of the scaled trend, the CDD ridge and
  C1. Since C0 = 0.5 trend + 0.5 ridge, C4 = 2/3 C0 + 1/3 C1.

### Difference from the earlier delta test (`pooled_trend_exploration.md`, lost)

The earlier test shifted daily temperatures by the pooled-trend temperature change (the
`ashley-boys` delta method), alone (2.17) and blended 50% with the trend CDD (2.28), against a
level-15 pooled trend (2.30), raw score on the official folds, with throwaway code. The new
candidates differ in four ways: (1) the shift is set by a full temperature forecast (T0 =
lead_split3, which includes the ridge in leads 1-3), not by the trend increment alone; (2) the
base is the last 10 valid years (C1) or complete-year 30/10 windows (C2), recounted per year;
(3) C3 and C4 blend the map with C0's CDD, which already contains the ridge; (4) the selection
is on the CDD skill alone, on the `all` window, on the official folds plus 27 rolling origins
with a paired win rate (Section 4), and the code is kept and tested.

### Fixed before running; not run

Ideas that come up after this point are listed in Section 4 as "not run".

## 2. Official folds (1980, 1995, 2011)

Run: `uv run proto-star climate-trial configs/mp_final_cdd.yaml --record`, run dir
`runs/trials/20261109-222300_final_cdd` (code `965e1c8` + uncommitted changes, master hash in the
appendix), 1 min 54 s. C0 reproduces the reference (4.69 / 1.32 / 7.12, CDD 8.91%).

CDD skill (%) and raw score, mean over the three folds. The other three metric skills are
identical for every candidate (temperature 9.86, precipitation 0.00, hottest day 0.00, all years).

| ID | method | CDD all | CDD yrs 1-3 | CDD yrs 4-7 | raw all | raw yrs 1-3 | raw yrs 4-7 |
|---|---|---|---|---|---|---|---|
| C0 | c0_lead_split3 | 8.91 | 5.35 | 10.74 | 4.69 | 1.32 | 7.12 |
| C1 | c1_map_t0 | 9.43 | 6.08 | 10.67 | 4.82 | 1.50 | 7.10 |
| C2 | c2_map_base3010 | 9.08 | 5.27 | 10.83 | 4.73 | 1.30 | 7.14 |
| C3 | c3_half_c1_c0 | 9.45 | 5.95 | 11.01 | 4.83 | 1.47 | 7.19 |
| C4 | c4_three_way | 9.33 | 5.81 | 10.98 | 4.80 | 1.43 | 7.18 |

CDD skill (%) per fold, all years:

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| c0_lead_split3 | 1.85 | 4.49 | 20.38 |
| c1_map_t0 | -0.89 | 5.02 | 24.15 |
| c2_map_base3010 | 0.42 | 4.60 | 22.21 |
| c3_half_c1_c0 | 0.90 | 4.93 | 22.52 |
| c4_three_way | 1.30 | 4.82 | 21.87 |

## 3. 27 rolling origins (1985-2011) and the selection rule

Run: `uv run python scripts/robustness_origins.py configs/mp_final_cdd.yaml --origins rolling27
--default c0_lead_split3 --out runs/robustness/final_cdd` (origins.csv, paired.csv,
paired_summary.csv), 23 min 46 s. Other metrics: the paired difference against C0 is exactly 0 for
temperature, precipitation and hottest day at every origin and window, for every candidate
(metric isolation on real data; `tests/test_final_cdd.py` checks it on synthetic data).

Mean over the 27 origins, CDD skill (%) and raw score (temperature skill 11.48 for all):

| ID | method | CDD all | CDD yrs 1-3 | CDD yrs 4-7 | raw all | raw yrs 1-3 | raw yrs 4-7 |
|---|---|---|---|---|---|---|---|
| C0 | c0_lead_split3 | 7.41 | 5.66 | 8.61 | 4.72 | 3.47 | 5.39 |
| C1 | c1_map_t0 | 7.80 | 6.17 | 8.92 | 4.82 | 3.59 | 5.47 |
| C2 | c2_map_base3010 | 8.05 | 6.15 | 9.27 | 4.88 | 3.59 | 5.55 |
| C3 | c3_half_c1_c0 | 7.81 | 6.04 | 9.04 | 4.82 | 3.56 | 5.49 |
| C4 | c4_three_way | 7.72 | 5.94 | 8.95 | 4.80 | 3.54 | 5.47 |

Paired against C0 (CDD skill difference in points; wins = origins with a strictly higher skill):

| method | wins all | mean diff all | wins yrs 1-3 | mean diff yrs 1-3 | wins yrs 4-7 | mean diff yrs 4-7 |
|---|---|---|---|---|---|---|
| c1_map_t0 | 15/27 | +0.39 | 15/27 | +0.50 | 10/27 | +0.31 |
| c2_map_base3010 | 12/27 | +0.64 | 17/27 | +0.48 | 13/27 | +0.66 |
| c3_half_c1_c0 | 15/27 | +0.41 | 16/27 | +0.37 | 13/27 | +0.43 |
| c4_three_way | 15/27 | +0.31 | 16/27 | +0.28 | 13/27 | +0.34 |

### Rule result (Section 4, `apply_selection_rule(..., metric="cdd")`, window `all`)

| candidate | 1. official > C0 (8.91) | 2. 27-origin mean > C0 (7.41) | 3. win rate >= 60% | passes |
|---|---|---|---|---|
| C1 c1_map_t0 | 9.43 yes | 7.80 yes | 55.6% no | no |
| C2 c2_map_base3010 | 9.08 yes | 8.05 yes | 44.4% no | no |
| C3 c3_half_c1_c0 | 9.45 yes | 7.81 yes | 55.6% no | no |
| C4 c4_three_way | 9.33 yes | 7.72 yes | 55.6% no | no |

**No candidate passes. The rule keeps the default C0 (lead_split3's CDD).** C1b
(`c1_map_tbest`) is not in this table; the main session adds it after integration.

### Observation (not used for any choice)

The paired CDD differences split by period. Over origins 1985-1997 every map candidate loses on
average (C1 -0.82, C2 -1.04, C3 -0.26, C4 -0.14 points; 2 to 4 wins of 13). Over 1998-2011 every
one wins on average (C1 +1.52, C2 +2.20, C3 +1.02, C4 +0.73; 10 to 11 wins of 14). This is why
the means are higher while the win rate stays under 60%. Consecutive origins share target years,
so the 27 differences are not independent. The rule was fixed before the run and is applied as
written; this split is reported only so a reader can see why it failed.

## 4. Variants tried, failures, not run

* **Variants scored: 4** (C1, C2, C3, C4) plus the default C0, each in exactly one official-fold
  run and one 27-origin run. No variant was changed or re-run after the results were seen.
* Before the scored runs, one unscored check ran C1 and C2 on the 1980 and 2011 folds for time
  and memory (2-25 s per fold, peak RSS 1.75 GB) and counted fallback cities: C1 1 of 210 at
  1980, 0 at 2011; C2 18 of 210 at 1980, 15 at 2011 (these cities have fewer than 5 complete
  years in both windows and keep C0's CDD). No skill was computed in that check.
* Failures: none in the model runs. One test was wrong on its first run: the leak test's positive
  control added a uniform +3 F to the cut-off year, which the map correctly removes (it subtracts
  each base year's own mean); the control was changed to a hotter July. No model code changed.
* A helper script to print these tables first failed (pandas `to_markdown` needs `tabulate`,
  not installed; no dependency was added; the tables were formatted by hand-written code).
* **Not run** (came up after the pre-registration; recorded only):
  * C1b `c1_map_tbest`: pending agent T's chosen temperature entry (main session).
  * A "complete year" threshold of 360 days (PstarAlu's precipitation rule) instead of every
    day, which would cut C2's fallback cities.
  * Rescaling the recount of a valid year with missing days to a full year.
  * Any other C3/C4 weights, or a map weight that depends on the period: these would be chosen
    after seeing the 1985-1997 / 1998-2011 split above, so they would be post-hoc.

---

## Appendix: record written by `climate-trial --record` (kept as written)

### Trial: final_cdd

Final round, agent C: CDD from a daily temperature map driven by a temperature forecast (Tatakae, PstarAlu), and blends with lead_split3's CDD; each replaces CDD only.


## What was used

| Item | Value |
|---|---|
| Date | 2026-11-09 |
| Config | `configs/mp_final_cdd.yaml` |
| Code version | `965e1c8` (uncommitted changes) |
| Data | `data/processed/protostar/annual_master.parquet`, content hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1` |
| Folds | cut-offs [1980, 1995, 2011], 7-year horizon (ADR 0004) |
| Reference | `thirty_year_mean` |
| Submit candidate | `c0_lead_split3` |

## Reproduce

```bash
uv run python scripts/download_protostar_data.py
uv run python scripts/build_master_dataset.py   # content hash above must match
uv run proto-star climate-trial configs/mp_final_cdd.yaml
```

## Forecasters

| forecaster | definition |
|---|---|
| thirty_year_mean | Mean of valid years in the 30 calendar years to the cutoff (reference) |
| c0_lead_split3 | Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day |
| c1_map_t0 | cdd = 1 x [cdd_daily_map: CDD = daily mean temperatures of each base year shifted to the temperature forecast of [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] and recounted (base 65 F); mean map over last 10 valid years (at least 5 base years per window, otherwise the temperature model's CDD)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| c2_map_base3010 | cdd = 1 x [cdd_daily_map: CDD = daily mean temperatures of each base year shifted to the temperature forecast of [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] and recounted (base 65 F); mean map over complete years in the last 30 calendar years and complete years in the last 10 calendar years (at least 5 base years per window, otherwise the temperature model's CDD)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| c3_half_c1_c0 | cdd = 0.5 x [cdd_daily_map: CDD = daily mean temperatures of each base year shifted to the temperature forecast of [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] and recounted (base 65 F); mean map over last 10 valid years (at least 5 base years per window, otherwise the temperature model's CDD)]; 0.5 x [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |
| c4_three_way | cdd = 0.33 x [pooled_trend: Mean of last-[10, 15]-valid-year levels plus a non-negative pooled 40-year trend for temperature and CDD; CDD trend = pooled temperature trend x each city's CDD per degree; 30-year mean for precipitation and hottest day]; 0.33 x [cdd_ridge: Pooled P09/P14 ridge for CDD alone (alpha 1, all training years)]; 0.33 x [cdd_daily_map: CDD = daily mean temperatures of each base year shifted to the temperature forecast of [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] and recounted (base 65 F); mean map over last 10 valid years (at least 5 base years per window, otherwise the temperature model's CDD)]; other metrics from [lead_blend: Pooled trend (levels [10, 15], 40-year slope, CDD sensitivity) blended with the pooled P09/P14 ridge (alpha 1): temperature trend weight by lead 0.5/0.5/0.5/1 (last holds), CDD trend weight 0.5; 30-year mean for precipitation and hottest day] |

## Results

Mean `raw_score` over the folds (the official score without its floor at zero), per-metric
skill in percent, and the number of folds each method beats `thirty_year_mean`.
`years_4_7` matches the Final Score; give it the most weight.

### all

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| c0_lead_split3 | 4.69 | 9.86 | 0.0 | 0.0 | 8.91 | 3 | 3 |
| c1_map_t0 | 4.82 | 9.86 | 0.0 | 0.0 | 9.43 | 2 | 3 |
| c2_map_base3010 | 4.73 | 9.86 | 0.0 | 0.0 | 9.08 | 2 | 3 |
| c3_half_c1_c0 | 4.83 | 9.86 | 0.0 | 0.0 | 9.45 | 2 | 3 |
| c4_three_way | 4.8 | 9.86 | 0.0 | 0.0 | 9.33 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_1_3

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| c0_lead_split3 | 1.32 | -0.09 | 0.0 | 0.0 | 5.35 | 3 | 3 |
| c1_map_t0 | 1.5 | -0.09 | 0.0 | 0.0 | 6.08 | 3 | 3 |
| c2_map_base3010 | 1.3 | -0.09 | 0.0 | 0.0 | 5.27 | 3 | 3 |
| c3_half_c1_c0 | 1.47 | -0.09 | 0.0 | 0.0 | 5.95 | 3 | 3 |
| c4_three_way | 1.43 | -0.09 | 0.0 | 0.0 | 5.81 | 3 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### years_4_7

| method | raw_score | annual_avg_temp_skill | total_precip_in_skill | hottest_day_temp_skill | cdd_skill | origins_beating_baseline | origins |
|---|---|---|---|---|---|---|---|
| c0_lead_split3 | 7.12 | 17.73 | 0.0 | 0.0 | 10.74 | 2 | 3 |
| c1_map_t0 | 7.1 | 17.73 | 0.0 | 0.0 | 10.67 | 2 | 3 |
| c2_map_base3010 | 7.14 | 17.73 | 0.0 | 0.0 | 10.83 | 2 | 3 |
| c3_half_c1_c0 | 7.19 | 17.73 | 0.0 | 0.0 | 11.01 | 2 | 3 |
| c4_three_way | 7.18 | 17.73 | 0.0 | 0.0 | 10.98 | 2 | 3 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 3 |

### Raw score per origin (all forecast years)

| method | 1980 | 1995 | 2011 |
|---|---|---|---|
| c0_lead_split3 | 0.05 | 4.83 | 9.2 |
| c1_map_t0 | -0.64 | 4.96 | 10.14 |
| c2_map_base3010 | -0.31 | 4.86 | 9.66 |
| c3_half_c1_c0 | -0.19 | 4.94 | 9.74 |
| c4_three_way | -0.09 | 4.91 | 9.57 |
| thirty_year_mean | 0.0 | 0.0 | 0.0 |
