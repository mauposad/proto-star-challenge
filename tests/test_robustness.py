import pandas as pd
import pytest

from proto_star.climate import DEFAULT_CUTOFFS, METRICS
from proto_star.robustness import (
    ROLLING_ORIGINS,
    apply_selection_rule,
    paired_differences,
    summarize_paired,
)


def _results(scores: dict[str, list[float]], cutoffs: list[int]) -> pd.DataFrame:
    """Fake compare_forecasters output: temperature skill = score, others 0."""
    rows = []
    for method, values in scores.items():
        for cutoff, value in zip(cutoffs, values, strict=True):
            row: dict[str, object] = {
                "method": method,
                "cutoff_year": cutoff,
                "window": "all",
                "raw_score": 25.0 * value,
            }
            for metric in METRICS:
                row[f"{metric}_skill"] = value if metric == "annual_avg_temp" else 0.0
            rows.append(row)
    return pd.DataFrame(rows)


def test_rolling_origins_are_1985_to_2011() -> None:
    assert ROLLING_ORIGINS[0] == 1985 and ROLLING_ORIGINS[-1] == 2011
    assert len(ROLLING_ORIGINS) == 27
    assert max(ROLLING_ORIGINS) + 7 <= 2018  # only target years up to 2018 are scored


def test_paired_differences_and_win_rate() -> None:
    results = _results({"base": [0.1, 0.2, 0.3], "cand": [0.2, 0.1, 0.4]}, [1990, 1991, 1992])
    paired = paired_differences(results, "base")
    assert paired["annual_avg_temp_skill_diff"].round(6).tolist() == [0.1, -0.1, 0.1]
    assert (paired["cdd_skill_diff"] == 0).all()  # metric isolation shows as zero differences
    summary = summarize_paired(paired).iloc[0]
    assert summary["annual_avg_temp_skill_diff_win_rate"] == pytest.approx(2 / 3)
    assert summary["origins"] == 3
    with pytest.raises(ValueError, match="not in the results"):
        paired_differences(results, "missing")


def _rule(official: dict[str, list[float]], origins: dict[str, list[float]]) -> str:
    chosen, _ = apply_selection_rule(
        _results(official, list(DEFAULT_CUTOFFS)),
        _results(origins, list(range(1985, 1990))),
        default="base",
        candidates=[m for m in official if m != "base"],
        metric="annual_avg_temp",
    )
    return chosen


def test_rule_needs_all_three_conditions() -> None:
    base = [0.1] * 5
    good = [0.2, 0.2, 0.2, 0.0, 0.2]  # wins 4 of 5 (80%)
    assert _rule({"base": [0.1] * 3, "c": [0.2] * 3}, {"base": base, "c": good}) == "c"
    # fails (1): official mean not higher
    assert _rule({"base": [0.1] * 3, "c": [0.1] * 3}, {"base": base, "c": good}) == "base"
    # fails (2): higher win rate but lower origin mean
    low_mean = [0.11, 0.11, 0.11, 0.11, -0.5]
    assert _rule({"base": [0.1] * 3, "c": [0.2] * 3}, {"base": base, "c": low_mean}) == "base"
    # fails (3): higher means but wins only 2 of 5 (40%)
    lucky = [0.9, 0.9, 0.0, 0.0, 0.0]
    assert _rule({"base": [0.1] * 3, "c": [0.2] * 3}, {"base": base, "c": lucky}) == "base"


def test_rule_picks_highest_origin_mean_among_passers() -> None:
    official = {"base": [0.1] * 3, "c1": [0.3] * 3, "c2": [0.2] * 3}
    origins = {"base": [0.1] * 5, "c1": [0.2] * 5, "c2": [0.25] * 5}
    assert _rule(official, origins) == "c2"


def test_rule_rejects_non_official_folds() -> None:
    with pytest.raises(ValueError, match="cut-offs"):
        apply_selection_rule(
            _results({"base": [0.1], "c": [0.2]}, [1990]),
            _results({"base": [0.1], "c": [0.2]}, [1990]),
            default="base",
            candidates=["c"],
            metric="annual_avg_temp",
        )
