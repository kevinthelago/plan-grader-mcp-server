# plan-grader-mcp-server

![License](https://img.shields.io/github/license/kevinthelago/plan-grader-mcp-server) ![Last commit](https://img.shields.io/github/last-commit/kevinthelago/plan-grader-mcp-server)

An MCP server that grades GitHub project plans, individual issues, and milestones against a structured rubric. Exposes three tools over stdio transport so any MCP-compatible host can drive it.

## Tools

### `grade_plan`

Grade a complete project plan loaded from disk or passed as direct arrays.

**Signature**
```
grade_plan(
    plan_dir: str = ".",
    issues: list | None = None,
    phases: list | None = None,
    repos: list | None = None,
) -> PlanGrade
```

Reads `issues.json`, `phases.json`, and `repos.json` from `plan_dir` by default. Pass the `issues`/`phases`/`repos` arrays directly to skip file I/O.

**Returns** `PlanGrade` — JSON-serializable object with:
```json
{
  "score": 0.82,
  "letter": "B",
  "reasons": [],
  "repoGrades": [...],
  "categories": [
    {"id": "acceptance", "label": "Acceptance criteria", "score": 0.9, "letter": "A", "weight": 0.35, "detail": "...", "examples": []},
    {"id": "ownership",  "label": "Ownership",           "score": 0.8, "letter": "B", "weight": 0.20, ...},
    {"id": "milestones", "label": "Milestones",          "score": 0.7, "letter": "C", "weight": 0.20, ...},
    {"id": "streams",    "label": "Streams",             "score": 1.0, "letter": "A", "weight": 0.15, ...},
    {"id": "titles",     "label": "Titles",              "score": 1.0, "letter": "A", "weight": 0.10, ...},
    {"id": "granularity","label": "Granularity",         "score": 0.6, "letter": "D", "weight": 0.0,  ...}
  ],
  "suggestions": [
    {"priority": "high", "title": "3 issue(s): add acceptance criteria", "detail": "..."}
  ]
}
```

---

### `grade_issue`

Grade a single GitHub issue against the per-issue rubric.

**Signature**
```
grade_issue(issue: dict) -> IssueGrade
```

`issue` is a raw issue dict (e.g. from the GitHub API). Optional fields are tolerated.

**Returns**
```json
{
  "ref": "#42",
  "score": 0.75,
  "letter": "B",
  "reasons": ["only 1 acceptance criterion (aim for >=2)"]
}
```

Scoring bands: A ≥ 0.90 · B ≥ 0.75 · C ≥ 0.60 · D ≥ 0.45 · F below 0.45.

Weighted dimensions (sum to 1.0):
| Dimension | Weight | Passes when… |
|---|---|---|
| acceptance | 0.35 | ≥ 2 acceptance criteria |
| ownership | 0.20 | `owns` field lists ≥ 1 file/glob |
| milestones | 0.20 | issue is assigned to a milestone/phase |
| streams | 0.15 | issue has an owning stream |
| titles | 0.10 | stripped title is ≥ 10 characters |

---

### `lint_plan`

Scan a set of plan files for unresolved placeholders and empty content.

**Signature**
```
lint_plan(files: dict[str, str]) -> LintResult
```

`files` maps filename → file content (strings). An empty map returns no gaps.

**Returns**
```json
{
  "gaps": ["README.md: unresolved placeholder", "ROADMAP.md: empty"],
  "blocked": true
}
```

Detected patterns: `TODO`, `TBD`, `FIXME`, `XXX`, `TKTK`, `placeholder` (case-insensitive), and `…` / `...` (but not `....`).

---

## Install

Downloads to `~/.base-studio-code/mcp/plan-grader-mcp-server`, then builds with `python -m uv sync`.

After cloning:

```bash
cd ~/.base-studio-code/mcp/plan-grader-mcp-server
python -m uv sync
```

Add to your MCP host config:

```json
{
  "mcpServers": {
    "plan-grader": {
      "command": "python",
      "args": ["-m", "uv", "run", "--directory", "/path/to/plan-grader-mcp-server", "plan-grader-mcp"]
    }
  }
}
```

## Local run

```bash
python -m uv run plan-grader-mcp
```

The server speaks MCP over stdio and stays running until the host closes the connection.

## Tests

```bash
python -m uv run pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

See [LICENSE](LICENSE).
