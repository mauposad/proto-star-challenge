"""Typed experiment configuration loaded from YAML.

Every training run is fully described by one YAML file in `configs/`. Keeping
config out of code makes runs reproducible and easy to compare in review.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from proto_star.paths import resolve


class _Strict(BaseModel):
    # Typos in YAML keys should fail loudly, not be silently ignored.
    model_config = ConfigDict(extra="forbid")


class DataConfig(_Strict):
    source: Literal["file", "hf"] = "file"
    train_path: str = Field(description="CSV/Parquet path, or HF dataset repo id if source=hf")
    test_path: str | None = Field(
        default=None, description="Leaderboard test inputs (no target column)"
    )
    hf_train_split: str = "train"
    hf_test_split: str = "test"
    target: str
    id_column: str | None = None
    time_column: str | None = None
    features: list[str] | None = Field(
        default=None, description="Explicit feature list; None = all numeric non-target columns"
    )
    calendar_features: bool = Field(
        default=True, description="Add seasonal features derived from time_column"
    )


class SplitConfig(_Strict):
    strategy: Literal["time", "random"] = "time"
    valid_fraction: float = Field(default=0.2, gt=0, lt=1)


class ModelConfig(_Strict):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class SubmissionConfig(_Strict):
    id_column: str = "id"
    prediction_column: str = "prediction"


class ExperimentConfig(_Strict):
    name: str
    seed: int = 42
    data: DataConfig
    split: SplitConfig = Field(default_factory=SplitConfig)
    model: ModelConfig
    metrics: list[str] = Field(default_factory=lambda: ["mae", "rmse", "r2"])
    submission: SubmissionConfig = Field(default_factory=SubmissionConfig)

    @model_validator(mode="after")
    def _time_split_needs_time_column(self) -> "ExperimentConfig":
        if self.split.strategy == "time" and not self.data.time_column:
            raise ValueError("split.strategy='time' requires data.time_column")
        return self


def load_config(path: str | Path) -> ExperimentConfig:
    with resolve(path).open() as f:
        return ExperimentConfig.model_validate(yaml.safe_load(f))
