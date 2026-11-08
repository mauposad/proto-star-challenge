# 0007: Submit the pooled warming trend (`trend_level10_15_sensitivity`)

- **Date:** 2026-11-08
- **Status:** accepted (2026-11-08)
- **Deciders:** mauposad (human owner). Method and package by corbe19 (Luke Corbett)

Numbered 0007 because 0005 and 0006 exist on `agent/integrate-papers`, not yet on `main`.

## Context

Two candidates were packaged on 2026-11-07, both built on the same master data (content hash
`99128065…`) and the same scorer:

- `hybrid_ridge_all_cdd` (ADR 0005, `agent/integrate-papers`): a ridge model pooled across all
  210 cities for CDD, `current_best` for the other metrics.
  HF `MekkoMau/protostar-climate-MKDir@02992aa`.
- `trend_level10_15_sensitivity` (`configs/lc_pooled_trend.yaml`, merged in PR #11): each
  city's mean of its last-10 and last-15-year levels plus a non-negative 40-year warming trend
  pooled across cities, for temperature and CDD. The CDD trend is the pooled temperature trend
  times each city's CDD per degree. 30-year mean for precipitation and hottest day.
  HF `corbe19/protostar-climate-MKDir-pooled-trend@af04833`.

Mean raw score on the ADR 0004 folds (cut-offs 1980, 1995, 2011):

| Method | All | Years 1–3 | Years 4–7 |
|---|---|---|---|
| `trend_level10_15_sensitivity` | **4.14** | 0.33 | **6.92** |
| `hybrid_ridge_all_cdd` | 3.60 | **0.94** | 5.54 |
| `current_best` | 2.92 | 0.63 | 4.68 |

Years 4–7 matches the Final Score (2022–2025), so the pooled trend leads on the window that
counts. The trial note says it was chosen from validation results only
([pooled_trend.md](../trials/pooled_trend.md)).

A diagnostic run on 42 cut-offs (1970–2011, see `docs/experiments.md`, 2026-11-08) gives a
smaller lead (years 4–7: 3.28 vs 2.81). The trend wins 19 of 42 cut-offs: it wins only 4 of 20
before 1990 and 10 of 12 from 2000. It is better on temperature, and the ridge model is better on CDD.
This run was not used to choose. ADR 0004 folds stay the selection rule.

## Decision

The pooled-trend package is the team's submission and the new bar. New methods are compared
against `trend_level10_15_sensitivity` on the ADR 0004 folds, as well as against
`current_best` and `thirty_year_mean`. It replaces `hybrid_ridge_all_cdd` (ADR 0005) as the
bar.

Its live score is 13.6 (2019–2021, up from 11.0 for `current_best`; see
[leaderboard_live_2026-11-08.md](../trials/leaderboard_live_2026-11-08.md)). That number is
recorded, not used to choose. The honor code forbids selecting on it.

## Consequences

- The `current_best` forecaster in code is unchanged. It is still the 10-year / 30-year mean
  ensemble and remains a reference in trial configs. "Bar" here means the submitted method.
- The trend bets that warming continues. It gains most at recent cut-offs and loses at the
  1970s–1980s ones, so a pause in warming during 2022–2025 would hurt it.
- Neither package has skill on precipitation or hottest day. Half the score is untouched.
- Revisit if a trial on the ADR 0004 folds beats it in years 4–7 under the trial's pre-set
  rule. An obvious first candidate is the trend for temperature with the pooled ridge model for
  CDD: summing the per-metric skills gives 7.00 in years 4–7, but it has not been run as a
  forecaster yet.
