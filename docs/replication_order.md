# Replication order

Plan only. Paper IDs refer to [literature/README.md](literature/README.md). Every step is
evaluated with the [backtest plan](backtest_plan.md) and must follow the
[honor code](honor_code.md).

1. Done (trial `baselines_round1`, [write-up](trials/baselines_round1.md)). Baselines per metric: 30-year mean, 10-year mean, 15-year mean, linear trend, hinge fit
   (P01 to P04). Add median versions of each window (P09).
2. Backtest harness with the cut-offs in the backtest plan (P10, P12). Fold design checked against 12 rolling origins in `docs/trials/fold_study.md` (P10, P12, P19; ADR 0006 proposed). Built: `proto_star.backtest`,
   usage in `notebooks/README.md`.
3. Done (trial `paper_p09_p14_pooled`, [summary](trials/papers_round1_summary.md)). One pooled model across all cities with a median (pinball loss at 0.5) objective.
   Inputs: lagged annual values, window means, latitude, longitude (P09).
4. Done (trial `paper_neural`). Neural models: N-BEATS and DeepAR, trained from scratch (P05, P08).
5. Optional: Group B papers, only after a ruling.
6. Done (trial `paper_p13_arima`). ARIMA per city, the dataset authors' own method (P13).
7. Done (trial `regional_p22_p24`, [round-2 summary](trials/papers_round2_summary.md)). City trends blended with regional trends, and other pooled models (P14, P22). The pooled P14 part ran with step 3.
8. Done (trial `station_p15`). Levels from the current station segment, and station steps estimated from neighbors (P15).
9. Done (trial `paper_cdd_forcing_p06_p21`, with P06 and P21). CDD recomputed from daily data after a warming shift.
10. Done (trial `paper_normals_gev`, with optimal and alternative normals P02–P04). Nonstationary extreme value model for the hottest day (P23).
11. Done (trial `combos_p16_p17`). Equal-weight average of the best few methods (P16, P17).
12. Done (trial `regional_p22_p24`). Elevation, land cover, or population as pooling groups (P24). This also adds interoperability.

Practice-run fact from the deck: temperature and CDD carry the signal. Precipitation and
hottest day are mostly noise. A window average near the 30-year average is already hard to
beat for those two.
