# Exploration behind the pooled-trend trial

Every variant tried before `configs/lc_pooled_trend.yaml` was fixed, including the ones that
failed. All used data through 2018 only, and no leaderboard score informed any choice.

These numbers come from throwaway scripts that were not kept, so treat them as a record of what
was tried. Only the forecasters in [pooled_trend.md](pooled_trend.md) are reproducible from the
repo. The official score is the mean of the four metric skills, so each metric was compared
alone. All variants below use the non-negative pooled slope unless noted.

Columns are skill in percent against the 30-year mean: mean over the official folds (1980, 1995,
2011), the same for forecast years 4–7, and the mean over seven cut-offs (adding 1985, 1990,
2000, 2005) as a robustness check.

## Disclosure: the non-negative slope was added after seeing a failure

The first version let the pooled slope go negative, and lost to `current_best` at 1980 (raw
score -3.15 against -0.75). The 40-year slope is negative at 1980 and 1985 (-0.026 and -0.019
°F per year) because of mid-century cooling. The floor fixes that. It was chosen after seeing
this fold, so the 1980 result is not an independent test of it. It has no effect on the
2019–2025 forecast: the slope through 2018 is +0.050 °F per year.

## Average temperature

| Variant | Official | Years 4–7 | 7 cut-offs |
|---|---|---|---|
| Level 10 | 8.86 | 18.19 | 10.03 |
| Level 15 | 7.93 | 16.51 | 10.75 |
| **Levels 10 and 15, averaged (chosen)** | 8.74 | 17.73 | 10.95 |
| Levels 5, 10 and 15, averaged | 7.53 | 14.96 | 10.57 |
| Level 10, 30-year trend window | 7.62 | 16.73 | 8.55 |
| Level 10, 50-year trend window | 8.67 | 17.36 | 9.32 |
| Level 10, 25% own-city slope | 7.65 | 16.34 | 9.06 |
| Level 10 from the current station only | 8.91 | 18.19 | 10.09 |

Level 10 and level 15 trade places depending on the cut-offs, so averaging them avoids betting on
either. The station-only level changed almost nothing, so it was not worth the extra code.

## Cooling degree days

| Variant | Official | Years 4–7 | 7 cut-offs |
|---|---|---|---|
| Level 10, pooled CDD slope | 7.74 | 10.06 | 6.46 |
| Level 15, pooled CDD slope | 6.22 | 7.93 | 6.00 |
| Levels 10 and 15, pooled CDD slope | 7.33 | 9.32 | 6.61 |
| Level 10, 30-year trend window | 6.88 | 9.47 | 5.02 |
| Level 10, 50-year trend window | 7.90 | 9.87 | 5.82 |
| Level 10, 25% own-city slope | 7.07 | 8.89 | 6.07 |
| Level 10, slope scaled by city sensitivity | 8.04 | 10.45 | 6.78 |
| Level 10, half pooled, half sensitivity | 7.97 | 10.35 | 6.69 |
| **Levels 10 and 15, sensitivity (chosen)** | 7.80 | 9.94 | 7.02 |
| Level 10, slope proportional to city level | 8.35 | 10.86 | 6.73 |
| Level 10 from the current station only | 7.82 | 10.16 | 6.54 |

Sensitivity and the proportional slope are close, and the gap is within noise. Sensitivity was
kept because it has a physical reading: CDD gained per degree in that city.

## Hottest day and precipitation

| Variant | Hottest: official / 7 cut-offs | Precipitation: official / 7 cut-offs |
|---|---|---|
| **30-year mean (chosen)** | 0.09 / 0.05 | 0.01 / 0.00 |
| 20-year mean | 0.09 / -0.55 | -1.00 / -0.83 |
| 40-year mean | -0.22 / -0.09 | 0.71 / 0.07 |
| 50-year mean | -2.19 / -1.09 | -0.25 / -0.23 |
| 30-year median | 0.13 / -0.40 | -0.64 / -0.79 |

The 40-year precipitation mean looks better on the official folds, but the gain vanishes over
seven cut-offs, so it was rejected. The 30-year rows differ slightly from zero because the
exploration code handled sparse cities a little differently from the reference.

## Tried earlier, also rejected

Raw score, official folds, with no slope floor. Reference points: level 15 with a pooled trend
scored 2.30, and `current_best` 2.92.

| Variant | Raw score |
|---|---|
| Regional slopes instead of one national slope | 1.78 |
| Slope multiplied by 1.5 | 1.94 |
| Trend added to hottest day as well | 1.81 |
| Trend added to all four metrics | 0.91 |
| CDD from shifted daily temperatures (delta method), blended 50% | 2.28 |
| CDD from shifted daily temperatures, alone | 2.17 |

The delta method comes from the public `ashley-boys` submission, which also inspired the pooled
trend. It did not help on our folds, so it was left out.

## Limits

About 40 variants were compared on few folds, so the small gaps above are not meaningful and the
winner's score is somewhat flattered. Only the large gap, a pooled trend against no trend for
temperature and CDD, is well supported. The gain is concentrated after about 2000. In forecast
years 1–3 the candidate scores below `current_best` (0.33 against 0.63), so a modest Live Score
would not by itself mean the method failed.
