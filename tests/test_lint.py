"""Parity tests for find_plan_gaps and the lint_plan / lint_stage MCP tools."""

from __future__ import annotations

import os

import pytest

from plan_grader.lint import find_plan_gaps
from plan_grader.tools.lint_plan import lint_plan, lint_stage


# ---------------------------------------------------------------------------
# find_plan_gaps — pure logic
# ---------------------------------------------------------------------------

class TestEmptyFileMap:
    def test_empty_map_returns_no_gaps(self):
        result = find_plan_gaps({})
        assert result == {"gaps": [], "blocked": False}


class TestEmptyContent:
    def test_empty_string_is_gap(self):
        result = find_plan_gaps({"context/goal.md": ""})
        assert result["gaps"] == ["context/goal.md: empty"]
        assert result["blocked"] is True

    def test_whitespace_only_is_gap(self):
        result = find_plan_gaps({"context/goal.md": "   \n\t  "})
        assert result["gaps"] == ["context/goal.md: empty"]

    def test_empty_takes_precedence_over_placeholder(self):
        # A whitespace-only file that happens to contain "TODO" after strip
        # would be empty — but that's impossible. Confirm empty check runs first
        # by using a file that is purely whitespace.
        result = find_plan_gaps({"f.md": "  "})
        assert result["gaps"] == ["f.md: empty"]


class TestPlaceholderKeywords:
    @pytest.mark.parametrize("keyword", ["TODO", "TBD", "FIXME", "XXX", "TKTK", "placeholder"])
    def test_keyword_detected(self, keyword):
        result = find_plan_gaps({"f.md": f"The goal is {keyword} — fill in later."})
        assert result["gaps"] == ["f.md: unresolved placeholder"]
        assert result["blocked"] is True

    @pytest.mark.parametrize("keyword", ["todo", "tbd", "fixme", "xxx", "tktk", "Placeholder"])
    def test_keyword_case_insensitive(self, keyword):
        result = find_plan_gaps({"f.md": f"Some {keyword} here."})
        assert result["gaps"] == ["f.md: unresolved placeholder"]

    def test_word_boundary_required(self):
        # "TODOS" should not match because \b requires a word boundary after TODO
        result = find_plan_gaps({"f.md": "TODOS and TODOS."})
        assert result["gaps"] == []
        assert result["blocked"] is False


class TestEllipsis:
    def test_three_dots_is_placeholder(self):
        result = find_plan_gaps({"f.md": "The approach is ... to be determined."})
        assert result["gaps"] == ["f.md: unresolved placeholder"]

    def test_four_dots_no_match(self):
        result = find_plan_gaps({"f.md": "A sentence ending...."})
        assert result["gaps"] == []
        assert result["blocked"] is False

    def test_five_dots_no_match(self):
        result = find_plan_gaps({"f.md": "Many dots....."})
        assert result["gaps"] == []
        assert result["blocked"] is False

    def test_unicode_ellipsis_is_placeholder(self):
        result = find_plan_gaps({"f.md": "The scope is… undetermined."})
        assert result["gaps"] == ["f.md: unresolved placeholder"]

    def test_three_dots_at_end_of_string(self):
        result = find_plan_gaps({"f.md": "Work in progress..."})
        assert result["gaps"] == ["f.md: unresolved placeholder"]

    def test_three_dots_followed_by_space(self):
        result = find_plan_gaps({"f.md": "Something... else"})
        assert result["gaps"] == ["f.md: unresolved placeholder"]


class TestCleanContent:
    def test_non_empty_placeholder_free_yields_no_gap(self):
        result = find_plan_gaps({"context/goal.md": "Deliver a reliable search feature."})
        assert result == {"gaps": [], "blocked": False}

    def test_multiple_clean_files_no_gaps(self):
        files = {
            "context/goal.md": "Ship the search feature by Q3.",
            "context/scope.md": "Backend only; no UI changes in scope.",
        }
        result = find_plan_gaps(files)
        assert result == {"gaps": [], "blocked": False}


class TestMultipleFiles:
    def test_gaps_reported_in_insertion_order(self):
        files = {
            "a.md": "",
            "b.md": "clean content here",
            "c.md": "TODO finish this",
        }
        result = find_plan_gaps(files)
        assert result["gaps"] == ["a.md: empty", "c.md: unresolved placeholder"]
        assert result["blocked"] is True

    def test_first_clean_then_gap(self):
        files = {
            "good.md": "This is fine.",
            "bad.md": "TBD",
        }
        result = find_plan_gaps(files)
        assert result["gaps"] == ["bad.md: unresolved placeholder"]

    def test_blocked_false_when_all_clean(self):
        files = {"a.md": "ok", "b.md": "also ok"}
        assert find_plan_gaps(files)["blocked"] is False

    def test_blocked_true_when_any_gap(self):
        files = {"a.md": "ok", "b.md": ""}
        assert find_plan_gaps(files)["blocked"] is True


# ---------------------------------------------------------------------------
# lint_plan MCP tool
# ---------------------------------------------------------------------------

class TestLintPlanTool:
    def test_clean_files_return_no_gaps(self):
        result = lint_plan({"goal.md": "Ship the search feature."})
        assert result == {"gaps": [], "blocked": False}

    def test_empty_file_returns_gap(self):
        result = lint_plan({"goal.md": ""})
        assert result["gaps"] == ["goal.md: empty"]
        assert result["blocked"] is True

    def test_placeholder_returns_gap(self):
        result = lint_plan({"scope.md": "FIXME: define scope"})
        assert result["gaps"] == ["scope.md: unresolved placeholder"]

    def test_empty_map_returns_no_gaps(self):
        result = lint_plan({})
        assert result == {"gaps": [], "blocked": False}

    def test_result_has_required_keys(self):
        result = lint_plan({"f.md": "some content"})
        assert "gaps" in result
        assert "blocked" in result


# ---------------------------------------------------------------------------
# lint_stage MCP tool
# ---------------------------------------------------------------------------

class TestLintStageTool:
    def test_reads_file_from_disk(self, tmp_path):
        (tmp_path / "goal.md").write_text("Ship a fast search feature.", encoding="utf-8")
        result = lint_stage(str(tmp_path), ["goal.md"])
        assert result == {"gaps": [], "blocked": False}

    def test_missing_file_surfaces_as_empty_gap(self, tmp_path):
        result = lint_stage(str(tmp_path), ["nonexistent.md"])
        assert result["gaps"] == ["nonexistent.md: empty"]
        assert result["blocked"] is True

    def test_placeholder_in_file_surfaces_as_gap(self, tmp_path):
        (tmp_path / "scope.md").write_text("TBD — ask product.", encoding="utf-8")
        result = lint_stage(str(tmp_path), ["scope.md"])
        assert result["gaps"] == ["scope.md: unresolved placeholder"]

    def test_empty_file_on_disk_surfaces_as_gap(self, tmp_path):
        (tmp_path / "empty.md").write_text("", encoding="utf-8")
        result = lint_stage(str(tmp_path), ["empty.md"])
        assert result["gaps"] == ["empty.md: empty"]

    def test_mixed_files(self, tmp_path):
        (tmp_path / "goal.md").write_text("Clear goal.", encoding="utf-8")
        (tmp_path / "scope.md").write_text("", encoding="utf-8")
        result = lint_stage(str(tmp_path), ["goal.md", "scope.md"])
        assert result["gaps"] == ["scope.md: empty"]

    def test_empty_file_list_returns_no_gaps(self, tmp_path):
        result = lint_stage(str(tmp_path), [])
        assert result == {"gaps": [], "blocked": False}
