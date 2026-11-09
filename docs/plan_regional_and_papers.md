# Plan: paper replications, the Coupled Regional Model, and external data

Team: **MKDir**. Version 2. This version fits the `proto-star-challenge` repo as of commit `aa8e869` and the challenge Space as of November 8.
Put this file at `docs/plan_regional_and_papers.md`. Claude Code reads it from there.

Deadline: Tuesday, November 10, 11:59 PM ET.

---

## 0. Rules

The repo rules apply first: `AGENTS.md`, `code/AGENTS.md`, `docs/honor_code.md`. This plan does not change them. If this plan conflicts with a repo rule, the repo rule wins. Stop and ask the human.

Rules that this plan depends on most:

1. Folds are fixed: cut-offs 1980, 1995, 2011, 7-year horizon (ADR 0004). Do not change them.
2. Use `scripts/robustness_origins.py` (7 cut-offs) only as a robustness check. Do not tune on it alone.
3. Give the most weight to `years_4_7`. It matches the Final Score.
4. Every forecaster is a function `forecaster(train, cutoff_year, forecast_years)`. It must compute everything from `train`. It must not read other files with weather data inside the function, except through a loader that applies `assert_weather_cutoff` with the fold cut-off.
5. One trial = one config in `configs/<initials>_<name>.yaml`. Run it with `uv run proto-star climate-trial <config> --record`.
6. Work on branches `agent/<topic>`. Do not commit, push, open PRs or submit unless the human asks.
7. uv only. Ask before you add a dependency, download more than 1 GB, or start a run longer than 15 minutes.
8. Do not use 2019-2025 weather data. Do not score variants on 2019-2025 to choose one.
9. Record every trial in `docs/trials/<name>.md`, failures included. Only the main session appends rows to `docs/experiments.md` (this prevents merge conflicts).

---

## 1. What the repo already shows

### 1.1 Current champion

`trend_level10_15_sensitivity` in `configs/lc_pooled_trend.yaml` (`src/proto_star/trend.py`):

| Metric | Method |
|---|---|
| annual_avg_temp | Mean of last 10 and 15 valid years + non-negative pooled 40-year slope |
| cdd | Same levels + pooled temperature slope x each city's CDD per degree |
| total_precip_in | 30-year mean |
| hottest_day_temp | 30-year mean |

Mean raw score on official folds: all years 4.14, years 1-3 0.33, years 4-7 6.92. `current_best` (old ensemble) has 0.63 in years 1-3. Thus the champion is weak in the early years.

Note: the mean (30-year) is the champion for precipitation and hottest day. CDD already uses the pooled trend. Check that this agrees with what the team means by "the mean wins for precipitation and CDD".

### 1.2 Already tried and rejected (from `docs/trials/pooled_trend_exploration.md`)

| Variant | Result | What this plan does with it |
|---|---|---|
| Free regional slopes in place of one national slope | 1.78 vs 2.30 (lost) | CRM must shrink regional slopes toward the national slope. Do not repeat free slopes. |
| 25% own-city slope | Lost | City slopes stay off. Use urban covariates instead (Section 5). |
| Level from current station only (temp, CDD) | No change | Do not repeat for temp and CDD. Test it for precipitation and hottest day only. |
| CDD from shifted daily temperatures (delta method) | Lost | Do not repeat. |
| Trend on hottest day or on all metrics | Lost | Hottest day keeps no trend unless a new model shows a gain. |
| 20, 40, 50-year means, 30-year median for precip and hottest day | No reliable gain | Do not repeat. |

### 1.3 Repo items this plan uses

- Regions: `proto_star.data.protostar.assign_region` gives 6 coordinate regions (Northwest, Southwest, North Central, South Central, Northeast, Southeast).
- Station joins: `city_info` and `station_metadata.py`.
- Daily data: `daily` table from `scripts/download_protostar_data.py`.
- torch is in the optional `hf` extra (`uv sync --extra hf`). xarray is in the `geo` extra.
- Open items in `docs/replication_order.md`: 3 (pooled median model), 7 (city plus regional trends), 8 (station segments, neighbor steps), 10 (GEV hottest day), 11 (equal-weight average), 12 (elevation, land cover, population groups). This plan covers 7, 8, 11 and 12.

### 1.4 What the challenge Space adds

From the Space code (`scoring.py`, `config.py`) and its About and Data tabs:

- Par is each city's 1989-2018 average. A city-metric needs 10 or more valid years in 1989-2018 to be scored (9 city-metrics, 63 rows are not scored). Predict all rows anyway.
- Practice-run CDD MAE with the official rule: 212 (30-year average) and 175 (trend). Differences under 10 F-days are noise.
- New subset `coverage_and_stations` (November 5): for each city and year, the days with both temperatures and the station the record comes from. Use it for the station-segment tests in 5.5.
- Judging weights: Reuse and Extensibility 25%, Interoperability 20%, Reproducibility 20%, Value 15%, Feedback 15%, Creativity 5%. The forecast Score counts only under Value and Creativity (20% together).
- Thus the method story and the README carry most of the grade. The CRM and the external data must be easy to reuse, and documented as such.
- The ProtoStar artifacts are the Lai and Dzombak records and their paper "Use of historical data to assess regional climate change" (J. Climate 32(14), 2019, doi 10.1175/JCLI-D-18-0630.1). That paper is a regional analysis. Present the CRM as a forecasting extension of it (Reuse criterion).
- The README needs an "AI Tools and Agents" section: tool, model, tasks, and what a person reviewed. Keep the agent instructions file in `code/`. The code must reproduce `submission.csv` without an agent.
- If the main finding is that reuse failed, the README can set "Negative result: yes". A "the papers do not transfer to observations only" result is a valid negative result for Phases 1A and 1B.
- CMU finalists present in person on Friday, November 13. Make figures that work on slides (regions map, interaction matrix, shrinkage plot).

---

## 2. Phase 0: main session, before any agent starts (about 1.5 h)

### 2.1 Checks

1. Run `uv sync` and `make check`. Paste the summary line.
2. Build the master table. Confirm the content hash in `docs/trials/pooled_trend.md`.
3. Run `uv run proto-star climate-trial configs/lc_pooled_trend.yaml`. Confirm 4.14 / 0.33 / 6.92.

### 2.2 One shared change: a plug-in point for new forecasters

Now each new model kind needs edits in `trial.py` (`TrialConfig`) and `backtest.py` (`resolve_forecaster`). Four agents that edit these two files in parallel will cause merge conflicts. Make one small change first, on branch `agent/forecaster-plugins`:

1. Add `src/proto_star/forecasters/__init__.py` with a registry: `name -> (SpecModel, build_function)`.
2. Add one optional field to `TrialConfig`: `models: dict[str, ModelEntry]`, where `ModelEntry = {kind: str, params: dict}`.
3. In `resolve_forecaster`, look up `models` entries in the registry. Validate `params` with the spec model of that `kind`.
4. Update `describe_forecaster` to use a `describe()` function from each spec.
5. Add tests. Existing configs must work with no change.
6. Ask the human to approve this change. It changes the config schema (a public interface in AGENTS.md).

After this change, each agent adds only: one module `src/proto_star/forecasters/<kind>.py`, one registry line, one test file, configs and a trial note.

### 2.3 ADR for the two papers

Both papers use CMIP output. The honor code puts such papers in the "Needs a ruling" group. Write a draft `docs/decisions/0005-paper-methods-on-observations.md`:

- Decision (proposed): we reuse the methods only. We train only on the challenge observations (and allowed external data up to 2018). We do not download or use CMIP data or any pretrained weights.
- Status: proposed. A human must accept it before agents A and B start.

---

## 3. Phase 1A: Luo et al. 2022, Bayesian deep learning with SVGD (agent A, branch `agent/luo-bdl`)

Paper: arXiv 2202.11244. Lowest priority. Do last if time is short.

### 3.1 The paper

- Data: CESM2 pre-industrial control North Atlantic SST (CMIP6). Not allowed for us.
- Preprocess: remove the mean and the seasonal cycle at each point.
- Problem: direct multi-step output (the next n_y states at once, not recursive).
- Model: DenseNet encoder-decoder, strided convolutions, no pooling, bilinear upsampling, optional fully connected bottleneck.
- Bayesian: SVGD, M = 20 particles, RBF kernel. Forecast = particle mean.
- Training: MSE, Adam lr 1e-3 with reduce-on-plateau, weight decay 5e-4, dropout 0.5, 1,280 samples.
- Result: BDL > deterministic DL > ConvLSTM > damped persistence.

### 3.2 Our version

1. Kind `luo_bdl`. Needs `uv sync --extra hf`. CPU only. Keep each fold under 2 minutes.
2. Target: the residual after the champion forecast. The network predicts only the anomaly from the champion. Add it back at the end. Thus the model cannot lose the trend.
3. Data: monthly anomalies from `daily` (monthly mean Tmax, Tmin, total precip per city), about 1,300 samples per fold. Aggregate to annual values. If the daily build is slow, use annual data and record the small sample.
4. Network: MLP over the 210-city vector (the paper's fully connected path). Optional: a coarse CONUS grid with a small conv encoder-decoder.
5. Input 12 or 24 months. Output 84 months, direct.
6. Bayesian: SVGD with 20 particles. Also a 20-member deep ensemble as a check.
7. Loss: MSE (paper), then L1 (our score).
8. Shrink: multiply the predicted anomaly by a factor in [0, 1]. Choose it on official folds. If the factor is 0, report that the model adds nothing.
9. Comparisons in the trial: champion, champion + AR(1) damped persistence, champion + deterministic DL, champion + BDL.

Expected result: little or no gain above the champion. The value is a clean replication and calibrated spread. Report it honestly.

---

## 4. Phase 1B: Fernandez and Barnes, ML model-analog (agent B, branch `agent/model-analog`)

Paper: arXiv 2502.17583. Second priority.

### 4.1 The paper

- Library: about 100,000 annual states from 29 CMIP6 models. Not allowed for us.
- Each state is baselined on its own 1961-1990 mean.
- A network learns a mask of weights. Input: two masked states. The weighted MSE between them goes to one linear node that predicts the target-region MSE L years later.
- Mask starts at all ones, relu, lr 0.001, batch 64, early stopping (patience 50, min change 0.005).
- Selection: the N library states with the lowest masked MSE to the current state. Their known future at lead L is the ensemble.
- Tethering: also match the 2 years before the start year, with smaller weights.
- Three masks compared: global (all equal), regional (target region only), learned.

### 4.2 Our version

1. Kind `model_analog`. Masks can be fit with numpy or scikit-learn (no torch needed). Use torch only if needed.
2. Library: observed years only, 1900 to (cutoff - L). A state = city anomalies for one year (210 cities x 4 metrics).
3. Anomaly of year Y = value(Y) minus the city's trailing 30-year mean that ends at Y.
4. Forecast at lead L: the champion forecast + the median over N analogs of their anomaly at Y + L. (Anomaly relative to the baseline at Y.) This keeps the champion trend.
5. Target regions: the 6 `assign_region` regions. One mask per (region, metric). Share across leads 3-7 if needed.
6. Grid in the config: N in {5, 10, 15, 20}, tether in {1, 2, 3}, mask in {global, regional, learned}.
7. Library size is about 80-110 years per fold. Report this limit.
8. Plot each learned mask on a map (`reports/figures/`, git-ignored). Judges value interpretability.

Expected result: a small gain in years 1-2 at most. The champion is weak there, so this is the target.

---

## 5. Phase 1C: the Coupled Regional Model, CRM (agent C, branch `agent/crm`)

First priority. This is the team's own framework.

### 5.1 Idea

Global pooled and city-local models are the two ends of one scale. K = 1 region is the pooled model. K = 210 regions is the local model. The CRM sits between them and starts at the pooled end. It moves toward regions only where the data shows signal.

The repo shows that free regional slopes lose. Thus the CRM never uses free regional slopes. It uses shrinkage toward the pooled model plus interaction terms.

### 5.2 Layer 1: regions

- Fixed: the 6 `assign_region` regions.
- Data-driven: spectral clustering of cities on the correlation of their detrended annual anomalies, plus a lat/lon distance term. K in {4, 5, 6}. Compute again in each fold from `train` only.

### 5.3 Layer 2: regional trends shrunk to the pooled trend

Start from `trend.py`. Keep its levels (mean of last 10 and 15 valid years) and its CDD sensitivity.

```
beta_final[r] = beta_pooled + k_r * (beta_regional[r] - beta_pooled)
k_r = tau^2 / (tau^2 + se_r^2)     # empirical Bayes, tau^2 from the spread of regional slopes
```

- `beta_pooled`: the existing non-negative pooled 40-year slope.
- `beta_regional[r]`: the same within-city slope, fit only on cities in region r.
- If `k_r` goes to 0, the CRM equals the champion. Report the fitted `k_r` per region and fold.
- Add a config switch `k_scale` in {0, 0.5, 1} to test less shrinkage.
- Precipitation and hottest day: keep the 30-year mean as default.

### 5.4 Layer 3: interaction variables

Let `z[t]` = detrended regional anomalies, K regions x 4 metrics (about 24 values per year). Detrend with Layer 2.

1. Sparse VAR: `z[t] = A z[t-1] + e`, fit with lasso (scikit-learn). Each entry of A is one interaction variable: how last year's metric n in region s changes this year's metric m in region r.
2. Forecast: `s[r,m,h] = (A^h z[cutoff])[r,m]`. It decays toward 0 with lead h. Add `s` to each city in the region.
3. Damping: multiply `s` by a factor in [0, 1]. Choose it on official folds.
4. This layer targets years 1-3, where the champion is weak (0.33 vs 0.63). Report years 1-3 and years 4-7 apart.
5. Optional: add 2018-only climate index values (ENSO, PDO, AMO) as start-state terms, if agent D delivers them (Section 6).

### 5.5 Precipitation and hottest day tests (not tried yet in the repo)

1. Mean from the current station segment only, if 15 or more valid years remain. Else fall back to the 30-year mean. Get the station per year from `coverage_and_stations`.
2. Regional pooling of the level: shrink the city's 30-year mean toward a regional anomaly-adjusted mean (empirical Bayes). This helps cities with many invalid years.
3. Gate: keep a change for a metric only if it beats the champion on 2 or 3 official folds and on the 7-cut-off check.

### 5.6 Trial configs and ablation

Make `configs/<initials>_crm.yaml` with these forecasters:

| Row | Forecaster |
|---|---|
| 1 | `thirty_year_mean` (reference) |
| 2 | `current_best` |
| 3 | `trend_level10_15_sensitivity` (champion) |
| 4 | CRM layer 2, fixed regions |
| 5 | CRM layer 2, data-driven regions |
| 6 | Row 4 or 5 (better one) + VAR interactions |
| 7 | Row 6 + precip/hottest-day tests from 5.5 |
| 8 | Row 7 + urban covariates (from agent D, if ready) |

Then run `scripts/robustness_origins.py` on the same config.

### 5.7 README sentence for judges

"Pooled and local models are two ends of one scale. Our Coupled Regional Model sets its position on that scale by shrinkage, and links regions through sparse interaction terms."

---

## 6. Phase 1D: external data (agent D, branch `agent/external-data`)

Rules for this agent:

- Raw downloads go in `data/external/` (immutable). Transforms go in `data/interim/` or `data/processed/`.
- One loader per source in `src/proto_star/data/external/`. Weather sources pass `assert_weather_cutoff`.
- Document each source in `docs/data.md`: source, license, schema, years, download command, and the use test result.
- Ask before downloads larger than 1 GB (NLCD national files are large: use a per-point or per-county extract).
- The use test: "Would this 2019-2025 series be different in a hotter or wetter year?" If yes, it is not a forecast input.

### 6.1 Sources, ranked

| Rank | Source | Years | Responds to weather? | Use |
|---|---|---|---|---|
| 1 | Census population per county or place (decennial, ACS) | any | no | Urban growth per city. CRM covariate: city slope offset `gamma * urban_growth`, with one pooled `gamma`. Replication order item 12, P24. |
| 2 | NLCD impervious surface and tree canopy, buffers 1, 5, 10 km around each station | any | no | Same as rank 1. |
| 3 | Elevation and distance to coast (GHCN station metadata already has elevation) | static | no | Clustering features. |
| 4 | Climate indices ONI, PDO, AMO, NAO (NOAA PSL, CPC) | up to 2018-12 | yes, so cap at 2018 | CRM Layer 3 start state. Analog states. |
| 5 | GHCN-Daily neighbor stations within 100 km | up to 2018-12-31 | yes, so cap at 2018 | Neighbor station-step estimates (replication order item 8, P15). |
| 6 | ERSSTv5 SST grid | up to 2018-12 | yes, so cap at 2018 | Optional analog precursors. Needs the `geo` extra. |

Urban covariate timing: use the population change up to the cut-off year for backtest folds (for example 1970 to 1980 census for the 1980 fold). For the final forecast, census 2020 is allowed (it does not respond to the weather), but use the same rule as the folds for consistency.

### 6.2 Needs a ruling (do not use)

- CO2 or forcing after 2018: it responds a little to ENSO.
- Solar cycle, volcanic eruptions after 2018: look allowed. Very small expected gain.
- ENSO forecasts issued in 2018: climate model output. Same status as CMIP.

### 6.3 Not allowed as forecast inputs

All 2019-2025 weather, home runs per game, streamflow, ozone days, bloom dates, West Nile cases, electricity demand, "AC repair" searches. These are allowed in the analysis and policy idea only. Mark them "Analysis only" in the data card.

### 6.4 Outputs

- `data/processed/external/city_static.parquet`: one row per city.
- `data/processed/external/indices_to_2018.parquet`.
- Tests with tiny synthetic data, plus a leak test for each weather source.

---

## 7. Phase 2: combine and choose (main session, about 2 h)

1. Merge agent branches into one integration branch (with human approval).
2. Append each trial to `docs/experiments.md`, failures included.
3. Make `configs/<initials>_final.yaml` with the champion, the best CRM row, the best analog, the best BDL, and an equal-weight average of the best 2 or 3 (replication order item 11, P17). Equal weights first: estimated weights overfit with 3 folds.
4. Choose per metric. Keep the champion for a metric unless a new model wins on 2 or 3 official folds in `years_4_7` and on the 7-cut-off check.
5. Set `submit:` from these results only.

## 8. Phase 3: package (main session, about 1 h)

1. `uv run proto-star climate-package configs/<initials>_final.yaml`.
2. Fill the `TODO before upload` items. Team name: MKDir. Write the README to the judging rubric:

| Criterion (weight) | README content |
|---|---|
| Reuse and Extensibility (25%) | CRM as an extension of Lai and Dzombak 2019. Paper replications and what changed. How another team runs the CRM on new cities (one config, one function). |
| Interoperability (20%) | Census, NLCD, GHCN and index sources joined by station ID and coordinates. Standard formats (parquet, CSV). The plug-in forecaster registry. |
| Reproducibility (20%) | `python code/reproduce.py`, master hash, trial notes, commit hash. |
| Value (15%) | Score, ablation table, policy idea. |
| Feedback (15%) | See item 3. |
| Creativity (5%) | The pooled-to-local scale and the interaction layer. |

3. Feedback to the Ecosystem: both papers depend on CMIP libraries, which the team rule blocks. Write what an observation-only version can and cannot do. Add station-change friction and any data-access problems agent D found.
4. AI Tools and Agents section: Claude Code, the model, each agent's task, and what a person reviewed. Copy `AGENTS.md` and `code/AGENTS.md` into `code/`.
5. A person uploads and submits.

---

## 9. Schedule and agents

| Step | Who | Branch | Starts after | Time box |
|---|---|---|---|---|
| Phase 0 checks, plug-in point, ADR 0005 draft | main session | `agent/forecaster-plugins` | now | 1.5 h |
| 1C CRM | agent C | `agent/crm` | Phase 0 | 6 h |
| 1D external data | agent D | `agent/external-data` | Phase 0 | 4 h |
| 1B model-analog | agent B | `agent/model-analog` | Phase 0 + ADR accepted | 5 h |
| 1A Luo BDL | agent A | `agent/luo-bdl` | Phase 0 + ADR accepted | 5 h |
| Phase 2 | main session | integration branch | 1A-1D | 2 h |
| Phase 3 | main session | integration branch | Phase 2 | 1 h |

Each agent must: branch from `agent/forecaster-plugins`, use worktrees, add only its own module, configs, tests and trial note, pass `make check`, and stop at its time box with a report.

---

## 10. Kickoff prompt for Claude Code

```
Read AGENTS.md, code/AGENTS.md, docs/honor_code.md, then docs/plan_regional_and_papers.md.
Repo rules win over the plan. Stop and ask if they conflict.

1. Do Phase 0 yourself. Report the make check line, the master hash, and the champion scores.
2. Show me the plug-in change (Section 2.2) and the ADR 0005 draft. Wait for my approval.
3. Then start agents C and D in separate worktrees. Start A and B after I accept ADR 0005.
   Give each agent Section 0, Section 1, its own section, and Section 9.
4. When the agents report, do Phase 2. Show me the per-metric choice table. Wait for approval.
5. Do Phase 3. Do not commit, push, upload or submit unless I say so.
No weather data after 2018-12-31. No forecast values from an LLM.
```

---

## 11. Open questions for the team

1. Does "the mean wins for CDD" mean the 30-year mean, or the current pooled-trend CDD? The repo shows the pooled trend with sensitivity wins for CDD.
2. Accept ADR 0005 (methods only, observations only) for both papers?
3. Approve the plug-in change to the config schema?
4. Use climate indices (capped at 2018) and census/NLCD data?
