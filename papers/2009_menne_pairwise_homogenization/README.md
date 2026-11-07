# Homogenization of temperature series via pairwise comparisons (P15)

| | |
|---|---|
| **Authors** | Matthew J. Menne, Claude N. Williams Jr. |
| **Year / venue** | 2009, Journal of Climate (volume and pages: TBD, not checked) |
| **Link** | DOI [10.1175/2008JCLI2263.1](https://doi.org/10.1175/2008JCLI2263.1) |
| **Code released by authors** | NOAA's pairwise homogenization algorithm (PHA) software exists; not used or read here (URL and license TBD). Our Python is written from scratch |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p15-station` (no PR) |

## Summary

Station records carry artificial jumps from station moves, instrument changes and changes in
observing time. They are hard to tell apart from real climate change in a single series. The
paper's idea is to compare each station with many neighbors: in the difference series
(target minus neighbor), the shared regional climate cancels and a step that shows up in all
pairs involving one station can be attributed to that station. Change points are found in
the pairwise difference series, attributed to the station that is common to the pairs, and
the size of each adjustment is estimated from several pairs. The algorithm is the one used
to homogenize the U.S. Historical Climatology Network (USHCN) version 2 temperatures.

## Architecture

- Model family: statistical homogenization (change-point detection plus step adjustment).
- Inputs: monthly temperature series of a target station and its correlated neighbors, plus
  station history metadata where available.
- Outputs: an adjusted (homogenized) series, in the frame of the most recent station.
- Procedure (as we understand it from the abstract and the standard description): detect
  change points in many pairwise difference series (SNHT-type tests), attribute each to one
  station, estimate each step from multiple pairs, and adjust the earlier segments.
- Key hyperparameters as reported: TBD (the full text was not read).

## Results claimed by the authors

TBD: the full text was not read for this replication, so no numbers are copied here.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | annual city values from the master table (≤ cut-off), `Station Segment` / `Station Changes` from `coverage_and_stations` |
| Target(s) | the homogenized series is not a forecast; we take the `current_best` window mean (10 years for `annual_avg_temp`/`cdd`, 30 years for `total_precip_in`/`hottest_day_temp`) of the adjusted series |
| Horizon | 7 years (folds 1980, 1995, 2011; real forecast 2019–2025) |
| Metric | relative MAE skill vs the 30-year mean |

## Deviations

- Break dates come from our station metadata (first year of a new `Station Segment`), not from
  a statistical change-point search. Undocumented breaks are not looked for.
- One step per documented switch: mean of the city-minus-neighbor difference after the switch
  minus the mean before it, over ±5 or ±10 years. Years flagged with a switch are mixed and
  are left out. The paper estimates steps from several pairwise series; we compare the city with
  the mean anomaly of its neighbors.
- Neighbors: the 5 or 10 nearest cities (great-circle, within 1,000 km) with no switch of their
  own in the same span. The paper selects neighbors by correlation.
- Annual instead of monthly values. One additive step for every metric, including precipitation
  and CDD (CDD and precipitation clipped at 0).
- Only switches inside the averaging window are adjusted; earlier ones cannot change the mean.
- Optional significance gate `min_t` (|step| / standard error), a simple stand-in for the paper's
  tests.
- The "segment" variants are not from the paper: they drop the old-station years instead of
  adjusting them (replication step 8, first half).

## Implementation

- Registry name: `station_p15`
- Code: `src/proto_star/forecasters/station_p15.py`
- Config: `configs/agent_paper_station_p15.yaml`
- Tests: `tests/test_forecasters_station_p15.py`
- Why analysis: `scripts/analyze_station_p15.py` → `docs/trials/station_p15_why.md`
- Leakage review: every quantity comes from the fold's `train` frame (years ≤ cut-off), for the
  city and its neighbors alike. The after-switch side of a step stops at the cut-off, and a
  switch with fewer than 3 clean years on either side is not adjusted. A test changes all
  post-cut-off values and adds a neighbor switch after the cut-off; forecasts stay identical.

## Our results

Same backtest origins as the baseline, raw score over all 7 forecast years, per-metric skill in
percent. Best P15-only variant `adj_temp_cdd_k10_w10` (`current_best` for precipitation and
hottest day):

| Origin | Score | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1980 | -0.57 | -2.53 | -1.80 | 0.00 | 0.00 | -0.50 |
| 1995 | 3.60 | 1.39 | 11.42 | 0.00 | 0.00 | 2.97 |
| 2011 | 5.95 | 5.16 | 8.06 | 0.00 | 0.00 | 15.74 |

Mean raw score (all / years 1–3 / years 4–7):

| Method | All | Years 1–3 | Years 4–7 |
|---|---|---|---|
| `adj_temp_k5_w5_ridge_cdd` (adjusted temperature + pooled ridge CDD) | 3.61 | 0.97 | 5.53 |
| `hybrid_ridge_all_cdd` (submitted, ADR 0005) | 3.60 | 0.94 | 5.54 |
| `seg_temp_cdd_min3` | 3.01 | 0.73 | 4.77 |
| `adj_temp_cdd_k10_w10` | 2.99 | 0.71 | 4.75 |
| `current_best` | 2.92 | 0.63 | 4.68 |

Command, commit and run dir: `uv run proto-star climate-trial configs/agent_paper_station_p15.yaml --record`;
the commit is in `docs/trials/station_p15.md`; run dir `runs/trials/<stamp>_station_p15/` (git-ignored).

## Takeaways

- Station switches inside the averaging window are rare: 39 of 630 city-origins for the 10-year
  window, and a step could be estimated at fewer than half of them.
- Where they occur, adjusting or dropping the old segment helps slightly on average
  (+0.07 to +0.09 raw points over `current_best`), mostly from one city (McCook). The gain does
  not grow with the size of the estimated step, so the mechanism check is only partly supported.
- On top of the submitted pooled ridge CDD it is a wash (5.53 vs 5.54 in years 4–7). Not adopted;
  `submit` stays `hybrid_ridge_all_cdd`. Keep the station tooling for diagnostics.
