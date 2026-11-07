# Live leaderboard snapshot, 2026-11-07

The challenge Space (`CMU-OSPO/protostar-challenge-climate-risk-intelligence`) was read on
2026-11-07 through its public `load_board` endpoint. The board says it was last updated on
Nov 7 at 13:26 ET. MKDir has one scored submission, `current_best`, from
[`MekkoMau/protostar-climate-MKDir@a008301`](https://huggingface.co/datasets/MekkoMau/protostar-climate-MKDir/commit/a008301729a3d6f016b2f0a1779ef1c3e3e1332b).

## How the Space scores (from its `scoring.py`, `config.py` and `leaderboard.py`)

- `MAE_m` is the mean absolute error per metric over the scored rows of a split.
- `S_m = 1 − MAE_m / MAE_ref,m`, where the reference is the 30-year average baseline.
- `Score = 100 × max(0, mean of the four S_m)`. This is our backtest `raw_score` with the floor.
- **Live split = 2019–2021**, forecast years 1–3 of our 7-year horizon. This is the board shown now.
- **Final split = 2022–2025**, forecast years 4–7. It is hidden until the deadline
  (2026-11-10 23:59 ET) and is the one that counts.
- **Only the team's latest submission counts**, on both splits. Each new submission replaces the
  previous one. The limit is 10 valid submissions per team per UTC day.

## Board (live split, 2019–2021)

| Rank | Team | Score | Temp MAE °F | Precip MAE in | Hottest day MAE °F | CDD MAE |
|---|---|---|---|---|---|---|
| 1 | PstarAlu (CMU) | 16.0 | 0.990 | 5.962 | 2.181 | 136.8 |
| 2 | TROUBLESHOOTERS (CMU) | 15.9 | 0.981 | 5.824 | 2.233 | 138.4 |
| 3 | GuaGuaBear (CMU) | 15.5 | 1.006 | 5.831 | 2.172 | 143.6 |
| 4 | Ashley boys | 14.9 | 1.026 | 5.987 | 2.173 | 140.8 |
| 5 | Team Tatakae | 14.4 | 1.061 | 5.987 | 2.173 | 140.2 |
| 6 | Evanguo12 | 13.8 | 1.080 | 5.993 | 2.174 | 142.0 |
| 7 | Team Hurricane (CMU) | 13.6 | 1.045 | 6.091 | 2.198 | 142.6 |
| 8 | LEGENDS OF THE FALL | 13.1 | 1.156 | 5.830 | 2.200 | 140.1 |
| 9 | GW OSPO | 12.8 | 1.098 | 5.975 | 2.177 | 147.3 |
| 10 | Zhoey | 12.8 | 1.106 | 5.987 | 2.173 | 146.2 |
| **11** | **MKDir (CMU)** | **11.0** | **1.190** | **5.987** | **2.173** | **149.6** |
| 12 | Ocarina of Ten (reference: 10-year mean, example notebook) | 10.4 | 1.191 | 5.782 | 2.295 | 149.6 |
| – | Linear trend (baseline) | 9.6 | 1.095 | 6.122 | 2.413 | 147.4 |
| – | 30-year average (baseline, the reference) | 0.0 | 1.477 | 5.987 | 2.176 | 198.0 |
| – | Last year repeated (baseline) | 0.0 | 1.146 | 8.466 | 2.751 | 175.8 |

## Our score, metric by metric

Skill against the reference MAEs above:

| Metric | MKDir skill | Leader (PstarAlu) skill | Points of the 5.0 gap |
|---|---|---|---|
| Avg temperature | +0.194 | +0.330 | **3.4** |
| Precipitation | 0.000 | +0.004 | 0.1 |
| Hottest day | +0.001 | −0.002 | −0.1 |
| CDD | +0.244 | +0.309 | **1.6** |
| **Score** | **11.0** | **16.0** | 5.0 |

(Points = skill difference / 4 × 100.) The numbers check out against our method:

- Temperature and CDD match the 10-year-mean reference team (1.190 vs 1.191; 149.6 vs 149.6).
- Precipitation equals the 30-year baseline exactly (5.987), which is what we submitted. Hottest
  day is 2.173 vs 2.176, a small difference from the ADR 0003 calendar window.
- We beat the 10-year-mean reference only because we used the 30-year mean for hottest day.

## What this tells us, and what it does not

**Honor code first.** The live board is knowledge of how 2019–2021 turned out.
[honor_code.md](../honor_code.md) forbids tuning a method on it, and AGENTS.md forbids selecting
models on leaderboard scores. Below, the board is used only to ask questions. Each one has to be
answered by a backtest on data through 2018, on the ADR 0004 folds, before it changes what we
submit. The candidate in [ADR 0005](../decisions/0005-submit-pooled-ridge-cdd.md) was chosen
before we saw these numbers.

It is also a small sample: 3 years × 210 cities, with errors that move together across cities
(one warm year shifts everyone). It covers years 1–3; the Final Score covers years 4–7.

### Observations

1. **About two thirds of our gap to the leaders is temperature.** Every team above us has a
   lower temperature MAE (0.98–1.16 vs 1.19). Even the linear-trend baseline (1.095) beats our
   10-year mean on temperature, although it loses overall because it does badly on
   precipitation and hottest day.
2. **About one third is CDD.** The leaders are at 137–144 against our 150.
3. **Precipitation and hottest day barely separate anyone.** Every team is within ±0.03 skill
   of the 30-year mean on both. Four teams submitted exactly the reference value for both, as
   we did. This is the same conclusion as round 1, finding 3.

### Effect on each research track

| Track | Round 1 conclusion | What the live board suggests (hypothesis only) |
|---|---|---|
| Pooled global model (P09/P14) | Best CDD method, beats `current_best` at 3/3 origins in years 4–7 | Supports it: CDD is a third of the gap. Pooled models shrank **temperature** toward the 30-year level, so keeping them to CDD looks right. |
| Climate normals (P02–P04) | OCN/EWMA lose in years 4–7 | In our backtest, `ewma_opt_o8` (1.75), `ewma_opt` (1.69) and `optimal_o8` (1.43) beat `current_best` (0.63) in **years 1–3**. Shorter or adaptive windows may help near-term temperature, so the live board does not contradict this track. Its open question is years 4–7. |
| GEV for hottest day (P23) | Ties the 30-year mean | Hottest day is worth about 0 points for every team. Deprioritize. |
| ARIMA (P13) | Drift extrapolates badly, except CDD at 1/3 origins | `arima_temp_cdd` scored 1.11 in years 1–3, against 0.63 for `current_best`. Temperature-only drift, damped and checked at 1980 as well as 2011, is worth a second look. |
| Neural (P05/P08) | `deepar_hybrid` edged temperature in years 4–7, within seed noise | Temperature is the main lever, so the planned 5–10 seed rerun is worth more than before. CI determinism is still untested. |
| Baselines / trend | Trends lose at every fold mean | The 3-fold mean is pulled down by the 1980 cut-off, where warming had paused. At 2011, the fold closest to the present, `linear_trend` improved temperature and CDD (experiments log, 2026-11-06). The equal-weight mean may undervalue methods that follow recent warming. |

### What this changes in our approach

1. **The fold design is now the main open question.** ADR 0004 weights 1980, 1995 and 2011
   equally. A method that follows warming loses at 1980 and wins at 2011. Proposal for the team:
   report per-fold scores alongside the mean and, if the team agrees, add more recent cut-offs
   (for example 2004 and 2008). Changing the validation scheme needs a new ADR and human
   approval. It must be argued from pre-2019 data (how stable warming rates were across eras),
   not from this board.
2. **Temperature gets the next round of effort.** The tests to run, all on the ADR 0004 folds:
   a damped or shrunk trend on temperature only; a short-window or EWMA temperature normal with
   the window fixed in advance; the DeepAR temperature seed study.
3. **CDD: go ahead with the pooled ridge** ([ADR 0005](../decisions/0005-submit-pooled-ridge-cdd.md)),
   then the fixed equal-weight CDD combination (P16/P17).
4. **Stop new work on precipitation and hottest day.** There is at most about 0.7 points
   available on the live board and none in our backtests.
