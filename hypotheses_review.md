# Hypotheses review

Run: `hypothesize-20261109-a`. Hypotheses: [hypotheses.md](hypotheses.md).

## Round 1

### Reviewer status

| Critic | Mode | Status | Blocker | Major | Nit |
| :----- | :--- | :----- | :------ | :---- | :-- |
| egm-novelty | BRAINSTORM | completed (on retry; the first run failed on a network error before reviewing) | 0 | 20 (as the critic reports; F1–F19 below) | 3 |
| egm-methodologist | BRAINSTORM | completed (on retry; the first run failed on a network error before reviewing) | 2 | 47 | 6 |
| egm-citation-auditor | REVIEW | not run (the human asked to skip auditor verification) | — | — | — |

This round is **incomplete**: egm-citation-auditor did not run.

### Finding IDs (egm-novelty)

Each finding in the critic's report has an ID: `F<n>` becomes `egm-novelty-r1-<n>` and `N<n>`
becomes `egm-novelty-r1-n<n>`. The table lists each ID with the hypotheses it is tagged to.

| ID | Severity | Hypotheses |
| :- | :------- | :--------- |
| egm-novelty-r1-1 | Major | U1, H4, H16 |
| egm-novelty-r1-2 | Major | all |
| egm-novelty-r1-3 | Major | U1 |
| egm-novelty-r1-4 | Major | U2 |
| egm-novelty-r1-5 | Major | U3 |
| egm-novelty-r1-6 | Major | H1, H11, H12 |
| egm-novelty-r1-7 | Major | H1, H11, H12 |
| egm-novelty-r1-8 | Major | H1, H11, H12 |
| egm-novelty-r1-9 | Major | H15 |
| egm-novelty-r1-10 | Major | U3, H1, H15 (H11, H12 rivals) |
| egm-novelty-r1-11 | Major | H2, H14 |
| egm-novelty-r1-12 | Major | H2, H14 |
| egm-novelty-r1-13 | Major | H2 |
| egm-novelty-r1-14 | Major | H3, H13 |
| egm-novelty-r1-15 | Major | H3, H13 |
| egm-novelty-r1-16 | Major | H4, H16 (U1) |
| egm-novelty-r1-17 | Major | H5 |
| egm-novelty-r1-18 | Major | H2, H5, H17 |
| egm-novelty-r1-19 | Major | H17 |
| egm-novelty-r1-n1 | Nit | U1, U2, U3 |
| egm-novelty-r1-n2 | Nit | H4 |
| egm-novelty-r1-n3 | Nit | Generator A, dropped candidates |

### egm-novelty report (verbatim)

## Novelty Critic report (BRAINSTORM): U1–U3, H1–H5, H11–H17

**Verdict.** No Blockers: no saved note already reports any hypothesis's contribution. The folder can only support "not found in this folder", not "new". 20 Major findings and 3 Nits follow. The most important points are:
- **lai2020use is the closest saved work in setting, and no hypothesis names it.** It is abstract-only.
- **Four groups of hypotheses duplicate each other across the two generators:** H3 and H13; H2 and H14; H1, H11 and H12; and the CDD summer-sensitivity arms of H2, H5 and H17.
- **H2's κ = 1 comes from a source that uses observations up to 2023.** This is outside the novelty lens but material.

All notes are unaudited, and every quote below is taken from the notes as written.

### Per-hypothesis summary (closest saved work / remaining gap / coverage)
- **U1.** Closest: montero-manso2021principles q3, hewamalage2021global q2, gardner1985forecasting q1–q2, lai2020use q2. Gap: the setting only (station annual anomalies, L1 loss, 30-year reference). Coverage: partial.
- **U2.** Closest: livezey2007estimation q8, wilks2013performance q4, smith2009simple q1, gardner1985forecasting q1. Gap: the setting only; the method is not new. Coverage: adequate for the method.
- **U3.** Closest: menne2009homogenization q1, q3. Gap: documented segments used as fixed effects in a pooled slope. Coverage: thin.
- **H1, H11, H12.** Closest: vandendool2011readme q1–q3, wilks2013performance q2, wilks2013projecting q3, menne2009homogenization, efron1975data. Gap: partial pooling of recent level anomalies at station scale, under MAE. Coverage: thin on estimating normals from neighbours.
- **H15.** Closest: wilks2013performance q2, menne2009homogenization q1, q3. Gap: documented breaks, applied to precipitation and annual maxima. Coverage: partial (the closest note is abstract-only).
- **H2, H14.** Closest: mckinnon2024pace q1, vose2017temperature q3, q5, arguez2009improving q4, katzndblock q4. Gap: a first forecasting rule for hottest day. Coverage: thin.
- **H3, H13.** Closest: natekin2013gradient q1, meinshausen2006quantile q3. Gap: a closed-form median shift applied to climatological levels. Coverage: thin.
- **H4.** Closest: ho2013statistical q1–q2, krueger2011simple q3, arguez2009improving q2. Gap: decomposing the residual into a cross-city common part and assuming it does not persist. Coverage: partial.
- **H16.** Closest: lai2020use q2, ho2013statistical q1, krueger2011simple q3. Gap: a pooled, lead-specific φ_h added on top of a pooled trend. Coverage: partial.
- **H5.** Closest: eia2025shortterm q2, petri2015impacts q2, morris1999impact q2. Gap: deriving the CDD level from the temperature forecast. Coverage: thin.
- **H17.** Closest: arguez2009improving q3–q4, vandendool2011readme q1, livezey2007estimation q7. Gap: recombining seasonal levels into annual targets, scored by MAE. Coverage: partial.

---

### Cross-cutting

**F1. Major: unnamed closest work (U1, H4, H16; bears on all metrics)**
- **Prior work:** lai2020use q1: "near-term (2–20 years) regional temperature and precipitation projections utilizing local historical observations". Its q2: "can be interpreted as an integration of the most recent observations and the long-term historical trend."
- **Why it matters:** `research_background.md` says the stations are "from the Lai & Dzombak records". This is the only saved forecasting study at local scale with annual targets and multi-year leads. No hypothesis cites it.
- **What is unknown:** the note's Not Covered section says: "Which indices ARIMA lost on, the error metric used, the station list, or results for annual maxima or degree days (full text not read)." So it may already cover these indices and this station set.
- **Recommendation:**
  - Fetch the full text before claiming any gap for U1 (a pooled model on local history), H16 (trend plus persistence of recent values) or H4.
  - Treat R03 (Lai & Dzombak 2021) as prior work for novelty, even though the index excludes it as a source of forecast inputs.

**F2. Major: search coverage does not support novelty (all)**
- **Sources were shallow.** The log has 26 OpenAlex keyword searches, each inspecting only the first 25 results (hit counts ran up to 1,313,422). Most queries were title or author lookups for the must-include list.
- **Every mechanism-level discovery query kept nothing:** 11h (CDD sensitivity), 11i (non-stationary GEV), 11j (precipitation trends), 11k (damped persistence), 18b (empirical-Bayes station trends) and 18c (annual-max Tmax trends).
- **Major databases were not used.** There was no Semantic Scholar, Google Scholar, Crossref keyword search or ORKG. arXiv was queried by ID only.
- **AMS was blocked (HTTP 403).** So the core normals papers are abstract-only (huang1996longlead, both wilks2013 papers, lai2020use) or metadata-only (arguez2011definition).
- **No citation chasing was done.** There were no forward-citation searches from livezey2007estimation, wilks2013projecting, huang1996longlead or lai2020use.
- **Scope was narrow:** English only, one run day, and all notes unaudited.
- **Recommendation:** keep the "unverified" wording both generators already use. Run the per-cluster searches named below before any write-up claims a contribution.

---

### User hypotheses

**F3. Major: unnamed closest work (U1)**
- U1 names no prior work.
- **What the folder already covers:**
  - Pooled models: montero-manso2021principles q3, "global linear models show an unreasonable effectiveness". Also hewamalage2021global q2, where LGBMs are "competitive ... series having short lengths, datasets with heterogeneous series".
  - Damping: gardner1985forecasting q1, "damping or ignoring altogether trends which have a low probability of persistence", with gains "particularly at long leadtimes" (q2).
  - Lead-dependent windows: livezey2007estimation q6–q7, where N is set "for τ = 1 yr" and "Fixed N ... is inadvisable unless Noptimal varies little".
  - L1 loss targets the median: natekin2013gradient q1.
- **Remaining gap:** the setting only. INDEX Gaps says: "No climate application was found."
- **Recommendation:**
  - Cite these as the parts the model combines, and add lai2020use (F1).
  - Search: "machine learning multi-year station temperature forecast"; "gradient boosting annual climate anomaly prediction"; "direct multi-step forecasting strategy"; "quantile regression climate normals".

**F4. Major: unnamed closest work (U2)**
- **Prior work:** U2 blends a trend-based forecast with a 10-year mean (an OCN-type forecast). Two saved sources propose exactly this kind of hybrid:
  - livezey2007estimation q8 recommends "a simple hybrid system that combines the advantages of both the OCN and the hinge fit".
  - wilks2013performance q4 reports that a hybrid "using one of these piecewise continuous functions when the regressions are sufficiently strong and the CPC 15 otherwise, exhibits a favorable trade-off between squared error and bias".
- **Supporting theory:** smith2009simple q1 and claeskens2016forecast q3 explain why equal weights work well; gardner1985forecasting q1 covers damping.
- **Remaining gap:** fixed equal weights rather than a regression-strength switch, at station scale with annual MAE. The setting is new; the method is not.
- **Recommendation:** cite livezey2007estimation q8 and wilks2013performance q4 as closest. Present U2 as an application, not a method.

**F5. Major: thin folder (U3)**
- **Closest saved:** menne2009homogenization q3, "relocation, replacement, or recalibration ... can lead to an abrupt shift". Its q1 forms pairwise difference series to detect and adjust breaks.
- **Gap:** U3 instead uses the documented segments as fixed effects inside a pooled slope.
- **Coverage:** no saved source covers estimating trends with known breakpoints, so novelty cannot be judged.
- **Searches to run:** "trend estimation known breakpoints station relocation"; "segment fixed effects temperature trend"; "splitting station records at moves (scalpel)"; "first-difference method station trends".

---

### H1, H11, H12 (neighbour or regional pooling of levels)

**F6. Major: overlap (H1, H11, H12)**
These three are one family of estimators: city level = a long-run city offset plus a regional recent anomaly, with shrinkage.
- **H12 (additive form):** m30_i + λ·R.
- **H11:** m30_i + R + B·(A_i − R). At B = 0 this becomes m30_i + R.
- **H1:** if its offset were taken over the 30-year window, the offset would be about m30_i. H1 would then be about m30_i + B̂·N_recent, which is H12 with λ = B̂ and k nearest neighbours in place of a region.
- **What H1 alone adds:** the current-segment offset and the distant-city placebo arm.
- **Inconsistencies to resolve:**
  - B means opposite things: in H1, B = 1 means fully anchored; in H11, B = 1 means no shrinkage.
  - H1's fixed settings do not give the length of the neighbours' "current" anomaly window. H12 uses 15 years.
  - Generator A dropped "CPC skill mask with damped anomalies for precipitation and hottest day" as overlapping U1 and U2, while Generator B proposed it as H12.
- **Recommendation:**
  - Run one factorial: metric × offset window (30 years or current segment) × neighbourhood (k nearest or region) × weight (Efron–Morris B̂ or in-fold λ).
  - Declare one primary arm and keep H1's placebo arm.
  - Align the meaning of B.

**F7. Major: unnamed closest work and an incomplete difference statement (H1, H11, H12)**
- **Divisional OCN is the nearest forecasting analogue.** vandendool2011readme q1: "last 10 (T), 15(P) years averaged minus a 30 year climatology". Its q3: "the amplitude of the operational OCN is reduced by a factor that relates to the a-priori skill so as to minimize RMS error."
  - This is the nearest analogue of H1's "neighbours' current anomaly + B̂" and of H12's damped regional anomaly.
  - H1 names only menne2009homogenization, a homogenization method, as its closest prior work.
  - H12's closest-work line describes OCN as having "fixed windows" and leaves out the damping, even though its own Inspirations line says "damped by skill".
- **wilks2013projecting q3 is the nearest negative result for precipitation.** "Averages of the most recent 15 and 30 yr have performed better ... for ... temperature and precipitation, respectively". H12 lists it only as a rival.
- **wilks2013performance q2 reports that aggregation lost.** "homogenized station data shows clear improvement over nonhomogenized station data and spatially aggregated data". H11 and H12 do not cite it; H1 cites it only for homogenization. The note is abstract-only, so the scoring target is unknown.
- **Recommendation:**
  - Restate the gap as: station annual targets, λ or B fitted under absolute error inside each fold, hottest day as a target, and partial rather than full aggregation.
  - Fetch the full text of wilks2013performance.

**F8. Major: novelty claim exceeds the search (H1, H11, H12)**
- Only one pooling query was run (18b), and it kept nothing. INDEX Gaps says: "Nothing was found that applies empirical Bayes, James-Stein or hierarchical pooling to station trends for forecasting."
- H1's own Thin Spots section concedes there is "no source on small-area estimation or on normals from neighbours".
- **Searches to run:** "estimating climate normals from neighbouring stations"; "anomaly or ratio method for incomplete-record normals"; "spatial interpolation of station normals"; "small-area estimation temperature"; "empirical Bayes climatology stations".

### H15 and station steps

**F9. Major: unnamed closest work (H15)**
- **Prior work:** wilks2013performance q2 shows that homogenizing improves normals' errors on independent data. That is closer to H15's contribution (adjust steps, get a better level) than menne2009homogenization, which builds homogenized series for trend analysis.
- Generator B discloses it did not read this note.
- **Remaining gap:** documented break dates, precipitation and annual maxima, and MAE. The temperature and CDD arm replicates what saved work anticipates.
- **Recommendation:** cite wilks2013performance as closest, and label the temperature arm as a replication.

**F10. Major: overlap (U3, H1, H15; rivals in H11 and H12)**
- The same station-step mechanism appears in several places:
  - U3, through segment demeaning in the slope.
  - H1, through the current-segment offset; this is also its rival (a).
  - H15, through explicit step adjustment.
  - As rival (b) in H11 and rival (c) in H12.
  - The team's rejected "level from the current station segment only".
- **Recommendation:** run one station-step study that shares the placebo designs (H1's distant-city neighbours, H15's steps at random years) and stratifies switching and non-switching cities.

### H2 and H14 (hottest day from summer-mean Tmax)

**F11. Major: overlap (H2, H14)**
- H14 = m30_hottest + (S_recent − S30), optionally plus a floored slope. This follows from its own identity check, S30 + E30 = m30.
- H2 = m30_hottest + b_JJA·(year − c30).
- Both transfer the shift in summer-mean Tmax to the annual maximum. They differ only in how they estimate the shift (a pooled slope or the city's recent level) and in the months used (June–August or July–August).
- Each names a different closest work: mckinnon2024pace for H2, katzndblock for H14.
- **Recommendation:** merge into one hypothesis with arms for slope, recent level, and level plus slope. Share the κ̂ diagnostic and cite both sources.

**F12. Major: thin folder (H2, H14)**
- **Saved sources describe trends, not forecasts:**
  - mckinnon2024pace q1 is about scale: "globally, in each hemisphere, and in the tropics from 1959 to 2023". Its note says it does not cover "U.S. station-level annual max Tmax trends".
  - vose2017temperature q5: "Since the mid-1960s, there has been only a very slight increase in the warmest daily temperature of the year".
  - arguez2009improving q4 is the only station-level summer Tmax source: "For July maximum temperatures ... a tendency for smaller N in the West". Neither generator cites it.
- INDEX says "No forecasting study was found", and searches 11i and 18c kept nothing.
- **Searches to run:** "annual maximum temperature (TXx) scaling with summer mean temperature"; "TXx relative to regional mean warming"; "prediction of annual maximum temperature from seasonal mean"; "non-stationary GEV with a seasonal-mean covariate"; "U.S. station TXx trends 1950–2018".

**F13. Major: source use, outside the novelty lens (H2)**
- The mckinnon2024pace note says: "Its analysis uses observations through 2023 and CMIP6, so treat it as background on trends, not as a source of forecast inputs."
- H2 nonetheless fixes κ = 1 from this source and calls its primary arm confirmatory. H14 treats the same source as "background only".
- The constraint is in `research_background.md`: "Never tune or select using ... knowledge of 2019–2025."
- **Recommendation:** justify κ = 1 from pre-2019 evidence, or from κ̂ estimated inside each fold. Route this to a constraints review.

### H3 and H13 (shift from mean toward median)

**F14. Major: overlap, an exact duplicate (H3, H13)**
- H3's precipitation arm is m30 − s²/(3·m30) = m30·(1 − CV²/3).
- That is H13's mean × (1 − q·CV²) with q = 1/3.
- The CDD arms differ: H3 uses the pooled skewness γ̂ in all cities, H13 only low-CDD cities. Only H3 has a hottest-day arm.
- **Recommendation:** merge. Use q = 1/3 as the confirmatory arm and q fitted inside each fold as the exploratory arm, with one shared placebo and CV-tercile test.

**F15. Major: thin folder (H3, H13)**
- **Closest saved sources are general ML statements:** natekin2013gradient q1, "The L1 -loss corresponds to the median of the conditional distribution", and meinshausen2006quantile q3. Neither concerns precipitation distributions or climatological levels.
- H13 discloses it did not read natekin2013gradient.
- **Searches to run:** "gamma distribution annual precipitation totals stations"; "median versus mean precipitation normals"; "climate normals under absolute error"; "skewness correction climatological precipitation forecast".

### H4 and H16 (persistence of residuals)

**F16. Major: overlap (H4, H16; also U1 and one of Generator A's dropped candidates)**
- Together, H4 (zero multi-year persistence of the common residual) and H16 (a φ_h on last year's residual) are the trend-plus-AR model of ho2013statistical q1 and krueger2011simple q3.
- Both propose the same split into a national part and a city part.
- Generator A dropped "Trend plus AR(1)" as a duplicate of U1, citing U1 features `last` and `d5`. U1's statement in `hypotheses.md` lists neither feature, so I cannot verify this. Generator B proposed it anyway as H16.
- **Recommendation:**
  - Run one study of residual persistence: the autocorrelation by lag of the common and city-specific residuals inside each fold, with H4 and H16 as arms.
  - Check U1's feature list.
  - Search: "lag-1 autocorrelation annual station temperature U.S."; "decadal persistence of U.S. regional temperature anomalies".

### H5 and H17 (CDD)

**F17. Major: thin folder (H5)**
- **Prior work:** eia2025shortterm q2 fits a "one-variable 30-year trend line". petri2015impacts q2 reports that CDD "increased due to warming trends". The INDEX says: "No observational study of CDD trends or of CDD sensitivity to warming at city level was retrieved", and "No source addresses the nonlinearity of CDD in mean temperature."
- H5's stated difference from eia2025shortterm is concrete, but novelty cannot be judged.
- **Searches to run:** "degree days estimated from mean temperature and its standard deviation"; "observed cooling degree day sensitivity to mean temperature"; "nonlinearity of the degree-day–temperature relationship".

**F18. Major: overlap (H2's secondary arm, H5's third arm, H17's CDD arm)**
- H2's secondary arm (city CDD-per-JJA-degree × the pooled JJA slope) and H17's CDD arm (CDD per warm-season degree × the pooled warm-season slope) are the same except for how the season is defined.
- H5's third arm adds the same summer sensitivity.
- **Recommendation:** run one CDD factorial: level (candidate, or H5's m30 + sens·ΔT) × sensitivity (annual or summer) × slope (annual or summer).

**F19. Major: unnamed closest work (H17)**
- **Prior work:** arguez2009improving already computes station-specific seasonal OCN windows. Its q3: "The correlation between N and β is -0.78, quantifying the intuitive notion that strong linear trends require shorter averaging periods" (January Tmin). Its q4 gives "-0.35" for July Tmax.
- **H17 overstates the gap:** its difference statement ("climate divisions ... here ... annual station targets") does not account for this station-level work.
- **The saved evidence also points against H17's predicted direction:** combined with morris1999impact q2 (winter-concentrated warming), it suggests shorter cold-season windows, not longer ones.
- **Cross-generator conflict:** Generator A dropped "separate level windows per season".
- **Remaining gap:** recombining seasonal levels into annual targets, with MAE skill (arguez2009improving reports no skill).
- **Recommendation:** cite arguez2009improving as closest, and explain why the predicted window direction differs.

---

### Nits
- **N1 (U1–U3).** All three still have Status "new", while Generator A reports results (U1 lost in years 4–7; U2 traded years 4–7 for years 1–3; U3 within noise). I did not verify these results. Update the statuses, because the overlaps in F16 and H11's rival (c) depend on them.
- **N2 (H4).** The differences H4 claims from ho2013statistical ("station scale", "no forcing series") are shared by arguez2009improving q2, which sets N "based on ... the residual lag-1 (g) autocorrelation and the linear trend (β)". The real difference is the cross-city common residual.
- **N3 (Generator A, dropped candidates).** The "lead-varying window" item cites arguez2009improving q2, but q2 is about station-specific N. Lead dependence is in livezey2007estimation q6.

### Leads to Fetch (unverified; from memory, the INDEX or the generators; not used as evidence)
- Lai & Dzombak (2020), full text; Lai & Dzombak (2021, JAMC; R03).
- Wilks & Livezey (2013), full text; Huang et al. (1996), full text; Livezey & Smith (1999).
- WMO-No. 1203 (2017), climate normals guidelines; Argüez et al. (2012), NOAA 1981–2010 normals; Daly et al., PRISM normals; Fay & Herriot (1979); Hosking & Wallis (1997).
- Rohde et al. (2013), Berkeley Earth "scalpel" method; Peterson et al. (1998), homogeneity review.
- Thom (1958), gamma-distributed precipitation; Thom (1950s), degree days from mean temperature.
- Seneviratne et al. (2016, Nature), regional TXx scaling; Cheng et al. (2014); Meehl et al. (2012); seasonal Tmax figures already in the vose2017temperature source text.
- Kunkel et al. (2020); Deser et al. (2012); Ben Taieb et al. (2012), multi-step forecasting strategies.

### Files read
- `/Users/atabaresa/repos-new/egm/egm-research/agents/novelty_critic.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- All 45 notes in `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`

I did not open `docs/trials` or anything in `sources/`, since they were not in the supplied context. No files were written.

### Finding IDs (egm-methodologist)

Each finding label in the critic's report maps to an ID of the form `egm-methodologist-r1-<label>`.

| ID | Severity | Hypotheses |
| :- | :------- | :--------- |
| egm-methodologist-r1-X1 | Blocker | all |
| egm-methodologist-r1-X2 … X8 | Major (7) | all (X3: H1, H2, H3, H5, H11, H13, H16; X5: H2, H5, H14, H17; X7: U1, H11, H12, H13, H16, H17) |
| egm-methodologist-r1-X9 | Nit | traceability |
| egm-methodologist-r1-U1-a … U1-d | Major (4) | U1 |
| egm-methodologist-r1-U2-a, U2-b | Major (2) | U2 |
| egm-methodologist-r1-U2-c | Nit | U2 |
| egm-methodologist-r1-U3-a | Blocker | U3 |
| egm-methodologist-r1-U3-b | Nit | U3 |
| egm-methodologist-r1-H1-a … H1-d | Major (4) | H1 |
| egm-methodologist-r1-H2-a … H2-d | Major (4) | H2 |
| egm-methodologist-r1-H3-a … H3-c | Major (3) | H3 |
| egm-methodologist-r1-H4-a … H4-c | Major (3) | H4 |
| egm-methodologist-r1-H5-a, H5-b | Major (2) | H5 |
| egm-methodologist-r1-H5-c | Nit | H5 |
| egm-methodologist-r1-H11-a … H11-c | Major (3) | H11 |
| egm-methodologist-r1-H12-a, H12-b | Major (2) | H12 |
| egm-methodologist-r1-H13-a, H13-b | Major (2) | H13 |
| egm-methodologist-r1-H13-c | Nit | H13 |
| egm-methodologist-r1-H14-a … H14-c | Major (3) | H14 |
| egm-methodologist-r1-H15-a … H15-c | Major (3) | H15 |
| egm-methodologist-r1-H16-a, H16-b | Major (2) | H16 |
| egm-methodologist-r1-H16-c | Nit | H16 |
| egm-methodologist-r1-H17-a … H17-c | Major (3) | H17 |

### egm-methodologist report (verbatim)

Methodologist review, BRAINSTORM mode: hypotheses.md (U1–U3, H1–H5, H11–H17)

**Study type and claim type.** This is a comparison of statistical and ML forecasting methods on rolling-origin backtests of observational station data, using one fixed harness. The forecasters use no pretrained models. Most claims are exploratory. These parts are labelled confirmatory:
- H2, H3 and H5: their primary arms.
- H11 and H13: the direction or sign of the effect.
- H16: the sign of φ1.

U1–U3 do not state a claim type.

**Review completeness.** The review is complete. I read:
- the persona;
- the AI/ML standard (`/Users/atabaresa/repos-new/egm/egm-research/resources/document_standards/ml-empirical-research-standard.md`) and the shadish2002experimental note;
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md` and `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`;
- `literature/INDEX.md` and the 30 notes the hypotheses cite.

I did not read 15 notes that no hypothesis relies on: arguez2011definition, proietti2025estimation, lai2020use, salinas2020deepar, oreshkin2019nbeats, smyl2020hybrid, makridakis2018m4, makridakis2020m4, qian2015forecast, wang2023forecast, friedman2001greedy, koenker1978regression, chen2016xgboost, bergmeir2012use and bracco2024machine.

To check leakage and feasibility, I also read files beyond your list:
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/data.md` (the background cites it by absolute path);
- `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/backtest.py`;
- `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/trend.py`, lines 1–171;
- `/Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/climate.py`, the `assert_weather_cutoff` and `annual_to_long` sections;
- a grep of `src/proto_star/data/master.py` for Lat/Lon.

I did not read `docs/trials/*`. Results for U1–U3 below come only from the two generator reports.

All literature notes are unaudited.

---

## Cross-cutting findings

**X1. Blocker. Testability and Design Fit. Applies to all IDs.**

*Risk:* the shared decision rules cannot tell the predicted effects apart from noise.
- **The fold rules are coin flips.** Under the null, with symmetric noise, "positive on at least 2 of 3 folds" passes with probability 4/8 = 0.5. "At least 4 of 7 origins" passes with probability 64/128 = 0.5.
- **The 7-origin check is not independent.** It contains the 3 official folds. Its forecast windows also overlap: 1986–92 shares two years with 1991–97, and so on.
- **A fold-level test cannot succeed.** A Wilcoxon signed-rank test on 3 folds cannot go below p = 0.25 two-sided (demsar2006statistical).
- **Effects are inside the noise.** Nearly every predicted effect is 0.1–1.5 points of skill on a single metric, which is 0.03–0.4 raw points. That sits at or below the stated noise floors: 0.5 raw (generator A) and 0.3 raw (generator B), neither derived. The precipitation window results show per-metric noise of about 0.5–1 point. For example, the 40-year mean scored +0.71 on the official folds and +0.07 over 7 origins.

So confirmations and refutations, as written, carry little information.

*Requirements:*
- Before any run, fix one primary endpoint per hypothesis: one metric and one lead window, or raw score.
- Fix one named paired test against one named comparator. The skill difference per fold is a sum of per-year contributions, (|e_comp| − |e_new|) / (n · MAE_ref). Test the 21 non-overlapping forecast years of the 3 official folds with a year-block bootstrap, or a Diebold–Mariano-type test with HAC variance. Do not test at row level: errors are strongly correlated across the 210 cities within a year.
- Derive one minimum detectable effect from the logged runs, for example from the spread of paired differences between near-identical variants.
- Relabel or drop any hypothesis whose predicted effect is below that minimum.

Source: standard §4 (dror2018hitchhikers, demsar2006statistical, agarwal2021deep).

**X2. Major. Statistical conclusion validity. Applies to all IDs.**

*Risk:*
- This round has 15 hypotheses and about 40 arms, across 4 metrics and 3 windows.
- They will run on folds already reused about 45 times.
- The comparator was itself picked from about 40 variants on these folds.
- The slope floor was added after the team saw the 1980 failure (trend.py docstring).

*Requirements:*
- Declare this round's primary arms as one family. Apply Holm's correction, or call everything exploratory.
- Declare a confirmation set now that no logged run has scored. One option is earlier non-overlapping origins such as 1955, 1962 and 1969, if city coverage allows. These suit precipitation and hottest-day hypotheses whose mechanisms do not depend on the warming era. This is a diagnostic, not a change to the ADR 0004 scoring.

Source: §1 (herrmann2024position), §4.

**X3. Major. Exploratory presented as confirmatory. Applies to H1, H2, H3, H5, H11, H13 and H16.**

*Risk:* several hypotheses came from patterns on the same folds that will test them.
- Generator A's derivation items 2–4 motivate H1, H2 and H3, using official and 7-origin window results.
- H12 takes its noise scale from the 40-year precipitation result.

*Requirement:* call every claim exploratory on the official folds. Allow confirmatory status only on the X2 confirmation set.

Source: §1 (herrmann2024position).

**X4. Major. Flexible analysis and undefined measures. Applies to U1, U2, H1–H5 and H11–H17.**

*Risk:*
- Most hypotheses list 3–6 predictions and are "refuted if any of" a subset fails. None states the verdict when predictions split.
- Many thresholds are undefined: "≈ 0", "about 1", "near 0", "clearly", "matches", "most".

*Requirements:*
- Name one primary prediction with a numeric threshold, and mark everything else as secondary.
- Turn every "≈" into an interval rule, for example "the 95% bootstrap interval contains 1 and excludes 0".

**X5. Major. Leakage risk from daily data. Applies to H2, H5's summer-sensitivity arm, H14 and H17.**

*Risk:* the harness passes only master rows up to the cut-off. backtest.py says reading other data inside a forecaster "defeats this protection, and nothing here can detect it". H2 does specify `Date ≤ cut-off` plus `assert_weather_cutoff`. H14 and H17 only say "aggregated in-fold".

*Requirements:*
- Build per-city-year seasonal aggregates once, from that year's days only. Examples: JJA mean Tmax and Tavg, and counts of valid days. These are not multi-year statistics, so they cannot leak.
- Join them to master on (ID, Year), so the harness's `Year ≤ cutoff` filter applies.
- Compute every multi-year quantity inside the forecaster: levels, slopes, sensitivities, excess means.
- Add an invariance test: running with daily data cut at the cut-off must give identical forecasts to running with uncut daily data.

Source: §2 (kapoor2022leakage).

**X6. Major. Contamination of selection through the generators. Applies to all IDs; worst for H2.**

*Risk:* the forecasters use no pretrained weights. But both generators run on LLMs whose knowledge extends past 2018 (generator A on Opus 5.5, generator B on Fable 5.2). Their priors can steer which hypotheses and constants get selected. The honor code bars selection that uses "knowledge of 2019–2025". Generator A's statement that "benchmark exposure cannot explain any result" covers the forecasts, not the selection.

*Requirements:*
- Fix the selection rule before running: the primary endpoints, the minimum detectable effect and the multiplicity handling. Then apply it mechanically.
- Adopt no constant proposed by a generator without in-fold justification. See H2-d.

Source: §2 Benchmark Contamination (sainz2023nlp), applied here to the selection step.

**X7. Major. Unequal tuning. Applies to U1, H11, H12, H13, H16 and H17 compared with the candidate.**

*Risk:* the candidate's constants were chosen on the scored folds:
- the 10/15-year levels;
- the 40-year trend window;
- the floor at 0;
- the CDD sensitivity.

So its fold scores include test-set selection. Challengers whose parameters are fitted in-fold are tuned honestly. This comparison favours the incumbent.

*Requirements:*
- Report each arm's tuning budget, meaning how many configurations were tried on the official folds.
- Optionally, add an "honest incumbent" whose windows are chosen on pseudo-origins up to cut-off − 7.

Source: §3 (melis2017state, dodge2019show).

**X8. Major. Feasibility and overlap. Applies to all IDs.**

*Risk:* 15 hypotheses at 0.75–2 hours each add up to roughly 15–20 hours. The background, written 2026-11-09, puts the deadline at 2026-11-10 23:59 ET, which is today. Several hypotheses overlap:
- H3 and H13 are the same rule.
- H2 and H14 both carry hottest-day signal through summer-mean Tmax.
- H2's secondary CDD arm, H5's arm 3 and H17's CDD arm are one idea: summer sensitivity times summer slope.
- H1, H11, H12 and H15 share neighbour code and the switch-city rival.
- H4 and H11 make opposite assumptions about the recent anomaly.

*Requirement:* merge these into about 6 families with shared arms. Count each family once under X2. Rank families by predicted effect relative to the minimum detectable effect, per hour of work.

**X9. Nit. Traceability.**

- IDs H6–H10 and H18–H20 do not appear. Say whether they were dropped or never generated.
- Generator B says "each hypothesis adds only one or two variants", but most of its plans have 3–4 arms.

---

## Per-hypothesis findings

### U1: pooled direct multi-horizon median model

- **U1-a. Major. Testability.** The status says "new", but both generator reports say U1 has been run. Generator A says it "lost in years 4–7" (hypotheses.md line 50; generator B at line 339 agrees it was tried). By U1's own statement, that refutes it. *Requirement:* mark U1 as tested and link the result. Any revised U1 is a new exploratory hypothesis.
- **U1-b. Major. Design Fit: look-ahead inside training.** The targets correctly respect origin ≤ cut-off − horizon. But the statement does not say the features are rebuilt for each origin. Features at risk: the pooled slope × lead, CDD per degree, city variability, data quality, and the 30-year mean. If they are computed once at the fold cut-off and attached to rows from earlier origins, they were fitted on the training targets' own years. The model then learns weights on hindsight it will not have at test time. All rows are still at or before the cut-off, so this does not break the background's rule, but it does bias the learned damping. *Requirements:* build every feature at origin o from years ≤ o. Add a unit test that origin-o features do not change when master is cut at o.
- **U1-c. Major. Fair comparison.** The design has two model families, two comparators and three windows, with no primary arm. GBM hyperparameters and seeds are not specified. *Requirements:* declare one primary arm. Fix the GBM settings in advance, or choose them on an inner split of origins up to cut-off − 7 − h, and report how many were tried. Run at least 5 seeds if subsampling is used. Source: §3, and §4 (bouthillier2021accounting).
- **U1-d. Major. Alternative explanation.** The 1980 fold learns its damping from the mid-century cooling era. Trees cannot extrapolate beyond the targets they were trained on. A loss could therefore come from a regime shift, not from a lack of learnable damping. *Requirements:* report the learned horizon coefficients for each fold. Ablate the model: same features, the candidate's fixed coefficients, median objective only.

### U2: equal-weight blend of the pooled trend and `current_best`

- **U2-a. Major. Testability.** The years 1–3 prediction cannot fail. For every row, |(a+b)/2 − y| ≤ (|a−y| + |b−y|)/2. So the blend's skill on each metric is at least the mean of the two components' skills, in every fold and window. In years 1–3 that bound is (0.63 + 0.33)/2 = 0.48, which is already above 0.33. The risk lies only in the all-years claim, where the bound is 3.53 against the needed 4.14. It also lies in the years 4–7 claim, where the bound is 5.80 against 6.92. *Requirements:* make all-years raw score against the candidate the primary endpoint. Define "most" numerically.
- **U2-b. Major. Unattributed gain.** The blend halves the slope. It also moves the level from (L10 + L15)/2 to 0.75·L10 + 0.25·L15. "Acts as a damped trend" is therefore not isolated. *Requirement:* add two arms: the candidate's level with slope × 0.5, and the blended level with the full slope.
- **U2-c. Nit.** The generator reports say U2 has already been tested; update its status. The test takes minutes.

### U3: station-segment-aware pooled slope

- **U3-a. Blocker. Testability: unfalsifiable.** "Will change the skill; direction unknown" is confirmed by any nonzero difference. Segment-level demeaning changes the forecast, so a nonzero difference is almost certain. The reported "within noise" result cannot be classified under the statement. *Requirements:* state a primary diagnostic, the change in the pooled slope at each cut-off with a city-bootstrap interval. Then restate the hypothesis in one of two ways:
  - **Directional:** compute the mean step at switches inside the 40-year window, in-fold. If it is positive, the city-demeaned slope is biased upward, so predict that the segment slope is lower.
  - **Equivalence:** use two one-sided tests with a margin, for example |Δraw| < 0.3, with a year-block interval.
- **U3-b. Nit. Alternative explanation.** Segment demeaning drops segments with fewer than `min_city_years` (10) valid years (trend.py `_window_anomalies`). So the sample changes along with the step removal. *Requirement:* refit the city-demeaned slope on the same retained rows. It is already a config switch (`slope_within="segment"`), so it takes minutes.

### H1: neighbour-anchored levels

- **H1-a. Major. Undefined measure.** Three parts are not defined:
  - The window for the "neighbours' current anomaly" is not given for precipitation or hottest day. If it is the 30-year window, the anomaly is about 0 by construction, and arm C collapses toward arm A.
  - v_i has no formula.
  - B̂ = mean(v)/var(m30 − a) measures how much of the disagreement is noise. Putting full weight on a when the disagreement is pure noise is optimal only if a has negligible error. The minimum-variance weight depends on the relative error variances of m30 and a.

  *Requirements:* write out a, v_i and the weight before running. Handle CDD ratios for cool cities, where CDD is near zero.
- **H1-b. Major. Alternative explanation.** The placebo arm D still removes much of the nationwide common anomaly and keeps the long segment offset. So D beating A does not contradict the mechanism. One random draw is noisy, and "matches" is undefined. *Requirements:* use at least 20 placebo draws with fixed seeds as a null distribution. Refute if C falls inside its central 90%. Add an arm that differences against the mean of all cities.
- **H1-c. Major. Design Fit.** The stratifiers come from the 2018 view: the 30 cities that switched in 1989–2018, plus Akron, Louisville, Wheeling and Trenton. For the 1980, 1995 and 2011 folds this is the wrong set, and it uses metadata from after the cut-off. *Requirement:* define switch cities, low-coverage cities and the "current segment" per fold, from `Station Segment` and the valid flags at years ≤ cut-off.
- **H1-d. Major. Feasibility.** Four arms, up to four metrics, the EB weight, fallbacks and placebo draws probably take more than 2 hours. *Requirement:* scope the run to precipitation and hottest day, with arms A, C and D×20.
- **Biggest threat:** rival (b), a longer effective window (A ≈ C). Keep arm A as a co-primary comparator.

### H2: June–August slope added to the hottest-day level

- **H2-a. Major. Testability.** The floor makes the 1980 fold identical to m30, so only two folds test H2. Refutation needs ≤ 0 on both, so a null effect survives with probability about 0.75. *Requirements:* make the primary endpoint the pooled years 4–7 hottest-day difference over the 8 forecast years of the 1995 and 2011 folds, with a year-block interval. Then confirm on the X2 set.
- **H2-b. Major. Alternative explanation.** The adjustment uses year − c30 = 14.5 + lead. So about 80% of it is the same at every lead, and years 4–7 get only about 1.2× the years 1–3 shift. "The gain grows with lead" therefore barely separates a trend from a constant shift (rival b, and H3's hottest-day arm). *Requirements:* add a constant-shift arm matched to H2's mean shift in each fold. Discriminate on variation in b_JJA across folds, not on lead.
- **H2-c. Major. Testability.** κ̂ divides a noisy annual-maximum slope by the JJA slope. Its "1975 to cut-off" window is the hindsight hinge that the same report drops elsewhere, and at the 1980 fold it spans only 6 years. *Requirements:* use the 40-year window. Add a bootstrap interval, and read "κ̂ ≈ 1" as an interval that contains 1 and excludes 0.
- **H2-d. Major. Honor code.** κ = 1 rests on mckinnon2024pace, whose data run to 2023. The note itself says to treat it as background only. *Requirement:* justify κ from in-fold data (κ̂ up to the cut-off, or chosen on pseudo-origins), or record why a constant from that paper is allowed.
- **Feasibility:** 1–1.5 hours, using the shared per-year JJA table from X5. X3 also applies.

### H3: pooled skew shift toward the median

- **H3-a. Major. Testability.** The prediction of a "symmetric loss for the reversed sign" contradicts the mechanism. Near the optimum, extra MAE grows roughly with the square of the distance from the median. If the mean sits δ above the median:
  - the primary shift removes about fδ² of extra MAE;
  - the reversed shift, to median + 2δ, adds about 3fδ².

  That 1:3 asymmetry holds in expectation even when m30 is noisy. A symmetric response is what rival (a) predicts: a common wet or dry offset much larger than δ. *Requirement:* predict the ratio, about 3 under skew and about 1 under rival (a), and use it as the discriminator.
- **H3-b. Major. Alternative explanation.** High-CV cities sit mostly in the arid West and Southwest. easterling2017precipitation q1 reports falling precipitation there, so regional drying produces the same tercile pattern. *Requirement:* form CV terciles within each region, or use region fixed effects.
- **H3-c. Major. Design Fit.** H3 is the same rule as H13: m − s²/(3m) = m(1 − CV²/3). The precipitation prediction of +0.1 to +0.4 points is about 0.03–0.1 raw, the smallest effect in the set. *Requirements:* merge it with H13, call it exploratory, and run it only with the X1 test. Define the detrending used for γ̂ in the CDD and hottest-day arms.
- **Feasibility:** 45 minutes.

### H4: removing the shared national residual from the level

- **H4-a. Major. Testability.** The autocorrelation criterion uses one national series of about 40 values per fold, so its standard error is about 0.16. The prediction (< 0.15) and the refutation (> 0.3) sit within 1–2 standard errors of each other. Residuals from an in-sample trend fit are also biased toward negative autocorrelation, which favours the hypothesis. There is also a gap between the prediction and the refutation that neither covers. *Requirements:* use a bias-corrected autocorrelation with a block-bootstrap interval. Close the gap with a single primary threshold.
- **H4-b. Major. Design Fit.** Test (iii) does not have "far more power". All origins share one series with overlapping windows, so only a few level/target pairs are independent. A 50% binomial null does not hold. *Requirement:* use non-overlapping origins, or a block-permutation null.
- **H4-c. Major. Alternative explanation.** The correction is one scalar per fold, shared by all cities. Three folds therefore give three draws, and the 1995 and 1980 folds are confounded by curvature and by the floor. *Requirements:* make the quadratic arm (ii) co-primary. Run H4 with H11 as a 2×2 design: remove the common residual × shrink the city-specific part.
- **Feasibility:** about 1 hour, plus about 30 minutes for (iii).

### H5: CDD from the temperature departure

- **H5-a. Major. Testability: partly circular.** sens_i comes from an OLS fit of CDD on temperature over the same 40-year window (trend.py lines 85–103). Because temperature trends, sens absorbs part of any CDD trend that temperature does not explain. That pulls the u-slope toward 0, which favours the hypothesis. *Requirement:* for the diagnostic, estimate sens on first-differenced or detrended series, and report the u-slope with an interval.
- **H5-b. Major. Multiplicity.** The summer-sensitivity arm duplicates H2's secondary arm and H17's CDD arm. *Requirement:* run it once, as a shared arm.
- **H5-c. Nit.** Rival (c) is misstated. Annual mean temperature is measured with almost no error, so attenuation from measurement error is not the issue. The issue is that winter variance carries no information about CDD.
- **Assessment:** this is the cleanest confirmatory candidate: it adds no parameter and comes from theory. It takes about 45 minutes. Its predicted +0.13 to +0.38 raw sits near the noise floor.

### H11: shrinking the recent anomaly toward the regional mean

- **H11-a. Major. Undefined measure.** The estimator for B and the region definition are both left open. *Requirements:* fix the region as master's `region` column and give B's formula on data up to the cut-off. Use leave-one-out regional means.
- **H11-b. Major. Alternative explanation.** Rival (c), damping toward m30, is the main threat. *Requirements:* make the shrink-to-zero arm at the same B co-primary. Run the 2×2 with H4.
- **H11-c. Major. Testability.** "B about 1" is undefined. +0.5 temperature points in years 1–3 is about 0.13 raw, which is below the minimum detectable effect.
- **Feasibility:** about 1 hour.

### H12: regional anomaly with an in-fold damping factor λ

- **H12-a. Major. Design Fit.** λ is fitted on pseudo-origins by absolute error pooled over about 210 correlated cities. Its variance is set by the number of pseudo-origin years, which is small for the 1980 fold. *Requirements:* report a year-block interval for λ, and read "λ ≈ 0" as an interval that includes 0. Exclude the target city from its own regional median.
- **H12-b. Major. Alternative explanation.** Rival (b) is one region in one fold. The leave-one-region-out check has no decision rule. *Requirement:* set the rule in advance.
- **Feasibility:** 1–1.5 hours, sharing code with H11.

### H13: skew correction with an in-fold q

- **H13-a. Major. Duplicate.** H3 is H13 with q = 1/3. *Requirements:* merge them. Make q = 1/3 the primary arm and the in-fold q̂ a diagnostic with an interval.
- **H13-b. Major.** The same confound with CV and region as H3-b. Keep the stratification by missing-day count.
- **H13-c. Nit.** The "low-CDD cities" threshold is undefined.

### H14: summer-mean Tmax level plus long-run excess

- **H14-a. Major. Leakage.** No guard for the daily data is stated. See X5.
- **H14-b. Major. Alternative explanation.** Station relocations shift both annual maxima and summer means together. That pushes the coefficient of the decadal-change regression toward 1 and spuriously confirms the mechanism. *Requirements:* compute decadal changes only within station segments. Report an interval, and define "near 0".
- **H14-c. Major. Overlap with H2.** H14 uses July–August while H2 uses June–August. *Requirements:* fix one season in advance. Run one family with four arms: m30, H2, H14 and a constant-shift control. Keep the identity check, which is a good design element.
- **Feasibility:** 1.5–2 hours, or less if the JJA table is shared with H2.

### H15: step adjustment before computing the 30-year mean

- **H15-a. Major. Leakage.** Two parts can leak:
  - The post-switch window must stop at the cut-off. For example, a 2008 switch has only 3 in-fold years in the 2011 fold.
  - "Non-switching neighbours" must be classified from metadata up to the cut-off. A neighbour that switches in 2014 counts as non-switching in the 2011 fold.

  *Requirements:* detect switches in-fold, require a minimum number of post-switch years, and add a truncation test.
- **H15-b. Major. Undefined measure.** The shrinkage factor for steps, the number of placebo draws and the placebo decision rule are not specified.
- **H15-c. Major. Power.** Only switch cities can change, so the total effect is about 0.08–0.25 raw. *Requirements:* make the primary endpoint the paired MAE difference among switch cities, with a year-block interval pooled across folds. Keep the temperature arm as a positive control.
- **Feasibility:** borderline at 1.5–2 hours.

### H16: lead-decaying residual persistence

- **H16-a. Major. Testability.** Residuals share national anomalies, so naive standard errors for the pooled φ are far too small. The confirmatory test of φ1's sign is therefore anti-conservative. *Requirements:* use year-clustered standard errors or a year-block bootstrap. Make the city-specific φ1 the primary quantity.
- **H16-b. Major. Design Fit.** The effect is about 0.05 raw over all years. Generator A dropped this idea as a duplicate of U1, which has already been run. *Requirement:* check U1's lead-1 result before running H16.
- **H16-c. Nit.** Pseudo-origins up to cut-off − h are also leakage-free and add data. Define a fallback for when the cut-off year is invalid.
- **Feasibility:** about 1 hour.

### H17: season-specific levels and warm-season CDD slope

- **H17-a. Major. Undefined measure and flexible analysis.** Season boundaries, the set of windows and the in-fold selection rule are all unspecified. *Requirement:* fix all three before running.
- **H17-b. Major. Leakage.** See X5. Add an identity check: the season-weighted 30-year temperature must reproduce the official 30-year annual mean.
- **H17-c. Major. Feasibility.** As planned, this probably exceeds 2 hours. *Requirements:* run only the CDD arm, merged with the shared summer-sensitivity arm. Defer the temperature arm.

---

## Summary

| ID | Worst severity | Fits 1–2 h? | Leakage status | Recommendation |
|---|---|---|---|---|
| U1 | Major | Already run | Possible look-ahead in training features (U1-b) | Mark as tested; any rerun is exploratory |
| U2 | Major | Minutes | Clean | All-years endpoint; add ablations |
| U3 | Blocker | Minutes | Clean | Restate as directional or equivalence claim |
| H1 | Major | Over 2 h as planned | Stratifiers need in-fold definitions | Scope to precipitation and hottest day |
| H2 | Major | Yes | Guard specified; κ needs honor-code justification | Merge into a family with H14 |
| H3 / H13 | Major | Yes, 45 min | Clean | Merge; exploratory only |
| H4 | Major | Yes | Clean | Run as 2×2 with H11 |
| H5 | Major | Yes, 45 min | Clean | Highest priority |
| H11 | Major | Yes | Clean | Run as 2×2 with H4 |
| H12 | Major | Yes | Clean if the city is left out of its regional median | Lower priority |
| H14 | Major | Borderline | Daily data unguarded | Family with H2 |
| H15 | Major | Borderline | Two leakage paths (H15-a) | Defer |
| H16 | Major | Yes | Clean | Check U1 first |
| H17 | Major | No | Daily data unguarded | CDD arm only, merged |

**Suggested order, given that the deadline is today:**
1. Fix X1, X2 and X6 first.
2. H5.
3. The H2/H14 family on the shared JJA table.
4. The H4 × H11 2×2.
5. H1, scoped.
6. H3/H13, exploratory.

Defer H12, H15, H16 and H17.

No files were written.

## Round 2

Past the round limit, at the human's explicit request ("These experiments are not good. You
can find better examples" / "and hypos").

### Reviewer status

| Critic | Mode | Status | Blocker | Major | Nit |
| :----- | :--- | :----- | :------ | :---- | :-- |
| egm-novelty | BRAINSTORM | completed | 0 | 14 | 16 |
| egm-methodologist | BRAINSTORM | completed | 3 | 30 | 11 |
| egm-citation-auditor | REVIEW | not run (the human asked to skip auditor verification) | — | — | — |

This round is **incomplete**: egm-citation-auditor did not run.

### Finding IDs

Each critic label maps to an ID:

- **egm-novelty:** `egm-novelty-r2-<label>`.
  - Labels: X-1, X-2, E1-a…c, E2-a…c, E3-a…c, E4-a…c, H21-a…b, H22-a, H23/H32-a, H23-b, H23/H32-c, H24/H35-a, H24-b, H24/H35-c, H25/H33-a…b, H31-a, H34-a…d.
  - The hypothesis tag is the label's prefix, or the "Tags" line for X-1 and X-2.
- **egm-methodologist:** `egm-methodologist-r2-<label>`.
  - Labels: R2-X1…X8, E1-a…b, E2-a…c, E3-a…c, E4-a…c, H21-a…c, H22-a…c, H23/H32-a…c, H24/H35-a…c, H25/H33-a…c, H31-a…b, H34-a…c.
  - Blockers: E3-a, E4-a, H31-a.

### egm-novelty report (verbatim)

The full report as returned by the critic is filed below.

## Novelty review of hypotheses.md, Round 2 (E1–E4, H21–H25, H31–H35). Mode: BRAINSTORM

**Result:** 0 Blockers, 14 Majors, 16 Nits. No saved source already reports a result that any Round 2 hypothesis claims.

The problems are of two kinds:
- **E1–E4 name no prior work.** Each has close sources in the folder.
  - E1 and E2 use the method of CPC's damped OCN (vandendool2011readme).
  - E3 is a fitted stand-in for the 1975 hinge, and a fitted version of the rejected "slope × 1.5".
  - E4 runs into wilks2013projecting's precipitation result and may duplicate the rejected "trend added to all four metrics".
- **The folder is too thin to judge the generator ideas, and some of them are duplicates.**
  - The folder cannot confirm novelty for any generator mechanism, and both generators say so.
  - Three cross-generator pairs are duplicates: H23 = H32, H24 = H35, and H25 contains H33.
  - Four entries bring back Round 1 dropped candidates without saying so: E1, E3, H23 and H24.

**What I read:**
- The persona file.
- All 1,222 lines of `hypotheses.md`, plus `research_background.md` and `docs/trials/candidate_error_analysis.md`.
- `literature/INDEX.md` (including its Search Log and Gaps) and all 45 notes in `literature/notes/`.

**Limits:**
- Every note is unaudited, per the INDEX, so every quote below is unverified.
- `docs/experiments.md` was not supplied. I could not check overlap with the refuted panel fixed-effects level. E2 and H21, which act on city offsets, are the most likely overlaps.

---

## Cross-cutting

**X-1. Nit. Tags: H23/H32, H24/H35, H25/H33.**
- **Scope:** generator independence.
- **Prior work & difference:** Generator A says it read Generator B's section before finishing. It also dropped the October–December idea only after seeing B drop it. The three convergent pairs are therefore not independent corroboration.
- **Recommendation:** treat each pair as one idea when weighing support.

**X-2. Major, Thin Folder. Tags: H21, H22, H23, H24, H25, H31, H32, H33, H34, H35.**
- **Scope:** the novelty status of every generator hypothesis.
- **Prior work & difference:** The Search Log was planned for Round 1 topics. It ran in English only, on OpenAlex, arXiv, web search, NTRS, Europe PMC and Figshare. Semantic Scholar, Google Scholar and ORKG were not used, and AMS full texts were blocked. None of its 45 rows targets a Round 2 mechanism. The nearest rows kept 0 sources:
  - 11k, damped persistence;
  - 18b, empirical Bayes station shrinkage;
  - 18c, annual max Tmax trends at U.S. stations;
  - 11j, U.S. precipitation trends.
- **Recommendation:** run these searches before anyone claims "new" beyond the team:
  - **H21:** "regional versus local station temperature anomaly persistence"; "spatial scale decomposition decadal predictability United States"; "small area estimation climate normals".
  - **H22:** "soft thresholding sparse normal means empirical Bayes"; "sparse inhomogeneities station network".
  - **H23/H32:** "persistence of minimum versus maximum temperature anomalies stations"; "diurnal temperature range trends United States stations"; "siting and instrument effects on Tmax and Tmin".
  - **H24/H35:** "r-largest order statistics temperature"; "annual maximum temperature versus summer upper quantiles trends United States".
  - **H25/H33:** "wet-day frequency and intensity contributions to annual precipitation trends United States"; "decadal persistence station precipitation frequency".
  - **H31:** "point forecast integer-valued observations absolute error"; "consistent scoring functions median discrete"; "rounded observations forecast verification MAE".
  - **H34:** "changepoint detection climate series review"; "undocumented breaks maximum temperature first-order stations"; "precipitation gauge inhomogeneity annual totals".

---

## E1: Damped city anomaly for the hottest day (and precipitation)

**Closest saved work:**
- **vandendool2011readme.** Quote 1: "Shown is the last 10 (T), 15(P) years averaged minus a 30 year climatology for each of 12 seasons." Quote 3: "the amplitude of the operational OCN is reduced by a factor that relates to the a-priori skill so as to minimize RMS error." That is m30 + λ·(m15 − m30) with λ set from past skill: E1's form. E1's 15-year window is CPC's precipitation window. The note says it has no "skill numbers, MAE results, station-level data, or annual targets".
- **huang1996longlead (abstract only).** Quote 1: shorter, annually updated windows beat the 30-year normal. Quote 3: "Forecasts at leads beyond one year (skipping a year) are also reasonably skillful." This covers temperature at climate divisions, scored by correlation.
- **wilks2013projecting (abstract only).** Quote 3: "Averages of the most recent 15 and 30 yr have performed better … for U.S. divisional seasonal temperature and precipitation, respectively." This is the only precipitation result in the folder, and it points to λ ≈ 0.

**Remaining gap:**
- the annual-max Tmax target, for which the INDEX Gaps list no forecasting study;
- station scale;
- the national part removed before damping;
- λ fitted under MAE on pseudo-origins.

The precipitation arm adds least.

**Search coverage:** OCN was searched (row 4a and DOI lookups), but the key sources are abstracts or a web page. Not searched: damped OCN for extremes or annual maxima, and OCN precipitation skill at stations.

**E1-a. Major, Unnamed Closest Work.**
- **Scope:** E1 as a whole; it has no prior-work section.
- **Prior work & difference:** vandendool2011readme quote 3 is the method.
- **Recommendation:**
  - Cite it.
  - State the difference concretely: only the city part is damped; λ is fitted by absolute error at pseudo-origins rather than from a-priori correlation; the target is station annual maxima.
  - Frame the precipitation arm as a station-scale test of wilks2013projecting quote 3.

**E1-b. Major, team overlap not acknowledged.**
- **Scope:** E1's status "new".
- **Prior work & difference:**
  - Round 1 Generator A dropped "CPC skill mask with damped anomalies for precipitation and hottest day … the window results show no persistent anomaly to damp."
  - H12's discriminating experiment already listed "Use the city's own 15-year ratio at the same λ". So E1 is, in effect, H12's own-city arm. H12 was merged into H1 and never run.
- **Recommendation:** State what changed since the drop: the error analysis's city-part slope of 0.42, and the removal of the national part. Register E1 as the H12 control family rather than a new idea.

**E1-c. Nit, vague specification.**
- **Scope:** the formula "m30 + λ̂·(A_city)".
- **Prior work & difference:** The formula does not say what weight the national part of the anomaly gets. If it is 0, E1 differs from both CPC OCN and the window family. If the whole anomaly is damped, m30 + λ(m15 − m30) = (1 − λ)·m30 + λ·m15, which is a fixed two-window blend in the rejected window family.
- **Recommendation:** State the weight, and add a whole-anomaly-damped arm.

## E2: Shrink only the city-specific part of the temperature anomaly

**Closest saved work:**
- **efron1975data (abstract only).** Quote 1: James–Stein "lower mean squared error than the sample mean". This shrinks toward a common mean with a weight set by sampling noise.
- **vandendool2011readme, quote 3.** Damping set from past skill, but toward climatology and on the whole anomaly.
- **arguez2009improving, quote 2.** A station-specific OCN window "based on … the residual lag-1 (g) autocorrelation and the linear trend (β)". No skill test.

**Remaining gap:** out-of-sample damping, under MAE, of only the city-minus-national part, with the national part and the pooled trend kept. The difference is concrete and not in the folder.

**Search coverage:** a single query (18b) returned nothing relevant. The INDEX Gaps confirm no station-level partial-pooling application was found.

**E2-a. Major, Unnamed Closest Work.**
- **Scope:** E2 has no prior-work section.
- **Prior work & difference:** the three sources above, none named.
- **Recommendation:** Cite them and contrast:
  - efron: a weight from noise variance, against E2's predictive fit;
  - vandendool: damping toward climatology of the whole anomaly;
  - arguez: a per-station window, against one pooled λ.

**E2-b. Major, Vague Difference from H11.**
- **Scope:** "This differs from H11 in two ways."
- **Prior work & difference:**
  - Difference (i), national rather than regional target, was already a planned H11 arm: H11's discriminating experiment says "Compare regional against national pooling targets."
  - Difference (ii) cannot be checked from the file. H11 says B is "estimated in-fold" without naming the rule.
- **Recommendation:** Report whether H11's national arm ran and what it scored, and quote H11's actual weight rule. If (i) ran, E2's only new element is the predictive λ.

**E2-c. Nit, overlap.**
- **Scope:** E2's lineage.
- **Prior work & difference:**
  - U2 damps the city part, the national part and the trend together.
  - U1 gives the anomaly a single pooled coefficient.
  - E2 is the nested control for H21, H23 and H32.
- **Recommendation:** List all three relationships.

## E3: Fitted multiplier κ on the pooled trend

**Closest saved work:**
- **livezey2007estimation.** Quote 3: "The OCN works well except with very strong trends or longer extrapolations … least squares linear trend fits to the period since the mid-1970s are viable alternatives. An even better alternative is the use of 'hinge fit' normals." Quote 4 gives the hinge form: flat to 1975, linear after.
- **wilks2013performance (abstract only).** Quote 3: "'hinge' functions with the change point fixed at 1975 performed well for the spring and summer seasons." Quote 4 describes a hybrid. Against this, wilks2013projecting quote 2 says the hinge is "not yet justified".
- **gardner1985forecasting.** Damping trends with low persistence. E3 predicts the opposite, κ > 1.

A 40-year window that straddles 1975 underestimates the post-1975 rate. E3's κ > 1 is a one-parameter proxy for the hinge correction. E3's own caveat ("at the 2018 cut-off the 40-year window is all post-1975") is the hinge argument.

**Remaining gap:** a fitted, MAE-scored trend multiplier on pooled station slopes. Narrow.

**Search coverage:** the hinge and OCN literature is reasonably covered, but the Wilks papers are abstract-only. Unknown whether their formulations include a scaled or accelerated trend.

**E3-a. Major, Unnamed Closest Work.**
- **Scope:** E3's mechanism.
- **Prior work & difference:** livezey2007estimation quotes 3–4 and wilks2013performance quote 3, neither cited.
- **Recommendation:** Cite them, and add a pooled post-1975-only slope arm as the comparator from the literature. κ̂ beating that arm is the only new result E3 can claim.

**E3-b. Major, team overlap not acknowledged.**
- **Scope:** E3's status "new".
- **Prior work & difference:**
  - `research_background.md` lists "slope × 1.5" as rejected.
  - Round 1 Generator A dropped the "Pooled 1975 hinge slope".
  - U1 learned "horizon-dependent trend damping".
  - Round 2 Generator A dropped "Pooled quadratic or accelerating trend: a variation of E3 and of the dropped hinge".
- **Recommendation:** Report κ̂ per fold. If κ̂ ≈ 1.5 at the official cut-offs, E3 is the rejected variant.

**E3-c. Nit.**
- **Scope:** headroom.
- **Prior work & difference:** E3 targets the same common-shift-per-fold headroom as H4, which was kept.
- **Recommendation:** List H4 as a sibling. The same headroom cannot be credited to both.

## E4: Pooled multiplicative precipitation trend

**Closest saved work:**
- **wilks2013projecting, quote 3.** 30-year averages were best for divisional seasonal precipitation among eight formulations, including the hinge.
- **easterling2017precipitation, quote 1.** "Annual precipitation has decreased in much of the West, Southwest, and Southeast and increased in most of the Northern and Southern Plains, Midwest, and Northeast. A national average increase of 4% … is mostly a result of large increases in the fall season." A single pooled trend averages over regions whose trends have opposite signs.
- **lai2020use (abstract only).** ARIMA was compared "with a linear trend method" for local annual precipitation. The error metric is unknown.

**Remaining gap:** a station-scale pooled relative trend, scored by MAE. The INDEX Gaps confirm nothing at station level. But the closest saved result is negative.

**Search coverage:** row 11j kept 0. The full texts of wilks2013projecting and lai2020use were not obtained.

**E4-a. Major, Unnamed Closest Work.**
- **Scope:** E4 as a whole.
- **Prior work & difference:** the three sources above, none named.
- **Recommendation:** Cite them, and state that E4 adds station annual totals, a pooled relative slope and MAE scoring.

**E4-b. Major, possible duplicate of a rejected variant.**
- **Scope:** E4's status "new".
- **Prior work & difference:**
  - `research_background.md` lists "trend added to the hottest day, or to all four metrics" as rejected. E4 must say whether that run used a precipitation-specific slope.
  - E4 has the same structure as H2 (m30 + slope·(year − c30)), which failed for the hottest day.
  - H3, H13, H25 and H33 all name E4's wetting drift as a rival.
  - Round 2 Generator A dropped a fall-only trend as a variation of E4.
- **Recommendation:** Add one line saying how E4 differs from the "all four metrics" run.

**E4-c. Nit, from the supplied data.**
- **Scope:** E4's premise.
- **Prior work & difference:**
  - The precipitation oracle for a perfect common shift per fold is only 0.65 (all years) in `candidate_error_analysis.md`.
  - The mean signed error of −0.52 in hides 4 of 10 origins with the opposite sign: 1962, 1995, 2000 and 2005.
- **Recommendation:** State the ceiling next to the prediction.

## H21: Damp the regional part, keep the local part

**Closest saved work:** H21 names haug2020spatial (quote 2: trend as a "latent Gaussian random field"), and its distinction is concrete. Closer for the forecasting step is vandendool2011readme quote 3, which damps the whole anomaly. efron1975data quote 1 also applies.

**Remaining gap:** separate damping weights by spatial scale. Not in the folder. Search coverage: X-2.

**H21-a. Nit.**
- **Scope:** Closest prior work.
- **Prior work & difference:** vandendool2011readme appears only as an inspiration.
- **Recommendation:** Name it as the closest forecasting precedent.

**H21-b. Nit, overlap.**
- **Scope:** Closest prior work (team).
- **Prior work & difference:** H21 names H11 and E2 but not:
  - Round 1 H1, which is the opposite corner of H21's 2×2 design. Its level is the neighbours' current anomaly plus a local offset averaged over the current station segment: the regional part at full weight, the recent local deviation replaced by a long-run offset.
  - H12, which damps only the regional part (for precipitation and the hottest day).
- **Recommendation:** Check whether H1's temperature arm ran. Its result bears directly on λ_r against λ_l.

## H22: Soft-threshold the hottest-day anomaly

**Closest saved work:**
- vandendool2011readme quote 2: "where a-priori correlation is less than 0.3 no forecast is shown". This is a skill threshold by location, and H22 states its difference from it concretely.
- efron1975data, the linear Stein rule, as the contrast.

**Remaining gap:** per-city nonlinear shrinkage with one pooled τ under MAE. The folder has no source on thresholding. Search coverage: X-2.

**H22-a. Nit, overlap understated.**
- **Scope:** the status line "overlaps H34's step story only in rival (d)".
- **Prior work & difference:**
  - The mechanism's sparse shifts ("relocations, instrument changes") are the H15/H34 step mechanism.
  - Arm 5 (switch-only) sits close to H15 and to the rejected "level from the current station segment only".
  - The hard-threshold arm is closest to Round 1 Generator A's dropped "CPC skill mask" idea.
- **Recommendation:** List these overlaps in the status line.

## H23 and H32: Separate Tmin and Tmax coefficients (duplicate)

**Closest saved work:**
- **arguez2009improving, quotes 3–4.** The window–trend correlation is −0.78 for January Tmin and −0.35 for July Tmax. This is station OCN with no skill test.
- **hausfather2013quantifying, quote 1.** Urbanization accounts for 14–21% of the rise in unadjusted Tmin since 1895.
- menne2009homogenization, quote 3.

**Remaining gap:** separate out-of-sample weights for the two components. Search coverage: X-2.

**H23/H32-a. Major, duplicate.**
- **Scope:** both entries.
- **Prior work & difference:** Same specification (candidate + β_max·A_max/2 + β_min·A_min/2, on 15-year city parts), same E2 comparator, same primary endpoint. They differ only in:
  - the clip: H32 uses [−1, 1]; H23 states none;
  - H32's switch-stratified arm;
  - H23's {regional, local} × {Tmax, Tmin} joint regression.
- **Recommendation:** Merge into one family with one primary endpoint.

**H23-b. Nit.**
- **Scope:** H23's Closest prior work.
- **Prior work & difference:** H23 omits Round 1 Generator B's dropped "Separate Tmax and Tmin components … algebraically the same as the candidate". H32 cites it and states the difference.
- **Recommendation:** Add it to H23.

**H23/H32-c. Nit.**
- **Scope:** Inspirations.
- **Prior work & difference:**
  - arguez2009improving compares January Tmin with July Tmax. Its contrast mixes component with season, which is the seasonal rival, so it does not isolate the diurnal component.
  - hausfather2013quantifying is about century-scale trends, not 7-year persistence, as H32's own Thin Spots concede.
- **Recommendation:** Treat both as motivation, not as prior evidence.

## H24 and H35: Mean of the 10 hottest days as the predictor (duplicate)

**Closest saved work:**
- katzndblock quote 4: "μ(t) = μ0 + μ1 t, ln σ(t) = σ0 + σ1 t". Trends are fitted on the maxima themselves.
- mckinnon2024pace quote 1: "the hottest summer days have warmed at the same pace as the median globally, in each hemisphere, and in the tropics from 1959 to 2023". This is the only saved source on upper quantiles of summer Tmax.

**Remaining gap:** using upper order statistics to predict the city part of the annual-maximum anomaly. Search coverage: X-2.

**H24/H35-a. Major, duplicate.**
- **Scope:** both entries.
- **Prior work & difference:** Same T10 predictor, same E1 comparator, same primary endpoint, and the same go/no-go check (a variance ratio of 0.85, or equivalently a reduction under 15%). They differ in:
  - the validity rule: H24 allows at most 10 missing Tmax days; H35 requires at least 85 June–August days;
  - H24's extra June–August standard-deviation and Avg Tmin control arms.
- **Recommendation:** Merge, and pick one validity rule.

**H24-b. Nit.**
- **Scope:** H24's Closest prior work.
- **Prior work & difference:** H24 omits Round 1 Generator A's dropped "Using the r largest daily Tmax values for the hottest-day level". H35 cites it and separates level from predictor.
- **Recommendation:** Add it to H24.

**H24/H35-c. Nit.**
- **Scope:** Closest prior work.
- **Prior work & difference:** mckinnon2024pace is listed only as background.
- **Recommendation:** Name it as the closest saved work on upper quantiles.

## H25 and H33: Wet-day frequency against intensity (near duplicate)

**Closest saved work:**
- easterling2017precipitation, quotes 1 and 3: regionally mixed trends, "Interannual variability is substantial".
- wilks2013projecting, quote 3.
- livezey2007estimation, quote 6.

**Remaining gap:** frequency and intensity components as predictors. Search coverage: X-2.

**H25/H33-a. Major, duplicate.**
- **Scope:** both entries.
- **Prior work & difference:** H33's three regressors (wet days, body total, total) are all arms of H25, which adds the intensity term. Both use λ clipped to [0, 1] on 15-year city-part ratios.
- **Recommendation:** Merge, with H25's two-coefficient form as primary.

**H25/H33-b. Nit.**
- **Scope:** Closest prior work and Leads.
- **Prior work & difference:**
  - The INDEX Unverified Leads already list Kunkel et al. (2020), "Precipitation Extremes: Trends and Relationships with Average Precipitation …". Neither entry cites it (H12 did).
  - The heavy-tail premise is the same as in H3 and H13.
- **Recommendation:** Fetch Kunkel et al. (2020), and name H3/H13.

## H31: Round the hottest-day forecast to a whole °F

**Closest saved work:** natekin2013gradient quote 1: "The L1 -loss corresponds to the median of the conditional distribution". No saved source covers point forecasts for discrete targets, as H31 says. Search coverage: X-2, with no relevant query in the log.

**H31-a. Nit.**
- **Scope:** Closest prior work and data inspiration.
- **Prior work & difference:** H31 is a competing reading of the Round 1 30-year-median result. Generator A's item 3 read that result as drift and H3/H13 as skew; H31 reads it as discreteness. H31 names these. Its derivation comes from no note.
- **Recommendation:** Keep "new" as team-internal until the X-2 searches run. Have the derivation checked by the methodologist; it is outside this review.

## H34: Data-chosen break year for the hottest day

**Closest saved work:**
- **menne2009homogenization, quotes 1–3.** Quote 2: "a lower false-alarm rate for undocumented changepoint detection relative to the more common use of a reference series."
- **wilks2013performance, quote 2.** "The use of homogenized station data shows clear improvement over nonhomogenized station data … in terms of mean-squared specification errors on independent data."
- **arguez2009improving, quote 6.** Pairwise homogenization detects undocumented changepoints.

Search coverage: X-2. The INDEX Gaps also note "Nothing specific to first-order or airport stations".

**H34-a. Major, Unnamed Closest Work.**
- **Scope:** Closest prior work.
- **Prior work & difference:** wilks2013performance quote 2 is the folder's only result that removing artifacts improves normals out of sample. H34 cites only menne2009homogenization.
- **Recommendation:** Cite it, and state the difference: annual maxima and precipitation; a level chosen at a break rather than a homogenized series; MAE scoring.

**H34-b. Major, unfavourable difference not addressed.**
- **Scope:** "H34 uses one regional reference".
- **Prior work & difference:** menne2009 quote 2, which H34 cites, reports the single-reference approach as having more false alarms than pairwise comparison.
- **Recommendation:** Justify the choice, for example by the sparse network, or add a pairwise-difference arm.

**H34-c. Nit, overlap.**
- **Scope:** Closest prior work (team).
- **Prior work & difference:** H34 names H15 and E1 but omits:
  - H22, which has the same sparse-shift premise;
  - U3;
  - H1's current-segment offset;
  - the rejected current-station level.
- **Recommendation:** List them.

**H34-d. Nit.**
- **Scope:** Inspirations.
- **Prior work & difference:** vose2017temperature quote 5 (only a slight national rise in the warmest day since the mid-1960s) says nothing about whether local changes are steps or trends.
- **Recommendation:** Drop it as support for steps.

---

## Overlap map

| ID | Within Round 2 | Earlier rounds | Named by the hypothesis? |
|---|---|---|---|
| E1 | Control for H22, H24/H35, H34, H25/H33 | H12 own-city arm, R1-A dropped "damped anomalies", window family, U2 | No |
| E2 | Nested in H21, H23/H32 | H11 (and its national arm), U1, U2 | H11 only |
| E3 | A's dropped quadratic trend | slope × 1.5, R1-A dropped hinge, U1, H4 | No |
| E4 | Rival in H25/H33; A's dropped fall-only trend | "trend added to all four metrics", H2 structure, H3/H13 rivals, 40/50-year precipitation means | No |
| H21 | Nests E2; H23/H32 are rivals | H11, H1, H12, H17 | H11 and E2 only |
| H22 | E1, H34 | H15, R1-A dropped skill mask, rejected current-station level | Partly |
| H23 = H32 | E2, H21 | R1-B dropped Tmax/Tmin split, H17 | H32 only for the R1 drop |
| H24 = H35 | E1, H22, H34 | H14, H2, R1-A dropped r-largest | H35 only for the R1 drop |
| H25 ⊇ H33 | E1 precipitation arm, E4 | H12, H3/H13 | Partly |
| H31 | Combines with every hottest-day arm | H3, H13, 30-year median, R1-A item 3 | Yes |
| H34 | E1, H22, H35 | H15, U3, H1, current-station level | H15 and E1 only |

(R1-A and R1-B are Round 1 Generators A and B.)

## Leads to Fetch (unverified; none used as evidence)

Already listed in the INDEX:
- Kunkel et al. (2020), JAMC, DOI 10.1175/JAMC-D-19-0185.1 (H25/H33, E4).
- Livezey & Smith (1999) (E3).
- Meehl et al. (2012) (H24/H35).
- Cheng et al. (2014) (H24/H35).
- Full texts of Huang et al. (1996), both Wilks (2013) papers, and Lai & Dzombak (2020) (E1, E3, E4).

From memory:
- van den Dool (2007), *Empirical Methods in Short-Term Climate Prediction*, on OCN damping (E1, E2).
- Gneiting (2011), JASA (H31).
- Donoho & Johnstone (1994), Biometrika (H22).
- Karl et al. (1993), BAMS (H23/H32).
- Karl & Knight (1998), BAMS (H25/H33).
- Coles (2001), on r-largest order statistics (H24/H35).
- Reeves et al. (2007), JAMC changepoint review (H34).
- Peterson et al. (1998), IJC homogeneity review (H34).
- Menne, Williams & Palecki (2010), JGR, on U.S. siting effects on Tmax and Tmin (H23/H32, H34).
- Quayle et al. (1991), BAMS, on thermometer (MMTS) changes, and the HO-83 Tmax bias literature (H34).
- Deser et al. (2012) (H21).
- Zhang et al. (2011), ETCCDI definitions (H24, H25/H33).

Relevant paths:
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`
- `/Users/atabaresa/repos-new/proto-star-challenge/docs/trials/candidate_error_analysis.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`

### egm-methodologist report (verbatim)

The full report as returned by the critic is filed below.

Methodologist review, BRAINSTORM mode: Round 2 (E1–E4, H21–H25, H31–H35)

**Study type and claim type.** This is a computational comparison of forecasting methods: statistical forecasters scored on fixed rolling-origin backtests of observational station data, used to pick one 2019–2025 submission. The document labels H21–H25 and H32–H35 exploratory and H31 confirmatory. E1–E4 have no label, but they are written as pass/fail tests. Every Round 2 hypothesis was derived from diagnostics that include the truth of the test folds, so I treat all of them as exploratory, with one exception: H31's narrow backtest claim.

**Files read**
- Persona: /Users/atabaresa/repos-new/egm/egm-research/agents/methodologist.md
- Standard: /Users/atabaresa/repos-new/egm/egm-research/resources/document_standards/ml-empirical-research-standard.md
- Standard notes: herrmann2024position, kapoor2022leakage, shadish2002experimental and dror2018hitchhikers, under /Users/atabaresa/repos-new/egm/egm-research/resources/literature/notes/
- Target: /Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md (all 1222 lines)
- Context: /Users/atabaresa/repos-new/proto-star-challenge/research_background.md, /Users/atabaresa/repos-new/proto-star-challenge/docs/trials/candidate_error_analysis.md, /Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md

I did not read `anomaly.py`, the configs, `paired_bootstrap.py` or `hypotheses_review.md`, because they were not supplied. The leakage requirements below are therefore about what the documents state, not about verified code. Every required file was readable, so the review is complete.

**Counts.** 3 Blockers (E3-a, E4-a, H31-a), 30 Majors, 11 Nits.

---

## Cross-cutting findings

**R2-X1 [all 14] — Major — Alternative Explanation (selection on the test folds)**
- **Risk:**
  - `candidate_error_analysis.md` uses the truth of all 10 origins. These are the 3 official folds plus every set Round 2 calls secondary (1985/1990/2000/2005 and 1955/1962/1969).
  - Every number that motivates the round comes from that truth: the slopes 0.42 / 0.21 / 0.65 / 0.88, the CDD bias series, the −0.52 in precipitation bias and the oracle headrooms.
  - So no origin set named in Round 2 can confirm anything. For E1 and E2 the official-fold result is partly known in advance: the in-fold λ̂ only has to recover a slope the analyst has already seen on those folds.
  - E1–E4 state pass rules but no claim type.
- **Requirement:**
  - Label every Round 2 official-fold result exploratory, except H31's backtest claim.
  - Before any run, fix a replication set whose target years were never used as F. The only option is origins before 1955 (for example 1934, 1941 and 1948, with targets 1935–1955). Count first how many cities have a valid 30-year window at those origins.
  - State that these origins are less contaminated, not clean: their years entered A and m30 for the 1955 and 1962 origins.
  - Fix the adoption rule now (see R2-X3). Source: herrmann2024position; standard §1.

**R2-X2 [E1–E4, H21–H25, H32–H35] — Major — Design Fit (leakage is under-specified)**
- **Risk:** "origin + lead ≤ cut-off" is necessary but not sufficient. None of the entries says how the quantities at each pseudo-origin p are built.
- **Requirement:** write the following into each config.
  1. At each p, recompute from years ≤ p only: the 30-year mean, the N-year anomaly, the cross-city and regional means, s_i, and CDD-per-degree. Using the fold's m30 instead would put the target years p+1..p+7 into both A and F and attenuate λ̂.
  2. Where the regressand is the candidate's error (H21, H23, H32), or where the trend is rescaled (E3), re-fit the candidate at p: pooled slope over p−39..p, with the floor. Do not reuse the slope fitted at the cut-off.
  3. For H34, re-run the break scan at each p.
  4. Build switch and segment indicators used as inputs (H22 arm 5, H32's secondary arm) only from station changes at or before the cut-off (at or before p for pseudo-origins). Confirm that `Station Segment` and `years_since_switch` do not encode station history after the cut-off.
  5. Build daily aggregates (H24/H35) with Date ≤ cut-off and per-year validity rules. Daily-quality flags must not come from full-record statistics.
  6. State the pseudo-origin set (first p and spacing), per-lead versus 7-year-mean targets, the fitting loss, and the coefficient bounds.
  7. Add an invariance test: perturb all rows after the cut-off and assert identical forecasts and coefficients.
- Source: kapoor2022leakage; standard §2.

**R2-X3 [all] — Major — Testability (multiple comparisons and adoption rule)**
- **Risk:**
  - There are 14 primary endpoints. The three convergent pairs (H23/H32, H24/H35, H25/H33) reduce them to about 11 families, plus about 40 secondary arms, on folds already reused about 60 times.
  - If all 11 nulls are true and the tests are independent, P(at least one passes at α = 0.05) ≈ 0.43. Nesting lowers this, but not to 0.05.
- **Requirement:** before running, fix a gatekeeping plan.
  - Root tests: E1 (hottest day), E2 and H31, under Holm at family-wise α = 0.05. E3 and E4 are kept out of the submission (see below).
  - Refinements are tested against their parent only if the parent passes, with Holm within each branch: H22, H24/H35 and H34 under E1; H21 and H23/H32 under E2; H25/H33 under E1's precipitation arm.
  - Adoption requires all three: passing the gate, the same sign on the replication set, and an in-fold coefficient with the same sign at all three cut-offs.
  - Run the final composite once. Expect the adopted gain to shrink (winner's curse).
- Source: dror2018hitchhikers, demsar2006statistical; standard §4.

**R2-X4 [H21, H22, H23, H24, H25, H32, H33, H34, H35] — Major — Alternative Explanation (gain not attributed)**
- **Risk:** Each primary endpoint compares against the candidate. Generator A's item 4 says this mostly measures the E1- or E2-type gain, so a pass would credit the refinement with its parent's gain.
- **Requirement:**
  - Make the primary the paired difference against the nested parent (E1, E2 or E1's precipitation arm), fitted by the same pseudo-origin procedure on the same rows. The comparison with the candidate becomes secondary.
  - The expected refinement gains are a few tenths of a point, which is inside the roughly ±0.5 pp interval. So make the in-fold coefficient contrast, with an era-blocked interval, the mechanism endpoint, and say in advance that the score comparison will probably be inconclusive.
- Source: lipton2018troubling; standard §3.

**R2-X5 [all; most acute for the city-part hypotheses] — Major — Testability (unit of inference)**
- **Risk:**
  - The paired year-block bootstrap resamples years. A city-part change fixes one adjustment per city per fold.
  - The uncertainty that matters for the decision is between eras: whether the persistence coefficient in 2019–2025 resembles that of 1980, 1995 and 2011. Resampling 21 year blocks does not capture it.
  - Generator A's claim that city-part changes give narrow intervals holds only for these three eras.
- **Requirement:**
  - Report per-fold paired differences and per-fold λ̂ for the 3 folds and all 10 origins.
  - Add a region × fold cluster bootstrap as a sensitivity check and report the wider interval.
  - State the number of resamples, the block definition and the interval type.
- Source: bouthillier2021accounting, dror2018hitchhikers; standard §4.

**R2-X6 [all; most acute for E3, E4, H31] — Major — Alternative Explanation (post-2018 knowledge in an LLM)**
- **Risk:**
  - All 14 hypotheses were written by LLMs whose training includes data after 2018.
  - Some changes cannot be justified by a backtest on data through 2018: E3, E4 and H31's transfer judgment. Those are the openings through which post-2018 knowledge could steer the submission, against the honor code rule "never tune or select using knowledge of 2019–2025".
- **Requirement:** adopt only changes whose whole justification lies in backtests and data checks through 2018, and record that justification for each change. Source: research_background constraints; standard §2 (contamination, by analogy).

**R2-X7 [all] — Major — Design Fit (time)**
- **Risk:** 14 hypotheses at 0.5–2 h each is about 15–20 h of work. The deadline is 2026-11-10 23:59 ET, and the error analysis was generated today.
- **Requirement:** fix a short list in this order:
  1. The H31 lattice gate (minutes).
  2. E1 (hottest day plus a precipitation arm).
  3. E2, read through H21's joint {regional, local} × {Tmax, Tmin} regression.
  4. H22, which reuses E1.
- Defer H24/H35, H25/H33 and H34. Drop E3 and E4 from the submission.

**R2-X8 [all] — Nit.** The literature notes are unaudited, and none addresses 7-year persistence of station anomalies (both generators say so). The inspirations are not evidence. The convergent pairs are not independent replications: Generator A saw B's section mid-run.

---

## Per-hypothesis findings

### E1 (damped city anomaly for hottest day, plus precipitation)
- **Refuted by:** in-fold λ̂ ≈ 0, or a hottest-day paired difference ≤ 0.
- **Simplest design:** m30 + λ̂·A_city with N = 15, master only, under 1 h.
- **Biggest threat:** the persisting city part is station or instrument steps whose mix changes by era.
- **E1-a — Major — Testability.**
  - *Risk:* There is only a pass rule. An interval that includes 0 is left undefined. N, the loss (OLS on 7-year means or MAE on annual rows), the pseudo-origin set, the bounds and the status of the precipitation arm are not given.
  - *Requirement:* Add refutation rules: point estimate ≤ 0, or λ̂ < 0.15 at 2 or more of 3 cut-offs, or a negative result on the replication set. Fix N = 15 and a clip of [0, 1]. Declare the precipitation arm secondary with its own endpoint.
- **E1-b — Major — Alternative Explanation.**
  - *Risk:* The gain may come from switch-city steps, and the share of switches differs between the 1950–1980 windows and the 1989–2018 window.
  - *Requirement:* Report the gain for cities with and without a switch inside each fold's 30-year window (in-fold definition), and λ̂ at each of the 10 origins.

### E2 (shrink the city part of the temperature anomaly toward the national mean)
- **E2-a — Major — Testability.**
  - *Risk:* There is no pass rule, refutation rule or claim type.
  - *Requirement:* Refuted if λ̂_c ≥ 0.9 at 2 or more cut-offs, or if the point estimate is ≤ 0. Define the anomaly as the city part of the candidate's 10/15-year level minus m30, declare CDD unchanged, and report the raw score.
- **E2-b — Major — Alternative Explanation.**
  - *Risk:* H11, which shrank the city-minus-region part, was significantly worse over 7 cut-offs (−0.74 [−1.08, −0.38]). So the local part carries signal, and E2 shrinks it too. Any E2 gain would have to come from the regional part, and only H21 can show that.
  - *Requirement:* Run E2 as the β_r = β_l case inside H21's design and interpret the two together.
- **E2-c — Nit.** The 0.65 is for N = 15 alone, while the candidate blends the 10- and 15-year levels (slopes 0.62 and 0.65). Say which one λ̂ targets.

### E3 (κ multiplier on the pooled trend)
- **E3-a — Blocker — Design Fit (does not transfer).**
  - *Risk:*
    - At the 2018 cut-off, every pseudo-origin with a complete 7-year target has p ≤ 2011, so its 40-year window starts in 1972 or earlier and straddles the mid-century plateau.
    - The real forecast's window, 1979–2018, is entirely after the mid-1970s turn. κ̂ is therefore fitted under a window composition that never occurs in the 2019–2025 forecast, and is likely above 1 for exactly that reason. Applied to the 1979–2018 slope, it would over-correct.
    - Per-lead fitting does not rescue this: windows starting after 1975 need p ≥ 2014, which gives a few overlapping pseudo-origins at leads ≤ 4 in a single era.
    - A hinge-conditioned κ cannot be backtested honestly at 1980 or 1995, because the hinge was hindsight for those folds.
    - The caveat E3 states in advance concedes all of this.
  - *Requirement:* Keep E3 out of the submission. At most, run it as a diagnostic.
- **E3-b — Major — Testability (power).**
  - *Risk:*
    - If the 1941–1980 pooled slope is floored, κ has no effect at the 1980 fold, leaving 2 active folds.
    - The 1995 fold is biased warm (+0.086 °F, +16.9 CDD), so κ > 1 probably hurts it. The cold-bias evidence comes mainly from 2000 and 2005, which are not official folds, and from 2011.
    - Common-shift intervals were ±3.3 pp for H4, and the effective sample is the number of folds.
  - *Requirement:* Report per-fold results. Treat any score as inconclusive unless the effect is at least about 3 pp.
- **E3-c — Major — Testability.**
  - *Risk:* κ also scales the CDD trend through CDD-per-degree, yet the primary endpoint is temperature only, and there is no refutation rule.
  - *Requirement:* Make the raw score in years 4–7 the primary. Refuted if κ̂ ≤ 1 at both active folds.

### E4 (pooled relative precipitation trend)
- **E4-a — Blocker — Design Fit (effect ceiling below the detection limit).**
  - *Risk:*
    - The same table caps a perfect per-fold national precipitation shift at 0.65 pp for all years (0.42 for years 1–3, 0.62 for years 4–7). A pooled relative trend is close to a common shift, so it can earn only part of that, about 0.16 raw at most.
    - Common-shift intervals in Round 1 were ±1.06 pp (hottest day) and ±3.3 pp (temperature).
  - *Requirement:* Before running, pass a placebo common shift through the same bootstrap to get the minimum detectable effect. If it exceeds about 0.3 pp, drop E4 as a hypothesis test.
- **E4-b — Major — Testability (measure not defined).** "Long window", the sign or floor rule, the pooled estimator and the anchor are all unspecified. Fix them before the run.
- **E4-c — Major — Alternative Explanation.** The sign of the reference's precipitation bias varies: 6 of the 10 origins are wetter than m30 and 4 are drier, and the official folds read −1.70, +0.63 and −1.59. Both the motivating −0.52 in and the losses of the Round 1 downward shifts (H3, H13) come from these same folds. Report the fitted trend's sign at each fold.

### H21 (damp the regional part, keep the local part)
- **Strength:** under pure noise the regional mean is more reliable, so noise predicts λ̂_r > λ̂_l. H21 predicts the opposite order, which makes it a severe test.
- **H21-a — Major — Testability.**
  - *Risk:* "λ̂_l interval contains 1" counts non-rejection as support. A wide interval passes trivially.
  - *Requirement:* Use an equivalence-style bound instead (for example, lower 95% bound ≥ 0.7). Replace "λ̂_r ≤ 0.7" with an interval criterion.
- **H21-b — Major — Design Fit (power).**
  - *Risk:* β_r is identified by about 6 regions × a few decadal episodes per fold, over heavily overlapping pseudo-origins.
  - *Requirement:* Use an era- and region-blocked coefficient bootstrap and state the pseudo-origin spacing. Expect H21 versus E2 to be inconclusive on score.
- **H21-c — Nit.** H21 was derived from H11's failure on the same 7 cut-offs. Its early-origin confirmatory declaration is valid only if it is made before the split is computed on any origin.

### H22 (soft threshold on the hottest-day z)
- **H22-a — Major — Design Fit (power).**
  - *Risk:* Only about 5% of cities fall in the |z| > 2 bin at each pseudo-origin, and adjacent pseudo-origins overlap. The bin slopes and τ̂ will be noisy, and the "slopes differ by less than 0.1" rule uses point estimates.
  - *Requirement:* Set a minimum bin count, use a city-cluster interval on the slope difference, and note that τ = 0 is the rejected full city anomaly.
- **H22-b — Major — Alternative Explanation.** Arms 5 and 6 test the documented-switch account well, but only with switch definitions built inside the fold (R2-X2, item 4).
- **H22-c — Nit.** Six arms add to the multiplicity load. Declare soft threshold versus E1 as the primary and every other arm secondary.

### H23 / H32 (separate Tmin and Tmax coefficients; one family)
- **H23/H32-a — Major — Testability.**
  - *Risk:* There are two specifications of one hypothesis: H32 clips to [−1, 1] and H23 states no clip, and their predictions and refutations differ.
  - *Requirement:* Pick one before running and count it as one family.
- **H23/H32-b — Major — Alternative Explanation.**
  - *Risk:* Reliability alone, meaning noisier Tmax city anomalies, predicts the same order.
  - *Requirement:* The mechanism is supported only if the fitted-minus-reliability-implied difference has an interval that excludes 0.
  - *Additional rival (my background knowledge, not in the folder; Generator B lists it as a lead):* era-specific Tmax instrument biases at first-order stations (the HO-83 period) could make λ_max < λ_min at the 1995 fold alone. Report λ̂ per origin.
- **H23/H32-c — Nit.**
  - Keep the scored rows identical to the candidate's, even where the Tmax and Tmin validity rules differ.
  - H32's "beats the single coefficient on 2 of 3 folds" is close to a coin flip at effects of a few tenths of a point.

### H24 / H35 (mean of the ten hottest days; one family)
- **H24/H35-a — Major — Testability.**
  - *Risk:* The score endpoint cannot detect the expected gain over E1, which is a few tenths of a point.
  - *Requirement:* Make the pseudo-origin correlation contrast the primary. Use a named test for dependent correlations that share F (Williams or Steiger, or a city-cluster bootstrap) and declare the 0.05 threshold. Make the score against E1 secondary.
- **H24/H35-b — Major — Design Fit (data and leakage).**
  - *Risk:* There are two validity rules for one quantity: Tmax missing on 10 days or fewer (H24) versus at least 85 June–August days (H35).
  - *Requirement:* Pick one, aggregate daily data per year inside the fold, and run the invariance test.
- **H24/H35-c — Nit.** The variance go/no-go is almost certain to pass and tests the wrong property (covariance with the future maximum matters, not variance). The k-ladder adds 4–6 arms.

### H25 / H33 (wet-day frequency; one family)
- **H25/H33-a — Major — Design Fit (power).**
  - *Risk:* The precipitation city-part slope is 0.21 with a correlation of 0.12 or less. The expected effect of +0.2 to +1.0 pp is at or below the minimum detectable effect.
  - *Requirement:* Use the λ̂_W versus λ̂_I contrast, with an interval, as the mechanism endpoint, and keep H25's "inconclusive" outcome.
- **H25/H33-b — Major — Alternative Explanation (measurement and transfer).**
  - *Risk:* The `Wet Days` threshold is unconfirmed, and wet-day counts are sensitive to the gauge, the observer and reporting precision. The 2018 precision change for temperatures raises the same question for precipitation.
  - *Requirement:* Confirm the threshold. Check the value lattice of the 2018 daily precipitation. Stratify by switch status, as both entries propose.
- **H25/H33-c — Nit.** There are two specifications of one family; pick one.

### H31 (round the hottest-day forecast to whole °F)
- **Strengths:** I re-derived the a/12 net gain and the 4.1/σ² skill figures, and they check out. The half-integer placebo predicts the opposite sign, there is a single arm, and the size is predicted in advance. The confirmatory label is acceptable for the backtest claim.
- **H31-a — Blocker — Design Fit (does not transfer).**
  - *Risk:*
    - Every backtest target year up to 2017 is integer-valued, so the backtest gain is close to guaranteed by arithmetic and says little about the decision.
    - The decision depends entirely on the precision of the 2019–2025 targets. The EDA note that about 36k values in 2018 carry one decimal is direct evidence that the integer lattice broke in 2018. If those are tmax and tmin values, that is roughly a quarter of the network-year.
    - Against a continuous target, rounding adds about a/12 to expected absolute error: the same size as the backtest gain, with the opposite sign.
    - The proposed check on scored 2018 rows has too little power to show the sign flip. The per-row difference has SD ≈ 0.29 °F against an effect of about 0.011 °F, so about 210 rows give SE ≈ 0.02 °F (z ≈ 0.5). By comparison, about 4,400 backtest rows give z ≈ 2.5.
  - *Requirement:* Make the 2018 lattice check the go/no-go gate, defined now and run before the backtest. Tabulate the share of daily tmax and annual `Max Tmax` values on whole °F in 2018, by city and by month.
    - If decimals appear in every city from some date onward, drop H31.
    - If decimals are confined to certain cities, round only the cities that stayed on whole °F.
    - Record that the decision used only data through 2018 (R2-X6).
- **H31-b — Nit.**
  - The refutation rule joins its two conditions with "and". Add a band of 0.5 to 2 times the predicted gain.
  - The derivation assumes uniform fractional parts and uses the density at the median. Off-centre forecasts make the predicted gain slightly too large.

### H34 (data-chosen break in the city-minus-region series)
- **H34-a — Major — Design Fit (leakage and selection).** Fitting λ absorbs the bias of picking the largest |t| only if the scan is re-run inside every pseudo-origin and the regional reference c_t uses 30-year means ending at p. State both.
- **H34-b — Major — Alternative Explanation.**
  - *Risk:* A max-|t| split also picks up gradual drifts. The random-split placebo controls for selection, not for step versus drift.
  - *Requirement:* Add an arm with a linear drift fitted to the difference series. Define a tolerance and a permutation null for "breaks fall on documented changes more often than chance".
- **H34-c — Nit.** It has the highest cost and a gain close to E1's, so defer it under R2-X7.

---

**What the concepts brief must include (summary)**
- Every Round 2 result labelled exploratory, plus a declared replication set before 1955 with a city count.
- The full pseudo-origin and leakage specification, with an invariance test.
- A gatekeeping plan with Holm control, an adoption rule fixed in advance, and a single composite run.
- Each refinement scored against its nested parent, with the coefficient contrast as the mechanism endpoint.
- Per-fold and per-origin effects and coefficients reported next to the bootstrap, plus a cluster-bootstrap sensitivity check.
- The H31 lattice gate in place before H31's backtest is used.
- E3 and E4 kept out of the submission.
- A short-list run order that fits the remaining hours before the 2026-11-10 23:59 ET deadline.

## Round 3

### Reviewer status

| Critic | Mode | Status | Blocker | Major | Nit |
| :----- | :--- | :----- | :------ | :---- | :-- |
| egm-novelty | BRAINSTORM | completed | 0 | 6 | 12 |
| egm-methodologist | BRAINSTORM | completed | 1 | 20 | 14 |
| egm-citation-auditor | REVIEW | not run (the human asked to skip auditor verification) | — | — | — |

This round is **incomplete**: egm-citation-auditor did not run.

### Finding IDs

- **egm-novelty:** `egm-novelty-r3-<label>`.
  - Labels: X1, X2, E2-a, E2-b, H23/H32-a, H23/H36-b, H23/H27-c, H36-a, H37-a, H37-b, H26-a, H27-a, H27-b, O-1, O-2, O-3, O-4, O-5.
  - Majors: X1, O-1, O-2, O-3, H37-a, H37-b.
- **egm-methodologist:** `egm-methodologist-r3-<label>`.
  - Labels: X1–X5, H32-a…e, H35-a…c, H36-a…e, H37-a…d, E2-a…b, H23-a…c, H26-a…c, H27-a…e.
  - Blocker: H32-a.

### egm-novelty report (verbatim)

Novelty review of Round 3 (Mode: BRAINSTORM)

Target: the "## Round 3" section of `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md` (lines 1257–1862). Refiner B wrote H32, H35, H36 and H37. Refiner A wrote E2, H23, H26 and H27. I used earlier rounds only to check overlaps.

## Summary

**No Blockers.** No saved source already reports the contribution of any Round 3 hypothesis.

**The folder still cannot back a novelty claim for any of the eight.** The literature folder is the same 45-source search dated 2026-11-09. None of the searches named in the Thin Spots of rounds 1, 2 and 3 has been run since.

**The main problems are inside the team's own record:**
- H23 (revised) is H32 (revised) plus H36. The two refiners wrote different refutation rules for what is the same test.
- H26 and H37 are one mechanism written in two forms. Refiner A dropped H37's two-block form by name in this round.
- H27 is a gate for H35 and H37, and neither B hypothesis names it.
- H37 misdescribes its closest saved source and leaves out the team's closest prior work.

## Cross-cutting findings

**R3N-X1. Major. Applies to E2, H23, H26, H27, H32, H35, H36, H37.** Thin folder; any novelty claim exceeds the search.

- **Prior work.**
  - INDEX shows one search run (2026-11-09, 45 log rows). Nothing has been added since round 1.
  - The searches that bear on Round 3 kept nothing:
    - 11h, CDD sensitivity (42,084 hits);
    - 11i, nonstationary GEV for annual maxima;
    - 11k, "statistical benchmark decadal forecast surface temperature damped persistence" (448 hits);
    - 18b, empirical-Bayes shrinkage of station trends;
    - 18c, annual maximum Tmax trends at U.S. stations.
  - No query at all covers Tmin/Tmax asymmetry, measurement-error correction, OCN or damped-persistence skill by lead, r-largest order statistics, 1930s or 1950s station heat, or the timing of station moves.
  - AMS journals returned 403 (J. Climate, JAMC and BAMS, where the OCN and Tmin/Tmax literature sits). So huang1996longlead, both wilks2013 papers and arguez2011definition are abstract-only or metadata-only.
  - The key notes for H26/H37 (huang1996longlead, gardner1985forecasting) and for the reliability benchmark (efron1975data) are abstracts.
  - All notes are unaudited.
  - H26, H27, H32 and H35 say they answer egm-novelty-r2 X-2, but they only restate that novelty is unverified. No search was run.
- **Searches still missing:**
  - **E2:** damped-anomaly or damped-persistence forecasts at stations; James–Stein or empirical-Bayes shrinkage of station normals or anomalies toward a regional or national mean; how CPC estimates its OCN damping factor.
  - **H23 / H32:** asymmetric Tmax/Tmin trends and diurnal temperature range at U.S. stations; siting and instrument effects by component (HO-83, MMTS, ASOS); persistence of station Tmin versus Tmax anomalies; errors-in-variables (attenuation) correction for climate predictors.
  - **H36 and H23's CDD arm:** observed city CDD sensitivity to Tmin versus Tmax; degree days computed from the mean and variance of daily temperature.
  - **H35:** r-largest order statistics for temperature extremes; trends in upper-order daily-Tmax indices at U.S. stations.
  - **H26 / H37:** OCN skill by lead; damped persistence by lead for annual station temperature; lead-dependent damping in statistical decadal benchmarks (re-run 11k with other terms and with Semantic Scholar, which was not used).
  - **H27:** Dust Bowl and 1950s drought heat in station annual maxima; mid-century moves of first-order stations to airports.
- **Recommendation.** This does not block running any test for the submission. It does block calling any of these "new". Run the searches above and use author copies to get around the AMS block.

**R3N-X2. Nit. H32, H35, H36, H37.** Refiner B says it did not re-read the notes. I checked every key and quote number B cites against the notes: hausfather q1, arguez q3–q4, menne q3, efron q1, mckinnon q1, katzndblock q4, vandendool q3, huang q3 and gardner. All match. The one exception is H37's description of vandendool (R3N-H37-a).

## Per hypothesis

### E2 (refiner A, revised, adopted)

**Closest saved work:**
- vandendool2011readme q3: "the amplitude of the operational OCN is reduced by a factor that relates to the a-priori skill so as to minimize RMS error". By q1, the anomaly being damped is "the last 10 (T), 15(P) years averaged minus a 30 year climatology".
- efron1975data q2: Stein's estimator "reviewed briefly in an empirical Bayes context" (abstract only).
- wilks2013performance q3: on USHCN station data, "The best single method overall was the most recent 15-yr average".

**Remaining gap.** E2 damps only the cross-city-demeaned part and keeps the national part and the pooled trend at full weight. It uses one pooled λ per metric, fitted at in-fold pseudo-origins, on annual station targets scored by MAE. The record states this concretely.

**Findings:**
- **R3N-E2-a. Nit.** The contrast "fits λ by least squares at pseudo-origins" against vandendool's "a-priori skill" factor is thinner than written. The note says that factor is chosen "so as to minimize RMS error", which is what a least-squares coefficient on past forecasts does. The differences that hold up are the city/national split and pooling across cities. Lead with those.
- **R3N-E2-b. Nit (carried from E2-b).** The closest team arm is H11's own discriminating experiment (line 365: "Compare regional against national pooling targets"). Whether that arm ran is still unresolved. If it ran, E2 differs from it only in how λ is fitted. Settle this from the H11 trial record, which was not supplied to me.

### H23 (refiner A, revised) and H32 (refiner B, revised)

**Closest saved work (shared by both):**
- arguez2009improving q3–q4: the window–trend correlation is "-0.78" for January Tmin and "a more modest -0.35" for July Tmax. Its Not Covered line says: "Any out-of-sample skill comparison". Season and component are mixed together here, as H32 notes.
- hausfather2013quantifying q1: urbanization accounts for "14% to 21% of the rise in unadjusted minimum temperatures since 1895". That is a share of a trend, not 7-year persistence, and the note does not cover airport stations or forecasting.
- efron1975data, as the shrinkage benchmark (see the finding below).

**Remaining gap.** Both test a reliability-corrected, out-of-sample gap in 7-year persistence between the city parts of Tmin and Tmax. H23 also uses the contrast scaled by k_i as a CDD predictor. The folder has nothing on either.

**Findings:**
- **R3N-H23/H32-a. Nit.** The "reliability-implied coefficient", 1 − noise variance / total variance, is the Efron–Morris empirical-Bayes shrinkage weight. Name efron1975data as the closest saved method for the endpoint; both list it only as an inspiration. Then state the test as "fitted predictive weight against the noise-only EB weight". Round 2 H32 called this "Efron–Morris style", and the revision dropped the phrase.
- **R3N-H23/H36-b. Nit.** The seasonal rival (H23 rival b, H36 rival a) has a saved source that neither cites: morris1999impact q2, "The concentration of the warming trend during the winter season…". Cite it.
- **R3N-H23/H27-c. Nit.** mueller2012hot is cited for the "Tmax-side regime" (H23) and for the 1950s heat (H27). The note is abstract-only, its target is "the number of hot days" in the hottest month, and its Not Covered line lists "Annual maximum temperature magnitude; multi-year forecasting". Label it as motivation only.

### H36 (refiner B, new)

**Closest saved work:**
- petri2015impacts q3: CDD uses the "standard US base temperature" of 65 °F. q4: CDD ranges from 163 to 4,608 across cities. Its Not Covered line: "CDD sensitivity per degree derived from observations; forecasting methods".
- eia2025shortterm q2: "a one-variable 30-year trend line" on state CDD. This is the only saved method for forecasting CDD.
- INDEX Gaps: "No observational study of CDD trends or of CDD sensitivity to warming at city level was retrieved."

**Remaining gap.** The same as H23's CDD arm (see O-1).

**Findings:**
- **R3N-H36-a. Nit (also concerns H26).** H36 says it is "the only kept hypothesis that can enter the submission under the fixed adoption rule" (line 1404). That is not so: H26 is also nested in the adopted E2, and H23's CDD arm is the same test as H36.

### H35 (refiner B, revised)

**Closest saved work:**
- mckinnon2024pace q1: "the hottest summer days have warmed at the same pace as the median globally… from 1959 to 2023". This is at large scale, with no station forecast, and its data run past 2018.
- katzndblock q4: "μ(t) = μ0 + μ1 t…", a trend fitted on the block maxima themselves.
- vose2017temperature q5: "only a very slight increase in the warmest daily temperature of the year (amidst large interannual variability)".

**Remaining gap.** H35 uses the mean of each year's 10 hottest days as a less noisy predictor of the city anomaly in the annual maximum, judged by out-of-sample correlation. The folder has no source on order statistics. This core mechanism carries the highest risk of having already been done (see Leads to Fetch). I base no finding on that recollection.

**Findings:** see O-3 and O-4.

### H37 (refiner B, new)

**Closest saved work:**
- vandendool2011readme q1 and q3.
- huang1996longlead q3: "Forecasts at leads beyond one year (skipping a year) are also reasonably skillful" (abstract only).
- gardner1985forecasting q2: damping "improves forecast accuracy, particularly at long leadtimes" (business series, abstract only).

**Remaining gap.** Lead-group damping of the hottest-day city anomaly. The mechanism is the same as H26's.

**Findings:**
- **R3N-H37-a. Major. Difference unsupported by the note.** Line 1438 says "vandendool2011readme damps by skill, not by lead, within annual targets."
  - The note says OCN is computed "for each of 12 seasons" over 102 climate divisions, and its Not Covered line lists "annual targets". So "within annual targets" is contradicted by the note.
  - The note does not say whether the skill-based factor varies with lead, so "not by lead" is unsupported.
  - If CPC's a-priori skill is lead-specific, then damping by skill is damping by lead, and H37's mechanism (and H26's) would be standard operational practice.
  - Both refiners list van den Dool (2007) on "OCN damping by lead" as a lead, which shows the risk.
  - **Recommendation:** rewrite the sentence as "the saved note does not say whether the factor varies with lead", and fetch the book before making any claim.
- **R3N-H37-b. Major. Closest team work not named.** H37 names only E1 and H16. The closer team record is:
  - U1, which "learns horizon-dependent trend damping and window weights" (line 17) and lost in years 4–7;
  - three earlier drops of lead-dependent damping as duplicates of U1: Round 1 A, line 284; Round 1 B, line 499 ("this is what U1 and U2 already test"); Round 2 A, line 944;
  - refiner A's drop, this round, of exactly H37's form (line 1824: "A two-block lead λ (years 1–3 and 4–7): a more arbitrary alternative to H26's linear form").

  **Recommendation:** cite these and say why a single-mechanism nested test is different, as H26 does.

### H26 (refiner A, new)

**Closest saved work:**
- ho2013statistical q1: a trend regression plus an AR1 residual, whose forecast weight fades with lead. H26's λ_h = (Var θ + ρ^h·Var η)/Var A is that structure with a persistent city offset added.
- krueger2011simple q3: "internal variability… described by an autoregressive model".
- vandendool2011readme q3 and huang1996longlead q3.

**Remaining gap.** One pooled linear lead slope on E2's city-part coefficient. The record distinguishes it from ho2013 concretely and names U1, H16 and the Round 2 drop.

**Findings:**
- **R3N-H26-a. Nit.** vandendool q3 appears only under Inspirations. H26 does not say how its lead-dependent coefficient differs from damping by skill. This is the same open question as R3N-H37-a.

### H27 (refiner A, new)

**Closest saved work:**
- vose2017temperature q2: "The Dust Bowl era of the 1930s remains the peak period for extreme heat". q4: the decreases are "particularly in the Great Plains" and "mainly tied to the unprecedented summer heat of the 1930s".
- mascioli2017timing q2: "Long-term summer cooling in the north central U.S. beginning in the 1930s reflects the recovery from the anomalously warm 'Dust Bowl'".
- easterling2017precipitation q3: droughts "in the 1930s and 1950s".

**Remaining gap.** H27 predicts that where a past regime falls inside the reference window sets the sign of a damped-anomaly forecaster's skill, and it makes a sign prediction on origins not yet run. The record states this concretely. The nearest saved statement, livezey2007estimation q3, is about trends, not regimes.

**Findings:**
- **R3N-H27-a. Nit.** No saved source calls the 1950s a hottest-day regime: vose q2/q4 and mascioli q2 name only the 1930s. The 1950s link is the refiner's own inference from drought (easterling q3) plus mueller (see R3N-H23/H27-c). Say so; the hedge "less clearly 1948" is right.
- **R3N-H27-b. Nit.** Base the pre-fixed list of "central-U.S." regions on vose q4 ("Great Plains") and mascioli q2 ("north central U.S."), and record that basis.

## Overlaps between the refiners

**O-1. Major. H23, H32, H36.** H23 (revised) is the same as H32 (revised) plus H36.
- **The CDD test is identical.**
  - Same regressor: H23's D_i = k_i(p)·(tmin_half − tmax_half) and H36's k_i,p·(A_tmin − A_tmax)/2.
  - Same parent (E2's CDD arm), same endpoint (CDD skill against E2, all years, official folds), same coefficient prediction (above 0 at all three cut-offs).
- **The rules differ:**
  - H23 is refuted if β̂_d ≤ 0 at 2 or more of 3 cut-offs, and adoption requires a Holm-adjusted interval.
  - H36 is refuted if γ̂ ≤ 0 at any cut-off, or if the difference is ≤ 0 on the official folds or on the replication set, with no Holm step.
  - So one run with the coefficient positive at 2 of 3 cut-offs passes H23 and refutes H36.
- **The mechanism endpoint is one quantity with two estimators.**
  - H32's G uses a separate correction for each component, built from the raw 30-year variance, at all pseudo-origins. It must hold at all 3 cut-offs, plus a pooled interval.
  - H23's ρ = (Σ_A − V)⁻¹Σ_A·Λ uses series with the national part removed and a linear trend taken out, at balanced origins p ≤ c−7, and must hold at 2 of 3 cut-offs.
  - λ_Tmin and λ_Tmax come from one joint fit on two correlated halves, so only the joint (matrix) correction matches that fit.
- **Multiplicity and independence.**
  - Refiner A's Holm m = 4 is right only if H36 is counted as the same test.
  - H36's "sign predicted… from an independent metric's result" overstates independence: it uses the same A_tmin and A_tmax regressors. Refiner A says a pass on both must not count as independent support.
- **Recommendation:** use one family ID, one specification and one refutation rule fixed before the run. Make one estimator primary and the other a sensitivity check, and count the test once.

**O-2. Major. H26, H37.** One mechanism ("persistence decays with lead, so one pooled λ is a compromise") in two forms on two parents.
- H26 is linear and sits on E2, so it can be adopted. H37 is two-block and sits on E1, which failed its gate.
- Each corrects the same fitting artefact differently: H26 re-fits on balanced origins p ≤ c−7; H37 weights each lead equally.
- Both read their motivating split by lead off the official folds.
- **Recommendation:** treat them as one family. Choose the shape from H26's free-λ_h diagnostic (its experiment 3), run for hottest day too. Use one artefact control, and give H37 an explicit new root.

**O-3. Major. H27, H35, H37.** H27 says it "decides whether hottest-day city-anomaly methods (H34, H35) deserve time". H35 (rival c) and H37 (rival a) mention era dependence only in general terms and do not name H27.
- H37's experiment for rival (a) reads λ̂ at 1934/1941/1948. Running any E1-family model there first would cancel H27's confirmatory status ("provided E1 has not yet been run on those origins").
- Under H27, the top-10-day mean carries the 1930s heat at least as strongly as the annual maximum. So H35's correlation gap at early or replication origins could not tell noise reduction from a regime artefact.
- **Recommendation:** run H27 first, and add it as a named rival in H35 and H37.

**O-4. Nit. H35 and the dropped H24.** H35 says "reconcile the specifications" with H24, but refiner A dropped H24 this round, so there is nothing to reconcile. H24 had an `Avg Tmin` negative control and a variance-channel arm that H35 lacks. Decide explicitly whether to inherit the control.

**O-5. Nit. H23, H27, H32, H37.** The refiners define "station switch" differently:
- refiner A uses per-year `Station Changes` in years ≤ p (line 1555), over c−14..c for H27;
- H32 uses `Station Segment` changes over 30 years, and its own record leaves the timing of that numbering unchecked (line 1288);
- H37 says only "segment change… (in-fold definition)".

Use one indicator across all four.

## Findings by severity

- **Major:** X1, O-1, O-2, O-3, H37-a, H37-b.
- **Nit:** X2, E2-a, E2-b, H23/H32-a, H23/H36-b, H23/H27-c, H36-a, H26-a, H27-a, H27-b, O-4, O-5.
- **Blocker:** none.

## Leads to Fetch

All are unverified and none is in the folder. Several come from the refiners' own lists or from memory.

- van den Dool (2007), *Empirical Methods in Short-Term Climate Prediction*: OCN damping by lead (H26, H37).
- Full text of Huang, van den Dool & Barnston (1996): skill by lead (H26, H37).
- Wilks, *Statistical Methods in the Atmospheric Sciences*: damped persistence (H26).
- Karl et al. (1993), BAMS: asymmetric Tmax/Tmin trends (H23, H32, H36).
- Menne, Williams & Palecki (2010), JGR: station exposure effects by component (H23, H32).
- The HO-83 Tmax bias literature, for example Gall et al. (1992), J. Climate, and Quayle et al. (1991), BAMS (H32 rival b).
- Fuller (1987), *Measurement Error Models* (H23, H32).
- Thom (1954), Monthly Weather Review: degree days from mean temperature and variability (H36). From memory.
- Coles (2001), *An Introduction to Statistical Modeling of Extreme Values*, ch. 3, and Smith (1986), J. Hydrology: r-largest order statistics (H35). From memory; this is the main "already done" risk for H35.
- Cheng et al. (2014), Climatic Change: already in the INDEX leads (H35, H37).
- Schubert et al. (2004), Science, and Cook, Miller & Seager (2009), PNAS: Dust Bowl drought and land feedback (H27).
- Meehl et al. (2012): already in the INDEX leads (H27).
- Studies of mid-century moves of first-order stations to airports (H27 rival a).
- Full text of Wilks & Livezey (2013), and Arguez et al. (2012) on NOAA normals (E2).

## Files read

- `/Users/atabaresa/repos-new/egm/egm-research/agents/novelty_critic.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md` (all 1862 lines)
- `/Users/atabaresa/repos-new/proto-star-challenge/research_background.md`
- `/Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md`
- All 45 notes in `/Users/atabaresa/repos-new/proto-star-challenge/literature/notes/`

I did not read `hypotheses_review.md`, the trial notes, configs or code, because they were not supplied. So I could not check the round-2 finding IDs the refiners say they answer. No files were written.

### egm-methodologist report (verbatim)

The full report as returned by the critic is filed below.

METHODOLOGIST REVIEW: Round 3 hypotheses (Mode: BRAINSTORM)

Study type: a statistical forecasting method comparison on rolling-origin historical backtests (observational station time series, 210 cities). This is a benchmark-style study.
Claim type: all Round 3 claims are labelled exploratory, except H27. H27 claims confirmatory status for two sign predictions on the 1934/1941/1948 replication origins.

Totals: 1 Blocker, 20 Major, 14 Nit.

SCOPE AND LIMITS
- Files read in full or in the relevant parts:
  - /Users/atabaresa/repos-new/egm/egm-research/agents/methodologist.md
  - /Users/atabaresa/repos-new/egm/egm-research/resources/document_standards/ml-empirical-research-standard.md
  - /Users/atabaresa/repos-new/proto-star-challenge/hypotheses.md: Round 3, lines 1257–1862; Round 2 Final table and E1–E4 statements as context.
  - /Users/atabaresa/repos-new/proto-star-challenge/research_background.md
  - /Users/atabaresa/repos-new/proto-star-challenge/src/proto_star/anomaly.py
  - /Users/atabaresa/repos-new/proto-star-challenge/literature/INDEX.md. I did not open the individual notes.
- Not read, because they were not supplied:
  - hypotheses_review.md (the texts of the R2 findings);
  - climate.py (`annual_to_long`);
  - trend.py (`cdd_per_degree` and the candidate);
  - the configs;
  - tests/test_anomaly.py;
  - the experiment logs.
- Findings that depend on these files are marked "unverified". The review of the supplied material is complete.

CODE CHECK: PSEUDO-ORIGIN CONSTRUCTION IN anomaly.py
What I verified inside this file:
- Pseudo-origins are p = c−30 … c−1 (line 219).
- The base forecaster is refit on `train.loc[Year <= p]` (line 145).
- Targets are p+1 … min(p+7, c). Their truth comes from `annual_to_long(train, cutoff_year=c)` (lines 144, 188).
- `_anomalies` filters to year ≤ p (line 62):
  - m30 covers years p−29 … p (lines 63–67);
  - the recent window is the last `window` rows ≤ p (line 68);
  - the national mean is taken over the cities present at p (line 70).
- Diurnal rows are screened row by row by their own missing-day column and Year ≤ c (lines 124–126), then filtered to ≤ p in `parts`.
- CDD-per-degree is refit on history ≤ p (lines 105–109).
- The final forecast uses only rows ≤ c (lines 255–256).

Inside this file, I found no path from rows after p into the pseudo-origin inputs, and no path from rows after c into the forecast. The remaining risks are in code this file calls (R3-X1). There are also two code defects that break nesting or confound the fit (R3-H36-a, R3-H36-b).

====================================================================
ROUND-LEVEL FINDINGS
====================================================================

R3-X1 [all: E2, H23, H26, H27, H32, H36, H37] Major (Blocker if confirmed). Dimension: Design Fit (leakage, unverified paths).
- Risk: anomaly.py is clean, but three inputs it depends on are unverified.
  (i) `annual_to_long`: if any screening in it uses statistics across years, rows in (p, c] can decide which cities and rows enter the pseudo-origin fits.
  (ii) The base forecaster gets columns that were precomputed in annual_master.parquet over the full 1851–2018 record: `valid_*`, `Station Segment`, `years_since_switch`, the daily-quality flag counts, and `region`. If any of these is not computed from its own row only, rows ≤ 1980 carry information from 1981–2018 into the official folds.
  (iii) The invariance test both refiners rely on (refiner A, line 1554) perturbs rows after c in the table that is already built. Precomputed columns are not recomputed, so the test cannot detect leakage through them.
- If (ii) holds for any column used by the base or by `annual_to_long`, every fold result is affected, including E2's adoption. That would be a Blocker.
- Requirement:
  1. List every column read by the base forecaster, `annual_to_long` and `cdd_per_degree`. For each, state whether it is computed from its own row only.
  2. Rebuild any column that is not, per cut-off, from raw rows ≤ c.
  3. Add a pseudo-origin invariance test: for a sample of p, perturb all raw rows in (p, c] except the target values, and assert that the regressors and base forecasts at p are identical.
  4. Add a cut-off test: rebuild the master table from raw rows ≤ c and assert identical forecasts.
- Source: standard §2 Splits and Leakage (kapoor2022leakage).

R3-X2 [H32, H37] Major. Dimension: Design Fit (leakage).
- Risk: the two refiners define switches differently.
  - H32 rival (c) uses changes in `Station Segment` (line 1323).
  - H37 rival (b) uses "segment change … (in-fold definition)" (line 1434).
  - Refiner A fixes switch indicators from per-year `Station Changes` in years ≤ p, never from the `Station Segment` numbering (line 1555).
  - Refiner B itself lists the chronology of `Station Segment` as unchecked (lines 1288, 1485).
- Requirement: one switch rule for the whole round. Use refiner A's rule for H32, H37 and H27.

R3-X3 [round; H23, H36, H32, H26, H37] Major. Dimension: Testability (multiplicity and flexible analysis).
- Risk: there is no single registry of tests, and the same tests appear twice under different rules.
  1. H23's CDD test and H36 are the same test. They share the parent (E2), the regressor (`contrast` on CDD rows, equal to k_i(p)·(A_tmin − A_tmax)/2, anomaly.py lines 99–113) and the endpoint (CDD skill against E2).
     - H23 requires a Holm-adjusted 98.75% interval and is refuted if β̂_d ≤ 0 at 2 of 3 cut-offs.
     - H36 requires only a positive point estimate and is refuted if γ̂ ≤ 0 at any cut-off or the difference is ≤ 0 on replication.
  2. H23's mechanism endpoint and H32's G answer the same question with different estimators and thresholds.
     - H23: multivariate ρ, block bootstrap, interval excluding 0 at 2 or more of 3 cut-offs.
     - H32: univariate G, pooled interval, G > 0 at all 3.
     - The fitted gap (≥ 0.43) is already known, so the analyst can pick whichever version passes.
  3. Lead dependence is tested twice in different forms on different parents: H26 is linear on E2, H37 is two-block on E1. Refiner A dropped the two-block form as "more arbitrary" (line 1824).
  4. Refiner A's Holm family (m = 4: H21, H23-temperature, H23-CDD, H26) leaves out H36 and states only the first Holm step. Refiner B applies no adjustment. The E1 branch (H27, H35, H37) has no plan.
- Requirement:
  - Before any run, write one registry table: one ID, one primary endpoint and one threshold per test.
  - Merge H36 into H23-CDD.
  - Use one mechanism estimator: H23's form (see R3-H32-a).
  - Pick one lead parametrization, or declare both exploratory.
  - Apply Holm only over the tests that can lead to adoption, with the full step-down: 97.5% then 95% if m = 2; 98.75%, 98.33%, 97.5%, 95% if m = 4. Use bootstrap p-values.
  - Label every other readout exploratory.
- Source: standard §1 Claim Type (herrmann2024position); §4 Named Tests (dror2018hitchhikers).

R3-X4 [round; E2 branch and H37] Major. Dimension: Testability (holdout reuse).
- Risk: the replication origins and the 7 cut-offs have already been read for E2, H21 and H23. They will be read again for H23/H36, H26, H37 and H27.
  - The adoption rule's "same sign on replication" passes about 50% of the time when a nested refinement has no effect.
  - "Same coefficient sign at all three cut-offs" is weaker than it looks, because the in-fold windows overlap: 1980 and 1995 share pseudo-origins 1965–1979, and 1995 and 2011 share 1981–1994.
  - H26 and H37 are motivated by block patterns on the official folds, so their official-fold results are not independent tests (R2-X1).
- Requirement:
  - Use the existing bootstrap to estimate the false-adoption rate of the combined rule when a refinement has no effect.
  - Report the replication estimate with its interval, not only its sign.
  - Treat the official-fold results of H26 and H37 as descriptive.

R3-X5 [H32, H35, H36, H37] Nit. Dimension: Testability.
- Risk: several refutation rules count "interval includes 0", or a point estimate ≤ 0 on the noisy replication set, as refutation (lines 1315, 1353, 1389, 1426). At the stated power, true small effects would often be recorded as refuted.
- Requirement: give each endpoint three outcomes:
  - supported;
  - refuted: an equivalence bound (interval inside ±δ), or a reversed sign with an interval excluding 0;
  - inconclusive.

====================================================================
REFINER B
====================================================================

H32: the persistence gap is real, beyond reliability
- Testability: falsifiable as written (G ≤ 0 refutes it).
- Design fit: an analysis script on the existing regressors, about 45 minutes, master table only.
- Biggest threat: the endpoint cannot separate the mechanism from reliability.

R3-H32-a [H32] BLOCKER. Dimension: Design Fit / Alternative Explanation.
- Risk: the two sides of G are not comparable.
  - λ_Tmin and λ_Tmax come from one joint regression on two correlated halves (split="diurnal": lines 198–199, one lstsq at line 239).
  - λ_rel is a reliability ratio computed for each component on its own (line 1311).
  - In a joint regression with noisy, correlated regressors, the more reliable regressor gains more weight than the separate reliability ratios imply.
- Worked illustration (made-up values, not estimates):
  - Tmax and Tmin city signals have unit variance and correlation 0.8, and persist equally.
  - Noise variance is 1 for Tmax and 0.25 for Tmin.
  - The joint coefficients are 0.44 and 1.16, a gap of 0.73.
  - The separate reliabilities are 0.50 and 0.80, a gap of 0.30.
  - So G = +0.43 under reliability alone. G is 0 under reliability only when the two true signals are uncorrelated.
- Consequence: G > 0 is expected under rival (a), so the primary endpoint cannot answer the question.
- Requirement:
  - Replace λ_rel with H23's multivariate correction, ρ = (Σ_A − V)⁻¹ Σ_A Λ.
  - Make V the full 2×2 noise covariance, including the Tmax–Tmin noise covariance (both halves see the same weather).
  - Calibrate it by simulation: generate reliability-only data with the observed Σ_A and V, run the same pipeline (national removal, candidate base, clip), and confirm the gap is about 0.
  - Merge this with H23's mechanism endpoint.

R3-H32-b [H32] Major. Dimension: Testability (flexible analysis).
- Risk: only λ_rel is new, and it is under-specified.
  - It does not say whether s_i² is detrended or has the national part removed.
  - It does not say how the per-pseudo-origin λ_rel values are combined into one value per cut-off.
  - s²/30 assumes independent years. Positive lag-1 autocorrelation in Tmax would understate its noise and push G upward.
  - The fitted gap is already known, so these open choices are forking paths.
- Requirement: fix the full estimator first. H23's template (lines 1642–1644): national-removed, linearly detrended, AR(1) inflation as sensitivity. The conclusion must hold under both the independent-years and the AR(1) versions.

R3-H32-c [H32] Major. Dimension: Design Fit (statistical conclusion).
- Risk: the bootstrap has too few independent blocks.
  - 7-year pseudo-origin blocks give about 4 blocks per cut-off.
  - The pooled G mixes overlapping cut-offs.
  - Adjacent pseudo-origins share 14 of 15 anomaly years and 6 of 7 target years, so each cut-off has only one or two independent time units in effect.
  - The interval will be too narrow.
- Requirement:
  - Make the primary interval a region-cluster (or spatial-block) bootstrap across cities within each cut-off.
  - Do not pool cut-offs whose windows overlap.
  - Use the 10 + 3 origins as a descriptive consistency check.

R3-H32-d [H32] Nit. Dimension: Design Fit.
- Risk: the rival (c) arm interacts A_city × S (line 1323), but its prediction concerns the D coefficient in cities without a switch.
- Requirement: interact D × S, keeping A × S as a control, or fit separately by switch status.

R3-H32-e [H32] Nit.
- Risk:
  - Two specifications are both called "fixed": split="diurnal" as run, and the one-degree-of-freedom contrast form. In code they are not exactly equivalent: the screening and national means differ.
  - The secondary endpoint repeats the round-2 result (+0.10 [−0.04, +0.25]); it adds no evidence.
- Requirement: name one form, and drop the secondary endpoint or label it a repeat.

H35: T10 anomaly beats the annual-maximum anomaly
- Testability: falsifiable (the Δr interval and its sign across cut-offs).
- Design fit: a daily T10 build (about 1.5 hours) plus a correlation analysis. It is mechanism-only: its parent E1 failed, so it cannot be adopted.
- Biggest threat: spatially correlated city errors.

R3-H35-a [H35] Major. Dimension: Design Fit (statistical conclusion).
- Risk:
  - A city-cluster bootstrap treats cities as independent. F has the national part removed, but nearby cities still share heat waves, so the intervals will be too narrow.
  - The 0.05 threshold has no stated expected Δr or minimum detectable Δr. My rough arithmetic: with r ≈ 0.4, corr(A_T10, A_max) ≈ 0.8 and 210 cities × 4 origins, the standard error of Δr is about 0.02–0.04 before spatial correlation. So 0.05 is near the detection limit.
- Requirement:
  - Use a region-cluster or spatial-block bootstrap.
  - State the expected Δr and the minimum detectable Δr.
  - Say whether r is pooled over the 4 pseudo-origins or averaged across them.

R3-H35-b [H35] Nit. Dimension: Alternative Explanation (interaction with H27).
- Risk: at C = 1980, pseudo-origins 1952–1973 have reference windows that contain the 1930s and 1950s heat. Under H27, r(A_max, F) there is driven by those regimes. T10, which captures multi-day heat, may carry the regimes more strongly than the single-day maximum, so the sign of Δr can flip for reasons unrelated to noise reduction.
- Requirement: report Δr separately for central and non-central cities, using H27's region list. Do not let the 1980 sign alone refute.

R3-H35-c [H35] Nit.
- Risk:
  - "Reconcile with H24" is moot, since refiner A dropped H24.
  - "Refuted if the Δr interval includes 0" does not say at which cut-off.
- Requirement: state the cut-off.

H36: Tmin–Tmax contrast added to E2's CDD correction
- Testability: falsifiable (the sign of γ̂ and the paired difference).
- Design fit: one extra coefficient, already coded as `diurnal_contrast`; about 1 hour.
- Biggest threat: because the fit has no intercept, γ̂ can soak up the candidate's average CDD bias.
- The same test as H23's CDD arm. Findings R3-H36-a to -e apply to H23 as well.

R3-H36-a [H36, H23] Major. Dimension: Alternative Explanation (code).
- Risk: the fit is least squares with no intercept (lines 239–241), and only one of the two regressors averages to zero.
  - E2's regressor A_city averages zero across cities at each pseudo-origin, because the national part is removed (line 70). The candidate's average error therefore does not load on it.
  - D_cdd = k_i(p)·contrast (lines 111–113) does not average zero. The contrast does, but multiplying by k_i, which is large in hot cities, leaves a nonzero mean whenever contrast and CDD sensitivity are correlated across cities.
  - The candidate has a large average CDD bias in recent folds (E3: −36, −82, −87 at 2000, 2005, 2011). So γ̂ can come out positive (or negative) from that bias alone, with no night-time persistence.
  - At forecast time, the uncentred term also adds a uniform CDD shift. That is a disguised version of E3's national bias correction, which the round rejected for transfer risk.
- Requirement:
  - Centre D_cdd across cities at each pseudo-origin and at the cut-off before fitting.
  - Report mean(D_cdd) per pseudo-origin.
  - State the γ̂ sign prediction for the centred regressor.

R3-H36-b [H36, H23] Major. Dimension: Design Fit (code; nesting).
- Risk: the code does not set a missing D to 0, so the comparison with E2 is not nested.
  - At forecast time the shift is a sum over regressors (line 264), and `np.nan_to_num` turns NaN into 0 (lines 266–268).
  - If the contrast or k_i is missing for a city, the whole shift becomes 0, so that city also loses E2's β·A_cdd term.
  - At fit time those rows are dropped (line 238), so β is fitted on a different sample than in E2.
  - H23 specifies "a missing D_i is set to 0" (line 1618).
  - The difference against E2 therefore includes an unplanned change. The round-2 diurnal-split result was exposed to the same defect.
- Requirement:
  - Fill missing D with 0 in both the fit and the forecast.
  - Add a test that the arm with γ forced to 0 reproduces E2's forecasts exactly.
  - Report how many cities have a missing D at each cut-off.

R3-H36-c [H36, H23] Major. Dimension: Design Fit (detectability).
- Risk: the expected effect sits below the detection limit.
  - The expected effect is +0.1 to +0.3 pp of CDD skill.
  - The ±0.15 pp width quoted is the temperature nested width. CDD intervals are wider: E2 against the candidate had a half-width of 0.41 pp for CDD against 0.34 pp for temperature.
  - A better guess for the nested CDD standard error is about 0.09 pp.
  - Minimum detectable effect at 80% power: about 0.26 pp at 95%, and about 0.31 pp at the Holm 98.75% level.
  - For the 0.1–0.2 pp effect that the round-2 temperature result (+0.10 pp) suggests, power is about 20–60% unadjusted and 8–40% under Holm.
- Requirement:
  - State the minimum detectable effect.
  - Make the in-fold γ̂, with a region-cluster standard error, the primary mechanism readout, and keep the score difference as the adoption gate.
  - Do not record a null score difference as a refutation.

R3-H36-d [H36, H23] Major. Dimension: Alternative Explanation.
- Risk: rival (a) is not tested. It says annual Tmin anomalies are weighted toward winter, while CDD is a warm-season quantity.
  - The proposed split of cities by CDD predicts the same pattern under the mechanism and under rival (a) (line 1395).
  - A negative γ̂ would refute H36 even if the warm-season version of the mechanism holds.
- Requirement:
  - Add a warm-season (June–August or May–September) Tmin–Tmax contrast built from daily rows ≤ p, as in /Users/atabaresa/repos-new/proto-star-challenge/scripts/build_summer_means.py, and declare it exploratory.
  - State in advance that "annual γ̂ ≤ 0 with warm-season γ̂ > 0" favours the seasonal reading, not a refutation of persistence.

R3-H36-e [H36, H23] Nit.
- Risk:
  - k_i is computed with `PooledTrendSpec(level_years=[10], trend_window=40)` (lines 105–109), while the candidate uses level years [10, 15]. Neither refiner read trend.py.
  - With temperature included in `metrics`, `diurnal_contrast` also changes the temperature rows (lines 200–201), but H23 requires the temperature rows to stay as E2.
- Requirement:
  - Confirm that `cdd_per_degree` does not depend on `level_years` and that the window of 40 matches the candidate.
  - Run this arm with metrics=["cdd"].

H37: lead-group coefficients beat E1's single λ
- Testability: falsifiable, but weakly, because support is the sign of a point estimate.
- Design fit: `lead_split=3` is already in the code; about 45 minutes. It cannot be adopted, since its parent E1 failed.
- Biggest threat: the lead split was read off the same official folds it is tested on, and era dependence (H27) also explains it.

R3-H37-a [H37] Major. Dimension: Design Fit (nesting).
- Risk: the comparison with E1 also changes the clip.
  - H37 clips λ to [0, 1] (line 1417). The code default is (−1, 1) (line 172), and E1's clip has not been checked (line 1754).
  - If E1 used (−1, 1), the H37-against-E1 difference mixes the lead split with a clip change.
  - A floor at 0 sets a negative long-lead λ̂ to 0. That makes years 4–7 equal to the reference, so "years 4–7 ≥ −0.1 pp" (line 1425) is close to automatic and holds for any long-lead shrinkage, not only lead decay.
- Requirement:
  - Use E1's exact clip; treat a clip change as a separate ablation.
  - Replace the years 4–7 prediction with one that only lead decay makes, for example λ̂_4–7 > 0 and λ̂_4–7 < λ̂_1–3 in a refit on balanced pseudo-origins.

R3-H37-b [H37] Major. Dimension: Testability (double use of the official folds; weak criterion).
- Risk:
  - The mechanism is read off E1's official-fold split (+0.83 / −0.44 pp, line 1411), and the primary endpoint is the paired difference on the same folds. Support is a positive point estimate, with no interval.
  - If the long-lead loss is removed, the expected all-years gain is about (4/7) × 0.44 ≈ +0.25 pp. The nested hottest-day standard error is probably 0.2–0.3 pp.
  - A positive point estimate then occurs about 50% of the time with no effect and about 80% with the predicted effect. It carries little evidential weight.
- Requirement: make the replication origins and the 4 extra cut-offs the primary endpoint, with an interval. Keep the official folds descriptive.

R3-H37-c [H37, H27] Major. Dimension: Alternative Explanation / sequencing.
- Risk:
  - H37's rival (a), era rather than lead, is H27's mechanism.
  - H37's refutation rule needs E1 run at the replication origins (line 1426). Running H37 first computes E1 at 1934/1941/1948, which voids H27's confirmatory condition.
- Requirement:
  - Run and log H27 first, or blind H37's replication readout until H27 is logged.
  - Then analyse lead group × era jointly: λ̂ by lead group at all 13 origins, with a regime-window classification fixed in advance.

R3-H37-d [H37] Nit.
- Risk:
  - Neither lead group is fitted on the same balanced pseudo-origins (p ≤ c−7), as H26 does. That leaves a truncation-by-era confound.
  - The rival (c) refit with equal weight per lead changes weights by only about 10%. Unequal weighting biases a pooled λ only if λ varies with lead, so this refit cannot discriminate.
  - The 0.1 threshold has no stated standard error behind it.
- Requirement: fit both groups on p ≤ c−7, and state the expected standard error of λ̂_1–3 − λ̂_4–7 to justify the 0.1 threshold.

====================================================================
REFINER A
====================================================================

E2: damped city part of the temperature and CDD anomaly (adopted)
- Testability: tested and not refuted under its pre-stated rule.
- Design fit: two checks, about 30 minutes.
- Biggest threat: λ̂ drifts with era (0.60 → 0.84), so the official-fold gain overstates the 2019–2025 gain.

R3-E2-a [E2] Nit. Dimension: Testability (flexible analysis).
- Risk: check 1 (λ̂ at the 2018 cut-off) and check 2 (the cluster bootstrap) have no decision attached. Either could become a post-hoc reversal.
- Requirement: state now whether either check can change the submission. For example: "E2 is submitted whatever λ̂_2018 is. If λ̂_2018 falls outside the range seen at the backtest cut-offs, report it as extrapolation."

R3-E2-b [E2] Nit. Dimension: Design Fit (scope).
- Risk: λ̂ at 2018 is likely closest to the 2011 value, so the three-fold mean is not the best guide to transfer. The 10-origin λ̂ table only describes; the truth at those origins motivated E2.
- Requirement: report the 2011-fold gain alone next to the three-fold mean, as the estimate most relevant to transfer.

H23: Tmin carries persistence beyond reliability; CDD contrast on E2
- Testability: falsifiable (the sign of β̂_d and the corrected gap).
- Design fit: the CDD arm is already coded (`diurnal_contrast`, metrics=["cdd"]); the reliability readout takes about 45 minutes.
- Biggest threat: the same as H36, plus an ill-conditioned correction.

R3-H23-a [H23] Major.
- Risk: the CDD score test is the same test as H36, so R3-H36-a to -e apply as written: centring, nesting with a missing D, detection limit, the seasonal rival, and the k_i check.
- Requirement: merge the H23 and H36 records (R3-X3).

R3-H23-b [H23] Major. Dimension: Design Fit (statistical conclusion).
- Risk:
  - The form ρ = (Σ_A − V)⁻¹ Σ_A Λ is correct, but the city-part Tmax and Tmin anomalies are probably strongly correlated. Σ_A − V may be near-singular, or not positive definite in some resamples, and inverting it amplifies error.
  - With 24 balanced pseudo-origins there are 3–4 blocks of 7 per cut-off, too few for a valid interval (see R3-H32-c).
  - "Reliability wins if the corrected interval contains 0" (line 1632) treats imprecision as evidence for the rival.
- Requirement:
  - Report the condition number and positive-definiteness of Σ_A − V per cut-off and per resample.
  - Use a region-cluster bootstrap.
  - Add the reliability-only simulation null from R3-H32-a.
  - Set an equivalence bound for "reliability wins".

R3-H23-c [H23] Nit.
- Risk: the regressors are halves, so V must be computed on the half-series (a quarter of the full-series covariance). Unstated, this invites a factor-of-4 error.
- Requirement: state the half-series scale explicitly.

H26: city-part coefficient varies linearly with lead
- Testability: falsifiable (the sign of b̂ at 3 cut-offs, the balanced refit, the point estimate).
- Design fit: `lead_slope=True` is already coded; about 1 hour.
- Biggest threat: the predicted gain is below the Holm-adjusted detection limit, and the motivating pattern comes from the official folds.

R3-H26-a [H26] Major. Dimension: Design Fit (detectability).
- Risk: the predicted gain is too small to detect on the score endpoint.
  - The ±0.04 raw nested width (data item 3, line 1536) comes from temperature alone. H26 changes both temperature and CDD, so the raw-score standard error is about 0.03 if the two changes are independent and up to 0.04 if they move together.
  - Minimum detectable effect at 80% power under Holm's first step: about 3.3 × SE ≈ 0.10 raw (range 0.07–0.14). That is above most of the predicted +0.02 to +0.08.
  - The gain from fitting b also grows only with b². Rough scaling from E2's own gain (Δλ ≈ 0.35 bought +0.38 pp of temperature skill; the mean squared λ change here is 4b²) shows the size:
    - b = −0.05 per lead gives about 8% of E2's gain, about 0.01 raw from temperature;
    - +0.08 raw needs b near −0.1 per lead or steeper on both metrics.
  - This scaling assumes the loss is roughly quadratic in λ and that E2's λ̂ is near the optimum.
- Requirement:
  - Before scoring, fit b̂ in-fold (no test truth is needed) and compute the gain it implies.
  - If that gain is below the detection limit, declare in advance that the score endpoint is uninformative.
  - In that case make the coefficient readouts primary: b̂ < 0 at all three cut-offs, surviving the balanced refit, and the MSE-by-lead profile. Keep the score only as the adoption gate.

R3-H26-b [H26] Nit. Dimension: Design Fit (code against spec).
- Risk:
  - The spec bounds λ_h to [0, 1.5] (line 1673). The code clips β_0 and β_1 separately after an unconstrained joint fit (lines 242–243) and never clips λ_h.
  - Clipping one coefficient after a joint fit leaves the other at its unconstrained value.
- Requirement: implement the λ_h bound or remove it from the spec. If a bound binds, refit with that coefficient held fixed.

R3-H26-c [H26] Nit. Dimension: Testability.
- Risk: the block pattern behind H26 (data item 2) is official-fold truth, so the official-fold endpoint is not independent (R3-X4).
- Requirement: report the replication result with its interval; it carries the only independent weight.

H27: E1's early gain is a 1930s/1950s regime artefact; E1 loses at 1941
- Testability: falsifiable (the 1941 sign).
- Design fit: the existing E1 config at 3 cut-offs plus a per-city breakdown, about 50 minutes.
- Biggest threat: the confirmatory endpoint is also predicted by a mixed account, and confirmatory status is not yet earned.

R3-H27-a [H27] Major. Dimension: Testability (exploratory presented as confirmatory).
- Risk: the confirmatory claim is not properly pre-registered.
  1. There is no immutable record. hypotheses.md is untracked in git (session status "??"), so nothing timestamps the plan.
  2. The "E1 not yet run on those origins" condition rests on "the supplied log" only. It is not verified across all outputs. In particular: did the round-2 combined arm include E1's hottest-day correction, and was it run at the replication origins? Did any robustness-script run cover them?
  3. The analysis is not fixed:
     - E1's clip has not been read (line 1754);
     - the case λ̂ < 0 is not covered: the void rule handles only λ̂ clipped to 0, and with a (−1, 1) clip a negative λ̂ reverses the predicted sign;
     - the list of central-U.S. regions is "fixed before the run" (line 1757) but is not written in the record;
     - the city panel at the early origins is not stated.
  4. The decision rule is the sign of a point estimate, with no interval. Support (pooled < 0) and refutation (pooled and 1941 both > 0) are asymmetric, so mixed outcomes are undefined.
- Requirement:
  - Commit the plan with its hash before running.
  - Read and state E1's clip, and state what a negative λ̂ means.
  - Write the region list and the city-panel rule into the record.
  - Give a three-outcome table (supported / refuted / inconclusive) based on the 1941 difference with a one-sided 95% bound.
  - State the expected effect size and the power it gives.
  - Until then, record H27 as exploratory.
- Source: standard §1 Claim Type.

R3-H27-b [H27] Major. Dimension: Testability.
- Risk: the pooled confirmatory endpoint includes origins whose predicted sign is missing or does not follow from the mechanism.
  - At 1934 no prediction is made, yet its targets (1935–1941) contain 1936, which favours an E1 gain.
  - At 1948 the stated prediction (≤ 0) does not follow. The recent 15 years (1934–1948) hold the 1930s heat, and the targets (1949–1955) hold the early-1950s drought heat that H27 itself names. That favours an E1 gain.
- Requirement:
  - Make the 1941 difference the single confirmatory endpoint.
  - Either derive the 1934 and 1948 predictions from a quantitative rule fixed now (for example, the sign of the correlation between A_city at c and a regime-exposure index computed from data ≤ c), or label them exploratory.

R3-H27-c [H27] Major. Dimension: Alternative Explanation.
- Risk: a 1941 loss is also predicted by "regime plus real persistent shifts". At 1941 the regime dominates A, so E1 would lose even if persistent shifts exist.
  - The endpoint therefore refutes only pure persistence. It does not show that the early gain "comes from" the regime.
  - The regime timing is also known from the cited literature, which lowers the test's severity. The origins are unseen in the code, but not in what drives the outcome.
- Requirement: pre-register a readout on the unseen origins that separates the two accounts: E1's hottest-day skill in non-central cities, outside the regime footprint. H27 predicts about 0 there; persistence predicts a gain.

R3-H27-d [H27] Nit. Dimension: Design Fit.
- Risk: data item 1 (A = (m_last15 − m_first15)/2) holds only with 30 valid years.
  - The code takes the last 15 valid rows ≤ p, which reach back before p−29 when years are missing (line 68). m30 averages whatever years exist (lines 63–67).
  - At 1934, with windows back to 1875, many cities have gaps, and the national mean is taken over a city set that changes as records begin.
- Requirement: pre-register a completeness rule (for example ≥ 27 valid years in the 30-year window) and a fixed city panel. Run E1 as-is as the primary result and the filtered panel as a sensitivity check.

R3-H27-e [H27] Nit.
- Risk:
  - Regional shares of a summed per-city MAE reduction are unstable when per-city changes have mixed signs.
  - "Spread in proportion" has no threshold, so the zone of 0–15 points is undefined.
  - `Station Changes` may be documented more sparsely in early records, so the two-thirds switch-share criterion can differ by era for documentation reasons alone.
- Requirement: use regional mean reductions with a cluster bootstrap, and state the threshold for "proportional".

====================================================================
WHAT TO FIX BEFORE RUNNING (deadline is today)
====================================================================
1. R3-H36-a and R3-H36-b: centre D_cdd, and fix the missing-value handling with an exact-nesting test. These affect the only refinement that could be adopted.
2. R3-X3: a single registry; merge H36 into H23-CDD; one threshold.
3. R3-X1: the column audit; it decides whether any fold result, including E2's, is affected by leakage.
4. R3-H27-a, R3-H27-b and R3-H37-c: commit H27's plan and run H27 before H37.
5. R3-H32-a: replace G with the multivariate, simulation-calibrated gap.

H35 and H37 are mechanism-only under a failed parent and cannot change the submission.
