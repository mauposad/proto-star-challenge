# Rows for the shared logs (the orchestrator merges these)

## docs/experiments.md

Covered by the single trial row in `papers/2025_eia_steo_cdd/log_rows.md`, which reports
both P21 variants. Do not add a second row.

## papers/README.md index row

| `2013_ho_forced_trend_ar1` | Ho, Hawkins, Shaffrey & Underwood, statistical decadal SST benchmark: forced trend + AR(1) (P21; P20 context) | 2013 | Statistical: per-city OLS on log NOAA Mauna Loa CO2 (or a regional-mean temperature anomaly) plus an AR(1) residual; temperature and CDD | adapted | `configs/agent_paper_cdd_forcing_p06_p21.yaml` | `p21_co2_ar1` -4.26 / 1.53 / 8.58 (1980/1995/2011; mean 1.95 all, 3.25 years 4–7); `p21_regional_ar1` -6.73 / 3.48 / 7.38 (1.38 / 2.78) | `p21_co2_ar1` better at 2/3 origins (-2.53 / 1.39 / 5.16) | Big win at 2011, big loss at 1980: the trend extrapolates the fit window. Temperature skill in years 4–7 10.0 % vs 11.9 % for the 10-year mean. CO2 data would not rebuild on CI. Not adopted |
