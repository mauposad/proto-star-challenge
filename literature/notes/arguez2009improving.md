# arguez2009improving

*   **Citation:** Arguez, A., & Vose, R. (2009, approx.). On Improving NOAA's Climate Normals: An Introduction to 'Optimal Normals' of Temperature. AMS conference paper 9B.3 (conference extended abstract; PDF created 2008-12-18; text refers to a 2009 release).
*   **Identifier:** URL — https://ams.confex.com/ams/pdfpapers/146498.pdf
*   **Retrieved:** 2026-11-09
*   **Access:** full text (`sources/arguez2009improving.pdf`, `sources/arguez2009improving.txt`)
*   **Type:** other (conference extended abstract, not peer reviewed)
*   **Relevance:** NOAA NCDC's station-level implementation of Annual Updates, OCN with station-specific N, and Hinge Fit on homogenized COOP data; closest to station-level (not divisional) normals.

## Contribution

*   **Research problem:** Official 30-yr normals updated every 10 years are unrepresentative of current climate under nonstationarity.
*   **Method:** Station-level Annual Updates, OCN with station-specific N (from lag-1 autocorrelation and trend, following Livezey et al. 2007), and Hinge Fit at 1975.
*   **Data or materials:** COOP station monthly max, min, mean temperature, QC'd and homogenized with pairwise comparisons; 1940-2007 for parameter estimation.
*   **Main result:** Optimal N is negatively correlated with trend strength (-0.78 for January Tmin; -0.35 for July Tmax).

## Quotes

1.  "Climate Normals are calculated retrospectively, but utilized prospectively. However, mounting evidence suggests that global climate statistics are non-stationary, calling into question the predictive skill of traditional climate normals." (section 1)
    *   Supports: the authors question the predictive skill of traditional normals under nonstationarity.
2.  "Livezey et al. (2007) contend that the appropriate N for OCN should be station-specific based on various factors, namely the residual lag-1 (g) autocorrelation and the linear trend (β). We follow the latter approach." (section 4)
    *   Supports: NCDC computed a station-specific OCN window from lag-1 autocorrelation and trend.
3.  "The correlation between N and β is -0.78, quantifying the intuitive notion that strong linear trends require shorter averaging periods." (section 4, January minimum temperature)
    *   Supports: stronger trends were associated with shorter optimal windows for January Tmin.
4.  "For July maximum temperatures, there is much less spatial correlation present, although there is a tendency for smaller N in the West, consistent with the changes seen in Figure 1. Here, the correlation between N and β is a more modest -0.35." (section 4)
    *   Supports: for July Tmax the N-trend relationship was weaker.
5.  "The hinge point is set to 1975. Prior to 1975, the Hinge Fit is constrained to be a constant value, and after 1975, the Hinge Fit is a straight line with constant slope." (section 5)
    *   Supports: NCDC's hinge implementation uses a 1975 hinge point.
6.  "In addition, time series homogenization is accomplished by using pairwise comparisons to detect undocumented changepoints." (section 2)
    *   Supports: the station data were homogenized with pairwise comparisons.

## Not Covered

*   Any out-of-sample skill comparison of the three methods; precipitation, annual maxima, or degree days.
