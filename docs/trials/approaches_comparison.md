# Comparison: the hypothesis trials against the team's approaches

Date 2026-11-10. Branch `agent/hypothesis-trials`, which starts from `main` at `aa8e869`.

This note compares the results of the hypothesis trials on this branch (`hypotheses.md`,
rounds 1–3) with the approaches the team recorded on `main` and on its other branches. It
selects nothing: no 2019–2025 data and no leaderboard score was used to choose anything here.

## How comparable the numbers are

Each number is copied from the trial note or experiment-log row named in its Source column.
They are comparable because every one of them uses:

*   the same folds: ADR 0004, cut-offs 1980, 1995 and 2011, with a 7-year horizon;
*   the same scorer: ADR 0003; the raw score is the official score without its floor;
*   the same input data: master content hash
    `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1`.

Two numbers confirm the match:

*   `trend_level10_15_sensitivity` scores 4.14 / 0.33 / 6.92 in Luke's log row on `main`, in
    `docs/trials/final_round.md` on `agent/final-round` and in `docs/trials/submit_e2.md` on
    this branch;
*   `docs/trials/final_round.md` also confirms the content hash.

Nothing in this note was rerun on another branch's code. The other branches' forecasters (for
example `lead_blend` and the CRM) are not on this branch.

**Notation.**

*   "Raw" means the raw score for all years / years 1–3 / years 4–7.
*   Skills are percent per metric.
*   "pp" means percentage points of one metric's skill.

## 1. The team's approaches (reported on their branches)

| Approach | Raw | Temperature / precipitation / hottest / CDD skill | Source |
| :------- | :-- | :------------------------------------------------ | :----- |
| `thirty_year_mean` (the reference) | 0.00 / 0.00 / 0.00 | 0 / 0 / 0 / 0 | the scorer's reference |
| `ten_year_mean` | 1.34 / −0.62 / 2.78 | — | `main`, `configs/mp_baselines_round1.yaml` |
| `current_best` (10-year mean for temperature and CDD) | 2.92 / 0.63 / 4.68 | 5.76 / 0 / 0 / 5.91 | `main`; live leaderboard 11.0 |
| ARIMA per city (P13) | 0.26 / −0.96 / 1.06 | — | `agent/paper-p13-arima` (`51cb1bf`) |
| OCN, alternative normals (P02–P04) | 2.35 / 0.49 / 3.68 | — | `agent/paper-p02-p04-p23-normals` (`207707d`) |
| N-BEATS generic (P05) | 2.32 / 0.52 / 3.39 | — | `agent/paper-p05-p08-neural` (`3cdd75a`) |
| DeepAR global (P08) | 2.39 / 0.25 / 3.87 | — | `agent/paper-p05-p08-neural` (`3cdd75a`) |
| Pooled ridge for CDD, `hybrid_ridge_all_cdd` (P09/P14) | 3.60 / 0.94 / 5.54 | — | `agent/paper-p09-p14-pooled` (`9cd63f6`) |
| Pooled trend, `trend_level10_15_sensitivity` | 4.14 / 0.33 / 6.92 | 8.74 / 0 / 0 / 7.80 | `main`, `configs/lc_pooled_trend.yaml`; live leaderboard 13.6 |
| CRM, `crm_s6_eb_urban` | 4.39 / 0.51 / 7.23 | 9.11 / 0.06 / 0.06 / 8.33 | `agent/crm` (`07af4ea`), `docs/trials/final_round.md` |
| Trend + ridge CDD mean, `h2_mean_cdd` | 4.41 / 0.70 / 7.12 | — | `lc/hybrid` (`e942ef0`), `configs/lc_hybrid.yaml` |
| Lead blend of trend and ridge, `lead_split3` | 4.69 / 1.32 / 7.12 | 9.86 / 0 / 0 / 8.91 | `agent/final-round` (`07af4ea`); ported from the Hub package `corbe19/protostar-climate-MKDir-lead` |
| `lead_split3` plus neighbour components (P5, H4), `r4_winners` | 4.85 / 1.46 / 7.30 | 9.86 / 0.21 / 0.43 / 8.91 | `agent/final-round` (`07af4ea`), `docs/trials/final_round.md` §3 |

`r4_winners` is the final round's submission candidate. Under that round's own rule it beats
`lead_split3` on the official folds (4.85 against 4.69), over 27 rolling origins (4.99 against
4.72) and at 27 of 27 origins. `final_round.md` reports point estimates and win rates. It gives
no bootstrap intervals.

## 2. This branch's approaches

All rows are against the previous submission candidate `trend_level10_15_sensitivity` unless
another reference is named. Intervals are 95% paired year-block bootstrap intervals
(`scripts/paired_bootstrap.py`). The full record is in `docs/experiments.md` (rows dated
2026-11-09 and 2026-11-10) and `hypotheses.md`.

| Approach | Result on the official folds | Status |
| :------- | :--------------------------- | :----- |
| **E2**: damp the city part of the recent temperature and CDD anomaly, λ fitted in-fold | Absolute raw **4.35 / 0.34 / 7.29**; skill 9.12 / 0 / 0 / 8.29. Against the candidate: +0.22 [+0.07, +0.35] raw; 2011 fold alone +0.07 [−0.08, +0.20]. | adopted on this branch; package built locally, not uploaded |
| U1: pooled direct multi-horizon model | raw years 4–7 −2.34 [−3.46, −1.14] (linear) | dropped |
| U2: blend of the pooled trend and `current_best` | raw −0.47 [−1.04, +0.14] | dropped |
| U3: station-segment-aware slope | raw +0.02 [−0.15, +0.20] | dropped |
| H1: neighbour-anchored levels for precipitation and the hottest day | raw +0.01 [−0.16, +0.19]; over 7 cut-offs −0.03 | dropped |
| H2: June–August slope for the hottest day | hottest-day skill, years 4–7: −1.23 [−2.20, −0.08] pp | dropped |
| H4: remove the shared national residual from the level | temperature skill, years 4–7: +1.62 [−1.71, +4.82] pp; early origins −5.47 pp | kept, inconclusive |
| H16: lead-decaying persistence of the last error | raw years 1–3: +0.77 [−0.30, +1.63] | kept, inconclusive |
| E1: damped hottest-day city anomaly | hottest-day skill +0.10 [−0.77, +0.97] pp | dropped |
| H23 = H36: Tmin − Tmax contrast for CDD, on E2 | CDD skill against E2 +0.17 [−0.01, +0.37] pp; replication −0.05 | kept, not adopted |
| H26: lead-varying λ on E2 | raw against E2 +0.03 [−0.00, +0.06] | kept, inconclusive |

## 3. What the comparison shows

1. **E2 does not beat the team's current candidates.**
   *   On all years, E2 scores 4.35 raw: about level with `h2_mean_cdd` (4.41) and the CRM
       (4.39), and below `lead_split3` (4.69) and `r4_winners` (4.85).
   *   Under ADR 0009 (proposed) the final score uses all seven years, so all years is the
       column that matters.
   *   E2 should not replace `r4_winners` as the submission.
2. **E2 differs from the team's methods only in years 1–3.**
   *   On years 4–7, E2 scores 7.29 against 7.30 for `r4_winners` and 7.12 for `lead_split3`.
   *   On years 1–3 it scores 0.34 against 1.46. `lead_split3`'s pooled ridge carries the
       early-lead skill, and E2 has no early-lead component.
   *   On the two metrics E2 changes, `lead_split3` is ahead: temperature 9.86 against 9.12,
       and CDD 8.91 against 8.29.
3. **Untested: E2's mechanism on top of `lead_split3`.**
   *   E2 damps the city part of the recent anomaly. `lead_split3` blends the trend with a
       ridge on normalized lags.
   *   They act on the same part of the error, so any gain from stacking them is likely
       smaller than E2's gain over the bare trend. On the 2011 fold, E2's gain was only +0.07.
   *   Testing it needs `lead_blend` on this branch (see section 4).
4. **The team's neighbour components succeeded where this branch's did not.**
   *   `r4_winners` takes its precipitation and hottest-day gains from component means:
       *   precipitation (+0.21 pp): a neighbour nudge averaged with a two-half level with
           Fay–Herriot shrinkage;
       *   hottest day (+0.43 pp): a neighbour nudge averaged with a second-highest anchor.
           This component wins at 27 of 27 rolling origins.
   *   This branch's neighbour anchoring (H1, +0.01 raw) and damped hottest-day anomaly (E1,
       +0.10 pp) did not reach significance. The specifications differ:
       *   `r4_winners`'s hottest-day nudge: a fixed 0.3 weight on the mean departure over
           the last 10 years from the 31 nearest cities;
       *   H1: anchors the level itself on neighbours;
       *   E1: fits a city damping coefficient.
5. **This branch's checks could stress-test `r4_winners`.**
   *   H27 found that hottest-day city persistence changes sign with where the 1930s heat
       sits in the reference window: E1 at the 1941 origin is −3.04 [−5.74, +0.02] pp.
   *   The final round's 27 rolling origins cover cut-offs 1985–2011 only.
   *   Two checks would show whether the hottest-day and precipitation nudges hold up:
       *   the replication origins 1934/1941/1948;
       *   the paired year-block bootstrap, for intervals on `r4_winners` against
           `lead_split3`.
   *   Neither has been run.
6. **The data are the same for `r4_winners`.**
   *   Its components (`lead_blend`, `final_precip`, `final_hottest`) read only the
       organizer's annual and daily tables, as this branch does.
   *   The CRM branch adds external data capped at 2018 for its regional model: GHCN
       neighbours, HadCRUT and NLCD (`docs/trials/external_data_notes.md` on that branch).

## 4. Merging this branch

This branch starts from `main`, not from `agent/final-round`, and the two would conflict:

*   **`proto_star.forecasters`:** this branch adds the module `src/proto_star/forecasters.py`,
    a custom-kind registry with `CustomSpec` and `register_kind`. `agent/final-round` has the
    package `src/proto_star/forecasters/`, with the plug-in registry of ADR 0008. Python cannot
    import both under one name.
*   **Shared modules:** both branches change `src/proto_star/trial.py`,
    `src/proto_star/backtest.py` and `src/proto_star/trend.py`.

The pieces worth porting are self-contained:

*   the E2 kind (`src/proto_star/anomaly.py`, kind `anomaly_correction`);
*   `fold_rows` and `paired_year_bootstrap` in `src/proto_star/backtest.py`;
*   `scripts/paired_bootstrap.py`, with its replication origin set.

Porting them to the ADR 0008 plug-in registry is a separate change.
