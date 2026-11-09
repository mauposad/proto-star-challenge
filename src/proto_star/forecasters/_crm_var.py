"""Layer 3 of the Coupled Regional Model: a sparse VAR(1) over regional anomalies.

``z[t]`` holds, for every region and metric, the mean over that region's cities of each city's
departure from its own Layer-2 baseline (the trend line for temperature and CDD, the window
mean for the other metrics). A lasso fit of ``z[t] = A z[t-1]`` gives one interaction per entry
of ``A``; the forecast shift at lead ``h`` is ``damping * A^h z[cutoff]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class VarFit:
    """A fitted sparse VAR(1), in standardized units, with the scales to undo it."""

    columns: pd.MultiIndex  # (region, metric)
    coefficients: np.ndarray  # A: rows = target, columns = predictor
    scale: np.ndarray  # std of each column, original units
    start: np.ndarray  # z at the cut-off year, standardized
    n_years: int

    def shifts(self, horizons: list[int], damping: float) -> pd.DataFrame:
        """Shift per (region, metric) and lead, in original units."""
        out = {}
        state = self.start.copy()
        for lead in range(1, max(horizons) + 1):
            state = self.coefficients @ state
            if lead in horizons:
                out[lead] = damping * state * self.scale
        return pd.DataFrame(out, index=self.columns)

    def interactions(self, tol: float = 1e-10) -> pd.DataFrame:
        """Non-zero entries of ``A``: target (region, metric), source (region, metric), weight."""
        rows = []
        for i, j in zip(*np.nonzero(np.abs(self.coefficients) > tol), strict=True):
            rows.append(
                {
                    "target_region": self.columns[i][0],
                    "target_metric": self.columns[i][1],
                    "source_region": self.columns[j][0],
                    "source_metric": self.columns[j][1],
                    "coefficient": float(self.coefficients[i, j]),
                }
            )
        return pd.DataFrame(rows)


def regional_panel(residuals: pd.DataFrame, years: range) -> pd.DataFrame:
    """Year x (region, metric) table of mean city residuals, every year in ``years`` present."""
    panel = residuals.pivot_table(
        index="year", columns=["region", "metric"], values="residual", aggfunc="mean"
    )
    return panel.reindex(index=list(years)).sort_index(axis=1)


def fit_sparse_var(panel: pd.DataFrame, *, alpha: float | None, seed: int) -> VarFit:
    """Lasso VAR(1) on the standardized panel. ``alpha=None`` picks it by time-series CV."""
    from sklearn.linear_model import Lasso, LassoCV  # lazy: only Layer 3 needs it
    from sklearn.model_selection import TimeSeriesSplit

    centered = panel - panel.mean()
    spread = centered.std()
    spread = spread.where(spread > 0, 1.0).fillna(1.0)
    scale = spread.to_numpy(dtype=float)
    standardized = centered.div(spread, axis=1).fillna(0.0).to_numpy(dtype=float)
    x, y = standardized[:-1], standardized[1:]
    n_columns = standardized.shape[1]
    coefficients = np.zeros((n_columns, n_columns))
    for target in range(n_columns):
        if alpha is None:
            model = LassoCV(
                cv=TimeSeriesSplit(n_splits=5),
                fit_intercept=False,
                random_state=seed,
                n_jobs=1,
                max_iter=20000,
            )
        else:
            model = Lasso(alpha=alpha, fit_intercept=False, random_state=seed, max_iter=20000)
        model.fit(x, y[:, target])
        coefficients[target] = model.coef_
    return VarFit(
        columns=cast(pd.MultiIndex, panel.columns),
        coefficients=coefficients,
        scale=scale,
        start=standardized[-1],
        n_years=len(standardized),
    )
