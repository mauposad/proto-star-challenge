# 0005: Submit the pooled ridge model for CDD (`hybrid_ridge_all_cdd`)

- **Date:** 2026-11-07
- **Status:** accepted (2026-11-07)
- **Deciders:** mauposad (human owner). Other team members: TBD

## Context

Our only scored submission is `current_best`: the 10-year mean for temperature and CDD, and the
30-year mean for precipitation and hottest day. Papers round 1
([summary](../trials/papers_round1_summary.md)) tested four literature tracks on the ADR 0004
folds (cut-offs 1980, 1995, 2011). Only one method beat `current_best` at every origin in every
window: `hybrid_ridge_all_cdd`. It is a ridge model pooled over all 210 cities (papers P14/P09)
that forecasts CDD only and keeps `current_best` for the other three metrics.

Mean raw score (all years / years 1–3 / years 4–7):

| Method | All | Years 1–3 | Years 4–7 | Origins beating `current_best` |
|---|---|---|---|---|
| `hybrid_ridge_all_cdd` | 3.60 | 0.94 | 5.54 | 3/3, 2/3, 3/3 |
| `current_best` | 2.92 | 0.63 | 4.68 | – |

CDD skill in years 4–7 rises from 6.84 % to 10.27 %. Three other unrelated methods (DeepAR,
EWMA, ARIMA) also beat the 10-year mean on CDD, which makes the direction credible.

The choice was made on the backtest alone, before the live leaderboard was read. The
[leaderboard snapshot](../trials/leaderboard_live_2026-11-07.md) was not used to make it.

## Decision

Submit the package built from `configs/agent_paper_p09_p14_pooled.yaml` (`submit:
hybrid_ridge_all_cdd`). Only the CDD column differs from `current_best`.

A person runs the `Publish submission` workflow with `upload` ticked and pastes the new dataset
commit into the challenge Space. Agents do not upload or submit.

## Consequences

- The new submission replaces `current_best` on both the live (2019–2021) and final
  (2022–2025) boards. Only the latest submission counts.
- Selection optimism: it was the best of 15 variants on 3 origins, so the true gain is probably
  smaller than the backtest shows.
- The live board will move only through CDD. A change there says little about years 4–7 and
  must not be used to switch back or tune (honor code).
- Revisit if the fixed equal-weight CDD combination (P16/P17) beats it on the same folds, or if
  the team changes the fold design in a new ADR.
