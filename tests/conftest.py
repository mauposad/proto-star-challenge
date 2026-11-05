from pathlib import Path

import pytest

from proto_star.config import ExperimentConfig
from proto_star.data.synthetic import make_train_test


@pytest.fixture
def data_files(tmp_path: Path) -> tuple[Path, Path]:
    train, test = make_train_test(n_days=400, n_stations=2)
    train_path, test_path = tmp_path / "train.parquet", tmp_path / "test.parquet"
    train.to_parquet(train_path, index=False)
    test.to_parquet(test_path, index=False)
    return train_path, test_path


@pytest.fixture
def cfg(data_files: tuple[Path, Path]) -> ExperimentConfig:
    train_path, test_path = data_files
    return ExperimentConfig.model_validate(
        {
            "name": "test",
            "data": {
                "train_path": str(train_path),
                "test_path": str(test_path),
                "target": "max_temp",
                "id_column": "id",
                "time_column": "date",
            },
            "model": {"name": "ridge"},
        }
    )
