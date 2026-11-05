"""Load tabular data from local files or the Hugging Face Hub."""

from collections.abc import Callable

import pandas as pd

from proto_star.config import DataConfig
from proto_star.paths import resolve

_READERS: dict[str, Callable[..., pd.DataFrame]] = {
    ".csv": pd.read_csv,
    ".parquet": pd.read_parquet,
    ".pq": pd.read_parquet,
    ".json": pd.read_json,
    ".jsonl": lambda p: pd.read_json(p, lines=True),
}


def read_table(path: str) -> pd.DataFrame:
    p = resolve(path)
    reader = _READERS.get(p.suffix.lower())
    if reader is None:
        raise ValueError(f"Unsupported file type {p.suffix!r}; expected one of {list(_READERS)}")
    if not p.exists():
        raise FileNotFoundError(f"{p} not found. See docs/data.md for how to obtain the data.")
    return reader(p)


def read_hf(repo_id: str, split: str) -> pd.DataFrame:
    from datasets import load_dataset  # imported lazily: slow import

    return load_dataset(repo_id, split=split).to_pandas()


def _load(cfg: DataConfig, location: str, hf_split: str) -> pd.DataFrame:
    df = read_hf(location, hf_split) if cfg.source == "hf" else read_table(location)
    if cfg.time_column and cfg.time_column in df.columns:
        df[cfg.time_column] = pd.to_datetime(df[cfg.time_column])
    return df


def load_train(cfg: DataConfig) -> pd.DataFrame:
    return _load(cfg, cfg.train_path, cfg.hf_train_split)


def load_test(cfg: DataConfig) -> pd.DataFrame:
    if cfg.source == "hf":
        return _load(cfg, cfg.test_path or cfg.train_path, cfg.hf_test_split)
    if cfg.test_path is None:
        raise ValueError("data.test_path must be set to generate a submission")
    return _load(cfg, cfg.test_path, cfg.hf_test_split)
