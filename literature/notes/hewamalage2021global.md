# hewamalage2021global

*   **Citation:** Hewamalage, H., Bergmeir, C., & Bandara, K. (2021/2022). Global models for time series forecasting: A Simulation study. Pattern Recognition 124, 108441. (OpenAlex lists publication year 2021.)
*   **Identifier:** DOI 10.1016/j.patcog.2021.108441; arXiv 2012.12485; OpenAlex W3116607345 — https://arxiv.org/abs/2012.12485
*   **Retrieved:** 2026-11-09
*   **Access:** full text (arXiv v3, `sources/hewamalage2021global.pdf`, `sources/hewamalage2021global.txt`; an identical earlier download is at `sources/hewamalage2022global.*`)
*   **Type:** peer-reviewed article (quotes taken from the arXiv v3 preprint)
*   **Relevance:** Simulation evidence on when global models (pooled regression, LightGBM, RNN) beat local univariate benchmarks, including for short series.

## Contribution

*   **Research problem:** Under which circumstances global forecasting models beat univariate benchmarks.
*   **Method:** Simulated datasets from AR, seasonal AR, and nonlinear DGPs with controlled heterogeneity, length and count; global RNN, FFNN, pooled regression, LGBM vs. univariate methods.
*   **Data or materials:** Simulated series.
*   **Main result:** Global nonlinear models (RNNs, LGBMs) are competitive for short series, heterogeneous datasets, and minimal prior knowledge.

## Quotes

1.  "it still remains unclear under which circumstances global forecasting models can outperform the univariate benchmarks, especially along the dimensions of the homogeneity/heterogeneity of series, the complexity of patterns in the series, the complexity of forecasting models, and the lengths/number of series." (abstract)
    *   Supports: the study's question is when global models beat univariate benchmarks.
2.  "Our experiments demonstrate that when trained as global forecasting models, techniques such as RNNs and LGBMs, which have complex non-linear modelling capabilities, are competitive methods in general under challenging forecasting scenarios such as series having short lengths, datasets with heterogeneous series and having minimal prior knowledge of the patterns of the series." (abstract)
    *   Supports: global RNNs/LGBMs were competitive for short and heterogeneous series in simulations.

## Not Covered

*   Real climate data; the absolute-loss setting; multi-year leads on annual data.
