# Backtest plan

Source: the challenge kickoff deck. Plan only; no backtest results are recorded here.

- Forecast 7 years ahead from each cut-off, as in the challenge.
- Cut-offs:

  | Train up to | Test years |
  |---|---|
  | 1980 | 1981–1987 |
  | 1995 | 1996–2002 |
  | 2011 | 2012–2018 |

- Never use random splits.
- Score like the Space: skill against the 30-year average, per metric, then the mean of the
  4 skills, clipped at 0. Skill per metric = 1 − MAE / MAE of the 30-year average;
  Final Score = 100 × max(0, mean of the 4 skills).
- Count only valid city-years (10 missing days or fewer, from the `Miss *` columns).
- Reason for caution: the Live board covers only 2019–2021. Three years of weather are
  noisy. Trust the backtest.

- Also report forecast years 4–7 separately. They match the Final Score (2022–2025).

These are the defaults in `proto_star.backtest` (see ADR 0004). Usage: `notebooks/README.md`.

Method references: P10, P12 and P19 in [literature/README.md](literature/README.md).
