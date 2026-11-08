# Forced trend + AR(1) benchmark: Ho, Hawkins, Shaffrey & Underwood 2013 (P21; P20 for context)

| | |
|---|---|
| **Authors** | Chun Kit Ho, Ed Hawkins, Len Shaffrey, Fiona M. Underwood (P21). P20: TBD (not read) |
| **Year / venue** | 2013, Climate Dynamics 41(3-4), 917-935: "Statistical decadal predictions for sea surface temperatures: a benchmark for dynamical GCM predictions" |
| **Link** | DOI [10.1007/s00382-012-1531-9](https://doi.org/10.1007/s00382-012-1531-9). P20: publications.hzg.de/id/28751 (not checked) |
| **Code released by authors** | none known |
| **PDF in repo?** | no (paywalled; only the abstract was read) |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p06-p21-cdd-forcing` (no PR) |

## Summary

Cheap statistical models built only on observations should be the yardstick for initialised
dynamical decadal forecasts. The paper models annual-mean SST at each HadISST grid box as a
radiatively forced trend, a linear regression on equivalent global-mean CO2, plus internal
variability modelled by AR(1) or by constructed analogues. The paper verified 46 retrospective
forecasts (start years 1960–2005). Trend + AR(1) anomaly correlation exceeds 0.7 over parts of the
extratropical North Atlantic, the Indian Ocean and the western Pacific, mostly from the forced
trend. (From the abstract; the full text was not read.)

## Architecture

- Statistical: OLS on a forcing series `F`, AR(1) on the residual.
- Forecast: `y(t+h) = a + b * F_hat(t+h) + phi**h * e(t)`, with `phi` the lag-1
  autocorrelation of the residuals over consecutive years, clipped to `[0, 0.95]`.
- Inputs: annual city temperature or CDD up to the cut-off; forcing = log of NOAA Mauna Loa
  annual CO2 (1959–2018), or a regional-mean temperature anomaly.

## Results claimed by the authors

The abstract's numbers above (anomaly correlation above 0.7 in some regions). It also reports
that DePreSys beats the statistical models over much of the North Atlantic at leads 2–5 and 6–9
years, but trend + AR(1) is generally better in the North Atlantic Current region.
Not our results.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | city annual `Avg Temp` and `cdd` (≤ cut-off), NOAA Mauna Loa CO2 ≤ cut-off |
| Target(s) | `annual_avg_temp`, `cdd` (`current_best` for precipitation and hottest day) |
| Horizon | 7 years (2019–2025) |
| Metric | relative MAE skill vs 30-year mean |

## Deviations

- Mauna Loa CO2 (log) instead of equivalent global-mean CO2. The series starts in 1959, so the
  fit uses at most the last 40 years from 1959 on (1959–1980 for the 1980 fold).
- Future forcing: the paper's rule was not read. We extrapolate CO2 linearly from the last 10
  annual values before each fold's cut-off, a rule fixed in the config. Observed later
  values are never used, even inside a backtest fold.
- The regional forcing variant uses the mean temperature anomaly of the cities in the same
  coordinate region (computed from training rows), extrapolated linearly from its last 30
  years. This is our addition, not the paper's.
- City temperature and CDD instead of gridded SST; no constructed-analogue model.
- P20 ("A Simple Empirical Model for Decadal Climate Prediction") was not read; listed for
  context only.

## Implementation

- Registry name: `forced_trend_ar1_p21` (also feeds the `shift10_co2` step-9 variant)
- Code: `src/proto_star/forecasters/cdd_forcing_p06_p21.py`
- Config: `configs/agent_paper_cdd_forcing_p06_p21.yaml`
- Data: `scripts/download_noaa_co2.py` → `data/external/noaa_co2/` (capped at 2018)
- Tests: `tests/test_forecasters_cdd_forcing_p06_p21.py` (exact recovery of a linear CO2 relation,
  and a test that post-cut-off CO2 values do not change any forecast)
- Leakage review: the CO2 file is cut to the fold's cut-off and checked with
  `assert_weather_cutoff` before use, and the regional forcing uses training rows only.

## Our results

Mean raw score, all / years 1–3 / years 4–7. References: `current_best` 2.92 / 0.63 / 4.68,
`hybrid_ridge_all_cdd` 3.60 / 0.94 / 5.54, `ten_year_mean` 1.34 / -0.62 / 2.78.

| Variant | All | 1–3 | 4–7 | Per origin (all years) 1980 / 1995 / 2011 | Temp skill 4–7 | CDD skill 4–7 |
|---|---|---|---|---|---|---|
| `p21_co2_ar1` | 1.95 | -0.02 | 3.25 | -4.26 / 1.53 / 8.58 | 10.04 % | 2.94 % |
| `p21_regional_ar1` | 1.38 | -0.48 | 2.78 | -6.73 / 3.48 / 7.38 | 7.44 % | 3.66 % |
| `shift10_co2` (CO2 temperature feeding step 9) | 2.61 | 0.55 | 3.96 | -2.04 / 2.54 / 7.32 | 11.90 % | 3.95 % |
| `current_best` | 2.92 | 0.63 | 4.68 | -0.75 / 3.56 / 5.95 | 11.90 % | 6.84 % |

Command, commit and run dir: see `docs/trials/paper_cdd_forcing_p06_p21.md`.

## Takeaways

- The forced trend wins big at 2011 (8.58 against 5.95 for `current_best`) and loses big at
  1980 (-4.26 against -0.75). It extrapolates the warming of the fit window, which pays off
  after 2011 and hurts after 1980. This matches round 1: trends are high variance on three
  origins.
- It loses to the 10-year mean on temperature in years 4–7 at the mean (10.0 % vs 11.9 %).
- Not adopted. Even if it had won, a CO2 forecaster would not rebuild on the CI publish
  workflow, which downloads only the protostar data.
