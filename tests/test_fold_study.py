import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from proto_star.backtest import compare_forecasters
from proto_star.climate import METRICS, annual_to_long
from proto_star.fold_study import (
    bootstrap_top_pick,
    build_study_forecasters,
    kendall_tau,
    leave_one_origin_out,
    load_fold_study_config,
    paired_wins,
    per_origin_ranks,
    ranks,
    recency_weights,
    rolling_cutoffs,
    score_matrix,
    trend_per_decade,
    warming_by_origin,
    weighted_scores,
)


def _results(table: dict[str, list[float]], cutoffs: list[int]) -> pd.DataFrame:
    """Long results in the backtest's format, for one window."""
    rows = []
    for method, scores in table.items():
        for cutoff, score in zip(cutoffs, scores, strict=True):
            row: dict[str, object] = {
                "method": method,
                "cutoff_year": cutoff,
                "window": "all",
                "raw_score": score,
            }
            for metric in METRICS:
                row[f"{metric}_skill"] = score / 100.0
            rows.append(row)
    return pd.DataFrame(rows)


CUTOFFS = [1980, 1990, 2000, 2010]
# "old" is best early, "new" is best late; "flat" is steady and best on an equal-weight mean.
TABLE = {
    "old": [6.0, 4.0, 0.0, -2.0],
    "new": [-4.0, 0.0, 4.0, 6.0],
    "flat": [2.5, 2.5, 2.5, 2.5],
}


def test_rolling_cutoffs_sorted_and_bounded():
    assert rolling_cutoffs(1980, 2010, 3, [2011, 1995]) == (
        1980, 1983, 1986, 1989, 1992, 1995, 1998, 2001, 2004, 2007, 2010, 2011,
    )  # fmt: skip
    with pytest.raises(ValueError, match="forecast past 2018"):
        rolling_cutoffs(1980, 2012, 4)
    with pytest.raises(ValueError, match="step must be positive"):
        rolling_cutoffs(1980, 2010, 0)


def test_recency_weights_sum_to_one_and_favor_recent():
    for scheme in ("equal", "linear", "exponential"):
        w = recency_weights(CUTOFFS, scheme, half_life_years=10.0)
        assert w.sum() == pytest.approx(1.0)
        assert list(w.index) == CUTOFFS
    linear = recency_weights(CUTOFFS, "linear")
    assert linear.to_list() == pytest.approx([0.1, 0.2, 0.3, 0.4])
    exp = recency_weights(CUTOFFS, "exponential", half_life_years=10.0)
    assert exp[2000] / exp[2010] == pytest.approx(0.5)
    with pytest.raises(ValueError, match="unknown weight scheme"):
        recency_weights(CUTOFFS, "cubic")


def test_weighted_scores_and_recency_change_the_pick():
    matrix = score_matrix(_results(TABLE, CUTOFFS), "all")
    equal = weighted_scores(matrix)
    assert equal.index[0] == "flat"
    assert equal["old"] == pytest.approx(2.0)
    recent = weighted_scores(matrix, recency_weights(CUTOFFS, "exponential", half_life_years=5.0))
    assert recent.index[0] == "new"
    assert ranks(equal).to_dict() == {"flat": 1, "old": 2, "new": 3}


def test_score_matrix_rejects_missing_cells():
    results = _results(TABLE, CUTOFFS)
    with pytest.raises(ValueError, match="incomplete"):
        score_matrix(results.iloc[1:], "all")
    with pytest.raises(ValueError, match="missing"):
        score_matrix(results, "all", cutoffs=[1980, 2020])


def test_per_origin_ranks():
    matrix = score_matrix(_results(TABLE, CUTOFFS), "all")
    r = per_origin_ranks(matrix)
    assert r.loc["old", 1980] == 1
    assert r.loc["new", 2010] == 1


def test_kendall_tau_known_values():
    a = pd.Series([1.0, 2.0, 3.0, 4.0], index=list("abcd"))
    assert kendall_tau(a, a) == pytest.approx(1.0)
    assert kendall_tau(a, -a) == pytest.approx(-1.0)
    swapped = pd.Series([2.0, 1.0, 3.0, 4.0], index=list("abcd"))
    assert kendall_tau(a, swapped) == pytest.approx(4 / 6)  # 5 concordant, 1 discordant pair
    with pytest.raises(ValueError, match="two shared"):
        kendall_tau(a.iloc[:1], a.iloc[:1])


def test_leave_one_origin_out_and_bootstrap():
    matrix = score_matrix(_results(TABLE, CUTOFFS), "all")
    looo = leave_one_origin_out(matrix)
    assert list(looo["dropped_cutoff"]) == CUTOFFS
    assert (looo["margin"] >= 0).all()
    share = bootstrap_top_pick(matrix, n_boot=500, seed=1)
    assert share.sum() >= 1.0  # ties count for every tied method
    assert share.between(0, 1).all()
    again = bootstrap_top_pick(matrix, n_boot=500, seed=1)
    pd.testing.assert_series_equal(share, again)  # seeded


def test_paired_wins():
    matrix = score_matrix(_results(TABLE, CUTOFFS), "all")
    assert paired_wins(matrix, "new", "flat") == (2, 4)
    with pytest.raises(ValueError, match="not in the results"):
        paired_wins(matrix, "nope", "flat")


def test_trend_per_decade():
    s = pd.Series([0.0, 1.0, 2.0], index=[2000, 2001, 2002])
    assert trend_per_decade(s) == pytest.approx(10.0)


def _master(first: int = 1940, last: int = 2018) -> pd.DataFrame:
    """Two cities warming 0.3 F per decade with deterministic noise."""
    rows = []
    for offset, city in enumerate(["A", "B"]):
        for year in range(first, last + 1):
            wiggle = math.sin(year * 1.7 + offset)
            trend = (year - first) * 0.03
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Avg Temp": 50.0 + 10 * offset + trend + 0.1 * wiggle,
                    "ToT Prcp": 30.0 + 5 * offset + 3 * wiggle,
                    "Max Tmax": 95.0 + 2 * wiggle,
                    "cdd": 800.0 + 300 * offset + 10 * trend + 50 * wiggle,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def test_warming_by_origin_recovers_trend():
    history = annual_to_long(_master())
    warm = warming_by_origin(history, [1990, 2000], leads=(4, 7))
    assert warm["pre_trend_per_decade"].to_numpy() == pytest.approx([0.3, 0.3], abs=0.05)
    # leads 4-7 sit about 10 years after the 10-year mean's midpoint: ~0.3 F warmer
    assert warm["shift_vs_10y"].to_numpy() == pytest.approx([0.3, 0.3], abs=0.1)
    assert (warm["shift_vs_30y"] > warm["shift_vs_10y"]).all()


def test_warming_pre_trend_ignores_years_after_cutoff():
    master = _master()
    history = annual_to_long(master)
    spiked = master.copy()
    spiked.loc[spiked["Year"] > 2000, "Avg Temp"] += 50.0
    spiked_history = annual_to_long(spiked)
    a = warming_by_origin(history, [2000])
    b = warming_by_origin(spiked_history, [2000])
    assert a["pre_trend_per_decade"].iloc[0] == pytest.approx(b["pre_trend_per_decade"].iloc[0])
    assert b["shift_vs_10y"].iloc[0] > a["shift_vs_10y"].iloc[0] + 40


def test_config_round_trip_and_rolling_backtest(tmp_path: Path):
    config = {
        "name": "unit_fold_study",
        "description": "tiny",
        "forecasters": ["current_best", "ten_year_mean", "thirty_year_mean"],
        "study": {
            "first_cutoff": 1995,
            "last_cutoff": 2010,
            "step": 5,
            "extra_cutoffs": [2011],
            "references": ["current_best"],
            "half_life_years": 10.0,
            "n_bootstrap": 10,
            "seed": 0,
        },
    }
    path = tmp_path / "study.yaml"
    path.write_text(yaml.safe_dump(config))
    cfg = load_fold_study_config(path)
    assert cfg.cutoffs == (1995, 2000, 2005, 2010, 2011)
    results = compare_forecasters(build_study_forecasters(cfg), _master(), cutoffs=cfg.cutoffs)
    matrix = score_matrix(results, "years_4_7", cutoffs=cfg.cutoffs)
    assert matrix.shape == (3, 5)
    assert np.allclose(matrix.loc["thirty_year_mean"], 0.0)  # it is the scoring reference

    config["study"]["references"] = ["missing"]
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match="references"):
        load_fold_study_config(path)
