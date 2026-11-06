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
- No downloading the original source records (DOIs `10.1184/R1/7890488` and
  `10.1184/R1/7961012`, or their `CMU-OSPO` Hub copies). They run past 2018. Cite them only.
- No tuning a method using knowledge of how 2019 to 2025 turned out. Every modeling choice
  must be justified by a backtest on data through 2018.
- Papers from any year are fine for methods. Never take observed 2019 to 2025 values or findings
  about those years from them.

The challenge allows data that responds to the weather for analysis and the policy idea only.
Mark it "Analysis only" in the data card. Forecasting code must not read it.

In practice: cap every download at 2018-12-31, pass every weather input through
`proto_star.climate.assert_weather_cutoff`, and list every external source and AI tool in the
root [README.md](../README.md).
