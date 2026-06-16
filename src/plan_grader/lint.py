"""Pure gap-detection logic for plan section files."""

from __future__ import annotations

import re

# Matches the host's placeholder pattern exactly (case-insensitive).
# '....' (four or more dots) does not match because of the negative lookahead.
_PLACEHOLDER_RE = re.compile(
    r"\b(TODO|TBD|FIXME|XXX|TKTK|placeholder)\b|\.\.\.(?!\.)|…",
    re.IGNORECASE,
)


def find_plan_gaps(files: dict[str, str]) -> dict:
    """Lint a filename-to-content map for empty files and unresolved placeholders.

    Args:
        files: Mapping of filename to file content.  The caller decides which
            files to include; there is no required set.

    Returns:
        ``{"gaps": [...], "blocked": bool}`` where each gap is one of:
        ``"{file}: empty"`` (whitespace-only content, checked first) or
        ``"{file}: unresolved placeholder"`` (content contains a TODO/TBD/
        FIXME/XXX/TKTK/placeholder keyword, ``...``, or ``…``).
        ``blocked`` is ``True`` when any gaps were found.
    """
    gaps: list[str] = []
    for filename, content in files.items():
        if not content.strip():
            gaps.append(f"{filename}: empty")
        elif _PLACEHOLDER_RE.search(content):
            gaps.append(f"{filename}: unresolved placeholder")
    return {"gaps": gaps, "blocked": bool(gaps)}
