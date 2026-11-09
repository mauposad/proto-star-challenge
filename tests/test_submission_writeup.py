"""The submission README carries the write-up, evidence and template fields judges look for."""

import math
from pathlib import Path

import pandas as pd
import pytest
import yaml

from proto_star.data.master import MANIFEST_FILE, MASTER_FILE
from proto_star.paths import PROJECT_ROOT
from proto_star.submission_package import build_package, verify_package

WRITEUP = "docs/submission/method_hybrid.md"
EVIDENCE = "docs/trials/pooled_trend.md"
CONFIG = {
    "name": "writeup_trial",
    "description": "Tiny trial for the write-up tests.",
    "forecasters": ["thirty_year_mean", "current_best"],
    "reference": "thirty_year_mean",
    "submit": "current_best",
    "writeup": WRITEUP,
    "evidence": [EVIDENCE],
}


def _master() -> pd.DataFrame:
    rows = []
    for offset, city in enumerate(["A", "B"]):
        for year in range(1960, 2019):
            wiggle = math.sin(year * 1.7 + offset)
            rows.append(
                {
                    "ID": city,
                    "Year": year,
                    "Avg Temp": 50.0 + 10 * offset + 0.05 * (year - 1960) + wiggle,
                    "ToT Prcp": 30.0 + 3 * wiggle,
                    "Max Tmax": 95.0 + 2 * wiggle,
                    "cdd": 800.0 + 300 * offset + 50 * wiggle,
                    "Miss Tmax": 0,
                    "Miss Tmin": 0,
                    "Miss Prcp": 0,
                }
            )
    return pd.DataFrame(rows)


def _package(tmp_path: Path, config: dict[str, object]) -> Path:
    path = tmp_path / "trial.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    master_dir, raw_dir = tmp_path / "processed", tmp_path / "raw"
    master_dir.mkdir()
    raw_dir.mkdir()
    master = _master()
    master.to_parquet(master_dir / MASTER_FILE, index=False)
    (master_dir / MANIFEST_FILE).write_text('{"content_hash": "abc", "sources_sha256": {}}')
    for name in ("annual_indices.parquet", "city_info.parquet"):
        master.to_parquet(raw_dir / name, index=False)
    return build_package(
        path, master=master, master_dir=master_dir, raw_dir=raw_dir, out_root=tmp_path / "out"
    )


@pytest.fixture
def package(tmp_path: Path) -> Path:
    return _package(tmp_path, CONFIG)


def test_readme_has_the_template_fields(package: Path) -> None:
    readme = (package / "README.md").read_text(encoding="utf-8")
    for expected in (
        "**Negative result:** no",
        "## Data",
        "10.1184/R1/7890488.v6",
        "10.1175/JCLI-D-18-0630.1",
        "## Policy idea",
        "## Feedback to the ecosystem",
    ):
        assert expected in readme, expected


def test_writeup_goes_into_the_method_section(package: Path) -> None:
    readme = (package / "README.md").read_text(encoding="utf-8")
    method = readme.split("## Method", 1)[1].split("## AI tools", 1)[0]
    first_line = (PROJECT_ROOT / WRITEUP).read_text(encoding="utf-8").strip().splitlines()[0]
    assert first_line in method


def test_negative_result_flag_reaches_the_readme(tmp_path: Path) -> None:
    package = _package(tmp_path, {**CONFIG, "negative_result": True})
    assert "**Negative result:** yes" in (package / "README.md").read_text(encoding="utf-8")


def test_evidence_and_backtest_script_are_shipped(package: Path) -> None:
    assert (package / "code" / "evidence" / Path(EVIDENCE).name).exists()
    assert (package / "code" / "backtest.py").exists()
    assert "backtest.py" in (package / "code" / "README.md").read_text(encoding="utf-8")


def test_generated_text_is_utf8(package: Path) -> None:
    for relative in ("README.md", "data/README.md", "code/README.md"):
        (package / relative).read_bytes().decode("utf-8")
    assert "°F" in (package / "data" / "README.md").read_text(encoding="utf-8")


def test_package_with_writeup_still_reproduces(package: Path) -> None:
    verify_package(package)
