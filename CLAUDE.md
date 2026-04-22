# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --extra dev

# Run the server (choose transport)
uv run python openproject-mcp-fastmcp.py   # stdio (Claude Desktop)
uv run python openproject-mcp-sse.py       # SSE (cloud deployment)
uv run python openproject-mcp-http.py      # HTTP with Bearer auth (multi-user)

# Tests
uv run pytest tests/                        # all tests
uv run pytest tests/test_work_packages.py  # single module
uv run pytest tests/ -k work_package       # by pattern
uv run pytest tests/ --cov=src             # with coverage
```

## Architecture

This is a [FastMCP](https://github.com/jlowin/fastmcp) server exposing ~49 tools for the OpenProject API v3. The server is async throughout and uses Pydantic for input validation.

**Entry points** (`openproject-mcp-fastmcp.py`, `openproject-mcp-sse.py`, `openproject-mcp-http.py`) each boot a different transport but all delegate to the same `src/` modules.

**`src/server.py`** — initializes the FastMCP instance, constructs the shared `OpenProjectClient`, and registers all tool modules.

**`src/client.py`** — the single async HTTP client wrapping the OpenProject API. All tool modules receive this client via dependency injection. It handles Basic Auth (API key encoded), exponential backoff retry (max 3), optional HTTP proxy, and `READ_ONLY_MODE` enforcement that blocks any mutating request.

**`src/tools/`** — one module per domain (work_packages, projects, users, memberships, hierarchy, relations, time_entries, versions, weekly_reports, news, connection). Each registers its tools via `@mcp.tool()` decorators.

**`src/utils/formatting.py`** — all tools format responses as markdown through helpers here before returning.

**`src/auth.py`** — Bearer token auth used only by the HTTP transport.

## Environment Variables

Required:
- `OPENPROJECT_URL` — base URL of the OpenProject instance
- `OPENPROJECT_API_KEY` — API key from user profile

Optional:
- `READ_ONLY_MODE=true` — blocks all write operations (POST/PATCH/PUT/DELETE)
- `OPENPROJECT_PROXY` — HTTP proxy URL
- `LOG_LEVEL` — DEBUG / INFO / WARNING / ERROR (default: INFO)
- `TEST_CONNECTION_ON_STARTUP=true` — validates API connectivity at boot

Copy `env_example.txt` to `.env` to get started.

## Tests

Tests live in `tests/` with one file per tool module. `tests/conftest.py` sets dummy env vars and provides a shared `mock_client` fixture (AsyncMock of `OpenProjectClient`). `pyproject.toml` sets `asyncio_mode = "auto"` so all async tests work without decorators.

The `tests/test_readonly_mode.py` module specifically validates that `READ_ONLY_MODE` rejects mutations.

## Custom Slash Commands

`.claude/commands/` provides project-specific commands:
- `/review-tool` — review a tool implementation against MCP best practices
- `/add-tool` — scaffold a new tool module
- `/test-coverage` — generate a coverage report
- `/api-docs` — look up OpenProject API docs
- `/optimize-code` — performance analysis
