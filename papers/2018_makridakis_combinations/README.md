# Forecast combinations: M4 (P16), the forecast combination puzzle (P17), combination review (P18)

| | |
|---|---|
| **Authors** | P16: Spyros Makridakis, Evangelos Spiliotis, Vassilios Assimakopoulos. P17: Jeremy Smith, Kenneth F. Wallis (original, not read); reviewed by Wei Qian, Craig A. Rolling, Gang Cheng, Yuhong Yang. P18: Xiaoqian Wang, Rob J Hyndman, Feng Li, Yanfei Kang |
| **Year / venue** | P16: 2018, International Journal of Forecasting 34(4), 802-808 (DOI 10.1016/j.ijforecast.2018.06.001). P17: Smith & Wallis 2009, venue TBD (not checked); Qian et al. 2015, arXiv preprint. P18: arXiv preprint 2022 (v2 23 Sep 2022), journal TBD |
| **Link** | P16: https://doi.org/10.1016/j.ijforecast.2018.06.001 (publisher page returned 403). P17: arXiv [1505.00475](https://arxiv.org/abs/1505.00475). P18: arXiv [2205.04216](https://arxiv.org/abs/2205.04216) |
| **Code released by authors** | none used |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p16-p17-combos` (no PR) |

## Summary

**P16 (M4).** Per docs/literature/README.md (the paper itself was not readable here): in the M4
competition, combinations of forecasts did well and pure machine-learning methods did poorly.
Detailed numbers from the paper: TBD (not read).

**P17 (forecast combination puzzle).** The simple average of candidate forecasts is often more
robust than combinations with estimated weights. Qian et al. (arXiv 1505.00475, abstract read)
review explanations such as estimation error in the weights, and separate "combining for
adaptation" (picking up the best member) from "combining for improvement" (exploiting diverse
errors). The Smith & Wallis 2009 original was not read.

**P18 (50-year review).** A survey of combination schemes from simple averages to estimated,
time-varying, nonlinear and cross-learned weights, for point and probabilistic forecasts.
Context only; no method from it was implemented beyond the ones above.

## Architecture

- Model family: forecast combination (no new model). Members are round-1 forecasters called
  through the registry: pooled ridge (P14), DeepAR (P08), hindcast-chosen EWMA (P04), ARIMA (P13),
  and the 10-year mean.
- Combiners: equal-weight mean (P16/P17), median, a trimmed mean, and Bates-Granger inverse-MSE
  weights from hindcasts inside each training fold (the P17 contrast).
- Per metric: CDD combines ridge, DeepAR, EWMA and ARIMA; temperature combines the 10-year mean,
  EWMA, DeepAR and ARIMA; precipitation and hottest day stay on `current_best`.
- Horizon: 7 years, the members' own direct or recursive forecasts.

## Results claimed by the authors

P16: TBD (paper not read). P17/P18: qualitative only (see summary). These are not our results.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | annual indices of 210 cities (≤ 2018) |
| Target(s) | `cdd` and `annual_avg_temp` combined; `total_precip_in`, `hottest_day_temp` on `current_best` |
| Horizon | 7 years (2019–2025) |
| Metric | relative MAE skill vs 30-year mean |

## Deviations

- Member sets were fixed by the round-1 summary (open question 2), not by a pool chosen in this paper's way.
- Trimmed mean: a symmetric trim of 4 members equals the median, so `trimmed` drops the single
  member farthest from the row median and averages the other three.
- Inverse-MSE weights use 2 in-train pseudo-origins (cut-off − 7, − 14) per fold, pooled over
  cities, one weight per member and metric. They are not time-varying.
- ARIMA `n_jobs` 3 instead of round 1's 5 (process count only; the forecasts matched round 1 exactly).

## Implementation

- Registry names: `forecast_combination`, `forecast_combination_torch` (same factory; the second pins torch for packages)
- Code: `src/proto_star/forecasters/combination_p16_p17.py`
- Config: `configs/agent_paper_combos_p16_p17.yaml`
- Tests: `tests/test_forecasters_combination_p16_p17.py`
- Analysis: `scripts/analyze_combos_p16_p17.py` → `docs/trials/combos_p16_p17_why.md`
- Leakage review: members only see the fold's `train` slice. Inverse-MSE weights come from
  pseudo-origins inside it, scored on years ≤ cut-off. A test checks that changing post-cut-off
  values does not change the forecasts, and another that the weights respond to training years.

## Our results

ADR 0004 folds, recorded at commit `b7d52b3` (clean tree): `docs/trials/combos_p16_p17.md`.
Command: `uv run proto-star climate-trial configs/agent_paper_combos_p16_p17.yaml --record`
(about 38 minutes). Master hash `99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1`.

Best fixed candidate (years 4–7) `combo_mean_cdd_only`, all-years raw score and skill (%). `hybrid_ridge_all_cdd` on the same rows: 0.24 / 4.13 / 6.44 (CDD skill 3.03 / 5.23 / 17.70).

| Origin | Score | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1980 | 0.16 | -2.53 | -2.06 | 0.00 | 0.00 | 2.69 |
| 1995 | 4.14 | 1.39 | 11.30 | 0.00 | 0.00 | 5.25 |
| 2011 | 6.18 | 5.16 | 8.05 | 0.00 | 0.00 | 16.66 |

Mean raw score (all / years 1–3 / years 4–7):

| Method | All | 1–3 | 4–7 | CDD skill 4–7 | Temp skill 4–7 |
|---|---|---|---|---|---|
| `hybrid_ridge_all_cdd` | 3.60 | 0.94 | 5.54 | 10.27 | 11.90 |
| `combo_mean_cdd_only` | 3.49 | 0.99 | 5.37 | 9.59 | 11.90 |
| `combo_mean_cdd_only_no_neural` | 3.51 | 1.04 | 5.36 | 9.55 | 11.90 |
| `combo_median_cdd_only` | 3.47 | 1.01 | 5.31 | 9.35 | 11.90 |
| `combo_inv_mse` | 3.48 | 1.51 | 4.92 | 9.59 | 10.07 |
| `combo_mean` | 3.47 | 1.51 | 4.91 | 9.59 | 10.06 |
| `combo_median` | 3.43 | 1.51 | 4.83 | 9.35 | 9.98 |
| `combo_trimmed` | 3.37 | 1.49 | 4.73 | 9.07 | 9.86 |
| `combo_mean_no_neural` | 3.34 | 1.59 | 4.63 | 9.55 | 8.96 |
| `current_best` | 2.92 | 0.63 | 4.68 | 6.84 | 11.90 |
| replica `combo_mean_cdd_only_seed7` | 3.45 | 0.95 | 5.33 | 9.44 | 11.90 |
| replica `combo_mean_seed7` | 3.39 | 1.49 | 4.80 | 9.44 | 9.74 |

## Takeaways

- Combining the CDD forecasts keeps most of the round-1 CDD gain without picking a winner (CDD
  skill 9.6 % vs 6.8 % for `current_best`, 3/3 origins in years 4–7), but it does not beat the
  pooled ridge alone (10.3 %). The ridge is clearly the best member, and the members' errors are
  0.94–0.99 correlated, so averaging pulls toward weaker members more than it cancels error.
- Combining temperature hurts in years 4–7 (10.1 % vs 11.9 %) and helps in years 1–3: EWMA and ARIMA are weak late.
- Without DeepAR, the CDD-only combo is unchanged (5.36 vs 5.37), so the neural member is not needed.
- Inverse-MSE weights scored like equal weights (4.92 vs 4.91): the combination puzzle in its benign form.
- Not adopted: `submit` stays `hybrid_ridge_all_cdd` (ADR 0005). Why-analysis: `docs/trials/combos_p16_p17_why.md`.
