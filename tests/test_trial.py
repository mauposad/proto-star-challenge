import hashlib
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

from proto_star.climate import DEFAULT_CUTOFFS, ClimateSubmissionError
from proto_star.data.master import MANIFEST_FILE, MASTER_FILE
from proto_star.forecasters import _crm_urban
from proto_star.submission_package import build_package, open_placeholders, verify_package
from proto_star.trial import load_trial_config, run_trial

CONFIG = {
    "name": "unit_trial",
    "description": "Tiny trial for tests.",
    "forecasters": ["current_best", "ten_year_mean", "hinge_fit", "mixed"],
    "ensembles": {
        "mixed": {
            "annual_avg_temp": "fifteen_year_mean",
            "total_precip_in": "thirty_year_median",
            "hottest_day_temp": "thirty_year_mean",
            "cdd": "hinge_fit",
        }
    },
    "reference": "current_best",
    "submit": "mixed",
}


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path = tmp_path / "trial.yaml"
    path.write_text(yaml.safe_dump(CONFIG))
    return path


def _city_master() -> pd.DataFrame:
    """Two cities, 1960-2018, with a trend and deterministic noise."""
    rows = []
    for offset, city in enumerate(["A", "B"]):
        for year in range(1960, 2019):
            wiggle = math.sin(year * 1.7 + offset)
            trend = (year - 1960) * 0.05
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Lat": 40.0 - 10 * offset,
                    "Lon": -80.0 - 20 * offset,
                    "Avg Temp": 50.0 + 10 * offset + trend + wiggle,
                    "ToT Prcp": 30.0 + 5 * offset + 3 * wiggle,
                    "Max Tmax": 95.0 + 2 * wiggle,
                    "cdd": 800.0 + 300 * offset + 10 * trend + 50 * wiggle,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def test_trial_config_rejects_cutoffs_and_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump({**CONFIG, "cutoffs": [2000]}))
    with pytest.raises(ValueError, match="cutoffs"):
        load_trial_config(path)


def test_trial_config_requires_reference_and_submit_to_be_listed(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump({**CONFIG, "submit": "linear_trend"}))
    with pytest.raises(ValueError, match="submit"):
        load_trial_config(path)


def test_run_trial_records_what_was_used(config_path: Path, tmp_path: Path) -> None:
    run_dir = run_trial(
        config_path,
        master=_city_master(),
        trials_dir=tmp_path / "runs",
        notes_dir=tmp_path / "notes",
        record=True,
    )
    assert {p.name for p in run_dir.iterdir()} == {
        "config.yaml",
        "results.csv",
        "summary.md",
        "meta.json",
    }
    results = pd.read_csv(run_dir / "results.csv")
    assert set(results["cutoff_year"]) == set(DEFAULT_CUTOFFS)
    assert set(results["method"]) == set(CONFIG["forecasters"])
    note = (tmp_path / "notes" / "unit_trial.md").read_text()
    assert note == (run_dir / "summary.md").read_text()
    for expected in ("content hash", "hinge_fit", "Per metric:", "climate-trial"):
        assert expected in note


def _package(
    config_path: Path,
    tmp_path: Path,
    team_path: Path | None = None,
    forecaster: str | None = None,
) -> Path:
    master_dir, raw_dir = tmp_path / "processed", tmp_path / "raw"
    master_dir.mkdir()
    raw_dir.mkdir()
    master = _city_master()
    master.to_parquet(master_dir / MASTER_FILE, index=False)
    (master_dir / MANIFEST_FILE).write_text('{"content_hash": "abc", "sources_sha256": {}}')
    for name in ("annual_indices.parquet", "city_info.parquet"):
        master.to_parquet(raw_dir / name, index=False)
    return build_package(
        config_path,
        master=master,
        master_dir=master_dir,
        raw_dir=raw_dir,
        out_root=tmp_path / "submissions",
        forecaster=forecaster,
        **({"team_path": team_path} if team_path else {}),
    )


def test_package_has_the_layout_the_challenge_asks_for(config_path: Path, tmp_path: Path) -> None:
    package = _package(config_path, tmp_path)
    for relative in (
        "submission.csv",
        "README.md",
        "code/reproduce.py",
        "code/check_submission.py",
        "code/requirements.txt",
        "code/trial.yaml",
        "code/src/proto_star/backtest.py",
        "code/README.md",
        "code/scripts/download_protostar_data.py",
        "code/scripts/build_master_dataset.py",
        "code/scripts/compare_baselines.py",
        "code/scripts/evaluate_metric_ensemble.py",
        "data/README.md",
        f"data/{MASTER_FILE}",
    ):
        assert (package / relative).exists(), relative
    submission = pd.read_csv(package / "submission.csv")
    assert list(submission.columns) == ["city_id", "year", "metric", "predicted_value"]
    assert len(submission) == 2 * 7 * 4  # two test cities
    assert "Policy idea" in (package / "README.md").read_text()


def test_package_readme_declares_the_viewer_config(config_path: Path, tmp_path: Path) -> None:
    package = _package(config_path, tmp_path)
    front = (package / "README.md").read_text().split("---")[1]
    config = yaml.safe_load(front)["configs"][0]
    assert config["config_name"] == "default"
    assert config["data_files"] == [{"split": "test", "path": "submission.csv"}]
    assert (package / "submission.csv").exists()


def test_package_code_readme_is_not_the_template_and_pins_all_runtime_deps(
    config_path: Path, tmp_path: Path
) -> None:
    code = _package(config_path, tmp_path) / "code"
    assert "Put the notebooks or scripts" not in (code / "README.md").read_text()
    pinned = {line.split("==")[0] for line in (code / "requirements.txt").read_text().split()}
    assert {"scikit-learn", "joblib", "typer", "pandas", "huggingface-hub"} <= pinned


def test_package_reproduces_and_detects_tampering(config_path: Path, tmp_path: Path) -> None:
    package = _package(config_path, tmp_path)
    verify_package(package)

    submission = pd.read_csv(package / "submission.csv")
    submission.loc[0, "predicted_value"] += 1.0
    submission.to_csv(package / "submission.csv", index=False)
    with pytest.raises(ClimateSubmissionError, match="differs"):
        verify_package(package)


@pytest.mark.parametrize("submit", ["mixed", None])
def test_forecaster_override_is_the_one_reproduced(submit: str | None, tmp_path: Path) -> None:
    config_path = tmp_path / "override.yaml"
    config = {k: v for k, v in CONFIG.items() if k != "submit"}
    config_path.write_text(yaml.safe_dump({**config, **({"submit": submit} if submit else {})}))
    package = _package(config_path, tmp_path, forecaster="ten_year_mean")
    assert load_trial_config(package / "code" / "trial.yaml").submit == "ten_year_mean"
    verify_package(package)  # rebuilds ten_year_mean and matches submission.csv


def test_urban_crm_package_carries_only_population_and_reproduces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {
        "name": "urban_crm_package",
        "description": "Tiny urban CRM packaging test.",
        "forecasters": ["thirty_year_mean", "urban_crm"],
        "models": {
            "urban_crm": {
                "kind": "crm",
                "params": {"regions": "fixed", "k_scale": 0.0, "urban": True},
            }
        },
        "reference": "thirty_year_mean",
        "submit": "urban_crm",
    }
    config_path = tmp_path / "urban.yaml"
    config_path.write_text(yaml.safe_dump(config))
    city_static = pd.DataFrame({"ID": ["A", "B"], "unused_nlcd": [5.0, 10.0]})
    for year, scale in zip((1970, 1980, 1990, 2000, 2010, 2020), range(1, 7), strict=True):
        city_static[f"pop_{year}"] = [100_000 * scale, 200_000 * (scale + 1)]
    source = tmp_path / "source_city_static.parquet"
    city_static.to_parquet(source, index=False)
    monkeypatch.setattr(_crm_urban, "CITY_STATIC_PATH", source)

    package = _package(config_path, tmp_path)
    packaged = package / "data" / "city_static.parquet"
    expected_columns = ["ID", *[f"pop_{year}" for year in _crm_urban.CENSUS_YEARS]]
    assert pd.read_parquet(packaged).columns.tolist() == expected_columns
    data_card = (package / "data" / "README.md").read_text()
    assert "U.S. Census Bureau Population Estimates Program" in data_card
    assert "2018 forecast uses 2000-2010" in data_card
    assert hashlib.sha256(packaged.read_bytes()).hexdigest()[:16] in data_card

    reproduced = subprocess.run(
        [sys.executable, package / "code" / "reproduce.py"],
        cwd=package,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "OK:" in reproduced.stdout


def test_package_fills_in_team_details_from_team_file(config_path: Path, tmp_path: Path) -> None:
    readme = (_package(config_path, tmp_path) / "README.md").read_text()
    for expected in ("MKDir", "@MekkoMau", "@DeenOjo", "@corbe19", "Claude Code", "Warp"):
        assert expected in readme
    assert "<Team Name>" not in readme


def test_package_lists_any_placeholder_left_in_the_team_file(
    config_path: Path, tmp_path: Path
) -> None:
    team = tmp_path / "team.yaml"
    team.write_text(
        yaml.safe_dump(
            {
                "team_name": "<Team Name>",
                "members": [{"name": "A", "hf_username": "@a", "affiliation": "TBD"}],
                "ai_tools": "x",
                "ai_work": "y",
                "human_review": "z",
            }
        )
    )
    package = _package(config_path, tmp_path, team_path=team)
    assert any("Team Name" in item for item in open_placeholders(package))
