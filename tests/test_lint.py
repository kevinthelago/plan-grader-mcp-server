"""Tests for plan linting (structural gap detection)."""

from __future__ import annotations

import json

import pytest

from plan_grader.lint import LintIssue, Severity, lint_plan
from plan_grader.tools.lint_plan import lint_plan as lint_plan_tool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_valid_plan() -> dict:
    return {
        "goal": "Deliver a fast, reliable search feature for the product catalogue.",
        "approach": "Implement an Elasticsearch-backed service with REST API and caching.",
        "risks": ["Elasticsearch cluster may be unavailable during peak load"],
        "testing": "Unit tests for indexing logic; integration tests against a local ES container.",
        "phases": ["Discovery & spike", "Implementation", "QA & hardening"],
        "acceptance_criteria": ["Search returns results in < 200 ms at p99"],
    }


def _errors(issues: list[LintIssue]) -> list[LintIssue]:
    return [i for i in issues if i.severity == Severity.ERROR]


def _warnings(issues: list[LintIssue]) -> list[LintIssue]:
    return [i for i in issues if i.severity == Severity.WARNING]


# ---------------------------------------------------------------------------
# lint_plan (core logic)
# ---------------------------------------------------------------------------

class TestLintPlanNoIssues:
    def test_valid_plan_returns_empty(self):
        issues = lint_plan(_minimal_valid_plan())
        assert issues == []


class TestRequiredFields:
    def test_missing_goal_is_error(self):
        plan = _minimal_valid_plan()
        del plan["goal"]
        issues = _errors(lint_plan(plan))
        assert any(i.field == "goal" for i in issues)

    def test_missing_approach_is_error(self):
        plan = _minimal_valid_plan()
        del plan["approach"]
        issues = _errors(lint_plan(plan))
        assert any(i.field == "approach" for i in issues)

    def test_empty_string_goal_is_error(self):
        plan = _minimal_valid_plan()
        plan["goal"] = ""
        issues = _errors(lint_plan(plan))
        assert any(i.field == "goal" for i in issues)

    def test_whitespace_only_goal_is_error(self):
        plan = _minimal_valid_plan()
        plan["goal"] = "   "
        issues = _errors(lint_plan(plan))
        assert any(i.field == "goal" for i in issues)

    def test_none_approach_is_error(self):
        plan = _minimal_valid_plan()
        plan["approach"] = None
        issues = _errors(lint_plan(plan))
        assert any(i.field == "approach" for i in issues)

    def test_short_goal_is_warning_not_error(self):
        plan = _minimal_valid_plan()
        plan["goal"] = "Fix bug"  # < 20 chars
        issues = lint_plan(plan)
        error_fields = {i.field for i in _errors(issues)}
        warning_fields = {i.field for i in _warnings(issues)}
        assert "goal" not in error_fields
        assert "goal" in warning_fields


class TestRecommendedFields:
    @pytest.mark.parametrize("field", ["risks", "testing", "phases", "acceptance_criteria"])
    def test_missing_recommended_field_is_warning(self, field):
        plan = _minimal_valid_plan()
        del plan[field]
        issues = _warnings(lint_plan(plan))
        assert any(i.field == field for i in issues)

    @pytest.mark.parametrize("field", ["risks", "testing", "phases", "acceptance_criteria"])
    def test_empty_recommended_field_is_warning(self, field):
        plan = _minimal_valid_plan()
        plan[field] = [] if isinstance(plan[field], list) else ""
        issues = _warnings(lint_plan(plan))
        assert any(i.field == field for i in issues)

    @pytest.mark.parametrize("field", ["risks", "testing", "phases", "acceptance_criteria"])
    def test_missing_recommended_field_not_an_error(self, field):
        plan = _minimal_valid_plan()
        del plan[field]
        assert not _errors(lint_plan(plan))


class TestIssueOrdering:
    def test_errors_before_warnings(self):
        plan = _minimal_valid_plan()
        del plan["goal"]  # error
        del plan["risks"]  # warning
        issues = lint_plan(plan)
        severities = [i.severity for i in issues]
        error_idx = severities.index(Severity.ERROR)
        warning_idx = severities.index(Severity.WARNING)
        assert error_idx < warning_idx


class TestExtraFieldsIgnored:
    def test_unknown_fields_produce_no_issues(self):
        plan = _minimal_valid_plan()
        plan["custom_section"] = "some content"
        plan["metadata"] = {"author": "Alice"}
        assert lint_plan(plan) == []


# ---------------------------------------------------------------------------
# lint_plan_tool (MCP wrapper)
# ---------------------------------------------------------------------------

class TestLintPlanTool:
    def test_valid_plan_json_returns_empty_list(self):
        result = lint_plan_tool(json.dumps(_minimal_valid_plan()))
        parsed = json.loads(result)
        assert parsed == []

    def test_returns_json_string(self):
        result = lint_plan_tool(json.dumps(_minimal_valid_plan()))
        assert isinstance(result, str)
        json.loads(result)  # must parse without error

    def test_missing_required_field_appears_in_output(self):
        plan = _minimal_valid_plan()
        del plan["goal"]
        result = json.loads(lint_plan_tool(json.dumps(plan)))
        assert any(i["field"] == "goal" and i["severity"] == "error" for i in result)

    def test_issue_has_required_keys(self):
        plan = _minimal_valid_plan()
        del plan["goal"]
        result = json.loads(lint_plan_tool(json.dumps(plan)))
        assert len(result) > 0
        issue = result[0]
        assert "severity" in issue
        assert "field" in issue
        assert "message" in issue

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="valid JSON"):
            lint_plan_tool("not json")

    def test_json_array_raises_value_error(self):
        with pytest.raises(ValueError, match="JSON object"):
            lint_plan_tool(json.dumps(["a", "b"]))

    def test_json_string_raises_value_error(self):
        with pytest.raises(ValueError, match="JSON object"):
            lint_plan_tool(json.dumps("just a string"))
