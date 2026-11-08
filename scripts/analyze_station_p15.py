"""Why analysis for the ``station_p15`` trial (paper P15: station segments and neighbor steps).

Reads the latest ``runs/trials/<stamp>_station_p15/results.csv`` for the score tables, then
recomputes the forecasts of a few variants on the ADR 0004 folds to split the score change by
city, by region, and by whether a station switch falls inside the averaging window.  Writes
``docs/trials/station_p15_why.md``.

    uv run python scripts/analyze_station_p15.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.backtest import DEFAULT_HORIZON, WINDOWS, resolve_forecaster
from proto_star.climate import (
    DEFAULT_CUTOFFS,
    METRICS,
    annual_to_long,
    baseline_forecast,
)
from proto_star.data.master import load_master
from proto_star.forecasters import _pooled_features as feats
from proto_star.forecasters.station_p15 import (
    StepParams,
    city_distances,
    estimate_steps,
    station_panels,
    window_years,
)
from proto_star.paths import CONFIGS_DIR, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.trial import load_trial_config

NAME = "station_p15"
CONFIG = CONFIGS_DIR / "agent_paper_station_p15.yaml"
OUT = TRIAL_NOTES_DIR / f"{NAME}_why.md"
REFS = ("current_best", "hybrid_ridge_all_cdd")
# Pairs recomputed per city: (variant, reference). The first is the best variant overall.
PAIRS = (
    ("adj_temp_k5_w5_ridge_cdd", "hybrid_ridge_all_cdd"),
    ("adj_temp_cdd_k10_w10", "current_best"),
    ("seg_temp_cdd_min3", "current_best"),
)
SHORT = {
    "annual_avg_temp": "temp",
    "total_precip_in": "precip",
    "hottest_day_temp": "hottest",
    "cdd": "cdd",
}
KEY = ["city_id", "year", "metric"]
# Interpretation written after reading the tables above (sections 1-5 are generated).
MECHANISM = """## 6. Mechanism and check

**Hypothesis.** A station switch inside the 10-year window mixes two sites in the mean. If
the old site reads differently by a step *s*, the mean is off by about *s* times the share
of old-station years, while the forecast years are measured at the new site. Removing the
step (pairwise neighbor estimate, P15) or dropping the old years (current segment) should
then help at the switched city-origins, more so for larger steps.

**Check.**

- Where the change lives: only city-origins with a switch inside the window change, by
  construction (section 5). That is 39 of 630 city-origins (6 %), and a temperature step
  could be estimated and applied at only 19 of them; switches in the last two years before
  the cut-off have too few clean years on the new side.
- Direction: supported weakly. More switched city-origins improve than worsen for the
  adjusted variant on its own (`adj_temp_cdd_k10_w10`, years 4-7: 12 better, 5 worse) but
  the segment variant is close to a coin flip (11 vs 10).
- Size of the step: **not supported.** The Spearman correlation between |estimated step|
  and the temperature gain is near zero or negative in every pair (section 5), so larger
  steps did not give larger gains.
- Concentration: the gains of the P15-only variants (+0.07 to +0.09 raw points) come mostly
  from one city, McCook (NE), which switched inside the window at two origins (plus
  Escondido for the segment variant).
- Against the submitted `hybrid_ridge_all_cdd`, the best variant only changes temperature at
  the switched cities: -0.05 skill points for temperature in years 4-7 and a raw score of
  5.53 vs 5.54. CDD is identical (ridge) and precipitation/hottest day are unchanged.
- Warming rate, region: no relation (Spearman of the 30-year warming rate with the change
  is about 0; the region totals are within +-0.08). Elevation: TBD (not in the master
  table, and this track uses no external data).

**Verdict.** The mechanism is real but tiny for this score: few switches fall inside the
averaging window, the step estimates from five neighbours over +-5 years are noisy (the
standard error of an applied step was about 0.2-0.7 degF for steps of 0.3-2.5 degF), and a 10-year
mean already keeps half its years on the new station. The station effect is far below the
fold-to-fold noise (differences under about 1 point are not distinguishable on 3 origins).
"""
CAVEATS = """## 7. Caveats

- 9 station variants plus 3 references, all fixed in the config before the first run. No
  variant was added after seeing results. Every method is deterministic (no seeds).
- `seg_temp_cdd_cap15` was meant as "segment capped at 15 years", but the cap also widens
  the fallback window to 15 years, so it mostly measures a 15-year mean. It lost badly
  (2.61 in years 4-7), as the 15-year mean did in `baselines_round1`.
- Selection optimism: the best P15-only variant is the best of 8 on 3 origins; its +0.07
  over `current_best` is well inside noise.
- Deviations from P15 (Menne & Williams 2009): break dates come from our station metadata
  instead of the SNHT pairwise break search; steps use simple before/after means of the
  city-minus-neighbor-mean difference over +-5 or +-10 years, not the paper's
  multi-pair attribution and median of pairwise estimates; annual, not monthly, values; one
  additive step for every metric (precipitation and CDD included); neighbours chosen by
  distance only, not by correlation. Paper full text was not read here (journal page); the
  method follows its abstract and the standard description of the pairwise algorithm.
- 5 of the 39 switched city-origins have no scored rows in the test years, so section 5
  counts 34.
"""


def latest_results() -> tuple[Path, pd.DataFrame]:
    runs = sorted(TRIALS_DIR.glob(f"*_{NAME}"))
    if not runs:
        raise FileNotFoundError(f"no {NAME} trial in {TRIALS_DIR}; run the trial first")
    return runs[-1], pd.read_csv(runs[-1] / "results.csv")


def md_table(frame: pd.DataFrame, digits: int = 2) -> str:
    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in frame.itertuples(index=False):
        cells = [f"{v:.{digits}f}" if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def score_table(results: pd.DataFrame) -> pd.DataFrame:
    """Mean raw score per window and origins won against each reference."""
    pivot = results.pivot_table(
        index=["method", "cutoff_year"], columns="window", values="raw_score"
    )
    rows = []
    for method in sorted(results["method"].unique()):
        row: dict[str, object] = {"method": method}
        for window in WINDOWS:
            row[window] = float(pivot.loc[method, window].mean())
        for ref in REFS:
            wins = [int((pivot.loc[method, w] > pivot.loc[ref, w] + 1e-12).sum()) for w in WINDOWS]
            row[f"wins vs {ref} (all/1-3/4-7)"] = "/".join(str(w) for w in wins)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("years_4_7", ascending=False)


def skill_table(results: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    """Per-metric skill (percent) by window, with the change vs both references."""
    skill_cols = [f"{m}_skill" for m in METRICS]
    mean = results.groupby(["method", "window"])[skill_cols].mean() * 100.0
    rows = []
    for method in methods:
        for window in WINDOWS:
            row: dict[str, object] = {"method": method, "window": window}
            for metric in METRICS:
                value = float(mean.loc[(method, window), f"{metric}_skill"])
                row[SHORT[metric]] = value
                for ref in REFS:
                    ref_value = float(mean.loc[(ref, window), f"{metric}_skill"])
                    row[f"{SHORT[metric]} vs {ref.split('_')[0]}"] = value - ref_value
            rows.append(row)
    return pd.DataFrame(rows)


def origin_table(results: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    sub = results.loc[results["method"].isin([*methods, *REFS])]
    pivot = sub.pivot_table(index="method", columns=["window", "cutoff_year"], values="raw_score")
    pivot.columns = [f"{w} {c}" for w, c in pivot.columns]
    return pivot.reset_index()


def city_contributions(
    master: pd.DataFrame, variant: str, reference: str, variants: dict
) -> pd.DataFrame:
    """Per city, origin and window: share of the raw-score change (sums to the difference)."""
    history = annual_to_long(master)
    out = []
    forecasters = {n: resolve_forecaster(n, variants=variants) for n in (variant, reference)}
    for cutoff in DEFAULT_CUTOFFS:
        years = list(range(cutoff + 1, cutoff + DEFAULT_HORIZON + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        clim = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "clim"})
        truth = history.loc[history["year"].isin(years)].merge(clim, on=KEY)
        for label, forecaster in forecasters.items():
            pred = forecaster(train, cutoff, years)[[*KEY, "predicted_value"]]
            truth = truth.merge(pred.rename(columns={"predicted_value": label}), on=KEY)
        truth["lead"] = truth["year"] - cutoff
        for window, (lo, hi) in WINDOWS.items():
            rows = truth.loc[truth["lead"].between(lo, hi)].copy()
            denom = rows.groupby("metric").apply(
                lambda g: len(g) * (g["clim"] - g["actual_value"]).abs().mean(),
                include_groups=False,
            )
            gain = (rows[reference] - rows["actual_value"]).abs() - (
                rows[variant] - rows["actual_value"]
            ).abs()
            rows["contrib"] = 100.0 / len(METRICS) * gain / rows["metric"].map(denom)
            per = rows.pivot_table(
                index="city_id", columns="metric", values="contrib", aggfunc="sum", fill_value=0.0
            )
            per = per.reindex(columns=list(METRICS), fill_value=0.0)
            per["total"] = per.sum(axis=1)
            per["cutoff_year"] = cutoff
            per["window"] = window
            out.append(per.reset_index())
    return pd.concat(out, ignore_index=True)


def switch_info(master: pd.DataFrame, params: StepParams) -> pd.DataFrame:
    """Per city and origin: switch inside the temperature/CDD and 30-year windows, and steps."""
    rows = []
    for cutoff in DEFAULT_CUTOFFS:
        train = master.loc[master["Year"] <= cutoff].copy()
        panels = feats.wide_panels(train, cutoff)
        segment, changes = station_panels(train, cutoff)
        temp = panels["annual_avg_temp"].reindex(columns=segment.columns)
        _, steps = estimate_steps(
            temp,
            segment,
            changes,
            city_distances(train),
            metric="annual_avg_temp",
            window=10,
            cutoff_year=cutoff,
            params=params,
        )
        applied = steps.loc[steps["applied"]].groupby("city_id")["step"].sum()
        estimated = set(steps["city_id"])
        prcp = panels["total_precip_in"].reindex(columns=segment.columns)
        for city in segment.index:
            seg = segment.loc[city]
            first_years = seg.index[1:][seg.to_numpy()[1:] != seg.to_numpy()[:-1]]
            t_win = window_years(temp.loc[city], "annual_avg_temp", 10, cutoff)
            p_win = window_years(prcp.loc[city], "total_precip_in", 30, cutoff)
            t_start = int(t_win.index.min()) if len(t_win) else cutoff
            p_start = int(p_win.index.min()) if len(p_win) else cutoff
            recent = temp.loc[city].loc[cutoff - 29 : cutoff].dropna()
            slope = (
                float(np.polyfit(recent.index.to_numpy(float), recent.to_numpy(), 1)[0]) * 10
                if len(recent) >= 10
                else np.nan
            )
            rows.append(
                {
                    "city_id": city,
                    "cutoff_year": cutoff,
                    "switch_in_10y": bool(any(b > t_start for b in first_years)),
                    "switch_in_30y": bool(any(b > p_start for b in first_years)),
                    "step_estimated": city in estimated,
                    "temp_step_applied": float(applied.get(city, 0.0)),
                    "warming_f_per_decade": slope,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    run_dir, results = latest_results()
    cfg = load_trial_config(CONFIG)
    variants = {k: v.model_dump() for k, v in cfg.variants.items()}
    master = load_master()
    region = master.groupby("ID")["region"].first()
    name = master.groupby("ID")["Name"].first()

    scores = score_table(results)
    station_methods = [m for m in cfg.forecasters if m not in (*REFS, "ten_year_mean")]
    best = PAIRS[0][0]
    skills = skill_table(results, [best, "adj_temp_cdd_k10_w10", "seg_temp_cdd_min3"])
    origins = origin_table(results, [best, "adj_temp_cdd_k10_w10", "seg_temp_cdd_min3"])

    k5 = StepParams(n_neighbors=5, side_years=5, min_side_years=3, max_km=1000.0)
    info = switch_info(master, k5)
    counts = info.groupby("cutoff_year").agg(
        cities=("city_id", "size"),
        switch_in_10y=("switch_in_10y", "sum"),
        switch_in_30y=("switch_in_30y", "sum"),
        temp_step_applied=("temp_step_applied", lambda s: int((s != 0).sum())),
    )
    counts = counts.reset_index()

    lines: list[str] = [
        f"# Why analysis: {NAME}",
        "",
        f"Source run: `{run_dir.relative_to(run_dir.parents[2])}` (results.csv), plus forecasts",
        "recomputed on the same ADR 0004 folds (1980, 1995, 2011; 7-year horizon) for the",
        "per-city split. Made by `scripts/analyze_station_p15.py`. Raw score = official score",
        "without its floor at zero. Nothing here uses leaderboard numbers.",
        "",
        "## 1. Score table",
        "",
        "Mean raw score over the three origins, and the origins (of 3) where the method beats",
        "each reference, per window (all / years 1-3 / years 4-7). Years 4-7 match the Final",
        "Score.",
        "",
        md_table(scores),
        "",
        "## 2. How many city-origins have a station switch in the averaging window",
        "",
        "A switch counts when a new `Station Segment` starts after the first year of the window",
        "that `current_best` averages: last 10 valid years (temperature/CDD) or the 30 calendar",
        "years to the cut-off (precipitation/hottest day). `temp_step_applied` counts cities where",
        "the k=5, ±5-year pairwise estimate could be made and was applied to temperature (it needs",
        "3 clean years on both sides of the switch, so switches in the last 2 years are skipped).",
        "",
        md_table(counts),
        "",
        f"Total over the three origins: {int(counts['switch_in_10y'].sum())} of "
        f"{int(counts['cities'].sum())} city-origins for the 10-year window and "
        f"{int(counts['switch_in_30y'].sum())} for the 30-year window. Every other city-origin "
        "gets exactly the reference forecast, by construction.",
        "",
        "## 3. Per-metric skill (percent), by window",
        "",
        "`x vs current` / `x vs hybrid` are the skill change against `current_best` and",
        "`hybrid_ridge_all_cdd` in percentage points.",
        "",
        md_table(skills),
        "",
        "## 4. Per-origin raw score",
        "",
        md_table(origins),
        "",
    ]

    for variant, reference in PAIRS:
        contrib = city_contributions(master, variant, reference, variants)
        merged = contrib.merge(info, on=["city_id", "cutoff_year"], how="left")
        merged["region"] = merged["city_id"].map(region)
        lines += [f"## 5. Per city: `{variant}` vs `{reference}`", ""]
        for window in ("all", "years_4_7"):
            sub = merged.loc[merged["window"] == window]
            split = (
                sub.groupby("switch_in_10y")
                .agg(
                    city_origins=("total", "size"),
                    raw_score_change=("total", "sum"),
                    improved=("total", lambda s: int((s > 1e-9).sum())),
                    worse=("total", lambda s: int((s < -1e-9).sum())),
                )
                .reset_index()
            )
            split["raw_score_change"] = split["raw_score_change"] / len(DEFAULT_CUTOFFS)
            lines += [
                f"**{window}**: mean raw-score change over origins split by switch in the 10-year "
                "window (sums to the score difference).",
                "",
                md_table(split, 3),
                "",
            ]
        sub = merged.loc[merged["window"] == "years_4_7"]
        per_city = sub.groupby("city_id")[["total", *METRICS]].sum() / len(DEFAULT_CUTOFFS)
        per_city["name"] = per_city.index.map(name)
        per_city["region"] = per_city.index.map(region)
        per_city["switch_origins"] = sub.groupby("city_id")["switch_in_10y"].sum()
        per_city["temp_step"] = sub.groupby("city_id")["temp_step_applied"].sum()
        show = ["name", "region", "switch_origins", "temp_step", "total", "annual_avg_temp", "cdd"]
        ranked = per_city.sort_values("total")
        moved = ranked.loc[ranked["total"].abs() > 1e-9]
        lines += [
            f"Years 4-7, {len(moved)} cities change at all. Top 10 (largest gain) and bottom 10:",
            "",
            md_table(moved.sort_values("total", ascending=False)[show].head(10).reset_index(), 3),
            "",
            md_table(moved[show].head(10).reset_index(), 3),
            "",
        ]
        regions = (
            per_city.groupby("region")
            .agg(cities=("total", "size"), change=("total", "sum"))
            .reset_index()
            .sort_values("change")
        )
        lines += ["Region totals (years 4-7):", "", md_table(regions, 3), ""]
        total = float(per_city["total"].sum())
        top = per_city["total"].idxmax()
        lines += [
            f"Years 4-7 total change {total:.3f} points; the largest single city "
            f"({per_city.loc[top, 'name']}) contributes {float(per_city.loc[top, 'total']):.3f}.",
            "",
        ]
        sw = sub.loc[sub["temp_step_applied"] != 0].copy()
        if len(sw) >= 4:
            sw["abs_step"] = sw["temp_step_applied"].abs()
            rho_step = sw[["abs_step", "annual_avg_temp"]].corr(method="spearman").iloc[0, 1]
            rho_warm = sub[["warming_f_per_decade", "total"]].corr(method="spearman").iloc[0, 1]
            lines += [
                f"City-origins with an applied temperature step: {len(sw)}. "
                "Spearman correlation of "
                f"|temperature step| with the temperature contribution: {rho_step:.2f}. "
                f"Spearman of 30-year warming rate (all city-origins) with the total contribution: "
                f"{rho_warm:.2f}.",
                "",
            ]
    lines += [MECHANISM, CAVEATS]
    lines += [
        "## 8. Variants in this trial",
        "",
        ", ".join(f"`{m}`" for m in station_methods)
        + f" ({len(station_methods)} station variants, all fixed before the first run).",
        "",
    ]
    OUT.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
