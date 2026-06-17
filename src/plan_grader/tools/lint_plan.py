"""MCP tools: lint_plan and lint_stage — detect gaps in plan section files."""

from __future__ import annotations

import os

from plan_grader.app import mcp
from plan_grader.grade import find_plan_gaps


@mcp.tool()
def lint_plan(files: dict[str, str]) -> dict:
    """Check plan section files for empty content or unresolved placeholders.

    Args:
        files: Mapping of filename to file content (e.g.
            ``{"context/goal.md": "...", "context/scope.md": "..."}``).
            Any filenames are accepted; the caller decides the set.

    Returns:
        ``{"gaps": list[str], "blocked": bool}``.  Each gap is
        ``"{filename}: empty"`` or ``"{filename}: unresolved placeholder"``.
        ``blocked`` is ``True`` when at least one gap exists.
    """
    return find_plan_gaps(files)


def lint_stage(plan_dir: str, files: list[str]) -> dict:
    """Read named files from *plan_dir* and lint them for gaps.

    Args:
        plan_dir: Directory that contains the plan files.
        files: Names of files to read relative to *plan_dir*.
            A file that cannot be read is treated as empty and surfaces as a
            ``"{file}: empty"`` gap.

    Returns:
        Same shape as :func:`lint_plan`.
    """
    content_map: dict[str, str] = {}
    for name in files:
        path = os.path.join(plan_dir, name)
        try:
            with open(path, encoding="utf-8") as fh:
                content_map[name] = fh.read()
        except OSError:
            content_map[name] = ""
    return find_plan_gaps(content_map)
