# Rows for the shared logs (the orchestrator merges these)

## docs/experiments.md (newest first)

| Date | Who | Config | Commit | Val MAE | Val RMSE | LB score | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-07 | agent | `configs/agent_fold_study_p10_p12_p19.yaml` | `c5d6eb5` + branch `agent/eval-p10-p12-p19-folds` | metric-specific | — | — | Fold design study (P10, P12, P19), evaluation only; ADR 0004 folds unchanged. 8 methods re-scored on 12 rolling origins (1980–2010 every 3 years, plus 2011). Years 4–7 mean raw score, ADR 3 origins / 12 origins / 12 with exponential recency weights: `hybrid_ridge_all_cdd` 5.54 / 3.97 / 5.12, `hybrid_a` 4.90 / 3.53 / 4.59, `current_best` 4.68 / 3.21 / 4.39, `gev_stationary` 4.69 / 3.01 / 4.28, `arima_temp_cdd` 2.98 / 2.53 / 3.35, `ten_year_mean` 2.78 / 2.27 / 3.77, `linear_trend` −15.15 / −8.66 / −4.15. Kendall tau-b, 3 vs 12 origins: 0.93 (years 4–7), 0.93 (all), 0.57 (years 1–3). `hybrid_ridge_all_cdd` is first in years 4–7 under every design, at 12/12 leave-one-out drops and in 99.8 % of origin bootstraps; it beats `current_best` at 10/12 origins. Recency weighting does not change the pick (it flips only years 1–3, `hybrid_a` → `current_best`). The 3 ADR origins run about 1.5 points high in years 4–7. `linear_trend` gains +4.5 points/decade of origin year but stays last. DeepAR/N-BEATS not re-scored (machine limits). Write-up: `docs/trials/fold_study.md`; proposed ADR 0006 |

## papers/README.md index row

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| `2020_cerqueira_rolling_origin_evaluation` | Cerqueira et al. performance estimation (P19), Hyndman & Athanasopoulos rolling origin (P12), Bergmeir & Benítez blocked CV (P10) | 2012–2020 | Evaluation design: rolling forecasting origins, no forecaster | adapted | `configs/agent_fold_study_p10_p12_p19.yaml` | n/a (study). Years 4–7, 12 origins: `hybrid_ridge_all_cdd` 3.97, `current_best` 3.21 | `ten_year_mean` 2.27 on 12 origins | 3 ADR origins and 12 rolling origins agree in years 4–7 (tau 0.93); recency weights do not change the pick; ADR origins overstate levels. Proposed ADR 0006: keep ADR 0004 folds and add the dense check |
