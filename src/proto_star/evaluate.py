"""Evaluation metrics. Keep the leaderboard's official metric first in configs."""

from collections.abc import Callable

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

Metric = Callable[[np.ndarray, np.ndarray], float]

METRICS: dict[str, Metric] = {
    "mae": lambda y, p: float(mean_absolute_error(y, p)),
    "rmse": lambda y, p: float(np.sqrt(mean_squared_error(y, p))),
    "r2": lambda y, p: float(r2_score(y, p)),
}


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, names: list[str]) -> dict[str, float]:
    unknown = set(names) - set(METRICS)
    if unknown:
        raise KeyError(f"unknown metrics {sorted(unknown)}; available: {sorted(METRICS)}")
    return {name: METRICS[name](y_true, y_pred) for name in names}
