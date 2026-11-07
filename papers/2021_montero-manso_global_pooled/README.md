# Pooled (global) median models: Montero-Manso & Hyndman 2021 (P14) with quantile loss (P09)

| | |
|---|---|
| **Authors** | P14: Pablo Montero-Manso, Rob J Hyndman. P09: Roger Koenker, Gilbert Bassett Jr.; Nicolai Meinshausen; Jerome H. Friedman |
| **Year / venue** | P14: 2021, International Journal of Forecasting 37(4), 1632-1653 (arXiv preprint 2020). P09: Koenker & Bassett 1978, *Econometrica* 46(1) "Regression Quantiles"; Meinshausen 2006, *JMLR* 7 "Quantile Regression Forests"; Friedman 2001, *Annals of Statistics* 29(5) "Greedy function approximation: a gradient boosting machine" (quantile / LAD loss for boosting) |
| **Link** | P14: arXiv [2008.00444](https://arxiv.org/abs/2008.00444). P09: DOIs not checked (see V02 in docs/literature/README.md) |
| **Code released by authors** | P14: none used. We use scikit-learn's `QuantileRegressor` and `HistGradientBoostingRegressor(loss="quantile")` |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p09-p14-pooled` (no PR) |

## Summary

**P14.** A *local* method fits one model per series. A *global* method fits one function to
every series in the group. The authors show that the two classes can produce the same forecasts
without any assumption that the series are similar. Local complexity grows with the number of
series, but global complexity stays constant. So a global model can afford much more memory
(a longer autoregressive order) and still generalize. In their empirical study, "purposely naive"
global linear autoregressive models are competitive with local methods while using about two
orders of magnitude fewer parameters. Two practical points matter: normalize each series before
pooling, and pick the lag order (memory) carefully, since global models benefit from long lags.

**P09.** Koenker & Bassett define regression quantiles by minimizing the asymmetric absolute
("pinball" / check) loss. At quantile 0.5 this is least-absolute-deviation regression, the
conditional median, and it minimizes MAE. Our official score is a relative MAE skill, so the
median is the right target. Meinshausen's quantile regression forests and boosting with the
quantile loss (Friedman 2001) give non-linear conditional quantiles.

## Architecture

- Model family: P14 uses global linear AR models (OLS on lag windows), plus global deep nets
  and boosting as non-linear variants. P09 uses linear quantile regression, QRF and quantile GBM.
- Inputs (P14): a window of the last `L` observations of each series, with each window
  normalized per series (the paper studies scaling choices). The same weights apply to every series.
- Outputs (P14): one-step forecasts, iterated (recursive) to the horizon.
- Loss: P14 uses squared error / MASE-style evaluation. P09 uses pinball loss at quantile tau.
- Hyperparameters: P14's key one is the AR order `L`. Global models can use much larger `L`
  than local ones.

## Results claimed by the authors

P14 reports that, on the M1, M3, M4 tourism, and other benchmark collections, global linear
models with long memory are competitive with or better than strong local benchmarks (ETS,
ARIMA, Theta). It does not give numbers on climate data. We do not copy their figures here.
P09: method papers with no benchmark relevant to us.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Group of series | 210 cities x 4 metrics = 840 annual series, about 1851-2018, with gaps |
| Data | annual master table (`train` frame of each fold only): valid-year metric values, Lat, Lon, region |
| Target(s) | `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd` |
| Horizon | 7 years after the cutoff (2019-2025; backtest folds 1980, 1995, 2011) |
| Metric | relative MAE skill vs 30-year mean, so the median (pinball tau=0.5) is the matching objective |

## Deviations

1. **Direct, not recursive, multi-horizon.** P14 iterates one-step AR forecasts. We fit a
   *direct* model for leads 1-7 instead: one model per lead for the linear variant, or lead
   as a feature for the boosted variant. Why: annual climate series are noisy, so recursive
   7-step forecasts compound errors. Also, the median is not preserved under recursion (the
   median of a sum is not the sum of medians), so a direct pinball fit targets exactly what is
   scored at each lead.
2. **Normalization.** Each training example (series, origin t) is centred on its trailing
   30-calendar-year mean (the same window as the reference forecast) and divided by its
   trailing 30-year standard deviation. Both are computed from years <= t only. The target is
   `(y[t+h] - level_t) / scale_t`, and the forecast is `level + scale * model output`.
   So the model learns how far to move from the reference level.
3. **Gaps.** Invalid years (more than 10 missing days) are NaN. Lags stay NaN for the
   boosted model, which handles NaN natively. For the linear model, NaN lags are set to 0,
   the series level in normalized units. Trailing means use the valid years in each calendar
   window (min 5 for 10/15-year means, 10 for the 30-year level and scale).
4. **Extra covariates.** P14 pools lags only. We add trailing 5/10/15-year means
   (normalized), Lat/Lon (standardized inside the pipeline) and region one-hot, as the task asked.
5. **Loss.** P14 uses squared error. We use pinball loss at 0.5 (P09), and keep an OLS-style
   (`ridge`) ablation to test whether the median objective matters.
6. **Fallback.** Series with too little recent history at the cutoff for a level and scale
   (fewer than 10 valid years in the last 30) get the `current_best` forecast.
7. **Per-metric hybrid.** `pooled_hybrid_p09_p14` uses the pooled model only for the metrics
   given in `model_metrics`, and `current_best` for the rest.

## Implementation

- Registry names: `pooled_median_p09_p14` (main), `pooled_hybrid_p09_p14` (per-metric hybrid)
- Code: `src/proto_star/forecasters/pooled_p09_p14.py`, features in
  `src/proto_star/forecasters/_pooled_features.py`
- Config: `configs/agent_paper_p09_p14_pooled.yaml`
- Tests: `tests/test_forecasters_pooled_p09_p14.py`
- Leakage review: the wide city x year panel is built from the fold's `train` frame only
  (via `annual_to_long`, so the valid-year screen applies). Lags use `shift(k)`, k >= 0
  relative to the origin. Trailing windows are pandas `rolling` with the default right
  alignment (no `center`). Training targets are `y[t+h]` with `t+h <= cutoff`. Scalers and the
  region encoder sit inside the sklearn pipeline, so they are fitted on training examples.
  A test checks that changing every value after the cutoff, and the forecast-year values, leaves
  predictions unchanged.

## Our results

See the section at the end (filled from the recorded trial run).

## Takeaways

See the section at the end.
