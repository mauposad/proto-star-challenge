"""Registry of model-based forecasters that trial configs can name.

A forecaster module in this package registers a *factory*: a function that takes the
hyperparameters from the trial config as keyword arguments and returns a
:data:`proto_star.backtest.Forecaster`.  Example::

    @register_forecaster(
        "my_model",
        description="What it does, in one line",
        requires=("statsmodels",),
    )
    def make_my_model(*, window: int = 15, seed: int = 0) -> Forecaster:
        def forecast(train, cutoff_year, forecast_years):
            ...
        return forecast

Modules are discovered automatically (see ``proto_star.forecasters``), so adding a model
means adding one file.  Import heavy optional packages (torch) inside the factory, never at
module level: every module is imported whenever any forecaster is looked up.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

Forecaster = Callable[[pd.DataFrame, int, list[int]], pd.DataFrame]
ForecasterFactory = Callable[..., Forecaster]


@dataclass(frozen=True)
class RegisteredForecaster:
    """One entry in :data:`REGISTRY`."""

    name: str
    factory: ForecasterFactory
    description: str
    # Distribution names the forecaster needs beyond proto-star's core dependencies.
    # They are pinned into a submission package's code/requirements.txt.
    requires: tuple[str, ...] = field(default_factory=tuple)

    def build(self, params: Mapping[str, Any] | None = None) -> Forecaster:
        """Call the factory with ``params`` and say which forecaster failed if it rejects them."""
        try:
            return self.factory(**dict(params or {}))
        except TypeError as error:
            message = f"forecaster {self.name!r} rejected params {params}: {error}"
            raise ValueError(message) from error


REGISTRY: dict[str, RegisteredForecaster] = {}


def register_forecaster(
    name: str, *, description: str, requires: tuple[str, ...] = ()
) -> Callable[[ForecasterFactory], ForecasterFactory]:
    """Decorator adding a forecaster factory to :data:`REGISTRY` under ``name``."""

    def decorate(factory: ForecasterFactory) -> ForecasterFactory:
        if name in REGISTRY and REGISTRY[name].factory is not factory:
            raise ValueError(f"forecaster {name!r} is already registered")
        REGISTRY[name] = RegisteredForecaster(name, factory, description, tuple(requires))
        return factory

    return decorate
