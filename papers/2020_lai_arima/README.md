# Use of the ARIMA model to forecast near-term regional temperature and precipitation

| | |
|---|---|
| **Authors** | Yuchuan Lai, David A. Dzombak |
| **Year / venue** | 2020, *Weather and Forecasting* 35(3) |
| **Link** | https://doi.org/10.1175/WAF-D-19-0158.1 |
| **Code released by authors** | R package `scifi` (github.com/yuchuan-lai/scifi), no license file found (literature V04). We read `R/annual_fcast.R` only to confirm the method. Nothing was copied; the Python here is a reimplementation |
| **PDF in repo?** | no |
| **Status** | adapted (did not beat `current_best`; not submitted) |
| **Owner** | agent (P13 track) |
| **Branch / PR** | `agent/paper-p13-arima` |

## Summary

The authors also built the city records our dataset comes from. They forecast annual
temperature and precipitation indices per city 2 to 20 years ahead with a univariate ARIMA
model fitted to each city's full annual history. The model blends recent observations (AR/MA
terms and differencing) with the long-term trend (a drift term, used only when a trend test
says so). Normality of the residuals decides whether a Box-Cox transform is used. They report
that ARIMA is not best for every index, but it is generally more accurate than a linear trend
and other common statistical methods, especially for interval forecasts.

## Architecture

The method as the authors' reference code (`fcast_annual(..., forecast.model = "ARIMA")`)
applies it to one city and one index:

1. **Data.** All non-missing annual values before the forecast start. Missing years are
   dropped and the remaining values are treated as consecutive.
2. **Trend test.** Mann-Kendall on the series. If p < 0.2, drift is allowed.
3. **Order selection.** `forecast::auto.arima` with defaults: KPSS unit-root tests pick
   d ≤ 2 (alpha 0.05). Then a stepwise Hyndman-Khandakar search over p, q ≤ 5 by AICc, with
   a constant (mean when d = 0, drift when d = 1) when allowed.
4. **Normality test.** Shapiro-Wilk on the residuals of that model (on the data itself if the
   order is (0,0,0)). If p < 0.05, the series is Box-Cox transformed. Lambda is the
   log-likelihood maximiser on [-1, 2], after shifting the series positive if it has zeros or
   negatives. The order is then reselected on the transformed scale.
5. **Final fit.** `Arima` refit with the selected (p, d, q) and `include.drift` set by the
   trend test, so with d = 0 and a trend the model is mean + linear trend + ARMA errors. When
   the order is (0,0,0) the stepwise model is kept (a mean).
6. **Forecast.** Point forecast is the back-transformed mean (the median on the original
   scale, no bias adjustment), from the last observed year onward. Non-temperature indices are
   clipped at 0. Prediction intervals (80 %, 95 %) are also produced; we do not need them.

Horizon: 2 to 20 years. No training beyond maximum likelihood; no tuned hyperparameters.

## Results claimed by the authors

From the abstract only (full text not read): ARIMA was not the best for every climate index,
but it generally gave more accurate projections, especially interval forecasts, than a linear
trend and other common statistical methods. No numbers are copied here.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data: annual indices per city, full record | annual master per city (≤ cutoff), quality-screened by `annual_to_long` |
| Target(s): many temperature and precipitation indices | `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd` |
| Horizon: 2–20 years | 7 years (1–7 years after each cutoff) |
| Evaluation: hindcasts vs linear trend etc. | relative MAE skill vs 30-year mean, origins 1980/1995/2011 (ADR 0004) |
| Cut-off | each fold's cutoff; 2018 for the submission |

## Deviations

1. **Python, not R `forecast`.** statsmodels has no `auto.arima`, so `arima_p13.py` codes the
   stepwise search itself: KPSS (`statsmodels` `kpss`, level, lag `trunc(3·sqrt(n)/13)`),
   start models (2,2), (0,0), (1,0), (0,1) with a constant and (0,0) without, then ±1 moves
   in p and q and the constant toggle until AICc stops improving. Models with an AR or MA
   root inside 1.01 are rejected, as in `forecast`. statsmodels state-space MLE replaces
   R's CSS-ML, so fitted values and AICc differ slightly.
2. **Mann-Kendall** is `scipy.stats.kendalltau` against time (tau-b, asymptotic p-value),
   not the `Kendall` package. The second trend test on the Box-Cox series is skipped: the
   test is rank based, so a monotone transform cannot change it.
3. **Box-Cox lambda** maximises the i.i.d. normal profile log-likelihood (what
   `BoxCox.lambda(method = "loglik")` does for a plain vector) with a bounded optimiser.
4. **Fallback.** A series with fewer than `min_obs` valid years, a failed final fit, or a
   non-finite forecast gets the 30-year mean instead. The paper has no fallback. Counts are
   reported in *Our results*.
5. **CDD** is not one of the paper's indices. It is treated like precipitation (clipped at 0).
6. **Variants beyond the paper** (marked as such in the config): a shorter history window,
   no Box-Cox, and a hybrid that uses ARIMA only for some metrics and `current_best` for the
   rest. The paper's own setting is variant `arima_lai2020`.
7. Forecasts are point values only; intervals are not computed.

## Implementation

- Registry name: `arima_lai2020`
- Code: `src/proto_star/forecasters/arima_p13.py`
- Config: `configs/agent_paper_p13_arima.yaml`
- Tests: `tests/test_forecasters_arima_p13.py`
- Leakage review: the forecaster reads only the `train` frame it is given, through
  `annual_to_long(train, cutoff_year=cutoff)`, which rejects later years. Every fit, test and
  lambda is computed per series from those rows. The fallback 30-year mean comes from the same
  rows. No randomness.

## Our results

Trial `configs/agent_paper_p13_arima.yaml`, write-up `docs/trials/paper_p13_arima.md`, run dir
`runs/trials/20261106-235252_paper_p13_arima/` (git-ignored). Base commit `e507f5e` with this
branch's new files uncommitted at run time; master hash `99128065…bb04d1`. Command:
`uv run proto-star climate-trial configs/agent_paper_p13_arima.yaml --record`, called through a
wrapper whose only change was turning on INFO logging for the path counts below. The trial took
about 16 minutes with 5 worker processes.

Raw score (official score without the floor), all 7 forecast years:

| Origin | `arima_paper` | `arima_temp_cdd` | `arima_window50` | `current_best` | `ten_year_mean` |
|---|---|---|---|---|---|
| 1980 | -2.59 | -0.86 | -9.30 | -0.75 | -2.53 |
| 1995 | 0.37 | 2.70 | -1.37 | 3.56 | 1.39 |
| 2011 | 3.01 | 4.79 | 3.91 | 5.95 | 5.16 |

Mean over origins, all / years 1–3 / years 4–7 (origins beating `current_best` in brackets):

| Method | All | Years 1–3 | Years 4–7 |
|---|---|---|---|
| `arima_paper` (the paper) | 0.26 (0/3) | -0.96 (0/3) | 1.06 (0/3) |
| `arima_temp_cdd` | 2.21 (0/3) | 1.11 (2/3) | 2.98 (0/3) |
| `arima_window50` | -2.25 (0/3) | -2.60 (0/3) | -2.32 (1/3) |
| `current_best` | 2.92 | 0.63 | 4.68 |
| `ten_year_mean` | 1.34 | -0.62 | 2.78 |

Per-metric skill in percent, mean over origins, years 4–7 (all years in brackets):

| Method | avg_temp | precip | hottest_day | cdd |
|---|---|---|---|---|
| `arima_paper` | 4.77 (2.87) | -2.27 (-2.35) | -5.42 (-5.43) | 7.16 (5.97) |
| `arima_window50` | -1.79 (-3.08) | -4.72 (-4.11) | -6.02 (-4.54) | 3.27 (2.74) |
| `current_best` | 11.90 (5.76) | 0.00 (0.00) | 0.00 (0.00) | 6.84 (5.91) |
| `ten_year_mean` | 11.90 (5.76) | -4.44 (-3.94) | -3.16 (-2.39) | 6.84 (5.91) |

`arima_temp_cdd` equals `arima_paper` on temperature and CDD and `current_best` on the rest.

Paths taken by `arima_paper` (840 city/metric series per fold; 1980 / 1995 / 2011): 832 / 832 /
839 fitted by ARIMA; 8 / 8 / 1 too short (< 10 valid years) and given the 30-year mean; 0 fit
failures. Box-Cox was used for 142 / 157 / 157 series and drift for 454 / 494 / 506. The
selected d was 0 for 493 / 490 / 456 series and 1 for 339 / 342 / 383; never 2.
`arima_window50` fell back for 9 / 17 / 9 series, including 8 / 9 / 6 with no valid year
in the window.

Derived from the same results, not a separate run: ARIMA for CDD only, with `current_best`
elsewhere, differs from `current_best` only through CDD skill. Its years 4–7 raw scores would be
-2.14 / 8.63 / 7.80, against -1.93 / 8.02 / 7.95 (1 of 3 origins). Its years 1–3 scores would
be 0.71 / -1.21 / 2.04, against 0.74 / -1.68 / 2.82. That is not a real win, so it was not
added as a variant.

## Takeaways

- Applied faithfully, the paper's method loses to `current_best` at every origin and in every
  window (years 4–7: 1.06 against 4.68). It also loses to `ten_year_mean` (1.06 against 2.78).
- Most of the loss is on precipitation and hottest day. There `current_best` uses the 30-year
  mean, while ARIMA's trend and random-walk forecasts follow noise.
- On annual temperature it trails the 10-year mean (4.77 % against 11.90 % in years 4–7).
  Fitting the whole record, which for some cities starts in the 1800s, sets the level and drift
  from the long-term trend rather than the recent warming. The 50-year window was worse still,
  most of all at 1980 (temperature skill -23.9 % over all years).
- CDD is the only metric where it matches or beats `current_best` (7.16 % against 6.84 % in
  years 4–7), and only at 1 of 3 origins. That gain is too small and too uneven to adopt.
- Decision: the submission stays `current_best`. Status is `adapted`. Possible follow-ups, not
  run: an ARIMA residual correction on top of the 10-year mean, or a model pooled across cities
  (P14).
