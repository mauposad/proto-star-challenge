# AGENTS.md (team data rule)

The repo-wide agent rules are in the root [AGENTS.md](../AGENTS.md). This file adds the
team's hard data rule. Full text: [docs/honor_code.md](../docs/honor_code.md).

## Team rule (hard constraint, no exceptions)

We use nothing that was trained or fitted on data after 2018-12-31.

- **NEVER** use pretrained weights unless their training data ends before 2019. Default:
  train every model from scratch.
- **NEVER** use weather data from 2019 to 2025, from any source or place.
- **NEVER** use data that responds to the weather (streamflow, ozone days, energy demand).
- **NEVER** give, suggest, or correct forecast values. An LLM may write or explain code only.
- Papers that use climate model output (for example CMIP6) need a ruling before use.
- **NEVER** download the original source records (DOIs `10.1184/R1/7890488` and
  `10.1184/R1/7961012`, or their `CMU-OSPO` Hub copies). They run past 2018. Cite them only.
- **NEVER** tune a method using knowledge of how 2019 to 2025 turned out. Justify every modeling
  choice with a backtest on data through 2018.
- Papers from any year are fine for methods. **NEVER** take observed 2019 to 2025 values or
  findings about those years from them.

Cap every download at 2018-12-31, and pass every weather input through
`proto_star.climate.assert_weather_cutoff`. List every external source and AI tool in README.md.
