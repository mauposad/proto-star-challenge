# DeepAR: Probabilistic forecasting with autoregressive recurrent networks

| | |
|---|---|
| **Authors** | David Salinas, Valentin Flunkert, Jan Gasthaus, Tim Januschowski |
| **Year / venue** | International Journal of Forecasting 36(3), 2020 (preprint 2017) |
| **Link** | https://doi.org/10.1016/j.ijforecast.2019.07.001, https://arxiv.org/abs/1704.04110 |
| **Code released by authors** | none in the paper (Amazon SageMaker / GluonTS implementations exist; not used) |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent |
| **Branch / PR** | `agent/paper-p05-p08-neural` |

## Summary

DeepAR trains **one global autoregressive RNN** over a large set of related series instead of
one model per series. At each step the network receives the previous value and covariates and
outputs the parameters of a likelihood (Gaussian for real values, negative binomial for counts).
Training maximises the likelihood over windows with teacher forcing. Forecasting draws Monte
Carlo sample paths by feeding each sample back as the next input. Per-series scaling lets
series of very different magnitudes share the same weights.

## Architecture

- Model family: LSTM, 3 layers; 40 cells for parts/electricity/traffic, 120 for ec/ec-sub
- Inputs per step: previous value z_{t-1} divided by a per-item scale ν (1 + mean over the
  conditioning range), time covariates, item "age", and an item embedding
- Output: likelihood parameters per step; Gaussian μ = linear(h), σ = softplus(linear(h))
- Training: windows covering a conditioning range plus the prediction range, loss = negative
  log-likelihood over the whole window, Adam, windows sampled per epoch
- Forecast: ancestral sampling of many paths (quantiles from the samples)

## Results claimed by the authors

From the abstract: on several real-world datasets, "accuracy improvements of around 15%
compared to state-of-the-art methods" (evaluated with quantile losses). These are the paper's
claims, **not** our results.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data: thousands of related series | 840 (city, metric) annual series, valid city-years only, ≤ 2018 |
| Target(s) | `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd` in one global model |
| Horizon | 7 years (2019–2025; 7-year folds at 1980, 1995, 2011) |
| Metric: ρ-risk (quantile loss) | relative MAE skill vs the 30-year mean → point forecast = **median** of the sample paths |
| Item embedding | metric embedding (dim 4) and city embedding (dim 4) |

## Deviations

- **Size.** 2 LSTM layers of 32 cells, dropout 0.1 between layers; the paper uses 3 layers of
  40 (or 120).
- **Scaling.** The paper divides by ν = 1 + mean of the conditioning range. For annual temperature the
  year-to-year variation is small next to the level, so dividing by the level would squash it. Instead we centre each window on the mean of its observed context values
  and divide by the series' training-fold standard deviation.
- **Covariates.** No calendar covariates (annual data, no seasonality) and no age feature;
  metric and city embeddings only. Each step also gets an observed/missing flag.
- **Missing values.** Missing context years enter as 0 (the window level) with flag 0, and are
  left out of the likelihood; the paper's data has no such gaps to impute.
- **Context.** 21 years of context (3 × horizon) plus 7 prediction years per training window;
  every window is used each epoch (no sampling).
- **Early stopping.** On the inner split inside each training fold (origin 7 years before the
  cut-off), scored by the MAE of a mean-path rollout; best weights kept. The paper trains a
  fixed number of epochs.
- **Ensemble.** 3 seeds × 100 sample paths, pooled, then the median per year. The paper uses
  one model and reports quantiles.
- **Fallback.** Series whose last context window has fewer than `min_obs_fraction` × context
  observed years, and metrics outside `neural_metrics` (hybrid variant), get the
  `current_best` baseline for their metric.

## Implementation

- Registry name: `deepar_p08`
- Code: `src/proto_star/forecasters/deepar_p08.py`, shared windowing in
  `src/proto_star/forecasters/_neural_common.py`, network and sampling in
  `src/proto_star/forecasters/_neural_torch.py` (torch imported only when the forecaster runs)
- Config: `configs/agent_paper_neural.yaml` (variants `deepar_global`, `deepar_hybrid`)
- Tests: `tests/test_forecasters_deepar_p08.py`
- Leakage review: as for N-BEATS. Training only sees the fold's `train` frame; scales come from
  training years; early stopping happens inside the training fold; sampling uses a seeded
  `torch.Generator`, so a rebuild on the same machine and thread count is identical.

## Our results

Same backtest origins as the baseline (ADR 0004). Raw score = the official score without the
floor at zero; skills in percent, all 7 forecast years. Means over origins, all / years 1–3 /
years 4–7: `current_best` 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / −0.62 / 2.78.

| Variant | all | years 1–3 | years 4–7 | origins beating `current_best` (all / 4–7) |
|---|---|---|---|---|
| `deepar_global` (all metrics) | 2.39 | 0.25 | 3.87 | 0 / 1 |
| `deepar_hybrid` (temperature + CDD only) | 3.36 | 0.96 | 5.08 | 2 / 1 |
| `deepar_hybrid_seed7` (same, other seed) | 3.03 | 0.83 | 4.63 | 1 / 1 |

Per origin, all years:

| Origin | Score global / hybrid / hybrid seed 7 | `ten_year_mean` | avg_temp skill (global / hybrid) | precip skill (global) | hottest_day skill (global) | cdd skill (global / hybrid) |
|---|---|---|---|---|---|---|
| 1980 | −0.79 / −0.91 / −0.75 | −2.53 | −2.71 / −4.15 | −1.20 | −0.41 | 1.15 / 0.51 |
| 1995 | 2.22 / 3.58 / 3.00 | 1.39 | 9.89 / 10.86 | −1.97 | −3.48 | 4.42 / 3.44 |
| 2011 | 5.75 / 7.40 / 6.85 | 5.16 | 12.00 / 12.82 | −0.74 | −2.59 | 14.32 / 16.79 |

Years 4–7 per origin, `deepar_hybrid` vs `current_best`: −3.27 vs −1.93 (1980), 7.43 vs 8.02
(1995), 11.09 vs 7.95 (2011).

Command, commit and run dir: `uv run proto-star climate-trial configs/agent_paper_neural.yaml
--record` (after `uv sync --extra hf`), base commit `e507f5e` plus this branch's new files,
master hash `99128065…bb04d1`, run dir `runs/trials/20261107-004902_paper_neural/` (not in the
repo). Write-up: `docs/trials/paper_neural.md`. One seed on all metrics takes about 2.4 min on
the 2011 fold; the hybrid's 2018 final fit (3 seeds) takes about 130 s on 2 threads and is
bit-identical when rebuilt.

## Takeaways

- `deepar_hybrid` has the best mean of every variant tried (3.36 / 0.96 / 5.08 against
  `current_best`'s 2.92 / 0.63 / 4.68). But in years 4–7, the window behind the Final Score, it
  wins only at the 2011 origin and loses at 1980 and 1995, and its seed-7 replica falls below
  `current_best` there (4.63). We read the mean gain as one strong origin plus seed noise, so it
  was **not** chosen for submission; `submit` stays `current_best`.
- The global model on all four metrics loses on precipitation and the hottest day, like N-BEATS.
- At the most recent origin the likelihood-trained median forecasts temperature and CDD better
  than both N-BEATS and the 10-year mean.
- Status: adapted, not adopted. Worth revisiting with more seeds (5–10) to shrink the seed noise,
  judged again on the same folds, and adopted only with an ADR.
