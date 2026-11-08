"""Compare backtest fold designs: few fixed origins against many rolling ones (P10, P12, P19).

Everything here works on the long results table of :func:`proto_star.backtest.compare_forecasters`
(one row per method, cut-off and window, with ``raw_score`` and per-metric skills).  It answers
questions about the evaluation itself: does a small set of origins rank methods the same way as a
dense set, how stable is the top pick, and does weighting recent origins change it.  None of it
changes the team's folds (ADR 0004); that needs a new ADR.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.backtest import DEFAULT_HORIZON, Forecaster, resolve_forecaster
from proto_star.climate import FORECAST_CUTOFF
from proto_star.trial import Variant

WEIGHT_SCHEMES = ("equal", "linear", "exponential")


class StudySettings(BaseModel):
    """Origins, weights and bootstrap settings, fixed before the study runs."""

    model_config = ConfigDict(extra="forbid")

    first_cutoff: int
    last_cutoff: int
    step: int = Field(gt=0)
    extra_cutoffs: list[int] = Field(default_factory=list)
    references: list[str] = Field(min_length=1)
    half_life_years: float = Field(gt=0)
    n_bootstrap: int = Field(gt=0)
    seed: int


class FoldStudyConfig(BaseModel):
    """A fold study: which forecasters to re-score and on which origins."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z0-9_]+$")
    description: str
    forecasters: list[str] = Field(min_length=1)
    variants: dict[str, Variant] = Field(default_factory=dict)
    study: StudySettings

    @model_validator(mode="after")
    def _check(self) -> FoldStudyConfig:
        missing = sorted(set(self.study.references) - set(self.forecasters))
        if missing:
            raise ValueError(f"references {missing} must be listed under forecasters")
        rolling_cutoffs(
            self.study.first_cutoff,
            self.study.last_cutoff,
            self.study.step,
            self.study.extra_cutoffs,
        )
        return self

    @property
    def cutoffs(self) -> tuple[int, ...]:
        s = self.study
        return rolling_cutoffs(s.first_cutoff, s.last_cutoff, s.step, s.extra_cutoffs)


def load_fold_study_config(path: Path) -> FoldStudyConfig:
    """Read and validate a fold-study config."""
    return FoldStudyConfig.model_validate(yaml.safe_load(path.read_text()))


def build_study_forecasters(cfg: FoldStudyConfig) -> dict[str, Forecaster]:
    """Resolve config names to forecasters, exactly as trials do."""
    variants: dict[str, dict[str, Any]] = {n: v.model_dump() for n, v in cfg.variants.items()}
    return {name: resolve_forecaster(name, None, variants) for name in cfg.forecasters}


def rolling_cutoffs(
    first: int,
    last: int,
    step: int,
    extra: Iterable[int] = (),
    *,
    horizon: int = DEFAULT_HORIZON,
) -> tuple[int, ...]:
    """Origins ``first, first+step, ... <= last`` plus ``extra``, sorted and de-duplicated.

    Every origin's forecast window must end by the team data cut-off (2018), so nothing
    after 2018 is ever scored.
    """
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")
    if last < first:
        raise ValueError(f"last cut-off {last} is before first cut-off {first}")
    origins = sorted({*range(first, last + 1, step), *extra})
    late = [c for c in origins if c + horizon > FORECAST_CUTOFF]
    if late:
        raise ValueError(
            f"cut-offs {late} forecast past {FORECAST_CUTOFF} with a {horizon}-year horizon; "
            f"the last allowed cut-off is {FORECAST_CUTOFF - horizon}"
        )
    return tuple(origins)


def recency_weights(
    cutoffs: Sequence[int], scheme: str, *, half_life_years: float = 10.0
) -> pd.Series:
    """Weights per origin that sum to 1.

    ``equal`` gives every origin the same weight; ``linear`` is proportional to the origin's
    position in time order (1, 2, ..., n); ``exponential`` halves every ``half_life_years``
    back from the latest origin.
    """
    origins = sorted(set(cutoffs))
    if not origins:
        raise ValueError("need at least one cut-off")
    if scheme == "equal":
        raw = np.ones(len(origins))
    elif scheme == "linear":
        raw = np.arange(1, len(origins) + 1, dtype=float)
    elif scheme == "exponential":
        if half_life_years <= 0:
            raise ValueError("half_life_years must be positive")
        age = max(origins) - np.asarray(origins, dtype=float)
        raw = 0.5 ** (age / half_life_years)
    else:
        raise ValueError(f"unknown weight scheme {scheme!r}; use one of {WEIGHT_SCHEMES}")
    return pd.Series(raw / raw.sum(), index=pd.Index(origins, name="cutoff_year"), name="weight")


def score_matrix(
    results: pd.DataFrame,
    window: str,
    *,
    value: str = "raw_score",
    cutoffs: Iterable[int] | None = None,
) -> pd.DataFrame:
    """Methods as rows, origins as columns, for one window.  Missing cells raise."""
    frame = results.loc[results["window"] == window]
    if frame.empty:
        raise ValueError(f"no results for window {window!r}")
    matrix = frame.pivot_table(index="method", columns="cutoff_year", values=value)
    if cutoffs is not None:
        wanted = list(cutoffs)
        absent = sorted(set(wanted) - set(matrix.columns))
        if absent:
            raise ValueError(f"cut-offs {absent} are missing from the results")
        matrix = matrix[wanted]
    if matrix.isna().to_numpy().any():
        method, cutoff = np.argwhere(matrix.isna().to_numpy())[0]
        raise ValueError(
            "results are incomplete, for example "
            f"{matrix.index[method]!r} at cut-off {matrix.columns[cutoff]}"
        )
    return matrix


def weighted_scores(matrix: pd.DataFrame, weights: pd.Series | None = None) -> pd.Series:
    """Weighted mean score per method across the matrix's origins, best first."""
    if weights is None:
        weights = recency_weights([int(c) for c in matrix.columns], "equal")
    aligned = weights.reindex(matrix.columns)
    if aligned.isna().any():
        raise ValueError("weights do not cover every origin in the matrix")
    scores = matrix.to_numpy() @ (aligned.to_numpy() / aligned.sum())
    return pd.Series(scores, index=matrix.index, name="score").sort_values(ascending=False)


def ranks(scores: pd.Series) -> pd.Series:
    """Rank 1 = best (highest score); ties share the lower rank."""
    return scores.rank(ascending=False, method="min").astype(int)


def per_origin_ranks(matrix: pd.DataFrame) -> pd.DataFrame:
    """Rank of each method within each origin (1 = best)."""
    return matrix.rank(axis=0, ascending=False, method="min").astype(int)


def kendall_tau(a: pd.Series, b: pd.Series) -> float:
    """Kendall's tau-b between two score (or rank) series over their shared index."""
    shared = a.index.intersection(b.index)
    if len(shared) < 2:
        raise ValueError("need at least two shared methods to compare rankings")
    x = a.loc[shared].to_numpy(dtype=float)
    y = b.loc[shared].to_numpy(dtype=float)
    i, j = np.triu_indices(len(shared), k=1)
    dx = np.sign(x[i] - x[j])
    dy = np.sign(y[i] - y[j])
    n0 = len(i)
    tied_x = np.sum(dx == 0)
    tied_y = np.sum(dy == 0)
    denom = np.sqrt((n0 - tied_x) * (n0 - tied_y))
    if denom == 0:
        raise ValueError("one of the rankings is all ties")
    return float(np.sum(dx * dy) / denom)


def leave_one_origin_out(matrix: pd.DataFrame, weights: pd.Series | None = None) -> pd.DataFrame:
    """Top pick and its margin over the runner-up after dropping each origin in turn."""
    if matrix.shape[1] < 2:
        raise ValueError("need at least two origins to leave one out")
    rows = []
    for dropped in matrix.columns:
        kept = matrix.drop(columns=dropped)
        w = None if weights is None else weights.drop(index=dropped)
        scores = weighted_scores(kept, w)
        rows.append(
            {
                "dropped_cutoff": int(dropped),
                "top": scores.index[0],
                "runner_up": scores.index[1],
                "margin": float(scores.iloc[0] - scores.iloc[1]),
            }
        )
    return pd.DataFrame(rows)


def bootstrap_top_pick(
    matrix: pd.DataFrame,
    *,
    n_boot: int,
    seed: int,
    weights: pd.Series | None = None,
) -> pd.Series:
    """Share of origin-bootstrap resamples in which each method has the best weighted mean.

    Origins are drawn with replacement; with ``weights``, each drawn origin keeps its weight,
    so recency weighting and resampling combine.  Ties count for every tied method.
    """
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    rng = np.random.default_rng(seed)
    values = matrix.to_numpy()
    n_origins = values.shape[1]
    base = (
        np.ones(n_origins)
        if weights is None
        else weights.reindex(matrix.columns).to_numpy(dtype=float)
    )
    wins = np.zeros(values.shape[0])
    for _ in range(n_boot):
        draw = rng.integers(0, n_origins, size=n_origins)
        w = np.bincount(draw, minlength=n_origins) * base
        means = values @ (w / w.sum())
        wins += np.isclose(means, means.max())
    share = pd.Series(wins / n_boot, index=matrix.index, name="share_top")
    return share.sort_values(ascending=False)


def paired_wins(matrix: pd.DataFrame, method: str, reference: str) -> tuple[int, int]:
    """Origins where ``method`` scores strictly above ``reference``, and the number of origins."""
    for name in (method, reference):
        if name not in matrix.index:
            raise ValueError(f"method {name!r} is not in the results")
    diff = matrix.loc[method].to_numpy(dtype=float) - matrix.loc[reference].to_numpy(dtype=float)
    return int(np.sum(diff > 0)), int(diff.size)


def trend_per_decade(series: pd.Series) -> float:
    """Least-squares slope of a series indexed by year, in units per 10 years."""
    if series.size < 2:
        raise ValueError("need at least two points for a slope")
    x = series.index.to_numpy(dtype=float)
    y = series.to_numpy(dtype=float)
    return float(np.polyfit(x, y, 1)[0] * 10.0)


def warming_by_origin(
    history: pd.DataFrame,
    cutoffs: Iterable[int],
    *,
    metric: str = "annual_avg_temp",
    leads: tuple[int, int] = (4, 7),
) -> pd.DataFrame:
    """City-averaged warming signals at each origin, for explaining rank changes.

    ``pre_trend_per_decade`` uses only years up to the cut-off (30-calendar-year slope).
    ``shift_vs_10y`` and ``shift_vs_30y`` compare the scored lead years with the 10-valid-year and
    30-calendar-year means at the cut-off; they use test years, so they are diagnostics for
    explaining results, never inputs to a forecast or a selection.
    ``history`` is the long table from :func:`proto_star.climate.annual_to_long`.
    """
    series = history.loc[history["metric"] == metric]
    if series.empty:
        raise ValueError(f"no history for metric {metric!r}")
    first_lead, last_lead = leads
    rows = []
    for cutoff in cutoffs:
        per_city = []
        for _, city in series.groupby("city_id"):
            values = city.set_index("year")["actual_value"].sort_index()
            past = values.loc[(values.index > cutoff - 30) & (values.index <= cutoff)]
            future = values.loc[
                (values.index >= cutoff + first_lead) & (values.index <= cutoff + last_lead)
            ]
            if past.size < 10 or future.empty:
                continue
            recent = values.loc[values.index <= cutoff].iloc[-10:]
            per_city.append(
                (
                    trend_per_decade(past),
                    float(future.mean() - recent.mean()),
                    float(future.mean() - past.mean()),
                )
            )
        if not per_city:
            raise ValueError(f"no city has enough {metric} data around cut-off {cutoff}")
        trend, vs10, vs30 = np.mean(np.asarray(per_city), axis=0)
        rows.append(
            {
                "cutoff_year": int(cutoff),
                "n_cities": len(per_city),
                "pre_trend_per_decade": float(trend),
                "shift_vs_10y": float(vs10),
                "shift_vs_30y": float(vs30),
            }
        )
    return pd.DataFrame(rows)
