"""P08 DeepAR (Salinas et al. 2020, IJF 36(3); arXiv 1704.04110), trained from scratch on CPU.

One global autoregressive LSTM over every (city, metric) series of ``neural_metrics``, with
metric and city embeddings as item covariates.  Each window is scaled by its context level
and the series' training-fold standard deviation.  Training maximises a Gaussian likelihood
over the whole window with teacher forcing; forecasting draws ``samples`` ancestral sample
paths per seed, pools the paths of all seeds and takes their **median**, since the official
skill is MAE-based.  Paper card: ``papers/2020_salinas_deepar/README.md``.

Fallback: metrics not in ``neural_metrics``, and series whose last context window has fewer
than ``min_obs`` observed years, get the ``current_best`` baseline for their metric.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from proto_star.backtest import Forecaster
from proto_star.climate import METRICS
from proto_star.forecasters._neural_common import (
    Panel,
    Windows,
    build_panel,
    check_metrics,
    forecast_windows,
    inner_split,
    to_frame,
    with_fallback,
)
from proto_star.forecasters.registry import register_forecaster


def _meta(panel: Panel, windows: Windows) -> tuple[np.ndarray, np.ndarray]:
    return panel.metric_index[windows.series], panel.city_index[windows.series]


@register_forecaster(
    "deepar_p08",
    description="DeepAR (P08): global Gaussian LSTM over all series, median of sample paths",
    requires=("torch",),
)
def make_deepar(
    *,
    context: int = 21,
    hidden: int = 32,
    layers: int = 2,
    dropout: float = 0.1,
    metric_dim: int = 4,
    city_dim: int = 4,
    seeds: int = 3,
    seed: int = 0,
    samples: int = 100,
    max_epochs: int = 60,
    patience: int = 8,
    batch_size: int = 256,
    learning_rate: float = 1e-3,
    weight_decay: float = 0.0,
    min_obs_fraction: float = 0.5,
    holdout: int = 7,
    neural_metrics: list[str] | None = None,
    threads: int = 4,
) -> Forecaster:
    """Build the forecaster.  Every argument comes from the trial config's ``params``."""
    metrics = check_metrics(neural_metrics)
    if seeds < 1 or samples < 1:
        raise ValueError("seeds and samples must be >= 1")
    min_obs = max(1, int(np.ceil(min_obs_fraction * context)))

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        from proto_star.forecasters import _neural_torch as nt

        nt.configure_torch(threads)
        horizon = max(forecast_years) - cutoff_year
        settings = nt.TrainSettings(max_epochs, patience, batch_size, learning_rate, weight_decay)
        panel = build_panel(train, cutoff_year, metrics)
        fit, valid = inner_split(
            panel,
            lookback=context,
            horizon=horizon,
            min_obs=min_obs,
            cutoff_year=cutoff_year,
            holdout=holdout,
        )
        windows = forecast_windows(panel, lookback=context, horizon=horizon, min_obs=min_obs)
        if len(fit) == 0 or len(windows) == 0:
            return with_fallback(train, cutoff_year, forecast_years, pd.DataFrame())
        model_kwargs: dict[str, int | float] = {
            "n_metrics": len(METRICS),
            "n_cities": int(panel.city_index.max()) + 1,
            "metric_dim": metric_dim,
            "city_dim": city_dim,
            "hidden": hidden,
            "layers": layers,
            "dropout": dropout,
        }
        paths = []
        for replica in range(seeds):
            member_seed = seed + 1000 * replica
            model = nt.train_deepar(
                fit,
                valid,
                _meta(panel, fit),
                _meta(panel, valid),
                seed=member_seed,
                settings=settings,
                model_kwargs=model_kwargs,
            )
            paths.append(
                nt.sample_deepar(
                    model,
                    windows,
                    _meta(panel, windows),
                    horizon=horizon,
                    samples=samples,
                    seed=member_seed + 1,
                )
            )
        median = np.median(np.concatenate(paths, axis=1), axis=1)
        neural = to_frame(
            panel,
            windows.series,
            median,
            windows.level,
            windows.scale,
            cutoff_year,
            forecast_years,
        )
        return with_fallback(train, cutoff_year, forecast_years, neural)

    return forecast
