"""Tests for src.tools.watchers."""

import json

from src.client import OpenProjectAPIError


async def test_list_watchers(mock_client, call_tool, load_fixture):
    mock_client.get_watchers.return_value = load_fixture("ctx_watchers")

    text = await call_tool("list_watchers", work_package_id=1234)

    mock_client.get_watchers.assert_awaited_once_with(1234)
    assert "(3)" in text
    for name, user_id in (("Jan Testowy", 304), ("Anna Przykładowa", 305), ("Piotr Próbny", 306)):
        assert f"**{name}** (ID {user_id})" in text


async def test_list_watchers_json(mock_client, call_tool, load_fixture):
    mock_client.get_watchers.return_value = load_fixture("ctx_watchers")

    data = json.loads(await call_tool("list_watchers", work_package_id=1234, format="json"))

    assert data["work_package_id"] == 1234
    assert [(user["id"], user["name"]) for user in data["watchers"]] == [
        (304, "Jan Testowy"), (305, "Anna Przykładowa"), (306, "Piotr Próbny"),
    ]


async def test_list_watchers_empty(mock_client, call_tool):
    mock_client.get_watchers.return_value = {"_embedded": {"elements": []}}

    assert "no watchers" in await call_tool("list_watchers", work_package_id=1)


async def test_list_watchers_error(mock_client, call_tool):
    mock_client.get_watchers.side_effect = OpenProjectAPIError(403, "")

    text = await call_tool("list_watchers", work_package_id=1)

    assert text.startswith("❌") and "403" in text


async def test_add_watcher(mock_client, call_tool):
    mock_client.add_watcher.return_value = {"_type": "User", "id": 304}

    text = await call_tool("add_watcher", work_package_id=1234, user_id=304)

    mock_client.add_watcher.assert_awaited_once_with(1234, 304)
    assert text.startswith("✅")


async def test_remove_watcher(mock_client, call_tool):
    mock_client.remove_watcher.return_value = True

    text = await call_tool("remove_watcher", work_package_id=1234, user_id=304)

    mock_client.remove_watcher.assert_awaited_once_with(1234, 304)
    assert text.startswith("✅")


async def test_add_watcher_error(mock_client, call_tool):
    mock_client.add_watcher.side_effect = OpenProjectAPIError(422, '{"message": "User is invalid"}')

    text = await call_tool("add_watcher", work_package_id=1234, user_id=1)

    assert text == "❌ Błąd API 422: User is invalid"
