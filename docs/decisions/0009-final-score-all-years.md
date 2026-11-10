# 0009: Select on all 7 forecast years, since the Final Score now uses all of them

- **Date:** 2026-11-09
- **Status:** proposed
- **Deciders:** the human owner (to accept); drafted by Claude Code for the final round

## Context

Until now the team gave the most weight to `years_4_7` (forecast leads 4-7), because the
Final Score covered 2022-2025 only (plan_regional_and_papers.md, rule 3). The challenge update
of November 9 changes the Final Score: it now uses all 7 years, 2019-2025, with equal weight
for each year. Our `all` window (leads 1-7, every year weighted equally in the MAE) matches the
new Final Score.

AGENTS.md requires an ADR to change the validation scheme or how candidates are chosen. This
ADR changes only which existing column is primary. It does not change the folds (ADR 0004),
the scorer (ADR 0003), the metric or any evaluation code.

## Decision

- The primary column for selecting a forecaster is `all` (leads 1-7), on the official folds
  1980, 1995 and 2011.
- `years_1_3` and `years_4_7` are still reported next to it, in every trial note.
- The final round also checks every candidate on 27 rolling origins (cut-offs 1985-2011, 7-year
  horizon, only target years up to 2018), with `scripts/robustness_origins.py --origins
  rolling27` (`proto_star.robustness`). This is a check on the same window, not a new fold
  scheme: the official folds stay as ADR 0004 defines them.
- No 2019-2025 data or leaderboard score is used to make this or any later choice.

## Consequences

- Methods that help in the first forecast years (such as lead_split3's ridge in years 1-3) now
  count fully. Methods tuned for years 4-7 alone lose weight.
- Earlier choices that were made on `years_4_7` (for example the CRM's row 6 choice) were made
  under the old rule. They are not reopened by this ADR; the final round re-tests them on `all`.
- Revisit if the challenge changes the Final Score weighting again.
