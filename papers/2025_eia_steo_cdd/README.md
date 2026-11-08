# CDD forecasts: EIA STEO weather model (P06) and CDD recomputed from shifted daily data (step 9)

| | |
|---|---|
| **Authors** | U.S. Energy Information Administration (EIA). Step 9 is our replication-plan item, not a paper |
| **Year / venue** | EIA handbook "Short-Term Energy Outlook: Weather Forecast", last updated October 2025 (method note, not peer reviewed) |
| **Link** | https://www.eia.gov/analysis/handbook/pdf/STEO%20Weather%20Model.pdf |
| **Code released by authors** | none |
| **PDF in repo?** | no |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p06-p21-cdd-forcing` (no PR) |

## Summary

**P06.** EIA's Short-Term Energy Outlook forecasts population-weighted heating and cooling
degree days for the nine Census divisions. Degree days use the daily mean `(high + low) / 2`
against a 65 °F base, summed over the period. For the current month EIA uses NOAA data and
forecasts. For the rest of the horizon it fits, per state, a one-variable OLS 30-year trend
line to the previous 30 years of annual HDD and CDD, uses it for annual forecasts, splits them
into months with 30-year seasonal factors, and weights states by population forecasts. The
equation itself is an image in the PDF and was not readable; the text says "a one-variable
30-year trend line ... estimated using the previous 30 years".

**Step 9** (docs/replication_order.md). CDD is a convex function of daily temperature, so a mean
of past CDD should understate CDD after warming. Take a recent daily climatology, shift every
day by a forecast temperature anomaly, and recompute CDD.

## Architecture

- Statistical, per city. No fitting beyond OLS.
- `eia_trend30` (faithful P06): OLS line through the last 30 calendar years of a city's CDD,
  extrapolated (the built-in `linear_trend` baseline, used for CDD only).
- `cdd_on_temp_p06` (the brief's version of P06): per city, OLS of annual CDD on annual mean
  temperature over the last 30 valid years, evaluated at a temperature forecast (10-year mean,
  or the 10-year mean plus half the 30-year slope carried to the target year).
- `cdd_daily_shift` (step 9): daily Tmean of each city's last N valid years (N = 10 or 30),
  shifted by `T_hat(year) - T_clim`, CDD recomputed as the sum of `max(0, Tmean - 65)` divided
  by N. The definition matches the challenge's `cdd` column exactly (checked on real data,
  max difference 5e-5 °F-days). `mode: linear` is the first-order version (same level shift,
  no convexity), used as an ablation. `T_hat` = 10-year mean, shrunk trend, or the P21 CO2
  model; a variant averages the CDD with the pooled ridge (`hybrid_ridge_all_cdd`).
- Output: CDD only; `current_best` for temperature, precipitation and hottest day.

## Results claimed by the authors

None: the EIA note reports no skill numbers.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | daily `tmax`/`tmin` from `daily.parquet` and the annual master, both ≤ each fold's cut-off |
| Target(s) | `cdd` only |
| Horizon | 7 years (2019–2025); EIA's is 13–24 months |
| Metric | relative MAE skill vs 30-year mean |

## Deviations

- EIA works per state with population weights and NOAA short-range forecasts. We work per city,
  unweighted, with no external forecast.
- The CDD-on-temperature regression is not in the EIA note. It is the version the team brief
  asked for, and we label it as an adaptation.
- Step 9 shifts every day by the same annual-mean anomaly. Seasonal and variance changes are
  not modelled.
- Climatology years are each city's last N years where both temperature and CDD pass the
  missing-days rule. CDD is summed over observed days, as in the challenge.

## Implementation

- Registry names: `cdd_daily_shift`, `cdd_on_temp_p06` (and the `eia_trend30` ensemble)
- Code: `src/proto_star/forecasters/cdd_forcing_p06_p21.py`
- Config: `configs/agent_paper_cdd_forcing_p06_p21.yaml`
- Tests: `tests/test_forecasters_cdd_forcing_p06_p21.py`
- Why analysis: `scripts/analyze_cdd_forcing_p06_p21.py` → `docs/trials/paper_cdd_forcing_p06_p21_why.md`
- Leakage review: `train` holds only rows up to the cut-off. The daily table is read from disk,
  cut to `Year <= cutoff_year` and checked with `assert_weather_cutoff` inside every fold. A
  test changes all post-cut-off daily, annual and CO2 values and checks the forecasts do not
  change. With N = 10 and the 10-year mean temperature, the shift is zero and the forecast
  equals `ten_year_mean` exactly (tested, and checked on real data).

## Our results

Mean raw score over the ADR 0004 folds, all / years 1–3 / years 4–7. References: `current_best`
2.92 / 0.63 / 4.68, `hybrid_ridge_all_cdd` 3.60 / 0.94 / 5.54.

| Variant | All | 1–3 | 4–7 | Per origin (all years) 1980 / 1995 / 2011 | CDD skill years 4–7 |
|---|---|---|---|---|---|
| `shift30_recent` | 2.63 | 0.05 | 4.65 | -0.15 / 3.08 / 4.96 | 6.71 % |
| `shift30_recent_linear` | 2.63 | 0.08 | 4.63 | -0.18 / 3.20 / 4.86 | 6.63 % |
| `shift10_trend` | 2.62 | 0.33 | 4.29 | -1.74 / 2.91 / 6.69 | 5.28 % |
| `shift10_trend_linear` | 2.62 | 0.33 | 4.29 | -1.74 / 2.93 / 6.68 | 5.26 % |
| `shift10_co2` | 2.61 | 0.55 | 3.96 | -2.04 / 2.54 / 7.32 | 3.95 % |
| `eia_trend30` | -0.33 | -1.84 | 0.65 | -4.23 / -3.01 / 6.25 | -9.31 % |
| `eia_cdd_on_temp_recent` | 2.82 | 0.47 | 4.68 | -0.11 / 3.89 / 4.67 | 6.82 % |
| `eia_cdd_on_temp_trend` | 2.65 | 0.34 | 4.40 | -0.94 / 3.42 / 5.46 | 5.70 % |
| `hybrid_ridge_shift30_avg` | 3.37 | 0.76 | 5.36 | 0.33 / 3.89 / 5.89 | 9.53 % |
| `current_best` | 2.92 | 0.63 | 4.68 | -0.75 / 3.56 / 5.95 | 6.84 % |
| `hybrid_ridge_all_cdd` | 3.60 | 0.94 | 5.54 | 0.24 / 4.13 / 6.44 | 10.27 % |

Command, commit and run dir: `uv run proto-star climate-trial configs/agent_paper_cdd_forcing_p06_p21.yaml --record`;
commit and run dir in `docs/trials/paper_cdd_forcing_p06_p21.md`.

## Takeaways

- No step-9 or P06 variant beats `current_best` on the mean, let alone `hybrid_ridge_all_cdd`.
  Averaging the shifted CDD into the ridge makes the ridge worse (5.36 vs 5.54 in years 4–7).
- The convexity is real but tiny. The exact recomputation is above its linear twin by 0.6 to
  1.9 °F-days on average, about +0.02 to +0.08 skill points. The temperature shifts are a few
  tenths of a °F, while the 10-year mean under-forecasts CDD by about 76 °F-days in years 4–7.
  A uniform shift of the daily climatology does not explain that bias.
- The faithful EIA 30-year trend line is the worst variant (-9.3 % CDD skill in years 4–7),
  consistent with round 1: straight trends extrapolate badly.
- Abandon step 9 as a submission candidate. Keep `hybrid_ridge_all_cdd`.
