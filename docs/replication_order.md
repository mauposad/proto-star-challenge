# Replication order

Plan only. Paper IDs refer to [literature/README.md](literature/README.md). Every step is
evaluated with the [backtest plan](backtest_plan.md) and must follow the
[honor code](honor_code.md).

1. Baselines per metric: 30-year mean, 10-year mean, 15-year mean, linear trend, hinge fit
   (P01 to P04). Add median versions of each window (P09).
2. Backtest harness with the cut-offs in the backtest plan (P10, P12).
3. One pooled model across all cities with a median (pinball loss at 0.5) objective.
   Inputs: lagged annual values, window means, latitude, longitude (P09).
4. Neural models: N-BEATS and DeepAR, trained from scratch (P05, P08).
5. Optional: Group B papers, only after a ruling.

Practice-run fact from the deck: temperature and CDD carry the signal. Precipitation and
hottest day are mostly noise. A window average near the 30-year average is already hard to
beat for those two.
