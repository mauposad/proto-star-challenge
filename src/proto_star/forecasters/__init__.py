"""Model-based forecasters, one module per method, discovered automatically.

Drop a module in this package that calls :func:`register_forecaster` and its forecaster can
be named in a trial config.  Nothing else needs editing.  See ``registry.py`` for the rules.
"""

from __future__ import annotations

import importlib
import pkgutil

from proto_star.forecasters.registry import (
    REGISTRY,
    Forecaster,
    ForecasterFactory,
    RegisteredForecaster,
    register_forecaster,
)

__all__ = [
    "REGISTRY",
    "Forecaster",
    "ForecasterFactory",
    "RegisteredForecaster",
    "load_all",
    "register_forecaster",
]


def load_all() -> dict[str, RegisteredForecaster]:
    """Import every forecaster module in this package and return the filled registry."""
    for module in pkgutil.iter_modules(__path__):
        if module.name != "registry" and not module.name.startswith("_"):
            importlib.import_module(f"{__name__}.{module.name}")
    return REGISTRY
