## What & why

<!-- One or two sentences. Link the issue: Closes #123 -->

## Type

- [ ] Data (loading / cleaning / features)
- [ ] Model / experiment
- [ ] Infrastructure / tooling
- [ ] Docs

## Results (model or feature changes)

| Config | Val metric (before) | Val metric (after) |
|---|---|---|
|  |  |  |

## Checklist

- [ ] `make check` passes locally
- [ ] Tests added/updated for new logic
- [ ] No data, weights, secrets, or notebook outputs committed
- [ ] New features use only information available at prediction time (no leakage)
- [ ] `docs/experiments.md` / `docs/data.md` updated if relevant
- [ ] New dependencies added with `uv add` and `uv.lock` committed
