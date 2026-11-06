# Submission release checklist

## Team and eligibility

- [ ] Register every member in one Hugging Face team before the deadline.
- [ ] Confirm that more than half of members are current CMU students using
  `@andrew.cmu.edu` addresses if pursuing the $2,500 CMU prize.
- [ ] Replace every `<...>` placeholder in the dataset card, including human
  review and team information.

## Reproducibility and compliance

- [ ] Run `uv sync`, `pytest -q`, and the project quality checks from a clean
  environment.
- [ ] Run `scripts/evaluate_metric_ensemble.py`; confirm the selected mapping
  remains temperature/CDD = ten-year mean and precipitation/hottest-day =
  thirty-year climatology unless a documented later experiment beats it.
- [ ] Generate `submissions/protostar_metric_ensemble.csv` and confirm 5,880
  rows with the official checker in the copied submission template.
- [ ] Confirm forecasting code reads no weather-responsive values after
  2018-12-31 and every external source is listed in the dataset card.

## Hugging Face dataset

- [ ] Copy the official submission template into the team's public dataset.
- [ ] Add `submission.csv`, `README.md`, `code/`, and a `data/README.md`
  copied from `docs/submission/data-card-template.md`.
- [ ] Include the method, policy, ecosystem feedback, limitations, AI-tool
  disclosure, source licenses, cutoff, and checksums.
- [ ] Commit/push the public dataset, record the commit hash, then paste its
  link in the challenge Space's Submission tab.
- [ ] Re-submit after any intended change: the latest recorded dataset commit
  is the version judges score.
