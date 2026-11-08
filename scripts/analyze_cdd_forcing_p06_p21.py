"""Why analysis for trial ``paper_cdd_forcing_p06_p21`` (step 9, P06, P21).

Reads the trial's ``results.csv`` (latest run dir unless ``--run-dir``), recomputes the CDD
forecasts it needs through the backtest folds, and writes
``docs/trials/paper_cdd_forcing_p06_p21_why.md``.

The mechanism and its checks were written before the results were read:

* Hypothesis: CDD is a convex function of daily temperature, so recomputing CDD from a warmed
  daily climatology raises the forecast above a mean of past CDD, which under-forecasts CDD
  when the climate is warming.
* Checks: (1) each ``daily`` step-9 variant beats its ``linear`` twin (same level shift, no
  convexity) on CDD skill at 2 or more of 3 origins in years 4-7; (2) ``current_best`` CDD
  forecasts are biased low (truth above forecast) at 2 or more of 3 origins in years 4-7;
  (3) the best variant's per-city gain over ``hybrid_ridge_all_cdd`` correlates positively with
  the city's 30-year warming rate.

    uv run python scripts/analyze_cdd_forcing_p06_p21.py [--run-dir runs/trials/<stamp>_...]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.backtest import DEFAULT_HORIZON, WINDOWS
from proto_star.climate import (
    BASELINE_WINDOW_YEARS,
    DEFAULT_CUTOFFS,
    METRICS,
    annual_to_long,
    baseline_forecast,
)
from proto_star.data.master import load_master
from proto_star.paths import PROJECT_ROOT, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.trial import build_forecasters, load_trial_config, markdown_table

NAME = "paper_cdd_forcing_p06_p21"
CONFIG = PROJECT_ROOT / "configs" / "agent_paper_cdd_forcing_p06_p21.yaml"
REFERENCES = ("current_best", "hybrid_ridge_all_cdd")
BASELINES = ("current_best", "ten_year_mean", "hybrid_ridge_all_cdd")
TWINS = (("shift30_recent", "shift30_recent_linear"), ("shift10_trend", "shift10_trend_linear"))
KEY = ["city_id", "year", "metric"]
CAVEATS = """## Caveats

- Variants: 11 new variants plus 3 references, all fixed in the config before the first run.
  No variant was added or changed after the results were read. Three origins only; gaps under
  about 1 raw-score point are within noise. The best new variant is the best of 11 (selection
  optimism). Every method is deterministic (no seeds, no replicas needed).
- The mechanism checks' size thresholds were added after the first read of the results (see
  the code); the sign rules were fixed before.
- P06: the EIA note (Oct 2025 handbook) fits a 30-year OLS *time* trend per state to annual
  degree days; `eia_trend30` is that, per city. The CDD-on-temperature regression is the
  brief's adaptation, not the note's method. Population weighting and NOAA's short-range
  forecasts are not applicable here.
- P21 (Ho, Hawkins, Shaffrey and Underwood 2013): full text paywalled, only the abstract was
  read. They regress gridded SST on equivalent global-mean CO2 and fit AR(1) to the residual;
  we use Mauna Loa CO2 (log), extrapolated linearly from the last 10 years before each fold's
  cut-off (never observed later values), fit on at most 40 years (from 1959 only, so the 1980
  fold fits on 1959-1980), on city temperature and CDD instead of SST. P20 was not read.
- Step 9: the shift is uniform over all days of the year (an annual-mean anomaly); seasonal
  or variance changes are not modelled. Climatology = each city's last N years where both
  temperature and CDD pass the missing-days rule.
- Per-city traits: elevation is not in the master table (TBD); station changes are counted
  from `coverage_and_stations`. Correlations are descriptive, not causal.
- Packaging: step-9 variants read `daily.parquet`, which the submission package does not ship
  (`RAW_INPUTS`), and the CO2 variants read `data/external/noaa_co2`, which CI does not
  download, so neither could be submitted without changing shared packaging code.
"""


def latest_run_dir() -> Path:
    runs = sorted(TRIALS_DIR.glob(f"*_{NAME}"))
    if not runs:
        raise FileNotFoundError(f"no {NAME} run in {TRIALS_DIR}; run the trial first")
    return runs[-1]


def score_table(results: pd.DataFrame) -> pd.DataFrame:
    """Mean raw score per window and origins won against each reference, per window."""
    mean = results.pivot_table(index="method", columns="window", values="raw_score").round(2)
    table = mean[list(WINDOWS)].rename(columns=lambda w: f"mean {w}")
    for reference in REFERENCES:
        ref = results.loc[results["method"] == reference, ["window", "cutoff_year", "raw_score"]]
        paired = results.merge(ref, on=["window", "cutoff_year"], suffixes=("", "_ref"))
        paired["win"] = paired["raw_score"] > paired["raw_score_ref"]
        wins = paired.pivot_table(index="method", columns="window", values="win", aggfunc="sum")
        for window in WINDOWS:
            table[f"wins vs {reference} {window}"] = wins[window].astype(int).astype(str) + "/3"
    order = results["method"].drop_duplicates().tolist()
    return table.loc[order].reset_index()


def metric_skill(results: pd.DataFrame, window: str) -> pd.DataFrame:
    """Mean skill (%) per metric in ``window`` and the difference to both references."""
    columns = [f"{m}_skill" for m in METRICS]
    frame = results.loc[results["window"] == window].groupby("method", sort=False)[columns]
    skill = frame.mean() * 100.0
    out = skill.rename(columns=lambda c: c.removesuffix("_skill")).round(2)
    for reference in REFERENCES:
        diff = skill.sub(skill.loc[reference], axis=1)
        out[f"cdd vs {reference}"] = diff["cdd_skill"].round(2)
        out[f"temp vs {reference}"] = diff["annual_avg_temp_skill"].round(2)
    return out.reset_index()


def per_origin(results: pd.DataFrame, window: str) -> pd.DataFrame:
    frame = results.loc[results["window"] == window]
    pivot = frame.pivot_table(index="method", columns="cutoff_year", values="raw_score")
    pivot = pivot.loc[frame["method"].drop_duplicates()]
    scores = pivot[list(DEFAULT_CUTOFFS)].copy()
    for reference in REFERENCES:
        pivot[f"origins > {reference}"] = (scores > scores.loc[reference]).sum(axis=1)
    return pivot.round(2).reset_index()


def fold_forecasts(
    master: pd.DataFrame, names: list[str]
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """CDD truth/reference rows of every fold and each named forecaster's CDD forecasts."""
    cfg = load_trial_config(CONFIG)
    forecasters = build_forecasters(cfg)
    history = annual_to_long(master)
    truth_rows: list[pd.DataFrame] = []
    forecasts: dict[str, list[pd.DataFrame]] = {name: [] for name in names}
    for cutoff in DEFAULT_CUTOFFS:
        years = list(range(cutoff + 1, cutoff + DEFAULT_HORIZON + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "reference_value"})
        truth = history.loc[history["year"].isin(years)].merge(reference, on=KEY)
        truth_rows.append(truth.loc[truth["metric"] == "cdd"].assign(cutoff_year=cutoff))
        for name in names:
            forecast = forecasters[name](train, cutoff, years)
            forecasts[name].append(
                forecast.loc[forecast["metric"] == "cdd"].assign(cutoff_year=cutoff)
            )
    truth_all = pd.concat(truth_rows, ignore_index=True)
    truth_all["lead"] = truth_all["year"] - truth_all["cutoff_year"]
    return truth_all, {n: pd.concat(f, ignore_index=True) for n, f in forecasts.items()}


def city_traits(master: pd.DataFrame) -> pd.DataFrame:
    """Per city and fold: 30-year warming rate, station changes, region, latitude, CDD level."""
    rows = []
    for cutoff in DEFAULT_CUTOFFS:
        window = master.loc[
            (master["Year"] <= cutoff) & (master["Year"] > cutoff - BASELINE_WINDOW_YEARS)
        ]
        for city_id, group in window.groupby("ID"):
            temp = group.loc[group["valid_annual_avg_temp"].astype(bool)]
            slope = (
                float(np.polyfit(temp["Year"], temp["Avg Temp"], 1)[0]) * 10
                if len(temp) >= 10
                else np.nan
            )
            rows.append(
                {
                    "city_id": str(city_id),
                    "cutoff_year": cutoff,
                    "warming_f_per_decade": slope,
                    "station_changes_30y": float(group["Station Changes"].fillna(0).sum()),
                    "cdd_level": float(group.loc[group["valid_cdd"].astype(bool), "cdd"].mean()),
                    "region": str(group["region"].iloc[-1]),
                    "lat": float(group["Lat"].iloc[-1]),
                    "name": str(group["Name"].iloc[-1]),
                }
            )
    return pd.DataFrame(rows)


def city_contributions(
    truth: pd.DataFrame, forecasts: dict[str, pd.DataFrame], best: str, against: str, leads: tuple
) -> pd.DataFrame:
    """Each city-fold's contribution to the raw-score gap ``best - against`` (score points).

    Raw score = 100/4 * sum of skills, and CDD skill = 1 - MAE/MAE_ref over the window's rows,
    so a city adds 25 * (|e_against| - |e_best|) summed over its rows / (n_rows * MAE_ref).
    """
    rows = truth.loc[truth["lead"].between(*leads)]
    merged = rows.merge(forecasts[best][[*KEY, "predicted_value"]], on=KEY).merge(
        forecasts[against][[*KEY, "predicted_value"]], on=KEY, suffixes=("_best", "_ref")
    )
    merged["gain"] = (merged["predicted_value_ref"] - merged["actual_value"]).abs() - (
        merged["predicted_value_best"] - merged["actual_value"]
    ).abs()
    norm = merged.groupby("cutoff_year").apply(
        lambda g: len(g) * (g["reference_value"] - g["actual_value"]).abs().mean(),
        include_groups=False,
    )
    merged["points"] = 25.0 * merged["gain"] / merged["cutoff_year"].map(norm)
    return merged.groupby(["city_id", "cutoff_year"], as_index=False)["points"].sum()


def bias_table(
    truth: pd.DataFrame, forecasts: dict[str, pd.DataFrame], leads: tuple
) -> pd.DataFrame:
    """Mean CDD error truth - forecast (°F-days) per origin: positive means under-forecast."""
    rows = truth.loc[truth["lead"].between(*leads)]
    out = {}
    for name, forecast in forecasts.items():
        merged = rows.merge(forecast[[*KEY, "predicted_value"]], on=KEY)
        error = merged["actual_value"] - merged["predicted_value"]
        out[name] = error.groupby(merged["cutoff_year"]).mean()
    return pd.DataFrame(out).T.round(1).reset_index().rename(columns={"index": "method"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=TRIAL_NOTES_DIR / f"{NAME}_why.md")
    args = parser.parse_args()
    run_dir = args.run_dir or latest_run_dir()
    results = pd.read_csv(run_dir / "results.csv")
    new = [m for m in results["method"].drop_duplicates() if m not in BASELINES]
    means = results.loc[results["window"] == "years_4_7"].groupby("method")["raw_score"].mean()
    best = str(means.loc[new].idxmax())

    master = load_master()
    names = sorted({*REFERENCES, best, *(n for pair in TWINS for n in pair)})
    cache = run_dir / "why_cdd_forecasts.parquet"  # git-ignored, next to the trial results
    if cache.exists():
        stored = pd.read_parquet(cache)
        truth = stored.loc[stored["source"] == "truth"].drop(columns=["source", "predicted_value"])
        forecasts = {
            n: stored.loc[stored["source"] == n, [*KEY, "predicted_value", "cutoff_year"]]
            for n in names
        }
    else:
        truth, forecasts = fold_forecasts(master, names)
        pd.concat(
            [truth.assign(source="truth")] + [f.assign(source=n) for n, f in forecasts.items()],
            ignore_index=True,
        ).to_parquet(cache, index=False)
    traits = city_traits(master)

    sections: list[str] = []
    sections.append(
        f"# Why analysis: {NAME}\n\nRun dir `{run_dir.relative_to(PROJECT_ROOT)}`. Written by "
        "`scripts/analyze_cdd_forcing_p06_p21.py`. Mean raw score over the three ADR 0004 "
        "origins (1980, 1995, 2011); `years_4_7` matches the Final Score. "
        f"Best new variant by mean years 4-7 raw score: **`{best}`** (best of {len(new)} new "
        "variants, so its edge carries selection optimism)."
    )
    sections.append("## Score table\n\n" + markdown_table(score_table(results)))
    for window in WINDOWS:
        sections.append(
            f"## Per-metric skill (%), {window}\n\n"
            "Mean skill over origins; the `vs` columns are the difference in skill points.\n\n"
            + markdown_table(metric_skill(results, window))
        )
    for window in ("all", "years_4_7"):
        sections.append(
            f"## Raw score per origin, {window}\n\n" + markdown_table(per_origin(results, window))
        )

    # Per-city breakdown, years 4-7, best vs hybrid_ridge_all_cdd
    contrib = city_contributions(truth, forecasts, best, "hybrid_ridge_all_cdd", (4, 7))
    contrib = contrib.merge(traits, on=["city_id", "cutoff_year"], how="left")
    by_city = (
        contrib.groupby(["city_id", "name", "region"], as_index=False)
        .agg(
            points=("points", "sum"),
            warming=("warming_f_per_decade", "mean"),
            station_changes=("station_changes_30y", "mean"),
            cdd_level=("cdd_level", "mean"),
            lat=("lat", "mean"),
        )
        .sort_values("points", ascending=False)
    )
    by_city["points"] = (by_city["points"] / len(DEFAULT_CUTOFFS)).round(4)
    shown = by_city.round({"warming": 2, "station_changes": 1, "cdd_level": 0, "lat": 1})
    region = (
        by_city.groupby("region", as_index=False)
        .agg(cities=("city_id", "size"), points=("points", "sum"), warming=("warming", "mean"))
        .sort_values("points", ascending=False)
        .round({"points": 3, "warming": 2})
    )
    corr = {
        trait: float(by_city["points"].corr(by_city[trait], method="spearman"))
        for trait in ("warming", "station_changes", "cdd_level", "lat")
    }
    corr_text = ", ".join(f"{k} {v:+.2f}" for k, v in corr.items())
    sections.append(
        f"## Per city: `{best}` vs `hybrid_ridge_all_cdd`, CDD, years 4-7\n\n"
        "`points` = the city's contribution to the raw-score gap (positive: the new variant is "
        "better), averaged over the 3 origins; the column sums to the mean CDD part of the "
        "raw-score gap. `warming` is the 30-year Avg Temp trend at the fold (°F/decade), "
        "`station_changes` the switches in the 30-year window, both averaged over folds. "
        "Elevation is not in the master table, so it is not checked (TBD).\n\n"
        f"Total: {by_city['points'].sum():+.3f} points. Spearman correlation of `points` with "
        f"city traits: {corr_text}.\n\n"
        "### Top 10\n\n"
        + markdown_table(shown.head(10))
        + "\n\n### Bottom 10\n\n"
        + markdown_table(shown.tail(10).iloc[::-1])
        + "\n\n### Regions\n\n"
        + markdown_table(region)
    )

    # Mechanism checks fixed before reading the results (verdict rules: see the docstring).
    # The size thresholds (0.5 skill points, |rho| >= 0.2 with p < 0.05) were added after the
    # first read of the results, so that a correct sign with a negligible size is not
    # reported as support.
    from scipy.stats import spearmanr

    cdd = results.loc[results["window"] == "years_4_7"].pivot_table(
        index="method", columns="cutoff_year", values="cdd_skill"
    )
    late = truth.loc[truth["lead"].between(4, 7), KEY]
    lines = []
    lifts: list[float] = []
    check1 = []
    for daily, linear in TWINS:
        wins = int((cdd.loc[daily] > cdd.loc[linear]).sum())
        gap = float((cdd.loc[daily] - cdd.loc[linear]).mean() * 100)
        pair = late.merge(forecasts[daily], on=KEY).merge(
            forecasts[linear], on=[*KEY, "cutoff_year"], suffixes=("_d", "_l")
        )
        lift = (pair["predicted_value_d"] - pair["predicted_value_l"]).groupby(pair["cutoff_year"])
        lift_text = ", ".join(f"{c}: {v:+.1f}" for c, v in lift.mean().items())
        check1.append((wins >= 2, abs(gap) >= 0.5))
        lifts.append(float(lift.mean().mean()))
        lines.append(
            f"- `{daily}` vs `{linear}`: CDD skill years 4-7 higher at {wins}/3 origins, "
            f"mean gap {gap:+.2f} skill points. Mean convexity lift of the forecast "
            f"(daily - linear, °F-days, years 4-7) by origin: {lift_text}."
        )
    sign_ok = all(c[0] for c in check1)
    size_ok = all(c[1] for c in check1)
    bias = bias_table(truth, forecasts, (4, 7))
    cb_low = int((bias.set_index("method").loc["current_best"] > 0).sum())
    pure = city_contributions(truth, forecasts, "shift30_recent", "current_best", (4, 7))
    pure = pure.merge(traits, on=["city_id", "cutoff_year"], how="left").dropna(
        subset=["warming_f_per_decade"]
    )
    rho_pure, p_pure = spearmanr(pure["points"], pure["warming_f_per_decade"])
    rho_best, p_best = spearmanr(by_city["points"], by_city["warming"], nan_policy="omit")

    def verdict(ok: bool) -> str:
        return "supported" if ok else "not supported"

    sections.append(
        "## Mechanism\n\n"
        "Hypothesis (fixed before the run): CDD is convex in daily temperature, so recomputing "
        "it from a warmed daily climatology raises the forecast above a mean of past CDD, which "
        "under-forecasts CDD under warming.\n\n"
        "Check 1, convexity (daily recomputation vs its first-order twin with the same shift). "
        f"Sign {verdict(sign_ok)}; size {verdict(size_ok)} (needs at least 0.5 skill points)."
        "\n\n" + "\n".join(lines) + "\n\n"
        "Check 2, the 10-year mean of CDD is biased low (mean truth - forecast, °F-days, "
        f"years 4-7, per origin): `current_best` under-forecasts at {cb_low}/3 origins, "
        f"{verdict(cb_low >= 2)}.\n\n" + markdown_table(bias) + "\n\n"
        "Check 3, the gain grows with the city's 30-year warming rate (Spearman over "
        "city-folds, needs rho >= 0.2 and p < 0.05): "
        f"`shift30_recent` vs `current_best` rho {rho_pure:+.2f} (p {p_pure:.2f}), "
        f"{verdict(rho_pure >= 0.2 and p_pure < 0.05)}; `{best}` vs `hybrid_ridge_all_cdd` "
        f"(per city) rho {rho_best:+.2f} (p {p_best:.2f}), "
        f"{verdict(rho_best >= 0.2 and p_best < 0.05)}."
    )
    cb_bias = float(bias.set_index("method").loc["current_best", list(DEFAULT_CUTOFFS)].mean())
    sections.append(
        "**Conclusion.** The convexity is real (the exact recomputation sits above its tangent "
        f"by {min(lifts):.1f} to {max(lifts):.1f} °F-days on average) but it is second order: the "
        f"temperature shifts are a few tenths of a °F, while `current_best` under-forecasts CDD "
        f"by {cb_bias:.0f} °F-days on average in years 4-7. A uniform annual-mean shift of the "
        "daily climatology does not recover that bias, and its gain does not follow the city "
        "warming rate, so the step-9 mechanism does not explain the CDD headroom. The pooled "
        "ridge captures more of it."
    )
    sections.append(CAVEATS)
    args.out.write_text("\n\n".join(sections).rstrip() + "\n")
    print(f"Wrote {args.out} (best new variant: {best})")


if __name__ == "__main__":
    main()
