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

Cap every download at 2018-12-31. List every external source and AI tool in README.md.
