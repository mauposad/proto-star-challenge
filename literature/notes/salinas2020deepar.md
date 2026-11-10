# salinas2020deepar

*   **Citation:** Salinas, D., Flunkert, V., Gasthaus, J., & Januschowski, T. (2020). DeepAR: Probabilistic forecasting with autoregressive recurrent networks. International Journal of Forecasting 36(3), 1181-1191. (arXiv 1704.04110 lists the first three authors.)
*   **Identifier:** DOI 10.1016/j.ijforecast.2019.07.001; arXiv 1704.04110; OpenAlex W2607045400 — https://arxiv.org/abs/1704.04110
*   **Retrieved:** 2026-11-09
*   **Access:** full text (arXiv v3, `sources/salinas2020deepar.pdf`, `sources/salinas2020deepar.txt`)
*   **Type:** peer-reviewed article (quotes taken from the arXiv v3 preprint)
*   **Relevance:** P08. A global autoregressive RNN trained across many related series.

## Contribution

*   **Research problem:** Probabilistic forecasting for large numbers of related time series.
*   **Method:** Autoregressive recurrent network trained on many related series.
*   **Data or materials:** Several real-world datasets (retail-type demand, etc.).
*   **Main result:** Around 15% accuracy improvements over state-of-the-art methods on the evaluated datasets.

## Quotes

1.  "we propose DeepAR, a methodology for producing accurate probabilistic forecasts, based on training an auto-regressive recurrent network model on a large number of related time series." (abstract)
    *   Supports: DeepAR is a single model trained across many related series.
2.  "We show through extensive empirical evaluation on several real-world forecasting data sets accuracy improvements of around 15% compared to state-of-the-art methods." (abstract)
    *   Supports: reported ~15% improvement on the authors' datasets.
3.  "In recent years, a new type of forecasting problem has become increasingly important in many applications. Instead of needing to predict individual or a small number of time series, one is faced with forecasting thousands or millions of related time series." (section 1)
    *   Supports: DeepAR targets settings with very many series.

## Not Covered

*   Short annual series (a few hundred cities with ~decades of annual values); climate data; multi-year leads.
