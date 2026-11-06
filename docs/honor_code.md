# Honor code: data cut-off

Hard constraint for the whole team. No exceptions.

We use nothing that was trained or fitted on data after **2018-12-31**.

- No pretrained weights unless the training data ends before 2019. Default: train every
  model from scratch.
- No weather data from 2019 to 2025, from any source or place.
- No data that responds to the weather (streamflow, ozone days, energy demand).
- No LLM or AI agent may give or correct forecast values. An LLM may write or explain
  code only.
- Any paper that uses climate model output (for example CMIP6) goes in the "Needs a ruling"
  group of [literature/README.md](literature/README.md). Low priority.

In practice: cap every download at 2018-12-31, and list every external source and AI tool
in the root [README.md](../README.md).
