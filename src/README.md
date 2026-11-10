# src

## Overview

`src/` is the source root for the installed `proto-star` distribution. Hatch builds it from
`packages = ["src/proto_star"]`, and the `proto-star` console script is `proto_star.cli:app`
(see `pyproject.toml`). It holds one Python package, nothing else.

The package works only as an editable install inside a repo checkout:

- `proto_star/paths.py` derives `PROJECT_ROOT` as `Path(__file__).parents[2]`, which assumes
  the `src/` layout.
- Three CLI commands import the top-level `scripts/`, which is not packaged.
- `submission_package` copies files from `src/proto_star`, `scripts/`, `AGENTS.md` and
  `docs/submission/`.

## Subdirectories & Boundaries

- `proto_star`: [./proto_star/README.md](./proto_star/README.md). The climate challenge workflow
  (cut-off and quality screen, official score, backtests, pooled-trend forecaster, trials,
  submission package) and the generic sklearn tabular pipeline. Its subpackages are `data/`,
  `models/` and `utils/`.
