# Papers

Research papers we study and **reproduce inside this repo**. Each paper gets one folder that
records what the paper proposes, how we implemented it, and how it scored on *our* challenge,
compared like-for-like with our baselines.

The aim is a single place to answer three questions: *which architectures have we tried, how
faithful was each reproduction, and did it beat the current best?*

## Index

One row per paper, newest first. Update the row whenever a paper's status or score changes.
Leave a cell as `TBD` until a real run produces the number; never copy scores from the paper.

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| `2018_makridakis_combinations` | Makridakis et al., M4 (P16); Smith & Wallis forecast combination puzzle via Qian et al. (P17); Wang et al. combination review (P18) | 2018, 2009, 2022 | Forecast combination of registered forecasters per metric: equal mean, median, trimmed, in-train inverse-MSE weights | adapted | `configs/agent_paper_combos_p16_p17.yaml` | best `combo_mean_cdd_only`: 0.16 / 4.14 / 6.18 (1980/1995/2011); mean 3.49 all, 5.37 years 4–7 | better at 3/3 origins (-2.53 / 1.39 / 5.16) | Beats `current_best` (2.92 / 4.68) but not `hybrid_ridge_all_cdd` (3.60 / 5.54). Errors highly correlated; equal ≈ estimated weights; no DeepAR needed. Not adopted |
| `2020_cerqueira_rolling_origin_evaluation` | Cerqueira et al. performance estimation (P19), Hyndman & Athanasopoulos rolling origin (P12), Bergmeir & Benítez blocked CV (P10) | 2012–2020 | Evaluation design: rolling forecasting origins, no forecaster | adapted | `configs/agent_fold_study_p10_p12_p19.yaml` | n/a (study). Years 4–7, 12 origins: `hybrid_ridge_all_cdd` 3.97, `current_best` 3.21 | `ten_year_mean` 2.27 on 12 origins | 3 ADR origins and 12 rolling origins agree in years 4–7 (tau 0.93); recency weights do not change the pick; ADR origins overstate levels. Proposed ADR 0006: keep ADR 0004 folds and add the dense check |
| `2025_eia_steo_cdd` | EIA STEO weather model note (P06), with CDD recomputed from shifted daily data (replication step 9) | 2025 | Statistical: per-city 30-year CDD trend line (EIA); CDD regressed on annual temperature; daily Tmean climatology shifted by a temperature forecast, CDD recomputed at 65 °F | adapted | `configs/agent_paper_cdd_forcing_p06_p21.yaml` | best of these `eia_cdd_on_temp_recent` -0.11 / 3.89 / 4.67 (1980/1995/2011; mean 2.82 all, 4.68 years 4–7); `shift30_recent` 2.63 / 4.65; `eia_trend30` -0.33 / 0.65 | `eia_cdd_on_temp_recent` better at 2/3 origins (-2.53 / 1.39 / 5.16) | No variant beats `current_best` (2.92 / 4.68) on the mean or `hybrid_ridge_all_cdd` (3.60 / 5.54). The convexity is real but tiny (+0.02 to +0.08 CDD skill points). Not adopted |
| `2013_ho_forced_trend_ar1` | Ho, Hawkins, Shaffrey & Underwood, statistical decadal SST benchmark: forced trend + AR(1) (P21; P20 context) | 2013 | Statistical: per-city OLS on log NOAA Mauna Loa CO2 (or a regional-mean temperature anomaly) plus an AR(1) residual; temperature and CDD | adapted | `configs/agent_paper_cdd_forcing_p06_p21.yaml` | `p21_co2_ar1` -4.26 / 1.53 / 8.58 (1980/1995/2011; mean 1.95 all, 3.25 years 4–7); `p21_regional_ar1` -6.73 / 3.48 / 7.38 (1.38 / 2.78) | `p21_co2_ar1` better at 2/3 origins (-2.53 / 1.39 / 5.16) | Big win at 2011, big loss at 1980: the trend extrapolates the fit window. Temperature skill in years 4–7 10.0 % vs 11.9 % for the 10-year mean. CO2 data would not rebuild on CI. Not adopted |
| `2020_haug_regional_trends` | Haug et al., spatial (hierarchical) trend analysis (P22), with Hausfather et al. 2013 urbanization groups (P24) | 2020, 2013 | P22: city trends shrunk to the regional trend by empirical-Bayes partial pooling, damped, on the 10-year level. P24: round-1 pooled ridge with region / elevation / population / land-cover pooling groups | adapted | `configs/agent_paper_regional_p22_p24.yaml` | best `p24_ridge_population_interact`: 0.17 / 4.21 / 6.45 (1980/1995/2011); mean 3.61 all, 5.55 years 4–7. Best P22 `p22_region_trend_damped`: -2.21 / 3.58 / 7.86; 3.08 / 5.24 | better at 3/3 origins (P24); P22 2/3 (-2.53 / 1.39 / 5.16) | Ties `hybrid_ridge_all_cdd` (3.60 / 5.54): groups add nothing. Regional trend loses at 1980 (negative 1951–1980 trends). Not adopted |
| `2009_menne_pairwise_homogenization` | Menne & Williams, pairwise homogenization (P15) | 2009 | Statistical: station-segment levels and pairwise neighbor step adjustment of documented station switches, then the `current_best` window means | adapted | `configs/agent_paper_station_p15.yaml` | best P15-only `adj_temp_cdd_k10_w10`: -0.57 / 3.60 / 5.95 (1980/1995/2011); mean 2.99 all, 4.75 years 4–7 | better at all 3 origins (-2.53 / 1.39 / 5.16) | Beats `current_best` (2.92 / 4.68) by under 0.1 point: only 39 of 630 city-origins have a switch in the window. With the pooled ridge CDD, `adj_temp_k5_w5_ridge_cdd` 3.61 / 5.53 ties `hybrid_ridge_all_cdd` (3.60 / 5.54). Not adopted |
| `2021_montero-manso_global_pooled` | Montero-Manso & Hyndman, global vs local (P14), with median/quantile regression (P09) | 2021 | Global linear AR (ridge / pinball-0.5 quantile regression) and quantile GBM, pooled over cities, direct multi-horizon | adapted | `configs/agent_paper_p09_p14_pooled.yaml` | `hybrid_ridge_all_cdd`: 0.24 / 4.13 / 6.44 at 1980/1995/2011 (mean 3.60; years 4–7 5.54) | -2.53 / 1.39 / 5.16 (mean 1.34): better at 3/3 origins | Helps CDD only. Temperature, precipitation and hottest day stay on `current_best`. The median loss did not beat squared loss. `current_best` is -0.75 / 3.56 / 5.95 |
| `2020_salinas_deepar` | Salinas et al., DeepAR (P08) | 2020 | Global autoregressive LSTM, Gaussian likelihood, median of sample paths | `adapted` | `configs/agent_paper_neural.yaml` | best `deepar_hybrid`: −0.91 / 3.58 / 7.40 (1980/1995/2011); mean 3.36 all, 5.08 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Best mean of the neural track but wins years 4–7 at 1 of 3 origins; seed-7 replica 3.03 / 4.63. Not adopted; revisit with more seeds |
| `2019_oreshkin_nbeats` | Oreshkin et al., N-BEATS (P05) | 2019 | MLP residual backcast/forecast blocks (generic; trend + generic), median ensemble | `adapted` | `configs/agent_paper_neural.yaml` | best `nbeats_hybrid`: −0.74 / 4.10 / 5.87 (1980/1995/2011); mean 3.08 all, 4.57 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Does not beat `current_best` (2.92 / 4.68); seed-7 replica 2.88 / 4.03. Full-metric variants lose on precip/hottest day |
| `2013_wilks_livezey_normals` | Huang et al. 1996 (P02), Wilks 2013 (P03), Wilks & Livezey 2013 (P04): optimal / alternative climate normals | 1996, 2013 | Statistical normals: OCN window by in-train hindcast, EWMA, damped trend | adapted | `configs/agent_paper_normals_gev.yaml` | best paper method `ewma_opt` 2.71 all / 3.46 yrs 4–7 (`current_best` 2.92 / 4.68) | beats (1.34 / 2.78) | Per-origin `ocn` -1.41 / 2.25 / 6.22, `ewma_opt` 0.13 / 3.06 / 4.96. EWMA best for CDD and years 1–3; worse for temperature in years 4–7. Not adopted |
| `2013_wilks_livezey_normals` | UCAR extremes notes (P23): nonstationary GEV with a location trend | n/a | GEV MLE, location trend shrunk, median forecast, hottest day only | adapted | `configs/agent_paper_normals_gev.yaml` | `gev_stationary` 2.92 all / 4.69 yrs 4–7; with trend `gev_trend_opt` 2.55 / 4.00 | beats (1.34 / 2.78) | Per-origin `gev_stationary` -0.68 / 3.53 / 5.92. Trend hurts even when shrunk; stationary median ties the 30-year mean. Not adopted |
| `2020_lai_arima` | Lai & Dzombak, ARIMA near-term regional temperature and precipitation forecasts (WAF) | 2020 | Statistical: per-series ARIMA (KPSS + stepwise AICc, Mann-Kendall drift, Box-Cox) | adapted | `configs/agent_paper_p13_arima.yaml` | -2.59 / 0.37 / 3.01 (1980/1995/2011) | worse: `ten_year_mean` -2.53 / 1.39 / 5.16 | Lost to `current_best` at every origin and window. Years 4–7 mean 1.06 against 4.68. CDD skill slightly better in years 4–7 at 1 of 3 origins. Not submitted |

**Status** values:

| Status | Meaning |
|---|---|
| `reading` | Paper card written, nothing implemented yet |
| `implementing` | Code in progress on a branch |
| `reproduced` | Runs end to end through the official backtest; result logged |
| `adapted` | Reproduced with documented deviations (data, targets, horizon, scale) |
| `abandoned` | Stopped. The card says why (keep it: negative results are results) |

## Folder layout

```
papers/
  README.md                      # this file: index + conventions
  _template.md                   # copy to start a new paper card
  <year>_<first-author>_<short-name>/
    README.md                    # the paper card (required)
    figures/                     # optional: our plots reproducing the paper's figures
```

Folder names are lowercase with underscores, e.g. `2023_lam_graphcast`.

## What lives where

Implementations follow the normal repo rules (see `AGENTS.md`). The paper folder is
documentation and provenance; it must not become a second codebase.

| Thing | Location |
|---|---|
| Paper card (summary, architecture, deviations, results) | `papers/<folder>/README.md` |
| Model code | one module in `src/proto_star/forecasters/`, registered with `@register_forecaster` (see `forecasters/registry.py`); heavy imports inside the factory |
| Paper-specific features / preprocessing | `src/proto_star/data/` (reusable, tested) |
| Hyperparameters | `configs/<initials>_paper_<short-name>.yaml`, under `variants: {name: {forecaster: ..., params: {...}}}` |
| Tests | `tests/`, mirroring the module tested |
| Run outputs | `runs/` (git-ignored, produced by the CLI only) |
| Every result, including failures | a row in `docs/experiments.md` **and** the index above |
| Decision to adopt a paper's method for submission | an ADR in `docs/decisions/` |

## The paper PDFs

Do **not** commit PDFs by default. Most papers are copyrighted, and the pre-commit hook rejects
files larger than 1 MB. Put a DOI or arXiv link in the card instead. A PDF may be committed only
if its license allows redistribution (e.g. CC-BY on arXiv) and it is under 1 MB; state the license
in the card. Keep a personal copy outside git otherwise.

## How to reproduce a paper

1. **Card first.** Copy `_template.md` to `papers/<folder>/README.md`. Fill in the citation,
   link, the problem the paper solves, its architecture, inputs and outputs, and the results
   *as claimed by the authors*. Add the index row with status `reading`.
2. **Map it to our problem.** Write down how the paper's setup maps to ours: inputs (annual
   indices, daily data, station metadata), targets (the four `proto_star.climate.METRICS`),
   horizon (7 years, 2019–2025), and the 2018 cutoff. Every mismatch goes under
   *Deviations*.
3. **Implement through the package.** Add the model to the registry, put hyperparameters in a
   config, and add tests. Follow the leakage rules in `AGENTS.md`: backward-looking features
   only, scalers fitted on training rows, no data after the cutoff.
4. **Score it the same way as everything else.** Use the official relative-skill metric on
   the rolling backtest origins (1980, 1995, 2011; 7-year horizon), using
   `proto_star.backtest` as shown in `notebooks/README.md`. Report the per-origin scores and the
   per-metric skill, with forecast years 4–7 separately. Always compare with `ten_year_mean` and
   the current best on the same origins, and record the commit and how the score was produced.
5. **Log the result.** Add a row to `docs/experiments.md`, update the index row, and fill the
   card's *Our results* section, **including when it is worse than the baseline**.
6. **Never tune on the leaderboard.** Select settings on the backtest only. Leaderboard
   submissions are made by a human, not by an agent.

## Scoring reference

Baseline: **`ten_year_mean`**. Its raw scores by backtest origin (from ADR 0004) are
-2.53 (1980), 1.39 (1995) and 5.16 (2011). The current best is the metric ensemble:
-0.75, 3.56 and 5.95. A paper beats the baseline only if it
improves on these across origins, not at one origin.
