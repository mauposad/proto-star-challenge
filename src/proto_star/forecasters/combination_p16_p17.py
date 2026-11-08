"""Forecast combinations after P16 (Makridakis et al. 2018, M4) and P17 (Smith & Wallis 2009,
"the forecast combination puzzle"), with P18 (the 50-year combination review) as context.

Each combined metric gets the row-wise combination of several *member* forecasters, each of
them an ordinary registered forecaster, built baseline, or ``current_best`` called through
:func:`proto_star.backtest.resolve_forecaster` (their code is not copied here).  Metrics not
combined come from ``rest`` (``current_best`` by default).

Combiners (``method``):

* ``mean``: equal weights, the P16/P17 recommendation.
* ``median``: row-wise median of the members.
* ``trimmed``: drop the one member farthest from the row's median, then average the rest.  A
  symmetric trimmed mean of four members equals their median, so this is the trimmed variant.
* ``inverse_mse``: Bates-Granger weights ``1 / MSE`` per metric, normalized to sum to one, with
  the MSE measured by hindcasts *inside the training years* (pseudo-origins ``cutoff - step``,
  ``cutoff - 2 * step``, ...).  The P17 contrast: estimated weights versus equal weights.

Member forecasts are memoized per (member spec, cut-off, forecast years, training data), so the
combiners in one trial share one fit of each member.  Members are deterministic given their
seeds (from the config), so the memo changes run time, never results.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from proto_star.climate import METRICS, annual_to_long
from proto_star.forecasters.registry import Forecaster, register_forecaster

METHODS = ("mean", "median", "trimmed", "inverse_mse")
_KEY = ["city_id", "year", "metric"]
# One memo entry is one member's forecast for one fold: a few thousand rows.
_MEMO: dict[tuple[str, int, tuple[int, ...], int], pd.DataFrame] = {}


def clear_member_cache() -> None:
    """Forget memoized member forecasts (tests use this to time or isolate runs)."""
    _MEMO.clear()


def _spec_key(spec: Mapping[str, Any]) -> str:
    return json.dumps(
        {"forecaster": spec["forecaster"], "params": spec.get("params") or {}},
        sort_keys=True,
        default=str,
    )


def _fingerprint(train: pd.DataFrame) -> int:
    return int(pd.util.hash_pandas_object(train, index=False).sum())


def build_member(spec: Mapping[str, Any]) -> Forecaster:
    """Resolve ``{forecaster: <name>, params: {...}}`` through the registry or the baselines."""
    from proto_star.backtest import resolve_forecaster  # lazy: backtest imports the registry

    unknown = sorted(set(spec) - {"forecaster", "params"})
    if unknown or "forecaster" not in spec:
        raise ValueError(f"member spec needs only 'forecaster' and 'params', got {dict(spec)}")
    name = str(spec["forecaster"])
    params = dict(spec.get("params") or {})
    if not params:
        return resolve_forecaster(name)
    return resolve_forecaster(
        "_member", variants={"_member": {"forecaster": name, "params": params}}
    )


def run_member(
    spec: Mapping[str, Any],
    forecaster: Forecaster,
    train: pd.DataFrame,
    cutoff_year: int,
    forecast_years: Sequence[int],
    *,
    cache: bool = True,
) -> pd.DataFrame:
    """One member's forecast, memoized when ``cache`` is set."""
    key = (_spec_key(spec), int(cutoff_year), tuple(int(y) for y in forecast_years), 0)
    if cache:
        key = (*key[:3], _fingerprint(train))
        if key in _MEMO:
            return _MEMO[key].copy()
    rows = forecaster(train, cutoff_year, list(forecast_years))[[*_KEY, "predicted_value"]]
    rows = rows.reset_index(drop=True)
    if cache:
        _MEMO[key] = rows.copy()
    return rows


def member_matrix(frames: Mapping[str, pd.DataFrame], metric: str) -> pd.DataFrame:
    """Rows of ``metric`` with one column per member (inner join: rows every member has)."""
    wide: pd.DataFrame | None = None
    for name, frame in frames.items():
        part = frame.loc[frame["metric"] == metric, [*_KEY, "predicted_value"]]
        part = part.rename(columns={"predicted_value": name})
        wide = part if wide is None else wide.merge(part, on=_KEY, how="inner")
    if wide is None:
        raise ValueError("a combination needs at least one member")
    return wide.reset_index(drop=True)


def combine_values(
    values: np.ndarray, method: str, weights: np.ndarray | None = None
) -> np.ndarray:
    """Combine an ``(n_rows, n_members)`` array row by row."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if values.ndim != 2 or values.shape[1] == 0:
        raise ValueError("values must be a 2-D array with at least one member column")
    if method == "mean":
        return np.asarray(values.mean(axis=1), dtype=float)
    if method == "median":
        return np.asarray(np.median(values, axis=1), dtype=float)
    if method == "trimmed":
        if values.shape[1] < 3:
            raise ValueError("the trimmed combination needs at least 3 members")
        distance = np.abs(values - np.median(values, axis=1, keepdims=True))
        drop = np.argmax(distance, axis=1)  # ties: the first such member
        keep = np.ones_like(values, dtype=bool)
        keep[np.arange(len(values)), drop] = False
        return np.asarray((values * keep).sum(axis=1) / keep.sum(axis=1), dtype=float)
    if weights is None or weights.shape != (values.shape[1],):
        raise ValueError("inverse_mse needs one weight per member")
    return np.asarray(values @ weights, dtype=float)


def inverse_mse_weights(
    specs: Mapping[str, Mapping[str, Any]],
    members: Mapping[str, Forecaster],
    train: pd.DataFrame,
    cutoff_year: int,
    *,
    metric: str,
    horizon: int,
    n_origins: int,
    step: int,
    cache: bool = True,
) -> dict[str, float]:
    """Bates-Granger weights for ``metric`` from hindcasts on years ``<= cutoff_year`` only.

    Each pseudo-origin ``o = cutoff - step * j`` (``j = 1 .. n_origins``) forecasts years
    ``o + 1 .. min(o + horizon, cutoff)`` from ``train`` rows up to ``o``.  Errors are pooled
    over the origins and over rows every member forecast.
    """
    history = annual_to_long(train, cutoff_year=cutoff_year)
    truth = history.loc[history["metric"] == metric, [*_KEY, "actual_value"]]
    squared: dict[str, list[np.ndarray]] = {name: [] for name in members}
    for j in range(1, n_origins + 1):
        origin = cutoff_year - step * j
        years = list(range(origin + 1, min(origin + horizon, cutoff_year) + 1))
        past = train.loc[train["Year"] <= origin].copy()
        if past.empty or not years:
            continue
        frames = {
            name: run_member(specs[name], member, past, origin, years, cache=cache)
            for name, member in members.items()
        }
        wide = member_matrix(frames, metric).merge(truth, on=_KEY, how="inner")
        for name in members:
            squared[name].append((wide[name] - wide["actual_value"]).to_numpy(dtype=float) ** 2)
    mse = {
        name: float(np.concatenate(parts).mean()) if parts and sum(map(len, parts)) else np.nan
        for name, parts in squared.items()
    }
    if not all(np.isfinite(v) and v > 0 for v in mse.values()):
        raise ValueError(f"cannot weight {metric} at cutoff {cutoff_year}: hindcast MSE {mse}")
    inverse = {name: 1.0 / value for name, value in mse.items()}
    total = sum(inverse.values())
    return {name: value / total for name, value in inverse.items()}


def make_forecast_combination(
    *,
    members: Mapping[str, Mapping[str, Any]],
    combine: Mapping[str, Sequence[str]],
    method: str = "mean",
    rest: str = "current_best",
    n_origins: int = 2,
    step: int = 7,
    cache: bool = True,
) -> Forecaster:
    """Combine member forecasts per metric.

    ``members`` maps a short member name to ``{forecaster: <name>, params: {...}}``.
    ``combine`` maps each combined metric to the member names to combine for it; every other
    metric comes from ``rest``.  ``n_origins`` and ``step`` set the in-train hindcast that
    ``method: inverse_mse`` uses; the other methods ignore them.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    unknown_metrics = sorted(set(combine) - set(METRICS))
    if unknown_metrics or not combine:
        raise ValueError(f"combine must map some of {list(METRICS)}, got {sorted(combine)}")
    for metric, names in combine.items():
        missing = sorted(set(names) - set(members))
        if missing or not names:
            raise ValueError(f"combine[{metric!r}] names unknown or no members: {missing}")
        if method == "trimmed" and len(names) < 3:
            raise ValueError(f"trimmed needs at least 3 members for {metric!r}")
    if n_origins < 1 or step < 1:
        raise ValueError("n_origins and step must be >= 1")
    used = sorted({name for names in combine.values() for name in names})
    specs = {name: dict(members[name]) for name in used}
    built = {name: build_member(spec) for name, spec in specs.items()}
    rest_spec: dict[str, Any] = {"forecaster": rest}
    rest_forecaster = build_member(rest_spec)

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        frames = {
            name: run_member(
                specs[name], built[name], train, cutoff_year, forecast_years, cache=cache
            )
            for name in used
        }
        base = run_member(
            rest_spec, rest_forecaster, train, cutoff_year, forecast_years, cache=cache
        )
        out = [base.loc[~base["metric"].isin(list(combine))]]
        horizon = max(forecast_years) - cutoff_year
        for metric, names in combine.items():
            chosen = {name: frames[name] for name in names}
            wide = member_matrix(chosen, metric)
            weights = None
            if method == "inverse_mse":
                found = inverse_mse_weights(
                    specs,
                    {name: built[name] for name in names},
                    train,
                    cutoff_year,
                    metric=metric,
                    horizon=horizon,
                    n_origins=n_origins,
                    step=step,
                    cache=cache,
                )
                weights = np.array([found[name] for name in names])
            values = wide[list(names)].to_numpy(dtype=float)
            combined = wide[_KEY].copy()
            combined["predicted_value"] = combine_values(values, method, weights)
            out.append(combined)
        result = pd.concat(out, ignore_index=True)
        # Rows some member lacked (none in practice: every member fills its own gaps) fall back.
        covered = base[_KEY].merge(result[_KEY], on=_KEY, how="left", indicator=True)
        gaps = covered.loc[covered["_merge"] == "left_only", _KEY]
        if not gaps.empty:
            result = pd.concat([result, base.merge(gaps, on=_KEY)], ignore_index=True)
        return result

    return forecast


register_forecaster(
    "forecast_combination",
    description=(
        "Per-metric combination of registered forecasters (P16/P17): equal-weight mean, "
        "median, trimmed mean or in-train inverse-MSE weights; current_best for the rest"
    ),
)(make_forecast_combination)

# Same factory; the separate name pins torch into a submission package's requirements when a
# member is a neural forecaster (DeepAR).
register_forecaster(
    "forecast_combination_torch",
    description=(
        "Per-metric combination of registered forecasters (P16/P17) with a torch member: "
        "equal-weight mean, median, trimmed mean or in-train inverse-MSE weights"
    ),
    requires=("torch",),
)(make_forecast_combination)
