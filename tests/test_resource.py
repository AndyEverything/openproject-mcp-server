"""Tests for the openproject://work-packages/{id} MCP resource."""

from fastmcp import Client

import src.server
from src.client import OpenProjectAPIError


async def _read(uri: str) -> str:
    async with Client(src.server.mcp) as client:
        contents = await client.read_resource(uri)
    return contents[0].text


async def test_resource_template_is_registered():
    templates = await src.server.mcp.get_resource_templates()

    assert "openproject://work-packages/{work_package_id}" in templates


async def test_read_resource_returns_context_markdown(mock_client, load_fixture):
    wp = load_fixture("wp_basic")
    wp["id"] = 123
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_schema.return_value = load_fixture("wp_schema")
    mock_client.get_work_package_activities.return_value = load_fixture("ctx_activities")
    mock_client.get_work_package_attachments.return_value = load_fixture("ctx_attachments")
    mock_client.list_work_package_relations.return_value = load_fixture("ctx_relations")
    mock_client.list_work_package_children.return_value = load_fixture("ctx_children")

    text = await _read("openproject://work-packages/123")

    mock_client.get_work_package.assert_awaited_once_with(123)
    assert "#123" in text
    assert "## 💬 Komentarze" in text
    assert "## 🌳 Hierarchia" in text


async def test_read_resource_not_found(mock_client):
    mock_client.get_work_package.side_effect = OpenProjectAPIError(404, "")

    text = await _read("openproject://work-packages/5")

    assert text.startswith("❌") and "404" in text
