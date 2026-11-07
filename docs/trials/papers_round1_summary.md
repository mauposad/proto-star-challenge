# Papers round 1: cross-track summary

Four literature tracks were run in parallel on 2026-11-06/07, each on its own branch, through
the shared forecaster registry (`src/proto_star/forecasters/`). All of them use the same
ADR 0004 folds (cut-offs 1980, 1995, 2011, 7-year horizon), the same master table (content hash
`99128065…bb04d1`) and the same official raw score. Nothing here was selected on leaderboard
scores. This page is a draft for team discussion. It decides nothing; adopting a method needs an
ADR and a person.

Per-track details:

| Track | Papers | Trial write-up | Paper card(s) |
|---|---|---|---|
| ARIMA per city | P13 | [paper_p13_arima.md](paper_p13_arima.md) | [2020_lai_arima](../../papers/2020_lai_arima/README.md) |
| Pooled global model | P09, P14 | [paper_p09_p14_pooled.md](paper_p09_p14_pooled.md) | [2021_montero-manso_global_pooled](../../papers/2021_montero-manso_global_pooled/README.md) |
| Climate normals + GEV | P02, P03, P04, P23 | [paper_normals_gev.md](paper_normals_gev.md) | [2013_wilks_livezey_normals](../../papers/2013_wilks_livezey_normals/README.md) |
| Neural, from scratch | P05, P08 | [paper_neural.md](paper_neural.md) | [2019_oreshkin_nbeats](../../papers/2019_oreshkin_nbeats/README.md), [2020_salinas_deepar](../../papers/2020_salinas_deepar/README.md) |

## Best variant per track

Mean raw score over the three folds. "Wins 4–7" counts the origins where the method beats
`current_best` in forecast years 4–7, the window that matches the Final Score.

| Method | Track | All | Years 1–3 | Years 4–7 | Wins 4–7 | Note |
|---|---|---|---|---|---|---|
| `hybrid_ridge_all_cdd` | Pooled | **3.60** | 0.94 | **5.54** | **3 / 3** | Pooled ridge for CDD only; `current_best` for the rest. Also wins 3 / 3 over all years |
| `deepar_hybrid` | Neural | 3.36 | 0.96 | 5.08 | 1 / 3 | Seed-7 replica: 3.03 / 0.83 / 4.63 |
| `hybrid_a` | Normals | 3.25 | 1.14 | 4.90 | 2 / 3 | Components picked after seeing results; one "win" is +0.06 |
| `nbeats_hybrid` | Neural | 3.08 | 0.78 | 4.57 | 1 / 3 | Seed-7 replica: 2.88 / 1.23 / 4.03 |
| `gev_stationary` | Normals | 2.92 | 0.67 | 4.69 | 2 / 3 | Ties `current_best` (stationary GEV median ≈ 30-year mean) |
| `current_best` | reference | 2.92 | 0.63 | 4.68 | – | 10-year mean for temperature/CDD, 30-year mean for precipitation/hottest day |
| `arima_temp_cdd` | ARIMA | 2.21 | 1.11 | 2.98 | 0 / 3 | The paper's method on all metrics: 0.26 / -0.96 / 1.06 |
| `ten_year_mean` | baseline | 1.34 | -0.62 | 2.78 | 0 / 3 | |

## What the four tracks agree on

1. **CDD is where the headroom is.** Four unrelated methods beat the 10-year mean on CDD skill
   in years 4–7 (`current_best` 6.84 %): pooled ridge 10.27 %, DeepAR 8.18 %, EWMA chosen by
   hindcast 7.65 %, ARIMA 7.16 %. Independent methods pointing the same way make this the most
   credible finding of the round.
2. **Temperature: the 10-year mean is hard to beat.** Only `deepar_hybrid` edges it in years
   4–7 (12.15 % vs 11.90 %), within seed noise. Pooled models shrink toward the 30-year level
   and miss recent warming. Hindcast-chosen windows and EWMAs are worse in years 4–7.
3. **Precipitation and hottest day: the 30-year mean is unbeaten.** Every model run on those
   two metrics loses or ties. This matches the kickoff deck: those two are mostly noise.
4. **Trends extrapolate badly.** ARIMA drift, GEV location trends (even shrunk to 25 %), and
   damped trends (the hindcast picked no trend at every fold) all lose, as `linear_trend` and
   `hinge_fit` did in `baselines_round1`.
5. **Simple beats complex for what does work.** Squared-loss ridge beat the pinball-loss
   median model and gradient boosting. Small neural models helped only through the
   temperature/CDD hybrid.

## Caveats

- Three origins only. Differences under about 1 point are not distinguishable from noise.
- Selection optimism. `hybrid_ridge_all_cdd` was the best of 15 variants; `hybrid_a` was
  assembled after seeing results; the neural hybrids have one replica seed each.
- The P03/P04 full texts and the P13 journal page were not readable (paywall or 403). Those
  tracks follow abstracts, standard definitions and, for P13, the authors' unlicensed public R
  code, which was only read; the Python was written from scratch. See each card's deviations.
- Trial notes record their code version as `e507f5e` with uncommitted changes, because the
  trials ran before the track commits. Results match the committed code (configs changed only
  in comments). The pooled track's note was rerecorded on a clean commit and reproduced
  byte-for-byte.

## Submission packages (none uploaded)

Every track built a package and dry-ran the Publish workflow (`upload=false`). All passed.

| Track | `submit` | Dry run | Local package (git-ignored) |
|---|---|---|---|
| ARIMA | `current_best` | [42340777301](https://github.com/mauposad/proto-star-challenge/actions/runs/42340777301) | `.claude/worktrees/agent-ad55bad4db6e64709/submissions/20261106-235333_paper_p13_arima` |
| Pooled | `hybrid_ridge_all_cdd` | [42342975807](https://github.com/mauposad/proto-star-challenge/actions/runs/42342975807) | `.claude/worktrees/agent-aafcde0cb83170d0f/submissions/20261107-002824_paper_p09_p14_pooled` |
| Normals + GEV | `current_best` | [42340800942](https://github.com/mauposad/proto-star-challenge/actions/runs/42340800942) | `.claude/worktrees/agent-a99e445318cd43676/submissions/20261106-235521_paper_normals_gev` |
| Neural | `current_best` | [42344500112](https://github.com/mauposad/proto-star-challenge/actions/runs/42344500112) | `.claude/worktrees/agent-a485122745c1ab30e/submissions/20261107-004920_paper_neural` |

Each package can be rebuilt from its config with `uv run proto-star climate-package <config>`.
The pooled package is also kept as the `submission-package` artifact of its dry-run run.

## Open questions for the team

1. **Submit `hybrid_ridge_all_cdd`?** It is the only method that beats `current_best` at every
   origin in every window that counts. It changes only the CDD column. If adopted, write an ADR
   first; the publish workflow can then run on `configs/agent_paper_p09_p14_pooled.yaml`.
2. **Combine the CDD forecasts (replication step 11, P16/P17).** An equal-weight average of the
   pooled ridge, DeepAR, EWMA and ARIMA CDD forecasts, fixed in advance, would test whether
   the CDD gain survives without picking a single winner.
3. **More seeds for DeepAR** (5–10) before reading anything into its 2011 win.
4. **A neural package has never been rebuilt on the CI runner.** Cross-machine determinism is
   untested; check it before submitting a neural method.
