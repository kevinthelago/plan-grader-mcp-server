"""Tests for grade_milestone, grade_repo, and grade_plan (F4, F5, F11)."""
from __future__ import annotations

import pytest
from plan_grader.grade import (
    MIN_ISSUES,
    MAX_ISSUES,
    grade_milestone,
    grade_plan,
    grade_repo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _issue(ref, *, title="Descriptive title here", acceptance=None, owns=None,
           phase="Phase 1", stream="s", repo="repo-a"):
    return {
        "ref": ref,
        "title": title,
        "acceptance": acceptance if acceptance is not None else ["c1", "c2"],
        "owns": owns if owns is not None else ["src/f.py"],
        "phase": phase,
        "stream": stream,
        "repo": repo,
    }


def _perfect(ref, **kw):
    return _issue(ref, **kw)


# ---------------------------------------------------------------------------
# grade_milestone
# ---------------------------------------------------------------------------

class TestGradeMilestone:
    def test_empty(self):
        g = grade_milestone([], name="M")
        assert g["score"] == pytest.approx(0.0)
        assert g["letter"] == "F"
        assert g["reasons"] == ["no issues in this milestone"]
        assert g["issueGrades"] == []

    def test_single_issue_gets_penalty(self):
        g = grade_milestone([_perfect("X1")], name="M")
        # avg=1.0, bonus=0.75 → score=0.75
        assert g["score"] == pytest.approx(0.75)
        assert g["letter"] == "B"
        assert "only 1 issue — too few; consider decomposing further" in g["reasons"]

    def test_two_issues_no_penalty(self):
        g = grade_milestone([_perfect("X1"), _perfect("X2")], name="M")
        assert g["score"] == pytest.approx(1.0)
        assert g["reasons"] == []

    def test_too_many_issues_penalty(self):
        issues = [_perfect(f"X{i}") for i in range(MAX_ISSUES + 1)]
        g = grade_milestone(issues, name="M")
        assert g["score"] == pytest.approx(1.0 * 0.85)
        assert f"{MAX_ISSUES + 1} issues — unusually many; consider splitting the milestone" in g["reasons"]

    def test_issue_count_tracked(self):
        issues = [_perfect("X1"), _perfect("X2"), _perfect("X3")]
        g = grade_milestone(issues, name="M")
        assert g["issueCount"] == 3


# ---------------------------------------------------------------------------
# grade_repo
# ---------------------------------------------------------------------------

REPOS = [{"name": "repo-a"}, {"name": "repo-b"}]
PHASES = [{"name": "Phase 1"}, {"name": "Phase 2"}]


class TestGradeRepo:
    def test_no_issues_for_repo(self):
        g = grade_repo([], REPOS, PHASES, "repo-a")
        assert g["score"] == pytest.approx(0.0)
        assert g["letter"] == "F"
        assert g["reasons"] == ["no issues attributed to this repo"]
        assert g["milestoneGrades"] == []

    def test_blank_repo_falls_back_to_first(self):
        issues = [_perfect("X1", phase="Phase 1", repo="")]
        g = grade_repo(issues, REPOS, PHASES, "repo-a")
        assert g["issueCount"] == 1

    def test_phase_matched_by_name(self):
        issues = [_perfect("X1", phase="Phase 1"), _perfect("X2", phase="Phase 1")]
        g = grade_repo(issues, REPOS, PHASES, "repo-a")
        ms_names = [m["name"] for m in g["milestoneGrades"]]
        assert "Phase 1" in ms_names

    def test_phase_matched_by_1based_index(self):
        # "1" should match phases[0] = "Phase 1"
        issues = [_perfect("X1", phase="1"), _perfect("X2", phase="1")]
        g = grade_repo(issues, REPOS, PHASES, "repo-a")
        ms_names = [m["name"] for m in g["milestoneGrades"]]
        assert "Phase 1" in ms_names

    def test_unscheduled_issues_form_own_group(self):
        issues = [
            _perfect("X1", phase="Phase 1"),
            _perfect("X2", phase="Phase 1"),
            _issue("X3", phase=None),
        ]
        g = grade_repo(issues, REPOS, PHASES, "repo-a")
        assert "1 unscheduled issue(s)" in g["reasons"]
        ms_names = [m["name"] for m in g["milestoneGrades"]]
        assert "Unscheduled" in ms_names

    def test_repo_score_is_issue_count_weighted(self):
        # Phase 1: 2 perfect issues (score 1.0 each)
        # Unscheduled: 2 bare issues with no phase, no stream, no owns,
        #              no acceptance, short title → score 0.0 each
        # Repo score = (1.0*2 + 0.0*2) / 4 = 0.5
        issues = [
            _perfect("X1", phase="Phase 1"),
            _perfect("X2", phase="Phase 1"),
            _issue("X3", phase=None, acceptance=[], owns=[], stream=None,
                   title="x", repo="repo-a"),
            _issue("X4", phase=None, acceptance=[], owns=[], stream=None,
                   title="x", repo="repo-a"),
        ]
        g = grade_repo(issues, REPOS, PHASES, "repo-a")
        assert g["score"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# grade_plan – empty / edge cases
# ---------------------------------------------------------------------------

class TestGradePlanEmpty:
    def test_no_issues(self):
        g = grade_plan([], [], [{"name": "r"}])
        assert g["score"] == pytest.approx(0.0)
        assert g["letter"] == "F"
        assert g["reasons"] == ["no issues defined"]
        assert g["repoGrades"] == []
        assert g["categories"] == []
        assert g["suggestions"] == []

    def test_no_repos(self):
        g = grade_plan([_perfect("X1")], [], [])
        assert g["score"] == pytest.approx(0.0)
        assert g["letter"] == "F"
        assert g["reasons"] == ["no repos linked"]
        assert g["repoGrades"] == []
        assert g["categories"] == []
        assert g["suggestions"] == []

    def test_unlinked_repo_reason(self):
        issues = [_issue("X1", repo="unknown-repo")]
        repos = [{"name": "repo-a"}]
        g = grade_plan(issues, [], repos)
        assert "1 issue(s) reference an unlinked repo" in g["reasons"]

    def test_blank_repo_attributed_to_first(self):
        issues = [_perfect("X1", repo=""), _perfect("X2", repo="")]
        repos = [{"name": "repo-a"}]
        phases = [{"name": "Phase 1"}]
        g = grade_plan(issues, phases, repos)
        assert g["repoGrades"][0]["issueCount"] == 2


# ---------------------------------------------------------------------------
# grade_plan – strong fixture
# ---------------------------------------------------------------------------

class TestGradePlanStrong:
    def test_strong_plan_grades_A(self, strong_plan):
        issues, phases, repos = strong_plan
        g = grade_plan(issues, phases, repos)
        assert g["score"] == pytest.approx(1.0)
        assert g["letter"] == "A"

    def test_strong_plan_no_reasons(self, strong_plan):
        issues, phases, repos = strong_plan
        g = grade_plan(issues, phases, repos)
        assert g["reasons"] == []

    def test_strong_plan_minimal_suggestions(self, strong_plan):
        issues, phases, repos = strong_plan
        g = grade_plan(issues, phases, repos)
        assert g["suggestions"] == []

    def test_strong_plan_one_repo_grade_per_repo(self, strong_plan):
        issues, phases, repos = strong_plan
        g = grade_plan(issues, phases, repos)
        assert len(g["repoGrades"]) == len(repos)


# ---------------------------------------------------------------------------
# grade_plan – thin fixture
# ---------------------------------------------------------------------------

class TestGradePlanThin:
    def test_thin_plan_grades_D(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        # Phase 1: 2 perfect (1.0); Unscheduled: 2 zeroes (0.0) → repo = 0.5 → D
        assert g["score"] == pytest.approx(0.5)
        assert g["letter"] == "D"

    def test_thin_plan_unscheduled_reason(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        repo_g = g["repoGrades"][0]
        assert "2 unscheduled issue(s)" in repo_g["reasons"]

    def test_thin_plan_category_details(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        cats = {c["id"]: c for c in g["categories"]}

        assert cats["acceptance"]["detail"] == "2/4 issues have >=2 acceptance criteria"
        assert cats["ownership"]["detail"] == "2/4 issues declare owned files"
        assert cats["milestones"]["detail"] == "2/4 issues are assigned to a milestone"
        assert cats["streams"]["detail"] == "2/4 issues have an owning stream"
        assert cats["titles"]["detail"] == "2/4 issues have a descriptive title (>=10 chars)"

    def test_thin_plan_suggestions_priority_order(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        priorities = [s["priority"] for s in g["suggestions"]]
        # high must come before medium, medium before low
        order = {"high": 0, "medium": 1, "low": 2}
        assert priorities == sorted(priorities, key=lambda p: order[p])

    def test_thin_plan_suggestion_titles(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        titles = {s["id"]: s["title"] for s in g["suggestions"]}
        # K = round(0.5 * 4) = 2
        assert titles["acceptance"] == "2 issue(s): add acceptance criteria"
        assert titles["ownership"] == "2 issue(s): declare owned files"
        assert titles["milestones"] == "2 issue(s): assign to a milestone"
        assert titles["streams"] == "2 issue(s): assign an owning stream"
        assert titles["titles"] == "2 issue(s): improve title (aim for >=10 chars)"

    def test_thin_plan_suggestions_include_examples(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        for s in g["suggestions"]:
            assert "(e.g." in s["detail"]

    def test_thin_plan_acceptance_high_priority(self, thin_plan):
        issues, phases, repos = thin_plan
        g = grade_plan(issues, phases, repos)
        acc = next(s for s in g["suggestions"] if s["id"] == "acceptance")
        assert acc["priority"] == "high"


# ---------------------------------------------------------------------------
# grade_plan – granularity
# ---------------------------------------------------------------------------

class TestGranularity:
    def test_granularity_bonus_below_min(self):
        # 1 issue in the milestone (< MIN_ISSUES=2) → penalty 0.75
        issues = [_perfect("X1")]
        phases = [{"name": "Phase 1"}]
        repos = [{"name": "repo-a"}]
        g = grade_plan(issues, phases, repos)
        gran = next(c for c in g["categories"] if c["id"] == "granularity")
        # 1 milestone with 1 issue → off-size → 0/1 well-sized → score=0
        assert gran["score"] == pytest.approx(0.0)

    def test_granularity_bonus_above_max(self):
        issues = [_perfect(f"X{i}") for i in range(MAX_ISSUES + 1)]
        phases = [{"name": "Phase 1"}]
        repos = [{"name": "repo-a"}]
        g = grade_plan(issues, phases, repos)
        gran = next(c for c in g["categories"] if c["id"] == "granularity")
        assert gran["score"] == pytest.approx(0.0)

    def test_granularity_well_sized(self):
        issues = [_perfect("X1"), _perfect("X2"), _perfect("X3")]
        phases = [{"name": "Phase 1"}]
        repos = [{"name": "repo-a"}]
        g = grade_plan(issues, phases, repos)
        gran = next(c for c in g["categories"] if c["id"] == "granularity")
        assert gran["score"] == pytest.approx(1.0)

    def test_granularity_suggestion_title(self):
        # 1 issue → off-size milestone → granularity suggestion
        issues = [_perfect("X1")]
        phases = [{"name": "Phase 1"}]
        repos = [{"name": "repo-a"}]
        g = grade_plan(issues, phases, repos)
        gran_s = next((s for s in g["suggestions"] if s["id"] == "granularity"), None)
        assert gran_s is not None
        assert "Re-scope" in gran_s["title"]
        assert "2-15 issues" in gran_s["title"]


# ---------------------------------------------------------------------------
# loader integration
# ---------------------------------------------------------------------------

class TestLoader:
    def test_loader_reads_strong_fixture(self, tmp_path):
        import json, shutil
        from pathlib import Path
        from plan_grader.loader import load_plan

        src = Path(__file__).parent / "fixtures" / "strong_plan"
        for f in src.iterdir():
            shutil.copy(f, tmp_path / f.name)

        issues, phases, repos = load_plan(str(tmp_path))
        assert len(issues) == 4
        assert len(phases) == 2
        assert len(repos) == 2

    def test_loader_missing_files_default_empty(self, tmp_path):
        from plan_grader.loader import load_plan

        issues, phases, repos = load_plan(str(tmp_path))
        assert issues == []
        assert phases == []
        assert repos == []
