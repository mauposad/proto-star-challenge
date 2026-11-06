# 0003: Use a calendar window for the 30-year baselines

- **Date:** 2026-11-06
- **Status:** proposed (needs team review on the PR)
- **Deciders:** TBD

## Context

The challenge defines the 30-year average as each city's mean from 1989 to 2018, and the trend
baseline as a line through the last 30 years. `thirty_year_mean` and `linear_trend` instead took
the last 30 *valid* years. For a city with gaps, that window reached back decades.

The organizers publish one check: train to 2010, predict 2011–2018, CDD MAE of 213 °F-days for
the 30-year average and 177 for the trend line. The old code did not reproduce these.

| CDD practice run MAE | Published | Before | After |
|---|---|---|---|
| 30-year average | 213 | 216.7 | 212.9 |
| Linear trend | 177 | 174.7 | 177.4 |

This changes evaluation code, so AGENTS.md requires an ADR. The purpose is to match the official
definition, not to raise a score. Some scores went down.

## Decision

`thirty_year_mean` and `linear_trend` use the calendar window ending at the cutoff year. If a
city has no valid value in that window, they fall back to its last 30 valid years, so every row
still gets a prediction. `ten_year_mean` and `last_valid_year` are unchanged.

## Consequences

Every score measured against the 30-year reference changed, including those in ADR 0002. Use
these numbers from now on.

| Method | Version | 1997 | 2002 | 2007 | 2011 |
|---|---|---|---|---|---|
| `ten_year_mean` | Before | 1.09 | 3.14 | 1.13 | 5.94 |
| `ten_year_mean` | After | 1.43 | 3.01 | 0.30 | 5.16 |
| Metric ensemble | Before | 3.02 | 3.33 | 1.56 | 6.74 |
| Metric ensemble | After | 3.45 | 3.33 | 0.87 | 5.95 |

The backtest still selects the same methods per metric: 10-year mean for temperature and CDD,
30-year mean for precipitation and hottest day.

Our scorer keeps rows for sparse cities, while the organizers do not score "the few cities
without enough past data". Their threshold is not published, so our scores can differ slightly
from theirs. Revisit this if they publish it.
