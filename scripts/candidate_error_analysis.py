"""Where do the candidate's errors come from? Diagnostics on historical folds only.

Every quantity uses backtest folds whose forecast years end by 2018, so this never touches
2019-2025.  The oracle rows use the fold's own truth.  They are ceilings that show where
headroom exists, not forecasters, and must never be used to select or tune a method.

Prints Markdown. Usage:
    uv run python scripts/candidate_error_analysis.py [--origins official|seven|early|all]
"""

import argparse

import numpy as np
import pandas as pd

from proto_star.backtest import fold_rows, pooled_trend_forecaster
from proto_star.climate import BASELINE_WINDOW_YEARS, DEFAULT_CUTOFFS, METRICS, annual_to_long
from proto_star.data.master import load_master
from proto_star.trend import PooledTrendSpec
from proto_star.trial import markdown_table

ORIGINS = {
    "official": list(DEFAULT_CUTOFFS),
    "seven": sorted({*DEFAULT_CUTOFFS, 1985, 1990, 2000, 2005}),
    "early": [1955, 1962, 1969],
    "all": [1955, 1962, 1969, 1980, 1985, 1990, 1995, 2000, 2005, 2011],
}
CANDIDATE = PooledTrendSpec(level_years=[10, 15], trend_window=40, cdd_sensitivity=True)


def skill(frame: pd.DataFrame, column: str) -> float:
    """Mean over folds of 100 x (1 - MAE / MAE_ref) for the rows given."""
    per_fold = frame.groupby("cutoff_year").apply(
        lambda f: (
            1
            - (f[column] - f["actual_value"]).abs().mean()
            / (f["reference_value"] - f["actual_value"]).abs().mean()
        ),
        include_groups=False,
    )
    return float(100 * per_fold.mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origins", choices=sorted(ORIGINS), default="seven")
    args = parser.parse_args()
    cutoffs = ORIGINS[args.origins]
    master = load_master()
    rows = fold_rows(pooled_trend_forecaster(CANDIDATE), master, cutoffs=cutoffs)
    rows["lead"] = rows["year"] - rows["cutoff_year"]
    rows["error"] = rows["predicted_value"] - rows["actual_value"]
    rows["ref_error"] = rows["reference_value"] - rows["actual_value"]

    # Oracle ceilings (fold truth only).
    group = rows.groupby(["cutoff_year", "metric", "city_id"])
    rows["oracle_city_level"] = group["actual_value"].transform("mean")
    rows["oracle_city_bias"] = rows["predicted_value"] - group["error"].transform("mean")
    by_year = rows.groupby(["cutoff_year", "metric", "year"])["error"]
    rows["oracle_common_year"] = rows["predicted_value"] - by_year.transform("mean")
    by_fold = rows.groupby(["cutoff_year", "metric"])["error"]
    rows["oracle_common_fold"] = rows["predicted_value"] - by_fold.transform("mean")

    print(f"# Candidate error analysis (origins {cutoffs})\n")
    print(
        "Candidate: `trend_level10_15_sensitivity`. Skill is percent, 100 x (1 - MAE/MAE_ref), "
        "averaged over folds. Oracle columns use each fold's truth. They are ceilings, never "
        "forecasters.\n"
    )
    table = []
    for metric in METRICS:
        for window, (lo, hi) in {"all": (1, 7), "years_1_3": (1, 3), "years_4_7": (4, 7)}.items():
            part = rows.loc[(rows["metric"] == metric) & rows["lead"].between(lo, hi)]
            table.append(
                {
                    "metric": metric,
                    "window": window,
                    "candidate": round(skill(part, "predicted_value"), 2),
                    "oracle: perfect common shift per year": round(
                        skill(part, "oracle_common_year"), 2
                    ),
                    "oracle: perfect common shift per fold": round(
                        skill(part, "oracle_common_fold"), 2
                    ),
                    "oracle: perfect city bias per fold": round(skill(part, "oracle_city_bias"), 2),
                    "oracle: true city mean of the 7 years": round(
                        skill(part, "oracle_city_level"), 2
                    ),
                }
            )
    print("## Headroom per metric\n")
    print(markdown_table(pd.DataFrame(table)))

    print("\n## Mean signed error (forecast minus actual) by lead, per metric\n")
    bias = rows.pivot_table(index="metric", columns="lead", values="error", aggfunc="mean")
    ref_bias = rows.pivot_table(index="metric", columns="lead", values="ref_error", aggfunc="mean")
    bias.columns = [f"lead {c}" for c in bias.columns]
    bias["reference, all leads"] = ref_bias.mean(axis=1)
    print(markdown_table(bias.round(3).reset_index()))

    print("\n## Mean signed error by fold (all leads), per metric\n")
    fold_bias = rows.pivot_table(index="metric", columns="cutoff_year", values="error")
    print(markdown_table(fold_bias.round(3).reset_index()))

    print("\n## Share of squared error that is common to all cities in a year\n")
    print(
        "Each fold-metric-year's errors split into the cross-city mean (common, for example a "
        "nationally warm year) and the city deviation from it.\n"
    )
    shares = []
    for metric in METRICS:
        part = rows.loc[rows["metric"] == metric]
        common = part.groupby(["cutoff_year", "year"])["error"].transform("mean")
        shares.append(
            {
                "metric": metric,
                "common share of squared error": round(
                    float((common**2).mean() / (part["error"] ** 2).mean()), 3
                ),
            }
        )
    print(markdown_table(pd.DataFrame(shares)))

    print("\n## Do recent city anomalies persist into the forecast window?\n")
    print(
        "Across cities, the correlation between A = (mean of the last N valid years before the "
        "cut-off - 30-year mean) and F = (mean of the 7 forecast years - 30-year mean). "
        "Below that, the slope of F on A (1 = full persistence, 0 = none), after removing each "
        "fold's cross-city mean of A and F (the national part).\n"
    )
    history = annual_to_long(master)
    persist = []
    for cutoff in cutoffs:
        past = history.loc[history["year"] <= cutoff]
        future = history.loc[history["year"].between(cutoff + 1, cutoff + 7)]
        m30 = (
            past.loc[past["year"] > cutoff - BASELINE_WINDOW_YEARS]
            .groupby(["metric", "city_id"])["actual_value"]
            .mean()
        )
        f = future.groupby(["metric", "city_id"])["actual_value"].mean() - m30
        for n in (1, 3, 5, 10, 15):
            recent = past.sort_values("year").groupby(["metric", "city_id"]).tail(n)
            a = recent.groupby(["metric", "city_id"])["actual_value"].mean() - m30
            joined = pd.concat({"a": a, "f": f}, axis=1).dropna()
            for metric in METRICS:
                part = joined.xs(metric, level="metric")
                da, df = part["a"] - part["a"].mean(), part["f"] - part["f"].mean()
                persist.append(
                    {
                        "cutoff": cutoff,
                        "metric": metric,
                        "N": n,
                        "corr": float(np.corrcoef(part["a"], part["f"])[0, 1]),
                        "slope_city_part": float((da * df).sum() / (da**2).sum()),
                    }
                )
    persist_frame = pd.DataFrame(persist)
    summary = persist_frame.groupby(["metric", "N"])[["corr", "slope_city_part"]].mean().round(2)
    print(markdown_table(summary.reset_index()))


if __name__ == "__main__":
    main()
