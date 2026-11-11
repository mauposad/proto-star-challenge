# Evidence for the judging criteria

This section maps each claim we make under five judging criteria to a file and a command that
checks it. Every number is copied from a tracked trial note or log row. All of it comes from
backtests on data through 2018-12-31; nothing here was chosen with 2019–2025 data or with a
leaderboard score.

Links point to the team repository: [`agent/ml-challengers`][ml] (the final-round code plus the
work below), [`agent/hypothesis-trials`][ht] at commit `4ac87a8` (the hypothesis rounds), and
the branches named in each row.

## Demonstrated reuse and extensibility

*Rubric: "Meaningful use or rigorous attempted reuse of ProtoStar artifacts; useful extension,
diagnosis, or recommendation for future researchers."*

| # | Claim | Result | Where to check |
| :- | :---- | :----- | :------------- |
| R1 | All four subsets of the challenge dataset are used, through one shared master table | `daily`, `annual_indices`, `city_info` and `coverage_and_stations` are joined, cleaned and flagged into one table with a content hash (`99128065…`) that every trial note records | [`docs/data.md`][data], "Annual master table" |
| R2 | **Attempted reuse of the source study's own method.** Lai & Dzombak's (2020) ARIMA procedure was re-implemented with the paper's rules and scored on our folds | Raw score 0.26 / −0.96 / 1.06 (all years / years 1–3 / years 4–7), against 4.14 for the pooled trend: the published method does not carry over to seven-year city forecasts | branch [`agent/paper-p13-arima`][p13], `docs/experiments.md` |
| R3 | Methods from about ten more papers were re-implemented on the same folds, wins and losses kept | OCN 2.35, N-BEATS 2.32, DeepAR 2.39, pooled ridge for CDD 3.60, pooled trend 4.14 (raw, all years) | branches `agent/paper-*`; [comparison note][cmp] |
| R4 | **Extension point:** a model kind is one file in a plug-in registry, and a kind can wrap any other kind | Two other teams' published methods (Tatakae, PstarAlu; CC BY 4.0) were re-implemented from their README text as components; tonight's `city_drift` and `residual_boost` stack on any registered forecaster | [`forecasters/__init__.py`][reg]; [`final_round.md`][fr], section 4 |
| R5 | **Diagnosis of the artifacts for the next user** | `Max Tmax` is integer-valued before 2018 and only 59% integer in 2018, a precision change in the last training year. The chronology of `Station Segment` numbering is unverified, so we use `Station Changes` per year. Folds that include 1980 select slow-warming models (V6) | [`experiments.md`][exp], "H31 gate" row; [`hypotheses.md`][hyp], "Final (Round 3)" |

## Interoperability and integration

*Rubric: "Successful combination or portability across repositories, institutions, agencies,
environments, or domains, or rigorous evidence showing why integration fails; value and limits
of common standards and machine-actionable formats."*

| # | Claim | Result | Where to check |
| :- | :---- | :----- | :------------- |
| I1 | Sources from several institutions are integrated with one documented procedure | CMU challenge tables, NOAA GHCN-Daily (station inventory and neighbour stations), Met Office/CRU HadCRUT4, NOAA ERSSTv5, U.S. Census population, NLCD land cover, elevation and climate indices: each with source, licence, download command and checksum. The submitted forecaster reads only the challenge tables; the others feed the regional model and the analysis | [`docs/data.md`][data], "External data" and "Input artifact checksums"; `tests/test_external_*.py` |
| I2 | The 2018 cut-off is enforced where sources meet | Every weather input passes `assert_weather_cutoff`. HadCRUT4 has no server-side date filter, so its download caps the text before anything is written | [`docs/data.md`][data], "Leakage policy" and "HadCRUT4" |
| I3 | Machine-actionable package | The card's YAML `configs` block makes `submission.csv` load with `datasets.load_dataset`; `data/README.md` describes every file; `code/reproduce.py` rebuilds the forecasts and compares them with the file | this dataset card; `code/` and `data/` |
| I4 | **Where integration failed, with the evidence** | (a) `chronos-forecasting` 1.5 would have downgraded `transformers`, `huggingface-hub` and `datasets` in the shared lock; 2.x adds three packages and changes none. (b) Chronos-Bolt could not be used at all: its training data is unpublished, so the data rule cannot be checked. (c) Chronos-T5 on a laptop CPU took 1.0 s for 10 series and 124 s for 100 in one batch, so the kind batches by 10. (d) Two branches each added a registry named `proto_star.forecasters`, one a module and one a package, and cannot be merged without a port | [`ml_challengers.md`][mlc], "Dependency" and "The 2018 data cut-off"; [comparison note][cmp], section 4 |
| I5 | The correction method is portable across forecasters | The same kind runs on the pooled trend in the tests and on `r4_winners` in the trial, with no change | [`test_city_drift.py`][cdtest]; [`at_city_drift.yaml`][cdyaml] |

## Reproducibility and openness

*Rubric: "Ability for others to reproduce the work using provided materials."*

- **The package checks itself.** `python code/reproduce.py` rebuilds all 5,880 forecasts from
  `data/` and compares them with `submission.csv`. Four builds on 2026-11-10 gave identical
  bytes.
- **Every result names its inputs.** Each trial note records the config, the commit, the data
  content hash and the folds; candidates and selection rules are written in the config header
  before the runs ([`at_city_drift.yaml`][cdyaml]).
- **Tests guard the cut-off.** 252 tests pass; they include look-ahead checks (features ignore
  years after the origin) and nesting checks (zero strength reproduces the base).
- **The research record is open.** Hypotheses, critiques and a ledger of 620 validated events
  are in the repository, including the places where the record and the files disagreed
  ([`ledger/`][ledger]).

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
[data]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/docs/data.md
[reg]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/src/proto_star/forecasters/__init__.py
[fr]: https://github.com/mauposad/proto-star-challenge/blob/agent/ml-challengers/docs/trials/final_round.md
[p13]: https://github.com/mauposad/proto-star-challenge/tree/agent/paper-p13-arima
[cmp]: https://github.com/mauposad/proto-star-challenge/blob/4ac87a8f1a3bfb29ab85b7a7b2e9c0fefedc14b7/docs/trials/approaches_comparison.md
