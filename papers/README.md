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
| `2021_montero-manso_global_pooled` | Montero-Manso & Hyndman, global vs local (P14), with median/quantile regression (P09) | 2021 | Global linear AR (ridge / pinball-0.5 quantile regression) and quantile GBM, pooled over cities, direct multi-horizon | adapted | `configs/agent_paper_p09_p14_pooled.yaml` | `hybrid_ridge_all_cdd`: 0.24 / 4.13 / 6.44 at 1980/1995/2011 (mean 3.60; years 4–7 5.54) | -2.53 / 1.39 / 5.16 (mean 1.34): better at 3/3 origins | Helps CDD only. Temperature, precipitation and hottest day stay on `current_best`. The median loss did not beat squared loss. `current_best` is -0.75 / 3.56 / 5.95 |
| `2020_salinas_deepar` | Salinas et al., DeepAR (P08) | 2020 | Global autoregressive LSTM, Gaussian likelihood, median of sample paths | `adapted` | `configs/agent_paper_neural.yaml` | best `deepar_hybrid`: −0.91 / 3.58 / 7.40 (1980/1995/2011); mean 3.36 all, 5.08 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Best mean of the neural track but wins years 4–7 at 1 of 3 origins; seed-7 replica 3.03 / 4.63. Not adopted; revisit with more seeds |
| `2019_oreshkin_nbeats` | Oreshkin et al., N-BEATS (P05) | 2019 | MLP residual backcast/forecast blocks (generic; trend + generic), median ensemble | `adapted` | `configs/agent_paper_neural.yaml` | best `nbeats_hybrid`: −0.74 / 4.10 / 5.87 (1980/1995/2011); mean 3.08 all, 4.57 years 4–7 | better at all 3 origins (−2.53 / 1.39 / 5.16) | Does not beat `current_best` (2.92 / 4.68); seed-7 replica 2.88 / 4.03. Full-metric variants lose on precip/hottest day |
| `2013_wilks_livezey_normals` | Huang et al. 1996 (P02), Wilks 2013 (P03), Wilks & Livezey 2013 (P04): optimal / alternative climate normals | 1996, 2013 | Statistical normals: OCN window by in-train hindcast, EWMA, damped trend | adapted | `configs/agent_paper_normals_gev.yaml` | best paper method `ewma_opt` 2.71 all / 3.46 yrs 4–7 (`current_best` 2.92 / 4.68) | beats (1.34 / 2.78) | Per-origin `ocn` -1.41 / 2.25 / 6.22, `ewma_opt` 0.13 / 3.06 / 4.96. EWMA best for CDD and years 1–3; worse for temperature in years 4–7. Not adopted |
| `2013_wilks_livezey_normals` | UCAR extremes notes (P23): nonstationary GEV with a location trend | n/a | GEV MLE, location trend shrunk, median forecast, hottest day only | adapted | `configs/agent_paper_normals_gev.yaml` | `gev_stationary` 2.92 all / 4.69 yrs 4–7; with trend `gev_trend_opt` 2.55 / 4.00 | beats (1.34 / 2.78) | Per-origin `gev_stationary` -0.68 / 3.53 / 5.92. Trend hurts even when shrunk; stationary median ties the 30-year mean. Not adopted |
| `2020_lai_arima` | Lai & Dzombak, ARIMA near-term regional temperature and precipitation forecasts (WAF) | 2020 | Statistical: per-series ARIMA (KPSS + stepwise AICc, Mann-Kendall drift, Box-Cox) | adapted | `configs/agent_paper_p13_arima.yaml` | -2.59 / 0.37 / 3.01 (1980/1995/2011) | worse: `ten_year_mean` -2.53 / 1.39 / 5.16 | Lost to `current_best` at every origin and window. Years 4–7 mean 1.06 against 4.68. CDD skill slightly better in years 4–7 at 1 of 3 origins. Not submitted |

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
| Model code | one module in `src/proto_star/forecasters/`, registered with `@register_forecaster` (see `forecasters/registry.py`); heavy imports inside the factory |
| Paper-specific features / preprocessing | `src/proto_star/data/` (reusable, tested) |
| Hyperparameters | `configs/<initials>_paper_<short-name>.yaml`, under `variants: {name: {forecaster: ..., params: {...}}}` |
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
   the rolling backtest origins (1980, 1995, 2011; 7-year horizon), using
   `proto_star.backtest` as shown in `notebooks/README.md`. Report the per-origin scores and the
   per-metric skill, with forecast years 4–7 separately. Always compare with `ten_year_mean` and
   the current best on the same origins, and record the commit and how the score was produced.
5. **Log the result.** Add a row to `docs/experiments.md`, update the index row, and fill the
   card's *Our results* section, **including when it is worse than the baseline**.
6. **Never tune on the leaderboard.** Select settings on the backtest only. Leaderboard
   submissions are made by a human, not by an agent.

## Scoring reference

Baseline: **`ten_year_mean`**. Its raw scores by backtest origin (from ADR 0004) are
-2.53 (1980), 1.39 (1995) and 5.16 (2011). The current best is the metric ensemble:
-0.75, 3.56 and 5.95. A paper beats the baseline only if it
improves on these across origins, not at one origin.
