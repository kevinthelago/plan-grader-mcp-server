from __future__ import annotations

from typing import Any

from plan_grader import grade as _grade
from plan_grader import loader as _loader
from plan_grader.server import mcp


@mcp.tool()
def grade_plan(
    plan_dir: str = ".",
    issues: list[dict[str, Any]] | None = None,
    phases: list[dict[str, Any]] | None = None,
    repos: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Grade a plan directory (or direct arrays) against the rubric.

    When issues/phases/repos are omitted the three JSON files are read from
    plan_dir.  Passing the arrays directly lets callers skip the filesystem.
    """
    if issues is None and phases is None and repos is None:
        issues, phases, repos = _loader.load_plan(plan_dir)
    else:
        issues = issues or []
        phases = phases or []
        repos = repos or []

    return _grade.grade_plan(issues, phases, repos)
