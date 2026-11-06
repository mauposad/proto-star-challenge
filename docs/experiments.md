# Experiment log

Record every run worth discussing, **including failures**. Newest first.
Validation metrics come from `runs/<run>/metrics.json`. List the official metric first.

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-06 | agent | `evaluate_metric_ensemble.py` | uncommitted | metric-specific | — | — | Backtest-selected ensemble: 10-year mean for annual temperature/CDD, 30-year climatology for precipitation/hottest day; score 3.02, 3.33, 1.56, 6.74 at 1997/2002/2007/2011 origins |
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | 10-year mean was the only baseline with positive relative skill across all four 7-year rolling origins; see ADR 0002 |
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | Linear trend improved temperature/CDD in the 2011 origin but underperformed on precipitation across all origins |
| 2026-11-05 | setup | `configs/hist_gbm.yaml` | — | 1.748 | 2.143 | — | Synthetic data, sanity check |
| 2026-11-05 | setup | `configs/baseline.yaml` | — | 6.138 | 7.022 | — | Synthetic data, mean baseline |

## Leaderboard submissions

| Date | Who | Run dir | Public score | Notes |
|---|---|---|---|---|
