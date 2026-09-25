"""Smoke tests for server initialization and the shared test helpers."""

from src.client import OpenProjectAPIError


def test_server_imports():
    import src.server

    assert src.server.mcp is not None
    assert src.server.get_client() is not None


async def test_call_tool_uses_mock_client(mock_client, call_tool):
    mock_client.get_statuses.return_value = {
        "_embedded": {"elements": [{"id": 1, "name": "Nowy", "isClosed": False}]}
    }

    result = await call_tool("list_statuses")

    assert "Nowy" in result
    mock_client.get_statuses.assert_awaited_once_with()


async def test_call_tool_mcp_returns_tool_result(mock_client, call_tool_mcp):
    mock_client.delete_work_package.side_effect = OpenProjectAPIError(404, "not found")

    result = await call_tool_mcp("delete_work_package", {"work_package_id": 5})

    assert "API Error 404" in result.data


NEW_AGENT_TOOLS = {
    "get_work_package",
    "get_work_package_context",
    "get_allowed_statuses",
    "list_watchers",
    "add_watcher",
    "remove_watcher",
    "list_work_package_attachments",
    "get_attachment",
    "upload_attachment",
    "list_my_work_packages",
    "list_queries",
    "run_query",
    "list_notifications",
    "get_version",
    "list_version_work_packages",
    "update_version",
    "list_work_package_code_links",
}

MINIMAL_CONFIG_SCRIPT = (
    "import asyncio, json, logging\n"
    "logging.disable(logging.CRITICAL)\n"
    "from src.server import mcp\n"
    "async def main():\n"
    "    return {\n"
    "        'tools': sorted((await mcp.get_tools()).keys()),\n"
    "        'templates': sorted((await mcp.get_resource_templates()).keys()),\n"
    "        'prompts': sorted((await mcp.get_prompts()).keys()),\n"
    "    }\n"
    "print(json.dumps(asyncio.run(main())))\n"
)


def test_minimal_config_registers_all_tools():
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    # Tylko wymagane zmienne – żadnych opcjonalnych OPENPROJECT_* z otoczenia
    env = {k: v for k, v in os.environ.items() if not k.startswith("OPENPROJECT_")}
    env.update(
        {
            "OPENPROJECT_URL": "https://op.example.test",
            "OPENPROJECT_API_KEY": "test-key",
            "PYTHONPATH": str(repo_root),
        }
    )
    completed = subprocess.run(
        [sys.executable, "-c", MINIMAL_CONFIG_SCRIPT],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    registered = json.loads(completed.stdout.strip().splitlines()[-1])

    tools = set(registered["tools"])
    assert NEW_AGENT_TOOLS <= tools
    assert {"list_projects", "create_work_package", "delete_project", "list_work_package_activities"} <= tools
    assert "openproject://work-packages/{work_package_id}" in registered["templates"]
    assert {"plan_work_package", "summarize_work_package"} <= set(registered["prompts"])
