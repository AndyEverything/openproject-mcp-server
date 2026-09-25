"""Narzędzia wersji: get_version, list_version_work_packages, update_version."""

import json

import pytest

import src.server
from src.client import OpenProjectAPIError
from src.utils.safety import WRITE_TOOLS


async def call_update_version(**kwargs):
    # call_tool ma własny parametr `name`, który koliduje z polem `name` wersji
    tool = await src.server.mcp.get_tool("update_version")
    return await tool.fn(**kwargs)


async def test_get_version_details(mock_client, call_tool, load_fixture):
    mock_client.get_version.return_value = load_fixture("disc_version")

    result = await call_tool("get_version", version_id=3236)

    mock_client.get_version.assert_awaited_once_with(3236)
    for expected in ("Sprint 42", "open", "2026-09-01", "2026-09-14", "system",
                     "Projekt Alfa", "Cel sprintu: **eksport**"):
        assert expected in result


async def test_get_version_json(mock_client, call_tool, load_fixture):
    mock_client.get_version.return_value = load_fixture("disc_version")

    data = json.loads(await call_tool("get_version", version_id=3236, format="json"))

    assert data == {
        "id": 3236,
        "name": "Sprint 42",
        "description": "Cel sprintu: **eksport**",
        "status": "open",
        "start_date": "2026-09-01",
        "end_date": "2026-09-14",
        "sharing": "system",
        "project": {"id": 21, "name": "Projekt Alfa"},
    }


async def test_get_version_not_found(mock_client, call_tool):
    mock_client.get_version.side_effect = OpenProjectAPIError(404, '{"message": "Nie ma."}')

    assert await call_tool("get_version", version_id=1) == "❌ Błąd API 404: Nie ma."


async def test_version_work_packages_default_all_statuses(mock_client, call_tool, load_fixture):
    mock_client.get_version.return_value = load_fixture("disc_version")
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    result = await call_tool("list_version_work_packages", version_id=3236)

    kwargs = mock_client.get_work_packages.await_args.kwargs
    assert json.loads(kwargs["filters"]) == [
        {"version": {"operator": "=", "values": ["3236"]}},
        {"status": {"operator": "*", "values": []}},
    ]
    assert kwargs["offset"] == 1 and kwargs["page_size"] == 20
    assert kwargs["project_id"] == 21
    assert "#101" in result and "In progress" in result and "#102" in result and "New" in result


async def test_version_work_packages_open_only_and_pagination(mock_client, call_tool, load_fixture):
    mock_client.get_version.return_value = load_fixture("disc_version")
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    await call_tool("list_version_work_packages", version_id=3236, include_closed=False, offset=3, page_size=50)

    kwargs = mock_client.get_work_packages.await_args.kwargs
    assert json.loads(kwargs["filters"])[1] == {"status": {"operator": "o", "values": []}}
    assert (kwargs["offset"], kwargs["page_size"]) == (3, 50)


async def test_version_work_packages_version_not_found(mock_client, call_tool):
    mock_client.get_version.side_effect = OpenProjectAPIError(404, '{"message": "Nie ma."}')

    assert await call_tool("list_version_work_packages", version_id=1) == "❌ Błąd API 404: Nie ma."
    mock_client.get_work_packages.assert_not_awaited()


def test_update_version_is_write_tool():
    assert "update_version" in WRITE_TOOLS


async def test_update_version_sends_only_given_fields(mock_client, call_tool, load_fixture):
    mock_client.update_version.return_value = load_fixture("disc_version")

    result = await call_tool("update_version", version_id=3236, description="Nowy cel", status="locked")

    mock_client.update_version.assert_awaited_once_with(
        3236, {"description": {"raw": "Nowy cel"}, "status": "locked"}
    )
    assert result.startswith("✅")


async def test_update_version_all_fields(mock_client, call_tool, load_fixture):
    mock_client.update_version.return_value = load_fixture("disc_version")

    await call_update_version(
        version_id=3236, name="Sprint 43", description="", status="closed",
        start_date="2026-09-15", end_date="2026-09-28", sharing="none",
    )

    mock_client.update_version.assert_awaited_once_with(
        3236,
        {
            "name": "Sprint 43",
            "description": {"raw": ""},
            "status": "closed",
            "startDate": "2026-09-15",
            "endDate": "2026-09-28",
            "sharing": "none",
        },
    )


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"status": "archived"}, {"sharing": "everyone"}, {"name": "  "}],
)
async def test_update_version_validation(mock_client, call_tool, kwargs):
    result = await call_update_version(version_id=3236, **kwargs)

    assert result.startswith("❌")
    mock_client.update_version.assert_not_awaited()


async def test_update_version_api_error(mock_client, call_tool):
    mock_client.update_version.side_effect = OpenProjectAPIError(422, '{"message": "Data końca przed startem."}')

    result = await call_tool("update_version", version_id=3236, end_date="2020-01-01")

    assert result == "❌ Błąd API 422: Data końca przed startem."


async def test_version_work_packages_warns_when_version_is_shared(mock_client, call_tool, load_fixture):
    version = load_fixture("disc_version")
    version["sharing"] = "system"
    mock_client.get_version.return_value = version
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    result = await call_tool("list_version_work_packages", version_id=3236, format="json")

    assert "system" in json.loads(result)["scope_note"]


@pytest.mark.parametrize("sharing", ["none", "descendants"])
async def test_version_work_packages_no_warning_when_scope_is_complete(
    mock_client, call_tool, load_fixture, sharing
):
    version = load_fixture("disc_version")
    version["sharing"] = sharing
    mock_client.get_version.return_value = version
    mock_client.get_work_packages.return_value = load_fixture("disc_work_packages")

    result = await call_tool("list_version_work_packages", version_id=3236, format="json")

    assert "scope_note" not in json.loads(result)
