# 0008: Reuse the Luo et al. and Fernandez and Barnes methods on observations only

- **Date:** 2026-11-08
- **Status:** accepted (2026-11-08)
- **Deciders:** mauposad (human owner). Other team members: TBD

The plan (`docs/plan_regional_and_papers.md`) calls this ADR 0005. Numbers 0005 to 0007 are
already used on other branches, so it is 0008.

## Context

Two papers in the "Needs a ruling" group of [docs/literature/README.md](../literature/README.md)
have methods we want to try:

| ID | Paper | What it trains on | Why it needs a ruling |
|---|---|---|---|
| R01 | Fernandez and Barnes 2025, ML model-analog (arXiv 2502.17583) | About 100,000 annual states from 29 CMIP6 models | CMIP6 runs extend past 2018 |
| R02 | Luo et al. 2022, Bayesian deep learning with SVGD (arXiv 2202.11244) | CESM2 pre-industrial control North Atlantic SST | Simulated data, not a U.S. city metric |

The honor code says: nothing trained or fitted on data after 2018-12-31; no pretrained weights
unless their training data ends before 2019; papers from any year are fine for methods; papers
that use climate model output need a ruling.

The question is whether we may reuse each paper's *method* while leaving out its *data*.

## Decision

1. We reuse the methods only: the model structure, loss, training procedure and selection rule.
2. We train and fit only on the challenge observations (the annual master table and the daily
   table, through 2018), plus external data allowed by the honor code, capped at 2018-12-31 and
   passed through `proto_star.climate.assert_weather_cutoff`.
3. We do not download, read or use any CMIP, CESM or other climate model output, for any years.
   This includes the paper's analog libraries and any derived files.
4. We do not use pretrained weights. Every network is trained from scratch, seeded from config.
5. We take no observed 2019-2025 values, and no findings about those years, from either paper.
6. Each replication is a forecaster `forecaster(train, cutoff_year, forecast_years)`, scored on
   the ADR 0004 folds like every other method, and recorded in `docs/trials/`.

Main changes forced by the data:

| Paper | Paper's library or training set | Ours |
|---|---|---|
| R01 model-analog | About 100,000 simulated annual states | Observed years 1900 to (cut-off - lead): about 80 to 110 states per fold |
| R02 Bayesian DL | 1,280 simulated monthly SST maps | About 1,300 monthly city anomalies per fold, from `daily` |

Both models predict an anomaly added to the current champion's forecast, so they cannot remove
its warming trend.

## Consequences

- Agents A (Luo, `agent/luo-bdl`) and B (model-analog, `agent/model-analog`) may start.
- The libraries are 100 to 1,000 times smaller than in the papers. A null or negative result is
  likely, and is reported as one ("the methods do not transfer to observations only"). The
  README may then mark it as a negative result.
- The README's Feedback section says that both papers depend on climate model libraries that
  this team's rule blocks, and what an observation-only version can and cannot do.
- R01 and R02 in `docs/literature/README.md` are marked "Methods only (ADR 0008)".
- Revisit if the organizers rule that simulated data, such as pre-industrial control runs, is
  allowed. That would be a new ADR, not an edit to this one.
