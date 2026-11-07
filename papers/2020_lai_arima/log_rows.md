# Rows for the orchestrator to merge

This branch only adds files, so these rows were not written into the shared tables.

## (a) Row for `docs/experiments.md` (top of the main table, newest first)

| 2026-11-06 | agent | `configs/agent_paper_p13_arima.yaml` | `e507f5e` + uncommitted new files | metric-specific | — | — | Paper P13 (Lai & Dzombak 2020). ARIMA per city series: KPSS d, stepwise AICc order, drift if Mann-Kendall p < 0.2, Box-Cox if residuals are non-normal. ADR 0004 folds. Mean raw score, all years / years 1–3 / years 4–7: `arima_paper` 0.26 / -0.96 / 1.06, `arima_temp_cdd` (ARIMA for temperature and CDD, `current_best` otherwise) 2.21 / 1.11 / 2.98, `arima_window50` -2.25 / -2.60 / -2.32, `current_best` 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / -0.62 / 2.78. The only ARIMA gain is CDD skill in years 4–7 (7.16 % against 6.84 %), at 1 of 3 origins. Fallback to the 30-year mean for 8 / 8 / 1 of 840 series. Not adopted; `submit: current_best`. Write-up: `docs/trials/paper_p13_arima.md`, card: `papers/2020_lai_arima/README.md` |

## (b) Row for the `papers/README.md` index

| `2020_lai_arima` | Lai & Dzombak, ARIMA near-term regional temperature and precipitation forecasts (WAF) | 2020 | Statistical: per-series ARIMA (KPSS + stepwise AICc, Mann-Kendall drift, Box-Cox) | adapted | `configs/agent_paper_p13_arima.yaml` | -2.59 / 0.37 / 3.01 (1980/1995/2011) | worse: `ten_year_mean` -2.53 / 1.39 / 5.16 | Lost to `current_best` at every origin and window. Years 4–7 mean 1.06 against 4.68. CDD skill slightly better in years 4–7 at 1 of 3 origins. Not submitted |
