"""Narzędzia odnajdywania pracy: moje zadania, zapisane widoki, powiadomienia."""

import json

import pytest

from src.client import OpenProjectAPIError


def sent_filters(mock_client):
    return json.loads(mock_client.get_work_packages.await_args.kwargs["filters"])


# --- list_my_work_packages ---------------------------------------------------


async def test_my_work_packages_default_open_assigned_to_me(mock_client, call_tool, load_fixture):
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    result = await call_tool("list_my_work_packages")

    assert sent_filters(mock_client) == [
        {"assignee": {"operator": "=", "values": ["me"]}},
        {"status": {"operator": "o", "values": []}},
    ]
    kwargs = mock_client.get_work_packages.await_args.kwargs
    assert kwargs["project_id"] is None
    assert kwargs["offset"] == 1 and kwargs["page_size"] == 20
    mock_client.get_current_user.assert_not_called()
    assert "#101" in result and "Poprawić eksport raportu" in result
    assert "In progress" in result and "High" in result and "2026-10-01" in result


async def test_my_work_packages_include_closed_and_project(mock_client, call_tool, load_fixture):
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    await call_tool("list_my_work_packages", project_id=21, include_closed=True, offset=2, page_size=5)

    assert sent_filters(mock_client)[1] == {"status": {"operator": "*", "values": []}}
    kwargs = mock_client.get_work_packages.await_args.kwargs
    assert (kwargs["project_id"], kwargs["offset"], kwargs["page_size"]) == (21, 2, 5)


async def test_my_work_packages_json_model(mock_client, call_tool, load_fixture):
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    data = json.loads(await call_tool("list_my_work_packages", page_size=2, format="json"))

    first, milestone = data["work_packages"]
    assert first == {
        "id": 101,
        "subject": "Poprawić eksport raportu",
        "status": "In progress",
        "type": "Task",
        "priority": "High",
        "assignee": "Kowalski Jan",
        "project": {"id": 21, "name": "Projekt Alfa"},
        "due_date": "2026-10-01",
        "percentage_done": 40,
    }
    assert milestone["due_date"] == "2026-10-15"
    assert milestone["assignee"] is None
    assert data["pagination"] == {
        "total": 3, "count": 2, "offset": 1, "page_size": 2, "next_offset": 2,
    }


async def test_my_work_packages_markdown_shows_next_page(mock_client, call_tool, load_fixture):
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    result = await call_tool("list_my_work_packages", page_size=2)

    assert "`offset=2`" in result


@pytest.mark.parametrize("kwargs", [{"offset": 0}, {"page_size": 0}, {"page_size": 101}, {"format": "xml"}])
async def test_my_work_packages_invalid_arguments(mock_client, call_tool, kwargs):
    result = await call_tool("list_my_work_packages", **kwargs)

    assert result.startswith("❌")
    mock_client.get_work_packages.assert_not_awaited()


async def test_my_work_packages_empty(mock_client, call_tool):
    mock_client.get_work_packages.return_value = {"_embedded": {"elements": []}, "total": 0}

    assert "brak zadań" in await call_tool("list_my_work_packages")


async def test_my_work_packages_api_error(mock_client, call_tool):
    mock_client.get_work_packages.side_effect = OpenProjectAPIError(403, '{"message": "Brak uprawnień."}')

    assert await call_tool("list_my_work_packages") == "❌ Błąd API 403: Brak uprawnień."


# --- list_queries / run_query --------------------------------------------------


async def test_list_queries_fields(mock_client, call_tool, load_fixture):
    mock_client.get_queries.return_value = load_fixture("disc_queries")

    result = await call_tool("list_queries", project_id=21)

    mock_client.get_queries.assert_awaited_once_with(21)
    assert "**Do testów** (ID: 2630)" in result
    assert "Projekt Alfa" in result and "⭐" in result and "publiczny" in result
    assert "Moje prywatne" in result and "globalny" in result and "prywatny" in result


async def test_list_queries_json(mock_client, call_tool, load_fixture):
    mock_client.get_queries.return_value = load_fixture("disc_queries")

    data = json.loads(await call_tool("list_queries", format="json"))

    mock_client.get_queries.assert_awaited_once_with(None)
    assert data["queries"] == [
        {"id": 2630, "name": "Do testów", "project": {"id": 21, "name": "Projekt Alfa"},
         "public": True, "starred": True},
        {"id": 17, "name": "Moje prywatne", "project": None, "public": False, "starred": False},
    ]


async def test_run_query_returns_view_results_and_passes_pagination(mock_client, call_tool, load_fixture):
    mock_client.get_query.return_value = load_fixture("disc_query_run")

    result = await call_tool("run_query", query_id=2630, offset=2, page_size=5)

    mock_client.get_query.assert_awaited_once_with(2630, offset=2, page_size=5)
    mock_client.get_work_packages.assert_not_called()
    assert "Do testów" in result and "(54)" in result
    assert "#77725" in result and "To test" in result
    assert "`offset=3`" in result


async def test_run_query_json(mock_client, call_tool, load_fixture):
    mock_client.get_query.return_value = load_fixture("disc_query_run")

    data = json.loads(await call_tool("run_query", query_id=2630, offset=2, page_size=5, format="json"))

    assert data["query"]["name"] == "Do testów"
    assert data["pagination"]["total"] == 54
    assert data["pagination"]["next_offset"] == 3
    assert [wp["id"] for wp in data["work_packages"]] == [77725]


async def test_run_query_not_found(mock_client, call_tool):
    mock_client.get_query.side_effect = OpenProjectAPIError(404, '{"message": "Nie znaleziono."}')

    assert "404" in await call_tool("run_query", query_id=999)


# --- list_notifications ------------------------------------------------------------


async def test_notifications_default_unread_only(mock_client, call_tool, load_fixture):
    mock_client.get_notifications.return_value = load_fixture("disc_notifications")

    await call_tool("list_notifications")

    mock_client.get_notifications.assert_awaited_once_with(
        unread_only=True, reason=None, offset=1, page_size=20
    )


async def test_notifications_reason_mentioned(mock_client, call_tool, load_fixture):
    mock_client.get_notifications.return_value = load_fixture("disc_notifications")

    result = await call_tool("list_notifications", reason="mentioned", offset=2, page_size=2)

    mock_client.get_notifications.assert_awaited_once_with(
        unread_only=True, reason="mentioned", offset=2, page_size=2
    )
    assert "mentioned" in result
    assert "#77725" in result and "Nowak Anna" in result and "Projekt Alfa" in result
    assert "2026-09-25T06:24:19.784Z" in result


async def test_notifications_json_model(mock_client, call_tool, load_fixture):
    mock_client.get_notifications.return_value = load_fixture("disc_notifications")

    data = json.loads(await call_tool("list_notifications", format="json"))

    wp_item, news_item = data["notifications"]
    assert wp_item == {
        "id": 1373805,
        "reason": "mentioned",
        "read": False,
        "created_at": "2026-09-25T06:24:19.784Z",
        "actor": "Nowak Anna",
        "work_package": {"id": 77725, "subject": "[Alfa] Dostosowanie do niestandardowego skalowania"},
        "resource": None,
        "project": {"id": 21, "name": "Projekt Alfa"},
    }
    assert news_item["work_package"] is None
    assert news_item["resource"]["title"] == "Nowa wersja systemu"
    assert data["pagination"]["total"] == 3


async def test_notifications_only_read_calls(mock_client, call_tool, load_fixture):
    mock_client.get_notifications.return_value = load_fixture("disc_notifications")

    await call_tool("list_notifications", unread_only=False)

    assert [c[0] for c in mock_client.method_calls] == ["get_notifications"]


async def test_notifications_invalid_reason(mock_client, call_tool):
    result = await call_tool("list_notifications", reason="spam")

    assert result.startswith("❌") and "mentioned" in result
    mock_client.get_notifications.assert_not_awaited()


# --- JSON przez pełny pipeline MCP -------------------------------------------------


@pytest.mark.parametrize(
    "tool, args, client_method, fixture",
    [
        ("list_my_work_packages", {}, "get_work_packages", "disc_work_packages"),
        ("list_queries", {}, "get_queries", "disc_queries"),
        ("run_query", {"query_id": 2630}, "get_query", "disc_query_run"),
        ("list_notifications", {}, "get_notifications", "disc_notifications"),
        ("get_version", {"version_id": 3236}, "get_version", "disc_version"),
        ("list_version_work_packages", {"version_id": 3236}, "get_work_packages", "disc_work_packages"),
    ],
)
async def test_read_tools_json_is_parseable_via_mcp(
    mock_client, call_tool_mcp, load_fixture, tool, args, client_method, fixture
):
    getattr(mock_client, client_method).return_value = load_fixture(fixture)
    mock_client.get_version.return_value = load_fixture("disc_version")

    response = await call_tool_mcp(tool, dict(args, format="json"))

    assert not response.is_error
    assert isinstance(json.loads(response.data), dict)
