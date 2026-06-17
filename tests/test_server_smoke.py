"""Smoke test: MCP tools/list returns exactly the three expected tools.

Depends on F7 (grade_plan), F8 (grade_issue), F10 (lint_plan) having been
merged so their modules exist under plan_grader/tools/.
"""

import asyncio
import importlib
import pkgutil
from typing import List

import pytest
from mcp.types import Tool

import plan_grader.tools
from plan_grader.app import mcp

EXPECTED_TOOLS = {"grade_plan", "grade_issue", "lint_plan"}


@pytest.fixture(scope="module")
def tools() -> List[Tool]:
    for _finder, name, _ispkg in pkgutil.iter_modules(
        plan_grader.tools.__path__,
        plan_grader.tools.__name__ + ".",
    ):
        importlib.import_module(name)
    return asyncio.run(mcp.list_tools())


def test_tools_list_count(tools):
    assert {t.name for t in tools} == EXPECTED_TOOLS


def test_tools_have_description_and_schema(tools):
    for tool in tools:
        assert tool.description, f"Tool {tool.name!r} missing description"
        assert tool.inputSchema, f"Tool {tool.name!r} missing inputSchema"


def test_lint_stage_absent(tools):
    assert "lint_stage" not in {t.name for t in tools}
