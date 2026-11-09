"""Plug-in point for model kinds that trial configs can name under ``models``.

Adding a model kind means adding one module to this package, with nothing else to edit::

    # src/proto_star/forecasters/my_kind.py
    class MyKindSpec(ForecasterSpec):
        window: int = Field(ge=1)

        def describe(self) -> str:
            return f"My model over {self.window} years"


    def build_my_kind(spec: MyKindSpec) -> Forecaster:
        def forecast(train, cutoff_year, forecast_years): ...

        return forecast


    register_kind("my_kind", MyKindSpec, build_my_kind)

and then, in a trial config::

    models:
      my_model_w15: {kind: my_kind, params: {window: 15}}

Modules are found automatically, so parallel branches never edit a shared list. A module is
imported whenever any model is looked up: import heavy optional packages (torch) inside the
build function, never at module level. Every forecaster must compute everything from ``train``
(see ``proto_star.backtest``).
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, ValidationError

if TYPE_CHECKING:
    from proto_star.backtest import Forecaster


class ForecasterSpec(BaseModel):
    """Base class for the ``params`` of one model kind. Unknown settings are rejected."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def describe(self) -> str:
        """One line saying what a model with these settings does, for notes and READMEs."""
        raise NotImplementedError(f"{type(self).__name__} must define describe()")


@dataclass(frozen=True)
class ForecasterKind:
    """One entry in :data:`REGISTRY`: a spec model and the function that builds a forecaster."""

    name: str
    spec: type[ForecasterSpec]
    build: Callable[[Any], Forecaster]

    def make_spec(self, params: Mapping[str, Any]) -> ForecasterSpec:
        """Validate ``params`` against this kind's spec, naming the kind if they are wrong."""
        try:
            return self.spec.model_validate(dict(params))
        except ValidationError as error:
            raise ValueError(f"model kind {self.name!r} rejected params: {error}") from error


REGISTRY: dict[str, ForecasterKind] = {}


def register_kind(
    name: str, spec: type[ForecasterSpec], build: Callable[[Any], Forecaster]
) -> ForecasterKind:
    """Add a model kind to :data:`REGISTRY`. Each name can be registered only once."""
    if name in REGISTRY and REGISTRY[name].build is not build:
        raise ValueError(f"model kind {name!r} is already registered")
    REGISTRY[name] = ForecasterKind(name, spec, build)
    return REGISTRY[name]


def load_all() -> dict[str, ForecasterKind]:
    """Import every module in this package and return the filled registry."""
    for module in pkgutil.iter_modules(__path__):
        if not module.name.startswith("_"):
            importlib.import_module(f"{__name__}.{module.name}")
    return REGISTRY


def get_kind(kind: str) -> ForecasterKind:
    """The registered model kind called ``kind``."""
    registry = load_all()
    if kind not in registry:
        raise ValueError(f"unknown model kind {kind!r}; registered kinds: {sorted(registry)}")
    return registry[kind]
