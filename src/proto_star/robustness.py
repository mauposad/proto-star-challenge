"""Rolling-origin robustness checks, paired comparisons and the final-round selection rule.

The official folds stay 1980, 1995, 2011 (ADR 0004). ``ROLLING_ORIGINS`` adds every cut-off from
1985 to 2011 with the same 7-year horizon, so only target years up to 2018 are scored (the
validation both other teams published). Consecutive origins share target years, so their
paired differences are not independent; read win rates as screening evidence.

The selection rule (final round, Section 4, written before any candidate ran) is in
:func:`apply_selection_rule`. It is code so that it cannot drift after results are seen.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from proto_star.climate import DEFAULT_CUTOFFS, METRICS

ROLLING_ORIGINS = tuple(range(1985, 2012))  # 27 cut-offs; cut-off + 7 <= 2018
SEVEN_ORIGINS = tuple(sorted({*DEFAULT_CUTOFFS, 1985, 1990, 2000, 2005}))
RAW = "raw_score"
MIN_WIN_RATE = 0.6


def score_column(metric: str) -> str:
    """Results column for a metric's skill, or ``raw_score`` for the whole score."""
    if metric == RAW:
        return RAW
    if metric not in METRICS:
        raise ValueError(f"unknown metric {metric!r}; use {list(METRICS)} or {RAW!r}")
    return f"{metric}_skill"


def paired_differences(results: pd.DataFrame, default: str) -> pd.DataFrame:
    """Per origin and window, each method's score minus ``default``'s, per metric and raw.

    ``results`` is the output of :func:`proto_star.backtest.compare_forecasters`. Skill
    differences are in skill points (fractions); ``raw_score`` differences in score points.
    """
    if default not in set(results["method"]):
        raise ValueError(f"default {default!r} is not in the results")
    columns = [RAW, *(score_column(m) for m in METRICS)]
    keys = ["cutoff_year", "window"]
    base = results.loc[results["method"] == default, [*keys, *columns]]
    merged = results.loc[results["method"] != default, ["method", *keys, *columns]].merge(
        base, on=keys, suffixes=("", "_default"), validate="many_to_one"
    )
    out = merged[["method", *keys]].copy()
    for column in columns:
        out[f"{column}_diff"] = merged[column] - merged[f"{column}_default"]
    out.insert(1, "default", default)
    return out.sort_values(["method", "window", "cutoff_year"], ignore_index=True)


def summarize_paired(paired: pd.DataFrame) -> pd.DataFrame:
    """Mean difference and share of origins with a strictly positive difference."""
    diff_columns = [c for c in paired.columns if c.endswith("_diff")]
    grouped = paired.groupby(["method", "default", "window"])
    mean = grouped[diff_columns].mean().add_suffix("_mean")
    positive = paired[diff_columns].gt(0).astype(float)
    positive[["method", "default", "window"]] = paired[["method", "default", "window"]]
    wins = positive.groupby(["method", "default", "window"])[diff_columns].mean()
    wins = wins.add_suffix("_win_rate")
    count = grouped.size().rename("origins")
    return pd.concat([mean, wins, count], axis=1).reset_index()


@dataclass(frozen=True)
class RuleRow:
    """One candidate's three conditions under the selection rule."""

    candidate: str
    official_mean: float
    official_default: float
    origins_mean: float
    origins_default: float
    win_rate: float

    @property
    def passes(self) -> bool:
        return (
            self.official_mean > self.official_default
            and self.origins_mean > self.origins_default
            and self.win_rate >= MIN_WIN_RATE
        )


def apply_selection_rule(
    official: pd.DataFrame,
    origins: pd.DataFrame,
    *,
    default: str,
    candidates: Sequence[str],
    metric: str,
    window: str = "all",
) -> tuple[str, list[RuleRow]]:
    """Final-round rule (Section 4). Returns the chosen method and each candidate's checks.

    A candidate replaces ``default`` for ``metric`` only if (1) its mean over the official
    folds is higher, (2) its mean over the rolling origins is higher, and (3) it beats the
    default at >= 60% of the rolling origins, paired; all on ``window`` (all 7 years). If
    several pass, the one with the highest rolling-origin mean wins; if none, the default stays.
    ``metric`` may be ``raw_score`` (used for R4 vs R2).
    """
    column = score_column(metric)

    def mean_of(frame: pd.DataFrame, method: str) -> float:
        rows = frame.loc[(frame["method"] == method) & (frame["window"] == window), column]
        if rows.empty:
            raise ValueError(f"no {window!r} results for {method!r}")
        return float(rows.mean())

    official_cutoffs = set(official["cutoff_year"])
    if official_cutoffs != set(DEFAULT_CUTOFFS):
        raise ValueError(f"official results must use cut-offs {DEFAULT_CUTOFFS}")
    paired = paired_differences(origins.loc[origins["window"] == window], default)
    checks: list[RuleRow] = []
    for candidate in candidates:
        diffs = paired.loc[paired["method"] == candidate, f"{column}_diff"]
        if diffs.empty:
            raise ValueError(f"no rolling-origin results for candidate {candidate!r}")
        checks.append(
            RuleRow(
                candidate=candidate,
                official_mean=mean_of(official, candidate),
                official_default=mean_of(official, default),
                origins_mean=mean_of(origins, candidate),
                origins_default=mean_of(origins, default),
                win_rate=float((diffs > 0).mean()),
            )
        )
    passing = [row for row in checks if row.passes]
    chosen = max(passing, key=lambda row: row.origins_mean).candidate if passing else default
    return chosen, checks
