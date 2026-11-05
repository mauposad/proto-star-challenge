"""Training entry point: config in, run directory out."""

from datetime import datetime
from pathlib import Path

import joblib

from proto_star.config import ExperimentConfig
from proto_star.data.features import build_features
from proto_star.data.load import load_train
from proto_star.data.split import split
from proto_star.data.validate import validate
from proto_star.evaluate import compute_metrics
from proto_star.models import build_model
from proto_star.paths import RUNS_DIR
from proto_star.tracking import create_run_dir, git_info, write_json
from proto_star.utils.logging import get_logger
from proto_star.utils.seed import set_seed

log = get_logger(__name__)


def train(cfg: ExperimentConfig, runs_dir: Path = RUNS_DIR) -> Path:
    set_seed(cfg.seed)

    df = load_train(cfg.data)
    validate(df, cfg.data)
    df = df.dropna(subset=[cfg.data.target])
    log.info("loaded %d rows", len(df))

    train_df, valid_df = split(df, cfg.split, time_column=cfg.data.time_column, seed=cfg.seed)
    x_train, y_train = build_features(train_df, cfg.data), train_df[cfg.data.target]
    x_valid, y_valid = build_features(valid_df, cfg.data), valid_df[cfg.data.target]
    log.info("train=%d valid=%d features=%d", len(x_train), len(x_valid), x_train.shape[1])

    model = build_model(cfg.model.name, cfg.seed, cfg.model.params)
    model.fit(x_train, y_train)
    metrics = compute_metrics(y_valid.to_numpy(), model.predict(x_valid), cfg.metrics)
    log.info("validation %s", "  ".join(f"{k}={v:.4f}" for k, v in metrics.items()))

    run_dir = create_run_dir(cfg, runs_dir)
    joblib.dump(model, run_dir / "model.joblib")
    write_json(run_dir / "metrics.json", metrics)
    write_json(
        run_dir / "meta.json",
        {
            "created": datetime.now().isoformat(timespec="seconds"),
            "git": git_info(),
            "n_train": len(x_train),
            "n_valid": len(x_valid),
            "feature_columns": list(x_train.columns),
        },
    )
    log.info("saved run to %s", run_dir)
    return run_dir
