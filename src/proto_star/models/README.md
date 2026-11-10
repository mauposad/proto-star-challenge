# proto_star.models

## Overview

The model registry for `proto_star`. A model is a factory function registered
under a string name. The factory returns a scikit-learn style estimator (or
`Pipeline`). Training looks up the model by the name in the experiment config,
so adding a model does not change training, evaluation, or submission code
(`[registry.py:module docstring]`). This directory has no subdirectories.

Callers outside this package:

- `src/proto_star/train.py` `[train.py:train]` calls
  `build_model(cfg.model.name, cfg.seed, cfg.model.params)` and then `.fit(...)`.
- `src/proto_star/cli.py` `[cli.py:models]` prints `available_models()`, one per
  line (`uv run proto-star models`).

## Interface

Public package API (`[__init__.py:__all__]` = `["available_models", "build_model"]`):

- `build_model(name: str, seed: int, params: dict[str, Any] | None = None) -> Any`
  `[registry.py:build_model]`: returns `_REGISTRY[name](seed=seed, **(params or {}))`,
  a new estimator on every call.
- `available_models() -> list[str]` `[registry.py:available_models]`: returns
  `sorted(_REGISTRY)`.

Module-level symbols in `proto_star.models.registry` (not re-exported by `__init__.py`):

- `register(name: str) -> Callable[[ModelFactory], ModelFactory]`
  `[registry.py:register]`: a decorator factory. It stores the decorated function
  in `_REGISTRY` under `name` and returns the function unchanged.
- `ModelFactory = Callable[..., Any]` `[registry.py:ModelFactory]`: the factory type alias.
- `_REGISTRY: dict[str, ModelFactory]` `[registry.py:_REGISTRY]`: private name-to-factory map.

Registered models (factory signature `(seed: int, **params: Any)`):

| Name | Factory | Returns | Where `seed` goes | Where `**params` go |
|---|---|---|---|---|
| `mean_baseline` | `[registry.py:_mean_baseline]` | `Pipeline[DummyRegressor(strategy="mean")]` | unused | `DummyRegressor` |
| `ridge` | `[registry.py:_ridge]` | `Pipeline[SimpleImputer, StandardScaler, Ridge]` | `Ridge(random_state=seed)` | `Ridge` |
| `random_forest` | `[registry.py:_random_forest]` | `Pipeline[SimpleImputer, RandomForestRegressor(n_jobs=-1)]` | `RandomForestRegressor(random_state=seed)` | `RandomForestRegressor` |
| `hist_gbm` | `[registry.py:_hist_gbm]` | bare `HistGradientBoostingRegressor` (no `Pipeline`, no imputer) | `random_state=seed` | `HistGradientBoostingRegressor` |

To add a model, follow the pattern in `[registry.py:module docstring]`:

```python
@register("my_model")
def _my_model(seed: int, **params):
    return MyEstimator(random_state=seed, **params)
```

Then reference it in a config as `model: {name: my_model, params: {...}}`.

## Invariants

- Model names are unique. Registering a name that already exists raises
  `ValueError("model '<name>' already registered")` `[registry.py:register]`. For
  decorated factories this check runs at import time. There is no function to
  unregister or override a name.
- An unknown name raises `KeyError("unknown model '<name>'; available: [...]")`,
  and the message lists the sorted registered names `[registry.py:build_model]`.
- `params=None` (or any falsy `params`) becomes `{}` `[registry.py:build_model]`.
- `seed` is always passed as the keyword `seed=`, so a `params` dict containing
  `seed` raises `TypeError` `[registry.py:build_model]`. The factories hard-code some
  keywords, so these `params` keys also raise `TypeError`: `random_state` for
  `[registry.py:_ridge]`, `[registry.py:_random_forest]`, and
  `[registry.py:_hist_gbm]`; `n_jobs` for `[registry.py:_random_forest]`; and
  `strategy` for `[registry.py:_mean_baseline]`. These errors come from the shape
  of the calls; there is no explicit validation.
- `available_models()` returns names in alphabetical order, not registration order
  `[registry.py:available_models]`.
- Every model must expose the scikit-learn `fit(X, y)` / `predict(X)` API
  (`[registry.py:module docstring]`). The return type is `Any` and the code does
  not check this. `[tests/test_pipeline.py:test_every_registered_model_builds]` is
  the only test covering every name, by asserting `hasattr(model, "fit")` and
  `hasattr(model, "predict")`. `[tests/test_pipeline.py:test_train_then_predict_end_to_end]`
  runs a real fit/predict, but only for `ridge` (the model in `tests/conftest.py`).
- Per the comment above the baselines, "every new model must beat these on the
  validation split" (`[registry.py:comment above _mean_baseline]`). This is policy
  stated in prose; the code does not enforce it.
- Deep learning models can be wrapped in a small class that exposes fit/predict
  (`[registry.py:module docstring]`).

## Side Effects

- Importing `proto_star.models` (whose `__init__.py` runs
  `from proto_star.models.registry import available_models, build_model`) mutates the
  module-global `_REGISTRY` four times
  through the `@register` decorators, in this order: `mean_baseline`, `ridge`,
  `random_forest`, `hist_gbm` `[registry.py:register]`.
- Each later call to `register(name)(fn)` also mutates the global `_REGISTRY`
  `[registry.py:register]`.
- `build_model` and `available_models` only read `_REGISTRY`
  `[registry.py:build_model]`, `[registry.py:available_models]`.
- `random_forest` hard-codes `n_jobs=-1`, so the returned estimator uses all CPU
  cores when it is fit or used to predict. The factory itself starts no work
  `[registry.py:_random_forest]`.
- No disk I/O, network access, logging, environment-variable reads, or global RNG
  seeding. Randomness is set only through the `random_state=seed` arguments
  `[registry.py]`.

## Verification

- Run: `make check` (lint + mypy + tests)
- Targeted: `uv run pytest tests/test_pipeline.py -q`
