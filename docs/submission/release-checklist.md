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
- [ ] Run the trial (`uv run proto-star climate-trial configs/<trial>.yaml --record`) and
  confirm the `submit` forecaster in the config is the one the validation results support.
- [ ] Build the folder with `uv run proto-star climate-package configs/<trial>.yaml`. It
  checks that `code/` and `data/` rebuild `submission.csv`, and lists what is left to fill in.
- [ ] Run the official `code/check_submission.py` from the copied submission template on
  the generated `submission.csv` (5,880 rows).
- [ ] Confirm forecasting code reads no weather-responsive values after
  2018-12-31 and every external source is listed in the dataset card.

## Hugging Face dataset

- [ ] Copy the official submission template into the team's public dataset.
- [ ] Upload the contents of the generated `submissions/<stamp>_<trial>/` folder
  (`submission.csv`, `README.md`, `code/`, `data/`) after filling in every
  `TODO before upload` line that `climate-package` printed.
- [ ] Confirm the repo is public and not gated, and that the dataset page shows the
  `default` config with a `test` split (the README front-matter `configs:` block
  points at `submission.csv`).
- [ ] Run the `Publish submission` workflow as a dry run first (`upload` unticked); it
  rebuilds the package in a clean environment and checks the layout. Uploading removes
  stale files under `code/` and `data/` on the Hub.
- [ ] Include the method, policy, ecosystem feedback, limitations, AI-tool
  disclosure, source licenses, cutoff, and checksums.
- [ ] Commit/push the public dataset, record the commit hash, then paste its
  link in the challenge Space's Submission tab.
- [ ] Re-submit after any intended change: the latest recorded dataset commit
  is the version judges score.
