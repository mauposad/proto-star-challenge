# Alternative climate normals (OCN, EWMA, damped trend) and a nonstationary GEV for the hottest day

One card for a group of closely related methods: P02, P03 and P04 in
[docs/literature/README.md](../../docs/literature/README.md) (how to set a "normal" when the
climate is not stationary), plus P23 (a nonstationary GEV for annual maxima).

| | |
|---|---|
| **Authors** | P02: J. Huang, H. M. van den Dool, A. G. Barnston. P03: D. S. Wilks. P04: D. S. Wilks, R. E. Livezey. P23: UCAR / NCAR extremes toolkit course notes (E. Gilleland et al.) |
| **Year / venue** | P02: 1996, *J. Climate* 9, 809–817. P03: 2013, *J. Appl. Meteor. Climatol.* 52, 289–302. P04: 2013, *J. Appl. Meteor. Climatol.* 52(8), 1677–1687. P23: course notes, undated |
| **Link** | P02: DOI not checked (see V02 in the literature list). P03: [10.1175/JAMC-D-11-0267.1](https://doi.org/10.1175/JAMC-D-11-0267.1). P04: [10.1175/JAMC-D-13-026.1](https://doi.org/10.1175/JAMC-D-13-026.1). P23: <https://projects.ral.ucar.edu/extremes/Extremes/eva1.pdf> |
| **Code released by authors** | none (P23's notes use the R package `extRemes`; we did not use it) |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p02-p04-p23-normals` (no PR) |

## Summary

A climate "normal" is the level you expect next year. The official one is a 30-year mean,
which lags a warming climate. **P02** (Huang et al. 1996) introduced the *optimal climate
normal* (OCN): the mean of the most recent *k* years, with *k* chosen by hindcast skill, which
for US seasonal temperature came out near 10 years. **P03** (Wilks 2013) tested window
lengths and simple trend fits for projecting normals and found that a roughly 15-year mean is
hard to beat. **P04** (Wilks & Livezey 2013) compared eleven alternatives to the 30-year mean
(including the 15-year mean, OCN, hinge fits, exponentially weighted averages and trend
extrapolations) on independent 2006–12 US data; the 15-year mean (CPC15) was the best single
method and a hinge-based hybrid a close alternative. **P23** treats the hottest day of the
year as a block maximum: a generalized extreme value (GEV) distribution whose location
parameter changes linearly with time, fitted by maximum likelihood.

The full texts of P03 and P04 were behind a paywall for this agent. The method descriptions
here come from the abstracts, citing sources and standard definitions. Details we could not
check are marked as deviations, not as the papers' choices.

## Architecture

Statistical, per series (one city and one metric), no learned weights shared across cities.

- **OCN** (P02/P03): `mean(last k valid years)`, held flat over the 7 forecast years.
  *k* from a candidate list is chosen by pooled hindcast MAE.
- **EWMA** (P04): `m_0 = x_0`, `m_i = alpha * x_i + (1 - alpha) * m_{i-1}` over the valid
  years, held flat. `alpha` fixed, or chosen from a list by the same hindcast.
- **Damped trend** (P04's trend family, with damping): `mean(last k) + phi * slope * (t - t_k)`,
  where `slope` is the OLS slope over the last 30 calendar years and `t_k` the mean year of the
  *k*-year window. `phi` in {0, 0.25, 0.5, 1} by hindcast (`phi = 0` is the *k*-year mean).
- **Nonstationary GEV** (P23): `X_t ~ GEV(mu0 + mu1 (t - t_bar)/10, sigma, xi)` on the valid
  years of the last `window` calendar years, own MLE (Nelder–Mead, `xi` bounded to
  [-0.5, 0.3]). The forecast is the fitted median (the MAE-optimal point), or mean or a
  quantile. The trend is multiplied by `trend_shrink`, fixed or chosen by hindcast.
- **Hindcast selection** (P02's recipe): inside the fold's training years only, pseudo-origins
  at `cutoff - 7`, `cutoff - 14`, ... each forecast their next 7 years; lowest pooled MAE wins,
  per metric (all cities), per region (6 NOAA regions) or per city.

## Results claimed by the authors

Not our results; quoted from the abstracts and citing sources only.

- P02: OCN beats the 30-year normal for US seasonal temperature at long leads; optimal
  window around 10 years for temperature (TBD: exact numbers not checked).
- P03 / P04: for US temperature normals, the most recent 15-year mean (CPC15) was the best
  single method in 2006–12 independent data; a 15-year-mean / hinge hybrid was a useful
  alternative; relative performance depended on the temperature dataset.
- P23: method notes, no claim.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data: US climate-division or station seasonal temperatures | 210 US cities, annual indices from the master table (≤ 2018), valid years only |
| Target(s): seasonal mean temperature (P02–P04); annual maxima (P23) | `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd`; GEV only for `hottest_day_temp` |
| Horizon: one season to one year ahead (P02, P04: 2006–12) | 7 years (2019–2025), backtest folds 1980 / 1995 / 2011 (ADR 0004) |
| Metric: skill / RMSE vs the 30-year normal | relative MAE skill vs the 30-year calendar mean, mean over the 4 metrics |
| Cut-off | 2018-12-31; every fit uses only the fold's `train` frame |

## Deviations

- **Annual, not seasonal.** We forecast annual indices, 1–7 years ahead, not seasonal means.
- **Selection target.** Windows, `alpha` and `phi` are chosen by pooled *MAE* (the challenge
  metric) over in-train pseudo-origins, not by the papers' skill scores.
- **Valid years only.** Windows count the last *k* valid years (as `ten_year_mean` does);
  EWMA ignores gaps. The papers use complete records.
- **Damping.** P04's trend methods are undamped as far as we could check; the damping factor is
  our addition, motivated by `linear_trend`'s poor backtest.
- **GEV.** One stationary scale and shape per city; shape bounded instead of a prior; trend
  shrinkage is our addition, and one shrink factor is shared by all cities in a fold.
- **Hybrid** combining the methods per metric is ours, not from the papers.

## Implementation

- Registry names: `ocn_normal`, `ewma_normal`, `damped_trend_normal` (module
  `src/proto_star/forecasters/normals_p02_p04.py`); `gev_hottest_day`, `normals_hybrid`
  (module `src/proto_star/forecasters/gev_p23.py`)
- Config: `configs/agent_paper_normals_gev.yaml`
- Tests: `tests/test_forecasters_normals_p02_p04.py`, `tests/test_forecasters_gev_p23.py`
- Leakage review: every statistic and every hindcast is computed from the fold's `train` frame
  (years ≤ cutoff). Pseudo-origins and their scored years are all ≤ the cutoff, and
  `hindcast_errors` drops later years even if given them. Tests perturb post-cutoff values and
  check the forecasts and selected settings do not change. No randomness is used.

## Our results

Same backtest origins as the baseline (ADR 0004: 1980, 1995, 2011; 7-year horizon), official
relative-MAE skill vs the 30-year mean, `raw_score` = unfloored score. Full tables, all 18
forecasters: [docs/trials/paper_normals_gev.md](../../docs/trials/paper_normals_gev.md).

Raw score per origin (all 7 years) and means over the three origins:

| Method | 1980 | 1995 | 2011 | Mean all | Mean years 1–3 | Mean years 4–7 | Origins beating `current_best` (all / 4–7) |
|---|---|---|---|---|---|---|---|
| `current_best` | -0.75 | 3.56 | 5.95 | 2.92 | 0.63 | 4.68 | — |
| `ten_year_mean` | -2.53 | 1.39 | 5.16 | 1.34 | -0.62 | 2.78 | 0 / 0 |
| `ocn` (P02, per metric) | -1.41 | 2.25 | 6.22 | 2.35 | 0.49 | 3.68 | 1 / 1 |
| `ocn_region` | -3.47 | 0.98 | 6.15 | 1.22 | 0.11 | 1.97 | 1 / 1 |
| `ocn_city` | -2.70 | 0.63 | 3.71 | 0.55 | -0.54 | 1.32 | 0 / 0 |
| `ocn_o8` (8 pseudo-origins) | -4.20 | 1.83 | 6.33 | 1.32 | 0.17 | 2.10 | 1 / 1 |
| `ocn_lead47` | -2.55 | 1.79 | 6.33 | 1.86 | 0.24 | 2.99 | 1 / 1 |
| `ewma_a01` (P04, alpha 0.1) | 0.52 | 2.27 | 2.93 | 1.90 | 1.12 | 2.50 | 1 / 1 |
| `ewma_opt` (alpha by hindcast) | 0.13 | 3.06 | 4.96 | 2.71 | 1.69 | 3.46 | 1 / 0 |
| `ewma_opt_o8` | -0.11 | 3.04 | 5.13 | 2.69 | 1.75 | 3.35 | 1 / 0 |
| `optimal_o4` (k-means vs EWMAs) | -0.89 | 2.54 | 3.92 | 1.85 | 1.19 | 2.37 | 0 / 0 |
| `optimal_o8` | -0.06 | 2.84 | 3.19 | 1.99 | 1.43 | 2.45 | 1 / 0 |
| `damped_trend` (P04 + damping) | -2.53 | 1.39 | 5.16 | 1.34 | -0.62 | 2.78 | 0 / 0 |
| `gev_trend_opt` (P23, shrink by hindcast) | -1.74 | 3.51 | 5.89 | 2.55 | 0.69 | 4.00 | 0 / 1 |
| `gev_shrink25` | -1.02 | 3.40 | 6.13 | 2.84 | 0.81 | 4.43 | 1 / 1 |
| `gev_stationary` | -0.68 | 3.53 | 5.92 | 2.92 | 0.67 | 4.69 | 1 / 2 |
| `gev_stationary_w40` | -0.85 | 3.58 | 5.79 | 2.84 | 0.58 | 4.62 | 1 / 1 |
| `hybrid_a` (post hoc, see below) | 0.45 | 3.99 | 5.31 | 3.25 | 1.14 | 4.90 | 2 / 2 |

Years 4–7 raw score per origin (the Final Score window): `current_best` -1.93 / 8.02 / 7.95;
`hybrid_a` -0.92 / 8.08 / 7.54; `gev_stationary` -1.92 / 7.82 / 8.19; `ocn` -3.36 / 5.68 / 8.73.

Per-metric skill (%), mean over origins, all years / years 4–7:

| Method | annual_avg_temp | total_precip_in | hottest_day_temp | cdd |
|---|---|---|---|---|
| `current_best` | 5.76 / 11.90 | 0.00 / 0.00 | 0.00 / 0.00 | 5.91 / 6.84 |
| `ten_year_mean` | 5.76 / 11.90 | -3.94 / -4.44 | -2.39 / -3.16 | 5.91 / 6.84 |
| `ocn` | 5.42 / 11.35 | -0.39 / -0.69 | -1.94 / -3.00 | 6.32 / 7.08 |
| `ewma_opt` | 3.90 / 6.91 | 0.19 / 0.02 | -0.26 / -0.75 | 7.02 / 7.65 |
| `optimal_o8` | 3.08 / 5.57 | -0.29 / -0.59 | -0.41 / -0.88 | 5.58 / 5.72 |
| `gev_trend_opt` | — | — | -1.47 / -2.73 | — |
| `gev_stationary` | — | — | 0.02 / 0.05 | — |
| `hybrid_a` | 5.76 / 11.90 | 0.19 / 0.02 | 0.02 / 0.05 | 7.02 / 7.65 |

(— = the metric comes from `current_best`, so it equals the first row.)

Windows the OCN hindcast picked (most common choice per metric at each fold cut-off, and at
2018 for the real forecast): temperature k = 10, 10, 12 (12 at 2018); precipitation k = 30,
25, 30 (30); hottest day k = 10, 12, 30 (25); CDD k = 10, 7, 7 (7). EWMA `alpha`: temperature
0.15–0.2, precipitation 0.05, hottest day 0.05–0.15, CDD 0.15–0.2. The damped trend's hindcast
picked `phi = 0` at every fold, so it reduced to the 10-year mean.

`hybrid_a` = 10-year mean for temperature, hindcast-chosen EWMA for precipitation and CDD,
stationary GEV median for the hottest day. Its components were chosen *after* seeing the
per-metric results of this trial, so its score is optimistic.

Command: `uv run proto-star climate-trial configs/agent_paper_normals_gev.yaml --record`, at
base commit `e507f5e` with this branch's new files (uncommitted at run time), master content
hash `99128065…bb04d1`. Run dir `runs/trials/20261106-235314_paper_normals_gev` (git-ignored).
Wall time about 11 minutes, one process.

## Takeaways

- **No paper method beats `current_best`.** Fixed baselines chosen per metric (10-year mean
  for temperature/CDD, 30-year mean for the rest) are already close to "optimal normals" on
  this data. Choosing the window by in-train hindcast (OCN) does not transfer well: it picks
  shorter windows for precipitation and the hottest day than the 30-year mean, and those lose.
  Finer scopes (region, city) are worse: more noise in the choice.
- **EWMA helps CDD and the early years.** Hindcast-chosen EWMA is the best single method
  for CDD (7.65 % vs 6.84 % in years 4–7) and for years 1–3 (1.69 vs 0.63), but is much
  worse for annual temperature in years 4–7 (6.91 % vs 11.90 %). The CDD gain in years 4–7
  comes from 1980 only (-0.14 % vs -3.65 %); it loses slightly at 1995 and 2011.
- **Trends still extrapolate badly, even damped.** The damped trend's hindcast always chose
  no trend. The GEV location trend hurts the hottest day even when shrunk; the hindcast
  choice of shrink (`gev_trend_opt`) is worse than a fixed 0.25, which is worse than none.
- **Stationary GEV median ≈ 30-year mean** for the hottest day (+0.05 % skill in years 4–7):
  a tie, not a gain.
- **Decision:** keep `current_best` as the submission (`submit: current_best`). `hybrid_a`
  has the highest mean (all 3.25, years 4–7 4.90) but beats `current_best` in years 4–7 only at
  1980, ties at 1995, loses at 2011, and was picked post hoc. Worth re-testing on more origins
  if ADR 0004 ever adds any. Status: **adapted**, not adopted.
