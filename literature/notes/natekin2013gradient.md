# natekin2013gradient

*   **Citation:** Natekin, A., & Knoll, A. (2013). Gradient boosting machines, a tutorial. Frontiers in Neurorobotics 7, Article 21.
*   **Identifier:** DOI 10.3389/fnbot.2013.00021; OpenAlex W2088794999 — https://doi.org/10.3389/fnbot.2013.00021
*   **Retrieved:** 2026-11-09
*   **Access:** full text (`sources/natekin2013gradient.pdf`, `sources/natekin2013gradient.txt`)
*   **Type:** peer-reviewed article (tutorial)
*   **Relevance:** States that L1 loss targets the conditional median and that quantile loss at alpha = 0.5 equals L1; supports median/MAE-targeted boosting.

## Contribution

*   **Research problem:** Tutorial on gradient boosting machines.
*   **Method:** Exposition of GBM loss families (L2, L1, Huber, quantile, etc.) with examples.
*   **Data or materials:** Illustrative and robotics (EMG) examples.
*   **Main result:** not stated (tutorial).

## Quotes

1.  "Another example is the absolute L1 -loss, denoted as the “Laplacian” loss function. The L1 -loss corresponds to the median of the conditional distribution, thus considered as the robust regression loss." (section 3.1, p. 4)
    *   Supports: L1 loss targets the conditional median.
2.  "It may be of particular interest in tasks where the response variable has long-tail error distribution." (section 3.1, p. 4)
    *   Supports: L1 loss suggested for long-tailed errors.
3.  "One can note that when α = 0.5, this would coincide with the L1 loss, thus resulting in the conditional median." (section 3.1, p. 4, on the quantile loss)
    *   Supports: quantile loss at 0.5 equals L1 loss.

## Not Covered

*   Forecasting or climate data; empirical comparison of loss functions.
