"""P05 N-BEATS (Oreshkin et al. 2019, arXiv 1905.10437), trained from scratch on CPU.

One small N-BEATS model per metric, shared by all cities of that metric, maps the
``lookback`` calendar years ending at the cut-off to the next ``horizon`` years.  As in the
paper the point forecast is the median of an ensemble, here over lookback lengths, losses
and seeds.  Paper card: ``papers/2019_oreshkin_nbeats/README.md``.

Fallback: metrics not in ``neural_metrics``, and series whose last lookback window has
fewer than ``min_obs`` observed years, get the ``current_best`` baseline for their metric.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from proto_star.backtest import Forecaster
from proto_star.forecasters._neural_common import (
    build_panel,
    check_metrics,
    forecast_windows,
    inner_split,
    to_frame,
    with_fallback,
)
from proto_star.forecasters.registry import register_forecaster


@register_forecaster(
    "nbeats_p05",
    description="N-BEATS (P05): per-metric MLP residual blocks, median of an ensemble",
    requires=("torch",),
)
def make_nbeats(
    *,
    architecture: str = "generic",
    lookbacks: tuple[int, ...] | list[int] = (14, 21, 28),
    losses: tuple[str, ...] | list[str] = ("l1",),
    seeds: int = 3,
    seed: int = 0,
    width: int = 64,
    layers: int = 2,
    generic_blocks: int = 3,
    trend_blocks: int = 2,
    degree: int = 2,
    max_epochs: int = 200,
    patience: int = 20,
    batch_size: int = 512,
    learning_rate: float = 1e-3,
    weight_decay: float = 0.0,
    min_obs_fraction: float = 0.5,
    holdout: int = 7,
    neural_metrics: list[str] | None = None,
    threads: int = 4,
) -> Forecaster:
    """Build the forecaster.  Every argument comes from the trial config's ``params``."""
    metrics = check_metrics(neural_metrics)
    lookback_list = [int(v) for v in lookbacks]
    loss_list = [str(v) for v in losses]
    if not lookback_list or not loss_list or seeds < 1:
        raise ValueError("lookbacks and losses must be non-empty and seeds >= 1")

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        from proto_star.forecasters import _neural_torch as nt

        nt.configure_torch(threads)
        horizon = max(forecast_years) - cutoff_year
        settings = nt.TrainSettings(max_epochs, patience, batch_size, learning_rate, weight_decay)
        frames = []
        for metric in metrics:
            panel = build_panel(train, cutoff_year, [metric])
            # Only series that can be windowed at the cut-off for *every* lookback get a
            # neural forecast, so each one is the median of the full ensemble.
            members: list[np.ndarray] = []
            target = None
            for lookback in lookback_list:
                min_obs = max(1, int(np.ceil(min_obs_fraction * lookback)))
                fit, valid = inner_split(
                    panel,
                    lookback=lookback,
                    horizon=horizon,
                    min_obs=min_obs,
                    cutoff_year=cutoff_year,
                    holdout=holdout,
                )
                windows = forecast_windows(
                    panel, lookback=lookback, horizon=horizon, min_obs=min_obs
                )
                if len(fit) == 0 or len(windows) == 0:
                    continue
                series = set(windows.series.tolist())
                target = series if target is None else target & series
                model_kwargs: dict[str, int | str] = {
                    "lookback": lookback,
                    "horizon": horizon,
                    "architecture": architecture,
                    "width": width,
                    "layers": layers,
                    "generic_blocks": generic_blocks,
                    "trend_blocks": trend_blocks,
                    "degree": degree,
                }
                for loss_index, loss in enumerate(loss_list):
                    for replica in range(seeds):
                        member_seed = seed + 1000 * replica + 100 * loss_index + lookback
                        model = nt.train_nbeats(
                            fit,
                            valid,
                            seed=member_seed,
                            loss=loss,
                            settings=settings,
                            model_kwargs=model_kwargs,
                        )
                        scaled = nt.predict_nbeats(model, windows)
                        # Members are combined in original units (levels differ by lookback).
                        full = np.full((len(panel.city_ids), horizon), np.nan)
                        full[windows.series] = windows.level[:, None] + (
                            windows.scale[:, None] * scaled
                        )
                        members.append(full)
            if not members or not target:
                continue
            chosen = np.array(sorted(target), dtype=np.int64)
            median = np.median(np.stack(members)[:, chosen, :], axis=0)
            frames.append(
                to_frame(
                    panel,
                    chosen,
                    median,
                    np.zeros(len(chosen)),
                    np.ones(len(chosen)),
                    cutoff_year,
                    forecast_years,
                )
            )
        neural = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        return with_fallback(train, cutoff_year, forecast_years, neural)

    return forecast
