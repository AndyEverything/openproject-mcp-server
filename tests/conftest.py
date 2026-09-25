"""Shared pytest configuration and fixtures.

Fikcyjne zmienne środowiskowe muszą być ustawione PRZED importem src.server.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("OPENPROJECT_URL", "https://op.example.test")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-key")
os.environ.setdefault("OPENPROJECT_CACHE_TTL", "600")

import src.server  # noqa: E402
from src.client import OpenProjectClient  # noqa: E402
from src.utils.cache import TTLCache  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_BASE_URL = os.environ["OPENPROJECT_URL"]


def read_fixture(name: str) -> Any:
    """Load tests/fixtures/<name>.json (".json" suffix optional)."""
    file_name = name if name.endswith(".json") else f"{name}.json"
    return json.loads((FIXTURES_DIR / file_name).read_text(encoding="utf-8"))


@pytest.fixture
def load_fixture() -> Callable[[str], Any]:
    """Return a loader: `load_fixture("wp_basic")` -> parsed JSON (fresh copy on each call)."""
    return read_fixture


@pytest.fixture
def mock_client(monkeypatch) -> MagicMock:
    """Replace the global client used by tools (src.server._client) with a mock.

    MagicMock(spec=OpenProjectClient): async methods are AsyncMock, so tests set
    `mock_client.get_work_package.return_value = {...}` or `.side_effect = ...`
    and assert with `mock_client.get_work_package.assert_awaited_once_with(...)`.
    Unknown method names raise AttributeError (spec). The original client is
    restored after the test.
    """
    client = MagicMock(spec=OpenProjectClient)
    client.base_url = TEST_BASE_URL
    client.api_key = "test-key"
    client.proxy = None
    client.headers = {}
    client.cache = TTLCache(ttl=0)
    monkeypatch.setattr(src.server, "_client", client)
    return client


@pytest.fixture(autouse=True)
def _clear_real_client_cache():
    """Isolate tests from the global client's dictionary cache."""
    yield
    real_client = getattr(src.server, "_client", None)
    if isinstance(real_client, OpenProjectClient):
        real_client.cache.clear()


async def invoke_tool(name: str, **kwargs: Any) -> Any:
    """Call a registered tool's Python function directly and return its raw result.

    Uses `(await mcp.get_tool(name)).fn(**kwargs)` - no MCP serialization and no
    argument validation; the return value is exactly what the tool returns
    (str, fastmcp Image, list...). Tools taking a pydantic model need the model
    instance, e.g. `invoke_tool("create_news", input=CreateNewsInput(...))`.
    """
    tool = await src.server.mcp.get_tool(name)
    return await tool.fn(**kwargs)


async def invoke_tool_mcp(name: str, arguments: Optional[Dict[str, Any]] = None):
    """Call a tool through the full MCP pipeline (fastmcp.Client(mcp)).

    Arguments are validated as JSON (pydantic models given as dicts). Returns
    fastmcp CallToolResult: `.data` (e.g. the returned str), `.content` (MCP
    content blocks, e.g. ImageContent), `.is_error`.
    """
    from fastmcp import Client

    async with Client(src.server.mcp) as client:
        return await client.call_tool(name, arguments or {}, raise_on_error=False)


@pytest.fixture
def call_tool() -> Callable[..., Any]:
    """Async helper: `result = await call_tool("get_work_package", work_package_id=1)`.

    See `invoke_tool` - returns the tool function's raw return value.
    """
    return invoke_tool


@pytest.fixture
def call_tool_mcp() -> Callable[..., Any]:
    """Async helper: `res = await call_tool_mcp("list_projects", {"active_only": True})`.

    See `invoke_tool_mcp` - returns fastmcp CallToolResult.
    """
    return invoke_tool_mcp
