"""PyTorch parts of the neural forecasters: N-BEATS (P05) and DeepAR (P08).

Imported lazily from the forecast functions only, so ``torch`` is needed just when a neural
forecaster actually runs.  Both models are small, trained from scratch on CPU, with early
stopping on an inner split inside the training fold (see ``_neural_common.inner_split``).

Determinism: every member reseeds torch from the config seed, uses its own
``torch.Generator`` for shuffling and sampling, and runs with
``torch.use_deterministic_algorithms(True)`` and a fixed thread count, so a rebuild on the
same machine and thread count reproduces the forecasts bit for bit.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor, nn

from proto_star.forecasters._neural_common import Windows

# 4 research agents share 20 cores: never use more than this many threads.
MAX_THREADS = 5


def configure_torch(threads: int) -> None:
    """Fix the thread count and switch on deterministic kernels (process-wide torch state)."""
    if not 1 <= threads <= MAX_THREADS:
        raise ValueError(f"threads must be between 1 and {MAX_THREADS}, got {threads}")
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)


@dataclass(frozen=True)
class TrainSettings:
    """Optimisation settings shared by both models (all from the trial config)."""

    max_epochs: int
    patience: int
    batch_size: int
    learning_rate: float
    weight_decay: float


def _tensor(array: np.ndarray) -> Tensor:
    return torch.from_numpy(np.ascontiguousarray(array))


# ---------------------------------------------------------------- N-BEATS (Oreshkin 2019)


class NBeatsBlock(nn.Module):
    """FC stack -> expansion coefficients -> backcast and forecast through a basis.

    ``kind="generic"``: learnt linear bases.  ``kind="trend"``: fixed polynomial bases of
    degree ``degree`` (the paper's interpretable trend block).  The observed-value mask is
    concatenated to the block input so the FC stack can tell gaps from zeros.
    """

    def __init__(
        self, lookback: int, horizon: int, width: int, layers: int, kind: str, degree: int
    ) -> None:
        super().__init__()
        stack: list[nn.Module] = [nn.Linear(2 * lookback, width), nn.ReLU()]
        for _ in range(layers - 1):
            stack += [nn.Linear(width, width), nn.ReLU()]
        self.fc = nn.Sequential(*stack)
        self.kind = kind
        if kind == "generic":
            self.theta_b = nn.Linear(width, width, bias=False)
            self.theta_f = nn.Linear(width, width, bias=False)
            self.basis_b = nn.Linear(width, lookback)
            self.basis_f = nn.Linear(width, horizon)
        elif kind == "trend":
            self.theta_b = nn.Linear(width, degree + 1, bias=False)
            self.theta_f = nn.Linear(width, degree + 1, bias=False)
            powers = torch.arange(degree + 1, dtype=torch.float32)[:, None]
            self.register_buffer("poly_b", (torch.arange(lookback) / lookback) ** powers)
            self.register_buffer("poly_f", (torch.arange(horizon) / horizon) ** powers)
        else:
            raise ValueError(f"unknown N-BEATS block kind {kind!r}")

    def forward(self, residual: Tensor, mask: Tensor) -> tuple[Tensor, Tensor]:
        hidden = self.fc(torch.cat([residual, mask], dim=1))
        if self.kind == "generic":
            return self.basis_b(self.theta_b(hidden)), self.basis_f(self.theta_f(hidden))
        return self.theta_b(hidden) @ self.poly_b, self.theta_f(hidden) @ self.poly_f


class NBeats(nn.Module):
    """Doubly residual stack of blocks: each removes its backcast, all forecasts add up.

    ``architecture="generic"``: ``generic_blocks`` generic blocks.
    ``architecture="interpretable"``: a trend stack (``trend_blocks`` blocks sharing weights,
    as in the paper) followed by a generic stack in place of the seasonality stack.
    """

    def __init__(
        self,
        *,
        lookback: int,
        horizon: int,
        architecture: str,
        width: int,
        layers: int,
        generic_blocks: int,
        trend_blocks: int,
        degree: int,
    ) -> None:
        super().__init__()
        if architecture not in ("generic", "interpretable"):
            raise ValueError(f"architecture must be 'generic' or 'interpretable': {architecture}")
        blocks: list[nn.Module] = []
        if architecture == "interpretable":
            trend = NBeatsBlock(lookback, horizon, width, layers, "trend", degree)
            blocks += [trend] * trend_blocks  # same module repeated: shared weights
        blocks += [
            NBeatsBlock(lookback, horizon, width, layers, "generic", degree)
            for _ in range(generic_blocks)
        ]
        self.blocks = nn.ModuleList(blocks)
        self.horizon = horizon

    def forward(self, x: Tensor, mask: Tensor) -> Tensor:
        residual = x
        forecast = torch.zeros(x.shape[0], self.horizon)
        for block in self.blocks:
            backcast, block_forecast = block(residual, mask)
            residual = (residual - backcast) * mask
            forecast = forecast + block_forecast
        return forecast


def _masked_loss(pred: Tensor, target: Tensor, mask: Tensor, loss: str) -> Tensor:
    error = (pred - target) * mask
    per_point = error.abs() if loss == "l1" else error.pow(2)
    return per_point.sum() / mask.sum().clamp(min=1.0)


def train_nbeats(
    fit: Windows,
    valid: Windows,
    *,
    seed: int,
    loss: str,
    settings: TrainSettings,
    model_kwargs: dict[str, int | str],
) -> NBeats:
    """Fit one ensemble member; keep the weights with the lowest inner-validation MAE."""
    if loss not in ("l1", "l2"):
        raise ValueError(f"N-BEATS loss must be 'l1' or 'l2', got {loss!r}")
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)
    model = NBeats(**model_kwargs)  # type: ignore[arg-type]  # kwargs checked by NBeats
    optimiser = torch.optim.Adam(
        model.parameters(), lr=settings.learning_rate, weight_decay=settings.weight_decay
    )
    x, xm, y, ym = (_tensor(a) for a in (fit.x, fit.x_mask, fit.y, fit.y_mask))
    vx, vxm, vy, vym = (_tensor(a) for a in (valid.x, valid.x_mask, valid.y, valid.y_mask))
    best_score, best_state, stale = float("inf"), copy.deepcopy(model.state_dict()), 0
    for _ in range(settings.max_epochs):
        model.train()
        order = torch.randperm(len(fit), generator=generator)
        for start in range(0, len(fit), settings.batch_size):
            batch = order[start : start + settings.batch_size]
            optimiser.zero_grad()
            value = _masked_loss(model(x[batch], xm[batch]), y[batch], ym[batch], loss)
            value.backward()
            optimiser.step()
        if len(valid) == 0:
            best_state = copy.deepcopy(model.state_dict())
            continue
        model.eval()
        with torch.no_grad():
            score = float(_masked_loss(model(vx, vxm), vy, vym, "l1"))
        if score < best_score - 1e-7:
            best_score, best_state, stale = score, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
            if stale >= settings.patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model


def predict_nbeats(model: NBeats, windows: Windows) -> np.ndarray:
    """Scaled point forecasts, shape (N, H)."""
    with torch.no_grad():
        return model(_tensor(windows.x), _tensor(windows.x_mask)).numpy().astype(float)


# ---------------------------------------------------------------- DeepAR (Salinas 2020)


class DeepAR(nn.Module):
    """Autoregressive LSTM with a Gaussian output, shared across every series.

    Step input: the previous scaled value, whether it was observed, and learnt embeddings of
    the metric and (optionally) the city, the paper's item covariates.
    """

    def __init__(
        self,
        *,
        n_metrics: int,
        n_cities: int,
        metric_dim: int,
        city_dim: int,
        hidden: int,
        layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.metric_embedding = nn.Embedding(n_metrics, metric_dim)
        self.city_embedding = nn.Embedding(n_cities, city_dim) if city_dim > 0 else None
        self.lstm = nn.LSTM(
            2 + metric_dim + city_dim,
            hidden,
            num_layers=layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0.0,
        )
        self.mu = nn.Linear(hidden, 1)
        self.sigma = nn.Linear(hidden, 1)

    def _covariates(self, metric: Tensor, city: Tensor, steps: int) -> Tensor:
        parts = [self.metric_embedding(metric)]
        if self.city_embedding is not None:
            parts.append(self.city_embedding(city))
        return torch.cat(parts, dim=1)[:, None, :].expand(-1, steps, -1)

    def forward(
        self,
        prev: Tensor,
        observed: Tensor,
        metric: Tensor,
        city: Tensor,
        state: tuple[Tensor, Tensor] | None = None,
    ) -> tuple[Tensor, Tensor, tuple[Tensor, Tensor]]:
        steps = prev.shape[1]
        inputs = torch.cat(
            [prev[..., None], observed[..., None], self._covariates(metric, city, steps)], dim=2
        )
        output, new_state = self.lstm(inputs, state)
        mu = self.mu(output).squeeze(-1)
        sigma = nn.functional.softplus(self.sigma(output)).squeeze(-1) + 1e-3
        return mu, sigma, new_state


def _deepar_sequences(windows: Windows) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    """Teacher-forcing inputs and targets over the whole window (context + prediction)."""
    values = np.concatenate([windows.x, windows.y], axis=1)
    masks = np.concatenate([windows.x_mask, windows.y_mask], axis=1)
    return (
        _tensor(values[:, :-1]),
        _tensor(masks[:, :-1]),
        _tensor(values[:, 1:]),
        _tensor(masks[:, 1:]),
    )


def _rollout(
    model: DeepAR,
    windows: Windows,
    metric: Tensor,
    city: Tensor,
    horizon: int,
    *,
    samples: int,
    generator: torch.Generator | None,
) -> Tensor:
    """Condition on the inputs, then step forward ``horizon`` years.

    ``generator=None`` feeds back the mean (used for early stopping); otherwise draws
    ``samples`` ancestral sample paths.  Returns (N, samples, H).
    """
    n = len(windows)
    repeat = 1 if generator is None else samples
    prev = _tensor(windows.x).repeat_interleave(repeat, dim=0)
    observed = _tensor(windows.x_mask).repeat_interleave(repeat, dim=0)
    metric, city = metric.repeat_interleave(repeat), city.repeat_interleave(repeat)
    mu, sigma, state = model(prev, observed, metric, city)
    ones = torch.ones(n * repeat, 1)
    paths = []
    for step in range(horizon):
        mean, spread = mu[:, -1:], sigma[:, -1:]
        if generator is None:
            draw = mean
        else:
            draw = mean + spread * torch.randn(mean.shape, generator=generator)
        paths.append(draw)
        if step + 1 < horizon:
            mu, sigma, state = model(draw, ones, metric, city, state)
    return torch.cat(paths, dim=1).reshape(n, repeat, horizon)


def train_deepar(
    fit: Windows,
    valid: Windows,
    fit_meta: tuple[np.ndarray, np.ndarray],
    valid_meta: tuple[np.ndarray, np.ndarray],
    *,
    seed: int,
    settings: TrainSettings,
    model_kwargs: dict[str, int | float],
) -> DeepAR:
    """Fit one member by Gaussian likelihood; keep the lowest inner-validation MAE weights.

    ``*_meta`` are (metric index, city index) per window.
    """
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)
    model = DeepAR(**model_kwargs)  # type: ignore[arg-type]  # kwargs checked by DeepAR
    optimiser = torch.optim.Adam(
        model.parameters(), lr=settings.learning_rate, weight_decay=settings.weight_decay
    )
    prev, observed, target, target_mask = _deepar_sequences(fit)
    metric, city = _tensor(fit_meta[0]), _tensor(fit_meta[1])
    v_metric, v_city = _tensor(valid_meta[0]), _tensor(valid_meta[1])
    v_target, v_mask = _tensor(valid.y), _tensor(valid.y_mask)
    horizon = fit.y.shape[1]
    best_score, best_state, stale = float("inf"), copy.deepcopy(model.state_dict()), 0
    for _ in range(settings.max_epochs):
        model.train()
        order = torch.randperm(len(fit), generator=generator)
        for start in range(0, len(fit), settings.batch_size):
            batch = order[start : start + settings.batch_size]
            optimiser.zero_grad()
            mu, sigma, _ = model(prev[batch], observed[batch], metric[batch], city[batch])
            nll = torch.distributions.Normal(mu, sigma).log_prob(target[batch]).neg()
            weights = target_mask[batch]
            value = (nll * weights).sum() / weights.sum().clamp(min=1.0)
            value.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 10.0)
            optimiser.step()
        if len(valid) == 0:
            best_state = copy.deepcopy(model.state_dict())
            continue
        model.eval()
        with torch.no_grad():
            path = _rollout(model, valid, v_metric, v_city, horizon, samples=1, generator=None)
            score = float(_masked_loss(path[:, 0, :], v_target, v_mask, "l1"))
        if score < best_score - 1e-7:
            best_score, best_state, stale = score, copy.deepcopy(model.state_dict()), 0
        else:
            stale += 1
            if stale >= settings.patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model


def sample_deepar(
    model: DeepAR,
    windows: Windows,
    meta: tuple[np.ndarray, np.ndarray],
    *,
    horizon: int,
    samples: int,
    seed: int,
) -> np.ndarray:
    """Ancestral sample paths in scaled units, shape (N, samples, H)."""
    generator = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        paths = _rollout(
            model,
            windows,
            _tensor(meta[0]),
            _tensor(meta[1]),
            horizon,
            samples=samples,
            generator=generator,
        )
    return paths.numpy().astype(float)
