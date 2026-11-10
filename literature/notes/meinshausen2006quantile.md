# meinshausen2006quantile

*   **Citation:** Meinshausen, N. (2006). Quantile Regression Forests. Journal of Machine Learning Research 7, 983-999.
*   **Identifier:** JMLR v7 (OpenAlex W1573647811) — https://www.jmlr.org/papers/volume7/meinshausen06a/meinshausen06a.pdf
*   **Retrieved:** 2026-11-09
*   **Access:** full text (`sources/meinshausen2006quantile.pdf`, `sources/meinshausen2006quantile.txt`)
*   **Type:** peer-reviewed article
*   **Relevance:** P09. Random forests generalized to estimate conditional quantiles (including the median, the MAE-optimal point forecast).

## Contribution

*   **Research problem:** Estimate the full conditional distribution, not only the mean.
*   **Method:** Quantile regression forests (generalization of random forests).
*   **Data or materials:** Numerical examples.
*   **Main result:** Consistent algorithm; competitive predictive power in examples.

## Quotes

1.  "It is shown here that random forests provide information about the full conditional distribution of the response variable, not only about the conditional mean. Conditional quantiles can be inferred with quantile regression forests, a generalisation of random forests." (abstract)
    *   Supports: QRF estimates conditional quantiles.
2.  "The algorithm is shown to be consistent. Numerical examples suggest that the algorithm is competitive in terms of predictive power." (abstract)
    *   Supports: consistency and competitive predictive power in the examples.
3.  "The conditional mean minimizes the expected squared error loss," (section 1)
    *   Supports: the paper notes standard regression targets the squared-error-optimal mean.

## Not Covered

*   Time series or climate forecasting; extrapolation beyond the training range (forests do not extrapolate trends; not discussed in quoted text).
