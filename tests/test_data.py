import pandas as pd
import pytest

from proto_star.config import SplitConfig
from proto_star.data.features import build_features
from proto_star.data.load import load_test, load_train
from proto_star.data.split import split
from proto_star.data.validate import DataValidationError, validate


def test_time_split_has_no_leakage(cfg):
    df = load_train(cfg.data)
    train, valid = split(df, SplitConfig(strategy="time"), time_column="date", seed=0)
    assert train["date"].max() < valid["date"].min()
    assert len(train) + len(valid) == len(df)


def test_random_split_is_reproducible(cfg):
    df = load_train(cfg.data)
    a = split(df, SplitConfig(strategy="random"), time_column=None, seed=1)[1]
    b = split(df, SplitConfig(strategy="random"), time_column=None, seed=1)[1]
    pd.testing.assert_frame_equal(a, b)


def test_validate_passes_on_good_data(cfg):
    validate(load_train(cfg.data), cfg.data)
    validate(load_test(cfg.data), cfg.data, has_target=False)


def test_validate_reports_missing_target_and_duplicate_ids(cfg):
    df = load_train(cfg.data).drop(columns="max_temp")
    df.loc[1, "id"] = df.loc[0, "id"]
    with pytest.raises(DataValidationError, match="missing columns") as exc:
        validate(df, cfg.data)
    assert "duplicate" in str(exc.value)


def test_features_exclude_target_id_and_time(cfg):
    x = build_features(load_train(cfg.data), cfg.data)
    assert not {"max_temp", "id", "date"} & set(x.columns)
    assert {"doy_sin", "doy_cos"} <= set(x.columns)


def test_features_match_between_train_and_test(cfg):
    train_cols = build_features(load_train(cfg.data), cfg.data).columns
    test_cols = build_features(load_test(cfg.data), cfg.data).columns
    assert list(train_cols) == list(test_cols)
