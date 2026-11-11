# Evidence: scientific value and technical creativity

This section maps each claim we make under two judging criteria to a file and a command that
checks it. Every number is copied from a tracked trial note or log row. All of it comes from
backtests on data through 2018-12-31; nothing here was chosen with 2019–2025 data or with a
leaderboard score.

Links point to two branches of the team repository:
[`agent/ml-challengers`][ml] (the final-round code plus the work below) and
[`agent/hypothesis-trials`][ht] at commit `4ac87a8` (the hypothesis rounds).

## Scientific, research, or societal value

*Rubric: "Useful knowledge, new research capability, improved decision-making, or meaningful
public benefit."* Our contribution is knowledge about what does and does not transfer when
forecasting city climate seven years ahead, with the negative results kept.

| # | Finding | Result | Where to check |
| :- | :------ | :----- | :------------- |
| V1 | A city's recent drift carries signal only when measured against its **neighbours**, not against the national mean | Same model, two references, both stacked on the team's best forecaster (`r4_winners`). Neighbours: +0.24 [+0.06, +0.46] raw on the official folds, and it wins at 20 of 27 rolling origins. National: −0.28 [−0.57, −0.03], wins at 12 of 27 | [`city_drift.md`][cd], rows `cd1_temp_cdd` and `cd3_national` |
| V2 | That gain **fades with time**, so a long backtest overstates what it is worth today | Gain over `r4_winners` by origin block: +0.46 (1985–1993), +0.26 (1994–2002), +0.02 (2003–2011), −0.02 (2005–2011) | [`city_drift.md`][cd], "Where the gain is, by era" |
| V3 | Hottest-day persistence **changes sign with the era**: it works when the 1930s heat sits in the reference window and fails otherwise | A damped city anomaly gains +1.73 [+0.93, +2.51] pp on origins 1955–1969 and loses −3.04 [−5.74, +0.02] pp at the 1941 origin | [`hypotheses.md`][hyp], "Final (Round 3)", H27 |
| V4 | **More flexible models do worse.** Skill rises as the model is allowed to learn less | Against `r4_winners` on the official folds: gradient boosting on its errors −5.47 [−6.90, −3.94]; city-relative −2.21 [−3.10, −1.13]; heavily regularized −0.32 [−0.67, +0.08]; zero-shot Chronos-T5 −7.79 [−10.62, −4.87] | [`ml_challengers.md`][mlc] |
| V5 | A **register of 33 hypotheses**, each tested one with an endpoint declared in its config and a 95% interval. One met the adoption rule (E2: +0.22 [+0.07, +0.35] over the pooled trend; on the 2011 fold alone +0.07 [−0.08, +0.20]) | Refuted, inconclusive and untested hypotheses are all listed with their numbers | [`hypotheses.md`][hyp] (three "Final" tables), [`experiments.md`][exp] |
| V6 | Most of the remaining error is in the **national level**, not in city detail | A perfect common shift per fold would lift the pooled trend's temperature skill from 8.74 to 15.09. Our forecasters assume +0.73 to +0.83 °F and +114 to +121 CDD for 2019–2021 against the 1989–2018 average | [`candidate_error_analysis.md`][cea]; `scripts/national_path.py` |

**Use for decisions.** V1 and V2 tell a city or utility how far to trust a station's recent
departure from its region: it is information about the station, it is small, and its value has
shrunk since about 2003. V3 warns against extrapolating one hot decade into a hottest-day
forecast. V4 and V5 save the next team the same experiments.

**About V6.** A third-party public report lists the national paths of other entries; the top
eight assume more warming than ours (+0.90 to +1.27 °F and +139 to +184 CDD for 2019–2021). We
report this as a difference between forecasts. We did not change any forecast because of it:
doing so would use the leaderboard, which the data rule forbids.

## Technical creativity

*Rubric: "Novel methods, AI approaches, technical solutions, or combinations of resources that
advance the goals of the challenge."* Our method is a way to add a learned correction to any
forecaster without leaking the future, together with a test protocol that kept us from
adopting gains that were not real.

| # | Method | What is new in it | Proof |
| :- | :----- | :---------------- | :---- |
| C1 | **In-fold stacking on pseudo-origins.** Any registered forecaster is refit at 30 earlier origins inside each fold, and a correction is trained on its own past errors there | The correction never sees a target after the fold's cut-off, and it wraps any base, including other teams' re-implemented methods | [`city_drift.py`][cdpy], [`residual_boost.py`][rbpy]; tests: zero strength reproduces the base exactly, and features ignore years after the origin |
| C2 | **City-relative by construction.** Targets and corrections are centred across cities for each year | The correction cannot move the national level or trend, which is the part that did not transfer in our earlier trials | [`test_city_drift.py`][cdtest]: the mean correction per year is zero and only the named metric changes |
| C3 | **A control arm inside the trial config.** The national-reference model (V1) is run next to the neighbour model; in round 1, neighbour anchoring was compared with 20 placebo neighbour sets | It separates "the method helps" from "the ingredient helps" | [`at_city_drift.yaml`][cdyaml]; [`hypotheses.md`][hyp], H1 |
| C4 | **Paired year-block bootstrap.** Two forecasters are compared on the same rows, resampling forecast years within each fold | Errors are shared across cities within a year, so city-level resampling gives intervals that are too narrow | [`paired.py`][paired]; test: the paired difference equals the official score difference exactly |
| C5 | **Out-of-era replication origins** (1934, 1941, 1948) and an adoption rule that also requires the fitted coefficient to keep its sign at every cut-off | An independent check on eras never used for development; it produced V3 | [`hypotheses.md`][hyp], "Final (Round 2)" and "Final (Round 3)" |
| C6 | **An audited AI research loop.** Two generator models propose hypotheses, independent critic agents review novelty and methodology, and a relator agent records every step in a ledger and logs where the record and the files disagree | 620 validated ledger events. The critics found two code defects before adoption; the fix turned +0.22 [+0.01, +0.45] into +0.17 [−0.01, +0.37], so the change was not adopted. No agent supplied a forecast value | [`ledger/`][ledger], [`hypotheses_review.md`][rev] |
| C7 | **Provenance check for a pretrained model.** Before testing Chronos, we chose the variant whose training corpus is published and checked its weather data against the 2018 cut-off | USHCN file checked ends 2014-12-31; WeatherBench is 1979–2018. The result is still labelled exploratory | [`ml_challengers.md`][mlc], "The 2018 data cut-off and the pretrained model" |

## Reproduce the headline results

```bash
uv sync --extra hf                      # the hf extra is needed only for the Chronos rows
uv run proto-star climate-trial configs/at_city_drift.yaml
uv run python scripts/robustness_origins.py configs/at_city_drift.yaml \
    --origins rolling27 --default r4_winners --out runs/robustness/city_drift
uv run python scripts/paired_bootstrap.py configs/at_city_drift.yaml --default r4_winners
uv run python scripts/national_path.py configs/at_city_drift.yaml
uv run pytest tests/test_city_drift.py tests/test_paired.py tests/test_ml_challengers.py -q
```

## Limits

- There is no untouched holdout. The 27 rolling origins overlap the official folds, and
  consecutive origins share target years.
- The city-drift correction was built and evaluated on the deadline day. Its expected gain on
  2019–2025 is about zero (V2).
- The hypothesis rounds ran on an earlier candidate (the pooled trend), not on `r4_winners`.
- The citation auditor was skipped in the hypothesis rounds, so the literature notes are
  unaudited and no novelty claim is made against the literature.

[ml]: https://github.com/mauposad/proto-star-challenge/tree/agent/ml-challengers
[ht]: https://github.com/mauposad/proto-star-challenge/tree/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7
[cd]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/docs/trials/city_drift.md
[mlc]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/docs/trials/ml_challengers.md
[cdpy]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/src/proto_star/forecasters/city_drift.py
[rbpy]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/src/proto_star/forecasters/residual_boost.py
[cdtest]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/tests/test_city_drift.py
[cdyaml]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/configs/at_city_drift.yaml
[paired]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/src/proto_star/paired.py
[hyp]: https://github.com/mauposad/proto-star-challenge/blob/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/hypotheses.md
[rev]: https://github.com/mauposad/proto-star-challenge/blob/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/hypotheses_review.md
[exp]: https://github.com/mauposad/proto-star-challenge/blob/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/docs/experiments.md
[cea]: https://github.com/mauposad/proto-star-challenge/blob/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/docs/trials/candidate_error_analysis.md
[ledger]: https://github.com/mauposad/proto-star-challenge/tree/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/ledger
