# Reading list and experiment ideas

A shortlist to split across the team. When someone picks a paper, copy `_template.md` into a new
paper folder and add its row to the index in `README.md`.

**How far this has been checked:** citations and summaries come from abstracts, catalog records,
and search snippets. Nobody has read the full texts yet, so confirm details in the paper before
relying on them.

## Rules for using this research

- Our task is forecasting **yearly climate statistics up to 7 years ahead**, not weather events.
  Weather models such as GraphCast work days ahead, and the FAQ bans those trained on reanalysis
  from 2019 onward.
- Papers from any year are fine for **methods**. Never copy observed 2019–2025 values or findings
  about those years into a forecast or a modeling choice. See the data rule in `AGENTS.md`.
- Only follow links to papers. Do not download datasets or code bundles linked from them without
  checking their end dates. Lai and Dzombak's repositories hold the source records that run past
  2018, so they are off limits.

## Start here

| Priority | Paper | Why it matters to us | Suggested test |
|---|---|---|---|
| 1 | Lai & Dzombak (2020), ARIMA near-term regional forecasting, *Weather and Forecasting*. [DOI](https://doi.org/10.1175/waf-d-19-0158.1) | **Same authors and same city records as our dataset**, for 2–20 year projections. Reports a blend of recent observations and long-term trend. Best fit for the 25% reuse criterion | Reimplement on annual series and score on the backtest |
| 2 | Livezey et al. (2007), climate normals and trends, *JAMC*. [Summary slides](https://ncics.org/ncics/pdfs/cnws/11_Alternative%20Normals%20Workshop-Livezey.pdf) | Compares optimal climate normals, linear trends, and the "hinge fit" (flat until 1975, then linear) | Add a hinge baseline per city and per region |
| 3 | Wilks & Livezey (2013), alternative normals, *JAMC* 52(8). [DOI](https://doi.org/10.1175/JAMC-D-13-026.1) | Found 15-year averages worked for temperature and 30-year for precipitation, and that hinge fits were not yet justified for U.S. divisional data. Homogenized station data also performed better | Compare 10, 15, and 30-year windows per metric |
| 4 | Montero-Manso & Hyndman (2021), local vs. global forecasting, *IJF* 37(4). [arXiv](https://arxiv.org/abs/2008.00444) | Short series benefit from pooled models, and simple global linear models do well. Supports modeling all 210 cities together | One pooled linear model on anomalies |
| 5 | Menne & Williams (2009), pairwise homogenization, *J. Climate*. [PDF](https://ncei.noaa.gov/pub/data/ushcn/papers/menne-williams2009.pdf) | Separates station artifacts from climate by comparing neighbors. Addresses the steps of up to about 4 °F found in our EDA | Estimate station-switch steps against nearby cities |

## Further reading by topic

**Combining and choosing forecasts**
- Makridakis et al. (2018), M4 competition findings, *IJF*. [Record](https://econpapers.repec.org/RePEc:eee:intfor:v:34:y:2018:i:4:p:802-808). Combinations did well and pure ML did poorly.
- Smith & Wallis (2009), the forecast combination puzzle, as reviewed in [this paper](https://arxiv.org/abs/1505.00475). Equal weights often beat estimated weights.
- [Forecast combinations: an over 50-year review](https://arxiv.org/abs/2205.04216).

**Validation**
- Cerqueira et al. (2020), *Machine Learning* 109. [arXiv](https://arxiv.org/abs/1905.11744). For non-stationary series, repeated out-of-sample tests gave the best estimates. This supports our rolling origins.

**Statistical climate benchmarks**
- [A Simple Empirical Model for Decadal Climate Prediction](https://publications.hzg.de/id/28751/index.php), *J. Climate*. CO2 forcing plus an autoregressive term. Any CO2 input must stop at 2018.
- [Statistical benchmark models for decadal SST forecasts](https://link.springer.com/article/10.1007/s00382-012-1531-9), *Climate Dynamics*. Forced trend plus AR(1).

**Pooling trends across places**
- Haug et al. (2020), [spatial trend analysis](https://munin.uit.no/handle/10037/18527). Hierarchical Bayesian trends on gridded data.
- We found no paper applying partial pooling to station temperature trends. If it works here, that is a contribution worth stating in the README.

**CDD and hottest day**
- Hottest-day extremes: nonstationary GEV with a location trend, as in this [UCAR course](https://projects.ral.ucar.edu/extremes/Extremes/eva1.pdf).
- CDD from daily data: this [hourly vs. daily study](https://par.nsf.gov/servlets/purl/10571122) shows how sensitive cooling estimates are to the method. Check whether it fits before citing it.

**Station and urban effects**
- Hausfather et al. (2013), [urbanization in USHCN](https://www.ncei.noaa.gov/pub/data/ushcn/papers/hausfather-etal2013.pdf). Useful for land-cover or population features, which are allowed as forecast inputs. Published estimates of the urban share of warming disagree widely.

## Check before using

| Item | Concern | Default |
|---|---|---|
| Lai & Dzombak (2021) G-ARIMA, *JAMC* 60(5). [DOI](https://doi.org/10.1175/JAMC-D-20-0204.1) | Needs climate model simulations for 2019–2025. The rules do not clearly cover these | Ask in the Space's Community tab first |
| [`scifi` R package](https://rdrr.io/github/yuchuan-lai/scifi/f/README.md) by Lai | May bundle data past 2018. Its license is unchecked | Inspect before installing, or reimplement from the paper |
| [Chronos](https://arxiv.org/abs/2403.07815) | Training data includes weather series. We could not confirm the end dates | Do not use unless a card proves a pre-2019 cutoff |
| [TimesFM](https://huggingface.co/google/timesfm-2.0-500m-jax) | Reported to train on data through about 2022, including Google Trends, and 2.0 adds further sets | Do not use |

## Experiment ideas

Compare every idea with the current ensemble, per metric, using the same origins. Also report
forecast years 4–7 separately, because those match the Final Score (2022–2025).

| Idea | Metrics | Effort |
|---|---|---|
| Regional trend blended with city trend | Temperature, CDD | Low |
| 15-year window instead of 10-year | Temperature, CDD | Low |
| Hinge fit | Temperature, CDD | Low |
| ARIMA per city, following Lai & Dzombak | All | Medium |
| Levels from the current station segment only | Temperature, CDD | Medium |
| Pooled linear model on anomalies | All | Medium |
| Shift daily temperatures by a warming estimate, then recompute CDD | CDD | Medium |
| Nonstationary GEV | Hottest day | Medium |
| Equal-weight average of the best few methods | All | Low |
| Elevation, land cover, or population as pooling groups (adds interoperability) | Temperature, CDD | High |
