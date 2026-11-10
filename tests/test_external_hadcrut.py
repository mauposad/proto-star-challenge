from pathlib import Path

import pytest

from proto_star.climate import ClimateDataError
from proto_star.data.external.hadcrut import (
    HADCRUT_FILE,
    SOURCE_URL,
    cap_text,
    load_hadcrut4_annual,
    parse_annual,
)

ROW_TAIL = " ".join(["0.0"] * 10)


def _text(years: range) -> str:
    return "".join(f"{y} 0.{y % 10} {ROW_TAIL}\n" for y in years)


def test_source_is_the_2019_02_09_archive_of_version_4_6_0_0() -> None:
    assert "web.archive.org/web/20190209" in SOURCE_URL
    assert "HadCRUT.4.6.0.0.annual_ns_avg.txt" in SOURCE_URL


def test_cap_text_drops_every_row_after_2018() -> None:
    capped = parse_annual(cap_text(_text(range(2010, 2024))))
    assert capped["year"].max() == 2018
    assert len(capped) == 9
    with pytest.raises(ClimateDataError, match="leading year"):
        cap_text("header line\n" + _text(range(2010, 2012)))


def test_loader_rejects_a_file_with_2019(tmp_path: Path) -> None:
    path = tmp_path / "leaky.txt"
    path.write_text(_text(range(2000, 2020)))
    with pytest.raises(ClimateDataError, match="2019"):
        load_hadcrut4_annual(path=path)


def test_loader_applies_the_fold_cutoff(tmp_path: Path) -> None:
    path = tmp_path / "ok.txt"
    path.write_text(_text(range(1950, 2019)))
    table = load_hadcrut4_annual(1995, path)
    assert table["year"].max() == 1995
    assert list(table.columns) == ["year", "gmst"]
    with pytest.raises(FileNotFoundError, match="download_hadcrut"):
        load_hadcrut4_annual(path=tmp_path / "missing.txt")


@pytest.mark.skipif(not HADCRUT_FILE.exists(), reason="HadCRUT4 file not downloaded")
def test_saved_file_holds_nothing_after_2018() -> None:
    table = parse_annual(HADCRUT_FILE.read_text())
    assert int(table["year"].max()) <= 2018
    assert int(table["year"].min()) == 1850
