"""MCP tool: lint_plan — report structural gaps in a plan document."""

from __future__ import annotations

import json
from typing import Any

from plan_grader.lint import LintIssue, lint_plan as _lint_plan


def _issue_to_dict(issue: LintIssue) -> dict[str, str]:
    return {
        "severity": issue.severity.value,
        "field": issue.field,
        "message": issue.message,
    }


def lint_plan(plan: str) -> str:
    """Check a plan document for structural gaps.

    Args:
        plan: JSON-encoded plan document.  Expected top-level keys include
            ``goal``, ``approach``, ``risks``, ``testing``, ``phases``, and
            ``acceptance_criteria``.

    Returns:
        JSON-encoded list of objects, each with ``severity`` ("error" or
        "warning"), ``field``, and ``message`` keys.  An empty list means
        no gaps were detected.

    Raises:
        ValueError: If *plan* is not valid JSON or is not a JSON object.
    """
    try:
        parsed: Any = json.loads(plan)
    except json.JSONDecodeError as exc:
        raise ValueError(f"plan must be valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("plan must be a JSON object, not a primitive or array")

    issues = _lint_plan(parsed)
    return json.dumps([_issue_to_dict(i) for i in issues])
