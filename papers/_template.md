# <Paper title>

<!-- Copy this file to papers/<year>_<first-author>_<short-name>/README.md -->

| | |
|---|---|
| **Authors** | |
| **Year / venue** | |
| **Link** | DOI or arXiv URL |
| **Code released by authors** | URL, license, or "none" |
| **PDF in repo?** | no / yes (license: …) |
| **Status** | reading / implementing / reproduced / adapted / abandoned |
| **Owner** | initials |
| **Branch / PR** | |

## Summary

What problem the paper addresses and its main idea, in 3–5 sentences.

## Architecture

- Model family (e.g. gradient boosting, LSTM, transformer, GNN, statistical / trend model)
- Inputs and their preprocessing
- Outputs and forecast horizon
- Loss and training procedure
- Key hyperparameters as reported

## Results claimed by the authors

The datasets, metric and numbers as reported in the paper. These are **not** our results.

## Mapping to our challenge

| Paper | Ours |
|---|---|
| Data | annual indices / daily / coverage and stations (≤ 2018) |
| Target(s) | `annual_avg_temp`, `total_precip_in`, `hottest_day_temp`, `cdd` |
| Horizon | 7 years (2019–2025) |
| Metric | relative MAE skill vs 30-year mean |

## Deviations

Every place where our implementation differs from the paper, and why.

## Implementation

- Registry name:
- Code: `src/proto_star/models/...`
- Config: `configs/<initials>_paper_<short-name>.yaml`
- Tests: `tests/...`
- Leakage review: how features avoid using information from after the cutoff

## Our results

Same backtest origins as the baseline. Fill these in only from real runs.

| Origin | Score | `ten_year_mean` | avg_temp skill | precip skill | hottest_day skill | cdd skill |
|---|---|---|---|---|---|---|
| 1997 | TBD | 1.09 | | | | |
| 2002 | TBD | 3.14 | | | | |
| 2007 | TBD | 1.13 | | | | |
| 2011 | TBD | 5.94 | | | | |

Command, commit and run dir:

## Takeaways

What worked, what did not, and whether to keep, adapt or abandon it.
