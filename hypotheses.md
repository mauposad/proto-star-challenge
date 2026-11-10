# Hypotheses

Run: `hypothesize-20261109-a`. Background: [research_background.md](research_background.md).

## User hypotheses

### U1: Pooled direct multi-horizon median model

- Status: new
- Author: human (adopted from an earlier assistant review)
- Statement: One model pooled across all cities and trained with an absolute-error (median)
  objective will beat the hand-set pooled trend on mean raw score in lead years 4–7 without
  losing years 1–3. Its training rows come from earlier forecast origins inside each fold (origin
  ≤ cut-off − horizon). Its target is the future value minus the 30-year mean at the origin.
  Its features are the recent-window means minus the 30-year mean, the pooled slope × lead, CDD
  per degree, city variability, data quality, location and horizon. It learns horizon-dependent
  trend damping and window weights.
- Test: a linear quantile regression (q = 0.5) and a gradient-boosted absolute-error model, on
  the ADR 0004 folds, against `trend_level10_15_sensitivity` and `current_best`.

### U2: Equal-weight blend of pooled trend and `current_best`

- Status: new
- Author: human (adopted from an earlier assistant review)
- Statement: Averaging `trend_level10_15_sensitivity` and `current_best` with equal weights acts
  as a damped trend. It will beat the pooled trend in lead years 1–3 and keep most of its
  years 4–7 gain, so its all-years raw score is at least as high.
- Test: per-row mean of the two forecasts, on the ADR 0004 folds.

### U3: Station-segment-aware pooled slope

- Status: new
- Author: human (adopted from an earlier assistant review)
- Statement: Station switches put steps into the 40-year window, and those steps bias the pooled
  within-city slope. Estimating the slope within city × station segment (demeaning per segment
  instead of per city) will change the temperature and CDD skill. The direction is not known in
  advance.
- Test: the same pooled-trend model with segment-level demeaning, on the ADR 0004 folds.

## Round 1

Two independent generators ran on identical inputs, at the human's request: A on the default
model (Opus 5.5), with IDs H1–H10, and B on Fable 5.2, with IDs H11–H20. Each report is filed
verbatim below.

### Generator A (Opus 5.5, default model)

## Background

The task is to raise the official score for annual forecasts of four metrics in 210 mostly-airport U.S. cities over 2019–2025, using data through 2018 only. Each metric's skill is relative MAE against that city's 1989–2018 mean, and the score is the mean of the four skills. The current candidate scores 4.14 / 0.33 / 6.92 (all / years 1–3 / years 4–7), all of it from temperature and CDD. It takes each city's 10/15-year level, adds a non-negative warming slope pooled across cities over 40 years, and gets CDD through each city's CDD-per-degree. Precipitation and hottest day stay on the 30-year mean. Open questions: how to get skill on precipitation and hottest day, the deficit in lead years 1–3, whether station artifacts, daily data or geography carry signal, and whether any gain holds on more than one fold. U1 (pooled direct median model), U2 (equal-weight blend) and U3 (slope fitted within station segments) are already tested: U1 lost in years 4–7, U2 gave up years 4–7 to gain years 1–3, and U3 was within noise. The hypotheses below are alternatives to them.

**Derived from the supplied data (step 7).** These are my own calculations, not claims from any note.
1. **A ceiling for stationary metrics.** For a stationary, serially independent, roughly normal series, an N-year mean has MAE ∝ √(1+1/N). Its expected skill against the 30-year mean is then 1 − √(1+1/N)/√(1+1/30):
   - −3.2 points for N=10, −1.6 for 15, −0.8 for 20, +0.4 for 40, +0.65 for 50;
   - at most +1.6 points with a perfectly known mean.

   So reducing noise alone can earn at most about 1.6 points per stationary metric, or about 0.4 raw-score points.
2. **Precipitation looks stationary over 20–40 years.** The 20-year mean (−1.00 / −0.83, official / 7 cut-offs) and the 40-year mean (+0.71 / +0.07) sit near that line. The 50-year mean (−0.25 / −0.23) falls below it. So the lever left for precipitation is noise reduction without reaching further back in time.
3. **Hottest day hints at an upward drift.** Two variants beat what stationarity predicts: the 20-year mean (+0.09 / −0.55, against −0.8 expected) and the 30-year median (+0.13 / −0.40; with the median's efficiency of about 2/π, about −0.9 expected). Two fall short: the 40-year mean (−0.22 / −0.09, against +0.4) and the 50-year mean (−2.19 / −1.09, against +0.65). This weakly suggests recent hottest days run above the 30-year mean while older ones differ. It is a hint only, given so few folds.
4. **The earlier "trend added to hottest day" test was confounded.** It scored a raw 1.81 against 2.30, but it changed two things at once: an unfloored slope and a 15-year level. By the line above, the 15-year level alone costs about 1.6 hottest-day points, roughly 80% of the observed loss of about 2.0 points. Whether a trend helps hottest day is therefore still untested.
5. **Some station steps are large.** The region-relative step at a switch reaches about 4 °F (Hayward 1998, Tri-Cities 1998, Denver 1995), against a 0.5 °F average. So the 30-year reference of the 30 cities that switched in 1989–2018 mixes two stations.

Items 2–4 use `pooled_trend_exploration.md`. Item 5 comes from the findings cell of `notebooks/03_agent_daily_eda.ipynb`, which `docs/data.md` refers to; it was not in your supplied list.

**General caveats.**
- The official folds have now been reused about 45 times, so gaps under about 0.5 raw points are noise. "Confirmatory" below means only this: one primary arm, specified before the run, with no tuned parameter.
- Every hypothesis must beat `trend_level10_15_sensitivity`, `current_best` and `thirty_year_mean`. Each primary arm fixes its constants now, so it competes with no more tuning than the candidate had.
- No pretrained models are involved, so benchmark exposure cannot explain any result.

---

### H1: Re-anchoring each city's level to its nearest neighbours will give precipitation and hottest day positive skill and raise temperature skill, most in lead years 1–3. The level is the city's offset from its neighbours' mean anomaly, estimated over its current station segment, plus the neighbours' current anomaly. It works by removing idiosyncratic sampling noise and station-switch steps without reaching back to older, non-stationary years.

*   **Status:** new
*   **Mechanism:**
    - **Model.** Each value is a regional common signal, plus a city offset that is stable within a station segment, plus idiosyncratic noise.
    - **What is wrong now.** The 30-year (or 10/15-year) mean keeps the idiosyncratic noise of only those years. For switching cities it also mixes two stations' offsets.
    - **The fix.** Differencing against the neighbours' mean anomaly removes the common signal. The offset can then be averaged over the whole current segment, which is long and low-noise, while the common signal still comes from the current window.
    - **Weight.** A pooled Efron–Morris weight per metric sets how far to move from the 30-year mean m30 toward the anchored value a: forecast = m30 + B̂·(a − m30), with B̂ = min(1, mean(v_i) / var_i(m30_i − a_i)). Here v_i is the sampling variance of (m30_i − a_i) expected if offsets are stable.
    - **Fixed settings:**
      - Neighbours: k = 5 nearest cities within 500 km (haversine on Lat/Lon), each with at least 20 valid years in the 30-year window.
      - Anomalies: relative to each neighbour's own 30-year mean. Use ratios for precipitation and CDD.
      - Offset: the mean of (city − neighbour anomaly) over the current-segment valid years. At least 10 years are needed; otherwise fall back to the current method.
      - Temperature and CDD: the anchored level replaces the 10/15 level, and the trend is unchanged.
*   **Inspirations:**
    - menne2009homogenization q1, q3 (pairwise difference series isolate station-specific shifts; relocations cause steps). This is from homogenization, outside the forecasting subfield.
    - efron1975data q1, q3 (Stein shrinkage). General statistics, outside the subfield.
    - haug2020spatial q1–q2 (spatial pooling).
    - wilks2013performance q2 (homogenized data improve normals).
    - wilks2013projecting q3 (30-year averages best for precipitation).
    - montero-manso2021principles q4.
    - vandendool2011readme q3 (shrinkage to minimize error).
*   **Prediction:**
    - Precipitation and hottest-day skill each rise by +0.2 to +0.8 points (all leads). Each is above 0 on at least 2 of 3 folds and on the 7-origin mean.
    - Temperature rises by +0.3 to +1.0 points, with a larger relative gain in years 1–3 than in years 4–7.
    - Per-city gains are larger for the 30 switching cities and for cities with few valid years in 1989–2018 (Akron, Louisville, Wheeling, Trenton).
    - B̂ for precipitation falls between 0.3 and 1.
    - Raw score rises by +0.3 to +0.7.
*   **Refuted if:** any of the following.
    - Precipitation and hottest-day skill are ≤ 0 on at least 2 of 3 folds.
    - B̂ ≈ 0 for precipitation and hottest day, meaning offsets are not stable.
    - The placebo-neighbour arm (below) matches the real-neighbour arm.
*   **Rivals:**
    - (a) The whole gain is station-step removal, not noise reduction.
    - (b) It is just a longer effective window, like the 40-year precipitation mean.
    - (c) Local differential change, such as urbanization (hausfather2013quantifying q1), makes offsets drift, so anchoring adds bias.
    - (d) A fold accident.
*   **Discriminating experiment:** four arms on the same folds.
    - A: the city's own long mean over its current segment, with no neighbours.
    - B: neighbour-anchored, offset over all years.
    - C: neighbour-anchored, offset over the current segment (the primary arm).
    - D: placebo, the same as C but with 5 random cities more than 1500 km away.

    How each explanation reads the results:
    - The mechanism predicts C > A and C > D, with D no better than A.
    - Rival (b) predicts A ≈ C.
    - Rival (a) predicts the gain disappears when switching cities are dropped from a diagnostic re-score.
    - Rival (c) predicts B̂ goes to 0, and that the gap between anchored value and m30 grows with the offset-window length.
*   **Closest prior work:** menne2009homogenization detects and adjusts undocumented breaks to build homogenized monthly temperature series for trend analysis. H1 uses the documented `Station Segment`, adjusts no series, uses neighbour differences only to estimate a forecast level, extends this to precipitation, annual max Tmax and CDD, and adds a pooled EB weight. (wilks2013performance used pre-homogenized USHCN data, which is not available here.)
*   **Claim type:** exploratory
*   **Needs:** master only (Lat, Lon, Station Segment), numpy and pandas. About 1.5–2 h. Build precipitation and hottest day first, then temperature; CDD is optional.
*   **Strengths / Costs:** Strength: one mechanism addresses three open questions (precipitation and hottest-day skill, station artifacts, geography) and comes with a placebo control. Cost: the most code of the set; isolated cities fall back to the current method; gains are capped near 1.6 points per stationary metric.

### H2: Adding a non-negative pooled 40-year trend of June–August mean Tmax to the hottest-day 30-year mean, projected from the window's centre, will give hottest day positive skill in years 4–7. Annual maxima shift with the summer median, whereas the annual-mean slope is winter-weighted, and the earlier test of this idea was confounded.

*   **Status:** new
*   **Mechanism:**
    - Hottest days warm at the pace of median summer days (mckinnon2024pace).
    - The 30-year mean is centred about 15 years before the cut-off, so it lags by (15.5 + lead) × the summer slope.
    - U.S. warming is concentrated in winter (morris1999impact q2), so the annual-mean slope overshoots summer.
    - A June–August mean averages about 92 days, so its pooled slope is much less noisy than a slope fitted to the annual maximum.

    Specification:
    - Data: daily values up to the cut-off. Per city and year, the June–August mean Tmax, requiring at least 85 of 92 days.
    - Slope: the same pooled within-city estimator as `trend.py`, over 40 years, floored at 0. The floor is inherited from the candidate, and at the 1980 fold it makes this arm identical to m30.
    - Forecast: hottest = m30 + κ·b_JJA·(year − c30), with κ = 1 fixed and c30 the centre of the 30-year window.
    - Secondary CDD arm: CDD trend = (the city's regression of annual CDD on June–August mean Tavg) × the pooled June–August Tavg slope. The level is unchanged.
*   **Inspirations:**
    - mckinnon2024pace q1, q3 (summer extremes follow the median). Extremes physics, outside the subfield.
    - katzndblock q4 (linear trend in the GEV location with constant shape). Extreme-value theory, outside the subfield.
    - morris1999impact q2.
    - wilks2013performance q3 (trend behaviour differs by season).
    - vose2017temperature q5, q6 (these support the rival).
*   **Prediction:**
    - Hottest-day skill in years 4–7 rises by +0.5 to +1.5 points. It is above 0 on the 1995 and 2011 folds and on the 7-origin mean.
    - The gain grows with lead.
    - The June–August arm does at least as well as the annual-slope arm.
    - The in-fold b_JJA at 2018 is below the annual-mean pooled slope (0.050 °F/yr).
    - The CDD arm lands within ±0.3 points of the candidate.
*   **Refuted if:** any of the following.
    - Hottest-day skill in years 4–7 is ≤ 0 on both the 1995 and 2011 folds.
    - The June–August arm does no better than both the annual-slope arm and the own-max-slope arm.
    - The in-fold ratio of the hottest-day pooled slope to the June–August pooled slope (1975 to cut-off) is below 0.5.
*   **Rivals:**
    - (a) The warmest day has barely trended since the mid-1960s, and land-surface and agricultural effects decouple it from summer means (vose2017temperature q5, q6), so any added trend hurts.
    - (b) Any gain comes from a constant upward shift (the skew account in H3), not from a trend.
    - (c) Siting changes affect Max Tmax.
*   **Discriminating experiment:** four hottest-day arms, all on the 30-year level.
    - m30 alone.
    - m30 plus the annual-temperature slope.
    - m30 plus the hottest day's own pooled slope, floored.
    - m30 plus the June–August slope (the primary arm).

    Also estimate κ̂ = (hottest-day pooled slope) / (June–August pooled slope) inside each fold. How each explanation reads the results:
    - The mechanism predicts κ̂ ≈ 1 and gains that grow with lead.
    - Rival (a) predicts κ̂ ≈ 0.
    - Rival (b) predicts equal gains in years 1–3 and years 4–7, and that a constant shift matches the result.
*   **Closest prior work:** mckinnon2024pace diagnoses 1959–2023 trends in summer-day quantiles at global and hemispheric scale. H2 turns "extremes follow the median" into a forecasting rule at U.S. station scale, using only data before the cut-off. It also differs from the team's rejected variant in three ways: a 30-year rather than 15-year level, the floor, and the slope source.
*   **Claim type:** confirmatory for the primary arm (κ = 1, no tuned parameter); exploratory for the other arms.
*   **Needs:** the daily table, loaded inside the forecaster, filtered to Date ≤ cut-off and passed through `assert_weather_cutoff`. About 1–1.5 h.
*   **Strengths / Costs:** Strength: a parameter-free physical rule for a metric now at zero, which the earlier rejection did not test. Cost: reading daily data inside the forecaster needs explicit leakage discipline, and it can lose up to about 2 hottest-day points if rival (a) holds.

### H3: Shifting skewed metrics from the mean toward the median by a pooled, closed-form skewness correction will raise their MAE skill, because the median minimizes MAE and a pooled shift avoids the variance that made per-city medians lose.

*   **Status:** new
*   **Mechanism:**
    - L1 loss is minimized by the median (natekin2013gradient q1, q3), while window means target squared error (meinshausen2006quantile q3).
    - Annual precipitation is gamma-like, so mean − median ≈ s²/(3·mean).
    - Per-city medians have about π/2 times the variance of the mean, which costs about 0.9 points. A pooled shift keeps the mean's precision.
    - Specification:
      - Precipitation, parameter-free: m30 − s30²/(3·m30).
      - CDD: the trend path − (γ̂/6)·s_resid,i, where γ̂ is the pooled in-fold skewness of standardized detrended residuals.
      - Hottest day: the same rule with its own γ̂. A negative γ̂ means an upward shift.
*   **Inspirations:**
    - natekin2013gradient q1, q3. An ML tutorial, outside the subfield.
    - meinshausen2006quantile q3. ML, outside the subfield.
    - easterling2017precipitation q3.
    - petri2015impacts q4 (CDD ranges widely across cities).
    - koenker1978regression (metadata only, no quote).
*   **Prediction:**
    - The pooled skewness of standardized precipitation anomalies is above 0 in every fold (about 0.2–0.6).
    - Precipitation skill rises by +0.1 to +0.4 points, above 0 on at least 2 of 3 folds.
    - CDD rises by 0 to +0.3 points.
    - The gain is concentrated in the top-CV tercile of cities.
    - Total effect is at most about 0.2 raw points.
*   **Refuted if:** any of the following.
    - Precipitation skill is ≤ 0 on at least 2 of 3 folds.
    - A placebo uniform shift of the same average size, not scaled by CV², does as well.
    - The gain is not larger in the high-CV tercile.
*   **Rivals:**
    - (a) Dry common-mode target periods make any downward shift pay.
    - (b) Regional wetting (easterling2017precipitation q1) makes downward shifts lose regardless of skew.
    - (c) For hottest day, an upward drift (H2) rather than skew.
*   **Discriminating experiment:** compare the primary shift, the placebo uniform shift, a reversed-sign shift, and the per-city 30-year median (already tested: −0.64 / −0.79).
    - The mechanism predicts primary > placebo, gains proportional to CV², and a symmetric loss for the reversed sign.
    - Rival (a) predicts placebo ≈ primary.
    - For hottest day, H3's shift is constant over lead while H2's grows with lead.
*   **Closest prior work:** natekin2013gradient targets the median by fitting an L1-loss model. H3 fits no model and applies a closed-form shift to climatological levels. It also differs from the team's per-city median, which pays the variance cost.
*   **Claim type:** confirmatory for the precipitation primary arm; exploratory for CDD and hottest day.
*   **Needs:** master only, about 45 min.
*   **Strengths / Costs:** Strength: the cheapest test, with no tuned parameter and a direct tie to the metric. Cost: the effect is probably below 3-fold noise, so it needs a paired per-row diagnostic.

### H4: Subtracting from each city's 10/15-year level the shared national residual from the pooled 40-year trend line, averaged over that city's level window, will raise temperature skill in years 4–7. Multi-year common anomalies around the forced trend do not persist, so the current level carries shared recent weather forward as if it were signal.

*   **Status:** new
*   **Mechanism:**
    - Statistical decadal benchmarks get most of their skill from the forced trend (ho2013statistical q2), and model internal variability with short-memory AR (krueger2011simple q3).
    - Gardner–McKenzie advise ignoring components with low persistence (gardner1985forecasting q1).
    - Specification: r_t = the cross-city mean of (y_it − ȳ_i − b(t − t̄_i)) in the 40-year window, using the candidate's floored slope b. Then level_i ← level_i − the mean of r_t over the city's level-window years.
    - Secondary CDD arm: subtract sens_i × r_t.
*   **Inspirations:**
    - ho2013statistical q1, q2. Ocean SST decadal prediction, outside the subfield.
    - krueger2011simple q1, q3.
    - gardner1985forecasting q1. Management science, outside the subfield.
    - huang1996longlead q2, livezey2007estimation q2, mascioli2017timing q3 (these support the rival).
*   **Prediction:**
    - In each fold's record before the cut-off, the autocorrelation of r_t at lags 4–10 averages below 0.15 in absolute value.
    - Temperature skill in years 4–7 rises by +0.3 to +1.0 points on at least 2 of 3 folds and at least 4 of 7 origins.
    - Years 1–3 change by no more than ±0.5.
*   **Refuted if:** temperature skill in years 4–7 falls on at least 2 of 3 folds and on the 7-origin mean, or the autocorrelation of r_t at lags 4–10 is above 0.3.
*   **Rivals:**
    - (a) Decadal internal variability persists (mascioli2017timing q3).
    - (b) The trend curves inside the window, for example the 1975 hinge inside the 1995 window (livezey2007estimation q4). That makes end-of-window residuals positive whether or not anything persists.
    - (c) The effect is one uniform shift per fold, so three folds are three draws. At 1980 the floored slope also turns this into a 40-year mean for the common part.
*   **Discriminating experiment:**
    - (i) Compute the autocorrelation of r_t by lag.
    - (ii) Add an arm that takes residuals from a pooled quadratic fit. Rival (b) predicts the loss disappears there.
    - (iii) A persistence-hit test across every historical origin inside each fold: does the sign of r over the level window predict the sign of r over the next 4–7 years? Rival (a) predicts agreement above 50%. This uses many origins, so it has far more power than the three folds.
*   **Closest prior work:** ho2013statistical uses a CO2-regression trend plus an AR1 residual at SST grid boxes, judged by correlation. H4 uses an empirical linear trend pooled across cities, needs no forcing series, sets the persistence of the common residual to zero, and is judged by MAE at station scale.
*   **Claim type:** exploratory
*   **Needs:** master only; reuses `_window_anomalies` in `trend.py`. About 1 h.
*   **Strengths / Costs:** Strength: isolates a single error component and directly tests whether recent-window skill comes from trend-tracking or from persistence. Cost: low power on three folds, the 1995 fold is confounded by curvature, and the direction of the shift for the 2019–2025 forecast cannot be known in advance.

### H5: Forecasting CDD as its 30-year mean plus the city's CDD-per-degree times the temperature forecast's departure from the temperature 30-year mean will beat the candidate's CDD forecast at all leads. The part of CDD that annual temperature does not explain is stationary noise, and the 10/15-year CDD window averages it over too few years.

*   **Status:** new
*   **Mechanism:**
    - Write CDD = f_i(T) + u.
    - The candidate's level is the recent mean of f(T) plus the recent mean of u. H5's level is the recent mean of f(T), obtained through sens × the temperature departure, plus the 30-year mean of u.
    - If u is stationary, H5 cuts its noise from 1/12.5 to 1/30 of its variance. If u is about half of CDD variance, that is roughly +1 point by the ceiling formula above.
*   **Inspirations:**
    - eia2025shortterm q2, q3.
    - morris1999impact q2 (supports the rival).
    - petri2015impacts q2.
    - smith2009simple q1 and claeskens2016forecast q2 (every extra estimated component adds error). Econometrics, outside the subfield.
    - montero-manso2021principles q4.
*   **Prediction:**
    - The in-fold pooled 40-year slope of u_it = CDD_it − sens_i·T_it is near 0: below 10% of the mean of sens × b_T.
    - CDD skill rises by +0.5 to +1.5 points at all leads, above 0 on at least 2 of 3 folds, and the gain in years 1–3 is at least as large as in years 4–7.
    - Temperature is unchanged by construction.
*   **Refuted if:** CDD skill falls on at least 2 of 3 folds or on the 7-origin mean, or u has a clearly positive pooled slope.
*   **Rivals:**
    - (a) Summers warm differently from the annual mean (H2's mechanism), so u has a trend.
    - (b) CDD is convex in T, so sens rises with warming and a linear mapping under-forecasts.
    - (c) sens is attenuated because the temperature regressor is noisy.
*   **Discriminating experiment:** four arms: the primary arm; the primary arm plus the pooled u-trend × (year − c30); the primary arm with a summer sensitivity (from H2's daily build); and the candidate.
    - Rival (a) predicts the u-trend arm wins and u's slope is above 0.
    - Rival (b) predicts the primary arm's signed error is negative in the warmest tercile and grows with lead.
*   **Closest prior work:** eia2025shortterm fits a separate 30-year OLS line to each state's annual CDD. H5 derives CDD from the temperature forecast and keeps only the 30-year mean of the CDD-specific part. It also differs from the team's rejected delta method, which changed the trend, not the level.
*   **Claim type:** confirmatory for the primary arm, which adds no parameter; exploratory for the other arms.
*   **Needs:** master only; reuses `cdd_per_degree` and the temperature path in `trend.py`. About 45 min.
*   **Strengths / Costs:** Strength: CDD carries half the current score, H5 adds no parameter, and it is a direct rival to H2. Cost: it loses at long leads if rival (a) holds, and sens is noisy for cool cities.

**How the hypotheses relate.**
- H1, H4 and H5 each change the level through a different error component (idiosyncratic spatial noise, common temporal noise, CDD-specific noise). They can be combined in a factorial run after separate tests.
- H2 and H5 are rival accounts of CDD's summer-specific part.
- H2 and H3 are rival accounts of any upward shift in hottest day: a trend versus skew.

---

**Dropped Candidates**
- Trend plus AR(1) on last year's residual (ho2013 / krueger2011 style): duplicate of U1, whose features include `last` and `d5`.
- Pooled 1975 hinge slope: no material change for 2019–2025, since the 1979–2018 window is already past the hinge. The 1975 hinge year was also known only with hindsight for the 1980 and 1995 folds.
- Level window that varies with lead, from the bias–variance trade-off (arguez2009improving q2): duplicate of U1, which learns window weights by horizon.
- Slope varying with latitude or continentality: close to the rejected regional slopes and the 25% own-city slope.
- City-specific urban trends shrunk by empirical Bayes: the expected differential (hausfather2013quantifying q1) is far below the slope noise, so the weight would be about 0.
- CO2-regression trend: needs an external forcing series (documentation and approval), krueger2011simple relies on AR4 runs, and for 2019–2025 it is about the same as a linear trend.
- Rescaling for missing days in valid years: expected bias is at most about 1% of the annual total for a few cities, a negligible effect on MAE. A count check is enough.
- Using the r largest daily Tmax values for the hottest-day level: the gain is bounded by within-year noise, and heat waves make the top days correlated. It overlaps H1.
- GEV median for hottest day (katzndblock): the mean–median gap is about 0.05 of the GEV scale, which is negligible.
- Precipitation deficit predicting next year's hottest day (mueller2012hot, abstract only): the documented coupling is sub-seasonal, so the prior is low. It could be a feature for U1 instead.
- CPC skill mask with damped anomalies for precipitation and hottest day: overlaps U1 and U2, and the window results show no persistent anomaly to damp.
- Separate level windows per season, and Huber or winsorized hottest-day levels: both belong to the window and median families already explored, with small expected effects.
- Blending the pooled trend with U1-linear: a variation of U2.

**Leads to Fetch** (unverified, not in the folder)
- WMO-No. 1203 (2017), Guidelines on the Calculation of Climate Normals: methods for estimating normals at stations with incomplete records from neighbours (H1).
- Fay & Herriot (1979, JASA), composite and small-area EB estimators (H1).
- Cochran, Sampling Techniques, ratio and regression estimators (H1, H5).
- Hosking & Wallis (1997), Regional Frequency Analysis (H1, H3).
- Peterson et al. (1998, IJC), review of homogeneity adjustments (H1).
- Coles (2001), extreme-value modelling, including location trends (H2).
- Seasonal U.S. Tmax trend figures in the full text of vose2017temperature, already in `sources/` but with no extracted quote (H2).
- Meehl et al. (2012) on warming-hole heat extremes (H2 rival; already listed in INDEX).
- Seneviratne et al. (2010), soil moisture–climate interactions (H2 rival).
- Thom (1958) and Wilks' textbook on gamma-distributed precipitation (H3).
- Deser et al. (2012) on internal variability in U.S. temperature (H4 rival).
- Observational studies of station CDD sensitivity to warming (H5).

**Thin Spots**
- The folder has more than ten relevant notes, but specific mechanisms are not covered, so novelty is unverified for:
  - H1: no source on small-area estimation or on normals from neighbours.
  - H3: no source on the shape of the precipitation distribution or on median normals.
  - H5: no observational CDD sensitivity.
  - H2: no quoted U.S. seasonal trends.
- There is no forecasting study of hottest day and none on decadal persistence of U.S. station anomalies.
- All notes are unaudited, and the notes used for vandendool2011readme q3, huang1996longlead, gardner1985forecasting, smith2009simple, efron1975data and mueller2012hot rest on abstracts or a single web page.

**Files read** (all under `/Users/atabaresa/repos-new/proto-star-challenge/` unless the path is absolute)
- Persona: `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- Supplied context:
  - `research_background.md`, `hypotheses.md`, `docs/data.md`
  - `docs/trials/user_hypotheses.md`, `docs/trials/pooled_trend.md`, `docs/trials/pooled_trend_exploration.md`
  - `literature/INDEX.md` and 31 of its 45 notes in `literature/notes/`, including every key cited above
- Beyond your list (disclosed):
  - Harness code, read to check feasibility: `src/proto_star/backtest.py`, `trend.py`, `direct.py`, `climate.py`, `data/master.py`, `scripts/build_master_dataset.py`
  - The EDA findings cell in `notebooks/03_agent_daily_eda.ipynb`, which `docs/data.md` refers to

No files were written.

### Generator B (Fable 5.2)

## Hypotheses H11–H17 (GENERATE)

I return seven candidates, H11–H17, each testable as a `forecaster(train, cutoff_year, forecast_years)` on the existing harness with numpy/pandas/scikit-learn. Nothing was run and no files were written. I read 16 of the 45 literature notes; all notes are unaudited, so every novelty claim below is unverified.

## Background

The question is which backtestable methods can raise the official relative-MAE skill for annual forecasts of four metrics in 210 U.S. cities, 2019–2025, using data through 2018 only. The current candidate (`trend_level10_15_sensitivity`) scores 4.14 / 0.33 / 6.92 (all / years 1–3 / years 4–7). All of that comes from temperature and CDD; precipitation and hottest day sit at exactly 0. About 40 variants and U1–U3 have been tried on three folds, so gaps under roughly 0.3 raw-score points are noise. Open points are skill on precipitation and hottest day, the negative temperature skill in years 1–3, and whether anything beats the candidate on more than one fold.

**A ceiling that bounds several candidates (my own arithmetic, not from a source).** If a metric is stationary with Gaussian year-to-year noise, the 30-year mean's estimation error adds only about 1/30 to forecast variance. Perfect knowledge of the level would then be worth about 1.6% MAE skill. Larger gains on precipitation or hottest day need either a bias in the reference (skew, station steps) or a real non-stationary signal.

**Rules common to all tests.**
- Every tunable quantity is fixed a priori or estimated inside the fold from pseudo-origins at or before cutoff − 7.
- Comparators are `trend_level10_15_sensitivity`, `current_best` and `thirty_year_mean`, on the ADR 0004 folds, with the 7-origin check as a secondary diagnostic.
- Each hypothesis adds only one or two variants, to limit further multiple comparisons.
- No pretrained models are involved, so benchmark exposure does not apply.

---

### H11: Shrinking each city's recent-level anomaly (10/15-year level minus 30-year mean) toward its regional mean anomaly improves temperature and CDD skill, mainly in lead years 1–3.

*   **Status:** new
*   **Mechanism:** A city's 10–15-year level carries city-specific sampling noise on top of a spatially coherent decadal signal. Partial pooling removes noise if most of the cross-city spread in recent anomalies is noise. This pools levels; the rejected variants pooled slopes (regional slopes, 25% own-city slope).
*   **Inspirations:** efron1975data q1, q3 (shrinkage of parallel means); vandendool2011readme q3 (operational OCN amplitude reduced by a-priori skill); haug2020spatial q1–q2 (spatial pooling of trend coefficients); livezey2007estimation q3.
*   **Prediction:** The shrink weight B on the city-specific part, estimated in-fold, falls clearly below 1 (about 0.3–0.8). Temperature skill in years 1–3 improves by at least 0.5 points over the candidate on at least 2 of 3 folds. Years 4–7 raw score does not drop by more than 0.3.
*   **Refuted if:** In-fold B is about 1 (city deviations are signal), or years 1–3 temperature skill does not improve on at least 2 folds and on the 7-origin mean.
*   **Rivals:**
    - (a) City-specific recent deviations are real and persistent (urban growth, the warming hole, station drift), so shrinkage hurts.
    - (b) Any gain comes from implicitly repairing station-switch steps through the neighbour mean, not from noise reduction.
    - (c) Any gain is just damping toward the 30-year mean, which is the U2 effect.
*   **Discriminating experiment:**
    - Run the shrinkage toward the regional anomaly and toward zero at the same B. If zero does as well, rival (c) holds.
    - Score switch and non-switch cities separately. A gain only in switch cities supports rival (b).
    - Compare regional against national pooling targets.
*   **Closest prior work:** haug2020spatial — it pools trend coefficients on a European grid for significance testing; this pools level anomalies of station series for forecasting under MAE. vandendool2011readme shrinks toward climatology, not toward a spatial mean.
*   **Claim type:** confirmatory for the direction in years 1–3; exploratory for the size.
*   **Needs:** Annual master table and the `region` column (or k nearest cities from `city_info` lat/lon). About 1 hour.
*   **Strengths / Costs:** Targets the documented weak early years and reuses the existing level and trend code. / U2 already showed damping helps years 1–3 slightly, so separating it from rival (c) is essential; region definitions add a degree of freedom.

### H12: A regionally pooled recent anomaly, applied with an in-fold-estimated damping factor λ, gives positive skill on precipitation (multiplicative) and hottest day (additive), where each city's own shorter window does not.

*   **Status:** new
*   **Mechanism:** City-level 15–20-year means failed because station noise swamps any decadal signal. If decadal precipitation or hot-extreme anomalies are spatially coherent, the regional median of (15-year mean / 30-year mean − 1) has far less noise than one city's ratio. Forecast = city 30-year mean × (1 + λ × regional ratio), with λ in [0, 1] fitted by pooled absolute error on pseudo-origins and defaulting to 0.
*   **Inspirations:** easterling2017precipitation q1 (regionally coherent signs of precipitation change), q3 (multi-year droughts); vose2017temperature q3 (warmest-day trends differ west and east of the Rockies); vandendool2011readme q1, q3 (15-year precipitation OCN, damped by skill); efron1975data q1.
*   **Prediction:** In-fold λ is above 0 in at least 2 folds. Precipitation skill is at least +1.0% on the official folds and at least +0.5% over 7 origins. The 40-year mean reached 0.71 / 0.07, which sets the noise scale.
*   **Refuted if:** λ is about 0 in most folds, or precipitation and hottest-day skill are at or below 0 on the 7-origin mean.
*   **Rivals:**
    - (a) Regional decadal anomalies do not persist over 1–7 years, as wilks2013projecting q3 suggests (30-year averages were best for precipitation).
    - (b) An apparent gain is one region in one fold.
    - (c) The gain comes from fixing station-step bias through neighbours.
*   **Discriminating experiment:**
    - Use the city's own 15-year ratio at the same λ. It should be worse if pooling is the mechanism.
    - Report per-region and leave-one-region-out skill.
    - Exclude switch cities.
*   **Closest prior work:** vandendool2011readme — OCN on climate divisions with fixed windows; here the anomaly is pooled across stations and λ is estimated under absolute error inside each fold. The literature index reports no station-level precipitation trend-versus-climatology study.
*   **Claim type:** exploratory
*   **Needs:** Annual master table and `region`. About 1–1.5 hours; shares code with H11.
*   **Strengths / Costs:** Addresses the half of the score that is at zero, and λ = 0 falls back safely to the reference. / The prior evidence in the folder is against it, and few pseudo-origins exist for the 1980 fold.

### H13: Shifting the precipitation forecast (and the CDD level in low-CDD cities) from the mean toward the median, using a skew correction pooled across cities, gives a small positive MAE skill that the 30-year sample median could not.

*   **Status:** new
*   **Mechanism:** MAE is minimised by the median. Annual precipitation, and CDD near its zero bound, are right-skewed, so the 30-year mean sits above the median. The rejected 30-year median is a noisy estimator. Forecast = mean × (1 − q × CV²), with one pooled q fitted in-fold by absolute error; this keeps the efficient mean and adds a low-variance bias correction. For a gamma shape, q near 1/3 is expected (from memory, not from the folder).
*   **Inspirations:** easterling2017precipitation q3 (large interannual variability); petri2015impacts q4 (CDD spans 163 to 4,608 across cities, so relative variability differs widely); efron1975data q1 (pooling to stabilise per-city estimates). The index lists natekin2013gradient for "L1 loss = conditional median"; I did not read that note.
*   **Prediction:** Precipitation skill of +0.2% to +1.0%, positive on at least 2 of 3 folds and on the 7-origin mean. The gain is concentrated in the highest-CV tercile of cities. In-fold q is positive in every fold.
*   **Refuted if:** In-fold q is at or below 0, or precipitation skill is at or below 0 on the 7-origin mean, or the gain is not larger in high-CV cities.
*   **Rivals:**
    - (a) A real downward precipitation trend in some regions would also reward a lower forecast.
    - (b) Missing-day low bias in targets rewards a lower forecast.
*   **Discriminating experiment:**
    - Stratify by CV tercile and by region. Skew predicts scaling with CV²; trend predicts a regional pattern.
    - Stratify scored rows by missing-day count.
*   **Closest prior work:** the team's own 30-year-median variant (rejected) — this replaces the per-city sample median with a pooled parametric shift. U1 used a median objective on temperature and CDD only.
*   **Claim type:** confirmatory for the sign; the size may fall below the noise floor.
*   **Needs:** Annual master table. About 45 minutes.
*   **Strengths / Costs:** Follows directly from the metric, is cheap, and has almost no downside. / The expected gain is about 0.05–0.25 raw-score points, hard to distinguish from noise on three folds.

### H14: Forecasting hottest day as a recent-level estimate of mean July–August daily Tmax plus a long-window mean of the "excess" (annual max minus that summer mean) beats the 30-year mean of annual maxima.

*   **Status:** new
*   **Mechanism:** The annual maximum is a one-day statistic with high noise, so trends added to it directly failed. If hot days warm at the pace of the summer median, any shift is better detected on the lower-noise summer-mean Tmax series. The excess is then treated as stationary and estimated over a long window.
*   **Inspirations:** mckinnon2024pace q1, q3 (hottest summer days warm with the median; background only, since its data run past 2018); vose2017temperature q5 (very slight increase in warmest day since the mid-1960s); katzndblock q4 (trend in the location parameter of block maxima); livezey2007estimation q3.
*   **Prediction:**
    - Identity check: 30-year summer level + 30-year excess reproduces the reference at 0 skill.
    - Summer level 10/15 + 30-year excess gives at least +1.0% hottest-day skill in years 4–7 on the official folds and above 0 on 7 origins.
    - Adding the floored pooled summer-Tmax slope does not reduce it.
*   **Refuted if:** Both arms are at or below 0 on the 7-origin mean, or a pooled in-fold regression of decadal change in annual max on decadal change in summer-mean Tmax has a coefficient near 0.
*   **Rivals:**
    - (a) The excess is not stationary (drought and land-surface feedbacks, vose2017temperature q4; mueller2012hot q1, q3), so it offsets summer-mean shifts.
    - (b) Summer-mean shifts are mostly station-switch steps.
    - (c) Hottest-day warming at these stations is too small relative to noise (vose2017temperature q5).
*   **Discriminating experiment:**
    - Read the in-fold coefficient above: near 1 supports the mechanism; near 0 supports rival (a) or (c).
    - Score switch and non-switch cities separately for rival (b).
    - Compare excess windows of 30 years against all years since 1950 for rival (a).
*   **Closest prior work:** katzndblock — a nonstationary GEV fits the trend on the maxima themselves; here the non-stationary part is estimated on the summer mean from daily data. The team's rejected "trend added to hottest day" used the maxima directly.
*   **Claim type:** exploratory
*   **Needs:** `daily` table (tmax), screened for missing July–August days, aggregated in-fold. About 1.5–2 hours.
*   **Strengths / Costs:** Uses the daily data, which is so far unexploited for this metric, and the ablation isolates the mechanism. / The summer 10-year mean has similar standard error to the 30-year mean of maxima, so the gain depends wholly on a real shift; the 1980 fold will likely be negative.

### H15: Adjusting pre-switch years for station-change steps estimated against neighbouring cities, before computing 30-year means, improves precipitation and hottest-day MAE in cities with a switch inside the window.

*   **Status:** new
*   **Mechanism:** A station move puts a step into the series, and the 30-year reference averages across it. That biases the level for up to 29 years, so the reference is beatable in exactly those cities. The step is estimated as the change in (city − mean of k nearest non-switching cities) between about 10 years after and before the switch, shrunk toward 0, and applied to pre-switch years. Precipitation uses ratios.
*   **Inspirations:** menne2009homogenization q1, q3 (pairwise difference series; relocation shifts unrelated to climate); hausfather2013quantifying q2; efron1975data q1 (shrinking noisy step estimates). The index says wilks2013performance reports better normals from homogenized data; I did not read that note.
*   **Prediction:** Among cities with a switch in the fold's 30-year window, hottest-day and precipitation MAE fall by at least 3% relative to the reference. Non-switch cities are unchanged by construction. Overall skill on each metric is about +0.3% to +1%, depending on the share of switch cities per fold.
*   **Refuted if:** Switch-city MAE does not improve on at least 2 folds, or estimated steps are indistinguishable from placebo steps at random years in non-switch cities.
*   **Rivals:**
    - (a) Steps for precipitation and annual maxima are too small relative to interannual noise to estimate over 10 years. The 0.5 °F figure is for temperature metrics.
    - (b) Neighbour differences capture real local climate divergence, not artifacts.
    - (c) Recent switches leave too few post-switch years to estimate the step.
*   **Discriminating experiment:**
    - Compare the placebo-step distribution with the real-step distribution.
    - Plot gain against years since switch.
    - Run a temperature and CDD arm, where the step is known to be about 0.5 °F and should be detectable.
*   **Closest prior work:** menne2009homogenization — monthly temperature with a dense network and automatic changepoint detection; here break dates are documented, the network is 210 sparse cities, the metrics include annual maxima and precipitation, and the criterion is forecast MAE. U3 changes how the slope is demeaned; the rejected "current-station level" discards pre-switch years instead of adjusting them and was tried only on temperature and CDD.
*   **Claim type:** exploratory
*   **Needs:** Annual master (`Station Segment`, `years_since_switch`) and `city_info` lat/lon. About 1.5–2 hours.
*   **Strengths / Costs:** One of the few routes to beat the reference through bias, and the placebo test is clean. / Only switch cities can gain (30 in 1989–2018), so the ceiling is low; "current-station level changed almost nothing" for temperature is prior evidence of a small effect.

### H16: Adding a pooled, lead-decaying fraction φ_h of the last observed year's residual from the level-plus-trend fit improves leads 1–2 for temperature and CDD, and possibly precipitation.

*   **Status:** new
*   **Mechanism:** Annual anomalies carry some year-to-year persistence (ocean memory, soil moisture, multi-year drought) that a 10/15-year mean weights at only 1/10 to 1/15. Forecast_h = baseline_h + φ_h × (last valid year − fitted baseline for that year), with φ_h for h = 1, 2, 3 estimated in-fold by pooled regression on pseudo-origins and set to 0 beyond lead 3.
*   **Inspirations:** ho2013statistical q1–q2 (forced trend plus AR(1) residual; skill mostly from the trend); krueger2011simple q3 (forced regression plus autoregressive internal variability); easterling2017precipitation q3.
*   **Prediction:** In-fold φ_1 lies in 0.05–0.3 and φ_h decays with h. Temperature skill in years 1–3 improves by at least 0.5 points on at least 2 folds. Years 4–7 are identical to the candidate by construction.
*   **Refuted if:** In-fold φ_1 is at or below 0 or unstable in sign across folds, or years 1–3 skill does not improve on at least 2 folds and on 7 origins.
*   **Rivals:**
    - (a) φ only reweights the level window (exponential-smoothing-like) and reflects level drift, not persistence.
    - (b) Nationally common anomalies make each origin effectively one sample, so φ fits a few ENSO sequences.
*   **Discriminating experiment:**
    - Split the residual into the national-mean part and the city-specific part and fit φ on each. Persistence only in the national part, with unstable sign, supports rival (b).
    - Compare with a level window that simply up-weights the last year for all leads. Under rival (a) that helps all leads; under true persistence only short leads.
*   **Closest prior work:** ho2013statistical — per-grid-box SST regressed on CO2 with AR(1), scored by correlation; here the trend is pooled across land stations, φ is pooled and lead-specific, and scoring is MAE against a 30-year mean. Overlap with U1 is possible if U1's features included a one-year window; this isolates that single mechanism on top of the candidate.
*   **Claim type:** confirmatory for the sign of φ_1; exploratory for the score gain.
*   **Needs:** Annual master table. About 1 hour.
*   **Strengths / Costs:** Aimed at the live-board horizon and cannot harm years 4–7. / The plausible gain is small (roughly φ² of one or two lead years), and 3 folds give about 3 independent lead-1 years.

### H17: Building annual temperature from season-specific levels (longer windows for the noisy cold season, shorter for the warm season), and driving CDD by a pooled warm-season slope times each city's CDD per warm-season degree, improves both metrics.

*   **Status:** new
*   **Mechanism:** Winter dominates the interannual variance of annual mean temperature, so one window length for the annual mean is a compromise. Seasonal series can each use the window their signal-to-noise supports. CDD depends almost only on May–September temperatures, so regressing CDD on annual mean temperature mixes in winter noise and attenuates the per-degree coefficient.
*   **Inspirations:** livezey2007estimation q7 (fixed averaging length inadvisable unless the optimum varies little), q6; vandendool2011readme q1 (OCN computed per season); petri2015impacts q3 (CDD defined on a 65 °F base, so only warm days count).
*   **Prediction:**
    - CDD arm alone: CDD skill in years 4–7 is at least +0.5 points over the candidate on at least 2 folds.
    - Temperature arm: years 1–3 temperature skill is less negative by at least 0.5 points, with no years 4–7 loss above 0.3 raw points.
    - In-fold-selected windows differ by season, with the cold season at least as long as the warm season.
*   **Refuted if:** In-fold-selected windows are the same across seasons, or neither arm improves on at least 2 folds and on 7 origins.
*   **Rivals:**
    - (a) Any temperature gain equals what an annual-series window of the same effective length gives; level 15 and level 10 already trade places.
    - (b) Warm-season per-degree coefficients are no better than "slope proportional to city level", which was within noise of sensitivity.
*   **Discriminating experiment:**
    - Compare with an annual-series forecaster using the day-weighted average window length, for rival (a).
    - For CDD, compare warm-season-sensitivity, annual-sensitivity and proportional-to-level slopes on identical levels, and check that in-fold per-degree coefficients have lower standard error under the warm-season regression.
*   **Closest prior work:** vandendool2011readme and livezey2007estimation — seasonal OCN as separate seasonal forecasts for climate divisions; here seasonal components are recombined into annual station targets with a pooled slope. The rejected delta method shifted daily temperatures, which is a different route to CDD.
*   **Claim type:** exploratory
*   **Needs:** `daily` table aggregated to city × year × season in-fold, with missing-day screening. About 1.5–2 hours.
*   **Strengths / Costs:** Works on the two metrics that carry the score, and its two arms are separable. / More tunables (season boundaries, window set); the gain over a 10/15 blend may be within noise.

---

## Dropped Candidates

- **CO2-forcing regressor in place of a linear time trend** (krueger2011simple, ho2013statistical): needs external CO2 data, which requires documentation and honor-code review, and is nearly collinear with a 40-year linear trend.
- **Geographic (lat/lon/elevation) model of city slopes:** too close to the rejected regional-slope and 25%-own-slope variants.
- **Separate Tmax and Tmin components for average temperature:** with pooled linear slopes and equal windows it is algebraically the same as the candidate.
- **Missing-day rescaling of precipitation and hottest day in training years:** scored targets carry the same bias; kept only as a rival check in H13.
- **Lead-dependent window weights or damping:** this is what U1 and U2 already test.
- **Equal-weight combinations of 10/15/20/30/40-year means for precipitation and hottest day:** a duplicate of rejected window variants.
- **Robust (trimmed or Huber) 30-year level for hottest day:** a near-duplicate of the rejected medians, with no mechanism beyond H13.
- **Same-year precipitation deficit as a hottest-day predictor** (mueller2012hot): the predictor is not known at forecast time.
- **Per-city nonstationary GEV for hottest day** (katzndblock): per-city trend fits already failed badly (`linear_trend` −12.76), and it would need scipy optimisation; H14 is the pooled alternative.

## Leads to Fetch (unverified, from memory or the index's lead list; not used as support)

- Gamma-distribution modelling of precipitation totals and the median approximation mean × (1 − 1/(3k)), for example Thom (1958), Monthly Weather Review. Bears on H13.
- Wilks & Livezey (2013), full text: the size of the homogenization benefit for normals. Bears on H15; the folder has the abstract only.
- Kunkel et al. (2020), JAMC, DOI 10.1175/JAMC-D-19-0185.1 (in the index's unverified leads). Bears on precipitation coherence for H12.
- Cheng et al. (2014), Climatic Change, DOI 10.1007/s10584-014-1254-5 (in the index's unverified leads). Bears on H14.
- Literature on decadal persistence of U.S. regional precipitation and on the lag-1 autocorrelation of annual station temperature. Bears on H12 and H16; nothing is in the folder.
- Seasonal differences in the optimal averaging window in Huang et al. (1996), full text. Bears on H17; the folder has the abstract only.

## Thin Spots

- Fewer than ten notes bear directly on any one hypothesis, so novelty is unverified for all seven.
- No source tests anything by MAE against a 30-year mean at annual, single-station scale and 1–7-year leads.
- Precipitation has no station-level forecasting evidence. Suggested searches: "decadal persistence annual precipitation United States stations"; "optimal climate normals precipitation station skill".
- Hottest day has no forecasting study and no source on the stationarity of (annual max − summer mean). Suggested search: "annual maximum temperature minus summer mean trend United States".
- Nothing covers station-switch effects on precipitation totals or annual maxima at airport stations. Suggested search: "station relocation precipitation inhomogeneity annual total".
- Nothing covers skew or median corrections under absolute-error scoring for climate normals.
- Nothing covers observed CDD sensitivity to seasonal rather than annual temperature.

## Files read

- `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/data.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/user_hypotheses.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/pooled_trend.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/pooled_trend_exploration.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- In `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`: livezey2007estimation, vandendool2011readme, wilks2013projecting, krueger2011simple, ho2013statistical, gardner1985forecasting, efron1975data, menne2009homogenization, hausfather2013quantifying, haug2020spatial, katzndblock, vose2017temperature, easterling2017precipitation, mueller2012hot, mckinnon2024pace, petri2015impacts (all `.md`).

## Final

The loop stopped after round 1 at the human's decision ("Stop here (Recommended)"). Every
backtest column is exploratory. It gives the paired year-block bootstrap difference against
`trend_level10_15_sensitivity`, with a 95% interval, on the arm's declared primary endpoint,
on the ADR 0004 folds. The primary endpoints were declared in each config header before the
run. "pp" means percentage points of one metric's skill; "raw" is the raw score. Findings are
in `hypotheses_review.md`; the citation auditor did not run.

| ID | Statement (short) | Status | Open Blocker / Major | Last round changed | Backtest (primary endpoint) |
| :- | :---------------- | :----- | :------------------- | :----------------- | :-------------------------- |
| U1 | Pooled direct multi-horizon median model | dropped | 1 (X1) / 13 | 1 | linear: raw years 4–7 −2.34 [−3.46, −1.14]; boosted −3.84 [−5.20, −2.49] |
| U2 | Equal-weight blend of pooled trend and `current_best` | dropped | 1 (X1) / 8 | 1 | raw all −0.47 [−1.04, +0.14]; years 4–7 −0.92 [−1.30, −0.58] |
| U3 | Station-segment-aware pooled slope | dropped | 2 (X1, U3-a) / 7 | 1 | raw all +0.02 [−0.15, +0.20]: equivalent within ±0.3 |
| H1 | Neighbour-anchored levels (precipitation, hottest day) | dropped | 1 (X1) / 14 | 1 | raw all +0.01 [−0.16, +0.19]; beats all 20 placebos; same endpoint over 7 cut-offs: −0.03 |
| H2 | June–August slope added to the hottest-day 30-year mean | dropped | 1 (X1) / 15 | 1 | hottest-day skill, years 4–7: −1.23 [−2.20, −0.08] pp (significantly worse) |
| H3 | Closed-form skew shift toward the median (q = 1/3) | dropped | 1 (X1) / 11 | 1 | precipitation skill −0.73 pp (fold mean; not bootstrapped); raw all 3.96 against 4.14 |
| H4 | Remove the shared national residual from the level | kept | 1 (X1) / 10 | 1 | temperature skill, years 4–7: +1.62 [−1.71, +4.82] pp; same endpoint on the early origins: −5.47 pp (unstable by era) |
| H5 | CDD from its 30-year mean plus CDD per degree × temperature departure | dropped | 1 (X1) / 11 | 1 | CDD skill, all years: −0.21 [−1.36, +0.92] pp; early origins significantly worse |
| H11 | Shrink city anomalies toward the regional mean | dropped | 1 (X1) / 14 | 1 | temperature skill, years 1–3: −0.02 [−0.53, +0.43] pp; same endpoint over 7 cut-offs: −0.74 [−1.08, −0.38] pp (worse) |
| H12 | Regional anomaly with in-fold damping (precipitation, hottest day) | merged into H1 | 1 (X1) / 12 | 1 | not run: merged into the H1 family and deferred |
| H13 | Skew correction with in-fold q | merged into H3 | 1 (X1) / 11 | 1 | fitted q: precipitation skill −1.34 pp (fold mean) |
| H14 | Recent summer-mean level plus a stationary excess (hottest day) | merged into H2 | 1 (X1) / 11 | 1 | hottest-day skill, years 4–7: −1.40 [−3.38, +0.74] pp; same endpoint on the early origins: +3.17 pp |
| H15 | Neighbour-estimated station steps before the 30-year mean | kept | 1 (X1) / 10 | 1 | not run (deferred: two leakage paths to close first, H15-a) |
| H16 | Lead-decaying persistence of last year's error | kept | 1 (X1) / 11 | 1 | raw, years 1–3: +0.77 [−0.30, +1.63]; 7 cut-offs +0.47 [−0.40, +1.41] |
| H17 | Season-specific levels and warm-season CDD slope | kept | 1 (X1) / 12 | 1 | not run (deferred: too large for the time box, H17-c) |

Open counts come from the ledger's `finding.raised` events (open Blockers / open Majors), matched
by each finding's hypothesis tag. Cross-cutting findings that apply to every hypothesis (X1,
X2–X8, F2) count for each one, so the counts overlap.

**Outcome.** No hypothesis beats the candidate with an interval that excludes 0. The candidate
`trend_level10_15_sensitivity` stays the submission candidate. H4 and H16 are kept as the only
leads with positive point estimates. Both are inconclusive, and both reverse or vanish on the
early-origin set.

## Round 2

The human judged round 1 "not good" and asked for better experiments and hypotheses, so this
round goes past the round limit at the human's explicit request. Every hypothesis here starts
from `docs/trials/candidate_error_analysis.md`, an error decomposition of the candidate over
10 historical origins (fold truth only, all before 2019). One idea was tested and refuted
before this round: a panel fixed-effects level (`configs/at_fe_level_scan.yaml`; see
`docs/experiments.md`).

### Assistant hypotheses (E1–E4)

These were written by the assistant at the human's request, from the error analysis. The
generators receive them as `AlreadyConsidered`.

#### E1: A damped city anomaly gives the hottest day (and precipitation) positive skill

- Status: new
- Author: assistant (elephant), from the error analysis
- Statement: Recent city-specific anomalies of the hottest day persist. The cross-city slope
  of (next-7-year mean − 30-year mean) on (last-15-year mean − 30-year mean), with the
  national mean removed, averages 0.42 over 10 origins; for precipitation it is 0.21. The
  current forecast uses λ = 0 for these metrics (the 30-year mean), and the rejected shorter
  windows use λ = 1. So m30 + λ̂·(A_city), with λ̂ fitted in-fold on pseudo-origins (about 0.4
  for the hottest day), will give positive hottest-day skill.
- Primary endpoint: hottest-day skill, all years, paired year-block bootstrap against the
  candidate; it passes when the 95% interval excludes 0.

#### E2: Shrinking only the city-specific part of the temperature anomaly toward the national mean improves temperature

- Status: new
- Author: assistant (elephant), from the error analysis
- Statement: The candidate carries each city's recent temperature anomaly forward at full
  weight. Only about 0.65 of the city-specific part persists. Keeping the national part and the
  trend, and scaling the city part by an in-fold λ̂_c, will raise temperature skill. This
  differs from H11 in two ways: it shrinks toward the national mean rather than the region,
  and λ is fitted on pseudo-origins rather than taken from a noise formula.
- Primary endpoint: temperature skill, all years.

#### E3: The candidate's warming-era cold bias is predictable in-fold

- Status: new
- Author: assistant (elephant), from the error analysis
- Statement: The candidate under-forecasts temperature and CDD in recent folds. CDD bias is
  −36, −82 and −87 at 2000, 2005 and 2011; a perfect national shift would add about 9 points
  of years 4–7 temperature skill. A multiplier κ on the pooled trend term, fitted on in-fold
  pseudo-origins by MAE, will be above 1 and reduce that bias.
- Caveat stated in advance: at the 2018 cut-off the 40-year window is all post-1975, so the
  slope may already be unbiased. A backtest gain may not transfer to 2019–2025.
- Primary endpoint: temperature skill, years 4–7.

#### E4: A pooled multiplicative precipitation trend corrects the wetting bias

- Status: new
- Author: assistant (elephant), from the error analysis
- Statement: Over 10 origins, actual precipitation exceeds its 30-year mean by about 0.5 in on
  average (the reference's mean signed error is −0.52 in). A within-city pooled relative trend
  of annual precipitation over a long window, applied from the centre of the 30-year window,
  will give small positive precipitation skill.
- Primary endpoint: precipitation skill, all years.

### Generator A, round 2 (Opus 5.5, default model)

# Round 2 hypotheses H21–H25 (GENERATE)

I kept five hypotheses, numbered H21–H25, and dropped thirteen candidates. Nothing was run and no files were written.

**Read this first: the inputs changed while I was working.**
- When I first read `hypotheses.md` it had 631 lines and ended at E4. Later a grep showed 859 lines: a section "Generator B, round 2 (Fable 5.2)" with H31–H35 had been added.
- `src/proto_star/anomaly.py` and `configs/at_round2_assistant.yaml` also appeared during the run. I read the first 90 lines of `anomaly.py` to check what code exists. I did not open the config.
- I drafted all five kept hypotheses before I saw Generator B's section, then read it.
- Three of mine closely match B's:
  - H23 matches H32 (separate Tmin and Tmax coefficients).
  - H24 matches H35 (mean of the 10 hottest days).
  - H25 matches H33 (wet-day frequency).
- B also derived the same 8.9% noise floor (item 1 below).
- I did not change any mechanism after reading. Each matching entry says how it differs; treat each pair as one family.
- H21 and H22 have no counterpart in B's set.
- I dropped the October–December idea after I had seen that B dropped it too. The arithmetic behind my drop is my own.
- So the two generators are only partly independent in this round.

## Background

The task is to raise the relative-MAE skill, against each city's 30-year mean, of annual forecasts for four metrics in 210 U.S. cities for 2019–2025, using data through 2018 only. The candidate `trend_level10_15_sensitivity` scores 4.14 / 0.33 / 6.92 (all / years 1–3 / years 4–7), and no trial so far has a paired interval that excludes 0.

The error analysis over 10 origins shows headroom in three places:
- the national shift per fold, for temperature and CDD;
- city-level bias per fold, for all four metrics;
- partial persistence of recent city anomalies. At N = 15 the city-part slope is 0.65 for temperature, 0.88 for CDD, 0.42 for hottest day and 0.21 for precipitation. The candidate carries this part at weight 1 for temperature and CDD, and at weight 0 for the other two.

All five hypotheses change only the city part of the anomaly. The national part and the trend stay exactly as in the candidate, so these hypotheses can be combined with E3 or H4 later.

## Derived from the supplied data (my own arithmetic, not from a note)

1. **The city oracles overstate predictable headroom.**
   - For independent years, knowing the realized 7-year mean gives skill 1 − √(1 − 1/7)/√(1 + 1/30) ≈ 8.9% with no real signal in it.
   - Subtracting that floor leaves about 3 points of real city headroom for precipitation (oracle 11.91) and about 7 for hottest day (oracle 16.32).
2. **Recent city anomalies partly revert, except for CDD.**
   - Model: a fixed city shift plus independent yearly noise. The anomaly A_N is the mean of the last N valid years minus the 30-year mean. The two windows overlap, so the noise variance of A_N is σ²(1/N − 1/30), and the noise in A is uncorrelated with the noise in the 7-year future mean F.
   - I calibrated the shift variance from the N = 1 slope, then predicted the slopes at N = 10 and 15:

     | metric | predicted, N = 10 / 15 | observed, N = 10 / 15 |
     |---|---|---|
     | temperature | 0.84 / 0.91 | 0.62 / 0.65 |
     | CDD | 0.83 / 0.91 | 0.80 / 0.88 |
     | hottest day | 0.52 / 0.69 | 0.37 / 0.42 |
     | precipitation | 0.43 / 0.60 | 0.21 / 0.21 |

   - CDD fits the fixed-shift model. Temperature, hottest day and precipitation fall short, so part of their city anomaly reverts rather than just being noisy.
   - Caveat: short-memory persistence inflates the N = 1 slope. My estimate is that it adds only about 0.04, far too little to close the gap.
   - This motivates two questions: which component reverts (H21, H23), and whether real shifts are sparse (H22).
3. **Changes that move only the city part give narrow intervals.** "City-part only" means the change has zero cross-city mean.
   - City-part only:
     - H11, temperature skill in years 1–3: about ±0.48 pp.
     - H1, precipitation and hottest day together: about ±0.18 raw.
   - Shifts that move every city together are 2–7 times wider:
     - H4, temperature in years 4–7: ±3.3 pp.
     - H2, hottest day in years 4–7: ±1.06 pp.
   - All five hypotheses below are city-part only. So a single-metric effect of about 0.5–0.7 pp should be detectable, and anything smaller should not.
4. **Rough effect sizes.**
   - Moving a city-part weight from w to the fitted slope λ* cuts MSE by (w − λ*)²·Var(A).
   - For hottest day (w = 0, λ* = 0.42, N = 15) that is about 2% of per-year MSE, or about +1 pp of skill. This is the E1-type gain.
   - Better predictors or functional forms (H22–H25) probably add only tenths of a point on top. So each primary endpoint against the candidate mostly measures the E1- or E2-type gain. Each hypothesis therefore needs its nested E1 or E2 arm, fitted with the same in-fold pseudo-origin procedure, as the mechanism control.

**Rules common to all five.**
- Every coefficient is fitted on in-fold pseudo-origins with origin + lead ≤ cut-off, as `anomaly_correction_forecast` does.
- Comparators: the candidate (primary, paired year-block bootstrap on the ADR 0004 folds), the nested E1/E2 arm, and `thirty_year_mean`. The 7 cut-offs and the early origins 1955/1962/1969 are secondary.
- All claims are exploratory on the official folds (X3), because N = 15 and the persistence figures come from an analysis that includes those folds.
- No pretrained model is involved. I am an LLM with knowledge past 2018; no constant here comes from that knowledge. Windows match the E1/E2 code, regions are master's `region` column, and grids are fixed in advance.

---

### H21: Damping only the regional part of each city's recent temperature anomaly, and keeping its local part at full weight, will raise temperature skill over the candidate, because regionally coherent decadal anomalies revert while local station offsets persist.

*   **Status:** new (no counterpart in H31–H35)
*   **Mechanism:**
    - Split the E2 anomaly A_i (15-year window) as A_i − n = r_i + l_i:
      - n is the cross-city mean;
      - r_i is the leave-one-out mean of (A − n) over the other cities in the same `region`;
      - l_i is the remainder, the local part.
    - The two parts should behave differently:
      - Regional multi-year anomalies come from large-scale variability and forcing patterns whose drivers change by period, so they revert.
      - Local offsets come from siting, urban growth and instruments, and stay until the next change.
    - The H11 result fits this picture. H11 damped the local part toward the region, and it was significantly worse over 7 cut-offs. If the local part persists, the 0.65 reversion (item 2) must sit in the regional part.
    - Specification: forecast = candidate + β_r·r_i + β_l·l_i. The betas are fitted by least squares on the candidate's own 7-year errors at in-fold pseudo-origins and clipped to [−1, 0.5]; λ = 1 + β. Leave CDD unchanged, since it fits the fixed-shift model.
*   **Inspirations:**
    - mascioli2017timing q3 (drivers vary by season, region and period).
    - vose2017temperature q7 (natural and human causes).
    - hausfather2013quantifying q1 (the urban signal is local; urban climatology, outside the subfield).
    - menne2009homogenization q3 (homogenization, outside the subfield).
    - efron1975data q1–q2 (statistics, outside the subfield).
    - haug2020spatial q2.
    - vandendool2011readme q3.
*   **Prediction:**
    - **Primary endpoint:** temperature skill, all years, official folds. The paired difference against the candidate is positive with a 95% interval excluding 0. Expected +0.5 to +1.5 pp.
    - **Secondary:**
      - λ̂_l has a pseudo-origin-block bootstrap interval that contains 1.
      - λ̂_r ≤ 0.7 at each official cut-off.
      - The split arm is at or above the E2 arm on the official folds and over 7 cut-offs.
      - CDD readout: λ̂_r and λ̂_l for CDD both have intervals that contain 1.
*   **Refuted if:**
    - The primary interval lies at or below 0.
    - λ̂_r ≥ λ̂_l at 2 or more of the 3 cut-offs; this refutes the mechanism whatever the score. If the primary passes with λ̂_r ≈ λ̂_l, the gain belongs to E2, not to H21.
*   **Rivals:**
    - (a) Reversion is uniform across scales, so E2's single coefficient is enough.
    - (b) Seasonal: the winter part reverts at every spatial scale. This is the H17 temperature-arm territory.
    - (c) Diurnal: the Tmax part reverts (H23, H32).
    - (d) Noise: a regional mean of 15-year anomalies still carries regional weather noise.
    - (e) The coefficients are unstable by era, as H4 was.
*   **Discriminating experiment:**
    - **Joint regression.** Regress the candidate's pseudo-origin errors on four parts: {regional, local} × {summer-implied, remainder}. The summer-implied part is the city part of the CDD anomaly divided by the city's CDD per degree from `trend.py`, so no daily data is needed.
      - (a) predicts four equal coefficients.
      - (b) predicts that both remainder coefficients fall below the summer ones.
      - H21 predicts that both regional coefficients fall below the local ones in either season part.
    - **Diurnal swap.** Swap the season split for {Tmax, Tmin} to test (c).
    - **Noise check for (d).** Compute the reliability-implied coefficient of r from in-fold regional variance. Reversion predicts λ̂_r at least 0.2 below it.
    - **Era check for (e).** Read the sign of λ̂_l − λ̂_r on 1955/1962/1969.
*   **Closest prior work:**
    - haug2020spatial treats the trend coefficient as a latent spatial field, in order to test significance on European grids. H21 splits the recent level anomaly by spatial scale and gives each scale its own forecast weight, fitted out of sample under the official metric.
    - Team: H11 damped the local part (the opposite of H21). E2 is the special case β_r = β_l.
*   **Claim type:** exploratory. The sign of λ̂_l − λ̂_r on the early origins can be declared confirmatory before the run.
*   **Needs:** master only (`region`, `Avg Temp`, `cdd`). About 1 hour on the `anomaly_correction_forecast` pattern with two regressors, plus about 30 minutes for the joint diagnostic.
*   **Strengths / Costs:** Strength: one extra coefficient, nests E2 and the opposite of H11, and includes a noise check that sampling noise cannot pass. Cost: six fixed regions are coarse, few independent regional-decadal episodes constrain β_r, and the gain beyond E2 may sit inside the ±0.5 pp interval.

### H22: A soft-threshold rule that keeps only the part of each city's recent hottest-day anomaly beyond τ̂ standard errors, with τ̂ fitted in-fold, will give positive hottest-day skill and beat a linear damped anomaly, because real persistent shifts in annual maxima are concentrated in a few cities.

*   **Status:** new (no counterpart in H31–H35; it overlaps H34's step story only in rival (d))
*   **Mechanism:**
    - If real shifts are sparse and large (relocations, instrument changes, local land-use or irrigation changes), the expected future anomaly given the recent one is S-shaped in z: near 0 for small |z|, with slope near 1 for large |z|.
    - One linear λ (E1) then over-shrinks the real shifts and adds noise everywhere else.
    - Operational OCN already thresholds by location skill and then damps. H22 thresholds each city by the standardized size of its own anomaly.
    - Specification:
      - ã_i is the city part of (15-year mean − 30-year mean) of `Max Tmax`.
      - se_i = s_i·√(1/15 − 1/30), where s_i is the in-fold 30-year standard deviation (item 2). z_i = ã_i/se_i.
      - Forecast = m30_i + se_i·sign(z_i)·max(0, |z_i| − τ).
      - τ comes from the fixed grid {0, 0.5, …, 4, ∞}, minimizing pooled MAE of the 7-year targets at in-fold pseudo-origins. τ = ∞ is the candidate.
*   **Inspirations:**
    - vandendool2011readme q2, q3 (skill mask, then amplitude reduction).
    - efron1975data q1–q3 (the linear Stein rule as the contrast; outside the subfield).
    - menne2009homogenization q3 (outside the subfield).
    - vose2017temperature q5, q6.
    - natekin2013gradient q1, q2 (L1 loss and long-tailed errors; ML, outside the subfield).
    - claeskens2016forecast q2 (estimated parameters add variance, hence a single pooled τ).
*   **Prediction:**
    - **Primary endpoint:** hottest-day skill, all years, official folds. The paired difference is positive with an interval excluding 0. Expected +0.5 to +2 pp.
    - **Secondary diagnostics, on in-fold pseudo-origins:**
      - The slope of future on recent anomaly in the |z| > 2 bin is at least 0.3 above the slope in the |z| < 1 bin.
      - 0.5 ≤ τ̂ ≤ 3 at 2 or more cut-offs.
      - The soft threshold is at or above E1's linear arm on the official folds and over 7 cut-offs.
*   **Refuted if:** any of the following.
    - The primary interval includes 0.
    - The bin slopes differ by less than 0.1, which means the relationship is linear.
    - τ̂ sits on a grid edge (0 or ∞) at 2 or more cut-offs.
    - E1 is at or above the soft threshold on both the official folds and the 7 cut-offs.
*   **Rivals:**
    - (a) Shifts are dense and roughly Gaussian across cities, so linear shrinkage is optimal.
    - (b) The large-|z| cities are documented station switches (H15 territory).
    - (c) Large |z| comes from single extreme years, which then revert.
    - (d) Undocumented steps (H34).
*   **Discriminating experiment:**
    - **Arms:**
      1. m30
      2. E1 linear
      3. soft threshold (primary)
      4. hard threshold
      5. switch-only: the full anomaly for cities with a switch in the window, m30 otherwise
      6. soft threshold scored on non-switch cities only
    - **Expected pattern:**
      - H22 predicts soft ≥ hard > linear, and a gain among non-switch cities.
      - (b) predicts switch-only ≈ soft and no gain among non-switch cities.
      - (a) predicts linear ≥ soft.
      - (c) predicts the large-z bin slope falls when z is computed from a 15-year median anomaly.
    - **Secondary:** a precipitation arm on the ratio scale.
*   **Closest prior work:**
    - vandendool2011readme withholds the OCN forecast where a-priori correlation is below 0.3, a skill threshold by location. H22 thresholds each city's own standardized anomaly, with one τ fitted out of sample under absolute error.
    - Team: E1 (linear λ); B's H34 (break search).
*   **Claim type:** exploratory
*   **Needs:** master only. About 1 hour; it reuses E1's pseudo-origin anomalies with a τ grid.
*   **Strengths / Costs:** Strength: it tests the shape of the persistence relation, which bears on every shrinkage-type hottest-day idea, and it falls back to m30 when τ̂ = ∞. Cost: there are few large-|z| cities per fold, so the bin slopes and τ̂ are noisy, and the gain over E1 may be under the interval width.

### H23: Scaling the city-specific Tmin and Tmax parts of the recent temperature anomaly by separate in-fold coefficients will raise temperature skill over the candidate, because local night-time offsets persist while daytime city anomalies revert.

*   **Status:** new. **Convergent with H32** (drafted independently). My additions: the reversion test in item 2, the H21 joint decomposition, and the CDD-implied seasonal rival.
*   **Mechanism:**
    - Urban growth and siting act mainly on Tmin and stay in place.
    - Tmax city anomalies follow moisture and land-surface regimes, which revert.
    - Specification:
      - A_max and A_min are the city parts of the 15-year anomalies of `Avg Tmax` and `Avg Tmin`, each valid under its own missing-days rule.
      - Forecast = candidate + β_max·A_max/2 + β_min·A_min/2, fitted on pseudo-origin errors.
      - Identity check first: (Avg Tmax + Avg Tmin)/2 should match `Avg Temp` within 0.05 °F. If it does not, add the residual as a third part held at weight 1.
*   **Inspirations:**
    - hausfather2013quantifying q1 (outside the subfield).
    - arguez2009improving q3, q4 (the window–trend relation is −0.78 for January Tmin and −0.35 for July Tmax).
    - vose2017temperature q4, q6.
    - mueller2012hot q1, q3 (land–atmosphere, outside the subfield).
    - efron1975data q1.
*   **Prediction:**
    - **Primary endpoint:** temperature skill, all years. The paired difference against the candidate is positive with an interval excluding 0.
    - **Secondary:** λ̂_min − λ̂_max ≥ 0.2 at each official cut-off, with a bootstrap interval excluding 0. The split arm is at or above the E2 arm.
*   **Refuted if:** the primary interval includes 0, or λ̂_min ≤ λ̂_max at 2 or more of the 3 cut-offs.
*   **Rivals:**
    - (a) Reliability: Tmin anomalies are simply less noisy.
    - (b) Spatial reversion (H21).
    - (c) Seasonal reversion, the CDD-implied part.
    - (d) Station steps shift both components equally.
*   **Discriminating experiment:**
    - Run the same joint regression as H21 with {regional, local} × {Tmax, Tmin}.
    - Compare each fitted coefficient with its reliability-implied value; (a) predicts they agree.
    - Repeat with CDD as the target. If the Tmax part persists better for CDD than for annual temperature, that favours (c).
*   **Closest prior work:**
    - arguez2009improving computes station-specific OCN windows from lag-1 autocorrelation and trend, separately for Tmin and Tmax normals, with no skill test. H23 gives the components separate forecast weights fitted out of sample.
    - Team: E2; B's H32.
*   **Claim type:** exploratory
*   **Needs:** master only. About 45–60 minutes on `anomaly.py`.
*   **Strengths / Costs:** Strength: the fitted coefficients read out the mechanism directly, with no daily data. Cost: it duplicates H32, and if E2 fails the split has little room.

### H24: The recent city-specific anomaly of the mean of each year's ten hottest daily Tmax values, scaled by an in-fold coefficient, will give positive hottest-day skill and beat the annual maximum's own damped anomaly, because it measures the same persistent warm-tail shift with less single-day noise.

*   **Status:** new. **Convergent with H35** (drafted independently). My additions:
    - a variance-channel arm (June–August mean plus June–August standard deviation of daily Tmax);
    - a cross-metric arm (the CDD-implied summer anomaly, whose city part persists at 0.88);
    - a negative control on `Avg Tmin`.
*   **Mechanism:**
    - Persistent local influences on hot extremes (land-surface feedbacks, irrigation, siting) shift the whole warm tail.
    - T10 averages that shift over many days, while one annual maximum is mostly single-event noise.
    - H14 failed with coefficient 1, using the June–August mean and including the national part. H24 fits β and keeps only the city part.
    - Specification:
      - T10 = mean of the 10 highest daily Tmax values per city-year, valid when Tmax is missing on 10 days or fewer.
      - Forecast = m30_hot + β̂·(city part of the 15-year T10 anomaly).
      - Per-year aggregates come from a script modelled on `build_summer_means.py`, joined on (ID, Year), with the X5 invariance test.
*   **Inspirations:**
    - katzndblock q4 (location and log-scale trends of block maxima; extreme-value theory, outside the subfield).
    - mckinnon2024pace q1 (background only; its data run past 2018).
    - vose2017temperature q4, q5, q6.
    - mueller2012hot q3.
    - efron1975data q1.
*   **Prediction:**
    - **Primary endpoint:** hottest-day skill, all years. The paired difference against the candidate is positive with an interval excluding 0.
    - **Secondary:**
      - Go/no-go before scoring: the in-fold year-to-year variance of T10 is at most 0.85 times that of the annual maximum.
      - The pseudo-origin correlation of the T10 anomaly with the future city anomaly exceeds the maximum's own by at least 0.05.
*   **Refuted if:** any of the following.
    - The correlation is not higher.
    - The primary interval includes 0.
    - The `Avg Tmin` control predicts as well as T10. That would point to a general station offset, not a warm-tail mechanism.
*   **Rivals:**
    - (a) Heat waves make the top ten days one event.
    - (b) The tail decouples from the body of the distribution, as with H14.
    - (c) A general station offset moves everything.
    - (d) The variance channel: changes in summer spread move the maximum at a constant mean.
*   **Discriminating experiment:**
    - Ladder over k = 1, 3, 10, 30 and the June–August mean.
    - Add the June–August standard deviation arm for (d), and the `Avg Tmin` control for (c).
*   **Closest prior work:**
    - katzndblock fits location and scale trends on the maxima themselves. H24 estimates the shift from upper order statistics and summer distribution moments of daily data, then predicts the maximum's city anomaly.
    - Team: H14, E1; B's H35.
*   **Claim type:** exploratory
*   **Needs:** the daily table and one per-year build script. About 1.5 hours.
*   **Strengths / Costs:** Strength: the variance check gives a go/no-go before any scoring, and the controls separate three accounts. Cost: it needs a new daily aggregate, and the gain over E1 is probably a few tenths of a point.

### H25: Splitting each city's recent precipitation anomaly into wet-day frequency and wet-day intensity parts, with separate in-fold coefficients, will give positive precipitation skill, because the frequency part persists while the intensity part, driven by a few heavy events, does not.

*   **Status:** new. **Convergent with H33** (drafted independently). My additions: the multiplicative split into W and I with two coefficients, so that the fitted order λ_W > λ_I is the test.
*   **Mechanism:**
    - P = W·I, where W is the `Wet Days` count and I = P/W is the mean wet-day intensity.
    - The year-to-year noise in P comes mostly from I. W sums many daily indicators, so regime shifts show in it more clearly.
    - Specification:
      - w̃ and ĩ are the city parts of the 15-year log-ratio anomalies of W and I.
      - Forecast = m30_P·(1 + λ_W·w̃ + λ_I·ĩ), fitted on pseudo-origins with each λ clipped to [0, 1].
      - Respect the blanked fake zeros, and confirm the `Wet Days` threshold first.
*   **Inspirations:**
    - easterling2017precipitation q1, q3.
    - wilks2013projecting q3.
    - livezey2007estimation q6.
    - menne2009homogenization q3 (for the rival; outside the subfield).
    - claeskens2016forecast q2 (econometrics, outside the subfield).
    - efron1975data q1.
*   **Prediction:**
    - **Primary endpoint:** precipitation skill, all years. The paired difference against the candidate is positive with an interval excluding 0. Expected +0.2 to +0.8 pp, which is at or near the minimum detectable effect (item 3).
    - **Secondary:** λ̂_W − λ̂_I ≥ 0.15 at 2 or more cut-offs.
*   **Refuted if:**
    - The primary interval lies at or below 0, or λ̂_W ≤ λ̂_I at 2 or more cut-offs.
    - If the interval spans 0 with the predicted order of the λs, the result is inconclusive.
*   **Rivals:**
    - (a) Gauge, threshold or observer changes move counts without moving totals.
    - (b) Nothing in precipitation persists beyond E4's drift.
    - (c) Persistent intensification, so λ̂_I > λ̂_W.
*   **Discriminating experiment:**
    - Arms: total anomaly only (the E1 precipitation arm), W only, W + I, and the "body" total P − `Max 5-day P`.
    - Score switch and non-switch cities separately for (a).
    - Report leave-one-region-out skill.
*   **Closest prior work:**
    - easterling2017precipitation assesses national and regional trends in annual totals. H25 uses the frequency and intensity components as forecast predictors under absolute error.
    - Team: E1, E4, H12; B's H33.
*   **Claim type:** exploratory
*   **Needs:** master only. About 1 hour.
*   **Strengths / Costs:** Strength: it uses columns no trial has touched, and the λ order reads out the mechanism. Cost: there are only about 3 points of real headroom, and the expected effect is near the noise.

**How they relate.**
- H21 and H23 are rival accounts of the same temperature reversion in item 2. One joint regression, {regional, local} × {Tmax, Tmin} plus the CDD-implied summer part, separates H21, H23, E2 and the seasonal (H17-type) account. Both nest E2.
- H22 (functional form) and H24 (predictor) are independent refinements of E1 for hottest day. They fit a 2×2 design with E1 as the shared control.
- H25 stands alone, with E1's precipitation arm as its control.
- None of the five touches the national part or the trend.

## Dropped Candidates

- **October–December anomaly as a lead-1 predictor (temperature, via persistence and ENSO).**
  - My arithmetic: a lead-1 annual correlation of about 0.14, worth about +0.35 pp of temperature skill in years 1–3. That is below the ±0.48 pp interval width.
  - It rests on only 3 lead-1 years in the official folds, and it is close to H16.
  - I decided after seeing B's identical drop.
- **Seasonal persistence split:** this is H17's temperature arm. It is kept only as rival (b) of H21, through the CDD-implied part.
- **Per-city shrinkage weights by interannual variance:** a variation of E2 and H11.
- **Anomaly provenance (switch-driven parts at weight 1):** overlaps H15. It is rival (b) of H22.
- **Lead-dependent decay of the city anomaly:** duplicates U1's horizon-specific weights.
- **Regional own slopes for hottest day:** close to the rejected regional slopes and to H2's own-slope arm, which scored −0.81 pp.
- **Pooled quadratic or accelerating trend:** a variation of E3 and of the dropped hinge.
- **Error-feedback from the candidate's last completed 7-year errors:** an own-city slope in disguise. The 25% own-city slope was rejected.
- **EOF or ENSO pattern regression at lead 1:** does not fit in 1–2 hours, and annual means dilute the seasonal signal.
- **Precipitation deficit predicting hottest day:** precipitation anomalies persist only 0.05–0.21.
- **Fall-only precipitation trend:** a variation of E4, and the national precipitation headroom is only 0.65 pp.
- **Per-city choice between the candidate and the reference:** a local model selection that will likely overfit (montero-manso2021principles q4).
- **2018 rounding artifact:** not testable on folds that end before 2018.

## Leads to Fetch (unverified, from memory; not used as support)

- Donoho & Johnstone (1994), Biometrika, on soft thresholding for sparse means (H22).
- Karl et al. (1993), BAMS, on asymmetric Tmax and Tmin trends (H23).
- Karl & Knight (1998), BAMS, on trends in U.S. precipitation amount, frequency and intensity (H25).
- Zhang et al. (2011), on the ETCCDI definitions of `Wet Days` and `Warm Days` (H24, H25).
- Coles (2001), on r-largest order statistics (H24).
- Seneviratne et al. (2010), on soil moisture–climate interactions (H23, H24).
- Deser et al. (2012), on internal variability in North American climate (H21).
- Studies of the ASOS transition at first-order stations, for temperature and precipitation (H22, H25).

## Thin Spots

- No note covers:
  - sparse versus Gaussian heterogeneity of station shifts, or thresholding estimators (H22);
  - regional versus local decomposition of decadal station anomalies (H21);
  - Tmin versus Tmax persistence on a 7-year scale (H23);
  - upper order statistics of daily Tmax (H24);
  - wet-day frequency versus intensity at stations (H25).
- Fewer than ten notes bear on any one hypothesis, so novelty is unverified for all five.
- Suggested searches for the librarian:
  - "soft thresholding sparse station inhomogeneity";
  - "regional decadal temperature variability U.S. stations persistence";
  - "precipitation frequency intensity trends United States stations";
  - "annual maximum temperature r-largest trend U.S.".

## Files read

- **Persona:** `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- **Supplied context** (in `/Users/atabaresa/repos-new/proto-star-challenge/`):
  - `research_background.md`, `docs/trials/candidate_error_analysis.md`, `docs/experiments.md`, `docs/data.md`
  - `hypotheses.md`, in both its 631-line and 859-line states
  - `literature/INDEX.md`
  - Notes in `literature/notes/`: livezey2007estimation, huang1996longlead, vandendool2011readme, wilks2013projecting, wilks2013performance, arguez2009improving, proietti2025estimation, ho2013statistical, krueger2011simple, lai2020use, morris1999impact, petri2015impacts, montero-manso2021principles, hewamalage2021global, claeskens2016forecast, smith2009simple, gardner1985forecasting, meinshausen2006quantile, natekin2013gradient, efron1975data, menne2009homogenization, hausfather2013quantifying, haug2020spatial, katzndblock, vose2017temperature, easterling2017precipitation, mascioli2017timing, mueller2012hot, mckinnon2024pace
- **Beyond the supplied list, read for feasibility and results:**
  - `hypotheses_review.md`
  - `docs/trials/family_levels.md`, `family_persistence_cdd.md`, `family_hottest_summer.md`, `family_neighbours.md`, `round1_cheap.md`
  - `src/proto_star/trend.py`, `backtest.py`, `climate.py`, `adjust.py`, `direct.py`, `data/summer.py`, `data/README.md`
  - `src/proto_star/anomaly.py`, lines 1–90


### Generator B, round 2 (Fable 5.2)

## Hypotheses H31–H35 (GENERATE)

Five candidates, each a forecaster on the existing harness; nothing was run and no files were written. Literature notes are unaudited, so every novelty claim is unverified. I found no new CDD mechanism that is not a variation of E3, H5, H17 or the rejected delta method, so CDD has no hypothesis here.

## Background

The task is to raise the official relative-MAE score for annual forecasts of four metrics in 210 U.S. cities for 2019–2025, using data through 2018 only. The candidate `trend_level10_15_sensitivity` scores 4.14 / 0.33 / 6.92 (all / years 1–3 / years 4–7), all from temperature and CDD; precipitation and hottest day sit on the 30-year mean at zero skill. Round 1 and the fixed-effects level produced nothing whose paired bootstrap interval excludes 0. The error analysis over 10 origins shows headroom in three places: the national shift per fold for temperature (8.7 → 15.1), city-level bias per fold for every metric, and partial persistence of recent city anomalies (slope 0.65 for temperature, 0.42 for hottest day and 0.21 for precipitation at N = 15).

**Three points from the supplied data and code (my own arithmetic, not from a note).**

1. **The "true city mean of the 7 years" oracle overstates predictable headroom.** For a stationary series with independent years, knowing the realized 7-year mean gives skill 1 − √(1 − 1/7) / √(1 + 1/30) ≈ 8.9% with nothing predictable in it. Against that floor, the city-level headroom is about 3 points for precipitation (11.9), about 7 for hottest day (16.3), and larger for temperature and CDD.
2. **Hottest-day targets are whole degrees in every backtest year.** The findings cell of `/Users/atabaresa/repos-new/proto-star-challenge/notebooks/03_agent_daily_eda.ipynb` says temperatures are whole °F up to 2017, and about 36k values in 2018 have one decimal. Expected absolute error against an integer-valued target is piecewise linear between integers, so a non-integer forecast pays a penalty that an integer forecast does not (H31).
3. **The trend is already anchored at the level window's centre.** `_trend_rows` in `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/trend.py` uses `year − center`, so an anchoring-lag correction is not available and I dropped it.

**Rules common to all five.**
- Comparators: `trend_level10_15_sensitivity` (primary, paired year-block bootstrap), `current_best` and `thirty_year_mean`, on the ADR 0004 folds. The 7-origin and early-origin sets are secondary.
- Every coefficient is fitted on in-fold pseudo-origins with origin + lead ≤ cut-off, as `anomaly_correction_forecast` in `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py` already does. H32 and H33 can reuse it with other regressors.
- The folds have been reused about 60 times, so five more primary endpoints add to the multiple-comparison load.
- No pretrained model is involved, so benchmark exposure cannot explain any result.

---

### H31: Rounding the hottest-day forecast to the nearest whole °F raises hottest-day skill, because the target is integer-valued and expected absolute error is linear between integers.

*   **Status:** new
*   **Mechanism:**
    - For an integer target X, E|X − f| is linear in f on each interval [k, k+1]. A forecast between integers pays the chord, which lies above the smooth loss curve by about a·δ(1 − δ), where a is the density of the annual maximum at its median and δ is the fractional part.
    - Averaged over δ, the penalty is a/6. Rounding to the nearest integer removes it and adds rounding variance worth a/12. The net gain is a/12 per row, whatever the forecast's own error.
    - For a roughly normal annual maximum with standard deviation σ_i, a = 0.399/σ_i. The gain is about 0.033/σ_i °F per row, or roughly 4.1/σ² points of hottest-day skill: about 0.45 at σ = 3 °F and 0.65 at σ = 2.5 °F.
    - Specification: hottest-day forecast = round(30-year mean). No fitted quantity. It composes with any other hottest-day forecaster, including E1.
*   **Inspirations:**
    - natekin2013gradient (absolute loss targets the median; ML tutorial, outside the subfield). I did not re-read this note; it is cited as in H3 of `hypotheses.md`.
    - katzndblock q4 (annual maxima as a block-maximum distribution with a location parameter; extreme-value theory, outside the subfield).
    - Data: Generator A's item 3 in `hypotheses.md` reports that the 30-year median for hottest day scored +0.13 / −0.40 against about −0.9 expected under stationarity. A median of integer data is an integer or half-integer, so a gap of 0.5–1.0 points is the size this mechanism predicts. Generator A read it as drift.
*   **Prediction:**
    - Before running, compute the predicted gain in-fold as 100 × mean_i(0.033/σ_i) / MAE_ref, with σ_i from the 30-year window.
    - Primary endpoint: hottest-day skill, all years, on the official folds. The paired difference is positive, its 95% interval excludes 0, and it lies within a factor of 2 of the predicted gain (expected +0.3 to +0.8 points, about +0.1 to +0.2 raw).
    - The interval should be narrow, because the paired difference per row is a quasi-random ±0.25 °F term and not climate noise.
*   **Refuted if:** the interval on the official folds includes 0 and the 10-origin difference is below +0.15 points, or the half-integer placebo (below) does not lose.
*   **Rivals:**
    - (a) A real upward or downward drift, or skew (H3), so any shift in the right direction pays.
    - (b) A fold accident.
    - (c) The backtest gain is real but does not transfer, because 2019–2025 targets may carry decimals as 2018 does.
*   **Discriminating experiment:** four arms on the 30-year mean.
    - Nearest integer (primary).
    - Nearest half-integer (k + 0.5): the mechanism predicts a loss of about a/6, twice the size of the primary gain and opposite in sign.
    - Floor and ceiling: rival (a) predicts one of them beats nearest; the mechanism predicts both lose to nearest.
    - Transfer check for rival (c), using only 2018 rows: the share of 2018 `Max Tmax` values within 0.1 °F of an integer. Near 100% means the lattice survives the precision change. Also compare the gain in the 2011 fold's lead-7 year (2018) with its other years.
*   **Closest prior work:** H3 and H13 (team) shift toward the median by a skew correction, and the rejected 30-year median pays the median's sampling variance. H31 changes nothing about the level estimate and uses only the discreteness of the target. No note in the folder covers point forecasts for discrete targets.
*   **Claim type:** confirmatory (one arm, no parameter, quantitative prediction made before the run).
*   **Needs:** master only. About 30 minutes.
*   **Strengths / Costs:** Strength: no parameter, no climate assumption, a predicted size, and a placebo with a predicted opposite sign. Cost: the ceiling is about 0.2 raw points, and transfer depends on target precision in 2019–2025, which only the 2018 check can indicate.

### H32: The persistent city-specific part of a recent temperature anomaly is carried by minimum temperature, so scaling the Tmin and Tmax parts with separate in-fold coefficients beats both the candidate and a single coefficient.

*   **Status:** new
*   **Mechanism:**
    - The error analysis gives 0.65 persistence for the city part of the 15-year temperature anomaly, and the candidate carries it at 1.0.
    - Local siting, urban growth and station moves act mostly on night-time temperature and stay in place, so the Tmin part should persist near 1. The Tmax part is closer to transient weather.
    - Specification: A_min and A_max are the city parts (cross-city mean removed) of the 15-year-minus-30-year anomalies of `Avg Tmin` and `Avg Tmax`. Regress the candidate's pseudo-origin errors on A_min/2 and A_max/2. Forecast = candidate + β_min·A_min/2 + β_max·A_max/2, both clipped to [−1, 1].
    - Secondary arm: one coefficient for cities with a station switch in the 30-year window and one for the rest.
*   **Inspirations:**
    - hausfather2013quantifying q1 (urbanization shows in unadjusted minimum temperatures).
    - arguez2009improving q3, q4 (the window–trend relation is −0.78 for January Tmin and −0.35 for July Tmax, so the two components behave differently).
    - menne2009homogenization q3 (instrument and siting changes cause steps; homogenization, outside the subfield).
    - efron1975data q1 (shrinkage of parallel means; general statistics, outside the subfield).
    - livezey2007estimation q7.
*   **Prediction:**
    - In-fold β_max is below β_min by at least 0.2 at all three official cut-offs, with β_max negative.
    - Primary endpoint: temperature skill, all years. The paired difference against the candidate is positive with an interval excluding 0, and the split arm is at least as good as the E2 single-coefficient arm on the official folds and over 7 cut-offs.
*   **Refuted if:** β_min and β_max differ by less than 0.1 or change order across folds, or the split arm does not beat the single-coefficient arm on at least 2 of 3 folds.
*   **Rivals:**
    - (a) The difference only reflects noise: Tmin anomalies have lower sampling variance, so any reliability weighting gives the same split.
    - (b) Station moves shift both components equally, so one coefficient is enough (E2).
    - (c) City anomalies persist through documented switches only, not through the component.
*   **Discriminating experiment:**
    - Compute the coefficient each component would get from its sampling variance alone (Efron–Morris style) and compare with the fitted values. Agreement supports rival (a).
    - The switch-stratified arm tests rival (c): it predicts the split vanishes within non-switch cities.
    - Fit the same split with CDD as the target, where the warm-season Tmax part should matter more; a reversed order there supports the mechanism over rival (a).
*   **Closest prior work:** E2 (team) scales the whole city anomaly by one coefficient, and H11 shrinks toward the region. Generator B dropped a Tmax/Tmin split because it is algebraically identical under equal windows and one slope; H32 differs by giving the two components different persistence. arguez2009improving reports component-specific windows but no skill.
*   **Claim type:** exploratory
*   **Needs:** master (`Avg Tmax`, `Avg Tmin`, `Station Segment`). About 1 hour, reusing `anomaly.py`.
*   **Strengths / Costs:** Strength: targets the metric that carries the score, and the fitted coefficients are a direct readout of the mechanism. Cost: it is an extension of E2, so if E2 fails the split has little room, and two coefficients on about three independent eras can overfit.

### H33: Recent wet-day frequency predicts a city's precipitation level better than its recent total does, because totals are dominated by a few heavy days and counts are not.

*   **Status:** new
*   **Mechanism:**
    - Annual total = wet days × mean intensity. A handful of heavy events drive the total's year-to-year noise, so a real shift in a city's precipitation regime is hard to see in a 15-year total (persistence slope 0.21).
    - The same shift should be clearer in the wet-day count, which is a sum of many small indicators.
    - Specification: r_w = city part of (15-year mean of `Wet Days` / 30-year mean − 1). Forecast = 30-year mean × (1 + λ_w·r_w), with λ_w fitted on pseudo-origins and clipped to [0, 1].
    - Second arm: the same with the "body" total, `ToT Prcp` − `Max 5-day P`.
*   **Inspirations:**
    - easterling2017precipitation q3 (large interannual variability), q1 (regional changes exist).
    - livezey2007estimation q6 (15-year precipitation windows in operational use).
    - efron1975data q1 (general statistics, outside the subfield).
    - menne2009homogenization q3 (the rival: observing changes shift counts without climate change; homogenization, outside the subfield).
    - Data: the annual EDA notebook reports skewness of 1.98 for `Max 1-day P`, 1.72 for `Max 5-day P` and 0.78 for `Wet Days`.
*   **Prediction:**
    - In-fold λ_w is above 0.2 at all three cut-offs.
    - In a two-regressor fit with the total's own anomaly, the wet-day term keeps the larger standardized coefficient.
    - Primary endpoint: precipitation skill, all years. The paired difference is positive with an interval excluding 0 (expected +0.3 to +1.0 points, against about 3 points of real headroom).
*   **Refuted if:** λ_w is at or near 0 in 2 of 3 folds, or the wet-day arm does no better than the same formula using the total's own anomaly (the E1 precipitation arm).
*   **Rivals:**
    - (a) Wet-day counts shift with gauge, threshold or observer changes that do not move totals, so the count anomaly is an artifact.
    - (b) Nothing in precipitation persists beyond the wetting drift E4 targets.
    - (c) Any gain is a one-region, one-fold accident.
*   **Discriminating experiment:**
    - Compare three regressors at their own fitted λ: wet days, body total, and total. The mechanism predicts wet days ≥ body total > total.
    - Score switch and non-switch cities separately. A wet-day signal only in switch cities, with no movement in totals, supports rival (a).
    - Report leave-one-region-out skill for rival (c).
*   **Closest prior work:** E1 (team) damps the total's own anomaly, E4 adds a pooled relative trend, and H12 pools the anomaly by region. H33 changes the predictor, not the pooling or the damping. The folder has no station-level study of precipitation frequency against totals.
*   **Claim type:** exploratory
*   **Needs:** master (`Wet Days`, `Max 5-day P`, with the blanked fake zeros respected). About 1 hour. Confirm the `Wet Days` threshold from the dataset documentation first.
*   **Strengths / Costs:** Strength: uses columns no trial has touched, and λ_w = 0 falls back to the reference. Cost: the real headroom is about 3 points of one metric, and the prior from wilks-type results in the folder is that 30-year averages are hard to beat for precipitation.

### H34: A city's hottest-day level is better described by a step at a data-chosen year than by a fixed recent window, so a post-break mean from the city-minus-reference series gives positive hottest-day skill.

*   **Status:** new
*   **Mechanism:**
    - Instrument and siting changes shift maximum temperatures abruptly, and many are not in the documented station threads. Under a step, the best level is the mean after the break, not a fixed 15-year mean.
    - Specification:
      - Reference c_t = cross-city median of (value − own 30-year mean) in year t, within `region`.
      - Difference d_it = value − c_t over the 30-year window.
      - For each split with at least 8 years on both sides, compute the two-sample t statistic; keep the split with the largest |t|.
      - Forecast = 30-year mean + λ·(post-break mean of d − 30-year mean of d), with one λ fitted on pseudo-origins. Fitting λ in-fold absorbs the selection bias of the maximum.
    - Second arm: the same for precipitation, in ratios.
*   **Inspirations:**
    - menne2009homogenization q1, q2, q3 (difference series, undocumented shifts; homogenization, outside the subfield).
    - arguez2009improving q6.
    - efron1975data q1 (outside the subfield).
    - vose2017temperature q5 (little trend in the warmest day since the mid-1960s, so level changes are more plausibly steps than trends).
*   **Prediction:**
    - In-fold λ is above 0.3 at all three cut-offs.
    - Primary endpoint: hottest-day skill, all years. The paired difference is positive with an interval excluding 0, and exceeds the E1 fixed-15-year arm.
    - Detected break years fall on documented `Station Changes` years more often than chance, and a visible share fall elsewhere.
*   **Refuted if:** the arm does not beat the random-split placebo, or does not beat the fixed-window arm on at least 2 of 3 folds and over 7 cut-offs.
*   **Rivals:**
    - (a) Level changes are gradual, so a damped fixed window (E1) is as good.
    - (b) All real steps are documented switches, so H15 covers it.
    - (c) The largest split is mostly noise, and λ shrinks to 0.
*   **Discriminating experiment:**
    - Placebo: the same forecaster with the split year drawn at random under the same minimum-length rule.
    - Fixed-window arm: E1 on the same difference series, to separate "remove the common signal" from "choose the break".
    - Restrict to cities with no documented switch in the window. A gain there supports undocumented steps over rival (b).
*   **Closest prior work:** menne2009homogenization detects breaks pairwise in monthly temperature to adjust series; H34 uses one regional reference, applies it to annual maxima and precipitation, adjusts no series, and is judged by forecast MAE. H15 (team, not run) uses documented switches only; E1 uses a fixed window.
*   **Claim type:** exploratory
*   **Needs:** master only (`region`). About 1.5–2 hours; the split scan is vectorizable over 23 candidate years.
*   **Strengths / Costs:** Strength: tests step against drift directly, with a placebo. Cost: the most code of the five, close to E1 in what it can gain, and few pseudo-origins constrain λ at the 1980 fold.

### H35: The recent anomaly of the mean of each year's ten hottest days predicts the hottest-day level better than the recent anomaly of the annual maximum itself, because it measures the same upper-tail shift with less one-day noise.

*   **Status:** new
*   **Mechanism:**
    - The persistence slope of 0.42 with a correlation of only 0.19 suggests the 15-year anomaly of annual maxima is a noisy measure of a real shift. Attenuation from measurement noise lowers both.
    - The mean of the ten highest daily Tmax values tracks the same tail but averages out single-day noise. H14 failed with the June–August mean, which sits far from the tail (the in-fold ratio was 1.83 at 1995 and 0.72 at 2011).
    - Specification: T10 = mean of the ten highest daily Tmax in the year, requiring at least 85 June–August days. A = city part of (15-year mean of T10 − 30-year mean of T10). Forecast = 30-year mean of the annual maximum + λ·A, with λ fitted on pseudo-origins.
*   **Inspirations:**
    - katzndblock q4 (a shift in the location of block maxima; extreme-value theory, outside the subfield).
    - mckinnon2024pace q1 (hot days move with the rest of the summer distribution; background only, since its data run past 2018).
    - vose2017temperature q5 (large interannual variability of the warmest day).
    - efron1975data q1 (outside the subfield).
*   **Prediction:**
    - Across in-fold pseudo-origins, the correlation between the T10 anomaly and the next-7-year maximum anomaly exceeds that of the maximum's own anomaly by at least 0.05.
    - Primary endpoint: hottest-day skill, all years. The paired difference is positive with an interval excluding 0, and is larger than the E1 arm's.
*   **Refuted if:** the in-fold correlation is not higher for T10, or the arm does not beat E1 on at least 2 of 3 folds and over 7 cut-offs.
*   **Rivals:**
    - (a) Heat waves make the top ten days one event, so T10 carries the same noise as the maximum.
    - (b) The maximum's shifts are single-day instrument artifacts that T10 dilutes.
    - (c) The tail and the body decouple, as with the June–August mean.
*   **Discriminating experiment:**
    - Vary the count: top 3, top 10, top 30, June–August mean. The mechanism predicts a peak at an intermediate count; rival (a) predicts no change from top 1 to top 10; rival (c) predicts a monotone decline.
    - Compute the in-fold year-to-year variance of T10 against the annual maximum. A reduction under 15% supports rival (a) before any scoring.
*   **Closest prior work:** H14 and H2 (team) use the June–August mean Tmax and were worse than the reference. Generator A dropped the r largest values as a way to estimate the 30-year level, where the ceiling is about 1.6 points; H35 uses them as the predictor of a persistent shift. katzndblock fits trends on the maxima themselves.
*   **Claim type:** exploratory
*   **Needs:** the daily table, one per-year build script modelled on `/Users/atabaresa/repos-new/proto-star-challenge/scripts/build_summer_means.py`, passed through `assert_weather_cutoff`. About 1.5 hours.
*   **Strengths / Costs:** Strength: the variance check gives a go/no-go before scoring. Cost: my estimate of the noise reduction is about 30% of the anomaly's noise variance, so the gain over E1 is probably small, and it needs a new daily aggregate.

**How they relate.** H31 is independent of the rest and stacks on any hottest-day forecaster. H34 and H35 are rival refinements of E1 for hottest day (window choice against predictor noise); run E1 first, since both need it as their control. H32 extends E2. H33 is the precipitation counterpart of H35.

---

## Dropped Candidates

- Anchoring the trend at the level window's centre: already done in `trend.py`.
- Precision-weighted pooled slope (weight low-variance cities): my estimate of the slope's standard error is about 0.012 °F per year, far below the fold biases, so slope noise is not the limiting error.
- Space-for-time CDD sensitivity (cross-city CDD against mean temperature): approximates the rejected delta method.
- Pooled CDD slope scaled by a city weight: the same as the tried "slope proportional to city level".
- City-specific shrinkage weights by interannual variance: a variation of E2 and H11; kept only as the rival check in H32.
- Leading spatial patterns (EOF filter) of the recent anomaly field: H11's result says city deviations from the region are signal, so filtering them would hurt.
- Late-year (October–December) anomaly as a lead-1 predictor: one month of persistence explains almost none of an annual mean; a variation of H16.
- Multi-year precipitation deficit predicting hottest day: precipitation anomalies barely persist (0.07–0.21), so there is nothing to carry forward.
- Exponentially weighted level: a variation of the window family and H16.
- Equal-weight combination of existing forecasters, or half-strength H4: variations of U2 and H4.
- Summer part of the temperature anomaly kept, winter part discarded: this is H17's temperature arm.
- City DTR trend as an urban-drift slope: own-city slopes were already rejected as noise.

## Leads to Fetch (unverified, from memory; not used as support)

- Gneiting (2011), "Making and evaluating point forecasts", JASA: optimal point forecasts under absolute error, including discrete targets (H31).
- Reeves, Chen, Wang, Lund & Lu (2007), review of changepoint detection for climate series, JAMC (H34).
- Karl et al. (1993), asymmetric trends of daily maximum and minimum temperature, BAMS (H32).
- Zhang et al. (2011), ETCCDI index definitions, for the `Wet Days` and `Warm Days` thresholds (H33).
- Literature on the ASOS and HO-83 maximum-temperature biases at U.S. first-order stations (H34).
- Coles (2001), r-largest order statistics models (H35).

## Thin Spots

- No note covers point forecasts for integer-valued targets; H31's derivation is my own and should be checked by the methodologist.
- No note covers precipitation frequency against totals, the stationarity of upper-tail daily Tmax statistics, or undocumented breaks in annual maxima at airport stations. Suggested searches: "wet day frequency versus intensity trends United States stations"; "changepoint annual maximum temperature inhomogeneity ASOS"; "r-largest order statistics temperature trend".
- No note gives observational evidence that city-level Tmin shifts persist longer than Tmax shifts; hausfather2013quantifying concerns long-term trends, not 7-year persistence.
- Fewer than ten notes bear on any single hypothesis, so novelty is unverified for all five.
- CDD: the folder has no observational CDD sensitivity study, and I found no untested mechanism.

## Files read

- `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/candidate_error_analysis.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/experiments.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/data.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- In `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`: livezey2007estimation, hausfather2013quantifying, menne2009homogenization, easterling2017precipitation, vose2017temperature, arguez2009improving, katzndblock, mckinnon2024pace, efron1975data, petri2015impacts (all `.md`)
- Beyond the supplied list, to check feasibility and facts: `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/trend.py`, `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py`, `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/data/summer.py`, and grep hits in `/Users/atabaresa/repos-new/proto-star-challenge/notebooks/03_agent_daily_eda.ipynb` and `/Users/atabaresa/repos-new/proto-star-challenge/notebooks/02_agent_annual_indices_eda.ipynb`

## Final (Round 2)

The round-2 loop stopped after one critique round. Every result is exploratory, because the
round was derived from diagnostics that include the test folds' truth (methodologist R2-X1).

The adoption rule was fixed before the final runs (methodologist R2-X3). An arm is adopted
only if:

- it passes the root gate: its official-fold 95% interval excludes 0;
- it has the same sign on the replication origins 1934/1941/1948;
- its in-fold coefficient has the same sign at all three cut-offs.

Refinements had to beat their nested parent. "pp" means percentage points of one metric's
skill.

| ID | Status | Primary endpoint (official folds) | 7 cut-offs | Early | Replication | Note |
| :- | :----- | :-------------------------------- | :--------- | :---- | :---------- | :--- |
| E1 | dropped | hottest-day skill +0.10 [−0.77, +0.97] pp | −0.15 pp | +1.73 pp | — | Fails the root gate |
| E2 | **adopted** | temperature skill +0.38 [+0.04, +0.71] pp; raw +0.22 [+0.07, +0.35] | raw +0.05 | raw +0.14 | raw +0.07 | λ_temperature 0.60/0.65/0.84 and λ_CDD 0.72/0.66/0.79 at 1980/1995/2011 |
| E3 | dropped | temperature skill, years 4–7, −1.72 [−2.78, −0.71] pp | −1.20 pp | — | — | Blocker E3-a: does not transfer |
| E4 | dropped | precipitation skill +0.17 [−1.46, +1.80] pp | −0.38 pp | — | — | Blocker E4-a: ceiling below the detectable effect |
| H21 | dropped | temperature skill +0.28 [−0.19, +0.73] pp | −0.09 pp | +2.37 pp | +0.57 pp | Mechanism refuted: λ_regional ≥ λ_local at 2 of 3 cut-offs |
| H22 | kept (not run) | — | — | — | — | Refinement of E1; E1 failed its gate |
| H23 = H32 | kept (mechanism supported, not adopted) | temperature skill +0.47 [+0.02, +0.91] pp; against E2 +0.10 [−0.04, +0.25] | +0.08 against E2 | +0.16 against E2 | −0.07 against E2 | λ_Tmin − λ_Tmax ≥ 0.43 at every cut-off; no score gain over E2 |
| H24 = H35 | kept (not run) | — | — | — | — | Refinement of E1; E1 failed its gate |
| H25 ⊇ H33 | kept (not run) | — | — | — | — | Refinement of E1's precipitation arm, which failed |
| H31 | dropped | not run | — | — | — | Lattice gate failed: every city has decimals in 2018 |
| H34 | kept (not run) | — | — | — | — | Deferred (cost) |

**Outcome.** E2 replaces the city-specific part of the candidate's temperature and CDD anomaly
with an in-fold damped version. It is the only arm that meets the adoption rule. Its realistic
gain is small: about +0.05 to +0.2 raw-score points over the candidate, and smaller still
after the winner's curse.

## Round 3

Refine round at the human's request ("Refine round 3"). Each generator refined its own
round-2 set: refiner A (Opus 5.5) took E1–E4 and H21–H25, and refiner B (Fable 5.2) took
H31–H35. Both got the round-2 findings and the logged backtest results. Each report is filed
verbatim.

### Refiner B, round 3 (Fable 5.2)

# REFINE report: H31–H35 (Generator B, Round 2)

**Outcome:** H31, H33 and H34 are dropped; H32 and H35 are revised; H36 and H37 are new. Nothing was run and no file was written.

None of the four kept hypotheses is likely to move the submission today. Expected gains are 0.02–0.1 raw points, and two of them sit under E1, which failed its gate.

## Background

The task is to raise the official relative-MAE score for annual forecasts of four metrics in 210 U.S. cities for 2019–2025, using data through 2018 only. Since H31–H35 were written, the Round 2 runs have settled several points:

- **E2 adopted.** Shrinking the city part of the temperature and CDD anomaly gives raw +0.22 [+0.07, +0.35] on the official folds.
- **E1 failed its root gate.** Hottest-day skill is +0.10 [−0.77, +0.97] pp. By lead, it is +0.83 pp in years 1–3 and −0.44 pp in years 4–7; early origins give +1.73 [+0.93, +2.51].
- **H23 = H32 mechanism readout held, with no score gain over E2.** λ_Tmin is 0.83/0.83/1.04 against λ_Tmax 0.31/0.40/0.58 at 1980/1995/2011. Against E2 the split adds +0.10 [−0.04, +0.25] pp, and −0.07 on the replication set.
- **H31 lattice gate failed.** Every city has decimal daily Tmax in 2018.

Every result below is exploratory (R2-X1), because the motivating numbers come from the truth of the test folds.

**Rules common to all kept hypotheses** (answers methodologist R2-X2, R2-X3, R2-X5, R2-X6):

- **Pseudo-origins.** For cut-off C, p = C−30 … C−1, with targets p+h ≤ C and h ≤ 7. This is what `anomaly_correction_forecast` in `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py` does.
- **Fitted quantities at each p use rows with year ≤ p only.** This covers the 30-year mean, the 15-valid-year anomaly, cross-city means, and the base forecast (pooled slope over p−39..p with its floor, and CDD-per-degree). `_errors` and `_anomalies` already filter this way.
- **Checks still to make.**
  - Whether `Station Segment` numbering can be read from rows ≤ p without later history.
  - Whether an invariance test (perturb rows after the cut-off, assert identical output) exists. I did not read `tests/test_anomaly.py`.
- **Fit.** Least squares on annual-row errors, coefficients clipped to [−1, 1].
- **Reporting.** Per-fold differences and per-cut-off coefficients for the official folds, the 7 cut-offs, early origins (1955/1962/1969) and replication origins (1934/1941/1948).
- **Adoption rule.** As already fixed: gate, same sign on replication, same coefficient sign at all three cut-offs.
- **Justification.** Every decision rests on data through 2018 only.
- **Literature.** I did not re-read the notes in this pass. Keys and quote numbers are as cited in `hypotheses.md` and the novelty review, and all are unaudited.

---

### H32: The city part of a recent temperature anomaly persists more in Tmin than in Tmax, beyond what the two components' sampling reliability alone predicts.

*   **Status:** revised (one family with H23; single specification)
*   **Answers findings:**
    - egm-novelty-r2: H23/H32-a, H23/H32-c, X-1, X-2.
    - egm-methodologist-r2: H23/H32-a, H23/H32-b, H23/H32-c, R2-X4, R2-X5.
*   **Mechanism:** Siting, urban and instrument offsets act on night-time temperature and stay in place. Daytime city anomalies are closer to transient weather. This revision changes the claim from "the split raises the score" to "the persistence gap is real and is not a reliability artifact". The score claim has been tested and was inconclusive.
*   **Specification (fixed; H23/H32-a):**
    - As run: `split=diurnal`, window 15, clip [−1, 1], base = candidate.
    - Equivalent one-degree-of-freedom form: E2's single regressor A_city plus the contrast D = (A_tmin − A_tmax)/2.
    - Scored rows are identical to the candidate's.
*   **Inspirations (motivation only, per H23/H32-c):** hausfather2013quantifying q1; arguez2009improving q3–q4 (mixes season with component); menne2009homogenization q3; efron1975data q1.
*   **Prediction (primary endpoint, against the nested parent E2):**
    - For each component, compute the reliability-implied coefficient at each pseudo-origin: λ_rel = 1 − mean_i(s_i²/30) / Var_cities(A). Here s_i² is the city's interannual variance over the 30 years ending at p, and s_i²/30 is the sampling variance of (15-year mean − 30-year mean) under independent years.
    - Endpoint: G = (λ_Tmin − λ_Tmax)_fitted − (λ_Tmin − λ_Tmax)_rel.
    - Prediction: G > 0 at all three cut-offs, and an era-blocked bootstrap interval for the pooled G excludes 0. Blocks are 7-year pseudo-origin blocks; cities are resampled within blocks as a sensitivity check.
    - Secondary, declared likely inconclusive: temperature skill against E2. The existing result is +0.10 [−0.04, +0.25] pp, with −0.07 on replication.
*   **Refuted if:** G ≤ 0 at 2 of 3 cut-offs, or its interval includes 0. In that case reliability weighting explains the gap, and E2 with one coefficient is the whole story.
*   **Rivals:**
    - (a) Reliability only.
    - (b) Era-specific Tmax instrument bias (HO-83 period) produces the gap at 1995 alone. This is the methodologist's background point and is not in the folder.
    - (c) Persistence comes through documented station switches, not through the component.
*   **Discriminating experiment:**
    - For (a): the primary endpoint.
    - For (b): λ per origin over all 10 origins plus replication. Rival (b) predicts a gap concentrated in windows that contain the 1980s. The already-observed gap of ≥ 0.43 at 1980, 1995 and 2011 speaks against it.
    - For (c): add an interaction A_city × S_i,p, where S = 1 if the city's `Station Segment` changes within the 30 years ending at p. Rival (c) predicts the D coefficient falls to about 0 among non-switch cities. The mechanism predicts it stays.
*   **Closest prior work:**
    - E2 (team) is the nested parent.
    - Round 1 Generator B dropped a Tmax/Tmin split as algebraically identical under one coefficient.
    - arguez2009improving gives component-specific windows with no skill test.
    - No note covers 7-year persistence by component, so novelty is unverified (X-2).
*   **Claim type:** exploratory
*   **Needs:** master only. About 45 minutes: a short analysis script on the existing regressors, with no new forecaster.
*   **Strengths / Costs:**
    - Strength: turns a supported readout into a severe test, and tells the team whether the diurnal structure is worth carrying into H36.
    - Cost: no direct score gain, and the independent-years variance formula is an approximation.

### H35: The recent city anomaly of the mean of each year's ten hottest daily Tmax values predicts the next-7-year hottest-day anomaly better than the annual maximum's own anomaly does.

*   **Status:** revised (one family with H24, which is refined separately; reconcile the specifications)
*   **Answers findings:**
    - egm-novelty-r2: H24/H35-a, H24/H35-c, X-1, X-2.
    - egm-methodologist-r2: H24/H35-a, H24/H35-b, H24/H35-c, R2-X4.
*   **Mechanism:** E1's hottest-day arm failed (+0.10 [−0.77, +0.97] pp). One reading is attenuation: a 15-year mean of single-day maxima is a noisy measure of a real tail shift. T10 averages out single-day noise.
*   **Specification:**
    - T10_i,y = mean of the ten highest daily Tmax in the year.
    - One validity rule (H24/H35-b): the year is valid if its Tmax missing-day count is ≤ 10, the scoring rule. This replaces the "≥ 85 June–August days" rule.
    - Build per year from daily rows with Date ≤ cut-off, passed through `assert_weather_cutoff`. Use no quality flag derived from full-record statistics.
    - Forecast = 30-year mean of the annual maximum + λ·A_T10. A_T10 is the city part of (15-year mean − 30-year mean of T10) at p; λ is fitted in-fold.
*   **Inspirations:** mckinnon2024pace q1 (closest saved work on upper summer quantiles; background only, since its data run past 2018); katzndblock q4; efron1975data q1.
*   **Prediction (primary endpoint, against the nested parent E1):**
    - Use non-overlapping pseudo-origins p = C−7, C−14, C−21, C−28 with complete 7-year targets.
    - Endpoint: Δr = r(A_T10, F) − r(A_max, F), where F is the city part of (next-7-year mean maximum − 30-year mean).
    - Prediction: Δr ≥ 0.05 with a city-cluster bootstrap 95% interval excluding 0 at C = 2011, and the same sign at 1980 and 1995.
    - Secondary, declared likely inconclusive: hottest-day skill, as a paired difference against E1 fitted by the same procedure on the same rows.
*   **Refuted if:** the Δr interval includes 0, or its sign changes across cut-offs.
*   **Rivals:**
    - (a) Heat waves make the top ten days one event, so there is no noise reduction.
    - (b) Shifts in the maximum are single-day instrument artifacts that T10 dilutes.
    - (c) E1 failed because persistence decays with lead or varies by era (see H37), not because of predictor noise.
*   **Discriminating experiment:**
    - Compute Δr separately for F over leads 1–3 and leads 4–7. Rival (c) predicts T10 helps at neither once lead is accounted for. The mechanism predicts a gain at both.
    - Add one arm with the top 3 days: rival (a) predicts top 3 ≈ top 10 ≈ top 1.
    - The variance go/no-go check is dropped (H24/H35-c).
*   **Closest prior work:**
    - H14 and H2 (team) used the June–August mean and were worse.
    - Round 1 Generator A dropped r-largest values as a level estimator.
    - mckinnon2024pace covers upper quantiles at large scale, with no station forecast.
*   **Claim type:** exploratory
*   **Needs:** the daily table and one build script modelled on `/Users/atabaresa/repos-new/proto-star-challenge/scripts/build_summer_means.py`. About 1.5 hours.
*   **Strengths / Costs:**
    - Strength: the primary endpoint needs no score comparison and is cheap once T10 exists.
    - Cost: its parent E1 failed the gate. Under the fixed plan (R2-X3) this branch cannot be adopted today, so the run is mechanism-only unless the human reopens the branch.

### H36: Adding the Tmin-minus-Tmax contrast of the recent temperature anomaly, scaled by each city's CDD-per-degree, to E2's CDD correction raises CDD skill, because the persistent part of a city's CDD anomaly is the part tied to its persistent night-time offset.

*   **Status:** new (promotes H32's "same split with CDD as target" discriminating arm)
*   **Mechanism:**
    - E2 scales the CDD city anomaly by one coefficient (λ_CDD 0.72/0.66/0.79).
    - CDD is driven by daily mean temperature, so both halves enter. If the Tmin half persists near 1 and the Tmax half near 0.3–0.6, as H23/H32 found for temperature, cities whose anomaly is Tmin-led are under-carried by E2 and Tmax-led cities are over-carried.
*   **Specification:**
    - Base = candidate, metric = CDD.
    - Regressors at each p: A_cdd,city (the E2 term) and D_cdd = k_i,p · (A_tmin − A_tmax)/2.
    - k_i,p is the candidate's CDD-per-degree for city i, refit from rows ≤ p. I did not check which estimator the candidate uses; reuse it unchanged.
    - Forecast = candidate + β·A_cdd + γ·D_cdd, clip [−1, 1].
    - Needs a small extension of `_anomalies`, which now attaches the diurnal halves to temperature rows only.
*   **Inspirations:** hausfather2013quantifying q1 (motivation only); petri2015impacts (CDD climatology; it does not address city persistence); the team's H23/H32 coefficients.
*   **Prediction (primary endpoint, against the nested parent E2's CDD arm):**
    - CDD skill, all years, official folds. The paired year-block difference against `e2_cdd_only` is positive.
    - In-fold γ̂ > 0 at all three cut-offs.
    - Expected size: +0.1 to +0.3 pp of CDD skill, about +0.03 to +0.08 raw. This is at the edge of detection; the nested interval for temperature was ±0.15 pp.
*   **Refuted if:** γ̂ ≤ 0 at any official cut-off, or the paired difference against E2 is ≤ 0 on the official folds or on the replication set.
*   **Rivals:**
    - (a) CDD is a warm-season quantity and annual Tmin anomalies are winter-weighted, so the annual contrast is the wrong regressor (H17's seasonal point).
    - (b) Reliability only (H32 rival a).
    - (c) k_i noise in low-CDD cities drives γ̂.
*   **Discriminating experiment:**
    - Fit γ separately for the top and bottom halves of cities by 30-year mean CDD at p. Rival (c) predicts the sign is unstable in the low half. Under the mechanism and rival (a), the gain concentrates in warm cities, where summer is a larger share of the year.
    - Compare with H32's G: if G ≤ 0 (reliability explains temperature), H36's mechanism loses its basis even if γ̂ > 0.
*   **Closest prior work:**
    - E2's CDD arm (parent); H5 and H17 (team; CDD from temperature).
    - The rejected delta method.
    - The INDEX Gaps list no observational city-level CDD sensitivity study, so novelty is unverified.
*   **Claim type:** exploratory
*   **Needs:** master only. About 1 hour.
*   **Strengths / Costs:**
    - Strength: one extra coefficient on an adopted parent, with the sign predicted in advance from an independent metric's result. It is the only kept hypothesis that can enter the submission under the fixed adoption rule.
    - Cost: the expected gain is small and may sit inside the interval.

### H37: The persistence of a city's hottest-day anomaly decays with lead, so lead-group coefficients (leads 1–3 and leads 4–7) fitted in-fold beat E1's single coefficient.

*   **Status:** new
*   **Mechanism:**
    - On the official folds E1's hottest-day arm scored +0.83 pp in years 1–3 and −0.44 pp in years 4–7.
    - A single λ fitted on pooled annual rows is a compromise between a useful short-lead coefficient and a near-zero long-lead one.
    - The pooled fit also over-represents short leads: lead 1 has 30 pseudo-origins and lead 7 has 24. That pushes λ̂ toward the short-lead value and hurts long leads.
*   **Specification:**
    - E1's hottest-day arm (30-year mean + λ·A_city, window 15), with A_city interacted with two lead-group indicators.
    - Fit λ_1–3 and λ_4–7 by least squares on pseudo-origin rows. Each row's lead is h = year − p; all inputs are from rows ≤ p.
    - Clip [0, 1].
*   **Inspirations:**
    - vandendool2011readme q3 (operational OCN damped by a-priori skill; the closest saved method).
    - gardner1985forecasting (damping by horizon; business forecasting, outside the subfield).
    - huang1996longlead q3.
*   **Prediction (primary endpoint, against the nested parent E1's hottest-day arm):**
    - Hottest-day skill, all years, as a paired difference against E1: positive on the official folds.
    - λ̂_1–3 − λ̂_4–7 ≥ 0.1 at all three cut-offs.
    - Years 4–7 hottest-day skill is no longer negative (≥ −0.1 pp).
*   **Refuted if:** the coefficient ordering fails at any cut-off, or the paired difference against E1 is ≤ 0 on the official folds or the replication set.
*   **Rivals:**
    - (a) The years 1–3 against years 4–7 pattern is a fold accident. Early origins gave E1 +1.73 pp overall, which suggests era dependence, not lead dependence.
    - (b) Persistence is carried by station steps and does not decay.
    - (c) The pattern only reflects the unequal lead weighting in the fit.
*   **Discriminating experiment:**
    - For (c): refit E1's single λ with rows weighted equally per lead. If that alone removes the years 4–7 loss, the lead-group structure is not needed.
    - For (a): report λ̂ by lead group at all 10 origins plus replication. Rival (a) predicts an unstable order.
    - For (b): restrict to cities with a segment change inside the window (in-fold definition). Rival (b) predicts no decay there.
*   **Closest prior work:**
    - E1 (parent).
    - H16 (team; lead-decaying residual persistence for temperature and CDD, based on the last year's residual, not the 15-year anomaly).
    - vandendool2011readme damps by skill, not by lead, within annual targets.
*   **Claim type:** exploratory. The motivating split by lead was read off the official folds (R2-X1), so the replication set carries the weight.
*   **Needs:** master only. About 45 minutes: a lead-group interaction in `anomaly_correction_forecast`.
*   **Strengths / Costs:**
    - Strength: targets hottest day, which has half-weight headroom and zero current skill, and years 1–3 match the live board.
    - Cost: its parent failed the root gate, so under R2-X3 it is not adoptable unless the human registers it as a new root. Its motivation is post hoc on the test folds.

---

## Dropped Candidates

- **H31 (round to whole °F):** dropped; the gain would not transfer.
  - Answers egm-methodologist-r2 H31-a (Blocker) and H31-b, and egm-novelty-r2 H31-a.
  - The lattice gate failed: all 210 cities have decimal daily Tmax in 2018, on 43–57% of days in every month. 2018 `Max Tmax` is 59% whole °F, against 100% before.
  - No per-city salvage exists, because no city stayed on whole degrees.
- **H33 (wet-day frequency):** dropped as a score hypothesis.
  - Answers egm-novelty-r2 H25/H33-a and H25/H33-b, and egm-methodologist-r2 H25/H33-a, b and c.
  - It is contained in H25 (refined separately), so it should not be a second family.
  - Its parent, E1's precipitation arm, scored −0.21 pp.
  - The expected gain of +0.2 to +1.0 pp is at or below the detection limit.
  - The `Wet Days` threshold and the 2018 precipitation precision are unconfirmed.
  - If H25 is kept, H33's three-regressor ordering (wet days ≥ body total > total) belongs there as a secondary arm.
- **H34 (data-chosen break year):** dropped as infeasible within 1–2 hours once the findings are met.
  - Answers egm-novelty-r2 H34-a to H34-d and egm-methodologist-r2 H34-a to H34-c.
  - The findings require a re-scan at every pseudo-origin, a drift arm, a pairwise or justified reference, and a permutation null.
  - Its parent E1 failed, and H22 already covers its sparse-shift premise.
  - Its one cheap piece, the documented-switch interaction, is kept as a discriminating arm in H32 and H37.
- **Switch-conditional persistence as its own hypothesis:** not kept.
  - Round 1 already rejected current-segment levels, and U3 and H15 cover the same ground.
  - It survives only as the rival (c) arm of H32.
- **Diurnal split applied to hottest day (Tmax persistence as the hottest-day predictor):** a variation of E1 with a noisier link; no distinct test.

## Leads to Fetch (unverified, from memory or the INDEX lead list; not used as support)

- Karl et al. (1993), BAMS: asymmetric Tmax and Tmin trends (H32, H36).
- Menne, Williams & Palecki (2010), JGR: U.S. siting effects on Tmax and Tmin (H32).
- Quayle et al. (1991), and the HO-83 Tmax bias literature (H32 rival b).
- Coles (2001): r-largest order statistics (H35).
- van den Dool (2007), *Empirical Methods in Short-Term Climate Prediction*: OCN damping by lead (H37).
- Gneiting (2011), JASA: recorded for H31's history only.

## Thin Spots

- No note covers 7-year persistence of station anomalies by diurnal component, by lead, or for annual maxima. Fewer than ten notes bear on any kept hypothesis, so all novelty is unverified. The searches listed in egm-novelty-r2 X-2 still stand.
- No note covers CDD sensitivity to Tmin against Tmax at city level (H36).
- Items I did not verify in code:
  - the candidate's CDD-per-degree estimator;
  - the chronology of `Station Segment`;
  - whether an invariance test exists for `anomaly.py`.

## Files read

- `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md` (Round 2: E1–E4, the Generator B section, the Final table)
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses_review.md` (Round 2: finding IDs, the novelty sections for H23–H34, the full methodologist report)
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/experiments.md` (rows dated 2026-11-10)
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/candidate_error_analysis.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/round2_assistant.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/round2_e2_family.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/round2_combined.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md` (notes not re-read)

### Refiner A, round 3 (Opus 5.5, default model)

# Round 2 REFINE: E1–E4 and H21–H25 (Mode: REFINE)

I ran nothing and wrote no files. I used only the supplied files, listed at the end. The literature notes are unaudited, so the inspirations below motivate the hypotheses; they are not evidence. Generator B's H31–H35 were context only.

## Background

The task is to raise the official score, the mean of four per-metric relative-MAE skills against each city's 30-year mean, for 2019–2025 annual forecasts in 210 U.S. cities, using data through 2018. The Round 2 backtests (the 2026-11-10 rows of `docs/experiments.md`) leave one change that meets the adoption rule:
- **E2** damps the city-specific part of the candidate's temperature and CDD anomaly with an in-fold λ.
- Raw score: +0.22 [+0.07, +0.35] on the official folds, +0.05 over the 7 cut-offs, +0.07 on the 1934/1941/1948 replication set.

Every hottest-day and precipitation arm failed its gate. E1's hottest-day gain appears only at the early origins: +1.73 [+0.93, +2.51] pp, against +0.10 [−0.77, +0.97] pp on the official folds. The H23 diurnal split showed its predicted coefficient pattern but no score gain over E2. Two questions remain open in this scope: can E2's single coefficient be refined by a detectable amount, and can the early-origin hottest-day signal transfer to the recent era at all?

## Decisions at a glance

| ID | Decision | One-line reason |
|---|---|---|
| E1 | dropped | Fails the gate on the official folds; −0.15 pp over 7 cut-offs. Its early-only gain is explained by H27. |
| E2 | kept (record revised; no new score test) | The only adopted arm. Two cheap checks before submission are listed. |
| E3 | dropped | The data confirm the transfer Blocker: −1.72 [−2.78, −0.71] pp. |
| E4 | dropped | Null, +0.17 [−1.46, +1.80] pp, against a 0.65 pp ceiling. |
| H21 | dropped | Its own pre-declared mechanism rule refuted it (λ_regional ≥ λ_local at 2 of 3 cut-offs). |
| H22 | dropped | Its parent E1 failed the gate; the sparse-shift premise is weakened; power is too low. |
| H23 | revised | The temperature score test is done (inconclusive). The new test is a CDD contrast nested in E2, plus a reliability-corrected mechanism endpoint. |
| H24 | dropped | Its parent failed; it duplicates H35; it needs a daily build. |
| H25 | dropped | Its parent (E1's precipitation arm) failed; the effect is at or below the detectable size; measurement and transfer doubts. |
| H26 | new | A lead-dependent city-part coefficient, nested in E2. |
| H27 | new | Explains E1's early-only gain as an artefact of the 1930s and 1950s regimes, with a sign prediction on unseen origins. |

## Derived from the supplied data (my arithmetic, not from any note)

1. **The recent anomaly is a half-window change.** With 30 valid years, m30 = (m_first15 + m_last15)/2. So the E-family anomaly A = m15 − m30 = (m_last15 − m_first15)/2. Every "persistence" result in this family asks whether a change from the first half of the reference window to the second half carries on into the targets (H27).
2. **E2's gain sits in years 4–7.** E2's raw difference is +0.22 for all years and +0.37 for years 4–7. That implies about +0.02 for years 1–3, from (7·0.22 − 4·0.37)/3. This is approximate, because block skills are ratios of MAEs. The combined arm shows the same pattern: +0.24 all years, +0.42 years 4–7 (H26).
3. **Nested comparisons are narrow.** H23 against E2 gave temperature skill +0.10 [−0.04, +0.25] pp. That is a half-width of about 0.15 pp, or about ±0.04 raw. Refinements nested in E2 can detect effects of a few hundredths of a raw point. Comparisons against the candidate cannot.
4. **Early reference windows hold heat that did not recur.**
   - The 30-year mean over-forecasts the hottest day by +1.63, +1.02 and +0.60 °F at the 1955, 1962 and 1969 origins.
   - At every later origin the error is under 0.7 °F in absolute value, except 2005 (−1.32) (H27).
5. **λ̂ drifts upward by era.**
   - E2: λ_T is 0.60, 0.65 and 0.84 at the 1980, 1995 and 2011 cut-offs.
   - H23: λ_Tmin is 1.04 at 2011.

   This is a rival for H26 and a transfer caveat for E2.

## Rules common to the kept hypotheses

- **Pseudo-origins (R2-X2).** Every kept hypothesis uses the `anomaly_correction_forecast` construction, which I checked in `src/proto_star/anomaly.py`.
  - The pseudo-origins are p = c−30 … c−1, spacing 1.
  - At each p, `_errors` refits the base forecaster on `train.loc[Year <= p]`. That recomputes the pooled slope over p−39..p with its floor, the 10/15-year levels and the CDD per degree.
  - `_anomalies` computes m30 from years p−29..p, the 15-year anomaly from the last 15 valid years ≤ p, and the national and city parts across the cities valid at p.
  - Targets are actual values in p+1..min(p+7, c); truth comes from `annual_to_long(train, cutoff_year=c)`.
  - So every input is computed from years ≤ p and every target from years ≤ c.
  - Each config adds an invariance test: perturb all rows after c and assert identical coefficients and forecasts.
- **Switch indicators (R2-X2 item 4)** come from per-year `Station Changes` in years ≤ p, never from the `Station Segment` numbering.
- **Multiplicity (R2-X3).**
  - The E2 branch now holds four tests: H21, H23-temperature (≡ H32), H23-CDD and H26. Under Holm, the smallest p-value must be below 0.0125, which means a 98.75% interval must exclude 0.
  - The adoption rule is unchanged: pass the gate, show the same sign on the replication set, and show the same coefficient sign at all three cut-offs. The final composite is run once.
- **Reporting (R2-X5).** Report per-fold differences and coefficients at the official folds and at all 13 origins, plus a region × fold cluster bootstrap as a sensitivity check. State the resample count and the block definition.
- **Post-2018 knowledge (R2-X6).** Every constant below (clips, the lead centring, the region list rule) is fixed in this report from the supplied backtests. No pretrained model is involved. H27 changes no forecast.

---

### E2: Damping only the city-specific part of the candidate's recent temperature and CDD anomaly, with λ fitted in-fold, raises temperature skill over the candidate.

*   **Status:** revised (adopted; record updated; no new score test)
*   **Answers findings:** egm-novelty-r2-E2-a, E2-b, E2-c; egm-methodologist-r2-E2-a, E2-b, E2-c, R2-X1, R2-X5
*   **Mechanism:**
    - The city part (cross-city mean removed) of the 15-year anomaly is partly a persistent offset, partly sampling noise and partly a reverting anomaly. The candidate carries it at weight about 1.
    - As implemented (`window=15`, `national=False`, `split="none"`), forecast = candidate + β·A_city and λ = 1 + β.
    - λ is therefore defined on the 15-year anomaly, not on the candidate's 10/15-year blend (E2-c).
*   **Inspirations:** efron1975data q1–q2; vandendool2011readme q3; arguez2009improving q2; claeskens2016forecast q2 (one pooled coefficient per metric).
*   **Prediction (tested):**
    - Temperature skill: +0.38 [+0.04, +0.71] pp.
    - Raw score: +0.22 [+0.07, +0.35].
    - CDD skill: +0.49 [+0.09, +0.91] pp.
    - λ_T 0.60/0.65/0.84 and λ_CDD 0.72/0.66/0.79 at 1980/1995/2011.
*   **Refuted if (methodologist E2-a):** λ̂ ≥ 0.9 at 2 or more cut-offs, or a point estimate ≤ 0. Not met.
*   **Rivals:**
    - (a) The gain is plain damping toward m30, the U2 effect. Unlikely: U2 lost −0.92 in years 4–7, while E2 gains +0.37 there.
    - (b) The effect is specific to an era: λ̂ drifts upward, and the 7-cut-off result is only +0.05 [−0.05, +0.15].
    - (c) MAE masking (see H26).
*   **Discriminating experiment (pre-submission checks, not new hypotheses):**
    1. Log λ̂ at the 2018 cut-off (pseudo-origins 1988–2017). If temperature λ̂ ≥ 0.9, E2 barely moves the submission, and its backtest gain does not describe 2019–2025.
    2. R2-X5: λ̂ at all 10 error-analysis origins, plus the region × fold cluster bootstrap.
*   **Closest prior work:**
    - vandendool2011readme q3 damps the whole OCN anomaly toward climatology, with the factor set from a-priori skill. E2 damps only the city-minus-national part, fits λ by least squares at pseudo-origins, and keeps the national part and the pooled trend.
    - efron1975data sets the weight from noise variance; E2 fits it predictively.
    - arguez2009improving q2 uses a station-specific window; E2 uses one pooled λ per metric.
    - **Team:**
      - H11's weight is "estimated in-fold" with no named rule (`hypotheses.md` line 356). Whether its national-target arm ran is not in the supplied files (E2-b).
      - H21 was run in the same design (E2-b, methodologist): it found λ_regional ≥ λ_local, so the local part is not the persistent one.
      - U2 damps everything; U1 learns weights inside a direct model.
      - E2 is the nested parent of H21, H23 and H26.
*   **Claim type:** exploratory (R2-X1)
*   **Needs:** the existing config. Checks 1–2 take about 30 minutes.
*   **Strengths / Costs:**
    - Strength: the only arm that meets the adoption rule.
    - Cost: the gain fades over 7 cut-offs and λ̂ drifts upward by era, so a realistic 2019–2025 gain is at most about +0.05 to +0.2 raw.

### H23: The persistent city part of recent temperature anomalies is carried by Tmin beyond what sampling reliability explains, so adding a Tmin-minus-Tmax contrast, scaled by each city's CDD per degree, to E2's single CDD coefficient will raise CDD skill over E2.

*   **Status:** revised.
    - The temperature score test against E2 has already run and was inconclusive: +0.10 [−0.04, +0.25] pp on the official folds, −0.07 on the replication set. It is not repeated.
    - The revision moves the score test to CDD, which H23's own discriminating experiment listed and which `anomaly.py` does not yet split. It also makes the reliability-corrected gap the mechanism endpoint.
    - H23 and H32 form one family; H32 is refined separately. A pass on H32's temperature endpoint and this CDD endpoint must not be counted as independent support.
*   **Answers findings:** egm-novelty-r2-H23/H32-a, H23-b, H23/H32-c, X-1; egm-methodologist-r2-H23/H32-a, H23/H32-b, H23/H32-c, R2-X2, R2-X4, R2-X5
*   **Mechanism:**
    - Local siting, urban and instrument influences shift Tmin and stay in place. City-level Tmax anomalies follow moisture and land-surface regimes, which revert.
    - The in-fold readout fits this: λ_Tmin 0.83/0.83/1.04 against λ_Tmax 0.31/0.40/0.58. It also fits a simple reliability difference.
    - CDD's city anomaly is roughly k_i times the warm-season temperature city anomaly. So E2's single λ_CDD should under-weight the Tmin part.
    - **Specification, fixed now:**
      - On CDD rows: forecast = candidate + β_c·A_city^CDD + β_d·D_i, with D_i = k_i(p)·(tmin_half_i − tmax_half_i).
      - The halves are as in `anomaly.py`: city parts of the 15-year Avg Tmin and Avg Tmax anomalies, each screened by its own missing-days column, divided by 2.
      - k_i(p) is the candidate's own CDD-per-degree coefficient, re-estimated from years ≤ p.
      - β_d = 0 recovers E2. Clips: β_c ∈ [−1, 1], as in E2; β_d ∈ [−1, 1].
      - Temperature rows are unchanged from E2.
      - The scored rows are identical to E2's. A missing D_i is set to 0 (H23/H32-c).
*   **Inspirations:**
    - hausfather2013quantifying q1 (motivation only; it covers century-scale trends; outside the subfield, urban climatology).
    - menne2009homogenization q3 (outside the subfield, homogenization).
    - efron1975data q1–q2 (outside the subfield, statistics).
    - mueller2012hot q1, q3 (the Tmax-side regime).
    - petri2015impacts q4 (CDD spans 163 to 4,608 across cities, hence the k_i scaling).
    - arguez2009improving q3–q4 (motivation only, per H23/H32-c).
*   **Prediction:**
    - **Primary endpoint (against the nested parent E2):** CDD skill, all years, official folds, paired year-block bootstrap. Positive, with a Holm-adjusted interval excluding 0. Expected +0.1 to +0.3 pp, which is probably inconclusive.
    - **Coefficient:** β̂_d > 0 at all three cut-offs.
    - **Mechanism endpoint:** the reliability-corrected persistence gap ρ_min − ρ_max > 0, with a pseudo-origin-block bootstrap interval (blocks of 7 consecutive pseudo-origins) excluding 0 at 2 or more of 3 cut-offs.
*   **Refuted if:**
    - β̂_d ≤ 0 at 2 or more of 3 cut-offs, or the primary point estimate is ≤ 0.
    - The reliability account wins if the corrected gap's interval contains 0 at 2 or more cut-offs while the uncorrected gap stays at about 0.4 or more.
*   **Rivals:**
    - (a) Reliability: Tmin city anomalies are simply less noisy.
    - (b) Seasonal: warm-season Tmax persists differently from annual Tmax (H17 territory), so β_d's sign for CDD can differ from temperature's.
    - (c) Era-specific Tmax instrument bias, the methodologist's HO-83 rival.
    - (d) Station steps (H32's switch arm).
*   **Discriminating experiment:**
    1. **Reliability correction.** Use balanced pseudo-origins c−30 ≤ p ≤ c−7.
       - Regress f_i(p), the 7-year future city-part anomaly of Avg Temp, on (tmax_half, tmin_half) to get Λ.
       - Σ_A is the pooled cross-city covariance of the halves.
       - V is (1/15 − 1/30) times the mean, over cities, of the within-window (p−29..p) covariance of the national-removed, linearly detrended annual half-series.
       - Then ρ = (Σ_A − V)⁻¹ Σ_A Λ.
       - Sensitivity: inflate V by (1 + r)/(1 − r), with r the pooled lag-1 autocorrelation.
       - Rival (a) predicts ρ_min ≈ ρ_max.
    2. **The sign of β̂_d** separates the seasonal rival (b).
    3. **The gap at each of the 10 origins** tests rival (c): it predicts the gap is confined to one era.
    4. **Splitting cities by in-fold documented switch** tests rival (d): it predicts the gap vanishes in non-switch cities.
*   **Pseudo-origin construction:** as in the common rules. Additionally, the halves, A_city^CDD, the national parts and k_i(p) all come from rows ≤ p. The reliability readout uses p ≤ c−7 and builds V and Σ_A from rows ≤ p. Invariance test included.
*   **Closest prior work:**
    - arguez2009improving computes component-specific OCN windows with no skill test. Here the component weights are fitted out of sample and corrected for reliability.
    - Round 1 Generator B dropped a Tmax/Tmin split as algebraically identical to the candidate. That holds only at β_d = 0, which is this hypothesis's nested null (H23-b).
*   **Claim type:** exploratory
*   **Needs:**
    - Master columns: `Avg Tmax`, `Avg Tmin`, `Miss Tmax`, `Miss Tmin`, `cdd`, `Station Changes`.
    - About 45 minutes to attach D_i to the CDD rows in `_anomalies`. This needs k_i(p) from `trend.py`, which I did not read.
    - About 30–45 minutes for the reliability readout.
    - About 1.5 hours in total.
*   **Strengths / Costs:**
    - Strength: it tests the one Round 2 mechanism that showed its predicted pattern, on a second metric, with one extra coefficient nested in E2.
    - Cost: the CDD gain is probably below the Holm-adjusted detection width. If rival (a) wins, the temperature finding is a noise artefact.

### H26: Letting E2's city-part coefficient vary linearly with lead, λ_h = λ̄ + b·(h − 4) with b fitted in-fold, will raise the raw score over E2, because the city anomaly is a persistent offset plus a component that decays over a few years, so one pooled λ over-shrinks at leads 1–3 and under-shrinks at leads 5–7.

*   **Status:** new (a refinement of E2, which it nests at b = 0)
*   **Answers findings:** egm-methodologist-r2-R2-X1, X2, X3, X4, X5, X6; egm-novelty-r2-X-2
*   **Mechanism:**
    - Suppose A_city = θ + η + e: a persistent offset θ, a part η with memory ρ per year, and noise e.
    - Then the slope of the lead-h future city anomaly on A is λ_h = (Var θ + ρ^h·Var η)/Var A, which falls as h grows.
    - E2 fits one λ averaged over leads. The block pattern in data item 2 fits this picture.
    - **Specification, per metric (temperature and CDD):**
      - forecast = candidate + β_0·A_city + β_1·(h − 4)·A_city, so λ_h = 1 + β_0 + β_1(h − 4).
      - Clips: β_0 ∈ [−1, 1], as in E2; β_1 ∈ [−0.2, 0.2]; λ_h ∈ [0, 1.5].
      - The same unweighted least squares as `anomaly.py`.
*   **Inspirations:**
    - ho2013statistical q1 (trend plus AR(1) residual).
    - krueger2011simple q3.
    - huang1996longlead q3.
    - vandendool2011readme q3.
    - gardner1985forecasting q1–q2 (outside the subfield: damping at long leads in business series).
    - smith2009simple q1 and claeskens2016forecast q2 (outside the subfield, econometrics: one extra parameter rather than seven free λ_h).
*   **Prediction:**
    - **Primary endpoint (against the nested parent E2):** raw score, all years, official folds, paired year-block bootstrap on the same resamples. Positive, with a Holm-adjusted interval excluding 0. Expected +0.02 to +0.08 raw, against a nested half-width of about ±0.04 (data item 3), so it may well be inconclusive.
    - **Coefficient:** b̂ < 0 for temperature at all three cut-offs, and a positive years 1–3 difference against E2.
*   **Refuted if:**
    - b̂ ≥ 0 for temperature at 2 or more of 3 cut-offs; or
    - the primary point estimate is ≤ 0; or
    - b̂ loses its sign in the balanced re-fit (experiment 1).

    If b̂ < 0 but the interval includes 0, the result is inconclusive and the change is not adopted.
*   **Rivals:**
    - (a) **MAE masking.** λ_h is flat, but a city-part change moves MAE only where the common error is small.
    - (b) **Truncation × era drift.** Pseudo-origins c−6..c−1 contribute only short leads and are the most recent, and λ̂ drifts upward by era. That can make the short-lead λ look higher with no lead decay.
    - (c) **Growing city-specific trends.** λ_h would rise with lead; λ_Tmin = 1.04 at 2011 hints at this. Predicts b̂ > 0.
    - (d) **CDD trend interaction.** The candidate's CDD trend term (slope × k_i) varies by city and grows with lead. If A_city^CDD correlates with k_i, E2 partly damps that term, which concentrates CDD gains at long leads.
*   **Discriminating experiment:**
    1. **Balanced re-fit** on p ≤ c−7, so each pseudo-origin contributes all 7 leads. Rival (b) predicts b̂ → 0.
    2. **E2's MSE gain over the candidate, by lead.** For a city-part change that sums to zero over the scored cities, the common error cancels from the MSE difference. Rival (a) predicts a flat MSE profile alongside a lead-concentrated MAE profile. The mechanism predicts the MSE gain is smallest at leads 1–3.
    3. **Free λ_h** (7 coefficients, diagnostic only). The mechanism predicts a monotone decline; rival (c) predicts a rise.
    4. **Block pattern by metric.** Rival (d) predicts the concentration in years 4–7 appears for CDD only.
    5. **b̂ at the replication and early origins.** Adoption needs the replication sign.
*   **Pseudo-origin construction:** as in the common rules. Lead h = target year − p at pseudo-origins and year − c at the cut-off. Invariance test included.
*   **Closest prior work:**
    - ho2013statistical damps the residuals of each grid box's own series with an AR(1). H26 fits one pooled lead slope on the city part only, at in-fold pseudo-origins, with the national part and the trend unchanged.
    - **Team:**
      - H16 uses lead-specific φ_h on the last year's residual (not significant).
      - U1 is a direct horizon model; it lost in years 4–7 by under-extrapolating the trend.
      - Round 2 Generator A dropped "lead-dependent decay" as a U1 duplicate. H26 isolates that single mechanism, nested in the adopted arm.
*   **Claim type:** exploratory (motivated by E2's official-fold block pattern)
*   **Needs:** master only. About 30 minutes of code: a lead column in `_errors`, one interaction regressor, and the lead at forecast time. About 30 minutes of runs over the four origin sets.
*   **Strengths / Costs:**
    - Strength: one parameter per metric, nested in the only adopted arm, aimed at the years 1–3 deficit, and each of the four rivals has a distinct readout.
    - Cost: the expected gain is at the edge of detection under Holm, and rival (b) can produce a negative b̂ with no lead decay.

### H27: E1's early-origin hottest-day gain comes from the 1930s and 1950s drought-heat regimes sitting inside the reference windows, not from persistent city shifts, so in-fold E1 will lose at the replication origins where that heat sits in the recent 15 years (1941, and less clearly 1948).

*   **Status:** new. It explains E1's pattern by era and bears on H34 and H35, which are refined separately.
*   **Answers findings:** egm-methodologist-r2-E1-b, R2-X1, R2-X5; egm-novelty-r2-E1-b, X-2
*   **Mechanism:**
    - By data item 1, E1's A is half the change from the first to the second half of the reference window.
    - At the 1955 and 1962 origins, the 1930s heat sits in the first half. After the national part is removed, regionally coherent hottest-day excess makes A negative for the affected cities. Their post-regime targets are indeed below m30. This looks like persistence with no persistent city shift.
    - At the 1941 origin (window 1912–1941, targets 1942–1948), the regime sits in the last 15 years and the targets come after it. So a positive λ̂ points the wrong way.
    - Windows from 1951 to 2011 hold no comparable regime, hence E1's null result there.
    - Data item 4 supports the premise.
*   **Inspirations:**
    - vose2017temperature q2, q4.
    - mascioli2017timing q2.
    - easterling2017precipitation q3 (multiyear droughts in the 1930s and 1950s).
    - mueller2012hot q1, q3 (outside the subfield: land–atmosphere coupling).
    - menne2009homogenization q3 and wilks2013performance q2 (outside the subfield: the station-step rival).
*   **Prediction:**
    - **Primary endpoint:** E1 minus the candidate, hottest-day skill, all years, pooled over the replication origins 1934/1941/1948, with the same paired bootstrap. Point estimate < 0.
      - This is conditional on in-fold λ̂ > 0 at 1941 and 1948. If λ̂ is clipped to 0, E1 equals the candidate and the test is void.
    - **Per origin:** 1941 < 0 and 1948 ≤ 0. No prediction for 1934, whose targets (1935–1941) still fall in the 1930s.
    - **Early origins:** in the 1955/1962/1969 gain, the central-U.S. regions' share of the summed per-city MAE reduction exceeds their share of cities by at least 15 points.
*   **Refuted if:**
    - the pooled replication estimate and the 1941 difference are both > 0 with λ̂ > 0; or
    - at least 2/3 of the early gain comes from cities with a documented change inside the 15-year anomaly window; or
    - the early gain is spread across regions in proportion to their city counts.
*   **Rivals:**
    - (a) Relocation or instrument steps whose share differs by era (E1-b, H15/H34 territory).
    - (b) Real persistent land-use effects on hot extremes (vose2017temperature q6). This predicts gains wherever the change sits, including at 1941.
    - (c) Chance across three overlapping early origins.
*   **Discriminating experiment:**
    - Run E1 at the replication origins.
    - Break down the per-city early gain by `region` and by in-window documented switch.
    - Report λ̂ at all 13 origins (E1-b).
    - Expected readouts:
      - Rival (a): the gain follows switch cities in every era.
      - Rival (b): the gain follows regions and keeps its sign at 1941.
      - H27: the gain follows regions and flips sign at 1941.
    - Secondary readout (exploratory): the same breakdown of H21's early temperature gain (+2.37 pp).
*   **Pseudo-origin construction:**
    - E1 exactly as it was run: base = candidate, `hottest_day_temp`, window 15, national part off, and the E1 config's clip. I did not read the config; it must match.
    - At each c ∈ {1934, 1941, 1948}: p = c−30..c−1, with m30 and A from years ≤ p and targets in (p, c].
    - Switch indicator: any `Station Changes` > 0 in years c−14..c.
    - The list of central-U.S. `region` labels is fixed before the run.
*   **Closest prior work:** vose2017temperature q4 and mascioli2017timing q2 describe the 1930s artefact in trends. H27 predicts how that artefact enters a damped-anomaly forecaster's skill, depending on where the regime falls in the reference window, as a sign prediction on unseen origins. Team: E1, H14 (+3.40 [+1.64, +5.07] pp early against −1.40 on the official folds) and H21's early gain.
*   **Claim type:** confirmatory for the 1941 sign and the pooled replication sign, provided E1 has not yet been run on those origins (the supplied log reports no such run); exploratory otherwise.
*   **Needs:** the existing E1 config at the replication cut-offs (about 20 minutes) and the per-city breakdown (about 30 minutes). The 1934 cut-off needs pseudo-origin windows back to 1875, so fewer cities enter λ̂ there.
*   **Strengths / Costs:**
    - Strength: a sign prediction on unseen origins that a persistent-shift account contradicts. It also decides whether hottest-day city-anomaly methods (H34, H35) deserve time before the deadline.
    - Cost: it cannot raise the score. If it holds, the hottest day stays on m30.

---

## Findings answered, by ID

- **egm-novelty-r2-**
  - **X-1:** H23 is counted with H32 as one family. H24 and H25 are dropped here; their B twins are handled separately.
  - **X-2:** novelty is unverified for H23, H26 and H27 (see Thin Spots).
  - **E1-a, E1-b, E1-c:** E1 is dropped on data. Its lineage is recorded: vandendool2011readme q3 and H12's own-city arm. As implemented, the national part gets weight 0 (`national=False`). The whole-anomaly arm would be the rejected window blend, so it was not proposed.
  - **E2-a, E2-b, E2-c:** answered in E2's record. The H11 national-arm question cannot be settled from the supplied files.
  - **E3-a, E3-b, E3-c:** E3 is dropped. κ̂ per fold is not in the supplied data.
  - **E4-a, E4-b, E4-c:** E4 is dropped.
  - **H21-a, H21-b:** H21 is dropped.
  - **H22-a:** H22 is dropped.
  - **H23/H32-a, H23-b, H23/H32-c:** H23 is revised.
  - **H24/H35-a, H24-b, H24/H35-c:** H24 is dropped; the family continues only under H35.
  - **H25/H33-a, H25/H33-b:** H25 is dropped.
- **egm-methodologist-r2-**
  - **R2-X1:** everything kept is exploratory except H27's conditional replication sign.
  - **R2-X2:** each construction is stated, with an invariance test.
  - **R2-X3:** Holm with m = 4 in the E2 branch; adoption rule unchanged.
  - **R2-X4:** H23 and H26 each have a primary endpoint against E2.
  - **R2-X5:** per-origin results and the cluster bootstrap are required.
  - **R2-X6:** constants are fixed in this report.
  - **R2-X7:** costs:
    - E2 checks about 30 minutes;
    - H27 about 50 minutes;
    - H26 about 1 hour;
    - H23 about 1.5 hours.
  - **R2-X8:** acknowledged.
  - **E1-a:** E1 fails the gate. **E1-b:** carried into H27.
  - **E2-a:** the rule was applied; E2 is not refuted. **E2-b:** read together with H21. **E2-c:** λ is defined on the 15-year anomaly.
  - **E3-a:** confirmed by data. **E3-b, E3-c:** moot.
  - **E4-a:** confirmed: the interval is ±1.6 pp against a 0.65 ceiling. **E4-b, E4-c:** moot.
  - **H21-a, H21-c:** moot. **H21-b:** the power concern was borne out.
  - **H22-a, H22-b, H22-c:** dropped.
  - **H23/H32-a, H23/H32-b, H23/H32-c:** revised.
  - **H24/H35-a, H24/H35-b, H24/H35-c:** dropped.
  - **H25/H33-a, H25/H33-b, H25/H33-c:** dropped.

## Dropped Candidates

**Earlier hypotheses:**
- **E1:** fails the gate on the official folds (+0.10 [−0.77, +0.97] pp) and is −0.15 pp over 7 cut-offs. The early-only gain is examined in H27.
- **E3:** infeasible to transfer (the Blocker), and the data confirm it: −1.72 [−2.78, −0.71] pp, −1.20 over 7 cut-offs.
- **E4:** null (+0.17 [−1.46, +1.80] pp; −0.38 over 7 cut-offs), with a ceiling below the detectable effect.
- **H21:** refuted by its own pre-declared rule (λ_r ≥ λ_l at 2 of 3). Its early gain (+0.59 raw) is not a rescue; it is a secondary readout in H27. A reliability-corrected re-reading would be post hoc and is not proposed.
- **H22:** its parent failed under the R2-X3 gatekeeping, and re-rooting it now would add an unplanned root. H1's own-segment arm (−0.30 [−0.70, +0.17]) weakens the sparse-shift premise, and H22-a's power concern stands. If H27's rival (a) wins, a successor with a new ID could be tested after the deadline.
- **H24:** its parent failed; it duplicates H35; it needs a 1.5-hour daily build; and under H27 the signal it would measure better may be a regime artefact.
- **H25:** E1's precipitation arm failed. The city-part slope is 0.21 with a correlation of 0.12 or less, so the effect is at or below the detectable size. The `Wet Days` threshold is unconfirmed. The 2018 tmax precision break raises the same transfer question for wet-day counts.

**New candidates drafted this round and dropped:**
- **λ fitted by absolute-error regression (LAD) instead of least squares:** the effect on a single pooled coefficient is below the detectable size.
- **Per-city reliability-weighted λ_i (Efron–Morris):** my estimate is about 0.15 pp, below detection. Both generators also dropped it earlier.
- **λ fitted on the last 15 pseudo-origins only:** a tuning knob chosen after seeing the drift in λ̂ (a forking path).
- **λ conditioned on documented switches:** a duplicate of H32's switch arm.
- **A fitted coefficient on the national part:** the common-shift family, which has the E3 and H4 blockers.
- **Shrinking the per-city CDD-per-degree coefficient:** the trend-term error it would fix is about 6 CDD, which is negligible.
- **The city part of `Avg Tmax` as a hottest-day predictor:** the E1/H14 family, which has failed on recent folds.
- **Errors demeaned within (pseudo-origin, year):** a precision change that leaves β̂ essentially unchanged.
- **A two-block lead λ (years 1–3 and 4–7):** a more arbitrary alternative to H26's linear form.

## Leads to Fetch (unverified, from memory; not used as support)

- van den Dool (2007), *Empirical Methods in Short-Term Climate Prediction*, on OCN damping by lead (H26). Wilks, *Statistical Methods in the Atmospheric Sciences*, on damped persistence (H26).
- Fuller (1987), *Measurement Error Models*, on the multivariate correction for attenuation (H23).
- Karl et al. (1993), BAMS, and Menne, Williams & Palecki (2010), JGR, on Tmax/Tmin asymmetry and siting (H23).
- Schubert et al. (2004), Science, and Cook, Miller & Seager (2009), PNAS, on the Dust Bowl drought and land-surface feedback (H27).
- Studies of U.S. first-order station relocations to airports in the mid-20th century (H27, rival a).
- Meehl et al. (2012), already in the INDEX leads, on the warming hole and heat extremes (H27).

## Thin Spots

- Fewer than ten notes bear on each kept hypothesis, so novelty is unverified for H23, H26 and H27. Searches for the librarian:
  - "damped persistence lead dependence station temperature anomalies"; "optimal climate normals skill by lead" (H26).
  - "errors-in-variables correction persistence climate anomalies"; "interannual variance Tmax Tmin U.S. stations" (H23).
  - "Dust Bowl annual maximum temperature station inhomogeneity"; "first-order station relocation airport temperature bias" (H27).
- **Not in the supplied data:**
  - E1's λ̂ per cut-off and its precipitation-arm result;
  - E3's κ̂ per fold;
  - whether H11's national arm ran;
  - E2's per-lead results;
  - the E1 config's clip.

  I did not read `trend.py`, the configs, the trial write-ups or `paired_bootstrap.py`, because they were not supplied. So the name and window of the k_i estimator are unverified.

## Files read

- `/Users/atabaresa/repos-new/egm/egm-research/agents/hypothesizer.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md` (lines 1–60, 351–375, 452–471, 572–1256)
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses_review.md` (lines 589–1231)
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/experiments.md` (rows 8–30)
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/candidate_error_analysis.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/data.md` (grep for column names only)
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- In `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`: vandendool2011readme, efron1975data, arguez2009improving, hausfather2013quantifying, menne2009homogenization, wilks2013performance, wilks2013projecting, livezey2007estimation, katzndblock, mckinnon2024pace, claeskens2016forecast, vose2017temperature, gardner1985forecasting, smith2009simple, easterling2017precipitation, mascioli2017timing, montero-manso2021principles, huang1996longlead, proietti2025estimation, ho2013statistical, haug2020spatial, mueller2012hot, petri2015impacts, natekin2013gradient, krueger2011simple, hewamalage2021global, qian2015forecast

## Final (Round 3)

Round 3 tested the refiners' score hypotheses against their nested parents. It also tested
H27's sign prediction (written as confirmatory) on the replication origins, which had not been scored
before that prediction was written. H27's sign prediction was written as
confirmatory, but it is relabelled exploratory after the critique (see the corrections below), so
everything in this round is exploratory. The adoption rule is unchanged. Holm with m = 4 applies in the E2 branch: H21, H23/H32
on temperature, H23/H36 on CDD, and H26.

| ID | Status | Primary endpoint (official folds, against the nested parent) | 7 cut-offs | Early | Replication | Mechanism readout | Note |
| :- | :----- | :----------------------------------------------------------- | :--------- | :---- | :---------- | :---------------- | :--- |
| E2 | **adopted** (unchanged) | — | — | — | — | λ_T 0.83 and λ_CDD 0.74 at the 2018 cut-off | The submission candidate (`configs/at_submit_e2.yaml`) |
| H23 = H36 (CDD contrast) | kept, not adopted | Rerun after the fix: CDD skill +0.17 [−0.01, +0.37] pp against E2's CDD arm (before the fix: +0.22 [+0.01, +0.45]) | +0.06 | +0.07 | −0.05 [−0.13, +0.02] | Centred γ̂ > 0 at all six cut-offs (0.27/0.37/0.21; 0.21/0.15/0.10) | The official interval includes 0 and the replication sign reverses; one family with H32 |
| H32 (reliability-corrected gap) | kept (not run) | — | — | — | — | — | A mechanism-only test; no score claim |
| H26 (lead slope on E2) | kept, inconclusive | raw +0.03 [−0.00, +0.06] against E2 | −0.00 | −0.01 | +0.01 | b̂ < 0 at all cut-offs (tiny) | Not adopted by its own rule |
| H37 (lead groups on E1) | dropped | hottest-day skill +0.04 [−0.05, +0.13] pp against `e1_hottest` (E1 refit on the hottest day only, clip [0, 1], as H37 specified; round-2 E1 used clip (−1, 1) and two metrics) | — | — | — | λ_short − λ_long = −0.02 at 1980 | Refuted by its coefficient rule |
| H27 (regime artefact) | supported (exploratory) | Pooled replication hottest-day skill, E1 minus candidate: −0.15 [−1.15, +0.93] (predicted < 0) | — | — | 1941: −3.04 [−5.74, +0.02] (predicted < 0); 1948: +0.53 (predicted ≤ 0, hedged) | λ_hot > 0 at all three replication cut-offs | The hottest day stays on the 30-year mean |
| H35 (top-10-day predictor) | kept (not run) | — | — | — | — | — | Parent E1 failed; H27 supports the regime-artefact reading |
| H31, H33, H34 | dropped | — | — | — | — | — | Dropped by refiner B |
| E1, E3, E4, H21, H22, H24, H25 | dropped | — | — | — | — | — | Dropped by refiner A |

**Corrections after the round-3 critique.**

- **The H36 code was fixed** (egm-methodologist-r3-H36-a and -H36-b):
  - the CDD contrast is now centred across cities;
  - a missing regressor now counts as 0, so the arm nests E2 exactly;
  - the H36 row shows the rerun; the pre-fix numbers are kept only for comparison;
  - E2's forecasts are unchanged (max abs diff 0.0).
- **The leakage audit found E2 clean** (egm-methodologist-r3-X1):
  - E2 and its base read only the organizer's per-row values through `annual_to_long`: `Avg Temp`, `ToT Prcp`, `Max Tmax`, `cdd` and the `Miss *` counts;
  - the master table's added columns are row-local or backward-only (`valid_*`, `years_since_switch`, `region` from lat/lon, daily flag counts);
  - `Station Segment` is the only column with unverified chronology. Only the refuted U3 (`slope_within: segment`) and the dropped H1 neighbour arms (`src/proto_star/neighbours.py`) used it.
- **E2 submission rule** (egm-methodologist-r3-E2-a): E2 is submitted whatever λ̂_2018 is. λ̂_2018 is 0.83 for temperature (backtest range 0.60–0.84) and 0.74 for CDD (0.66–0.79), so it is not an extrapolation.
- **E2 on the 2011 fold alone** (egm-methodologist-r3-E2-b), the fold closest to the 2018 transfer, E2 minus candidate:
  - all years +0.07 [−0.08, +0.20] raw;
  - years 1–3 +0.03 [−0.32, +0.31];
  - years 4–7 +0.10 [−0.02, +0.22].

  Against the three-fold +0.22 [+0.07, +0.35], this is the better guide to the real gain.
- **H27 is relabelled exploratory** (egm-methodologist-r3-H27-a): the plan was never committed, so no immutable record dates the prediction.

**Outcome after three rounds.** Only E2 met the adoption rule, and it is the submission
candidate. Round 3 found the mechanisms behind E2 behaving as predicted: Tmin persists more
than Tmax, and λ decays slightly with lead. None of these refinements adds a detectable score
gain. H27 accounts for why every hottest-day persistence method fails in the recent era.

### Final table (all round-3 hypotheses)

The open counts come from the ledger state after r3-decision: findings whose status is open or
awaiting decision, matched by each finding's hypothesis scope. Every round-3 finding has a triage
call, so none is open.

Five triage calls are waiting for the human's approval. They are counted in the last column,
because they apply to each hypothesis listed:

- egm-novelty-r3-X1 (Major) applies to every round-3 hypothesis.
- egm-methodologist-r3-X1 (Major) applies to every round-3 hypothesis except H35, following the critic's tag `[all: E2, H23, H26, H27, H32, H36, H37]`.
- egm-methodologist-r3-X4 (Major) applies to E2, H23/H36, H26, H37 and H27, the hypotheses its text names.
- egm-methodologist-r3-E2-a and egm-novelty-r3-E2-a (Nits) apply to E2.

Round 1 still has 7 open Majors, all on round-1 hypotheses (H1, H2, H4, H16 and related arms).

| ID | Statement (short) | Status | Open Blocker / Major | Awaiting human approval (Major / Nit) | Last round changed |
| :- | :---------------- | :----- | :------------------- | :------------------------------------ | :----------------- |
| E2 | Damp the city part of the recent temperature and CDD anomaly, λ fitted in-fold | kept: **adopted**, the submission candidate | 0 / 0 | 3 / 2 | 3 |
| H23 | Tmin carries city persistence beyond reliability; CDD contrast on E2 | kept, not adopted (merged with H36) | 0 / 0 | 3 / 0 | 3 |
| H36 | Tmin − Tmax contrast × CDD per degree added to E2's CDD correction | merged into H23 | 0 / 0 | 3 / 0 | 3 |
| H26 | E2's coefficient varies linearly with lead | kept, inconclusive | 0 / 0 | 3 / 0 | 3 |
| H27 | E1's early hottest-day gain is a 1930s/1950s regime artefact | kept, supported (exploratory) | 0 / 0 | 3 / 0 | 3 |
| H32 | Tmin–Tmax persistence gap beyond reliability | kept (not run) | 0 / 0 | 2 / 0 | 3 |
| H35 | Top-10-day anomaly predicts the hottest day better than the annual maximum | kept (not run) | 0 / 0 | 1 / 0 | 3 |
| H37 | Lead-group coefficients beat E1's single λ (hottest day) | dropped (refuted) | 0 / 0 | 3 / 0 | 3 |
