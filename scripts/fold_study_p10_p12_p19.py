"""Fold design study (P10, P12, P19): re-score methods on rolling origins and compare rankings.

Two steps, so slow forecasters can run one at a time:

    uv run python scripts/fold_study_p10_p12_p19.py run --run-id <id> [--only NAME ...]
    uv run python scripts/fold_study_p10_p12_p19.py report --run-id <id>

``run`` writes ``runs/trials/fold_study/<id>/<method>.csv`` (git-ignored) plus a JSON note with
the code version, data hash, origins and run time.  ``report`` reads them and writes the
generated tables to ``docs/trials/fold_study_results.md``.  Origins, recency weights and
bootstrap settings come from the config and were fixed before the first run.  Leaderboard
numbers are not used anywhere.
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from proto_star.backtest import WINDOWS, compare_forecasters
from proto_star.climate import DEFAULT_CUTOFFS, METRICS, annual_to_long
from proto_star.data.master import content_hash, load_master
from proto_star.fold_study import (
    FoldStudyConfig,
    bootstrap_top_pick,
    build_study_forecasters,
    kendall_tau,
    leave_one_origin_out,
    load_fold_study_config,
    paired_wins,
    per_origin_ranks,
    ranks,
    recency_weights,
    score_matrix,
    warming_by_origin,
    weighted_scores,
)
from proto_star.paths import PROJECT_ROOT, TRIAL_NOTES_DIR, TRIALS_DIR
from proto_star.tracking import git_info, read_json, write_json
from proto_star.trial import markdown_table

DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "agent_fold_study_p10_p12_p19.yaml"
EXPECTED_HASH = "99128065d035cf531fe13c214e514b6bb73927ae90a80a9b903949d13abb04d1"
OUT_ROOT = TRIALS_DIR / "fold_study"
EARLY_LATE_SPLIT = 1995  # origins <= this are "early", later ones "late"


def run(
    cfg: FoldStudyConfig, run_id: str, only: list[str] | None, cutoffs: list[int] | None
) -> None:
    master = load_master()
    data_hash = content_hash(master)
    if data_hash != EXPECTED_HASH:
        raise SystemExit(f"master content hash {data_hash} != expected {EXPECTED_HASH}")
    forecasters = build_study_forecasters(cfg)
    names = only or cfg.forecasters
    unknown = sorted(set(names) - set(forecasters))
    if unknown:
        raise SystemExit(f"unknown forecasters {unknown}; configured: {cfg.forecasters}")
    origins = cutoffs or list(cfg.cutoffs)
    out_dir = OUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        target = out_dir / f"{name}.csv"
        if target.exists():
            raise SystemExit(f"{target} exists; use a new --run-id instead of overwriting")
        start = time.perf_counter()
        results = compare_forecasters({name: forecasters[name]}, master, cutoffs=origins)
        elapsed = time.perf_counter() - start
        results.to_csv(target, index=False)
        write_json(
            out_dir / f"{name}.json",
            {
                **git_info(),
                "date": datetime.now().isoformat(timespec="seconds"),
                "master_hash": data_hash,
                "method": name,
                "cutoffs": origins,
                "seconds": round(elapsed, 1),
            },
        )
        print(f"{name}: {len(origins)} origins in {elapsed:.0f} s -> {target}")


def _fmt(frame: pd.DataFrame, digits: int = 2) -> str:
    # object dtype keeps integer columns (years, counts) from printing as floats
    return markdown_table(frame.round(digits).reset_index().astype(object))


def report(cfg: FoldStudyConfig, run_id: str, out_path: Path) -> None:
    out_dir = OUT_ROOT / run_id
    frames, notes = [], {}
    for name in cfg.forecasters:
        path = out_dir / f"{name}.csv"
        if not path.exists():
            raise SystemExit(f"missing results for {name}: {path}")
        frames.append(pd.read_csv(path))
        notes[name] = read_json(out_dir / f"{name}.json")
    results = pd.concat(frames, ignore_index=True)
    dense = list(cfg.cutoffs)
    adr = list(DEFAULT_CUTOFFS)
    other = [c for c in dense if c not in adr]
    refs = cfg.study.references
    hl = cfg.study.half_life_years
    weights = {
        "equal": recency_weights(dense, "equal"),
        "linear": recency_weights(dense, "linear"),
        "exponential": recency_weights(dense, "exponential", half_life_years=hl),
    }
    weights_adr = {
        "equal": recency_weights(adr, "equal"),
        "linear": recency_weights(adr, "linear"),
        "exponential": recency_weights(adr, "exponential", half_life_years=hl),
    }
    commits = sorted({f"{n['commit']}{' (dirty)' if n['dirty'] else ''}" for n in notes.values()})
    seconds = pd.DataFrame(
        {
            "method": list(notes),
            "origins": [len(n["cutoffs"]) for n in notes.values()],
            "seconds": [n["seconds"] for n in notes.values()],
        }
    ).set_index("method")

    out: list[str] = [
        f"# Fold study results (generated): {cfg.name}",
        "",
        "Generated by `scripts/fold_study_p10_p12_p19.py report`; do not edit by hand. "
        "Write-up: [fold_study.md](fold_study.md).",
        "",
        "| Item | Value |",
        "|---|---|",
        "| Config | `configs/agent_fold_study_p10_p12_p19.yaml` |",
        f"| Run dir | `runs/trials/fold_study/{run_id}/` (git-ignored) |",
        f"| Code version(s) | {', '.join(f'`{c}`' for c in commits)} |",
        f"| Data hash | `{EXPECTED_HASH}` |",
        f"| Dense origins | {dense} ({len(dense)}), 7-year horizon |",
        f"| ADR 0004 origins | {adr} |",
        f"| Recency weights | linear (1..n), exponential (half-life {hl:g} years "
        f"from {max(dense)}) |",
        f"| Bootstrap | {cfg.study.n_bootstrap} origin resamples, seed {cfg.study.seed} |",
        "",
        "Run time per method:",
        "",
        _fmt(seconds, 1),
        "",
        "Weights per origin:",
        "",
        _fmt(pd.DataFrame(weights).T, 3),
        "",
    ]

    summary_rows = []
    for window in WINDOWS:
        matrix = score_matrix(results, window, cutoffs=dense)
        out += [f"## Window `{window}`", "", "### Raw score per origin", "", _fmt(matrix), ""]
        out += ["### Rank per origin (1 = best)", "", _fmt(per_origin_ranks(matrix)), ""]

        rankings = {
            "adr3_equal": weighted_scores(matrix[adr], weights_adr["equal"]),
            "dense_equal": weighted_scores(matrix, weights["equal"]),
            "dense_non_adr": weighted_scores(matrix[other]),
            "dense_linear": weighted_scores(matrix, weights["linear"]),
            "dense_exponential": weighted_scores(matrix, weights["exponential"]),
            "adr3_exponential": weighted_scores(matrix[adr], weights_adr["exponential"]),
            "early_origins": weighted_scores(matrix[[c for c in dense if c <= EARLY_LATE_SPLIT]]),
            "late_origins": weighted_scores(matrix[[c for c in dense if c > EARLY_LATE_SPLIT]]),
        }
        table = pd.DataFrame(rankings)
        rank_table = table.apply(ranks)
        out += [
            "### Mean score under each design",
            "",
            _fmt(table.sort_values("dense_equal", ascending=False)),
            "",
        ]
        out += ["### Rank under each design", "", _fmt(rank_table.sort_values("dense_equal")), ""]
        taus = {
            f"adr3_equal vs {k}": kendall_tau(rankings["adr3_equal"], v)
            for k, v in rankings.items()
            if k != "adr3_equal"
        }
        taus["dense_equal vs dense_exponential"] = kendall_tau(
            rankings["dense_equal"], rankings["dense_exponential"]
        )
        taus["early_origins vs late_origins"] = kendall_tau(
            rankings["early_origins"], rankings["late_origins"]
        )
        out += [
            "### Kendall tau-b between rankings",
            "",
            _fmt(pd.Series(taus, name="tau").to_frame(), 3),
            "",
        ]
        for key, scores in rankings.items():
            summary_rows.append(
                {
                    "window": window,
                    "design": key,
                    "top": scores.index[0],
                    "top_score": scores.iloc[0],
                    "runner_up": scores.index[1],
                    "margin": scores.iloc[0] - scores.iloc[1],
                }
            )

        vs_rows = []
        for method in matrix.index:
            row: dict[str, object] = {"method": method}
            for ref in refs:
                diff = matrix.loc[method] - matrix.loc[ref]
                for label, w in (("eq", weights["equal"]), ("exp", weights["exponential"])):
                    row[f"vs {ref} ({label})"] = float(diff @ w)
                won, n = paired_wins(matrix, method, ref)
                won3, n3 = paired_wins(matrix[adr], method, ref)
                row[f"wins vs {ref}"] = f"{won}/{n} (ADR {won3}/{n3})"
            vs_rows.append(row)
        out += [
            "### Difference from the references (weighted mean raw score) and origins won",
            "",
            _fmt(pd.DataFrame(vs_rows).set_index("method")),
            "",
        ]

        looo = leave_one_origin_out(matrix)
        looo_exp = leave_one_origin_out(matrix, weights["exponential"])
        looo["top_exponential"] = looo_exp["top"]
        looo["margin_exponential"] = looo_exp["margin"]
        out += ["### Leave one origin out (dense set)", "", markdown_table(looo.round(2)), ""]
        boot = pd.DataFrame(
            {
                "dense_equal": bootstrap_top_pick(
                    matrix, n_boot=cfg.study.n_bootstrap, seed=cfg.study.seed
                ),
                "dense_exponential": bootstrap_top_pick(
                    matrix,
                    n_boot=cfg.study.n_bootstrap,
                    seed=cfg.study.seed,
                    weights=weights["exponential"],
                ),
                "adr3_equal": bootstrap_top_pick(
                    matrix[adr], n_boot=cfg.study.n_bootstrap, seed=cfg.study.seed
                ),
            }
        ).fillna(0.0)
        out += [
            "### Bootstrap share of resamples where each method is top",
            "",
            _fmt(boot.sort_values("dense_equal", ascending=False), 3),
            "",
        ]

        skill_rows = []
        for metric in METRICS:
            sm = score_matrix(results, window, value=f"{metric}_skill", cutoffs=dense) * 100.0
            for era, cols in (
                ("early", [c for c in dense if c <= EARLY_LATE_SPLIT]),
                ("late", [c for c in dense if c > EARLY_LATE_SPLIT]),
                ("adr3", adr),
                ("dense", dense),
            ):
                for method in sm.index:
                    skill_rows.append(
                        {
                            "metric": metric,
                            "era": era,
                            "method": method,
                            "skill": float(sm.loc[method, cols].mean()),
                        }
                    )
        skills = pd.DataFrame(skill_rows).pivot_table(
            index=["metric", "method"], columns="era", values="skill"
        )[["adr3", "dense", "early", "late"]]
        out += [
            f"### Per-metric skill (%) by origin group (early <= {EARLY_LATE_SPLIT} < late)",
            "",
            _fmt(skills),
            "",
        ]

        trend_rows = []
        years = np.asarray(dense, dtype=float)
        for method in matrix.index:
            row = {"method": method}
            for ref in refs:
                diff = (matrix.loc[method] - matrix.loc[ref]).to_numpy()
                row[f"slope vs {ref} per decade"] = float(np.polyfit(years, diff, 1)[0] * 10)
            trend_rows.append(row)
        out += [
            "### Does the gap to each reference grow with the origin year? (OLS slope)",
            "",
            _fmt(pd.DataFrame(trend_rows).set_index("method")),
            "",
        ]

    history = annual_to_long(load_master())
    out += [
        "## Warming signal per origin (diagnostic only)",
        "",
        "City-mean values. `pre_trend_per_decade` uses only years up to the cut-off. The shifts "
        "compare forecast years with the 10- and 30-year means at the cut-off, so they use test "
        "years: they explain results and are never used to forecast or select.",
        "",
    ]
    for metric in ("annual_avg_temp", "cdd"):
        for leads in ((1, 3), (4, 7)):
            warm = warming_by_origin(history, dense, metric=metric, leads=leads).set_index(
                "cutoff_year"
            )
            out += [f"### `{metric}`, forecast years {leads[0]}-{leads[1]}", "", _fmt(warm, 3), ""]
            window = "years_1_3" if leads == (1, 3) else "years_4_7"
            matrix = score_matrix(results, window, cutoffs=dense)
            skill = score_matrix(results, window, value=f"{metric}_skill", cutoffs=dense)
            corr_rows = []
            for method in matrix.index:
                for ref in refs:
                    if method == ref:
                        continue
                    gaps = {
                        "raw score": matrix.loc[method] - matrix.loc[ref],
                        f"{metric} skill": (skill.loc[method] - skill.loc[ref]) * 100.0,
                    }
                    for label, diff in gaps.items():
                        if np.allclose(diff, 0.0):
                            continue  # identical forecasts for this metric: no correlation
                        corr_rows.append(
                            {
                                "method": method,
                                "reference": ref,
                                "gap": label,
                                "mean gap": float(diff.mean()),
                                "corr with pre_trend": float(
                                    np.corrcoef(diff, warm["pre_trend_per_decade"])[0, 1]
                                ),
                                "corr with shift_vs_10y": float(
                                    np.corrcoef(diff, warm["shift_vs_10y"])[0, 1]
                                ),
                            }
                        )
            out += [
                f"Correlation across origins of each `{window}` gap with this metric's signal "
                "(gaps that are zero at every origin are left out):",
                "",
                markdown_table(pd.DataFrame(corr_rows).round(2)),
                "",
            ]

    summary = pd.DataFrame(summary_rows)
    out += ["## Top pick under each design", "", markdown_table(summary.round(2)), ""]
    out_path.write_text("\n".join(out))
    print(f"wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["run", "report"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--only", nargs="*", help="run only these forecasters")
    parser.add_argument(
        "--cutoffs",
        nargs="*",
        type=int,
        help="override origins for a slow method (say so in the write-up)",
    )
    parser.add_argument("--out", type=Path, default=TRIAL_NOTES_DIR / "fold_study_results.md")
    args = parser.parse_args()
    cfg = load_fold_study_config(args.config)
    if args.command == "run":
        run(cfg, args.run_id, args.only, args.cutoffs)
    else:
        report(cfg, args.run_id, args.out)


if __name__ == "__main__":
    main()
