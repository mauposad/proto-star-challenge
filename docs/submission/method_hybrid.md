**In one sentence:** each city's recent level plus one warming trend shared by all 210 cities,
with cooling degree days (CDD) averaged from two different models.

| Metric | Forecast |
|---|---|
| Average temperature | **Pooled trend.** The mean of each city's last 10 and last 15 valid years, plus one warming slope fitted across all cities over 1979-2018 (+0.050 °F per year), extended from the middle of those years to each forecast year |
| CDD | **Average of two models.** (1) The pooled trend, with each city's slope = the shared warming slope x that city's own CDD gained per degree (a hot city gains far more CDD from one degree than a cool one). (2) A pooled ridge regression fitted across all cities, one model per forecast year, on each city's normalized lags, trailing means, latitude, longitude and region (Montero-Manso & Hyndman 2021; built by Mauricio Posadas, team ADR 0005) |
| Precipitation, hottest day | **30-year mean** (1989-2018). Nothing we tried beat it reliably |

**Why these choices.** A trend fitted to one city is mostly year-to-year noise; one slope shared
by all cities keeps the signal. The two CDD models are built in very different ways, and each won
on different cut-offs, so their average beats either one. Every choice was made from backtests
on data through 2018: seven-year forecasts from 1980, 1995 and 2011, scored with the challenge's
own skill formula. The candidates and the rule for choosing were written into `code/trial.yaml`
before any of them was run, and the leaderboard was never used to choose.

**What did not work** (all in `code/evidence/`): regional slopes, a 1.5x slope multiplier,
trends on precipitation or hottest day, a hottest-day trend scaled by each city's sensitivity,
recomputing CDD from shifted daily temperatures, and levels from the current station only.

**Disclosure.** The shared slope is not allowed to go negative. We added that rule after seeing
the first version fail at the 1980 cut-off, where mid-century cooling makes the 40-year slope
negative, so the 1980 result is not an independent test of it. It does not change these
forecasts: the slope through 2018 is positive. About 40 variants were compared over the project,
so small differences between them are noise; the well-supported gain is a shared trend against
none.

**Expected behavior.** The gain is largest in forecast years 4-7, the Final Score window. In
years 1-3, the Live Score window, it is small.
