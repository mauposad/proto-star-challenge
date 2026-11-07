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
   window (at least 3 for the 5/10/15-year means, 10 for the 30-year level and scale).
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

8. **Solver.** `QuantileRegressor` uses HiGHS interior point (`highs-ipm`). It is about 6x
   faster than the default simplex on our ~12k-row fits, and the coefficients agreed in a spot check.
9. **Lags.** The linear variant sets missing lags to 0. Real series have gaps, so P14's
   fixed-window AR is only approximated.

## Our results

Same backtest origins as the baseline (ADR 0004 folds 1980/1995/2011, 7-year horizon).
Trial note: `docs/trials/paper_p09_p14_pooled.md`. Command:
`OMP_NUM_THREADS=5 uv run proto-star climate-trial configs/agent_paper_p09_p14_pooled.yaml --record`
(code commit `993784c`, about 13 minutes on 5 threads). Master content hash
`99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1`.

**Chosen variant `hybrid_ridge_all_cdd`** (pooled ridge on all history for CDD only, `current_best`
for the other three metrics). All-years window, skill in %:

| Origin | Score | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1980 | 0.24 | -2.53 | -2.06 | 0.00 | 0.00 | 3.03 |
| 1995 | 4.13 | 1.39 | 11.30 | 0.00 | 0.00 | 5.23 |
| 2011 | 6.44 | 5.16 | 8.05 | 0.00 | 0.00 | 17.70 |

`current_best` on the same rows: -0.75 / 3.56 / 5.95 (CDD skill -0.93 / 2.93 / 15.73).

Mean `raw_score` over the 3 origins (all / years 1-3 / years 4-7), and the number of origins
that beat `current_best` (all / 1-3 / 4-7):

| Method | All | Years 1-3 | Years 4-7 | Wins vs current_best | CDD skill 4-7 | Temp skill 4-7 |
|---|---|---|---|---|---|---|
| `current_best` | 2.92 | 0.63 | 4.68 | - | 6.84 | 11.90 |
| `ten_year_mean` | 1.34 | -0.62 | 2.78 | 0/0/0 | 6.84 | 11.90 |
| **`hybrid_ridge_all_cdd`** | **3.60** | **0.94** | **5.54** | **3/2/3** | 10.27 | 11.90 |
| `hybrid_ql_cdd` (median, 60 y) | 3.20 | 0.85 | 4.90 | 2/2/2 | 7.70 | 11.90 |
| `hybrid_ql_all_cdd` (median, all history) | 2.34 | -0.96 | 4.73 | 1/1/1 | 7.04 | 11.90 |
| `pooled_ql` (median, all metrics) | 2.22 | 1.79 | 2.21 | 1/2/1 | 7.70 | 2.71 |
| `pooled_ql_lags20` | 1.37 | 1.65 | 0.90 | 0/1/1 | 7.12 | 0.56 |
| `pooled_ql_all_history` | 0.69 | -2.04 | 2.43 | 1/0/1 | 7.04 | 6.33 |
| `pooled_ridge` (60 y) | 2.24 | 1.64 | 2.38 | 2/2/1 | 8.49 | 3.08 |
| `pooled_ridge_all_history` | 2.75 | 1.03 | 3.76 | 1/2/1 | 10.27 | 7.51 |
| `pooled_ridge_all_alpha100` | 2.78 | 1.06 | 3.80 | 1/2/1 | 10.32 | 7.60 |
| `pooled_ridge_all_lags20` | 2.34 | 1.24 | 2.90 | 0/2/1 | 10.27 | 6.03 |
| `pooled_ridge_all_nostatic` | 2.70 | 0.76 | 3.87 | 1/2/2 | 10.19 | 8.31 |
| `pooled_ridge_pool_metrics` | 1.58 | 1.17 | 1.73 | 1/2/1 | 8.70 | 5.59 |
| `pooled_hgb` (quantile GBM) | 0.93 | 1.13 | 0.56 | 0/2/1 | 4.24 | 3.34 |
| `pooled_hgb_pool_metrics` | 1.77 | 1.83 | 1.58 | 1/2/1 | 5.22 | 5.01 |
| `pooled_hgb_all_pool_metrics` | 2.19 | 1.22 | 2.80 | 1/2/0 | 7.92 | 7.38 |

Full per-metric, per-window tables are in the trial note.

## Takeaways

- **The pooled model helps CDD, and only CDD.** Every pooled *linear* variant beat the 10-year
  mean on CDD skill in years 4-7 (7.0% to 10.3% vs 6.8%). Two of the three boosted variants
  did not. For temperature, all of them lost to the
  10-year mean (at best 8.3% vs 11.9% in years 4-7). For precipitation and hottest day they lost
  to the 30-year mean (small negative skill). Normalizing on the 30-year level and pooling many
  decades teaches the model to shrink toward the 30-year mean. That is right for noisy metrics
  but too conservative for the recent warming trend in annual temperature.
- **The median objective (P09) did not beat squared loss here.** On CDD, ridge beat the
  pinball-0.5 linear model at both history lengths. The full-history quantile fit
  (`origin_stride: 2`) was the weakest linear variant. We did not find out why. Possible causes:
  the thinned origins, or the approximate interior-point solution. Quantile boosting was worse
  than both linear models, which agrees with P14's point that simple global linear models do well.
- **Longer memory (P14's main lever) did not help.** 20 lags were worse than 10 for both losses.
  The trailing means already summarize long memory, and annual data has few effective points.
- **Pooling across metrics hurt** precipitation in particular.
- **Adopted for submission: `hybrid_ridge_all_cdd`.** It beats `current_best` at 3/3 origins
  over all years and in years 4-7, and at 2/3 in years 1-3 (it loses CDD at 2011 years 1-3:
  7.0% vs 11.1%). The gain is modest (+0.68 all, +0.86 years 4-7), and it was picked from 15
  variants on 3 origins, so expect some selection optimism. The adopted model is P14's global
  linear model with squared loss. The P09 median loss did not make it in.
- Status: **adapted**. Keep the CDD hybrid. Abandon the pooled model for the other metrics
  unless it gets a trend-aware level (for example a 10-year normalization for temperature).
