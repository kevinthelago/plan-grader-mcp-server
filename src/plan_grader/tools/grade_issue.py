from plan_grader.app import mcp
from plan_grader import grade


@mcp.tool()
def grade_issue(issue: dict) -> dict:
    """Grade a single plan issue on five weighted dimensions.

    Returns {ref, score, letter, reasons} using the same rubric applied
    per-issue inside grade_plan. Optional fields are tolerated; absent
    fields trigger their respective shortfall reasons.
    """
    return grade.grade_issue(issue)
