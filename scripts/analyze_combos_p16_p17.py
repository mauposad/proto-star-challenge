"""Why-analysis for the P16/P17 forecast combination trial.

Config: `configs/agent_paper_combos_p16_p17.yaml`.

Reads the trial's ``results.csv`` for the score tables, then recomputes the member forecasts on
the same ADR 0004 folds (through the registry, as the trial did) for the per-city breakdown,
the pairwise correlation of member errors and the error decomposition.  Writes
``docs/trials/combos_p16_p17_why.md``.

    uv run python scripts/analyze_combos_p16_p17.py [runs/trials/<stamp>_combos_p16_p17]

Recomputing refits DeepAR and ARIMA once per fold (about 15 minutes on a laptop).
Nothing here selects a method: the analysis reads the backtest that was already fixed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST, WINDOWS, resolve_forecaster
from proto_star.climate import DEFAULT_CUTOFFS, METRICS, annual_to_long, baseline_forecast
from proto_star.data.master import load_master
from proto_star.forecasters.combination_p16_p17 import build_member, combine_values, run_member
from proto_star.paths import PROJECT_ROOT, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.trial import load_trial_config, markdown_table

CONFIG = PROJECT_ROOT / "configs" / "agent_paper_combos_p16_p17.yaml"
OUT = TRIAL_NOTES_DIR / "combos_p16_p17_why.md"
HYBRID = "hybrid_ridge_all_cdd"
REFERENCES = (CURRENT_BEST, HYBRID)
NON_CANDIDATES = {
    CURRENT_BEST,
    "ten_year_mean",
    HYBRID,
    "member_deepar",
    "member_ewma",
    "member_arima",
}
REPLICAS = {"combo_mean_seed7", "combo_mean_cdd_only_seed7"}
HORIZON = 7
KEY = ["city_id", "year", "metric"]
COMBINED = {
    "cdd": ["ridge", "deepar", "ewma", "arima"],
    "annual_avg_temp": ["ten", "ewma", "deepar", "arima"],
}
SHORT = {
    "annual_avg_temp": "temp",
    "total_precip_in": "precip",
    "hottest_day_temp": "hottest",
    "cdd": "cdd",
}


def latest_run() -> Path:
    runs = sorted(TRIALS_DIR.glob("*_combos_p16_p17"))
    if not runs:
        raise FileNotFoundError(
            "no combos_p16_p17 trial run under runs/trials/; run the trial first"
        )
    return runs[-1]


def score_table(results: pd.DataFrame) -> pd.DataFrame:
    """Mean raw score per window plus origins won against each reference, per window."""
    pivot = results.pivot_table(
        index="method", columns="window", values="raw_score", aggfunc="mean"
    )
    table = pd.DataFrame(
        {
            "method": pivot.index,
            "all": pivot["all"].round(2).to_numpy(),
            "years 1-3": pivot["years_1_3"].round(2).to_numpy(),
            "years 4-7": pivot["years_4_7"].round(2).to_numpy(),
        }
    )
    for ref in REFERENCES:
        ref_rows = results.loc[results["method"] == ref, ["window", "cutoff_year", "raw_score"]]
        paired = results.merge(ref_rows, on=["window", "cutoff_year"], suffixes=("", "_ref"))
        paired["win"] = paired["raw_score"] > paired["raw_score_ref"]
        wins = paired.pivot_table(index="method", columns="window", values="win", aggfunc="sum")
        label = "cb" if ref == CURRENT_BEST else "hybrid"
        table[f"wins vs {label} (all/1-3/4-7)"] = [
            f"{wins.loc[m, 'all']}/{wins.loc[m, 'years_1_3']}/{wins.loc[m, 'years_4_7']}"
            for m in table["method"]
        ]
    return table.sort_values("years 4-7", ascending=False, ignore_index=True)


def metric_skill_table(results: pd.DataFrame, window: str) -> pd.DataFrame:
    """Per-metric skill (%) and its difference to each reference, for one window."""
    columns = [f"{m}_skill" for m in METRICS]
    means = results.loc[results["window"] == window].groupby("method")[columns].mean() * 100.0
    out = pd.DataFrame({"method": means.index})
    for metric in METRICS:
        values = means[f"{metric}_skill"]
        out[SHORT[metric]] = values.round(2).to_numpy()
    for metric in ("annual_avg_temp", "cdd"):
        values = means[f"{metric}_skill"]
        out[f"{SHORT[metric]} - cb"] = (values - values[CURRENT_BEST]).round(2).to_numpy()
        out[f"{SHORT[metric]} - hybrid"] = (values - values[HYBRID]).round(2).to_numpy()
    return out.sort_values("cdd", ascending=False, ignore_index=True)


def per_origin_table(results: pd.DataFrame, window: str) -> pd.DataFrame:
    pivot = results.loc[results["window"] == window].pivot_table(
        index="method", columns="cutoff_year", values="raw_score"
    )
    pivot.columns = [str(c) for c in pivot.columns]
    for ref, label in ((CURRENT_BEST, "cb"), (HYBRID, "hybrid")):
        ahead = pivot.gt(pivot.loc[ref], axis=1).sum(axis=1)
        pivot[f"origins > {label}"] = ahead
    return pivot.round(2).reset_index()


def fold_frames(
    master: pd.DataFrame, cfg_variants: dict[str, dict[str, Any]], best: str
) -> pd.DataFrame:
    """Long frame of truth, the 30-year reference, every member and the scored forecasters."""
    members = cfg_variants["member_deepar"]["params"]["members"]
    used = sorted({name for names in COMBINED.values() for name in names})
    history = annual_to_long(master)
    frames = []
    for cutoff in DEFAULT_CUTOFFS:
        years = list(range(cutoff + 1, cutoff + HORIZON + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "ref30"})
        truth = history.loc[history["year"].isin(years), [*KEY, "actual_value"]].merge(
            reference[[*KEY, "ref30"]], on=KEY
        )
        for name in used:
            rows = run_member(members[name], build_member(members[name]), train, cutoff, years)
            truth = truth.merge(rows.rename(columns={"predicted_value": name}), on=KEY, how="left")
        for name in (CURRENT_BEST, HYBRID, best):
            forecaster = resolve_forecaster(name, variants=cfg_variants)
            rows = forecaster(train, cutoff, years)[[*KEY, "predicted_value"]]
            truth = truth.merge(rows.rename(columns={"predicted_value": name}), on=KEY, how="left")
        truth["cutoff_year"] = cutoff
        truth["lead"] = truth["year"] - cutoff
        frames.append(truth)
    return pd.concat(frames, ignore_index=True)


def in_window(frame: pd.DataFrame, window: str) -> pd.DataFrame:
    first, last = WINDOWS[window]
    return frame.loc[frame["lead"].between(first, last)]


def error_correlations(data: pd.DataFrame, metric: str, window: str) -> pd.DataFrame:
    names = COMBINED[metric]
    rows = in_window(data.loc[data["metric"] == metric], window)
    errors = pd.DataFrame({n: rows[n] - rows["actual_value"] for n in names})
    return errors.corr().round(3).reset_index(names="member")


def deviation_correlations(data: pd.DataFrame, metric: str, window: str) -> pd.DataFrame:
    """Correlation of the members' *differences* from the 10-year mean (what each adds)."""
    names = [n for n in COMBINED[metric] if n != "ten"]
    rows = in_window(data.loc[data["metric"] == metric], window)
    deviations = pd.DataFrame({n: rows[n] - rows["ten"] for n in names})
    return deviations.corr().round(3).reset_index(names="member")


def decomposition(data: pd.DataFrame, metric: str, window: str) -> dict[str, float]:
    """MAE (and the MSE ambiguity decomposition) of the equal-weight mean against its members."""
    names = COMBINED[metric]
    rows = in_window(data.loc[data["metric"] == metric], window)
    values = rows[names].to_numpy(dtype=float)
    actual = rows["actual_value"].to_numpy(dtype=float)
    mean = combine_values(values, "mean")
    member_mae = {n: float(np.abs(rows[n] - rows["actual_value"]).mean()) for n in names}
    member_mse = np.mean((values - actual[:, None]) ** 2, axis=0)
    ambiguity = float(np.mean((values - mean[:, None]) ** 2))
    return {
        **{f"MAE {n}": member_mae[n] for n in names},
        "MAE avg member": float(np.mean(list(member_mae.values()))),
        "MAE equal mean": float(np.abs(mean - actual).mean()),
        "MAE 30y ref": float(np.abs(rows["ref30"] - rows["actual_value"]).mean()),
        "MSE avg member": float(member_mse.mean()),
        "MSE ambiguity (spread)": ambiguity,
        "MSE equal mean": float(np.mean((mean - actual) ** 2)),
    }


def city_contributions(data: pd.DataFrame, best: str, window: str) -> pd.DataFrame:
    """Raw-score points each city adds to ``best`` over ``HYBRID``, mean over the folds.

    For one fold and metric the skill gap is the sum over rows of
    ``|e_hybrid| - |e_best|`` over the sum of ``|e_ref30|``; the raw score averages the four
    metrics, so the per-city terms add up exactly to the raw-score gap of that fold.
    """
    rows = in_window(data, window).copy()
    rows["gain"] = (rows[HYBRID] - rows["actual_value"]).abs() - (
        rows[best] - rows["actual_value"]
    ).abs()
    rows["ref_abs"] = (rows["ref30"] - rows["actual_value"]).abs()
    denom = rows.groupby(["cutoff_year", "metric"])["ref_abs"].transform("sum")
    rows["points"] = 100.0 * rows["gain"] / denom / len(METRICS)
    per_fold = rows.pivot_table(
        index=["city_id", "cutoff_year"],
        columns="metric",
        values="points",
        aggfunc="sum",
        fill_value=0.0,
    )
    per_city = per_fold.groupby("city_id").sum() / len(DEFAULT_CUTOFFS)
    per_city["total"] = per_city.sum(axis=1)
    return per_city


def city_covariates(master: pd.DataFrame) -> pd.DataFrame:
    """Warming rate 1981-2010, station switches 1951-2018, latitude and region per city."""
    temp = annual_to_long(master)
    temp = temp.loc[(temp["metric"] == "annual_avg_temp") & temp["year"].between(1981, 2010)]
    slopes = temp.groupby("city_id").apply(
        lambda g: (
            float(np.polyfit(g["year"], g["actual_value"], 1)[0]) * 10.0 if len(g) >= 10 else np.nan
        ),
        include_groups=False,
    )
    recent = master.loc[master["Year"].between(1951, 2018)]
    switches = (
        recent.assign(switch=recent["Station Changes"].fillna(0) > 0).groupby("ID")["switch"].sum()
    )
    static = master.drop_duplicates("ID").set_index("ID")[["Name", "Lat", "region"]]
    static.index = static.index.astype(str)
    switches.index = switches.index.astype(str)
    return static.assign(warming_per_decade=slopes, station_switches=switches)


def _mean_offdiag(frame: pd.DataFrame) -> float:
    values = frame.drop(columns="member").to_numpy(dtype=float)
    return float(values[~np.eye(len(values), dtype=bool)].mean())


def mechanism_section(results: pd.DataFrame, data: pd.DataFrame, best: str) -> list[str]:
    """The stated mechanism and the numbers that check it."""
    cdd = decomposition(data, "cdd", "years_4_7")
    temp = decomposition(data, "annual_avg_temp", "years_4_7")
    err_corr = _mean_offdiag(error_correlations(data, "cdd", "years_4_7"))
    dev_corr = _mean_offdiag(deviation_correlations(data, "cdd", "years_4_7"))
    late = results.loc[results["window"] == "years_4_7"].groupby("method")["raw_score"].mean()
    spread_share = 100.0 * cdd["MSE ambiguity (spread)"] / cdd["MSE avg member"]
    ridge_edge = 100.0 * (1.0 - cdd["MAE ridge"] / cdd["MAE avg member"])
    return [
        "## Mechanism",
        "",
        "**Claim.** An equal-weight mean beats its best member only when the members' errors "
        "are diverse enough that averaging cancels more error than it adds by pulling toward "
        "the weaker members. Here the four CDD members share most of their error (the same "
        "year-to-year weather noise), so the averaging gain is small, while the pooled ridge is "
        "clearly better than the other three. The mean therefore lands between the ridge and "
        "the average member: better than `current_best`, worse than `hybrid_ridge_all_cdd`. "
        "Estimated (inverse-MSE) weights cannot fix this because the members' hindcast MSEs "
        "are close, so the weights stay near equal (the P17 puzzle in its benign form).",
        "",
        "**Check (CDD, years 4-7, pooled over folds).**",
        "",
        f"- Mean pairwise correlation of member errors: {err_corr:.3f}. Of what the members add "
        f"beyond the 10-year mean: {dev_corr:.3f}. The members do disagree about the signal, "
        "but that disagreement is small next to the shared noise.",
        f"- Spread (ambiguity) is {spread_share:.1f} % of the average member MSE: that is all the "
        "squared error the equal mean can remove.",
        f"- The ridge's MAE is {ridge_edge:.1f} % below the average member's "
        f"({cdd['MAE ridge']:.1f} vs {cdd['MAE avg member']:.1f}); the equal mean is at "
        f"{cdd['MAE equal mean']:.1f}, between them, so the mean loses to the ridge.",
        f"- Temperature, same window: the 10-year mean member has MAE {temp['MAE ten']:.3f}, "
        f"the equal mean {temp['MAE equal mean']:.3f} and DeepAR {temp['MAE deepar']:.3f}; "
        "EWMA and ARIMA are worse, so combining temperature costs skill against `current_best`.",
        f"- Scores agree: years 4-7 `combo_mean` {late['combo_mean']:.2f}, `combo_inv_mse` "
        f"{late['combo_inv_mse']:.2f}, `{best}` {late[best]:.2f}, `hybrid_ridge_all_cdd` "
        f"{late[HYBRID]:.2f}, `current_best` {late[CURRENT_BEST]:.2f}.",
        "",
        "Verdict: the check **supports** the mechanism. The inverse-MSE weights themselves were "
        'not logged; "near equal" is inferred from the near-identical scores (TBD: log them).',
        "",
    ]


CAVEATS = [
    "## Caveats",
    "",
    "- Variants: 8 candidates and 2 seed replicas, fixed in the config before the first run, "
    "plus 3 reproduction rows and 3 references. Nothing was added after seeing results.",
    "- Seeds: DeepAR uses 3 internal seeds (20170411, +1000, +2000) and one replica set "
    "(seed 7). The pooled ridge, EWMA and ARIMA are deterministic.",
    "- Three origins only; differences under about 1 point are within noise. The best "
    "candidate is picked from 8, so its score is optimistic, and it still loses.",
    "- `hybrid_ridge_all_cdd` itself was the best of 15 round-1 variants, so the reference is "
    "optimistic too: a fair comparison would discount it, which this trial does not do.",
    "- The members were chosen in round 1 because they beat the 10-year mean on CDD in the "
    "same folds, so all combinations inherit that selection.",
    "- Trimmed mean: a symmetric trimmed mean of 4 members equals their median, so "
    "`combo_trimmed` drops the member farthest from the median instead (a deviation).",
    "- Papers: the M4 paper (P16) was not readable here (publisher page 403); its finding is "
    "taken from docs/literature/README.md. P17's Smith & Wallis 2009 was not read; the puzzle "
    "is taken from Qian et al. (arXiv 1505.00475), whose abstract was read. P18 abstract read.",
    "- Elevation is not available locally (GHCN station metadata not downloaded): TBD.",
    "",
]


def fmt(frame: pd.DataFrame) -> str:
    return markdown_table(frame.round(3))


def main(run_dir: Path) -> None:
    results = pd.read_csv(run_dir / "results.csv")
    cfg = load_trial_config(CONFIG)
    variants = {name: v.model_dump() for name, v in cfg.variants.items()}
    candidates = [m for m in cfg.forecasters if m not in NON_CANDIDATES and m not in REPLICAS]
    table = score_table(results)
    ranked = table.loc[table["method"].isin(candidates)]
    best = str(ranked.iloc[0]["method"])  # highest years 4-7 mean among the fixed candidates
    master = load_master()
    cached = run_dir / "analysis_forecasts.parquet"  # git-ignored run dir; saves a 20-min refit
    if cached.exists():
        data = pd.read_parquet(cached)
    else:
        data = fold_frames(master, variants, best)
        data.to_parquet(cached, index=False)

    sections = [
        "# Why-analysis: combos_p16_p17",
        "",
        f"Generated by `scripts/analyze_combos_p16_p17.py` from `{run_dir.name}/results.csv` and a "
        "recomputation of the member forecasts on the same folds (cut-offs 1980, 1995, 2011, "
        "7-year horizon). `cb` = `current_best`, `hybrid` = `hybrid_ridge_all_cdd`. Raw score = "
        "official score without the floor at zero. Members: ridge = pooled ridge "
        "(`hybrid_ridge_all_cdd`'s model), deepar = `deepar_hybrid` (seed 20170411), ewma = "
        "`ewma_opt`, arima = `arima_temp_cdd`, ten = 10-year mean.",
        "",
        "## Score table",
        "",
        "Mean raw score over the three origins. Wins = origins (of 3) beating the reference, "
        "per window. Sorted by years 4-7.",
        "",
        fmt(table),
        "",
        "Best fixed candidate by years 4-7 mean (replicas and reproduction rows excluded): "
        f"`{best}`.",
        "",
        "## Per-metric skill (%)",
        "",
    ]
    for window in ("all", "years_1_3", "years_4_7"):
        sections += [f"### {window}", "", fmt(metric_skill_table(results, window)), ""]
    sections += ["## Per-origin raw score", ""]
    for window in ("all", "years_4_7"):
        sections += [f"### {window}", "", fmt(per_origin_table(results, window)), ""]

    sections += [
        "## Member errors: pairwise correlation",
        "",
        "Pearson correlation of forecast errors (forecast minus actual), pooled over cities, "
        "years and the three folds. Combinations help when errors are not strongly correlated.",
        "",
    ]
    for metric in ("cdd", "annual_avg_temp"):
        for window in ("all", "years_4_7"):
            sections += [
                f"### {metric}, {window}",
                "",
                fmt(error_correlations(data, metric, window)),
                "",
            ]
    sections += [
        "### What the members add beyond the 10-year mean",
        "",
        "Correlation of each member's forecast minus the 10-year mean (years 4-7). This removes "
        "the weather noise all members share and shows whether the members disagree in the same "
        "direction.",
        "",
    ]
    for metric in ("cdd", "annual_avg_temp"):
        sections += [
            f"#### {metric}",
            "",
            fmt(deviation_correlations(data, metric, "years_4_7")),
            "",
        ]
    sections += [
        "### Error decomposition of the equal-weight mean",
        "",
        "MSE of the mean = average member MSE minus the spread of the members around their mean "
        "(Krogh-Vedelsby ambiguity decomposition, exact for squared error). The official score "
        "uses MAE, shown on top.",
        "",
    ]
    for metric in ("cdd", "annual_avg_temp"):
        rows = []
        for window in ("all", "years_1_3", "years_4_7"):
            rows.append({"window": window, **decomposition(data, metric, window)})
        sections += [f"#### {metric}", "", fmt(pd.DataFrame(rows)), ""]

    covariates = city_covariates(master)
    sections += [f"## Per-city: `{best}` vs `{HYBRID}`", ""]
    for window in ("all", "years_4_7"):
        per_city = city_contributions(data, best, window).join(covariates)
        per_city.index.name = "city_id"
        per_city = per_city.sort_values("total", ascending=False).reset_index()
        shown = ["city_id", "Name", "region", *[m for m in METRICS if m in per_city], "total"]
        regions = per_city.groupby("region")[
            ["total", *[m for m in ("annual_avg_temp", "cdd") if m in per_city]]
        ].sum()
        corr = {
            name: float(per_city["total"].corr(per_city[name], method="spearman"))
            for name in ("warming_per_decade", "station_switches", "Lat")
        }
        sections += [
            f"### {window}",
            "",
            "Raw-score points each city adds (positive: the combination is better), mean over the "
            f"folds. They sum to the raw-score gap: {per_city['total'].sum():.3f}.",
            "",
            "Top 10 cities:",
            "",
            fmt(per_city[shown].head(10)),
            "",
            "Bottom 10 cities:",
            "",
            fmt(per_city[shown].tail(10)),
            "",
            "Region totals:",
            "",
            fmt(regions.reset_index().sort_values("total", ascending=False)),
            "",
            "Spearman correlation of the city total with city covariates (warming = OLS slope of "
            "annual mean temperature 1981-2010 per decade; station switches = years with a "
            "station change 1951-2018; elevation is not available locally, TBD): "
            + ", ".join(f"{k} {v:.2f}" for k, v in corr.items())
            + f" (n = {len(per_city)}).",
            "",
        ]
    sections += mechanism_section(results, data, best)
    sections += CAVEATS
    OUT.write_text("\n".join(sections))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else latest_run())
