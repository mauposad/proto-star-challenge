# Rows to merge (orchestrator)

This track may only add files, so these rows were not appended to the shared tables. Paste each
row into the table named, unchanged.

## (a) `docs/experiments.md`, experiments table

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | agent | `configs/agent_paper_p09_p14_pooled.yaml` | `07d6c39` | metric-specific | — | — | Papers P14 + P09: model pooled over the 210 cities, direct leads 1-7, on per-series normalized lags and trailing means plus Lat/Lon/region. ADR 0004 folds. Mean raw score, all / years 1–3 / years 4–7: `current_best` 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / -0.62 / 2.78, **`hybrid_ridge_all_cdd` (pooled ridge for CDD only) 3.60 / 0.94 / 5.54, beating `current_best` at 3/3, 2/3 and 3/3 origins**. Median (pinball 0.5) `pooled_ql` 2.22 / 1.79 / 2.21, `hybrid_ql_cdd` 3.20 / 0.85 / 4.90, `pooled_ql_all_history` 0.69 / -2.04 / 2.43, `pooled_ql_lags20` 1.37 / 1.65 / 0.90. Ridge: `pooled_ridge_all_history` 2.75 / 1.03 / 3.76. Quantile GBM: `pooled_hgb` 0.93 / 1.13 / 0.56, `pooled_hgb_all_pool_metrics` 2.19 / 1.22 / 2.80. Pooling helps CDD (years 4–7 skill up to 10.3% vs 6.8%) but loses to the 10-year mean for temperature and to the 30-year mean for precipitation and hottest day. Squared loss beat the median loss. Chosen from 15 variants, so expect some selection optimism. Write-up: `docs/trials/paper_p09_p14_pooled.md`, card `papers/2021_montero-manso_global_pooled/README.md` |

## (b) `papers/README.md`, index table

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| `2021_montero-manso_global_pooled` | Montero-Manso & Hyndman, global vs local (P14), with median/quantile regression (P09) | 2021 | Global linear AR (ridge / pinball-0.5 quantile regression) and quantile GBM, pooled over cities, direct multi-horizon | adapted | `configs/agent_paper_p09_p14_pooled.yaml` | `hybrid_ridge_all_cdd`: 0.24 / 4.13 / 6.44 at 1980/1995/2011 (mean 3.60; years 4–7 5.54) | -2.53 / 1.39 / 5.16 (mean 1.34): better at 3/3 origins | Helps CDD only. Temperature, precipitation and hottest day stay on `current_best`. The median loss did not beat squared loss. `current_best` is -0.75 / 3.56 / 5.95 |
