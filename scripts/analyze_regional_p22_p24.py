"""Why analysis of the ``regional_p22_p24`` trial (papers P22, P24).

Reads ``runs/trials/<stamp>_regional_p22_p24/results.csv`` (latest by default) and recomputes
per-city errors of the best P22 and best P24 variants (and ``hybrid_ridge_all_cdd``) through
the backtest API, then writes ``docs/trials/regional_p22_p24_why.md``.

Per-city numbers are *score contributions*: for each origin and metric, a city's share of the
skill difference ``(sum |e_ref| - sum |e_var|) / (n_rows x MAE of the 30-year mean)``.  They add
up, over cities and divided by 4 metrics (x 100), to the raw-score difference at that origin.

Run: ``uv run python scripts/analyze_regional_p22_p24.py [--run-dir runs/trials/<stamp>_...]``
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.backtest import CURRENT_BEST, DEFAULT_HORIZON, WINDOWS
from proto_star.climate import DEFAULT_CUTOFFS, METRICS, annual_to_long, baseline_forecast
from proto_star.data.master import load_master
from proto_star.forecasters.regional_p22_p24 import load_city_groups
from proto_star.paths import CONFIGS_DIR, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.trial import build_forecasters, load_trial_config, markdown_table

NAME = "regional_p22_p24"
CONFIG = CONFIGS_DIR / f"agent_paper_{NAME}.yaml"
ROUND1 = "hybrid_ridge_all_cdd"
REFERENCES = (CURRENT_BEST, ROUND1)
CONTROLS = (CURRENT_BEST, "ten_year_mean", ROUND1)
SHORT = {
    "annual_avg_temp": "temp",
    "total_precip_in": "precip",
    "hottest_day_temp": "hottest",
    "cdd": "cdd",
}
_KEY = ["city_id", "year", "metric"]

# MECHANISM and CHECK were written after reading the trial numbers (see the caveats).
MECHANISM = """\
**Mechanism (hypothesis).** P22: the 10-year mean lags the cutoff by about 5.5 years and the
forecast years by 5.5 + lead years, so on a warming series it is biased low; a city trend shrunk
toward its region's trend is far less noisy than a raw city trend, so adding it removes part of
that lag bias without the variance that sank raw extrapolation in round 1. P24: pooling groups
give the pooled ridge a group-specific relation between recent anomalies and the future CDD
anomaly, which helps only if the groups really differ in that relation; with about 12k rows per
lead the ridge already pools well, so we expect little from it.

**Check.** {check}
"""

CHECK = """\
Partly supported for P22, supported for P24.

- Lag bias is real: `current_best` under-forecasts temperature in years 4-7 at every origin
  (mean actual - forecast +0.71 / +0.31 / +1.40 F at 1980 / 1995 / 2011; CDD +41 / +26 / +160).
- Less noise helps, as predicted: with damping 0.5, the fully pooled regional trend
  (`p22_region_trend_damped`, 5.24 years 4-7) beats the empirical-Bayes city trend
  (`p22_eb_region_damped`, 4.73) and the elevation-band version (4.65); undamped EB loses badly
  (3.66), and so does a 50-year window (4.34).
- But the sign of a 30-year trend is not stable across regimes. At the 1980 cutoff the 1951-1980
  regional temperature trends were negative in 4 of 6 regions (North Central -0.35, Northeast
  -0.44, South Central -0.52, Southeast -0.27 F/decade), so the trend pushed forecasts down while
  the truth went up: `p22_region_trend_damped` scores -4.33 in years 4-7 at 1980 vs -1.93 for
  `current_best`. At 1995 and 2011 the trends were positive and it wins (8.82 vs 8.02, 11.22 vs
  7.95), though at 2011 the damped trend adds only about 0.17 F against a 1.40 F bias.
- Per city (years 4-7, vs `hybrid_ridge_all_cdd`) the P22 gain rises with the city's 1982-2011
  warming rate (Spearman +0.30) and the Southeast, the slowest-warming region, loses most
  (-0.39 points, mostly CDD): the trend pays where warming persisted.
- P24: pooling groups change CDD skill by at most +0.03 points in years 4-7 (population bands),
  far below noise. More flexible group models (region interactions, separate region models) gain
  in years 1-3 (+0.94 CDD skill) and lose in years 4-7 (-1.24), the pattern of fitting short-lead
  structure that does not carry to longer leads. The population-band gain lines up with city size
  (Spearman +0.35 with 2010 population) but totals only about +0.01 raw-score points.
"""


def latest_run_dir() -> Path:
    runs = sorted(TRIALS_DIR.glob(f"*_{NAME}"))
    if not runs:
        raise FileNotFoundError(f"no {NAME} run in {TRIALS_DIR}; run the trial first")
    return runs[-1]


def family(method: str) -> str:
    if method.startswith("p22_"):
        return "P22"
    if method.startswith("p24_"):
        return "P24"
    return "reference"


def score_table(results: pd.DataFrame) -> pd.DataFrame:
    """Mean raw score per window and origins won against each reference."""
    raw = results.pivot_table(index="method", columns="window", values="raw_score")
    table = raw[list(WINDOWS)].round(2)
    for ref in REFERENCES:
        ref_rows = results.loc[results["method"] == ref, ["cutoff_year", "window", "raw_score"]]
        paired = results.merge(ref_rows, on=["cutoff_year", "window"], suffixes=("", "_ref"))
        wins = (
            (paired["raw_score"] > paired["raw_score_ref"])
            .groupby([paired["method"], paired["window"]])
            .sum()
        )
        counts = wins.reset_index(name="won").pivot_table(
            index="method", columns="window", values="won", aggfunc="sum"
        )
        won = counts[list(WINDOWS)].astype(int).astype(str) + "/3"
        table[f"wins vs {ref} (all, 1-3, 4-7)"] = won.agg(", ".join, axis=1)
    table = table.rename(columns={"all": "all", "years_1_3": "yrs 1-3", "years_4_7": "yrs 4-7"})
    return table.sort_values("yrs 4-7", ascending=False).reset_index()


def metric_skill(results: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    """Mean skill (%) per metric and window, and the difference to each reference."""
    cols = [f"{m}_skill" for m in METRICS]
    mean = results.groupby(["window", "method"])[cols].mean() * 100.0
    mean.columns = [SHORT[m] for m in METRICS]
    rows = []
    for window in WINDOWS:
        for method in methods:
            row = {"window": window, "method": method, **mean.loc[(window, method)].round(2)}
            for ref in REFERENCES:
                diff = mean.loc[(window, method)] - mean.loc[(window, ref)]
                row[f"Δ vs {ref}"] = ", ".join(f"{SHORT[m]} {diff[SHORT[m]]:+.2f}" for m in METRICS)
            rows.append(row)
    return pd.DataFrame(rows)


def per_origin(results: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    frame = results.loc[results["method"].isin(methods)]
    table = frame.pivot_table(index=["window", "method"], columns="cutoff_year", values="raw_score")
    return table.round(2).reset_index()


def city_errors(master: pd.DataFrame, forecasters: dict[str, object]) -> pd.DataFrame:
    """Absolute errors per city/year/metric/origin for each method, and for the reference."""
    history = annual_to_long(master)
    frames = []
    for cutoff in DEFAULT_CUTOFFS:
        years = list(range(cutoff + 1, cutoff + DEFAULT_HORIZON + 1))
        train = master.loc[master["Year"] <= cutoff].copy()
        reference = baseline_forecast(
            history, cutoff_year=cutoff, forecast_years=years, method="thirty_year_mean"
        ).rename(columns={"predicted_value": "ref_value"})
        truth = history.loc[history["year"].isin(years)].merge(reference, on=_KEY)
        truth["cutoff_year"] = cutoff
        for name, forecaster in forecasters.items():
            forecast = forecaster(train, cutoff, years)  # type: ignore[operator]  # Forecaster
            scored = truth.merge(forecast, on=_KEY, how="inner")
            scored["method"] = name
            frames.append(scored)
    errors = pd.concat(frames, ignore_index=True)
    errors["abs_err"] = (errors["predicted_value"] - errors["actual_value"]).abs()
    errors["ref_abs_err"] = (errors["ref_value"] - errors["actual_value"]).abs()
    errors["lead"] = errors["year"] - errors["cutoff_year"]
    return errors


def city_contributions(
    errors: pd.DataFrame, method: str, against: str, leads: tuple[int, int]
) -> pd.DataFrame:
    """Per-city raw-score contribution of ``method`` minus ``against``, mean over origins."""
    window = errors.loc[errors["lead"].between(*leads)]
    a = window.loc[window["method"] == method].set_index([*_KEY, "cutoff_year"])
    b = window.loc[window["method"] == against].set_index([*_KEY, "cutoff_year"])
    against_err = b[["abs_err"]].rename(columns={"abs_err": "abs_err_against"})
    joined = a[["abs_err", "ref_abs_err"]].join(against_err).reset_index()
    norm = joined.groupby(["cutoff_year", "metric"])["ref_abs_err"].transform("sum")
    joined["contrib"] = (
        100.0 / len(METRICS) * (joined["abs_err_against"] - joined["abs_err"]) / norm
    )
    per_city = joined.pivot_table(
        index=["cutoff_year", "city_id"], columns="metric", values="contrib", aggfunc="sum"
    )
    per_city = per_city.reindex(columns=list(METRICS)).fillna(0.0)
    per_city["total"] = per_city.sum(axis=1)
    return per_city.groupby("city_id").sum() / len(DEFAULT_CUTOFFS)


def city_attributes(master: pd.DataFrame) -> pd.DataFrame:
    """Static and pre-2012 descriptors to line the per-city change up against."""
    attrs = (
        master.assign(city_id=master["ID"].astype(str))
        .groupby("city_id")
        .agg(name=("Name", "first"), region=("region", "first"))
    )
    history = annual_to_long(master.loc[master["Year"] <= 2011], cutoff_year=2011)
    temp = history.loc[(history["metric"] == "annual_avg_temp") & (history["year"] > 1981)]
    slope = temp.groupby("city_id").apply(
        lambda g: np.polyfit(g["year"], g["actual_value"], 1)[0] * 10.0 if len(g) > 10 else np.nan,
        include_groups=False,
    )
    attrs["warming_F_per_decade_1982_2011"] = slope
    changes = master.loc[master["Year"] <= 2018].groupby(master["ID"].astype(str))[
        "Station Changes"
    ]
    attrs["station_changes"] = changes.max()
    try:
        groups = load_city_groups()
        attrs = attrs.join(groups[["elevation_m", "pop_2010", "land_cover"]])
    except FileNotFoundError:
        pass
    return attrs


def city_section(contrib: pd.DataFrame, attrs: pd.DataFrame, label: str) -> list[str]:
    frame = contrib.join(attrs)
    cols = ["name", "region", "total", *METRICS]
    shown = frame[cols].rename(columns=SHORT).round(3)
    lines = [f"### {label}", ""]
    lines += [
        "Top 10 cities (gain):",
        "",
        markdown_table(shown.sort_values("total", ascending=False).head(10).reset_index()),
        "",
    ]
    lines += [
        "Bottom 10 cities (loss):",
        "",
        markdown_table(shown.sort_values("total").head(10).reset_index()),
        "",
    ]
    region = frame.groupby("region")[["total", *METRICS]].sum().rename(columns=SHORT).round(3)
    region["cities"] = frame.groupby("region").size()
    lines += [
        "Region totals (sum of city contributions, raw-score points):",
        "",
        markdown_table(region.reset_index()),
        "",
    ]
    numeric = [
        c
        for c in ("warming_F_per_decade_1982_2011", "elevation_m", "pop_2010", "station_changes")
        if c in frame
    ]
    corr = {c: frame["total"].corr(frame[c], method="spearman") for c in numeric}
    lines.append(
        "Spearman correlation of the per-city total with: "
        + ", ".join(f"{c} {v:+.2f}" for c, v in corr.items())
        + f" (n = {len(frame)}; |rho| > 0.14 is about p < 0.05)."
    )
    if "land_cover" in frame:
        lc = frame.groupby("land_cover")["total"].agg(["sum", "mean", "size"]).round(3)
        lines += ["", "By NLCD 2016 land-cover group:", "", markdown_table(lc.reset_index())]
    lines.append("")
    return lines


def main(run_dir: Path | None = None, *, check: str = CHECK) -> Path:
    run_dir = run_dir or latest_run_dir()
    results = pd.read_csv(run_dir / "results.csv")
    variants = [m for m in results["method"].unique() if family(m) != "reference"]
    means = results.loc[results["window"] == "years_4_7"].groupby("method")["raw_score"].mean()
    best = {
        fam: means[[m for m in variants if family(m) == fam]].idxmax() for fam in ("P22", "P24")
    }
    overall = max(best.values(), key=lambda m: means[m])

    cfg = load_trial_config(CONFIG)
    built = build_forecasters(cfg)
    compare = [ROUND1, CURRENT_BEST, *best.values()]
    master = load_master()
    errors = city_errors(master, {m: built[m] for m in compare})
    attrs = city_attributes(master)

    lines = [
        f"# Why analysis: {NAME} (P22 regional trends, P24 pooling groups)",
        "",
        f"Source: `{run_dir.relative_to(run_dir.parents[2])}/results.csv`; per-city numbers "
        "recomputed with the backtest API by `scripts/analyze_regional_p22_p24.py`. "
        "Folds 1980/1995/2011 (ADR 0004). Raw score = mean of the four skills x 100, "
        "without the floor at 0.",
        "",
        f"Best variant by mean years 4-7 raw score: P22 `{best['P22']}`, P24 `{best['P24']}`; "
        f"overall `{overall}`. All 12 variants are listed; none were added after the first run.",
        "",
        "## 1. Score table",
        "",
        markdown_table(score_table(results)),
        "",
        "## 2. Per-metric skill (%) and difference to the references",
        "",
        "Mean over the three origins. Metrics: temp = annual_avg_temp, precip = total_precip_in, "
        "hottest = hottest_day_temp.",
        "",
        markdown_table(metric_skill(results, [*CONTROLS, *variants])),
        "",
        "## 3. Per-origin raw score",
        "",
        markdown_table(per_origin(results, [*CONTROLS, *best.values()])),
        "",
        "## 4. Per-city and per-region breakdown",
        "",
        "Contribution to the raw-score difference (raw-score points, mean over origins). "
        "Positive = the variant is better than the comparison for that city. Warming rate is the "
        "1982-2011 OLS temperature trend (data before the last cutoff only); station changes = "
        "`Station Changes` by 2018.",
        "",
    ]
    for method in dict.fromkeys([overall, *best.values()]):
        for leads, tag in (((4, 7), "years 4-7"), ((1, 7), "all years")):
            contrib = city_contributions(errors, method, ROUND1, leads)
            lines += city_section(contrib, attrs, f"`{method}` vs `{ROUND1}`, {tag}")
    lines += [
        "## 5. Mechanism",
        "",
        MECHANISM.format(check=check),
        "## 6. Caveats",
        "",
        CAVEATS,
        "",
    ]
    out = TRIAL_NOTES_DIR / f"{NAME}_why.md"
    out.write_text("\n".join(lines).rstrip("\n") + "\n")
    print(f"Wrote {out}")
    return out


CAVEATS = """\
- 12 variants (6 P22, 6 P24), fixed in the config before the first run; no variant was added or
  changed after seeing results. The best of 12 on three origins carries selection optimism.
- All forecasters are deterministic (closed-form trends, ridge), so there are no seed replicas.
- Three origins only: differences under about 1 raw-score point are not distinguishable from noise.
- P22 is a hierarchical Bayesian space-time model on gridded data with a latent Gaussian random
  field for the trend; we replace it with method-of-moments empirical-Bayes shrinkage within
  discrete groups (no spatial field, no MCMC/INLA), on 210 station series, and use it for
  forecasting rather than trend significance.
- P24 classifies USHCN stations as urban/rural to measure the urban share of warming; we use
  population, land cover and elevation only as pooling groups. Its full text was not machine-read
  here (PDF text not extractable without a PDF library); we rely on the Crossref abstract.
- The 2010 Census and NLCD 2016 postdate the 1980 and 1995 cutoffs. They are static attributes,
  not weather, but a city's 2010 size partly reflects growth after those cutoffs (mild look-ahead
  in the group assignment for early folds only).
- NLCD land cover is read at 5 pixels per station (centre and +-~500 m), not a full buffer, and
  GHCN elevation comes from the current station inventory (station elevation is static metadata;
  an archived pre-2019 copy was not used).
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    main(args.run_dir)
