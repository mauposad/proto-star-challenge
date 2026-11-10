# Research background: ProtoStar climate forecast (2019–2025)

## Question

Which forecasting methods, which are falsifiable and testable on historical backtests, can raise
the official relative-skill score for annual city-level climate forecasts for 2019–2025? Only
data through 2018 may be used.

## Setting

- **Challenge:** CMU OSPO × Hugging Face ProtoStar, track "Climate Risk Intelligence".
  Submission deadline: 2026-11-10 23:59 America/New_York.
- **Data:** 210 U.S. cities. The stations are mostly airports, from the Lai & Dzombak records
  (Hugging Face dataset `CMU-OSPO/protostar-climate-train-to-2018`, CC0). Observations end on
  2018-12-31. The tables are:
  - `annual_indices`: one row per city-year, 1851–2018, with `Avg Temp`, `Max Tmax`,
    `ToT Prcp`, `cdd`, many other indices, and per-variable missing-day counts.
  - `daily`: about 10M rows of tmax/tmin (°F) and prcp (in).
  - `coverage_and_stations`: days observed, station segment, and station changes per year.
  - `city_info`: lat/lon and station threads.

  The team's cleaned table is `data/processed/protostar/annual_master.parquet`: 28,052 rows,
  37 columns, with `valid_*` flags, `Station Segment`, `years_since_switch`, `region` and
  daily-quality flag counts. Schema and known issues are in
  `/Users/atabaresa/repos-new/proto-star-challenge/docs/data.md`.
- **Targets:** four per city and year:
  - `annual_avg_temp` (°F)
  - `total_precip_in` (inches)
  - `hottest_day_temp` (°F, the annual max of daily Tmax)
  - `cdd` (cooling degree days, °F-days)

  A value is scored only if its metric's missing-day columns are each ≤ 10.
- **Official metric:**
  - For each metric, skill = 1 − MAE(model) / MAE(reference), where the reference is each
    city's mean over the 30 calendar years ending at the cut-off (1989–2018 for the real
    forecast).
  - Score = 100 × max(0, mean of the 4 skills).
  - The live board scores 2019–2021. After the deadline the final board pools 2019–2025, and a
    separate final score covers 2022–2025.
- **Validation (fixed, ADR 0004):**
  - Rolling origins with cut-offs 1980, 1995 and 2011, each forecasting 7 years.
  - Results are reported for all years, lead years 1–3 (like the live board) and lead years
    4–7 (like the final score).
  - Each method is compared using `raw_score`, the official score without the zero floor.
  - A 7-origin robustness check (adding 1985, 1990, 2000, 2005) is a secondary diagnostic only.

## What is known (team backtests, mean raw score over the 3 folds: all / years 1–3 / years 4–7)

- **Baselines:**
  - `thirty_year_mean` (the reference): 0 / 0 / 0.
  - `ten_year_mean`: 1.34 / −0.62 / 2.78.
  - `fifteen_year_mean`: 0.88 / 0.10 / 1.49.
  - Medians of the 10-, 15- and 30-year windows are all below their means.
  - `linear_trend` (per-city OLS over 30 years): −12.76.
  - `hinge_fit` (per-city flat-then-ramp): −19.83.
- **Per-metric ensemble `current_best`:** 10-year mean for temperature and CDD, 30-year mean for
  precipitation and hottest day. Scores 2.92 / 0.63 / 4.68.
- **Pooled trend (current submission candidate):**
  - Method: each city's recent level (mean of the last 10 and last 15 valid years, averaged),
    plus one within-city least-squares warming slope pooled across all cities over a 40-year
    window and floored at 0.
  - For CDD, the slope = pooled temperature slope × the city's own CDD-per-degree regression
    coefficient.
  - Precipitation and hottest day stay on the 30-year mean.
  - Scores 4.14 / 0.33 / 6.92. Per-metric skill in years 4–7: temperature 17.73%, CDD 9.94%,
    precipitation 0, hottest day 0.
- **The score comes from two metrics only.** The whole current score is (temp skill + CDD
  skill) / 4. Precipitation and hottest day contribute nothing.
- **Weak early years.** Temperature skill in lead years 1–3 is negative (about −1.6% to −2.8%)
  for every recent-level method.
- **Gain concentrated after 2000.** The 1980 fold is negative for most recent-window methods,
  because of mid-century cooling.
- **Variants tried and rejected:** about 40 variants were compared on the same folds, so small
  gaps are noise:
  - level windows of 5, 10 and 15 years; trend windows of 30, 40 and 50 years;
  - 25% own-city slope; regional slopes instead of a national one; slope × 1.5;
  - trend added to the hottest day, or to all four metrics;
  - CDD recomputed from daily temperatures shifted by the trend (delta method), alone or blended;
  - level from the current station segment only;
  - for precipitation and hottest day: 20-, 40- and 50-year means and the 30-year median.

  The 40-year precipitation mean helped on the official folds but not over 7 origins.
- **Station switches** shift temperature metrics by about 0.5 °F on average. 30 cities switch
  station within 1989–2018. Partially missing years read low until screened.
- **Practice-run fact from the organizers:** temperature and CDD carry the signal.
  Precipitation and hottest day are mostly noise.

## What is open

- How to gain skill on precipitation and hottest day, which carry half the score's weight,
  given that window means near the 30-year average are hard to beat.
- How to avoid losing skill in lead years 1–3 while keeping the trend gain in years 4–7.
- Whether learned combinations or damping would beat the hand-set pooled trend under MAE.
  Equally open: whether station artifacts, missing-day bias, the daily distribution, or
  geography carry exploitable signal.
- Whether anything beats the pooled trend on more than one of the three folds.

## Constraints

- **Honor code (hard):**
  - Use no data after 2018-12-31 and no 2019–2025 weather or weather-responsive data
    (streamflow, energy, air quality).
  - Use no pretrained weights trained on post-2018 data; train from scratch.
  - Do not download the original source records, which run past 2018.
  - No LLM may produce or correct forecast values.
  - Never tune or select using leaderboard scores or knowledge of 2019–2025. Every choice must
    be justified by backtests on data through 2018.
  - Static, non-weather data (for example elevation from the NOAA station inventory) is allowed
    if documented.
- **Leakage:** anything fitted (levels, slopes, climatologies, models) must be computed inside
  each fold from rows at or before that fold's cut-off.
- **Compute and time:**
  - One laptop; the existing Python stack (numpy, pandas, scikit-learn). New dependencies need
    human approval.
  - Each hypothesis must be implementable and backtested within about 1–2 hours using the
    existing harness `proto_star.backtest.compare_forecasters`.
  - The deadline is about 24 hours away.
- **Validation is fixed:** the folds, horizon and metric cannot be changed to raise a score.
