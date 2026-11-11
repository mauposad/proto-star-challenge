from pathlib import Path

from proto_star.paths import PROJECT_ROOT
from proto_star.submission_package import EVIDENCE_DOC, PLACEHOLDER, evidence_section


def test_evidence_section_is_empty_without_the_doc(tmp_path: Path) -> None:
    assert evidence_section(tmp_path) == ""


def test_evidence_section_wraps_the_doc_under_one_heading(tmp_path: Path) -> None:
    (tmp_path / EVIDENCE_DOC).write_text("# Evidence\n\nA claim and where to check it.\n")
    section = evidence_section(tmp_path)
    assert section.startswith("## Evidence for the judging criteria\n\n# Evidence")
    assert section.endswith("check it.\n\n")


def test_tracked_evidence_doc_has_no_placeholder_and_covers_both_criteria() -> None:
    text = (PROJECT_ROOT / "docs" / "submission" / EVIDENCE_DOC).read_text()
    assert PLACEHOLDER.findall(text) == []
    assert "## Scientific, research, or societal value" in text
    assert "## Technical creativity" in text
