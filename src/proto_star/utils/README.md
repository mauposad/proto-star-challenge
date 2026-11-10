# proto_star.utils

## Overview

Small cross-cutting helpers shared by the training and prediction entry points:
a logger factory (`logging.py`) and a global RNG seeding helper (`seed.py`).
The package `__init__.py` is empty (0 bytes), so there are no package-level
re-exports and no `__all__`; import from the submodules directly.

Known callers (repository paths):

- `src/proto_star/train.py` imports `get_logger` and `set_seed`; it calls
  `get_logger(__name__)` at module level and `set_seed(cfg.seed)` inside the
  training flow.
- `src/proto_star/predict.py` imports `get_logger` and calls
  `get_logger(__name__)` at module level.

## Interface

- `[logging.py:get_logger]` `get_logger(name: str = "proto_star") -> logging.Logger`:
  returns `logging.getLogger(name)`, attaching a stderr `StreamHandler` with a
  formatter and setting level `INFO` only if the logger has no handlers yet.
  No docstring.
- `[seed.py:set_seed]` `set_seed(seed: int) -> None`: seeds Python `random`,
  NumPy's legacy global RNG, sets `PYTHONHASHSEED`, and seeds PyTorch (CPU and
  all CUDA devices) when `torch` is importable. Docstring: "Seed every RNG we
  use so runs are reproducible."
- `[__init__.py]` Empty module; no symbols.

## Invariants

- `[logging.py:get_logger]` Handler setup is idempotent per logger name, guarded
  by `if not logger.handlers:`. Repeated calls with the same name add no extra
  handler and do not reset the level.
- `[logging.py:get_logger]` `logger.setLevel(logging.INFO)` runs only inside the
  `if not logger.handlers:` branch; a logger that already had handlers keeps its
  existing level.
- `[logging.py:get_logger]` The guard checks only the named logger's own
  `handlers`, not its ancestors'. `logger.propagate` is never set, so it keeps
  the stdlib default (`True`) and records also reach ancestor handlers.
- `[logging.py:get_logger]` The default logger name is `"proto_star"` (parameter
  default `name: str = "proto_star"`).
- `[seed.py:set_seed]` PyTorch is optional: `try: import torch` /
  `except ImportError: return` skips torch seeding silently when torch is not
  installed. Other exceptions are not caught.
- `[seed.py:set_seed]` `torch` is imported lazily inside the function; only
  `os`, `random`, and `numpy as np` are imported at module top level.
- `[seed.py:set_seed]` Only NumPy's legacy global RNG is seeded
  (`np.random.seed(seed)`); `np.random.default_rng` Generator instances are not
  affected. No torch determinism flags (cuDNN or
  `torch.use_deterministic_algorithms`) are set.
- `[logging.py]` The module file name shadows the stdlib `logging` module. Its
  `import logging` is absolute and resolves to the stdlib as long as
  `src/proto_star/utils/` itself is not on `sys.path`. Do not run scripts with
  this directory as the working or script directory.

## Side Effects

- `[logging.py:get_logger]` Mutates global logging state for the named logger,
  only when it has no handlers: adds one `logging.StreamHandler()` (no
  arguments, so it writes to `sys.stderr`) using
  `logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%H:%M:%S")`,
  and sets the level to `logging.INFO`. Subsequent log calls on that logger
  write to stderr.
- `[seed.py:set_seed]` Mutates the global stdlib RNG state via
  `random.seed(seed)`.
- `[seed.py:set_seed]` Mutates NumPy's legacy global RNG state via
  `np.random.seed(seed)` (inline comment:
  `# noqa: NPY002 - seeds legacy global RNG used by some libraries`).
- `[seed.py:set_seed]` Sets the process environment variable
  `os.environ["PYTHONHASHSEED"] = str(seed)`. Python reads `PYTHONHASHSEED`
  only at interpreter startup, so this does not change hash randomization in the
  current process; it is inherited by child processes.
- `[seed.py:set_seed]` If `torch` is importable: imports it (adding it to
  `sys.modules`), then mutates torch's global CPU RNG via
  `torch.manual_seed(seed)` and every CUDA device RNG via
  `torch.cuda.manual_seed_all(seed)`.
- `[seed.py:set_seed]` No disk, network, or stdout output.

## Verification

- Run: `make check` (ruff lint and format check, mypy, pytest with coverage).
- No test under `tests/` imports `proto_star.utils` directly. The helpers are
  exercised indirectly by `tests/test_pipeline.py`, which imports
  `proto_star.train.train` and `proto_star.predict.predict`.
