# montero-manso2021principles

*   **Citation:** Montero-Manso, P., & Hyndman, R. J. (2021). Principles and algorithms for forecasting groups of time series: Locality and globality. International Journal of Forecasting 37(4), 1632-1653.
*   **Identifier:** DOI 10.1016/j.ijforecast.2021.03.004; arXiv 2008.00444; OpenAlex W3046229894 — https://arxiv.org/abs/2008.00444
*   **Retrieved:** 2026-11-09
*   **Access:** full text (arXiv v3, `sources/montero-manso2021principles.pdf`, `sources/montero-manso2021principles.txt`)
*   **Type:** peer-reviewed article (quotes taken from the arXiv v3 preprint)
*   **Relevance:** P14. Theory and evidence that a single global (pooled) model fit across many series can match or beat per-series local models, including simple global linear autoregressions.

## Contribution

*   **Research problem:** When and why global models (one function for all series) outperform local models (one per series).
*   **Method:** Formal equivalence result, generalization bounds, and an empirical study with global linear models, deep networks and polynomials.
*   **Data or materials:** Benchmark forecasting datasets (details in paper).
*   **Main result:** Global methods are not more restrictive than local ones; global linear models are competitive with far fewer parameters.

## Quotes

1.  "We show that global methods are not more restrictive than local methods for time series forecasting, a result which does not apply to sets of regression problems in general. Global and local methods can produce the same forecasts without any assumptions about similarity of the series in the set" (abstract)
    *   Supports: global models can reproduce local forecasts without assuming series similarity.
2.  "We find that the complexity of local methods grows with the size of the set while it remains constant for global methods." (abstract)
    *   Supports: generalization-bound argument favoring global models as the number of series grows.
3.  "In particular, global linear models show an unreasonable effectiveness, providing competitive forecasting accuracy with far fewer parameters than the simplest of local methods." (abstract)
    *   Supports: pooled linear autoregressions were competitive in the benchmarks.
4.  "Temporal dependence and the short length of the series makes time series forecasting a notoriously difficult problem. Individual time series cannot be modeled in a data-driven way because even basic models (e.g., linear) will suffer from over-fitting." (section 1)
    *   Supports: the authors motivate pooling by over-fitting risk on short individual series.

## Not Covered

*   Climate or weather series; annual data at multi-year leads; MAE against a climatological baseline.
