# Rows to merge (P08 DeepAR)

These rows were not added to the shared tables, so parallel branches do not conflict. The
orchestrator merges them.

## (a) `docs/experiments.md`, experiment log (newest first)

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | agent | `configs/agent_paper_neural.yaml` | `e507f5e` + branch `agent/paper-p05-p08-neural` | metric-specific | — | — | P08 DeepAR from scratch (CPU, one global Gaussian LSTM 2×32 with metric/city embeddings, context 21, median of 3 seeds × 100 sample paths, early stopping on the last 7 training years). Mean raw score, all years / years 1–3 / years 4–7: `deepar_global` 2.39 / 0.25 / 3.87, `deepar_hybrid` (temperature + CDD only) 3.36 / 0.96 / 5.08, its seed-7 replica 3.03 / 0.83 / 4.63; `current_best` 2.92 / 0.63 / 4.68. The hybrid beats `current_best` in years 4–7 only at 2011 (11.09 vs 7.95; loses 1980 and 1995) and the seed replica trails in years 4–7, so `submit` stays `current_best`. Write-up: `docs/trials/paper_neural.md`, card `papers/2020_salinas_deepar/` |

## (b) `papers/README.md`, index

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| `2020_salinas_deepar` | Salinas et al., DeepAR (P08) | 2020 | Global autoregressive LSTM, Gaussian likelihood, median of sample paths | `adapted` | `configs/agent_paper_neural.yaml` | best `deepar_hybrid`: −0.91 / 3.58 / 7.40 (1980/1995/2011); mean 3.36 all, 5.08 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Best mean of the neural track but wins years 4–7 at 1 of 3 origins; seed-7 replica 3.03 / 4.63. Not adopted; revisit with more seeds |
