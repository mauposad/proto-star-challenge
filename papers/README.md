# Papers

Research papers we study and **reproduce inside this repo**. Each paper gets one folder that
records what the paper proposes, how we implemented it, and how it scored on *our* challenge,
compared like-for-like with our baselines.

The aim is a single place to answer three questions: *which architectures have we tried, how
faithful was each reproduction, and did it beat the current best?*

## Index

One row per paper, newest first. Update the row whenever a paper's status or score changes.
Leave a cell as `TBD` until a real run produces the number; never copy scores from the paper.

| Folder | Paper (short) | Year | Architecture | Status | Config | Backtest score | vs `ten_year_mean` | Notes |
|---|---|---|---|---|---|---|---|---|
| — | *none yet* | | | | | | | |

**Status** values:

| Status | Meaning |
|---|---|
| `reading` | Paper card written, nothing implemented yet |
| `implementing` | Code in progress on a branch |
| `reproduced` | Runs end to end through the official backtest; result logged |
| `adapted` | Reproduced with documented deviations (data, targets, horizon, scale) |
| `abandoned` | Stopped. The card says why (keep it: negative results are results) |

## Folder layout

```
papers/
  README.md                      # this file: index + conventions
  _template.md                   # copy to start a new paper card
  <year>_<first-author>_<short-name>/
    README.md                    # the paper card (required)
    figures/                     # optional: our plots reproducing the paper's figures
```

Folder names are lowercase with underscores, e.g. `2023_lam_graphcast`.

## What lives where

Implementations follow the normal repo rules (see `AGENTS.md`). The paper folder is
documentation and provenance; it must not become a second codebase.

| Thing | Location |
|---|---|
| Paper card (summary, architecture, deviations, results) | `papers/<folder>/README.md` |
| Model code | `src/proto_star/models/`, registered in `models/registry.py` |
| Paper-specific features / preprocessing | `src/proto_star/data/` (reusable, tested) |
| Hyperparameters | `configs/<initials>_paper_<short-name>.yaml` |
| Tests | `tests/`, mirroring the module tested |
| Run outputs | `runs/` (git-ignored, produced by the CLI only) |
| Every result, including failures | a row in `docs/experiments.md` **and** the index above |
| Decision to adopt a paper's method for submission | an ADR in `docs/decisions/` |

## The paper PDFs

Do **not** commit PDFs by default. Most papers are copyrighted, and the pre-commit hook rejects
files larger than 1 MB. Put a DOI or arXiv link in the card instead. A PDF may be committed only
if its license allows redistribution (e.g. CC-BY on arXiv) and it is under 1 MB; state the license
in the card. Keep a personal copy outside git otherwise.

## How to reproduce a paper

1. **Card first.** Copy `_template.md` to `papers/<folder>/README.md`. Fill in the citation,
   link, the problem the paper solves, its architecture, inputs and outputs, and the results
   *as claimed by the authors*. Add the index row with status `reading`.
2. **Map it to our problem.** Write down how the paper's setup maps to ours: inputs (annual
   indices, daily data, station metadata), targets (the four `proto_star.climate.METRICS`),
   horizon (7 years, 2019–2025), and the 2018 cutoff. Every mismatch goes under
   *Deviations*.
3. **Implement through the package.** Add the model to the registry, put hyperparameters in a
   config, and add tests. Follow the leakage rules in `AGENTS.md`: backward-looking features
   only, scalers fitted on training rows, no data after the cutoff.
4. **Score it the same way as everything else.** Use the official relative-skill metric on
   the rolling backtest origins (1997, 2002, 2007, 2011; 7-year horizon), as in ADR 0002 and
   `uv run proto-star climate-backtest`. Report the per-origin scores and the per-metric skill.
   Always compare with `ten_year_mean` (the current baseline) on the same origins.
   The backtest currently scores only the built-in baseline methods. Until registered models
   are wired into it, record exactly how the score was produced (command, commit, config).
5. **Log the result.** Add a row to `docs/experiments.md`, update the index row, and fill the
   card's *Our results* section, **including when it is worse than the baseline**.
6. **Never tune on the leaderboard.** Select settings on the backtest only. Leaderboard
   submissions are made by a human, not by an agent.

## Scoring reference

Current best: **`ten_year_mean`**. Its aggregate skills by backtest origin (from ADR 0002) are
1.09 (1997), 3.14 (2002), 1.13 (2007) and 5.94 (2011). A paper beats the baseline only if it
improves on these across origins, not at one origin.
