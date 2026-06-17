from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Lint — find_plan_gaps (owned by lint-plan stream)
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(
    r"\b(TODO|TBD|FIXME|XXX|TKTK|placeholder)\b|(?<!\.)\.\.\.(?!\.)|…",
    re.IGNORECASE,
)


def find_plan_gaps(files: dict[str, str]) -> dict:
    """Lint a filename-to-content map for empty files and unresolved placeholders.

    Args:
        files: Mapping of filename to file content.

    Returns:
        ``{"gaps": list[str], "blocked": bool}`` where each gap string is
        ``"{file}: empty"`` or ``"{file}: unresolved placeholder"``.
    """
    gaps: list[str] = []
    for filename, content in files.items():
        if not content.strip():
            gaps.append(f"{filename}: empty")
        elif _PLACEHOLDER_RE.search(content):
            gaps.append(f"{filename}: unresolved placeholder")
    return {"gaps": gaps, "blocked": bool(gaps)}

MIN_ISSUES = 2
MAX_ISSUES = 15

_RUBRIC_DIMS: list[dict[str, Any]] = [
    {
        "id": "acceptance",
        "label": "Acceptance criteria",
        "weight": 0.35,
        "good_phrase": "have >=2 acceptance criteria",
        "fix_phrase": "add acceptance criteria",
        "why": "Acceptance criteria clarify when an issue is done.",
    },
    {
        "id": "ownership",
        "label": "Ownership",
        "weight": 0.20,
        "good_phrase": "declare owned files",
        "fix_phrase": "declare owned files",
        "why": "Ownership makes it clear who is responsible for which code.",
    },
    {
        "id": "milestones",
        "label": "Milestones",
        "weight": 0.20,
        "good_phrase": "are assigned to a milestone",
        "fix_phrase": "assign to a milestone",
        "why": "Milestones help prioritize and schedule work.",
    },
    {
        "id": "streams",
        "label": "Streams",
        "weight": 0.15,
        "good_phrase": "have an owning stream",
        "fix_phrase": "assign an owning stream",
        "why": "Streams keep parallel work organized.",
    },
    {
        "id": "titles",
        "label": "Titles",
        "weight": 0.10,
        "good_phrase": "have a descriptive title (>=10 chars)",
        "fix_phrase": "improve title (aim for >=10 chars)",
        "why": "Short titles make it hard to understand scope at a glance.",
    },
]


def letter_from_score(score: float) -> str:
    if score >= 0.90:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.60:
        return "C"
    if score >= 0.45:
        return "D"
    return "F"


def _dim_pass(issue: dict[str, Any], dim_id: str) -> bool:
    if dim_id == "acceptance":
        return len(issue.get("acceptance") or []) >= 2
    if dim_id == "ownership":
        return len(issue.get("owns") or []) > 0
    if dim_id == "milestones":
        return bool(issue.get("phase"))
    if dim_id == "streams":
        return bool(issue.get("stream"))
    if dim_id == "titles":
        return len((issue.get("title") or "").strip()) >= 10
    return False


def _repo_name(repo: Any) -> str:
    """Normalise a repo entry to its string identifier (supports str or dict)."""
    if isinstance(repo, str):
        return repo
    return repo.get("name", "") if repo else ""


def grade_issue(issue: dict[str, Any]) -> dict[str, Any]:
    ref = issue.get("ref")  # None when absent — do not default to ""
    score = 0.0
    reasons: list[str] = []

    acceptance = issue.get("acceptance") or []
    if len(acceptance) >= 2:
        score += 0.35
    elif len(acceptance) == 1:
        score += 0.18
        reasons.append("only 1 acceptance criterion (aim for >=2)")
    else:
        reasons.append("no acceptance criteria")

    owns = issue.get("owns") or []
    if len(owns) > 0:
        score += 0.20
    else:
        reasons.append("no owned files/globs declared")

    if issue.get("phase"):
        score += 0.20
    else:
        reasons.append("not assigned to a milestone/phase")

    if issue.get("stream"):
        score += 0.15
    else:
        reasons.append("no owning stream")

    title = (issue.get("title") or "").strip()
    if len(title) >= 10:
        score += 0.10
    else:
        reasons.append("title too short")

    score = min(1.0, max(0.0, score))

    return {
        "ref": ref,
        "score": score,
        "letter": letter_from_score(score),
        "reasons": reasons,
    }


def grade_milestone(issues: list[dict[str, Any]], name: str = "") -> dict[str, Any]:
    if not issues:
        return {
            "name": name,
            "score": 0.0,
            "letter": "F",
            "reasons": ["no issues in this milestone"],
            "issueGrades": [],
            "issueCount": 0,
        }

    issue_grades = [grade_issue(i) for i in issues]
    avg = sum(g["score"] for g in issue_grades) / len(issue_grades)
    n = len(issues)
    reasons: list[str] = []

    if n < MIN_ISSUES:
        bonus = 0.75
        reasons.append(f"only {n} issue — too few; consider decomposing further")
    elif n > MAX_ISSUES:
        bonus = 0.85
        reasons.append(f"{n} issues — unusually many; consider splitting the milestone")
    else:
        bonus = 1.0

    score = min(1.0, avg * bonus)

    return {
        "name": name,
        "score": score,
        "letter": letter_from_score(score),
        "reasons": reasons,
        "issueGrades": issue_grades,
        "issueCount": n,
    }


def grade_repo(
    issues: list[dict[str, Any]],
    repos: list[Any],
    phases: list[dict[str, Any]],
    repo_ref: str = "",
) -> dict[str, Any]:
    first_repo = _repo_name(repos[0]) if repos else ""
    effective_ref = repo_ref or first_repo

    repo_issues = [
        i for i in issues
        if (i.get("repo") or first_repo) == effective_ref
    ]

    if not repo_issues:
        return {
            "repo": effective_ref,
            "score": 0.0,
            "letter": "F",
            "reasons": ["no issues attributed to this repo"],
            "milestoneGrades": [],
            "issueCount": 0,
        }

    # Build phase lookup: name -> canonical name, "1-based-index" -> canonical name
    # Phases may be dicts with "name" or plain strings.
    phase_map: dict[str, str] = {}
    for idx, p in enumerate(phases, 1):
        pname = p.get("name", "") if isinstance(p, dict) else str(p)
        phase_map[pname] = pname
        phase_map[str(idx)] = pname

    groups: dict[str, list[dict[str, Any]]] = {}
    unscheduled: list[dict[str, Any]] = []
    for issue in repo_issues:
        raw_phase = issue.get("phase")
        if raw_phase:
            norm = phase_map.get(str(raw_phase))
        else:
            norm = None
        if norm:
            groups.setdefault(norm, []).append(issue)
        else:
            unscheduled.append(issue)

    reasons: list[str] = []
    if unscheduled:
        n = len(unscheduled)
        reasons.append(f"{n} unscheduled issue(s)")
        groups["Unscheduled"] = unscheduled

    milestone_grades = [
        grade_milestone(group_issues, gname)
        for gname, group_issues in groups.items()
    ]

    total_count = sum(mg["issueCount"] for mg in milestone_grades)
    if total_count == 0:
        repo_score = 0.0
    else:
        repo_score = min(
            1.0,
            sum(mg["score"] * mg["issueCount"] for mg in milestone_grades) / total_count,
        )

    return {
        "repo": effective_ref,
        "score": repo_score,
        "letter": letter_from_score(repo_score),
        "reasons": reasons,
        "milestoneGrades": milestone_grades,
        "issueCount": total_count,
    }


def _build_categories(
    issues: list[dict[str, Any]],
    repo_grades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    n = len(issues)
    categories: list[dict[str, Any]] = []

    for dim in _RUBRIC_DIMS:
        passing = [i for i in issues if _dim_pass(i, dim["id"])]
        failing = [i for i in issues if not _dim_pass(i, dim["id"])]
        score = len(passing) / n if n > 0 else 0.0
        detail = f'{len(passing)}/{n} issues {dim["good_phrase"]}'
        examples = [i.get("ref", "") for i in failing[:4]]
        categories.append(
            {
                "id": dim["id"],
                "label": dim["label"],
                "score": score,
                "letter": letter_from_score(score),
                "weight": dim["weight"],
                "detail": detail,
                "examples": examples,
            }
        )

    # Granularity (weight 0): fraction of milestones with >=1 issue sized 2..15
    all_ms = [
        mg
        for rg in repo_grades
        for mg in rg.get("milestoneGrades", [])
        if mg.get("issueCount", 0) > 0
    ]
    total_ms = len(all_ms)
    well_sized = [m for m in all_ms if MIN_ISSUES <= m["issueCount"] <= MAX_ISSUES]
    off_size = [m for m in all_ms if m["issueCount"] < MIN_ISSUES or m["issueCount"] > MAX_ISSUES]

    gran_score = len(well_sized) / total_ms if total_ms > 0 else 0.0
    gran_detail = (
        f"{len(well_sized)}/{total_ms} milestones sized 2-15 issues"
        if total_ms > 0
        else "no milestones resolved"
    )
    gran_examples = [f'{m["name"]} ({m["issueCount"]})' for m in off_size[:4]]

    categories.append(
        {
            "id": "granularity",
            "label": "Milestone granularity",
            "score": gran_score,
            "letter": letter_from_score(gran_score),
            "weight": 0.0,
            "detail": gran_detail,
            "examples": gran_examples,
        }
    )

    return categories


def _build_suggestions(
    categories: list[dict[str, Any]],
    issue_count: int,
) -> list[dict[str, Any]]:
    dim_map = {d["id"]: d for d in _RUBRIC_DIMS}
    suggestions: list[dict[str, Any]] = []

    for cat in categories:
        score = cat["score"]
        if score >= 0.999:
            continue

        shortfall = 1.0 - score
        weight = cat["weight"]
        impact = (weight if weight > 0 else 0.10) * shortfall

        if impact >= 0.12:
            priority = "high"
        elif impact >= 0.05:
            priority = "medium"
        else:
            priority = "low"

        examples = cat["examples"]
        cat_id = cat["id"]

        if cat_id == "granularity":
            k = len(examples)
            title = f"Re-scope {k} milestone(s) toward 2-15 issues"
            detail = "Milestones outside that range read as under- or over-scoped."
        else:
            dim = dim_map[cat_id]
            k = round(shortfall * issue_count)
            title = f"{k} issue(s): {dim['fix_phrase']}"
            detail = dim["why"]

        if examples:
            detail += f" (e.g. {', '.join(examples)})"

        suggestions.append(
            {
                "id": cat_id,
                "priority": priority,
                "title": title,
                "detail": detail,
                "impact": impact,
            }
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s["priority"], 3))

    return suggestions


def grade_plan(
    issues: list[dict[str, Any]],
    phases: list[Any],
    repos: list[Any],
) -> dict[str, Any]:
    _empty: dict[str, Any] = {
        "score": 0.0,
        "letter": "F",
        "reasons": [],
        "repoGrades": [],
        "categories": [],
        "suggestions": [],
    }

    if not issues:
        return {**_empty, "reasons": ["no issues defined"]}

    if not repos:
        return {**_empty, "reasons": ["no repos linked"]}

    first_repo = _repo_name(repos[0])
    repo_names = {_repo_name(r) for r in repos}

    reasons: list[str] = []
    unlinked = [i for i in issues if (i.get("repo") or first_repo) not in repo_names]
    if unlinked:
        reasons.append(f"{len(unlinked)} issue(s) reference an unlinked repo")

    repo_grades = [
        grade_repo(issues, repos, phases, _repo_name(repo))
        for repo in repos
    ]

    total_count = sum(rg["issueCount"] for rg in repo_grades)
    if total_count == 0:
        plan_score = 0.0
    else:
        plan_score = min(
            1.0,
            sum(rg["score"] * rg["issueCount"] for rg in repo_grades) / total_count,
        )

    categories = _build_categories(issues, repo_grades)
    suggestions = _build_suggestions(categories, len(issues))

    return {
        "score": plan_score,
        "letter": letter_from_score(plan_score),
        "reasons": reasons,
        "repoGrades": repo_grades,
        "categories": categories,
        "suggestions": suggestions,
    }
