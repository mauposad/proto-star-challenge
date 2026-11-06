---
pretty_name: "ProtoStar Climate Risk Intelligence — <Team Name>"
license: cc-by-4.0
task_categories:
  - time-series-forecasting
tags:
  - climate
  - forecasting
  - protostar-climate-2026
---

# <Team Name>: ProtoStar Climate Challenge Submission

Negative result: no

Forecasts of annual weather for 210 U.S. cities, 2019–2025, generated using
only weather observations through 2018-12-31.

## Team

| Name | Hugging Face username | University, Program |
| --- | --- | --- |
| <team member> | <@username> | <institution and program> |

## Method

We quality-screened CMU's `annual_indices` table at the metric level: annual
average temperature and CDD require both Tmax and Tmin missing-day counts at
most 10; total precipitation requires precipitation missing days at most 10;
and hottest-day temperature requires Tmax missing days at most 10.

We ran leakage-safe seven-year rolling backtests from 1997, 2002, 2007, and
2011, scoring each target against the official 30-year-average reference.
The final metric-specific ensemble uses:

- `annual_avg_temp`: ten-year mean of valid years;
- `total_precip_in`: thirty-year climatology;
- `hottest_day_temp`: thirty-year climatology;
- `cdd`: ten-year mean of valid years.

The ensemble's historical scores were 3.02, 3.33, 1.56, and 6.74 across those
four origins. It deliberately preserves climatology for precipitation and
hottest-day values, where simple trend extrapolation was not robust.

## AI Tools and Agents

- Tools and models: Warp Oz agent.
- What they did: implemented reproducible data ingestion, quality checks,
  baseline backtests, official-score calculation, static metadata integration,
  documentation drafts, and submission validation.
- What a person reviewed: <team must complete before publication>.
- Agent instructions file: `AGENTS.md`; it enforces the 2018-12-31 weather
  cutoff and prohibits agents from supplying forecast values.

## Policy Idea

See the finalized text in `docs/submission/policy-idea.md`, copied here before
upload. The proposal uses city-scale CDD and temperature forecasts for
utility/city peak-cooling planning while explicitly avoiding neighborhood-level
claims from airport-station records.

## Feedback to the Ecosystem

See `docs/submission/ecosystem-feedback.md`, copied here before upload.

## Files

| File | Content |
| --- | --- |
| `submission.csv` | Required 5,880 city/year/metric forecasts |
| `code/` | This repository's climate pipeline and requirements |
| `data/README.md` | Input provenance, licensing, checksums, and leakage assessment |

## How to Reproduce

1. Install the pinned environment with `uv sync`.
2. Download the documented CMU training tables with
   `uv run python scripts/download_protostar_data.py`.
3. Run `uv run python scripts/evaluate_metric_ensemble.py`.
4. Generate and validate forecasts with `uv run proto-star
   climate-ensemble-submission data/raw/protostar/annual_indices.parquet
   data/raw/protostar/city_info.parquet`.
5. Run `uv run pytest -q` and `python code/check_submission.py` after copying
   the final CSV into the official Hugging Face submission template.

## Data

- Forecast input: `CMU-OSPO/protostar-climate-train-to-2018`,
  `annual_indices` and `city_info`, CC0-1.0, cutoff at 2018-12-31.
- Static interoperability metadata: NOAA GHCN-Daily station inventory,
  joined by station ID only. It contains no weather observations and is not
  read by the forecasting code.
- Exact artifact checksums and limitations: `docs/data.md`.
