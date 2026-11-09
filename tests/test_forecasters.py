from pathlib import Path

import pandas as pd
import pytest
import yaml
from pydantic import Field

from proto_star.backtest import Forecaster, compare_forecasters, resolve_forecaster
from proto_star.climate import DEFAULT_CUTOFFS
from proto_star.data.synthetic import make_climate_master
from proto_star.forecasters import REGISTRY, ForecasterSpec, get_kind, load_all, register_kind
from proto_star.trend import PooledTrendSpec
from proto_star.trial import (
    build_forecasters,
    describe_forecaster,
    load_trial_config,
    run_trial,
)

TREND = {"level_years": [10, 15], "trend_window": 40, "cdd_sensitivity": True}


def _config(**extra: object) -> dict[str, object]:
    return {
        "name": "plugin_trial",
        "description": "Plug-in models next to the older blocks.",
        "forecasters": ["thirty_year_mean", "old_trend", "new_trend"],
        "pooled_trends": {"old_trend": TREND},
        "models": {"new_trend": {"kind": "pooled_trend", "params": TREND}},
        "reference": "thirty_year_mean",
        **extra,
    }


def _write(tmp_path: Path, cfg: dict[str, object]) -> Path:
    path = tmp_path / "trial.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


class _ShiftSpec(ForecasterSpec):
    shift: float = Field(ge=0)

    def describe(self) -> str:
        return f"Thirty-year mean plus {self.shift}"


def _build_shift(spec: _ShiftSpec) -> Forecaster:
    base = resolve_forecaster("thirty_year_mean")

    def forecast(train: pd.DataFrame, cutoff_year: int, forecast_years: list[int]) -> pd.DataFrame:
        out = base(train, cutoff_year, forecast_years)
        return out.assign(predicted_value=out["predicted_value"] + spec.shift)

    return forecast


@pytest.fixture
def shift_kind() -> object:
    kind = register_kind("unit_shift", _ShiftSpec, _build_shift)
    yield kind
    REGISTRY.pop("unit_shift")


def test_registry_discovers_the_pooled_trend_kind() -> None:
    assert "pooled_trend" in load_all()
    assert issubclass(get_kind("pooled_trend").spec, PooledTrendSpec)


def test_models_entry_matches_the_older_pooled_trends_block(tmp_path: Path) -> None:
    cfg = load_trial_config(_write(tmp_path, _config()))
    results = compare_forecasters(
        build_forecasters(cfg), make_climate_master(), cutoffs=DEFAULT_CUTOFFS
    )
    old = results.loc[results["method"] == "old_trend"].drop(columns="method")
    new = results.loc[results["method"] == "new_trend"].drop(columns="method")
    pd.testing.assert_frame_equal(old.reset_index(drop=True), new.reset_index(drop=True))
    assert describe_forecaster("new_trend", cfg) == describe_forecaster("old_trend", cfg)


def test_a_new_kind_runs_through_a_trial(tmp_path: Path, shift_kind: object) -> None:
    cfg = _config(
        forecasters=["thirty_year_mean", "shifted"],
        pooled_trends={},
        models={"shifted": {"kind": "unit_shift", "params": {"shift": 0.5}}},
    )
    run_dir = run_trial(
        _write(tmp_path, cfg),
        master=make_climate_master(),
        trials_dir=tmp_path / "runs",
        notes_dir=tmp_path / "notes",
        record=True,
    )
    note = (tmp_path / "notes" / "plugin_trial.md").read_text()
    assert "Thirty-year mean plus 0.5" in note
    assert (run_dir / "results.csv").exists()


def test_unknown_kind_is_rejected_at_load_time(tmp_path: Path) -> None:
    cfg = _config(models={"new_trend": {"kind": "magic", "params": {}}})
    with pytest.raises(ValueError, match="unknown model kind 'magic'"):
        load_trial_config(_write(tmp_path, cfg))


def test_bad_params_are_rejected_at_load_time(tmp_path: Path) -> None:
    bad = {**TREND, "trend_window": 3}
    cfg = _config(models={"new_trend": {"kind": "pooled_trend", "params": bad}})
    with pytest.raises(ValueError, match=r"model 'new_trend'.*rejected params"):
        load_trial_config(_write(tmp_path, cfg))
    extra = {**TREND, "magic": 1}
    cfg = _config(models={"new_trend": {"kind": "pooled_trend", "params": extra}})
    with pytest.raises(ValueError, match="rejected params"):
        load_trial_config(_write(tmp_path, cfg))


def test_model_names_cannot_clash_with_other_blocks(tmp_path: Path) -> None:
    cfg = _config(models={"old_trend": {"kind": "pooled_trend", "params": TREND}})
    with pytest.raises(ValueError, match="both `models` and `pooled_trends`"):
        load_trial_config(_write(tmp_path, cfg))
    cfg = _config(models={"ten_year_mean": {"kind": "pooled_trend", "params": TREND}})
    with pytest.raises(ValueError, match="shadow built-in"):
        load_trial_config(_write(tmp_path, cfg))


def test_kind_names_register_once(shift_kind: object) -> None:
    with pytest.raises(ValueError, match="already registered"):
        register_kind("unit_shift", _ShiftSpec, lambda spec: _build_shift(spec))


def test_spec_without_describe_says_so() -> None:
    class Bare(ForecasterSpec):
        pass

    with pytest.raises(NotImplementedError, match="must define describe"):
        Bare().describe()


def test_existing_configs_still_load() -> None:
    for path in sorted(Path("configs").glob("*.yaml")):
        raw = yaml.safe_load(path.read_text())
        if "forecasters" in raw:  # trial configs, not training configs
            assert load_trial_config(path).models == {}
