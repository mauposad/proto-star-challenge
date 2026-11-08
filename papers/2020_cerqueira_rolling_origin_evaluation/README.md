# Evaluating forecasts on rolling origins (P10, P12, P19)

One shared card for three evaluation-design references. They are not forecasting methods, so
nothing was "reproduced". We used their shared idea, many time-ordered forecast origins, to test
our own fold design (ADR 0004).

| | |
|---|---|
| **Authors** | P19: Vitor Cerqueira, Luis Torgo, Igor Mozetič. P12: Rob J. Hyndman, George Athanasopoulos. P10: Christoph Bergmeir, José M. Benítez |
| **Year / venue** | P19: 2020, *Machine Learning* 109, 1997–2028 (arXiv 1905.11744, 2019). P12: *Forecasting: Principles and Practice*, 2nd ed., online textbook. P10: 2012, *Information Sciences* 191, 192–213 |
| **Link** | P19: https://arxiv.org/abs/1905.11744. P12: https://otexts.com/fpp2/accuracy.html. P10: DOI TBD (not checked; the publisher page did not load) |
| **Code released by authors** | P19: TBD (not checked). P12: the `tsCV()` function in the R `forecast` package. P10: TBD |
| **PDF in repo?** | no |
| **Status** | adapted (evaluation study, no forecaster) |
| **Owner** | agent |
| **Branch / PR** | `agent/eval-p10-p12-p19-folds` |

## Summary

- **P12 (rolling forecasting origin).** Score a forecaster on a series of test sets. Each one
  trains only on data before its origin, and the origin moves forward in time. Average the error
  over origins, and choose the model with the smallest cross-validated error. For multi-step
  forecasts, score the errors at the horizon you care about.
- **P19 (empirical comparison of estimators).** On 62 real and 3 synthetic series, the authors
  compare cross-validation and out-of-sample estimators of forecast error. The abstract says
  cross-validation can be used on stationary series. On real series with several sources of
  non-stationarity, out-of-sample methods that keep observations in time order gave the most
  accurate estimates.
- **P10 (blocked cross-validation).** Listed in our literature index as the reference for
  blocked cross-validation in time-series evaluation. We did not read the full text; this card
  makes no claims about its results.

## Architecture

None: these are evaluation procedures. What we take from them:

- origins in time order, each trained only on data up to its cut-off (P12, P19)
- more origins than the three in ADR 0004, so the estimate depends less on any one origin
- scores at the horizon that matters: years 4–7, which match the Final Score (P12)

## Results claimed by the authors

P19 (from the abstract): out-of-sample methods that keep time order gave the most accurate error
estimates on non-stationary real-world series. No numbers are copied here. P10 and P12: TBD (not
read for numbers).

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | 210 cities, annual indices through 2018 |
| Origins | ADR 0004: 1980, 1995, 2011. Study: 1980–2010 every 3 years, plus 2011 (12 origins) |
| Horizon | 7 years, scored as years 1–3, 4–7 and all |
| Metric | official raw score: mean relative-MAE skill against the 30-year mean, ×100, no floor |

## Deviations

- No forecaster is implemented. The study re-scores existing round-1 methods.
- With 3-year steps and a 7-year horizon, test windows overlap (each test year is scored from
  2 or 3 origins). P10's blocked design would avoid overlap, but with non-overlapping 7-year
  blocks before 2019 we would have only about 4–5 origins after the 30-year warm-up. We accepted
  the overlap and report it as a caveat.
- The recency weights (linear and exponential with a 10-year half-life) are our own addition,
  not from any of the three papers. They were fixed in the config before the first run.
- DeepAR and N-BEATS were left out. They are too heavy for this laptop across 12 origins.

## Implementation

- Registry name: none (no forecaster)
- Code: `src/proto_star/fold_study.py`, `scripts/fold_study_p10_p12_p19.py`
- Config: `configs/agent_fold_study_p10_p12_p19.yaml`
- Tests: `tests/test_fold_study.py`
- Leakage review: every origin goes through `proto_star.backtest.compare_forecasters`, which
  trains only on years up to the cut-off and checks this with `assert_weather_cutoff`. The last
  origin (2011) forecasts through 2018. The warming diagnostics that use test years are only for
  explaining results; nothing is selected or weighted with them.

## Our results

See [docs/trials/fold_study.md](../../docs/trials/fold_study.md) and the generated tables in
[docs/trials/fold_study_results.md](../../docs/trials/fold_study_results.md).

## Takeaways

See the write-up and the proposed [ADR 0006](../../docs/decisions/0006-fold-design-dense-origins.md).
