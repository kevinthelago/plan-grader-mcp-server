from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_plan(plan_dir: str) -> tuple[list[Any], list[Any], list[Any]]:
    """Load issues, phases, and repos from JSON files in plan_dir.

    Missing files default to []. Missing optional issue fields are tolerated.
    Returns (issues, phases, repos) ready for grade.grade_plan.
    """
    base = Path(plan_dir)

    def _load(filename: str) -> list[Any]:
        path = base / filename
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []

    return _load("issues.json"), _load("phases.json"), _load("repos.json")
