# Coupled Regional Model (CRM): notes behind the `crm` trial

Plan: [docs/plan_regional_and_papers.md](../plan_regional_and_papers.md), Section 5. Code:
`src/proto_star/forecasters/crm.py` (kind `crm`) and the `_crm_*.py` helpers. Config:
`configs/mp_crm.yaml`. The recorded run is [crm.md](crm.md). Every number here comes from code
run on data through 2018. No leaderboard score or 2019-2025 weather informed any choice.

## What the model is

Pooled and local models are two ends of one scale. The CRM starts at the pooled end (the
champion `trend_level10_15_sensitivity`) and moves toward regions only as far as the data
supports.

| Layer | What it does | Settings |
|---|---|---|
| 1 Regions | the 6 fixed `assign_region` regions, or spectral clusters of cities. Affinity = 0.5 x max(corr, 0) of 60-year detrended temperature anomalies + 0.5 x exp(-(distance / 800 km)^2). Recomputed in every fold from `train` only. | `regions`, `n_clusters` in {4, 5, 6}, seed 0 |
| 2 Shrunk trends | `beta[r] = pooled + k_scale * k_r * (regional[r] - pooled)`, floored at 0. `k_r = tau^2 / (tau^2 + se_r^2)`. `se_r` is a year-clustered standard error of the regional within-city slope, so cities sharing a year's anomaly are not counted as independent. `tau^2 = max(0, mean((regional - pooled)^2) - mean(se^2))`. CDD: city CDD per degree x the region's shrunk temperature trend (the champion's rule). Two pre-declared alternatives (`cdd_trend`) use the region's shrunk CDD slope. | `k_scale` in {0, 0.5, 1} |
| 3 Interactions | lasso VAR(1), no intercept, on the year x (region, metric) panel of mean city residuals from the Layer-2 baseline, 40 years, standardized. Forecast shift = damping x A^h z[cutoff], added to every city of the region. Optionally in city-standardized units (`var_city_scale`). | `var_alpha` in {CV, 0.1}, damping in {0.5, 1} |
| 5.5 Levels | precipitation and hottest day. `segment`: mean of the 30-year window on the current station segment if >= 15 such years, else the 30-year mean. `regional_eb`: a two-way fit (city level + region-year anomaly, anomalies averaging 0 over the window). It gives each city's gap-filled 30-year level, blended with the raw mean by EB weights. A city with no missing years keeps its raw mean exactly. | `flat_level` |
| Row 8 Urban | temperature slope + gamma x (centred log county-population growth over the last census decade at or before the cut-off). One pooled gamma, least squares on the champion's within-city anomalies. Census from agent D's `data/processed/external/city_static.parquet`, read by `_crm_urban.load_city_static`. | `urban` |

`k_scale = 0` gives the champion exactly. A test checks this, and the trial row `crm_fixed_k0`
matches the champion to the last digit on every fold.

## Order in which variants were tried (selection disclosure)

1. Layer-2 grid, fixed before any CRM score: fixed regions with k_scale 0, 0.5, 1; spectral
   K 4, 5, 6. The first diagnostics showed the champion's CDD rule ignores the regional CDD
   slopes, so before scoring I added the two `cdd_trend` alternatives (fixed and spectral).
2. Rule declared in advance: best Layer-2 row by mean `years_4_7` goes on. That was
   `crm_spectral6` (7.14).
3. VAR: CV alpha with damping 0.5 / 1, alpha 0.1, and fixed regions with damping 0.5. After seeing
   that a single regional CDD shift in F-days hurt cool cities, I added `var_city_scale`
   (4 rows). After seeing the per-metric skills, I added the hottest-day-only VAR (2 rows).
   **These last two steps were chosen after seeing official-fold results.**
4. 5.5 levels on `crm_spectral6` and on the hottest-day VAR row. The first `regional_eb`
   version moved complete cities by up to 0.16 because its anomaly baseline was inconsistent.
   A unit test caught it. I replaced it with the two-way fit before the recorded run, and the
   earlier EB numbers were discarded.
5. Row 8: `city_static.parquet` appeared during the run, so the urban covariate was added on
   `crm_spectral6` and on the row-7 candidate.
6. Robustness check on 7 cut-offs for all rows. The hottest-day VAR failed it (below). The
   per-metric gate then gives `crm_s6_eb_urban` (row 8 without VAR). **This row was built
   after seeing every other row, including the 7-cut-off results.** Its components were each
   scored first, and they touch different metrics, so the combination adds no new freedom
   beyond the choice itself.

Rows tried: 27 CRM variants plus 3 references. With 3 folds the best of 27 is flattered.

## Results (raw score; official folds 1980/1995/2011; 7 cut-offs add 1985/1990/2000/2005)

| Row | Forecaster | all | yrs 1-3 | yrs 4-7 | 4-7 by fold (1980/1995/2011) | 7-cut all | 7-cut yrs 4-7 |
|---|---|---|---|---|---|---|---|
| 1 | thirty_year_mean | 0.00 | 0.00 | 0.00 | 0 / 0 / 0 | 0.00 | 0.00 |
| 2 | current_best | 2.92 | 0.63 | 4.68 | -1.93 / 8.02 / 7.95 | 2.74 | 3.27 |
| 3 | champion | 4.14 | 0.33 | 6.92 | -2.60 / 8.63 / 14.72 | 4.49 | 5.82 |
| 4 | crm_fixed_k0 | 4.14 | 0.33 | 6.92 | identical to champion | 4.49 | 5.82 |
| 4 | crm_fixed_k05 | 4.19 | 0.38 | 6.97 | -2.46 / 8.65 / 14.72 | 4.57 | 5.91 |
| 4 | crm_fixed | 4.24 | 0.44 | 7.01 | -2.34 / 8.64 / 14.73 | 4.62 | 5.97 |
| 4 | crm_fixed_cdd_slope | 4.12 | 0.38 | 6.86 | -2.36 / 8.46 / 14.47 | 4.46 | 5.77 |
| 4 | crm_fixed_cdd_rescaled | 4.19 | 0.44 | 6.94 | -2.21 / 8.37 / 14.65 | 4.50 | 5.81 |
| 5 | crm_spectral4 | 4.23 | 0.38 | 7.04 | -2.21 / 8.63 / 14.71 | 4.63 | 5.98 |
| 5 | crm_spectral5 | 4.31 | 0.49 | 7.10 | -2.21 / 8.81 / 14.71 | 4.62 | 5.95 |
| 5 | **crm_spectral6** | 4.30 | 0.42 | 7.14 | -1.98 / 8.66 / 14.73 | 4.65 | 6.02 |
| 5 | crm_spectral4/5/6_cdd_rescaled | 4.30 / 4.31 / 4.23 | 0.43 / 0.50 / 0.37 | 7.13 / 7.09 / 7.06 | | 4.59 / 4.56 / 4.54 | 5.92 / 5.88 / 5.88 |
| 6 | crm_fixed_var05 | 4.22 | 0.39 | 7.01 | | 4.63 | 5.97 |
| 6 | crm_s6_var (CV, damping 1) | 4.14 | 0.06 | 7.14 | | 4.51 | 6.02 |
| 6 | crm_s6_var05 | 4.24 | 0.28 | 7.14 | | 4.59 | 6.02 |
| 6 | crm_s6_var_a01 | 4.26 | 0.16 | 7.20 | | 4.46 | 6.05 |
| 6 | crm_s6_var_cs / cs05 | 4.17 / 4.25 | 0.14 / 0.32 | 7.14 / 7.14 | | 4.52 / 4.60 | 6.02 / 6.02 |
| 6 | crm_s6_var_a01_cs / cs05 | 4.26 / 4.39 | 0.16 / 0.55 | 7.20 / 7.17 | | 4.42 / 4.71 | 6.06 / 6.04 |
| 6 | crm_s6_var_hot (VAR on hottest day only) | 4.45 | 0.73 | 7.13 | | 4.52 | 6.02 |
| 6 | crm_s6_var_hot05 | 4.40 | 0.64 | 7.13 | | 4.61 | 6.02 |
| 7 | crm_spectral6_seg | 4.31 | 0.46 | 7.12 | | 4.63 | 6.00 |
| 7 | crm_spectral6_eb | 4.33 | 0.45 | 7.17 | -1.93 / 8.68 / 14.75 | 4.68 | 6.06 |
| 7 | crm_s6_var_hot_seg | 4.45 | 0.77 | 7.12 | | 4.51 | 5.99 |
| 7 | crm_s6_var_hot_eb | 4.48 | 0.76 | 7.16 | | 4.56 | 6.05 |
| 8 | crm_spectral6_urban | 4.36 | 0.47 | 7.20 | -1.73 / 8.54 / 14.79 | 4.70 | 6.09 |
| 8 | crm_s6_var_hot_eb_urban | 4.53 | 0.80 | 7.22 | -1.71 / 8.58 / 14.80 | 4.60 | 6.12 |
| gate | **crm_s6_eb_urban** | 4.39 | 0.51 | 7.23 | -1.68 / 8.56 / 14.82 | 4.73 | 6.12 |

`crm_s6_eb_urban` on 7 cut-offs, years 4-7 against the champion: 1980 +0.92, 1985 +0.55,
1990 +0.57, 1995 -0.07, 2000 -0.01, 2005 +0.05, 2011 +0.10. Years 1-3, 7-cut-off mean: 2.62
(champion 2.45, current_best 1.98).

## Per-metric gate (beats the champion on >= 2 of 3 official folds in years 4-7 AND on the 7 cut-offs)

Skill difference from the champion, in skill points, years 4-7.

| Metric | Change | Official folds 1980 / 1995 / 2011 | 7 cut-offs: wins, mean | Verdict |
|---|---|---|---|---|
| temperature | Layer 2, spectral6 | +1.09 / -0.11 / 0.00 | 3 of 7, +0.36 | fails (1 of 3) |
| temperature | Layer 2 + urban | +1.53 / -0.32 / +0.06 | 4 of 7, +0.51 | passes, narrowly (2011 gain is +0.06) |
| CDD | Layer 2, spectral6 | +1.39 / +0.22 / +0.04 | 6 of 7, +0.44 | passes |
| CDD | Layer 2 + urban | +1.96 / -0.04 / +0.24 | 5 of 7, +0.56 | passes |
| precipitation | regional EB level | +0.17 / -0.04 / +0.08 | 5 of 7, +0.04 | passes, but within noise |
| precipitation | segment level | -0.50 / +0.10 / -0.04 | 3 of 7, -0.09 | fails |
| hottest day | regional EB level | +0.01 / +0.12 / +0.02 | 7 of 7, +0.09 | passes, tiny |
| hottest day | segment level | +0.45 / -0.20 / +0.04 | 3 of 7, -0.00 | fails |
| hottest day | VAR (alpha 0.1), years 1-3 | -1.36 / +1.87 / +3.22 | 3 of 7, **-1.11** | fails: 1985 -2.3, 1990 -7.0, 2000 -3.1 |

## Fitted k_r (k_scale 1)

Temperature, both region sets: tau^2 = 0 at 2011 and 2018. **Every k_r is 0 there, so the CRM
temperature trend is the pooled trend.** At 1980 tau^2 = 5e-4 and k_r = 0.66-0.89. At 1995
tau^2 = 1e-4 and k_r = 0.21-0.44.

| Fixed regions, temperature k_r | 1980 | 1995 | 2011 | 2018 |
|---|---|---|---|---|
| North Central | 0.66 | 0.30 | 0 | 0 |
| Northeast | 0.79 | 0.33 | 0 | 0 |
| Northwest | 0.85 | 0.34 | 0 | 0 |
| South Central | 0.84 | 0.38 | 0 | 0 |
| Southeast | 0.87 | 0.34 | 0 | 0 |
| Southwest | 0.83 | 0.44 | 0 | 0 |
| pooled slope (F/yr) | 0 (raw -0.026) | 0.025 | 0.038 | 0.050 |

| Fixed regions, CDD k_r | 1980 | 1995 | 2011 | 2018 |
|---|---|---|---|---|
| North Central | 0.84 | 0.69 | 0.62 | 0.56 |
| Northeast | 0.86 | 0.72 | 0.59 | 0.60 |
| Northwest | 0.97 | 0.86 | 0.89 | 0.86 |
| South Central | 0.67 | 0.68 | 0.41 | 0.47 |
| Southeast | 0.79 | 0.67 | 0.57 | 0.51 |
| Southwest | 0.81 | 0.70 | 0.65 | 0.63 |
| tau^2 | 13.5 | 8.3 | 5.2 | 4.9 |

Spectral K = 6, CDD k_r per fold: 1980 0.74-0.94, 1995 0.65-0.80, 2011 0.28-0.69, 2018
0.25-0.60 (tau^2 13.6, 6.5, 1.9, 1.6). Temperature k_r follows the fixed pattern: 0.71-0.89,
then 0.21-0.35, then 0, then 0. Cluster labels are arbitrary per fold, but the groups are
stable. In every fold they are Upper Midwest (about 43N 92W, 54-60 cities), Northeast /
Mid-Atlantic (40N 77W), Southeast (32N 86W), Plains (36-38N 99-104W), Pacific Northwest
(45N 119W) and California / Southwest (35-36N 117W).

Raw regional CDD slopes (F-days/yr) at 2018, fixed: North Central 2.9, Northeast 5.6,
Northwest 4.9, South Central 10.1, Southeast 9.5, Southwest 9.8, against pooled 6.3.

Urban gamma (F/yr per unit log-growth), positive at every cut-off: 1980 0.017, 1985 0.011,
1990 0.027, 1995 0.025, 2000 0.018, 2005 0.016, 2011 0.024, 2018 0.039.

## VAR sparsity

Panel: 6 spectral regions x 4 metrics = 24 series, 40 years, 576 possible entries.

| Cut-off | CV alpha: non-zero (same-region) | by target metric | alpha 0.1: non-zero |
|---|---|---|---|
| 1980 | 34 (6) | temp 7, CDD 8, hottest 18, precip 1 | 176 |
| 1995 | 39 (6) | temp 26, CDD 3, precip 10 | 194 |
| 2011 | 23 (7) | temp 3, CDD 8, precip 12 | 187 |
| 2018 | 22 (3) | temp 2, CDD 8, precip 12 | 172 |

Largest |coefficient| 0.31-0.46 in standardized units. With CV, hottest day has no non-zero
equation after 1980, and most entries are cross-region and cross-metric. Their signs change
from fold to fold (for example the 2011 and 2018 hottest-day equations at alpha 0.1). That is
what a lasso fitting noise in 39 samples looks like.

## Effect on the 2019-2025 forecast (cut-off 2018, compared with the champion, no scoring)

| Forecaster | temperature | CDD | precip | hottest day |
|---|---|---|---|---|
| crm_spectral6 | 0 rows change | 14 rows (2 sparse cities on the fallback slope), mean abs 0.21 F-days | 0 | 0 |
| crm_s6_eb_urban | mean abs 0.028 F, max 0.29 | mean abs 3.3 F-days, max 46 | 308 rows, mean abs 0.025 in | 308 rows, mean abs 0.012 F |

The Space's noise level for CDD MAE is about 10 F-days. **On the real forecast the CRM is
practically the champion.**

## Why

- **Layer 2 gains come from the early folds, not the recent ones.** At 1980-1990 the 40-year
  pooled slope is near zero or negative (mid-century cooling) and is floored at 0. The West
  (Northwest +0.003, Southwest +0.022 F/yr at 1980) was warming while the East cooled. The
  regional spread is then larger than its sampling error, so tau^2 > 0 and k_r is high. The
  western regions keep a positive trend and the rest stay at 0. That is the +1.1 temperature
  and +1.4 CDD skill at 1980, and the +0.4-0.6 raw gain at 1985-1990. By 2005 (partly already at
  2000, where the shrunk slopes cost -0.19 skill) the regional temperature slopes (0.018-0.047 at 2011) lie within about one clustered standard error
  (0.010-0.017) of the pooled 0.038. tau^2 falls to 0 and the CRM gives back the pooled slope:
  0.00 change at 2005, 2011 and 2018. This agrees with the earlier finding that free regional
  slopes lose: regional trend differences in recent decades are noise at this sample size.
- **CDD keeps real regional signal** (k_r 0.3-0.9 even at 2018: the South warms faster in
  CDD than the North). With the champion's rule (sensitivity x temperature trend) it reaches
  the forecast only through the temperature trend. So the CDD gain tracks the temperature
  gain, plus a few sparse fallback cities. Using the regional CDD slope directly
  (`cdd_slope`, `cdd_rescaled`) lost (6.86 and 6.94 against 7.01). The city sensitivity
  already encodes the warm-South pattern, and the regional CDD slope only adds noise.
- **Spectral beat fixed regions slightly** (7.14 against 7.01, years 4-7). The clusters split
  California / Southwest from the Pacific Northwest, and the Plains from the Upper Midwest.
  Those are the units that differed in 1980. The gap is within noise.
- **The VAR does not help.** Year-to-year regional anomalies have little persistence once the
  trend is removed: under CV the lasso keeps 22-39 small entries out of 576, almost none for
  temperature. Its CDD shift hurt years 1-3 (CDD skill 4.09 down to 2.9-3.7). The hottest-day
  VAR looked good on the official folds (+1.9 and +3.2 skill at 1995 and 2011). It failed on
  the 7 cut-offs (-7.0 at 1990, -3.1 at 2000, -2.3 at 1985). It was chosen after seeing
  results, and the 7-cut-off check exposed it as noise. Layer 3 cannot reach years 4-7 anyway,
  because A^h decays within 2-3 years. Climate indices (ENSO, PDO) as start states were not
  available.
- **Regional EB levels help a little and consistently** (hottest day 7 of 7 cut-offs, precip
  5 of 7). They change only cities with missing years in the 30-year window. That is 44 of 210
  cities at 2018 (308 rows / 7 years). The size, +0.04 to +0.09 skill, is far below noise. The
  segment level lost (precip -0.09 over 7 cut-offs). A station move does not reset the
  climate that the 30-year reference and the truth are measured against.
- **Urban growth gives a small, physically signed gain.** Gamma is positive at all 8
  cut-offs: faster-growing counties warm faster. It adds +0.5 temperature skill over the
  7 cut-offs, mostly before 1995, and +0.06 at 2011. At 2018 it moves temperature forecasts by
  0.03 F on average.

## Limits and open items

- 27 variants on 3 folds: the best rows are flattered. The gated row was assembled after all
  results were seen. Only the CDD Layer-2 gain passes the gate with some margin, and even that
  gain is concentrated in 1980-1990.
- The trial note records `61b8035 (uncommitted changes)`. It must be re-recorded after the
  commit for a clean code hash.
- The years 1-3 target (beat `current_best` 0.63) was met only by the VAR rows (0.73-0.80),
  and those failed robustness. The gated row scores 0.51 on the official folds but 2.62 against
  1.98 for `current_best` over the 7 cut-offs.
- Not tried: climate-index start states (agent D's `indices_to_2018.parquet` did not exist),
  K > 6, other geo weights, VAR with more lags.
