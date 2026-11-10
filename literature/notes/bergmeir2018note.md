# bergmeir2018note

*   **Citation:** Bergmeir, C., Hyndman, R. J., & Koo, B. (2018). A note on the validity of cross-validation for evaluating autoregressive time series prediction. Computational Statistics & Data Analysis 120, 70-83. Quotes are from the earlier working paper: "A Note on the Validity of Cross-Validation for Evaluating Time Series Prediction", Monash University Department of Econometrics and Business Statistics Working Paper 10/15 (April 2015).
*   **Identifier:** DOI 10.1016/j.csda.2017.11.003; working paper DOI 10.26180/21521274; OpenAlex W2770188460 — https://doi.org/10.26180/21521274
*   **Retrieved:** 2026-11-09
*   **Access:** full text (working paper from Monash Figshare, `sources/bergmeir2018note.pdf`, `sources/bergmeir2018note.txt`)
*   **Type:** peer-reviewed article (quotes from the 2015 working paper version; may differ from the journal version)
*   **Relevance:** P11. Conditions under which K-fold CV is valid for autoregressive ML forecasting.

## Contribution

*   **Research problem:** Whether standard K-fold CV is valid for time series forecasting evaluation.
*   **Method:** Theory plus simulation comparing K-fold CV, out-of-sample evaluation, and non-dependent CV.
*   **Data or materials:** Simulated series.
*   **Main result:** In the usual ML autoregressive setup, K-fold CV is possible and performs favorably in simulations.

## Quotes

1.  "In this paper, we show that the particular setup in which time series forecasting is usually performed using Machine Learning methods renders the use of standard K-fold CV possible." (abstract)
    *   Supports: K-fold CV can be valid in the standard ML autoregressive setup.
2.  "Furthermore, we present a simulation study where we show empirically that K-fold CV performs favorably compared to both OOS evaluation and other time-series-specific techniques such as non-dependent cross-validation." (abstract)
    *   Supports: simulation result favoring K-fold CV.
3.  "when it comes to time series forecasting, because of the inherent serial correlation and potential non-stationarity of the data, its application is not straightforward and often omitted by practitioners in favor of an out-of-sample (OOS) evaluation." (abstract)
    *   Supports: CV is complicated by serial correlation and nonstationarity.

## Not Covered

*   Nonstationary (trending) series validity; the quoted text does not state conditions on residual correlation (the papers.csv summary of conditions was not checked against the journal version).
