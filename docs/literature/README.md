# Literature starting point

Papers and method notes we start from for the Protostar climate forecast (210 U.S. cities,
2019–2025, metrics `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd`).
This is a reading list, not a set of results. Nothing here has been replicated yet.

- Machine-readable copy: [papers.csv](papers.csv) (same rows).
- Team data rule every entry is checked against: [../honor_code.md](../honor_code.md).
- Order in which we plan to replicate: [../replication_order.md](../replication_order.md).
- Once a paper is replicated, its card and score go in [`papers/`](../../papers/README.md).

Entries marked "not checked" have not been verified against the source. Verify the citation
and DOI before relying on them.

## Group A: usable, data before 2019 only

| ID | Citation | Link or DOI | Use for | Priority |
|----|----------|-------------|---------|----------|
| P01 | Livezey et al. 2007. Estimation and Extrapolation of Climate Normals and Climatic Trends. J. Appl. Meteor. Climatol. 46(11). | 10.1175/2007JAMC1666.1 | Hinge fit and optimal climate normal baselines. Temperature, CDD. | High |
| P02 | Huang, van den Dool, Barnston 1996. Long-lead seasonal temperature prediction using optimal climate normals. J. Climate 9, 809-817. | not checked | Choose the averaging window length per metric. | High |
| P03 | Wilks 2013. Projecting "normals" in a nonstationary climate. J. Appl. Meteor. Climatol. 52, 289-302. | 10.1175/JAMC-D-11-0267.1 | Tested window lengths. Evidence that about 15 years is strong. | High |
| P04 | Wilks and Livezey 2013. Performance of Alternative "Normals" for Tracking Climate Changes. J. Appl. Meteor. Climatol. 52(8), 1677-1687. | 10.1175/jamc-d-13-026.1 | Eleven alternative baselines and a test method. | High |
| P05 | Oreshkin et al. 2019. N-BEATS. | arXiv 1905.10437 | Deep model for single series. Architecture only. Train from scratch. | Medium |
| P06 | EIA. STEO Weather Forecast model note (Oct 2025). | eia.gov, "STEO Weather Model" | Regression on annual degree-day data. CDD reference. Method note, not a paper. | Medium |
| P07 | Survey: Machine Learning for the Physics of Climate. | arXiv 2408.09627 | Map of the field. Source of more citations. | Low |
| P08 | Salinas et al. DeepAR. Int. J. Forecasting 36(3), 2020 (arXiv 1704.04110, 2017). | 10.1016/j.ijforecast.2019.07.001 | One global model trained on many related series. Fits 210 cities. | Medium |
| P09 | Median and quantile methods: Koenker and Bassett (pinball loss; year not checked, 1978 from memory); Meinshausen 2006 (quantile regression forests); Chen and Guestrin 2016 (XGBoost). | not checked | Median regression equals MAE minimization. Use for precipitation, CDD, hottest day. | High |
| P10 | Bergmeir and Benitez 2012. On the use of cross-validation for time series predictor evaluation. Information Sciences 191, 192-213. | not checked | Evaluation design. Blocked cross-validation. | Medium |
| P11 | Bergmeir, Hyndman, Koo 2018. A note on the validity of cross-validation for evaluating autoregressive time series prediction. Comput. Stat. Data Anal. 120, 70-83. | 10.1016/j.csda.2017.11.003 | When k-fold is valid. See the note below. | Low |
| P12 | Hyndman and Athanasopoulos. Forecasting: Principles and Practice (rolling forecasting origin). | otexts.com/fpp2 | Rolling-origin evaluation method. | Medium |

Note on P11: the paper says k-fold is valid for purely autoregressive models with
uncorrelated errors. The kickoff deck says never use random splits. Follow the deck. Use
rolling-origin tests.

Note on P05 and P08: use the architectures only. Train from scratch; no pretrained weights
(see the honor code).

## Group B: needs a ruling (low priority, visit if time permits)

| ID | Citation | Link | Reason |
|----|----------|------|--------|
| R01 | Fernandez and Barnes 2025. Multi-Year-to-Decadal Temperature Prediction using a Machine Learning Model-Analog Framework. | arXiv 2502.17583 | Uses CMIP6 runs. Those runs extend past 2018. |
| R02 | Luo et al. 2022. A Bayesian Deep Learning Approach to Near-Term Climate Prediction. J. Adv. Model. Earth Syst. 14(10). | arXiv 2202.11244 | Uses a CESM2 control run. Simulated data. Target is not a U.S. city metric. |

If we ask the organizers, use the Space's Community tab.

## Group C: excluded for now

| ID | What | Reason |
|----|------|--------|
| C01 | Medium-range ML weather models (for example GraphCast, Pangu-Weather). | They need current weather fields as input. For 2019 to 2025, those fields break the rule. They also forecast days ahead, not years. Training data not checked. |
| C02 | Foundation models named in P07 (ClimaX, NeuralGCM). | Training data not checked. Treat as excluded. |

## To verify before use

| ID | What | Status |
|----|------|--------|
| V01 | arXiv 2511.05071 (a 2025 paper on climate normals). | Authors and result not checked. |
| V02 | DOIs marked "not checked" above (P02, P09, P10). | Not checked. |
| V03 | ES-RNN (Smyl, M4 winner). | Not searched. Add only after a check. |

IDs C01–C02 and V01–V03 were assigned in this file so every row in `papers.csv` has an ID.
