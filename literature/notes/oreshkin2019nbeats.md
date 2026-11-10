# oreshkin2019nbeats

*   **Citation:** Oreshkin, B. N., Carpov, D., Chapados, N., & Bengio, Y. (2019/2020). N-BEATS: Neural basis expansion analysis for interpretable time series forecasting. arXiv:1905.10437v4; header states "Published as a conference paper at ICLR 2020".
*   **Identifier:** arXiv 1905.10437 — https://arxiv.org/abs/1905.10437
*   **Retrieved:** 2026-11-09
*   **Access:** full text (`sources/oreshkin2019nbeats.pdf`, `sources/oreshkin2019nbeats.txt`)
*   **Type:** preprint (arXiv version of an ICLR 2020 conference paper; conference publication not independently verified)
*   **Relevance:** P05. Deep univariate architecture benchmarked on M3, M4, TOURISM.

## Contribution

*   **Research problem:** Univariate point forecasting with deep learning.
*   **Method:** Deep stack of fully connected layers with backward and forward residual links.
*   **Data or materials:** M3, M4, TOURISM competition datasets.
*   **Main result:** 11% better than a statistical benchmark and 3% better than the M4 winner.

## Quotes

1.  "We propose a deep neural architecture based on backward and forward residual links and a very deep stack of fully-connected layers." (abstract)
    *   Supports: architecture description.
2.  "We test the proposed architecture on several well-known datasets, including M3, M4 and TOURISM competition datasets containing time series from diverse domains. We demonstrate state-of-the-art performance for two configurations of N-BEATS for all the datasets, improving forecast accuracy by 11% over a statistical benchmark and by 3% over last year’s winner of the M4 competition, a domain-adjusted hand-crafted hybrid between neural network and statistical time series models." (abstract)
    *   Supports: reported gains on M3/M4/TOURISM vs. a statistical benchmark and the M4 winner.

## Not Covered

*   Performance on short annual climate series or at 1-7 yr leads; data requirements for training.
