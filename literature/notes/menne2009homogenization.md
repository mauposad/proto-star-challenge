# menne2009homogenization

*   **Citation:** Menne, M. J., & Williams, C. N., Jr. (2009). Homogenization of Temperature Series via Pairwise Comparisons. Journal of Climate 22(7), 1700-1717. (OpenAlex lists publication year 2008, likely online-first.)
*   **Identifier:** DOI 10.1175/2008JCLI2263.1; OpenAlex W2153133730 — https://doi.org/10.1175/2008JCLI2263.1
*   **Retrieved:** 2026-11-09
*   **Access:** full text (publisher PDF hosted by NOAA NCEI, https://www.ncei.noaa.gov/pub/data/ushcn/v2/monthly/menne-williams2009.pdf; `sources/menne2009homogenization.pdf`, `sources/menne2009homogenization.txt`)
*   **Type:** peer-reviewed article
*   **Relevance:** P15. Pairwise homogenization algorithm (basis of USHCN v2) for detecting and adjusting station artifacts such as relocations and instrument changes.

## Contribution

*   **Research problem:** Detect and adjust undocumented artificial shifts in station temperature series.
*   **Method:** Pairwise difference series with neighbors; changepoint detection; attribution to the responsible station; use of station history; adjustment.
*   **Data or materials:** Simulated scenarios; U.S. monthly temperature data.
*   **Main result:** Robust detection with a lower false-alarm rate than reference-series approaches.

## Quotes

1.  "The algorithm works by forming pairwise difference series between serial monthly temperature values from a network of observing stations. Each difference series is then evaluated for undocumented shifts, and the station series responsible for such breaks is identified automatically." (abstract)
    *   Supports: method uses neighbor difference series to find and attribute breaks.
2.  "Moreover, the approach is shown to yield a lower false-alarm rate for undocumented changepoint detection relative to the more common use of a reference series." (abstract)
    *   Supports: lower false alarms than reference-series methods.
3.  "The relocation, replacement, or recalibration of an instrument, for example, can lead to an abrupt shift in time-ordered observations that is unrelated to any real change in climate." (section 1)
    *   Supports: station changes can create artificial shifts.

## Not Covered

*   Daily Tmax extremes, precipitation, or degree days; forecasting skill impact of homogenization (see wilks2013performance for that).
