"""Tests for grade.letter_from_score and grade.grade_issue (F3)."""
from __future__ import annotations

import pytest
from plan_grader.grade import grade_issue, letter_from_score


# ---------------------------------------------------------------------------
# letter_from_score
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "score, expected",
    [
        (1.00, "A"),
        (0.90, "A"),
        (0.89, "B"),
        (0.75, "B"),
        (0.74, "C"),
        (0.60, "C"),
        (0.59, "D"),
        (0.45, "D"),
        (0.44, "F"),
        (0.00, "F"),
    ],
)
def test_letter_from_score_bands(score, expected):
    assert letter_from_score(score) == expected


# ---------------------------------------------------------------------------
# grade_issue – full score
# ---------------------------------------------------------------------------

def _perfect_issue(ref="X1"):
    return {
        "ref": ref,
        "title": "Implement something useful",
        "acceptance": ["criterion one", "criterion two"],
        "owns": ["src/x.py"],
        "phase": "Phase 1",
        "stream": "stream-x",
        "repo": "repo-x",
    }


def test_grade_issue_perfect():
    g = grade_issue(_perfect_issue())
    assert g["ref"] == "X1"
    assert g["score"] == pytest.approx(1.0)
    assert g["letter"] == "A"
    assert g["reasons"] == []


# ---------------------------------------------------------------------------
# acceptance dimension
# ---------------------------------------------------------------------------

def test_grade_issue_acceptance_two():
    g = grade_issue(_perfect_issue())
    assert g["score"] == pytest.approx(1.0)
    assert "no acceptance criteria" not in g["reasons"]


def test_grade_issue_acceptance_one():
    issue = {**_perfect_issue(), "acceptance": ["only one"]}
    g = grade_issue(issue)
    assert g["score"] == pytest.approx(0.18 + 0.20 + 0.20 + 0.15 + 0.10)
    assert "only 1 acceptance criterion (aim for >=2)" in g["reasons"]


def test_grade_issue_acceptance_zero():
    issue = {**_perfect_issue(), "acceptance": []}
    g = grade_issue(issue)
    assert "no acceptance criteria" in g["reasons"]
    assert g["score"] == pytest.approx(0.20 + 0.20 + 0.15 + 0.10)


def test_grade_issue_acceptance_missing_key():
    issue = {k: v for k, v in _perfect_issue().items() if k != "acceptance"}
    g = grade_issue(issue)
    assert "no acceptance criteria" in g["reasons"]


# ---------------------------------------------------------------------------
# ownership dimension
# ---------------------------------------------------------------------------

def test_grade_issue_no_owns():
    issue = {**_perfect_issue(), "owns": []}
    g = grade_issue(issue)
    assert "no owned files/globs declared" in g["reasons"]
    assert g["score"] == pytest.approx(0.35 + 0.20 + 0.15 + 0.10)


# ---------------------------------------------------------------------------
# milestone dimension
# ---------------------------------------------------------------------------

def test_grade_issue_no_phase():
    issue = {**_perfect_issue(), "phase": None}
    g = grade_issue(issue)
    assert "not assigned to a milestone/phase" in g["reasons"]
    assert g["score"] == pytest.approx(0.35 + 0.20 + 0.15 + 0.10)


# ---------------------------------------------------------------------------
# stream dimension
# ---------------------------------------------------------------------------

def test_grade_issue_no_stream():
    issue = {**_perfect_issue(), "stream": None}
    g = grade_issue(issue)
    assert "no owning stream" in g["reasons"]
    assert g["score"] == pytest.approx(0.35 + 0.20 + 0.20 + 0.10)


# ---------------------------------------------------------------------------
# title dimension
# ---------------------------------------------------------------------------

def test_grade_issue_short_title():
    issue = {**_perfect_issue(), "title": "Short"}
    g = grade_issue(issue)
    assert "title too short" in g["reasons"]
    assert g["score"] == pytest.approx(0.35 + 0.20 + 0.20 + 0.15)


def test_grade_issue_title_exactly_10():
    issue = {**_perfect_issue(), "title": "1234567890"}
    g = grade_issue(issue)
    assert "title too short" not in g["reasons"]


def test_grade_issue_title_strip_whitespace():
    # "exactly ten" = 11 chars after strip → should pass
    issue = {**_perfect_issue(), "title": "   exactly ten   "}
    g = grade_issue(issue)
    assert "title too short" not in g["reasons"]


# ---------------------------------------------------------------------------
# score is clamped to [0, 1]
# ---------------------------------------------------------------------------

def test_grade_issue_score_clamped_to_one():
    g = grade_issue(_perfect_issue())
    assert g["score"] <= 1.0


def test_grade_issue_all_missing():
    g = grade_issue({"ref": "Z"})
    assert g["score"] == pytest.approx(0.0)
    assert g["letter"] == "F"
    assert len(g["reasons"]) == 5
