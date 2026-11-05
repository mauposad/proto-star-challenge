"""Guardrails on the repo itself, enforced in CI."""

import pytest

from proto_star.paths import PROJECT_ROOT

MAX_AGENT_DOC_LINES = 200  # longer instruction files get skimmed and rules get ignored


@pytest.mark.parametrize("name", ["AGENTS.md", "CLAUDE.md"])
def test_agent_instruction_files_stay_short(name):
    path = PROJECT_ROOT / name
    n_lines = len(path.read_text().splitlines())
    assert n_lines < MAX_AGENT_DOC_LINES, f"{name} has {n_lines} lines; keep it under 200"
