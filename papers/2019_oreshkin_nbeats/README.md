# N-BEATS: Neural basis expansion analysis for interpretable time series forecasting

| | |
|---|---|
| **Authors** | Boris N. Oreshkin, Dmitri Carpov, Nicolas Chapados, Yoshua Bengio |
| **Year / venue** | 2019 preprint; ICLR 2020 |
| **Link** | https://arxiv.org/abs/1905.10437 |
| **Code released by authors** | https://github.com/ElementAI/N-BEATS (not used; we reimplemented the architecture in plain PyTorch) |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent |
| **Branch / PR** | `agent/paper-p05-p08-neural` |

## Summary

N-BEATS is a pure deep-learning univariate forecaster: no recurrence, no convolutions and no
time-series-specific feature engineering. A deep stack of fully connected blocks maps a
lookback window straight to a multi-step forecast. Each block outputs a *backcast*, which is
subtracted from its input before the next block (doubly residual stacking), and a partial
*forecast*, and the partial forecasts are summed. With fixed polynomial and Fourier bases the
blocks become an interpretable trend + seasonality decomposition. One model is trained over
all series of a dataset, and the final forecast is the median of a large ensemble.

## Architecture

- Model family: deep MLP with residual backcast/forecast blocks
- Block: 4 FC layers with ReLU → linear projections to expansion coefficients θ_b, θ_f →
  basis g_b, g_f. *Generic* block: learnt linear bases. *Trend* block: polynomial basis
  of small degree p over normalized time. *Seasonality* block: Fourier basis.
- Stacks: generic model = 30 stacks × 1 block, width 512; interpretable model = trend stack
  (3 blocks, width 256, polynomial degree 2) + seasonality stack (3 blocks, width 2048); weights
  shared within each interpretable stack.
- Inputs: lookback of 2H to 7H points (H = horizon); output: H points directly (no
  autoregression).
- Loss and training: sMAPE, MASE and MAPE on M4/M3 (MAPE on TOURISM), Adam, windows sampled
  from the recent history of each series.
- Ensemble: 180 models (6 lookbacks × 3 losses × 10 bags), combined by median.

## Results claimed by the authors

From the abstract: state-of-the-art performance for both configurations on M4, M3 and TOURISM,
"improving forecast accuracy by 11% over a statistical benchmark and by 3% over last year's
winner of the M4 competition"; the interpretable variant comes "without considerable loss in
accuracy". These are the paper's claims, **not** our results.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data: M4/M3/TOURISM series | 210 cities × 4 metrics of annual indices, valid city-years only (`annual_to_long`), ≤ 2018 |
| Target(s): one univariate series | each (city, metric) series of `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd` |
| Horizon: dataset-specific H | 7 years (2019–2025; 7-year folds at 1980, 1995, 2011) |
| Metric: sMAPE / MASE / OWA | relative MAE skill vs the 30-year mean, years 4–7 weighted most |
| One model per dataset/frequency | one model per metric, shared by all 210 cities |

## Deviations

- **Sizes.** Our series are ~85–130 annual points with gaps, so the models are tiny: width 64,
  2 FC layers per block, 3 generic blocks (generic variant) or a 2-block trend stack sharing
  weights + 1 generic block (interpretable variant). The paper uses width 256–2048, 4 layers,
  up to 30 stacks.
- **No seasonality stack.** Annual series have no seasonal cycle; the interpretable variant
  replaces the seasonality stack with a generic block. Trend basis degree 2, as in the paper.
- **Gaps.** Years that fail the missing-days rule are 0 in the scaled input; an observed-value
  mask is concatenated to every block's input, backcast residuals are masked, and the loss
  ignores missing targets. The paper's series have no gaps.
- **Scaling.** Each window is centred on the mean of its observed inputs and divided by the
  series' standard deviation over the training fold (the paper needs no scaling because its
  losses are scale-free).
- **Loss.** MAE (L1) only, matching the MAE-based official skill; the paper ensembles sMAPE,
  MASE and MAPE (sMAPE/MAPE are unstable near zero CDD values).
- **Ensemble.** 9 members: lookbacks 14, 21, 28 (2H, 3H, 4H) × 3 seeds, median combined. The
  paper uses 180 members and lookbacks up to 7H; 7H = 49 years would leave too few windows.
- **Early stopping.** On an inner split inside each training fold: the origin 7 years before
  the cut-off forecasts the last 7 training years; training windows only score targets up to
  that origin. Best-validation weights are kept (no refit). The paper uses a fixed number of
  iterations.
- **Fallback.** A series whose last lookback window has fewer than `min_obs_fraction` × lookback
  observed years gets the `current_best` baseline for its metric; so do metrics outside
  `neural_metrics` (hybrid variant).

## Implementation

- Registry name: `nbeats_p05`
- Code: `src/proto_star/forecasters/nbeats_p05.py`, shared windowing in
  `src/proto_star/forecasters/_neural_common.py`, networks in
  `src/proto_star/forecasters/_neural_torch.py` (torch imported only when the forecaster runs)
- Config: `configs/agent_paper_neural.yaml` (variants `nbeats_generic`, `nbeats_interpretable`,
  `nbeats_hybrid`)
- Tests: `tests/test_forecasters_nbeats_p05.py`
- Leakage review: the forecaster sees only the fold's `train` frame (`annual_to_long` rejects
  later years); scaling statistics come from training years only; early stopping uses the
  last 7 years inside the training fold; the forecast input window ends at the cut-off.
  Seeds come from the config, and `torch.use_deterministic_algorithms(True)` with a fixed thread
  count makes a rebuild on the same machine identical.

## Our results

Same backtest origins as the baseline (ADR 0004). Raw score = the official score without the
floor at zero; skills in percent, all 7 forecast years. Means over origins, all / years 1–3 /
years 4–7: `current_best` 2.92 / 0.63 / 4.68, `ten_year_mean` 1.34 / −0.62 / 2.78.

| Variant | all | years 1–3 | years 4–7 | origins beating `current_best` (all / 4–7) |
|---|---|---|---|---|
| `nbeats_generic` (all metrics) | 2.32 | 0.52 | 3.39 | 1 / 1 |
| `nbeats_interpretable` (trend + generic, all metrics) | 2.25 | 0.92 | 3.04 | 0 / 0 |
| `nbeats_hybrid` (generic on temperature + CDD only) | 3.08 | 0.78 | 4.57 | 2 / 1 |
| `nbeats_hybrid_seed7` (same, other seed) | 2.88 | 1.23 | 4.03 | 1 / 1 |

Per origin, all years. Skills are for `nbeats_generic`; the hybrid has the same temperature/CDD
skill and 0 for precipitation and the hottest day.

| Origin | Score generic / interpretable / hybrid | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1980 | −0.64 / −0.88 / −0.74 | −2.53 | −3.43 | −0.06 | 0.46 | 0.48 |
| 1995 | 2.91 / 2.85 / 4.10 | 1.39 | 11.64 | −1.71 | −3.02 | 4.74 |
| 2011 | 4.69 / 4.77 / 5.87 | 5.16 | 9.27 | −3.91 | −0.83 | 14.22 |

Command, commit and run dir: `uv run proto-star climate-trial configs/agent_paper_neural.yaml
--record` (after `uv sync --extra hf`), base commit `e507f5e` plus this branch's new files,
master hash `99128065…bb04d1`, run dir `runs/trials/20261107-004902_paper_neural/` (not in the
repo). Write-up: `docs/trials/paper_neural.md`. The 9-forecaster trial took 28.6 min on 2 torch
threads; one fold of the 9-member ensemble on all metrics takes about 4 min (2011 fold).

## Takeaways

- N-BEATS beats `ten_year_mean` but not `current_best`. On all four metrics it loses on
  precipitation and the hottest day, where the 30-year mean is hard to beat.
- On temperature and CDD it helps CDD in years 4–7 (9.4 % skill vs 6.8 %) but hurts annual
  temperature (8.9 % vs 11.9 %). So the hybrid ends up just under `current_best` in years 4–7
  (4.57 vs 4.68), and the seed-7 replica is lower still (4.03): any edge is within seed noise.
- The interpretable (trend) variant is not better than the generic one. With a 7-year horizon a
  degree-2 trend mostly adds extrapolation risk.
- Status: adapted, not adopted. Possible next steps (not run): more seeds per member, a refit on
  all windows after early stopping, N-BEATS for CDD only, each judged on fresh seeds.
