# eia2025shortterm

*   **Citation:** U.S. Energy Information Administration (2025). Short-Term Energy Outlook: Weather Forecast (model documentation, last updated October 2025). U.S. Department of Energy.
*   **Identifier:** URL — https://www.eia.gov/analysis/handbook/pdf/STEO%20Weather%20Model.pdf
*   **Retrieved:** 2026-11-09
*   **Access:** full text (`sources/eia2025shortterm.pdf`, `sources/eia2025shortterm.txt`)
*   **Type:** report
*   **Relevance:** P06. Operational degree-day forecasting beyond the first month uses an OLS 30-year trend line on annual HDD and CDD per state.

## Contribution

*   **Research problem:** not stated (method documentation).
*   **Method:** First month from NOAA forecasts; thereafter state-level OLS regressions of annual degree days on time over the previous 30 years; monthly seasonal factors; population weighting.
*   **Data or materials:** NOAA state-level weather history/forecasts; S&P Global population.
*   **Main result:** not stated.

## Quotes

1.  "For the rest of the forecast period, the model first generates state-level regressions using annual degree day data." (section 4, p. 4)
    *   Supports: beyond the first month EIA fits regressions on annual degree days.
2.  "The regressions (using the ordinary least squares method) are a one-variable 30-year trend line represented by the following equation estimated using the previous 30 years of HDD and CDD data:" (section 4, p. 4)
    *   Supports: the regression is an OLS linear trend over the previous 30 years.
3.  "Two equations are generated for each state, one for HDDs and one for CDDs. The equations are then used to create annual HDD and CDD forecasts." (section 4, p. 4)
    *   Supports: separate trend equations for HDD and CDD produce annual forecasts.

## Not Covered

*   Any reported skill of the trend-line method versus a 30-year mean; city or station scale.
