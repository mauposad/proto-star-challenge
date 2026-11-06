# ADR 0002: Use the 10-year mean as the initial ProtoStar submission baseline

## Status

Accepted 2026-11-06.

## Context

The challenge requires a single 2019–2025 forecast per city and metric, made
using data available through 2018 only. The official score is mean relative
MAE skill against the 30-year average, so a complicated method that does not
outperform that reference is not useful.

We ran leakage-safe seven-year rolling backtests at 1997, 2002, 2007, and 2011
origins. Each fold quality-screened annual values with the organizer's
ten-missing-day rule and evaluated the four official metrics equally.

## Decision

Generate the first local submission with each city and metric's last ten valid
years mean (`ten_year_mean`).

Its aggregate skills were positive in every tested window: 1.09 (1997), 3.14
(2002), 1.13 (2007), and 5.94 (2011). The linear trend had stronger temperature
and CDD performance in the most recent fold, but negative precipitation skill
in every fold and a non-positive aggregate score in three of four windows.

## Consequences

The 10-year mean is an honest, reproducible benchmark and a valid submission
candidate. Future models must be compared on the same rolling folds and report
each metric's skill, not only a combined score. A metric-specific ensemble is a
promising next experiment, but it must be selected without leaderboard tuning
or any post-2018 weather-responsive input.
