# Rows to merge (P05 N-BEATS)

These rows were not added to the shared tables, so parallel branches do not conflict. The
orchestrator merges them.

## (a) `docs/experiments.md`, experiment log (newest first)

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | agent | `configs/agent_paper_neural.yaml` | `e507f5e` + branch `agent/paper-p05-p08-neural` | metric-specific | — | — | P05 N-BEATS from scratch (CPU, per-metric model, median of lookbacks 14/21/28 × 3 seeds, early stopping on the last 7 training years). Mean raw score, all years / years 1–3 / years 4–7: `nbeats_generic` 2.32 / 0.52 / 3.39, `nbeats_interpretable` 2.25 / 0.92 / 3.04, `nbeats_hybrid` (temperature + CDD only) 3.08 / 0.78 / 4.57, its seed-7 replica 2.88 / 1.23 / 4.03; `current_best` 2.92 / 0.63 / 4.68. Loses on precipitation and hottest day; the hybrid's small edge in all years is seed noise and it trails in years 4–7. Not adopted. Write-up: `docs/trials/paper_neural.md`, card `papers/2019_oreshkin_nbeats/` |

## (b) `papers/README.md`, index

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| `2019_oreshkin_nbeats` | Oreshkin et al., N-BEATS (P05) | 2019 | MLP residual backcast/forecast blocks (generic; trend + generic), median ensemble | `adapted` | `configs/agent_paper_neural.yaml` | best `nbeats_hybrid`: −0.74 / 4.10 / 5.87 (1980/1995/2011); mean 3.08 all, 4.57 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Does not beat `current_best` (2.92 / 4.68); seed-7 replica 2.88 / 4.03. Full-metric variants lose on precip/hottest day |
