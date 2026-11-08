# 0006: Keep the ADR 0004 folds for selection, and add a dense rolling-origin check

- **Date:** 2026-11-07
- **Status:** proposed
- **Deciders:** TBD (the team; a person decides. This ADR changes nothing by itself)

## Context

ADR 0004 scores every method on three equal-weight origins (1980, 1995, 2011) with a 7-year
horizon. The live leaderboard snapshot ([leaderboard_live_2026-11-07.md](../trials/leaderboard_live_2026-11-07.md))
raised the question of whether three origins are enough, and whether recent origins, which
look more like the warming regime of the 2022–2025 Final Score, should count more. That page
was used only to ask the question. No leaderboard number went into this study.

The literature on time-series evaluation (P10 Bergmeir & Benítez 2012, P12 Hyndman &
Athanasopoulos on the rolling forecasting origin, P19 Cerqueira et al. 2020) recommends many
time-ordered origins, and P19 found that time-ordered out-of-sample estimates worked best on
non-stationary real series.

We re-scored eight methods (`current_best`, `ten_year_mean`, `thirty_year_mean`,
`linear_trend`, `hybrid_ridge_all_cdd`, `hybrid_a`, `gev_stationary`, `arima_temp_cdd`) on
12 rolling origins: 1980 to 2010 every 3 years, plus 2011. The set includes the three ADR 0004
origins. Recency weights (linear; exponential with a 10-year half-life) and a 2,000-resample
origin bootstrap were fixed in the config before the first run. Full results:
[fold_study.md](../trials/fold_study.md).

Findings that matter for the decision (raw score, years 4–7 unless stated):

1. **Rankings agree where it matters.** Kendall tau-b between the 3-origin and 12-origin
   rankings of the eight methods is 0.93 in years 4–7 and over all years, which is one swapped pair out of 28. It is also 0.93
   against the 9 dense origins that are not ADR origins. In years 4–7 the swapped pair is
   `current_best` / `gev_stationary`, 0.01 apart on the ADR origins. Years 1–3 agree poorly
   (tau 0.57).
2. **The pick does not change.** `hybrid_ridge_all_cdd` is first in years 4–7 under every
   design tried: 3 origins, 12 origins, the 9 non-ADR origins only, linear and exponential
   recency weights, early origins only and late origins only. It stays first when any one
   origin is dropped (smallest margin 0.32). It is first in 99.8 % of origin-bootstrap resamples
   (99.2 % with exponential weights) and beats `current_best` at 10 of 12 origins. Its edge
   comes from CDD skill and is about the same at early and late origins.
3. **Recency weighting changes the runner-up and years 1–3, not the pick.** With recency
   weights, `current_best` moves ahead of `hybrid_a` over all years and in years 1–3.
   `hybrid_a`'s gain over `current_best` is larger at early origins. In years 1–3 the pick
   moves from `hybrid_a` to `current_best`.
4. **The three ADR origins overstate the level.** `current_best` averages 4.68 in years 4–7 on
   the ADR origins but 3.21 on the 12. 1995 and 2011 are two of the three best origins for
   that window. Differences between methods are similar; absolute scores are not.
5. **Years 1–3 are unstable under any design.** The top pick flips between `hybrid_a` and
   `current_best` depending on the origins and weights. Margins are under 0.4 points.

## Decision

Proposed:

1. **Keep** ADR 0004's three origins and equal weights as the selection folds and as
   `DEFAULT_CUTOFFS`. The denser set ranks methods the same way where it matters, so
   changing the folds three days before the deadline would add churn without changing the pick.
2. **Add** the 12-origin rolling check (`scripts/fold_study_p10_p12_p19.py`) as a required
   second opinion before any new submission candidate is adopted: the candidate must also beat
   the current submission on the dense set in years 4–7 and win at most of its origins.
3. **Do not** adopt recency weights for selection. They did not change the pick here, and the
   choice of half-life would be one more tuning knob.
4. When quoting a backtest level (not a difference between methods), quote the 12-origin
   mean as well, since the 3-origin mean runs high.

## Consequences

- Selection stays reproducible with the existing `climate-trial` command. Nothing in
  `proto_star.backtest` or `proto_star.trial` changes.
- A dense check costs about 2 minutes per light method and about 18 minutes for ARIMA (3 workers) on this
  laptop. Neural methods (DeepAR, N-BEATS) were not re-scored and would be much slower.
- The dense origins overlap: with 3-year steps and a 7-year horizon, each test year is scored
  from 2 or 3 origins, so the 12 origins are not 12 independent samples. The bootstrap and
  leave-one-out numbers are therefore optimistic about stability.
- Revisit if a future candidate wins on the 3 ADR origins but loses on the dense set, or if
  the team wants to switch to non-overlapping blocks (P10) at the cost of fewer origins.
