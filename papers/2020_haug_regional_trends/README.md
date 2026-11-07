# Regional trends and pooling groups: Haug et al. 2020 (P22) and Hausfather et al. 2013 (P24)

One card for two loosely paired papers, run as one trial (replication steps 7 and 12).

| | |
|---|---|
| **Authors** | P22: Ola Haug, Thordis L. Thorarinsdottir, Sigrunn H. Sørbye, Christian L. E. Franzke. P24: Zeke Hausfather, Matthew J. Menne, Claude N. Williams, Troy Masters, Ronald Broberg, David Jones |
| **Year / venue** | P22: 2020, *Advances in Statistical Climatology, Meteorology and Oceanography* 6(1), 1-12, "Spatial trend analysis of gridded temperature data at varying spatial scales". P24: 2013, *Journal of Geophysical Research: Atmospheres* 118(2), 481-494, "Quantifying the effect of urbanization on U.S. Historical Climatology Network temperature records" |
| **Link** | P22: [10.5194/ascmo-6-1-2020](https://doi.org/10.5194/ascmo-6-1-2020) (checked on the publisher page). P24: [10.1029/2012JD018509](https://doi.org/10.1029/2012JD018509) (checked via Crossref) |
| **Code released by authors** | P22: not checked. P24: not checked. None used |
| **PDF in repo?** | no (P22 is CC BY 4.0, but not needed) |
| **Status** | adapted |
| **Owner** | agent (for mp) |
| **Branch / PR** | `agent/paper-p22-p24-regional` (no PR) |

## Summary

**P22.** Classical trend assessments on gridded temperature treat every grid cell on its own and
ignore the spatial correlation of trend estimates. The authors build a space-time hierarchical
Bayesian model for temperature anomalies in which the trend coefficient is a latent Gaussian
random field, which smooths trends across neighbouring cells and allows joint (simultaneous)
significance statements. Their case study is 65 years of summer gridded temperature over Europe.
Spatial smoothing generally widens the regions where "no trend" is rejected, but not in every
subregion (abstract, publisher page).

**P24.** The authors classify USHCN stations as urban or rural with four proxies and compare
urban and rural trends with station pairing and spatial gridding. Per the Crossref abstract,
urbanization accounts for 14-21 % of the rise in unadjusted minimum temperatures since 1895;
USHCN v2 homogenization removes most of that signal in recent decades but only about half
before 1930. The full text was not machine-readable here (no PDF tool), so the four proxies
and other details are TBD.

## Architecture

- P22: hierarchical Bayesian model, temperature anomaly = spatially varying trend x time +
  noise; the trend field is a latent Gaussian random field. Inference details (INLA/MCMC): TBD
  (not read beyond the abstract).
- P24: not a forecasting model. Station classification by urbanity proxies, pairwise
  urban-rural trend differences, gridded averages.

## Results claimed by the authors

See the summary; we do not reuse their numbers. Neither paper reports forecast skill.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | P22: gridded European summer temperature, 65 years. P24: USHCN stations. Ours: 210 city station series (annual master table, years <= cutoff) plus static attributes |
| Target(s) | P22 on `annual_avg_temp` and `cdd`; P24 groups on `cdd` (the only metric where the round-1 pooled ridge helps). `total_precip_in` and `hottest_day_temp` stay on `current_best` |
| Horizon | 7 years (2019-2025); backtest folds 1980 / 1995 / 2011 |
| Metric | relative MAE skill vs 30-year mean |

## Deviations

1. **P22 shrinkage is empirical Bayes in discrete groups**, not a latent Gaussian random field.
   Within each group (NOAA climate region, or elevation band) we estimate each city's OLS slope
   over the last 30 (or 50) years and its sampling variance, the between-city trend variance
   `tau2 = max(0, var(slope) - mean(sampling variance))` (method of moments), and shrink each
   city slope toward the precision-weighted group trend with weight `tau2 / (tau2 + var_i)`.
   No spatial covariance, no MCMC/INLA.
2. **P22 is used to forecast**, not to test trend significance: forecast = mean of the last 10
   valid years + `damping` x shrunk trend x (forecast year - centre year of those 10 years).
   Round 1 found that raw trend extrapolation loses, so damping 0.5, a fully pooled
   (group-only) trend, and a level-update-only control (`extrapolate_lead: false`) were included.
3. **P24 is used for pooling groups only.** We do not measure the urban share of warming. Groups
   feed the round-1 pooled ridge (`pooled_median_p09_p14` features, imported, not edited) as
   group x feature interactions, one model per region, or additive one-hots.
4. **Urbanity proxies differ from P24's.** We use (a) the 2010 Census population of the most
   populous Census place within 20 km of the station, banded at 50,000 / 175,000, and (b) the
   NLCD 2016 land cover at 5 pixels around the station (centre and about 500 m N/S/E/W), majority
   of developed-high (NLCD 23/24), developed-low (21/22) or undeveloped. The full NLCD raster is
   several GB, so we sample points through the MRLC WMS instead (documented proxy). Elevation is
   the GHCN-Daily station inventory elevation, banded at 130 / 310 m. Band edges are rough terciles
   of the 210 cities, set from the attribute table before any run.
5. **Vintage.** 2010 Census and NLCD 2016 postdate the 1980 and 1995 cutoffs: static, not weather,
   but a mild look-ahead in group assignment for early folds. GHCN elevation is from the current
   inventory (static metadata; no archived pre-2019 copy used).

## Implementation

- Registry names: `regional_trend_p22`, `pooled_groups_p24`
- Code: `src/proto_star/forecasters/regional_p22_p24.py` (imports `_pooled_features` and
  `pooled_p09_p14._make_estimator`)
- Data: `scripts/download_regional_p22_p24.py` -> `data/external/regional_p22_p24/city_groups.csv`
  (needed only for the elevation, population and land-cover groups; region comes from the master)
- Config: `configs/agent_paper_regional_p22_p24.yaml` (12 variants fixed before the first run)
- Tests: `tests/test_forecasters_regional_p22_p24.py`
- Why analysis: `scripts/analyze_regional_p22_p24.py` -> `docs/trials/regional_p22_p24_why.md`
- Leakage review: trends, levels, lags and training targets come from the fold's `train` frame
  only (`annual_to_long`, `_pooled_features`); scalers and encoders sit inside the sklearn
  pipeline. Group attributes are static per city. A test changes every value after the cutoff and
  checks that both forecasters' predictions are unchanged.

## Our results

Trial note `docs/trials/regional_p22_p24.md`, run `runs/trials/20261107-170322_regional_p22_p24`,
recorded at commit `913aedf` (clean tree), master hash `99128065…bb04d1`, about 5 minutes on 3
threads. Command: `uv run proto-star climate-trial configs/agent_paper_regional_p22_p24.yaml --record`.

Best P24 variant `p24_ridge_population_interact`, all years, skill in %:

| Origin | Score | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1980 | 0.17 | -2.53 | -2.06 | 0.00 | 0.00 | 2.76 |
| 1995 | 4.21 | 1.39 | 11.30 | 0.00 | 0.00 | 5.55 |
| 2011 | 6.45 | 5.16 | 8.05 | 0.00 | 0.00 | 17.75 |

Best P22 variant `p22_region_trend_damped`, all years: 1980 -2.21 (temp -6.25, CDD -2.59),
1995 3.58 (12.17, 2.15), 2011 7.86 (11.72, 19.70).

Mean raw score (all / years 1-3 / years 4-7):

| Method | All | Yrs 1-3 | Yrs 4-7 | Wins 4-7 vs `current_best` | Wins 4-7 vs `hybrid_ridge_all_cdd` |
|---|---|---|---|---|---|
| `hybrid_ridge_all_cdd` (reference) | 3.60 | 0.94 | 5.54 | 3/3 | - |
| `current_best` | 2.92 | 0.63 | 4.68 | - | 0/3 |
| `p24_ridge_population_interact` | 3.61 | 0.95 | 5.55 | 3/3 | 2/3 |
| `p24_ridge_all_groups_additive` | 3.59 | 0.95 | 5.52 | 3/3 | 0/3 |
| `p24_ridge_landcover_interact` | 3.52 | 0.89 | 5.43 | 3/3 | 0/3 |
| `p24_ridge_region_interact` | 3.56 | 1.18 | 5.23 | 2/3 | 2/3 |
| `p24_ridge_region_separate` | 3.54 | 1.19 | 5.20 | 2/3 | 2/3 |
| `p24_ridge_elevation_interact` | 3.43 | 0.98 | 5.18 | 3/3 | 0/3 |
| `p22_region_trend_damped` | 3.08 | 0.19 | 5.24 | 2/3 | 2/3 |
| `p22_eb_region_flat` (control) | 2.63 | -0.24 | 4.79 | 2/3 | 1/3 |
| `p22_eb_region_damped` | 2.73 | 0.05 | 4.73 | 2/3 | 1/3 |
| `p22_eb_elevation_damped` | 2.68 | 0.03 | 4.65 | 2/3 | 1/3 |
| `p22_eb_region_long_damped` | 2.68 | 0.42 | 4.34 | 1/3 | 1/3 |
| `p22_eb_region` (undamped) | 1.75 | -0.92 | 3.66 | 1/3 | 1/3 |

## Takeaways

- **P24 pooling groups: no gain.** The best group model ties `hybrid_ridge_all_cdd`
  (+0.01 / +0.01 / +0.01). Region interactions and separate region models gain CDD skill in
  years 1-3 (+0.94 points) but lose it in years 4-7 (-1.24). The round-1 ridge already pools
  well; extra group structure fits short-lead patterns that do not last.
- **P22 shrunk trends: better than raw trends, still not good enough.** Shrinking hard (the
  pure regional trend) and damping (0.5) is the best P22 setting and gains temperature (+1.23)
  and CDD (+0.98) skill in years 4-7 over `current_best`, but it loses years 1-3 and loses badly
  at the 1980 origin, where 1951-1980 regional trends were negative and warming followed. The
  trend's sign is not stable across regimes, which is the same failure round 1 saw.
- `submit` stays `hybrid_ridge_all_cdd`. Not adopted. Status: **adapted**. A possible follow-up
  is to combine the P22 regional trend for temperature only with the pooled ridge for CDD, but
  that would be a new variant chosen after seeing these results.
