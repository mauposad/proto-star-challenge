# Experiment log

Record every run worth discussing, **including failures**. Newest first.
Validation metrics come from `runs/<run>/metrics.json`. List the official metric first.

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-08 | Luke + agent | `configs/lc_hybrid.yaml` | `2e94a90` | metric-specific | — | — | Pooled trend (ADR 0007) blended per metric with Mauricio's pooled ridge (ADR 0005), candidates and selection rule fixed in the config before running. Mean raw score on ADR 0004 folds, all / years 1–3 / years 4–7: **`h2_mean_cdd` 4.41 / 0.70 / 7.12** (trend temperature, CDD = mean of trend and ridge), `h1_trend_temp_ridge_cdd` 4.35 / 0.70 / 7.00, `h3_mean_temp_cdd` 4.08 / 1.32 / 6.05, `h4_mean_cdd_hot50` 4.27 / 0.58 / 6.91, `h5_mean_cdd_hot100` 4.01 / 0.37 / 6.56, `trend` 4.14 / 0.33 / 6.92, `ridge_cdd` 3.60 / 0.94 / 5.54. 7 cut-offs (diagnostic): h2 4.62, trend 4.49. h2 meets all three parts of the rule. The new hottest-day sensitivity trend lost skill at both strengths (−0.57 and −1.59 points of hottest-day skill), so hottest day stays on the 30-year mean. Write-up: `docs/trials/hybrid.md` |
| 2026-11-06 | Luke + agent | `configs/lc_pooled_trend.yaml` | uncommitted | metric-specific | — | — | Pooled trend on ADR 0004 folds. Mean raw score, all years / years 1–3 / years 4–7: `trend_level10_15_sensitivity` 4.14 / 0.33 / 6.92, `trend_level10` 4.15 / 0.18 / 7.06, `trend_level10_15` 4.02 / 0.29 / 6.76, `current_best` 2.92 / 0.63 / 4.68. Beats `current_best` overall but not in years 1–3. Over 7 cut-offs (diagnostic only): 4.49, 4.12, 4.39, 2.74. Write-ups: `docs/trials/pooled_trend.md`, `docs/trials/pooled_trend_exploration.md` |
| 2026-11-06 | agent | `configs/mp_baselines_round1.yaml` | uncommitted | metric-specific | — | — | Finished the baseline set on the ADR 0004 folds. Mean raw score, all years / years 1–3 / years 4–7: `current_best` 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / -0.62 / 2.78, `fifteen_year_mean` 0.88 / 0.10 / 1.49, `thirty_year_median` -0.69 / -0.31 / -0.94, `ten_year_median` -0.23 / -1.97 / 1.06, `fifteen_year_median` -0.53 / -1.06 / -0.06, `linear_trend` -12.76 / -10.12 / -15.15, `hinge_fit` -19.83 / -13.96 / -25.27. No new baseline beat `current_best` at any window. Hinge fit (hinge year fit per series) extrapolates badly, as `linear_trend` does. Write-up: `docs/trials/baselines_round1.md` |
| 2026-11-06 | agent | `compare_baselines.py` | uncommitted | metric-specific | — | — | Kickoff cut-offs 1980, 1995, 2011 (ADR 0004). Mean raw score, all years / years 1–3 / years 4–7: ensemble 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / -0.62 / 2.78, `linear_trend` -12.76 / -10.12 / -15.15. Same methods selected. Older rows use other cut-offs |
| 2026-11-06 | agent | `compare_baselines.py` | uncommitted | metric-specific | — | — | Shared scorer in `proto_star.backtest` reproduces the logged origin scores. Mean raw score, all years / years 1–3 / years 4–7: ensemble 3.40 / 0.77 / 4.92, `ten_year_mean` 2.48 / -0.35 / 4.15, `linear_trend` -3.84 / -5.75 / -3.35 |
| 2026-11-06 | agent | exploratory forecaster | uncommitted | metric-specific | — | — | 15-year mean for temperature and CDD, 30-year for the rest: 3.43 / 2.36 / 4.13. Beat the ensemble at 3 of 4 origins overall but 1 of 4 in years 4–7, with weaker CDD skill. Not adopted |
| 2026-11-06 | agent | `evaluate_metric_ensemble.py` | uncommitted | metric-specific | — | — | Rerun after ADR 0003 calendar-window fix: ensemble 3.45, 3.33, 0.87, 5.95 and `ten_year_mean` 1.43, 3.01, 0.30, 5.16 at 1997/2002/2007/2011. Scores in older rows used the old reference. CDD practice run now gives 212.9 and 177.4 (published 213 and 177) |
| 2026-11-06 | agent | `evaluate_metric_ensemble.py` | uncommitted | metric-specific | — | — | Backtest-selected ensemble: 10-year mean for annual temperature/CDD, 30-year climatology for precipitation/hottest day; score 3.02, 3.33, 1.56, 6.74 at 1997/2002/2007/2011 origins |
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | 10-year mean was the only baseline with positive relative skill across all four 7-year rolling origins; see ADR 0002 |
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | Linear trend improved temperature/CDD in the 2011 origin but underperformed on precipitation across all origins |
| 2026-11-05 | setup | `configs/hist_gbm.yaml` | — | 1.748 | 2.143 | — | Synthetic data, sanity check |
| 2026-11-05 | setup | `configs/baseline.yaml` | — | 6.138 | 7.022 | — | Synthetic data, mean baseline |

## Leaderboard submissions

| Date | Who | Run dir | Public score | Notes |
|---|---|---|---|---|
