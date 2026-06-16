# plan-grader-mcp-server

![License](https://img.shields.io/github/license/kevinthelago/plan-grader-mcp-server) ![Last commit](https://img.shields.io/github/last-commit/kevinthelago/plan-grader-mcp-server)

# Plan Grader MCP Server

## Overview

# Plan Grader MCP Server

## Tech stack

# Stack

One repo, one language. Choices are dictated by the host's drop-in conventions (match the sibling first-party servers exactly) — not open design decisions.

| Layer | Choice | Notes / justification |
|---|---|---|
| **Language** | Python ≥ 3.10 | Matches sibling first-party servers. `match`/union types/`list[str]` generics want ≥3.10; keep the floor there unless the `mcp` SDK forces higher. |
| **Build front-end / packaging** | **uv**, invoked as `python -m uv` | The host builds the clone with **`python -m uv sync`** and launches with **`python -m uv run --directory {dir} plan-grader-mcp`**. Never a bare `uv` — its console-script shim is often not on PATH on a fresh machine. `pyproject.toml` must build clean from a clean checkout under `python -m uv sync`. |
| **Build backend** | Hatchling (`hatchling.build`) | Standard PEP 517 backend for a `src/`-layout package; uv works with it out of the box. (Agent decides; default = hatchling.) |
| **Project layout** | `src/` layout — `src/plan_grader/` | Package import name `plan_grader`; console-script `plan-grader-mcp = "plan_grader.server:main"`. |
| **MCP framework** | Official `mcp` Python SDK — `FastMCP` | `FastMCP("plan-grader")` registers the three tools; `main()` runs `mcp.run()` over **stdio**. |
| **Transport** | MCP **stdio** | The only transport. No HTTP/SSE. |
| **Testing** | **pytest** | Run as `python -m uv run pytest`. Parity fixtures live in `tests/`. |
| **Runtime deps** | `mcp` (the SDK) only | The grade path is pure stdlib (`json`, `re`, `dataclasses`, `statistics`/manual mean). No network/HTTP/clock/random libraries — forbidden by the determinism rule. |
| **Determinism** | stdlib only in `grade.py` | No `datetime.now`, no `random`, no I/O beyond reading the three JSON files in the server layer. Same inputs → byte-identical output. |

## Toolchain commands (build / test / run)

- Build/sync: `python -m uv sync`
- Run server: `python -m uv run plan-grader-mcp`
- Tests: `python -m uv run pytest`

These will be registered in `commands.json` (project + repo scope) so build/triage sessions don't block on permission prompts. `python` and `pytest`/`uv` invocations all go through `python -m uv run`, so the allowed binary is **`python`**.

## Open defaults (agent decides)

- **Python version floor** — default **3.10**; bump only if the pinned `mcp` SDK requires it.
- **Build backend** — default **hatchling**; any PEP 517 backend that builds the `src/` layout under `python -m uv sync` is acceptable.
- **`mcp` SDK version** — pin a recent stable `mcp` release that exposes `FastMCP`; agent picks the version at build time.

## Getting started

```bash
git clone https://github.com/kevinthelago/plan-grader-mcp-server.git
cd plan-grader-mcp-server
# install dependencies and run the project's build/test/dev commands
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

See [LICENSE](LICENSE).

---

_Scaffolded by base-studio-code._