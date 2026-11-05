import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from proto_star.config import ExperimentConfig, load_config
from proto_star.evaluate import compute_metrics
from proto_star.models import available_models, build_model
from proto_star.predict import SubmissionError, predict, validate_submission
from proto_star.tracking import read_json
from proto_star.train import train


def test_baseline_configs_parse():
    for name in ("baseline", "hist_gbm"):
        load_config(f"configs/{name}.yaml")


def test_config_rejects_unknown_keys(cfg):
    raw = cfg.model_dump()
    raw["modle"] = {}
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(raw)


@pytest.mark.parametrize("name", available_models())
def test_every_registered_model_builds(name):
    model = build_model(name, seed=0)
    assert hasattr(model, "fit") and hasattr(model, "predict")


def test_metrics():
    m = compute_metrics(np.array([1.0, 2.0]), np.array([1.0, 4.0]), ["mae", "rmse"])
    assert m == pytest.approx({"mae": 1.0, "rmse": np.sqrt(2)})


def test_train_then_predict_end_to_end(cfg, tmp_path):
    run_dir = train(cfg, runs_dir=tmp_path / "runs")
    for f in ("config.yaml", "meta.json", "metrics.json", "model.joblib"):
        assert (run_dir / f).exists()
    assert read_json(run_dir / "metrics.json")["r2"] > 0.5  # ridge should learn seasonality

    sub_path = predict(run_dir, out_dir=tmp_path / "subs")
    sub = pd.read_csv(sub_path)
    assert list(sub.columns) == ["id", "prediction"]
    assert sub["prediction"].notna().all()


def test_submission_validator_rejects_nan(cfg):
    sub = pd.DataFrame({"id": [0, 1], "prediction": [1.0, np.nan]})
    with pytest.raises(SubmissionError, match="NaN"):
        validate_submission(sub, cfg, expected_rows=2)
