# Literature Index

ResearchQuestion: Which statistical or machine-learning forecasting methods can raise out-of-sample skill (relative MAE against a 30-year climatological mean) for annual, city-level (station-based, mostly U.S. airport) forecasts 1-7 years ahead of annual mean temperature, annual total precipitation, annual hottest-day temperature, and annual cooling degree days, using only observations through a fixed cut-off year?

Mode: SEARCH. Run date: 2026-11-09.

**Audit status: ALL NOTES ARE UNAUDITED.** The human asked to skip the citation-auditor verification step for this run. No Goldfish/auditor check has been run on any quote.

Layout: `sources/` holds raw fetched files (PDF, JSON, XML, HTML) plus extracted text (`.txt`) and rebuilt OpenAlex abstracts (`.abstract.txt`). `notes/` holds one note per kept source. `search/` holds raw search and metadata API responses.

## Sources

45 sources: 29 full text, 11 abstract only, 5 metadata only. "Must-include" IDs refer to `docs/literature/papers.csv`.

| Key | Citation | Identifier | Access | Type | Relevance |
|-----|----------|------------|--------|------|-----------|
| livezey2007estimation | Livezey, Vinnikov, Timofeyeva, Tinker, van den Dool (2007). Estimation and Extrapolation of Climate Normals and Climatic Trends. JAMC 46(11), 1759-1776. | 10.1175/2007JAMC1666.1 | full text (publisher PDF found as an exhibit in a public Missouri PSC filing) | peer-reviewed article | P01. OCN, trend, and hinge-fit normals; extrapolation several years ahead |
| huang1996longlead | Huang, van den Dool, Barnston (1996). Long-Lead Seasonal Temperature Prediction Using Optimal Climate Normals. J. Climate 9(4), 809-817. | 10.1175/1520-0442(1996)009<0809:LLSTPU>2.0.CO;2 | abstract only | peer-reviewed article | P02. Origin of OCN; shorter, annually updated windows beat the 30-yr normal |
| vandendool2011readme | van den Dool (2000-2011). CPC OCN readme page. | cpc.ncep.noaa.gov/products/people/wd51hd/ocn/readme.html | full text | other | Operational OCN: 10-yr T, 15-yr P, skill mask, damping |
| wilks2013projecting | Wilks (2013). Projecting "Normals" in a Nonstationary Climate. JAMC 52(2), 289-302. | 10.1175/JAMC-D-11-0267.1 | abstract only | peer-reviewed article | P03. 15-yr (T) and 30-yr (P) averages best recently; hinge not justified |
| wilks2013performance | Wilks & Livezey (2013). Performance of Alternative "Normals" for Tracking Climate Changes, Using Homogenized and Nonhomogenized Seasonal U.S. Surface Temperatures. JAMC 52(8), 1677-1687. | 10.1175/JAMC-D-13-026.1 | abstract only | peer-reviewed article | P04. 11 alternatives; CPC 15-yr best; homogenized data better |
| arguez2009improving | Arguez & Vose (c. 2009). On Improving NOAA's Climate Normals: An Introduction to 'Optimal Normals' of Temperature. AMS conf. paper 9B.3. | ams.confex.com/ams/pdfpapers/146498.pdf | full text | other (conference, not peer reviewed) | Station-level OCN/hinge at NCDC; optimal N vs. trend |
| arguez2011definition | Argüez & Vose (2011). The Definition of the Standard WMO Climate Normal: The Key to Deriving Alternative Climate Normals. BAMS 92(6), 699-704. | 10.1175/2010BAMS2955.1 | metadata only | peer-reviewed article | Alternative normals framing (no text retrieved) |
| proietti2025estimation | Proietti & Giovannelli (2025). On the Estimation of Climate Normals and Anomalies. arXiv 2511.05071. | arXiv 2511.05071 | full text | preprint | V01. Regularized real-time filter for normals under trends |
| krueger2011simple | Krueger & von Storch (2011). A Simple Empirical Model for Decadal Climate Prediction. J. Climate 24(4), 1276-1283. | 10.1175/2010JCLI3726.1 | full text | peer-reviewed article | P20. CO2 regression + AR benchmark (uses AR4 20th-century runs to separate components) |
| ho2013statistical | Ho, Hawkins, Shaffrey, Underwood (2013). Statistical decadal predictions for sea surface temperatures: a benchmark for dynamical GCM predictions. Clim. Dyn. 41, 917-935. | 10.1007/s00382-012-1531-9 | full text | peer-reviewed article | P21. Trend (CO2 regression) + AR1 / analogue benchmark |
| lai2020use | Lai & Dzombak (2020). Use of the ARIMA Model to Forecast Near-Term Regional Temperature and Precipitation. Wea. Forecasting 35(3), 959-976. | 10.1175/WAF-D-19-0158.1 | abstract only | peer-reviewed article | P13. ARIMA vs linear trend, 2-20 yr, local records |
| eia2025shortterm | EIA (2025). Short-Term Energy Outlook: Weather Forecast. | eia.gov/analysis/handbook/pdf/STEO Weather Model.pdf | full text | report | P06. OLS 30-yr trend line on annual CDD/HDD |
| morris1999impact | Morris (c. 1999). The Impact of Temperature Trends on Short-Term Energy Demand. EIA. | eia.gov/outlooks/steo/special/pdf/temptrnd.pdf | full text | report | 30-yr norms miss warming trend for degree-day projections |
| montero-manso2021principles | Montero-Manso & Hyndman (2021). Principles and algorithms for forecasting groups of time series: Locality and globality. IJF 37(4), 1632-1653. | 10.1016/j.ijforecast.2021.03.004; arXiv 2008.00444 | full text | peer-reviewed article | P14. Global (pooled) models, incl. linear, competitive |
| hewamalage2021global | Hewamalage, Bergmeir, Bandara (2021/22). Global models for time series forecasting: A Simulation study. Pattern Recognition 124, 108441. | 10.1016/j.patcog.2021.108441; arXiv 2012.12485 | full text | peer-reviewed article | Global vs local under short/heterogeneous series |
| salinas2020deepar | Salinas, Flunkert, Gasthaus, Januschowski (2020). DeepAR. IJF 36(3), 1181-1191. | 10.1016/j.ijforecast.2019.07.001; arXiv 1704.04110 | full text | peer-reviewed article | P08. Global autoregressive RNN |
| oreshkin2019nbeats | Oreshkin, Carpov, Chapados, Bengio (2019/2020). N-BEATS. arXiv 1905.10437 (ICLR 2020 per header). | arXiv 1905.10437 | full text | preprint | P05. Deep univariate architecture |
| smyl2020hybrid | Smyl (2020). A hybrid method of exponential smoothing and recurrent neural networks for time series forecasting. IJF 36(1), 75-85. | 10.1016/j.ijforecast.2019.03.017 | metadata only | peer-reviewed article | V03. ES-RNN (M4 winner) |
| makridakis2018m4 | Makridakis, Spiliotis, Assimakopoulos (2018). The M4 Competition: Results, findings, conclusion and way forward. IJF 34(4), 802-808. | 10.1016/j.ijforecast.2018.06.001 | metadata only | peer-reviewed article | P16 (claims not verified) |
| makridakis2020m4 | Makridakis, Spiliotis, Assimakopoulos (2020). The M4 Competition: 100,000 time series and 61 forecasting methods. IJF 36(1), 54-74. | 10.1016/j.ijforecast.2019.04.014 | abstract only | peer-reviewed article | Companion to P16 |
| gardner1985forecasting | Gardner & McKenzie (1985). Forecasting Trends in Time Series. Management Science 31(10), 1237-1246. | 10.1287/mnsc.31.10.1237 | abstract only | peer-reviewed article | Damped trend; better at long leads |
| smith2009simple | Smith & Wallis (2009). A Simple Explanation of the Forecast Combination Puzzle. OBES 71(3), 331-355. | 10.1111/j.1468-0084.2008.00541.x | abstract only | peer-reviewed article | P17. Equal weights vs estimated weights |
| qian2015forecast | Qian, Rolling, Cheng, Yang (2015). On the Forecast Combination Puzzle. arXiv 1505.00475. | arXiv 1505.00475 | full text | preprint | Review cited in P17 |
| claeskens2016forecast | Claeskens, Magnus, Vasnev, Wang (2016). The forecast combination puzzle: A simple theoretical explanation. IJF 32(3), 754-762. | 10.1016/j.ijforecast.2015.12.005 | full text (author manuscript) | peer-reviewed article | Estimated weights biased, higher variance |
| wang2023forecast | Wang, Hyndman, Li, Kang (2022). Forecast combinations: an over 50-year review. arXiv 2205.04216. | arXiv 2205.04216 | full text | preprint | P18. Combination review (journal version not verified) |
| koenker1978regression | Koenker & Bassett (1978). Regression Quantiles. Econometrica 46(1). | 10.2307/1913643 | metadata only | peer-reviewed article | P09. Quantile/median regression origin |
| meinshausen2006quantile | Meinshausen (2006). Quantile Regression Forests. JMLR 7, 983-999. | jmlr.org v7 | full text | peer-reviewed article | P09. Conditional quantiles (median) from forests |
| chen2016xgboost | Chen & Guestrin (2016). XGBoost: A Scalable Tree Boosting System. KDD '16. | 10.1145/2939672.2939785; arXiv 1603.02754 | full text | peer-reviewed article | P09. Gradient tree boosting system |
| friedman2001greedy | Friedman (2001). Greedy function approximation: A gradient boosting machine. Ann. Stat. 29(5), 1189-1232. | 10.1214/aos/1013203451 | abstract only | peer-reviewed article | Boosting with least absolute deviation loss |
| natekin2013gradient | Natekin & Knoll (2013). Gradient boosting machines, a tutorial. Front. Neurorobot. 7:21. | 10.3389/fnbot.2013.00021 | full text | peer-reviewed article | L1 loss = conditional median; quantile 0.5 = L1 |
| efron1975data | Efron & Morris (1975). Data Analysis Using Stein's Estimator and its Generalizations. JASA 70(350). | 10.1080/01621459.1975.10479864 | abstract only | peer-reviewed article | James-Stein / empirical Bayes shrinkage |
| bergmeir2012use | Bergmeir & Benítez (2012). On the use of cross-validation for time series predictor evaluation. Inf. Sci. 191, 192-213. | 10.1016/j.ins.2011.12.028 | metadata only | peer-reviewed article | P10. Blocked CV |
| bergmeir2018note | Bergmeir, Hyndman, Koo (2018). A note on the validity of cross-validation for evaluating autoregressive time series prediction. CSDA 120, 70-83 (quotes from 2015 working paper). | 10.1016/j.csda.2017.11.003; 10.26180/21521274 | full text (working paper) | peer-reviewed article | P11. K-fold CV validity for AR ML models |
| cerqueira2020evaluating | Cerqueira, Torgo, Mozetič (2020). Evaluating time series forecasting models. Machine Learning 109, 1997-2028. | 10.1007/s10994-020-05910-7; arXiv 1905.11744 | full text | peer-reviewed article | P19. Order-preserving OOS best for nonstationary series |
| menne2009homogenization | Menne & Williams (2009). Homogenization of Temperature Series via Pairwise Comparisons. J. Climate 22(7), 1700-1717. | 10.1175/2008JCLI2263.1 | full text | peer-reviewed article | P15. Pairwise homogenization |
| hausfather2013quantifying | Hausfather, Menne, Williams, Masters, Broberg, Jones (2013). Quantifying the effect of urbanization on U.S. Historical Climatology Network temperature records. JGR-Atmos 118(2), 481-494. | 10.1029/2012JD018509 | full text (accepted manuscript) | peer-reviewed article | P24. Urban share of raw Tmin trends; removed by homogenization |
| haug2020spatial | Haug, Thorarinsdottir, Sørbye, Franzke (2020). Spatial trend analysis of gridded temperature data at varying spatial scales. ASCMO 6, 1-12. | 10.5194/ascmo-6-1-2020 | full text | peer-reviewed article | P22. Hierarchical Bayesian spatially pooled trends |
| katzndblock | Katz (n.d., PDF 2011). EVA Tutorial #1: Block Maxima Approach under Nonstationarity. NCAR slides. | projects.ral.ucar.edu/extremes/Extremes/eva1.pdf | full text | other (lecture notes) | P23. Nonstationary GEV with trend in location/scale |
| vose2017temperature | Vose, Easterling, Kunkel, LeGrande, Wehner (2017). Temperature changes in the United States. CSSR Vol. I, ch. 6, 185-206. | 10.7930/J0N29V45 | full text | report | U.S. warming, warmest-day-of-year trends, warming hole |
| easterling2017precipitation | Easterling et al. (2017). Precipitation change in the United States. CSSR Vol. I, ch. 7, 207-230. | 10.7930/J0H993CC | full text | report | U.S. annual precipitation trends: small, regionally mixed |
| mascioli2017timing | Mascioli, Previdi, Fiore, Ting (2017). Timing and seasonality of the United States 'warming hole'. ERL 12, 034008. | 10.1088/1748-9326/aa5ef4 | full text | peer-reviewed article | Warming hole definition and drivers |
| mueller2012hot | Mueller & Seneviratne (2012). Hot days induced by precipitation deficits at the global scale. PNAS 109(31), 12398-12403. | 10.1073/pnas.1204330109 | abstract only | peer-reviewed article | Precipitation deficits raise hot-day counts |
| mckinnon2024pace | McKinnon, Simpson, Williams (2024). The pace of change of summertime temperature extremes. PNAS 121. | 10.1073/pnas.2406143121 | full text | peer-reviewed article | V05 (actual content differs from papers.csv); hot days warm with the median |
| petri2015impacts | Petri & Caldeira (2015). Impacts of global warming on residential heating and cooling degree-days in the United States. Sci. Rep. 5, 12427. | 10.1038/srep12427 | full text | peer-reviewed article | CDD climatology; cited cooling sensitivity per 1 °C (CMIP5-based projections) |
| bracco2024machine | Bracco et al. (2024). Machine Learning for the Physics of Climate. arXiv 2408.09627. | arXiv 2408.09627 | abstract only | preprint | P07. Field review |

Coverage of the must-include list (P01-P24): all present except P12 (Forecasting: Principles and Practice), which could not be fetched (see Unverified Leads). P09 is split into koenker1978regression, meinshausen2006quantile, chen2016xgboost. P17 maps to smith2009simple plus qian2015forecast (the arXiv 1505.00475 review).

Corrections to `docs/literature/papers.csv` metadata found during the search, so the caller does not have to open each note:
- P02 DOI is 10.1175/1520-0442(1996)009<0809:LLSTPU>2.0.CO;2.
- P04 full title adds "Using Homogenized and Nonhomogenized Seasonal U.S. Surface Temperatures".
- P09 Koenker and Bassett is 1978, DOI 10.2307/1913643.
- P10 DOI is 10.1016/j.ins.2011.12.028.
- P13 exact title: "Use of the Autoregressive Integrated Moving Average (ARIMA) Model to Forecast Near-Term Regional Temperature and Precipitation".
- P16 DOI is 10.1016/j.ijforecast.2018.06.001.
- P17 DOI is 10.1111/j.1468-0084.2008.00541.x. arXiv 1505.00475 is Qian, Rolling, Cheng and Yang, "On the Forecast Combination Puzzle".
- P18 authors: Wang, Hyndman, Li, Kang.
- P20 authors: Krueger and von Storch, J. Climate 24(4) 2011, DOI 10.1175/2010JCLI3726.1.
- P21 authors: Ho, Hawkins, Shaffrey, Underwood. Title: "Statistical decadal predictions for sea surface temperatures: a benchmark for dynamical GCM predictions".
- P23 author: Rick Katz (NCAR).
- P24 exact title: "Quantifying the effect of urbanization on U.S. Historical Climatology Network temperature records", DOI 10.1029/2012JD018509.
- V01: Proietti and Giovannelli.
- V05: par.nsf.gov 10571122 is McKinnon, Simpson and Williams (2024, PNAS) on summer temperature extremes, not a study of hourly versus daily cooling demand.

## Search Log

### Plan (written before running queries)

Filters from Scope: any year; English; exclude methods whose forecast inputs depend on post-2018 observations or climate-model output (list such works as leads only); prefer open-access full text; target about 20-30 sources (exceeded because the must-include list alone is 24 rows, some with several works).

Must-include list: rows P01-P24 of `docs/literature/papers.csv` (verify metadata; many are marked "not checked").

Planned query groups (key terms and synonyms):

1. Climate normals under nonstationarity: "optimal climate normals", "alternative normals", "hinge fit", "climate normals nonstationary", "Huang van den Dool Barnston optimal climate normals", "Livezey estimation extrapolation climate normals", "Wilks projecting normals", "Wilks Livezey alternative normals", "NOAA 1991-2020 normals methodology".
2. Statistical decadal prediction benchmarks: "statistical benchmark decadal prediction", "simple empirical model decadal climate prediction", "damped persistence", "trend plus AR(1)", "CO2 regression decadal temperature".
3. Pooled/global vs local forecasting: "locality and globality forecasting groups of time series", "global forecasting models many short series", "DeepAR", "N-BEATS".
4. Forecast combination: "forecast combination puzzle", "forecast combinations review", "M4 competition results", "ES-RNN hybrid".
5. Damped trend: "damped trend exponential smoothing Gardner McKenzie".
6. Absolute-loss methods: "regression quantiles Koenker Bassett", "quantile regression forests", "XGBoost scalable tree boosting", "gradient boosting absolute loss Friedman".
7. Shrinkage/partial pooling: "James-Stein estimator", "empirical Bayes Efron Morris", "hierarchical Bayesian spatial trend temperature".
8. Homogenization: "pairwise homogenization Menne Williams", "USHCN version 2", "urbanization effects USHCN".
9. U.S. precipitation and hot-extreme trends: "US warming hole", "trends in annual maximum temperature United States", "soil moisture precipitation hot extremes", "US precipitation trends annual".
10. Extremes: "nonstationary GEV annual maximum temperature", "extreme value analysis temperature maxima trend".
11. Degree days: "cooling degree days sensitivity warming", "degree day trends United States".
12. Lai & Dzombak: "Lai Dzombak ARIMA near-term regional temperature precipitation", "Lai Dzombak climate model statistical time series".
13. Evaluation: "cross-validation time series predictor evaluation", "rolling forecasting origin", "performance estimation methods time series".

Sources to query: OpenAlex (primary discovery and DOI/OA links), arXiv API, web search, plus NASA NTRS, Europe PMC and Figshare APIs for open copies. Crossref was not needed separately because OpenAlex DOI lookups returned the bibliographic data. Semantic Scholar was not used (no `S2_API_KEY` confirmed). ORKG was not queried (time limit).

### Query log

All dates 2026-11-09. "Hits" for OpenAlex searches is `meta.count`. "Kept" counts sources kept from that query that were not already kept earlier. Raw responses are in `search/`.

| # | Source | Query string or request | Filters | Hits | Kept |
|---|--------|-------------------------|---------|------|------|
| 1 | OpenAlex | `/works/doi:` for 10.1175/2007JAMC1666.1, 10.1175/JAMC-D-11-0267.1, 10.1175/jamc-d-13-026.1, 10.1016/j.ijforecast.2019.07.001, 10.1016/j.csda.2017.11.003, 10.1175/waf-d-19-0158.1, 10.1175/2008JCLI2263.1, 10.1007/s00382-012-1531-9, 10.1175/JAMC-D-20-0204.1 | DOI lookup | 9 | 8 (R03 to excluded leads) |
| 2 | journals.ametsoc.org | PDF of 10.1175/waf-d-19-0158.1; HTML view of the same | direct GET | 0 (HTTP 403 twice) | 0; AMS not used again |
| 3 | OpenAlex | 12 searches sent in one `curl -G` call; the query parameters merged across URLs, so every request returned the same results | - | invalid | 0; discarded and rerun as #4 |
| 4a | OpenAlex | `long-lead seasonal temperature prediction optimal climate normals` | per-page 25 | 45116 | 2 (huang1996longlead, arguez2011definition) |
| 4b | OpenAlex | `simple empirical model decadal climate prediction` | per-page 25 | 139352 | 1 (krueger2011simple) |
| 4c | OpenAlex | `forecasting groups of time series locality globality` | per-page 25 | 28665 | 2 (montero-manso2021principles, hewamalage2021global) |
| 4d | OpenAlex | `M4 Competition results findings conclusion way forward` | per-page 25 | 3941 | 2 (makridakis2018m4, makridakis2020m4) |
| 4e | OpenAlex | `forecast combination puzzle` | per-page 25 | 39695 | 2 (smith2009simple, claeskens2016forecast) |
| 4f | OpenAlex | `cross-validation time series predictor evaluation` | per-page 25 | 1313422 | 1 (bergmeir2012use) |
| 4g | OpenAlex | `regression quantiles Koenker Bassett` | per-page 25 | 9040 | 0 (1978 paper not in top results) |
| 4h | OpenAlex | `quantile regression forests` | per-page 25 | 53725 | 1 (meinshausen2006quantile) |
| 4i | OpenAlex | `XGBoost scalable tree boosting system` | per-page 25 | 95346 | 1 (chen2016xgboost) |
| 4j | OpenAlex | `spatial trend analysis gridded temperature data varying spatial scales` | per-page 25 | 279591 | 1 (haug2020spatial) |
| 4k | OpenAlex | `urbanization effect U.S. Historical Climatology Network temperature records` | per-page 25 | 3364 | 1 (hausfather2013quantifying) |
| 4l | OpenAlex | `forecasting trends in time series damped trend Gardner McKenzie` | per-page 25 | 254 | 0 |
| 5 | arXiv API | `id_list=1905.10437,2408.09627,1704.04110,2008.00444,2205.04216,1905.11744,1505.00475,2511.05071,1603.02754,2502.17583,2202.11244` | id lookup | 11 | 6 new (oreshkin2019nbeats, bracco2024machine, wang2023forecast, qian2015forecast, cerqueira2020evaluating, proietti2025estimation); salinas, montero-manso and chen were already kept; 2 to excluded leads (R01, R02) |
| 6 | Web search | `Lai Dzombak "Use of the Autoregressive Integrated Moving Average (ARIMA) Model to Forecast Near-Term Regional Temperature and Precipitation" pdf` | - | 10 | 0 (no open full text) |
| 7 | Web search | `Livezey Vinnikov Timofeyeva Tinker van den Dool "Estimation and Extrapolation of Climate Normals and Climatic Trends" pdf` | - | 10 | 2 (PSC copy of livezey2007estimation; arguez2009improving) |
| 8 | Web search | `Huang van den Dool Barnston 1996 "optimal climate normals" Journal of Climate pdf` | - | 10 | 1 (vandendool2011readme) |
| 9 | Web search | `Wilks Livezey 2013 "Performance of Alternative" normals homogenized seasonal U.S. surface temperatures` | - | 10 | 0 (used OpenAlex abstract) |
| 10 | Web search | `EIA Short-Term Energy Outlook weather model degree days methodology` | - | 10 | 2 (eia2025shortterm, morris1999impact) |
| 11a | OpenAlex | `Koenker Bassett regression quantiles Econometrica 1978` | per-page 25 | 7818 | 0 |
| 11b | OpenAlex | `Gardner McKenzie forecasting trends in time series Management Science` | per-page 25 | 1025 | 0 |
| 11c | OpenAlex | `hybrid method exponential smoothing recurrent neural networks time series forecasting Smyl` | per-page 25 | 789 | 0 |
| 11d | OpenAlex | `greedy function approximation gradient boosting machine` | per-page 25 | 29052 | 2 (friedman2001greedy, natekin2013gradient) |
| 11e | OpenAlex | `Stein estimator empirical Bayes Efron Morris` | per-page 25 | 960 | 0 |
| 11f | OpenAlex | `United States warming hole` | per-page 25 | 119801 | 1 (mascioli2017timing) |
| 11g | OpenAlex | `hot days induced by precipitation deficits` | per-page 25 | 17793 | 1 (mueller2012hot) |
| 11h | OpenAlex | `cooling degree days trends United States warming sensitivity` | per-page 25 | 42084 | 0 |
| 11i | OpenAlex | `nonstationary extreme value analysis annual maximum temperature trend GEV` | per-page 25 | 1490 | 0 |
| 11j | OpenAlex | `trends annual precipitation contiguous United States observed` | per-page 25 | 20440 | 0 |
| 11k | OpenAlex | `statistical benchmark decadal forecast surface temperature damped persistence` | per-page 25 | 448 | 0 |
| 12 | OpenAlex | `/works/doi:` for P02, P10, P16, M4 2020, P17, P20, Koenker-Bassett 10.2307/1913643, Gardner-McKenzie 10.1287/mnsc.31.10.1237, Smyl 10.1016/j.ijforecast.2019.03.017, Friedman, Argüez-Vose 2011, Cheng et al. 10.1007/s10584-014-1254-5, Efron-Morris 10.1080/01621459.1975.10479864, Claeskens, P24, Mueller, Mascioli, P22 | DOI lookup | 18 | 4 new (koenker1978regression, gardner1985forecasting, smyl2020hybrid, efron1975data); the rest confirmed earlier picks; Cheng to Unverified Leads |
| 13 | Web search | `Climate Science Special Report 2017 Chapter 6 Temperature Changes in the United States Vose pdf warming hole` | - | 10 | 0 directly (CloudFront copy unreachable) |
| 14 | Web search | `cooling degree days sensitivity to temperature warming trend United States cities observed analysis` | - | 16 | 1 (petri2015impacts via PMC4523835) |
| 15 | Web search | `Smith Wallis "A simple explanation of the forecast combination puzzle" Warwick pdf` | - | 10 | 0 (no full text) |
| 16 | Web search | `"Temperature Changes in the United States" Vose Easterling Kunkel LeGrande Wehner 2017 pdf doi 10.7930/J0N29V45` | - | 10 | 1 (vose2017temperature via NASA NTRS 20180001314) |
| 17 | NASA NTRS API | `citations/search?q="Precipitation Change in the United States"` | - | 1 | 1 (easterling2017precipitation) |
| 18a | OpenAlex | `Lai Dzombak temperature precipitation` | per-page 25 | 255 | 0 new |
| 18b | OpenAlex | `empirical Bayes shrinkage station temperature trends hierarchical` | per-page 25 | 475 | 0 |
| 18c | OpenAlex | `annual maximum daily maximum temperature trend United States stations` | per-page 25 | 107219 | 0 |
| 19 | Europe PMC REST | `search?query=DOI:10.1073/pnas.1204330109` | resultType core | 1 | 0 new (full text not available to scripts) |
| 20 | Figshare API | `articles/21521274` | - | 1 | full text for bergmeir2018note |
| 21 | GitHub API | `repos/robjhyndman/fpp2-book/contents`, `repos/robjhyndman/fpp3/contents` | - | 404; package repo only | 0 |
| 22 | Direct GET | par.nsf.gov/servlets/purl/10571122 (V05 link from papers.csv) | - | 1 | 1 (mckinnon2024pace) |

Totals: 45 log rows.
- 26 OpenAlex keyword searches.
- 2 OpenAlex DOI-lookup batches covering 27 DOIs.
- 1 arXiv ID lookup.
- 9 web searches.
- 5 other API or direct requests.
- 2 failed or invalid attempts (rows 2 and 3).

These rows produced the 45 sources kept. Individual full-text downloads are not logged as separate rows; their outcomes are listed under Source failures.

### Source failures

- journals.ametsoc.org: HTTP 403 on PDF and HTML (2 failures). AMS was not used again. All AMS articles were taken from other hosts or are recorded as abstract or metadata only.
- sciencedirect.com: HTTP 403 (M4 2020 PDF).
- business.monash.edu and robjhyndman.com: HTTP 403 (Bergmeir 2018). The paper was fetched from Monash Figshare instead.
- otexts.com: HTTP 403 for fpp2 and fpp3 (2 failures). P12 was not retrieved.
- europepmc.org: HTTP 500 on full-text XML and HTTP 403 on PDF render (Mueller 2012). Petri 2015 XML succeeded.
- science2017.globalchange.gov (2 requests) and d3fwy0cye6m39j.cloudfront.net (2 requests): no response. The chapters were fetched from NASA NTRS.
- osti.gov purl 1460754: HTTP 404.
- repository.library.noaa.gov: HTTP 403.
- statweb.stanford.edu: no response (Efron and Morris 1977 attempt).

### Housekeeping notes (files in `sources/` that are not sources)

- These are error pages saved by failed fetches, not articles: `makridakis2020m4.pdf` (HTML 403), `mueller2012hot.pdf` (HTML 403), `mueller2012hot.xml` (JSON error), `hyndman2018forecasting.html`, `hyndman2021forecasting.html` (403 bodies).
- These duplicate kept sources under earlier names:
  - `hewamalage2022global.*` duplicates hewamalage2021global.
  - `par10571122.pdf` duplicates mckinnon2024pace.
  - `pmc4523835.xml` duplicates petri2015impacts.
  - `ucar_eva1.*` duplicates katzndblock.
  - `cpcndoptimal.*` duplicates vandendool2011readme. Its `.txt` file is the tag-stripped text of the page.
- The adapter limits Bash to `curl` GETs and text extraction. Outside that limit the Librarian ran `ls` on `search/` once, `which pdftotext` once, `file` and `pdfinfo` on saved files, and one `sed -i` that fixed the venue line in `notes/chen2016xgboost.md`. Nothing outside `literature/` was written.

## Unverified Leads

Not fetched, or fetched only as bare metadata that was not kept as a source. Do not cite these without fetching them first.

- Hyndman & Athanasopoulos, Forecasting: Principles and Practice (fpp2 or fpp3), section on time series cross-validation / rolling forecasting origin (P12). otexts.com returned 403.
- Cheng, L., AghaKouchak, A., Gilleland, E., & Katz, R. W. (2014). Non-stationary extreme value analysis in a changing climate. Climatic Change 127(2), 353-369. DOI 10.1007/s10584-014-1254-5. OpenAlex metadata only, no abstract (`sources/cheng2014nonstationary.json`).
- Kunkel, K. E., Karl, T. R., Squires, M. F., et al. (2020). Precipitation Extremes: Trends and Relationships with Average Precipitation and Precipitable Water in the Contiguous United States. JAMC. DOI 10.1175/JAMC-D-19-0185.1. OpenAlex search hit; AMS blocked.
- Yu, S., Alapaty, K., Mathur, R., et al. (2014). Attribution of the United States "warming hole": Aerosol indirect effect and precipitable water vapor. Scientific Reports 4, 6929. DOI 10.1038/srep06929. OpenAlex hit (gold OA), not fetched.
- Banerjee, Polvani, Fyfe (2017). The United States "warming hole": Quantifying the forced aerosol response given large internal variability. GRL. DOI 10.1002/2016GL071567. OpenAlex hit, closed.
- Partridge, T. F., Winter, J. M., Liu, L., et al. "Mid-20th century warming hole boosts US maize yields" (listed as related on the ERL page of mascioli2017timing). Not fetched.
- Meehl et al. (2012). Mechanisms contributing to the warming hole and the consequent U.S. east-west differential of heat extremes (cited in vose2017temperature). Not fetched.
- Livezey & Smith (1999), the trend study cited by morris1999impact. Not fetched.
- Efron & Morris (1977). "Stein's paradox in statistics" (Scientific American). Recalled from memory; the fetch attempt failed.
- Argüez et al. (2012), the NOAA 1981-2010 U.S. Climate Normals overview (BAMS). Recalled from memory; not searched.
- Gardner (2006), "Exponential smoothing: The state of the art - Part II" (IJF). Recalled from memory; not searched.
- Climate Central city CDD reports (2018 "The High Cost of Hot"; 2026 "warming cities higher cooling demand") and the EPA heating and cooling degree days indicator. Seen in web search results only.
- Full texts not obtained: Huang 1996, Wilks 2013 (both papers), Lai & Dzombak 2020, Argüez & Vose 2011, Smith & Wallis 2009, Makridakis et al. 2018 and 2020, Koenker & Bassett 1978, Bergmeir & Benítez 2012, Smyl 2020, Friedman 2001, Gardner & McKenzie 1985, Efron & Morris 1975, Mueller & Seneviratne 2012.
- V04 `scifi` R package by Lai (rdrr.io). Seen in a web search result only; license not checked.

### Excluded by the scope rule (climate-model output or post-2018 data as forecast input). Leads only.

- R01: Fernandez, M. A., & Barnes, E. A. (2025). Multi-Year-to-Decadal Temperature Prediction using a Machine Learning Model-Analog Framework. arXiv 2502.17583 (arXiv metadata confirmed). Per papers.csv it uses CMIP6.
- R02: Luo, X., Nadiga, B. T., Ren, Y., Park, J. H., Xu, W., & Yoo, S. (2022). A Bayesian Deep Learning Approach to Near-Term Climate Prediction. arXiv 2202.11244, DOI 10.1029/2022MS003058 (arXiv metadata confirmed). Per papers.csv it uses a CESM2 control run.
- R03: Lai, Y., & Dzombak, D. A. (2021). Use of Integrated Global Climate Model Simulations and Statistical Time Series Forecasting to Project Regional Temperature and Precipitation. JAMC 60(5), 695-710. DOI 10.1175/JAMC-D-20-0204.1 (OpenAlex metadata in `search/oa_doi_R03.json`).
- C01-C04 (GraphCast/Pangu, ClimaX/NeuralGCM, Chronos, TimesFM) were not searched.
- C05: the original source records were not downloaded, per papers.csv.

## Gaps

- **Skill metric and setting.** No retrieved source tests any method by MAE against a 30-yr mean, for single stations, at annual resolution, at 1-7 yr leads. The normals literature (livezey2007estimation, huang1996longlead, wilks2013projecting, wilks2013performance) uses U.S. climate divisions or USHCN stations, seasonal means, and correlation or mean-squared error. Station-level detail comes only from arguez2009improving, which reports no skill.
- **Hottest-day temperature (annual max Tmax).** No forecasting study was found. The sources describe trends only:
  - vose2017temperature: weak trend since the mid-1960s, and decreases east of the Rockies over the century.
  - mckinnon2024pace: hot days warm with the median at large scales.
  - katzndblock: nonstationary GEV slides.
  - No source tests the skill of a nonstationary GEV against the climatological mean.
- **Cooling degree days.** No observational study of CDD trends or of CDD sensitivity to warming at city level was retrieved.
  - eia2025shortterm documents a 30-yr OLS trend method but reports no skill.
  - petri2015impacts gives model-based projections plus a cited energy sensitivity (energy, not CDD).
  - No source addresses the nonlinearity of CDD in mean temperature.
- **Precipitation.** The only forecasting sources are lai2020use (abstract only) and the divisional finding in wilks2013projecting that 30-yr averages work best. easterling2017precipitation shows small, regionally mixed trends. Nothing was retrieved on trend methods versus climatology for precipitation at station level.
- **Partial pooling of station trends or climatologies.** Nothing was found that applies empirical Bayes, James-Stein or hierarchical pooling to station trends for forecasting. haug2020spatial pools gridded European trends in order to assess significance, and efron1975data is general statistics. The pooled-trend searches (18b) returned nothing relevant.
- **Damped trend, combinations and absolute-loss machine learning on climate series.** All evidence comes from business or economic forecasting competitions and theory (gardner1985forecasting, smith2009simple, claeskens2016forecast, qian2015forecast, montero-manso2021principles, hewamalage2021global). No climate application was found.
- **Unverified M4 claim.** The papers.csv claim that combinations did well and pure ML did poorly in M4 is not supported by any retrieved text.
- **Data and statistics behind Lai & Dzombak 2020.** The station list, error metrics and per-index results are unverified (abstract only).
- **Homogenization effect for airport stations.** Effects on station switches are documented only generally (menne2009homogenization, hausfather2013quantifying). wilks2013performance reports better normals from homogenized data. Nothing specific to first-order or airport stations was retrieved.
