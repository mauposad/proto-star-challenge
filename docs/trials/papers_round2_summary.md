# Papers round 2: cross-track summary

Five tracks ran on 2026-11-07, each on its own branch from `agent/integrate-papers` (`b1684e0`). A first
attempt that afternoon crashed the host machine (5 agents, each with its own environment) and left no
commits. The rerun used at most 3 agents at a time, a shared environment and 3 cores per agent.
Every method was scored on the same ADR 0004 folds (cut-offs 1980, 1995, 2011, 7-year horizon), the same
master table (content hash `99128065…bb04d1`) and the same official raw score. Nothing was selected on
leaderboard scores. This page decides nothing; adopting a method needs an ADR and a person.

**Bottom line: no round-2 method beats `hybrid_ridge_all_cdd` (ADR 0005).** Two tie it within 0.01 points.
The fold study shows that its lead over `current_best` holds on 12 rolling origins.

## References

| Method | Role | All | Years 1–3 | Years 4–7 |
|---|---|---|---|---|
| `hybrid_ridge_all_cdd` | submitted under ADR 0005 (live score pending; it will be logged here, never used to select) | 3.60 | 0.94 | 5.54 |
| `current_best` | previous scored submission | 2.92 | 0.63 | 4.68 |

## Best variant per track

Mean raw score over the three ADR 0004 origins. "Wins 4–7" counts origins won in forecast years 4–7, the
Final Score window.

| Track | Papers | Best variant | All | 1–3 | 4–7 | Wins 4–7 vs `current_best` | Wins 4–7 vs `hybrid_ridge_all_cdd` | Verdict |
|---|---|---|---|---|---|---|---|---|
| A combinations | P16, P17 (P18) | `combo_mean_cdd_only` | 3.49 | 0.99 | 5.37 | 3 / 3 | 1 / 3 | loses to the bar |
| B regional | P22, P24 | `p24_ridge_population_interact` | 3.61 | 0.95 | 5.55 | 3 / 3 | 2 / 3 | tie (+0.01) |
| C station | P15 | `adj_temp_k5_w5_ridge_cdd` | 3.61 | 0.97 | 5.53 | 3 / 3 | 2 / 3 | tie (+0.01 all, −0.01 4–7) |
| D CDD + forcing | step 9, P06, P21 | `hybrid_ridge_shift30_avg` | 3.37 | 0.76 | 5.36 | 3 / 3 | 2 / 3 | loses to the bar on the mean |
| E fold study | P10, P12, P19 | evaluation only | – | – | – | – | – | supports the ADR 0005 pick |

Per-track write-ups (each has a `_why.md` with per-metric, per-origin and per-city breakdowns):
[combos_p16_p17](combos_p16_p17.md), [regional_p22_p24](regional_p22_p24.md),
[station_p15](station_p15.md), [paper_cdd_forcing_p06_p21](paper_cdd_forcing_p06_p21.md),
[fold_study](fold_study.md).

## Why each track came out as it did

- **A, combinations.** The four CDD members have highly correlated errors (0.94–0.99), and the pooled
  ridge is clearly the best member, so an equal mean pulls toward the weaker ones. The spread between
  members is only 2.6 % of member MSE. Estimated (inverse-MSE) weights ≈ equal weights, as in the P17
  "combination puzzle". Dropping DeepAR changes nothing (5.36 vs 5.37). Combining temperature
  forecasts costs skill in years 4–7 (10.06 % vs 11.90 %).
- **B, regional trends and groups.** Pooling groups (P24) add nothing beyond a ridge that already pools
  about 12k rows per lead. The damped regional trend (P22) gains temperature in years 4–7 (13.13 % vs
  11.90 %) at 1995 and 2011 but loses at 1980, when 1951–1980 regional trends were negative in 4 of 6
  regions.
- **C, station segments.** Only 39 of 630 city-origins have a station switch inside the 10-year window,
  and a step can be estimated at 19. The gain is mostly one city (McCook, NE) and does not grow with the
  step size.
- **D, CDD from daily data and forcing.** `current_best` under-forecasts CDD (76 °F-days in years 4–7),
  but convexity explains almost none of it. The temperature shifts are 0.2–0.7 °F, so recomputing CDD
  adds only +0.02 to +0.08 skill points. The pooled ridge learns the under-forecast directly. Forced
  trends (CO2, regional) win big at 2011 and lose big at 1980.
- **E, fold design.** 3 ADR origins vs 12 rolling origins: Kendall tau 0.93 in years 4–7.
  `hybrid_ridge_all_cdd` is first at 12/12 leave-one-out drops and in 99.8 % of bootstraps, and it beats
  `current_best` at 10/12 origins. Its CDD edge is the same at early and late origins, so recency weights
  don't change the pick. The ADR origins overstate levels by about 1.5 points (1995 and 2011 are easy
  origins), not the gaps between methods.

## What the tracks agree on

1. **The pooled ridge's CDD gain is real and stable.** It survives 12 origins (E). No combination,
   regrouping or physical recomputation adds to it (A, B, D).
2. **Trend-following is unstable across regimes.** P22 regional trends, P21 forced trends and
   `linear_trend` all fail at 1980/1983, when the trailing 30-year trend was negative, and gain at
   recent origins (B, D, E). None of them beats the ridge even at recent origins.
3. **Temperature is still the unsolved part.** The 10-year mean under-forecasts temperature in years
   4–7 at every origin (B). Only the damped regional trend improved it, and not reliably.
4. **Precipitation and hottest day: still nothing beats the 30-year mean** (C applied to them loses).

## Caveats

- Three origins per trial; differences under about 1 point are not distinguishable from noise. E's
  12-origin check overlaps test years, so it overstates stability.
- Selection optimism: each best variant is the best of 8–12, and the bar itself was the best of 15.
- Several papers were read from abstracts only (P10, P16, P17 original, P18, P20, P21, P24 full text).
  Each card lists its deviations and marks unknowns TBD.
- B's elevation/population/land-cover groups postdate the 1980 and 1995 cut-offs (mild look-ahead in
  static labels only). B's and D's external data are not downloaded on CI, so those variants would not
  rebuild there. None is submitted.
- Track A's recorded trial ran ARIMA with about 9 cores, over the per-agent budget; later runs were capped.

## Submittable branches

Every branch is pushed and self-contained (`gh workflow run publish.yml --ref <branch> -f config=<cfg>`).
All four packages submit `hybrid_ridge_all_cdd`. The C, B and D `submission.csv` files are byte-identical.

| Branch | Head | Config | `submit` | Dry run | Local package (git-ignored) |
|---|---|---|---|---|---|
| `agent/paper-p16-p17-combos` | `e746d13` | `configs/agent_paper_combos_p16_p17.yaml` | `hybrid_ridge_all_cdd` | [42437304105](https://github.com/mauposad/proto-star-challenge/actions/runs/42437304105) | `.claude/worktrees/combos/submissions/20261107-183531_combos_p16_p17` |
| `agent/paper-p22-p24-regional` | `3ee90fa` | `configs/agent_paper_regional_p22_p24.yaml` | `hybrid_ridge_all_cdd` | [42421025087](https://github.com/mauposad/proto-star-challenge/actions/runs/42421025087) | `submissions/20261107-180317_regional_p22_p24` |
| `agent/paper-p15-station` | `294a1e5` | `configs/agent_paper_station_p15.yaml` | `hybrid_ridge_all_cdd` | [42419919506](https://github.com/mauposad/proto-star-challenge/actions/runs/42419919506) | `submissions/20261107-180155_station_p15` |
| `agent/paper-p06-p21-cdd-forcing` | `9cab4ee` | `configs/agent_paper_cdd_forcing_p06_p21.yaml` | `hybrid_ridge_all_cdd` | [42421089511](https://github.com/mauposad/proto-star-challenge/actions/runs/42421089511) | `submissions/20261107-180407_paper_cdd_forcing_p06_p21` |
| `agent/eval-p10-p12-p19-folds` | `a0ac848` | `configs/agent_fold_study_p10_p12_p19.yaml` | – (no package) | – | – |

The round-1 local package paths in [papers_round1_summary.md](papers_round1_summary.md) pointed into
worktrees that no longer exist. Rebuild them with `uv run proto-star climate-package <config>`.

## Open questions for the team

1. **ADR 0006 (proposed):** keep the ADR 0004 folds, and add the 12-origin check as a required second
   opinion before adopting a new method. See [0006](../decisions/0006-fold-design-dense-origins.md).
2. **Temperature.** P22's damped regional trend for temperature plus the ridge for CDD was suggested
   after seeing results. It would need to be fixed in advance and tested on 12 origins, not only the
   three ADR origins.
3. **Log the ADR 0005 live score** when it arrives. Do not select on it.
