# 0004: Use the kickoff deck's backtest cut-offs

- **Date:** 2026-11-06
- **Status:** accepted (2026-11-06)
- **Deciders:** the team; Luke proposed it, and the human owner confirmed it as the agreed validation scheme

## Context

The repo backtested from 1997, 2002, 2007, and 2011. The challenge kickoff deck, recorded in
[docs/backtest_plan.md](../backtest_plan.md), uses 1980, 1995, and 2011. Luke proposed following
that plan wherever work overlaps, pending team review. AGENTS.md requires an ADR to change the validation
scheme.

## Decision

Use cut-offs 1980, 1995, and 2011 as the default in `proto_star.backtest`, the CLI, and
`scripts/evaluate_metric_ensemble.py`. They are defined once, as `DEFAULT_CUTOFFS` in
`proto_star.climate`, and trial configs cannot override them.

## Consequences

The backtest still selects the same methods: 10-year mean for temperature and CDD, 30-year mean
for precipitation and hottest day. The test periods no longer overlap, but there are only three.

Scores below use the ADR 0003 scorer. `raw_score` is the official score without its floor at zero.

| Method | Raw score 1980 | Raw score 1995 | Raw score 2011 |
|---|---|---|---|
| Metric ensemble | -0.75 | 3.56 | 5.95 |
| `ten_year_mean` | -2.53 | 1.39 | 5.16 |
| `linear_trend` | -15.43 | -24.85 | 2.00 |

The ensemble loses to the 30-year average from 1980, so a recent window is not always better. A
method that needs recent warming to work will be penalized at that cut-off, which is a useful test.

Earlier rows in docs/experiments.md and scores in ADRs 0002 and 0003 use the old cut-offs and are
not comparable with these.
