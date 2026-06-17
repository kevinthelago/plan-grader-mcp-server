"""Parity tests for grade_issue across rubric branch points.

Covers: acceptance len 2/1/0, missing owns, missing phase, falsy stream,
short title, fully-passing issue, and identity between the standalone
grade_issue call and the per-issue grade produced by grade_plan.
"""
import pytest
from plan_grader import grade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_issue(**overrides) -> dict:
    """Return a fully-passing issue dict, with any field overridden."""
    issue = {
        "ref": "T1",
        "title": "Implement user authentication flow",
        "phase": 1,
        "stream": "auth-stream",
        "owns": ["src/auth/**"],
        "acceptance": [
            "Users can log in with email and password",
            "JWT token is issued on successful login",
        ],
        "repo": "myorg/myrepo",
    }
    issue.update(overrides)
    return issue


def _find_issue_grade(plan_grade: dict, ref: str) -> dict | None:
    """Navigate repoGrades -> milestoneGrades -> issueGrades to find grade by ref."""
    for repo_grade in plan_grade.get("repoGrades", []):
        for milestone_grade in repo_grade.get("milestoneGrades", []):
            for issue_grade in milestone_grade.get("issueGrades", []):
                if issue_grade.get("ref") == ref:
                    return issue_grade
    return None


# ---------------------------------------------------------------------------
# Fully-passing issue — 1.0 / A / no reasons
# ---------------------------------------------------------------------------

def test_fully_passing_issue():
    result = grade.grade_issue(_base_issue())
    assert result["score"] == pytest.approx(1.0)
    assert result["letter"] == "A"
    assert result["reasons"] == []
    assert result["ref"] == "T1"


# ---------------------------------------------------------------------------
# Acceptance dimension (weight 0.35)
# ---------------------------------------------------------------------------

def test_acceptance_two_criteria_full_credit():
    """>=2 criteria -> +0.35, score 1.0."""
    result = grade.grade_issue(_base_issue(acceptance=["a", "b"]))
    assert result["score"] == pytest.approx(1.0)
    assert result["letter"] == "A"
    assert not any("acceptance" in r for r in result["reasons"])


def test_acceptance_one_criterion_partial():
    """1 criterion -> +0.18 partial + reason; score 0.83 -> B."""
    result = grade.grade_issue(_base_issue(acceptance=["only one"]))
    # 0.18 + 0.20 + 0.20 + 0.15 + 0.10 = 0.83
    assert result["score"] == pytest.approx(0.83, abs=1e-9)
    assert result["letter"] == "B"
    assert "only 1 acceptance criterion (aim for >=2)" in result["reasons"]


def test_acceptance_zero_criteria_no_credit():
    """0 criteria -> +0.00 + reason; score 0.65 -> C."""
    result = grade.grade_issue(_base_issue(acceptance=[]))
    # 0.00 + 0.20 + 0.20 + 0.15 + 0.10 = 0.65
    assert result["score"] == pytest.approx(0.65, abs=1e-9)
    assert result["letter"] == "C"
    assert "no acceptance criteria" in result["reasons"]


def test_acceptance_absent_field():
    """Absent 'acceptance' key treated the same as empty list."""
    issue = _base_issue()
    del issue["acceptance"]
    result = grade.grade_issue(issue)
    assert result["score"] == pytest.approx(0.65, abs=1e-9)
    assert "no acceptance criteria" in result["reasons"]


# ---------------------------------------------------------------------------
# Ownership dimension (weight 0.20)
# ---------------------------------------------------------------------------

def test_owns_present_full_credit():
    result = grade.grade_issue(_base_issue(owns=["src/**"]))
    assert result["score"] == pytest.approx(1.0)
    assert not any("owned" in r for r in result["reasons"])


def test_owns_empty_list_no_credit():
    """Empty owns -> reason; score 0.80 -> B."""
    result = grade.grade_issue(_base_issue(owns=[]))
    # 0.35 + 0.00 + 0.20 + 0.15 + 0.10 = 0.80
    assert result["score"] == pytest.approx(0.80, abs=1e-9)
    assert result["letter"] == "B"
    assert "no owned files/globs declared" in result["reasons"]


def test_owns_absent_field():
    issue = _base_issue()
    del issue["owns"]
    result = grade.grade_issue(issue)
    assert result["score"] == pytest.approx(0.80, abs=1e-9)
    assert "no owned files/globs declared" in result["reasons"]


# ---------------------------------------------------------------------------
# Milestone/phase dimension (weight 0.20)
# ---------------------------------------------------------------------------

def test_phase_present_full_credit():
    result = grade.grade_issue(_base_issue(phase=1))
    assert result["score"] == pytest.approx(1.0)
    assert not any("milestone" in r for r in result["reasons"])


def test_phase_none_no_credit():
    """phase=None -> reason; score 0.80 -> B."""
    result = grade.grade_issue(_base_issue(phase=None))
    # 0.35 + 0.20 + 0.00 + 0.15 + 0.10 = 0.80
    assert result["score"] == pytest.approx(0.80, abs=1e-9)
    assert result["letter"] == "B"
    assert "not assigned to a milestone/phase" in result["reasons"]


def test_phase_absent_field():
    issue = _base_issue()
    del issue["phase"]
    result = grade.grade_issue(issue)
    assert result["score"] == pytest.approx(0.80, abs=1e-9)
    assert "not assigned to a milestone/phase" in result["reasons"]


# ---------------------------------------------------------------------------
# Stream dimension (weight 0.15)
# ---------------------------------------------------------------------------

def test_stream_truthy_full_credit():
    result = grade.grade_issue(_base_issue(stream="my-stream"))
    assert result["score"] == pytest.approx(1.0)
    assert not any("stream" in r for r in result["reasons"])


def test_stream_empty_string_no_credit():
    """stream='' (falsy) -> reason; score 0.85 -> B."""
    result = grade.grade_issue(_base_issue(stream=""))
    # 0.35 + 0.20 + 0.20 + 0.00 + 0.10 = 0.85
    assert result["score"] == pytest.approx(0.85, abs=1e-9)
    assert result["letter"] == "B"
    assert "no owning stream" in result["reasons"]


def test_stream_none_no_credit():
    result = grade.grade_issue(_base_issue(stream=None))
    assert result["score"] == pytest.approx(0.85, abs=1e-9)
    assert "no owning stream" in result["reasons"]


def test_stream_absent_field():
    issue = _base_issue()
    del issue["stream"]
    result = grade.grade_issue(issue)
    assert result["score"] == pytest.approx(0.85, abs=1e-9)
    assert "no owning stream" in result["reasons"]


# ---------------------------------------------------------------------------
# Title dimension (weight 0.10)
# ---------------------------------------------------------------------------

def test_title_long_enough_full_credit():
    result = grade.grade_issue(_base_issue(title="Add login feature"))  # 17 chars
    assert result["score"] == pytest.approx(1.0)
    assert not any("title" in r for r in result["reasons"])


def test_title_short_no_credit():
    """title.strip() < 10 chars -> reason; everything else passes -> 0.90 = 'A'."""
    result = grade.grade_issue(_base_issue(title="Fix bug"))  # 7 chars after strip
    # 0.35 + 0.20 + 0.20 + 0.15 + 0.00 = 0.90 -> 'A' (boundary)
    assert result["score"] == pytest.approx(0.90, abs=1e-9)
    assert result["letter"] == "A"
    assert "title too short" in result["reasons"]


def test_title_exactly_ten_chars_passes():
    result = grade.grade_issue(_base_issue(title="1234567890"))
    assert result["score"] == pytest.approx(1.0)
    assert not any("title" in r for r in result["reasons"])


def test_title_nine_chars_fails():
    result = grade.grade_issue(_base_issue(title="123456789"))
    assert "title too short" in result["reasons"]


def test_title_whitespace_stripped_before_check():
    """Surrounding whitespace is stripped before the length check."""
    result = grade.grade_issue(_base_issue(title="   Fix   "))  # 3 chars after strip
    assert "title too short" in result["reasons"]


def test_title_absent_field():
    issue = _base_issue()
    del issue["title"]
    result = grade.grade_issue(issue)
    assert "title too short" in result["reasons"]


# ---------------------------------------------------------------------------
# ref pass-through
# ---------------------------------------------------------------------------

def test_ref_echoed_back():
    result = grade.grade_issue(_base_issue(ref="MY-42"))
    assert result["ref"] == "MY-42"


def test_ref_absent_returns_none_or_absent():
    """Absent ref is echoed as None (or key absent), not injected."""
    issue = _base_issue()
    del issue["ref"]
    result = grade.grade_issue(issue)
    assert result.get("ref") is None or "ref" not in result


# ---------------------------------------------------------------------------
# Score boundary: clamping
# ---------------------------------------------------------------------------

def test_score_never_exceeds_one():
    assert grade.grade_issue(_base_issue())["score"] <= 1.0


def test_score_never_below_zero():
    issue = {"title": "x", "acceptance": [], "owns": []}
    assert grade.grade_issue(issue)["score"] >= 0.0


# ---------------------------------------------------------------------------
# All dimensions fail simultaneously
# ---------------------------------------------------------------------------

def test_all_dimensions_fail():
    """A bare issue with only a short title gets every shortfall reason and score 0."""
    issue = {"ref": "BARE", "title": "x"}
    result = grade.grade_issue(issue)
    assert result["score"] == pytest.approx(0.0)
    assert result["letter"] == "F"
    assert "no acceptance criteria" in result["reasons"]
    assert "no owned files/globs declared" in result["reasons"]
    assert "not assigned to a milestone/phase" in result["reasons"]
    assert "no owning stream" in result["reasons"]
    assert "title too short" in result["reasons"]


# ---------------------------------------------------------------------------
# Parity: grade_issue == per-issue grade inside grade_plan
# ---------------------------------------------------------------------------

def test_issue_grade_identical_in_plan():
    """A fully-passing issue scores identically standalone vs inside grade_plan."""
    issue = _base_issue(ref="PARITY-1")
    repos = ["myorg/myrepo"]
    phases = [{"name": "Phase 1"}]

    standalone = grade.grade_issue(issue)
    plan_result = grade.grade_plan(issues=[issue], phases=phases, repos=repos)

    in_plan = _find_issue_grade(plan_result, "PARITY-1")
    assert in_plan is not None, "issue grade not found in plan result — check field names in repoGrades"

    assert standalone["ref"] == in_plan["ref"]
    assert standalone["score"] == pytest.approx(in_plan["score"], abs=1e-12)
    assert standalone["letter"] == in_plan["letter"]
    assert standalone["reasons"] == in_plan["reasons"]


def test_partial_issue_grade_identical_in_plan():
    """A partial issue (acceptance=1) scores identically standalone vs inside grade_plan."""
    issue = _base_issue(ref="PARITY-2", acceptance=["one criterion"])
    repos = ["myorg/myrepo"]
    phases = [{"name": "Phase 1"}]

    standalone = grade.grade_issue(issue)
    plan_result = grade.grade_plan(issues=[issue], phases=phases, repos=repos)

    in_plan = _find_issue_grade(plan_result, "PARITY-2")
    assert in_plan is not None, "issue grade not found in plan result"

    assert standalone["score"] == pytest.approx(in_plan["score"], abs=1e-12)
    assert standalone["letter"] == in_plan["letter"]
    assert standalone["reasons"] == in_plan["reasons"]


# ---------------------------------------------------------------------------
# MCP tool surface
# ---------------------------------------------------------------------------

def test_grade_issue_tool_module_importable():
    """Importing the tool module triggers MCP registration without error."""
    from plan_grader.tools import grade_issue as _  # noqa: F401


def test_grade_issue_tool_function_delegates_to_grade():
    """The tool function delegates correctly to grade.grade_issue."""
    from plan_grader.tools.grade_issue import grade_issue as tool_fn

    issue = _base_issue()
    expected = grade.grade_issue(issue)
    result = tool_fn(issue)

    assert result["score"] == pytest.approx(expected["score"], abs=1e-12)
    assert result["letter"] == expected["letter"]
    assert result["reasons"] == expected["reasons"]
