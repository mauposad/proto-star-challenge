# Experiment log

Record every run worth discussing, **including failures**. Newest first.
Validation metrics come from `runs/<run>/metrics.json`. List the official metric first.

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | 10-year mean was the only baseline with positive relative skill across all four 7-year rolling origins; see ADR 0002 |
| 2026-11-06 | agent | `climate-backtest` | uncommitted | metric-specific | — | — | Linear trend improved temperature/CDD in the 2011 origin but underperformed on precipitation across all origins |
| 2026-11-05 | setup | `configs/hist_gbm.yaml` | — | 1.748 | 2.143 | — | Synthetic data, sanity check |
| 2026-11-05 | setup | `configs/baseline.yaml` | — | 6.138 | 7.022 | — | Synthetic data, mean baseline |

## Leaderboard submissions

| Date | Who | Run dir | Public score | Notes |
|---|---|---|---|---|
