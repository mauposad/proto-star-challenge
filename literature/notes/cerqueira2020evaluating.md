# cerqueira2020evaluating

*   **Citation:** Cerqueira, V., Torgo, L., & Mozetič, I. (2020). Evaluating time series forecasting models: An empirical study on performance estimation methods. Machine Learning 109, 1997-2028 (journal ref per arXiv metadata).
*   **Identifier:** DOI 10.1007/s10994-020-05910-7; arXiv 1905.11744 — https://arxiv.org/abs/1905.11744
*   **Retrieved:** 2026-11-09
*   **Access:** full text (arXiv v1, `sources/cerqueira2020evaluating.pdf`, `sources/cerqueira2020evaluating.txt`)
*   **Type:** peer-reviewed article (quotes from arXiv v1 preprint)
*   **Relevance:** P19. Out-of-sample methods that keep temporal order gave the most accurate performance estimates on real (nonstationary) series.

## Contribution

*   **Research problem:** Which performance estimation methods suit time series forecasting.
*   **Method:** Compare CV variants and out-of-sample approaches.
*   **Data or materials:** 62 real-world series and three synthetic series.
*   **Main result:** CV is fine for stationary series; for real-world nonstationary series, order-preserving out-of-sample methods are most accurate.

## Quotes

1.  "We compare different variants of cross-validation and of out-of-sample approaches using two case studies: One with 62 real-world time series and another with three synthetic time series." (abstract)
    *   Supports: study design.
2.  "In particular, empirical experiments suggest that cross-validation approaches can be applied to stationary time series. However, in real-world scenarios, when different sources of non-stationary variation are at play, the most accurate estimates are produced by out-of-sample methods that preserve the temporal order of observations." (abstract)
    *   Supports: order-preserving out-of-sample evaluation was most accurate for nonstationary real series.

## Not Covered

*   Climate data; the specific "repeated" out-of-sample variant named in papers.csv is not named in the quoted abstract.
