"""Model registry.

Every model follows the scikit-learn estimator API (`fit(X, y)`, `predict(X)`),
so training, evaluation and submission code never changes when a new model is
added. To add a model:

    @register("my_model")
    def _my_model(seed: int, **params):
        return MyEstimator(random_state=seed, **params)

then reference it in a config as `model: {name: my_model, params: {...}}`.
Deep learning models can be wrapped in a small class exposing fit/predict.
"""

from collections.abc import Callable
from typing import Any

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

ModelFactory = Callable[..., Any]
_REGISTRY: dict[str, ModelFactory] = {}


def register(name: str) -> Callable[[ModelFactory], ModelFactory]:
    def deco(fn: ModelFactory) -> ModelFactory:
        if name in _REGISTRY:
            raise ValueError(f"model {name!r} already registered")
        _REGISTRY[name] = fn
        return fn

    return deco


def build_model(name: str, seed: int, params: dict[str, Any] | None = None) -> Any:
    if name not in _REGISTRY:
        raise KeyError(f"unknown model {name!r}; available: {available_models()}")
    return _REGISTRY[name](seed=seed, **(params or {}))


def available_models() -> list[str]:
    return sorted(_REGISTRY)


# ---------------------------------------------------------------------------
# Baselines: every new model must beat these on the validation split.
# ---------------------------------------------------------------------------


@register("mean_baseline")
def _mean_baseline(seed: int, **params: Any) -> Pipeline:
    """Predicts the training mean (a "climatology" baseline)."""
    return make_pipeline(DummyRegressor(strategy="mean", **params))


@register("ridge")
def _ridge(seed: int, **params: Any) -> Pipeline:
    return make_pipeline(SimpleImputer(), StandardScaler(), Ridge(random_state=seed, **params))


@register("random_forest")
def _random_forest(seed: int, **params: Any) -> Pipeline:
    return make_pipeline(
        SimpleImputer(), RandomForestRegressor(random_state=seed, n_jobs=-1, **params)
    )


@register("hist_gbm")
def _hist_gbm(seed: int, **params: Any) -> HistGradientBoostingRegressor:
    # Handles missing values natively, no imputer needed.
    return HistGradientBoostingRegressor(random_state=seed, **params)
