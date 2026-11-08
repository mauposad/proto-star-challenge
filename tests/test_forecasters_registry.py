from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
import yaml

from proto_star import submission_package
from proto_star.backtest import Forecaster, resolve_forecaster
from proto_star.climate import DEFAULT_CUTOFFS
from proto_star.data.master import MANIFEST_FILE, MASTER_FILE
from proto_star.data.synthetic import make_annual_master
from proto_star.forecasters import REGISTRY, load_all, register_forecaster
from proto_star.submission_package import build_package, verify_package
from proto_star.trial import describe_forecaster, load_trial_config, run_trial

TOY = "toy_offset_mean"


def _make_toy(*, window: int = 10, offset: float = 0.0) -> Forecaster:
    """Mean of the last ``window`` years plus ``offset``: easy to check by hand."""

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        from proto_star.climate import annual_to_long

        history = annual_to_long(train, cutoff_year=cutoff_year)
        recent = history.loc[history["year"] > cutoff_year - window]
        level = recent.groupby(["city_id", "metric"], as_index=False)["actual_value"].mean()
        rows = level.merge(pd.DataFrame({"year": forecast_years}), how="cross")
        rows["predicted_value"] = rows["actual_value"] + offset
        return rows[["city_id", "year", "metric", "predicted_value"]]

    return forecast


@pytest.fixture
def toy() -> Iterator[str]:
    register_forecaster(TOY, description="Toy mean plus offset", requires=("statsmodels",))(
        _make_toy
    )
    yield TOY
    REGISTRY.pop(TOY, None)


def _config(tmp_path: Path, **overrides: object) -> Path:
    config = {
        "name": "registry_trial",
        "description": "Registry test.",
        "forecasters": ["current_best", "ten_year_mean", "toy_plus_one", TOY],
        "variants": {"toy_plus_one": {"forecaster": TOY, "params": {"offset": 1.0}}},
        "reference": "current_best",
        "submit": "toy_plus_one",
        **overrides,
    }
    path = tmp_path / "trial.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


def test_registered_forecaster_resolves_with_defaults_and_variant_params(toy: str) -> None:
    master = make_annual_master()
    train = master.loc[master["Year"] <= 2000]
    plain = resolve_forecaster(toy)(train, 2000, [2001])
    shifted = resolve_forecaster(
        "shifted", variants={"shifted": {"forecaster": toy, "params": {"offset": 2.5}}}
    )(train, 2000, [2001])
    diff = shifted["predicted_value"].to_numpy() - plain["predicted_value"].to_numpy()
    assert diff == pytest.approx(2.5)


def test_variant_errors_name_the_problem(toy: str) -> None:
    with pytest.raises(ValueError, match="unregistered forecaster 'nope'"):
        resolve_forecaster("v", variants={"v": {"forecaster": "nope"}})
    with pytest.raises(ValueError, match="rejected params"):
        resolve_forecaster("v", variants={"v": {"forecaster": toy, "params": {"bogus": 1}}})
    with pytest.raises(ValueError, match="registered forecaster"):
        resolve_forecaster("magic")


def test_duplicate_registration_is_rejected(toy: str) -> None:
    with pytest.raises(ValueError, match="already registered"):
        register_forecaster(toy, description="other")(lambda: _make_toy())


def test_load_all_imports_without_side_effects_on_builtins() -> None:
    registry = load_all()
    assert "registry" not in registry
    assert all(entry.name == name for name, entry in registry.items())


def test_trial_config_rejects_unknown_variant_fields(tmp_path: Path, toy: str) -> None:
    path = _config(tmp_path, variants={"x": {"forecaster": toy, "parms": {}}})
    with pytest.raises(ValueError, match="parms"):
        load_trial_config(path)


def test_trial_runs_and_describes_variants(tmp_path: Path, toy: str) -> None:
    path = _config(tmp_path)
    cfg = load_trial_config(path)
    assert "offset=1.0" in describe_forecaster("toy_plus_one", cfg)
    assert "defaults" in describe_forecaster(toy, cfg)
    run_dir = run_trial(
        path, master=make_annual_master(), trials_dir=tmp_path / "runs", record=False
    )
    results = pd.read_csv(run_dir / "results.csv")
    assert set(results["method"]) == set(cfg.forecasters)
    assert set(results["cutoff_year"]) == set(DEFAULT_CUTOFFS)


def test_package_pins_the_submitted_forecasters_requirements(
    tmp_path: Path, toy: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(submission_package.EXTRA_INDEXES, "statsmodels", "https://example/whl")
    master = make_annual_master()
    master_dir, raw_dir = tmp_path / "processed", tmp_path / "raw"
    master_dir.mkdir()
    raw_dir.mkdir()
    master.to_parquet(master_dir / MASTER_FILE, index=False)
    (master_dir / MANIFEST_FILE).write_text('{"content_hash": "abc", "sources_sha256": {}}')
    for name in ("annual_indices.parquet", "city_info.parquet"):
        master.to_parquet(raw_dir / name, index=False)
    package = build_package(
        _config(tmp_path),
        master=master,
        master_dir=master_dir,
        raw_dir=raw_dir,
        out_root=tmp_path / "submissions",
    )
    lines = (package / "code" / "requirements.txt").read_text().splitlines()
    assert lines[0] == "--extra-index-url https://example/whl"
    assert any(line.startswith("statsmodels==") for line in lines)
    assert (package / "code/src/proto_star/forecasters/registry.py").exists()
    verify_package(package)
