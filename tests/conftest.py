from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> tuple[list, list, list]:
    base = FIXTURES / name
    issues = json.loads((base / "issues.json").read_text())
    phases = json.loads((base / "phases.json").read_text())
    repos = json.loads((base / "repos.json").read_text())
    return issues, phases, repos


@pytest.fixture()
def strong_plan():
    return _load_fixture("strong_plan")


@pytest.fixture()
def thin_plan():
    return _load_fixture("thin_plan")
