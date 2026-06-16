"""Structural gap detection for plan documents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class LintIssue:
    severity: Severity
    field: str
    message: str


# Fields that must be present and non-empty for the plan to be valid.
_REQUIRED_FIELDS: tuple[str, ...] = ("goal", "approach")

# Fields that should be present; absence is a warning, not an error.
_RECOMMENDED_FIELDS: tuple[str, ...] = (
    "risks",
    "testing",
    "phases",
    "acceptance_criteria",
)

# Minimum character count for a string field to be considered substantive.
_MIN_CHARS = 20

# Minimum item count for a list field to be considered substantive.
_MIN_LIST_ITEMS = 1


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _is_thin(value: Any) -> bool:
    """Return True when a value is present but lacks substance."""
    if isinstance(value, str):
        return len(value.strip()) < _MIN_CHARS
    if isinstance(value, list):
        return len(value) < _MIN_LIST_ITEMS
    return False


def lint_plan(plan: dict[str, Any]) -> list[LintIssue]:
    """Check *plan* for structural gaps.

    Args:
        plan: Parsed plan document (already deserialized from JSON).

    Returns:
        Ordered list of :class:`LintIssue` objects, errors before warnings.
    """
    issues: list[LintIssue] = []

    for field in _REQUIRED_FIELDS:
        value = plan.get(field)
        if _is_empty(value):
            issues.append(
                LintIssue(
                    severity=Severity.ERROR,
                    field=field,
                    message=f"Required field '{field}' is missing or empty.",
                )
            )
        elif _is_thin(value):
            issues.append(
                LintIssue(
                    severity=Severity.WARNING,
                    field=field,
                    message=(
                        f"Field '{field}' is too short to be meaningful "
                        f"(minimum {_MIN_CHARS} characters for strings, "
                        f"{_MIN_LIST_ITEMS} item(s) for lists)."
                    ),
                )
            )

    for field in _RECOMMENDED_FIELDS:
        value = plan.get(field)
        if _is_empty(value):
            issues.append(
                LintIssue(
                    severity=Severity.WARNING,
                    field=field,
                    message=f"Recommended field '{field}' is missing or empty.",
                )
            )
        elif _is_thin(value):
            issues.append(
                LintIssue(
                    severity=Severity.WARNING,
                    field=field,
                    message=(
                        f"Field '{field}' is too short to be meaningful "
                        f"(minimum {_MIN_CHARS} characters for strings, "
                        f"{_MIN_LIST_ITEMS} item(s) for lists)."
                    ),
                )
            )

    return issues
