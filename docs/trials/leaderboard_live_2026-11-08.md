# Live leaderboard snapshot, 2026-11-08

Read on 2026-11-08 from the challenge Space
(`CMU-OSPO/protostar-challenge-climate-risk-intelligence`) through its public `load_board`
endpoint. Recorded for reference only. The honor code forbids choosing or tuning on it.

The Space scores each metric as `S_m = 1 − MAE_m / MAE_30yr,m` and reports
`100 × max(0, mean S_m)`. The live split is 2019–2021 (our forecast years 1–3). The final split,
2022–2025, is hidden until the deadline. Only a team's latest submission counts.

## Board (live split, 2019–2021)

| Rank | Team | Score | Temp MAE °F | Precip MAE in | Hottest day MAE °F | CDD MAE | Version that counts |
|---|---|---|---|---|---|---|---|
| 1 | PstarAlu (CMU) | 16.1 | 0.990 | 5.956 | 2.174 | 136.8 | Nov 8, 00:52 ET |
| 2 | TROUBLESHOOTERS (CMU) | 15.9 | 0.981 | 5.824 | 2.233 | 138.4 | Nov 7, 02:27 ET |
| 3 | GuaGuaBear (CMU) | 15.5 | 1.006 | 5.831 | 2.172 | 143.6 | Nov 6, 23:00 ET |
| 4 | Ashley boys | 14.9 | 1.026 | 5.987 | 2.173 | 140.8 | Nov 6, 14:14 ET |
| 5 | Team Tatakae | 14.4 | 1.061 | 5.987 | 2.173 | 140.2 | Nov 7, 08:25 ET |
| 6 | unicorns (CMU) | 14.1 | 1.064 | 5.987 | 2.173 | 141.9 | Nov 7, 22:02 ET |
| 7 | Klepon Nusantara | 14.1 | 1.093 | 6.001 | 2.165 | 138.6 | Nov 7, 23:20 ET |
| 8 | Evanguo12 | 13.8 | 1.080 | 5.993 | 2.174 | 142.0 | Nov 7, 02:34 ET |
| **9** | **MKDir (CMU)** | **13.6** | **1.068** | **5.987** | **2.173** | **145.2** | **Nov 7, 16:33 ET** |
| 10 | LEGENDS OF THE FALL | 13.1 | 1.156 | 5.830 | 2.200 | 140.1 | Nov 2, 08:13 ET |
| 11 | Carbon Copies (CMU) | 12.9 | 1.089 | 5.987 | 2.185 | 146.9 | Nov 7, 15:51 ET |
| 12 | Cloudbreak (CMU) | 12.9 | 1.126 | 5.987 | 2.176 | 143.2 | Nov 7, 20:47 ET |
| 13 | GW OSPO | 12.8 | 1.098 | 5.975 | 2.177 | 147.3 | Nov 5, 11:52 ET |
| 14 | Zhoey | 12.8 | 1.106 | 5.987 | 2.173 | 146.2 | Nov 7, 18:19 ET |
| 15 | Placeholder (CMU) | 12.5 | 1.128 | 5.987 | 2.176 | 146.0 | Nov 7, 17:35 ET |
| 16 | Team Hurricane (CMU) | 11.7 | 1.018 | 6.942 | 2.185 | 134.1 | Nov 7, 20:05 ET |
| 17 | Ocarina of Ten (reference: 10-year mean, example notebook) | 10.4 | 1.191 | 5.782 | 2.295 | 149.6 | Nov 5, 09:12 ET |
| – | Linear trend (baseline) | 9.6 | 1.095 | 6.122 | 2.413 | 147.4 | |
| – | 30-year average (baseline, the reference) | 0.0 | 1.477 | 5.987 | 2.176 | 198.0 | |
| – | Last year repeated (baseline) | 0.0 | 1.146 | 8.466 | 2.751 | 175.8 | |

## Which package is scored

The counted version (Nov 7, 16:33 ET) is the pooled-trend package,
`corbe19/protostar-climate-MKDir-pooled-trend@af04833` (committed 16:29 ET). The temperature MAE
moved from 1.190 to 1.068. `hybrid_ridge_all_cdd` keeps the old 10-year-mean temperature column,
so it would have left the temperature MAE at 1.190.

## Our score, metric by metric

| Metric | `current_best` (11.0) | Pooled trend (13.6) | 30-year average (par) | Skill, pooled trend |
|---|---|---|---|---|
| Avg temperature (°F) | 1.190 | 1.068 | 1.477 | +0.277 |
| Precipitation (in) | 5.987 | 5.987 | 5.987 | 0.000 |
| Hottest day (°F) | 2.173 | 2.173 | 2.176 | +0.001 |
| CDD (°F-days) | 149.6 | 145.2 | 198.0 | +0.267 |
| Score | | | | 13.6 |

Precipitation and hottest day are the 30-year mean in both submissions, so all of the gain is in
temperature and CDD. The CDD gain (4.4 °F-days) is within the 10 °F-day noise level the Space
states. The live split covers forecast years 1–3, where the pooled trend was weakest in the
backtest (raw score 0.33 vs 0.63 for `current_best`), so this board says little about 2022–2025.
