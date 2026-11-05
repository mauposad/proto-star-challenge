"""Generate and validate a leaderboard submission from a training run."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml

from proto_star.config import ExperimentConfig
from proto_star.data.features import build_features
from proto_star.data.load import load_test
from proto_star.data.validate import validate
from proto_star.paths import SUBMISSIONS_DIR
from proto_star.tracking import read_json
from proto_star.utils.logging import get_logger

log = get_logger(__name__)


class SubmissionError(ValueError):
    pass


def load_run(run_dir: Path) -> tuple[ExperimentConfig, object, list[str]]:
    with (run_dir / "config.yaml").open() as f:
        cfg = ExperimentConfig.model_validate(yaml.safe_load(f))
    model = joblib.load(run_dir / "model.joblib")
    features = read_json(run_dir / "meta.json")["feature_columns"]
    return cfg, model, features


def predict(run_dir: Path, out_dir: Path = SUBMISSIONS_DIR) -> Path:
    cfg, model, feature_columns = load_run(run_dir)
    test_df = load_test(cfg.data)
    validate(test_df, cfg.data, has_target=False)

    x = build_features(test_df, cfg.data)
    # Same columns, same order as training. Missing columns are a hard error.
    missing = set(feature_columns) - set(x.columns)
    if missing:
        raise SubmissionError(f"test data is missing training features: {sorted(missing)}")
    preds = model.predict(x[feature_columns])  # type: ignore[attr-defined]

    ids = test_df[cfg.data.id_column] if cfg.data.id_column else test_df.index
    sub = pd.DataFrame(
        {cfg.submission.id_column: np.asarray(ids), cfg.submission.prediction_column: preds}
    )
    validate_submission(sub, cfg, expected_rows=len(test_df))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{run_dir.name}.csv"
    sub.to_csv(out_path, index=False)
    log.info("wrote %d predictions to %s", len(sub), out_path)
    return out_path


def validate_submission(sub: pd.DataFrame, cfg: ExperimentConfig, expected_rows: int) -> None:
    """Catch format mistakes locally instead of burning a leaderboard submission."""
    s = cfg.submission
    if list(sub.columns) != [s.id_column, s.prediction_column]:
        raise SubmissionError(f"columns must be {[s.id_column, s.prediction_column]}")
    if len(sub) != expected_rows:
        raise SubmissionError(f"expected {expected_rows} rows, got {len(sub)}")
    if sub[s.id_column].duplicated().any():
        raise SubmissionError("duplicate ids in submission")
    if not np.isfinite(sub[s.prediction_column].to_numpy(dtype=float)).all():
        raise SubmissionError("predictions contain NaN or inf")
