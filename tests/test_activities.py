"""Tests for src.utils.activities and the list_work_package_activities tool."""

import pytest

from src.client import OpenProjectAPIError
from src.utils.activities import activities_to_markdown, build_activities, strip_emphasis


def _collection(*elements):
    return {"_embedded": {"elements": list(elements)}}


def _activity(activity_id=1, comment="", details=(), user=None, internal=False):
    return {
        "id": activity_id,
        "createdAt": "2026-08-01T10:00:00.000Z",
        "comment": {"format": "markdown", "raw": comment, "html": ""},
        "details": [{"format": "custom", "raw": raw, "html": ""} for raw in details],
        "internal": internal,
        "_links": {"user": user or {"href": "/api/v3/users/304", "title": "Jan Testowy"}},
    }


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("**Status** changed from *New* to *In progress*", "Status changed from New to In progress"),
        ("__Typ__ set to _Feature_", "Typ set to Feature"),
        ("Opis changed (/journals/1362675/diff/description)", "Opis changed (/journals/1362675/diff/description)"),
        ("Pole custom_field_name set to 2*3", "Pole custom_field_name set to 2*3"),
    ],
)
def test_strip_emphasis(raw, expected):
    assert strip_emphasis(raw) == expected


def test_build_activities_maps_fixture(load_fixture):
    activities = build_activities(load_fixture("ctx_activities"))

    assert [item["id"] for item in activities] == [1001, 1002, 1003, 1004, 1005]
    status_change = activities[2]
    assert status_change["changes"][0] == "Status changed from New to In progress"
    assert len(status_change["changes"]) == 4
    assert activities[1]["comment"] == "Pierwszy komentarz.\n\nDruga linia z **pogrubieniem**."
    assert activities[1]["user"] == "Jan Testowy"
    assert activities[1]["user_id"] == 304


def test_user_without_title_is_shown_by_id(load_fixture):
    internal = build_activities(load_fixture("ctx_activities"))[3]

    assert internal["user"] == "Użytkownik #93"
    assert internal["internal"] is True


def test_comments_only_skips_entries_without_comment(load_fixture):
    activities = build_activities(load_fixture("ctx_activities"), comments_only=True)

    assert [item["id"] for item in activities] == [1002, 1004]


def test_long_comment_is_not_truncated():
    comment = "A" * 1000 + " " + "B" * 999
    activities = build_activities(_collection(_activity(comment=comment)))

    assert activities[0]["comment"] == comment
    assert comment in activities_to_markdown(activities)


def test_markdown_contains_all_changes_and_internal_marker(load_fixture):
    text = activities_to_markdown(build_activities(load_fixture("ctx_activities")))

    assert "Status changed from New to In progress" in text
    assert "Termin set to 2026-09-30" in text
    assert "🔒 Komentarz wewnętrzny" in text
    assert "> Druga linia z **pogrubieniem**." in text


def test_empty_collection():
    assert build_activities({}) == []
    assert activities_to_markdown([]) == "Brak aktywności."


# --- narzędzie list_work_package_activities ---


async def test_tool_without_new_parameters(mock_client, call_tool, load_fixture):
    mock_client.get_work_package_activities.return_value = load_fixture("ctx_activities")

    text = await call_tool("list_work_package_activities", work_package_id=1234)

    mock_client.get_work_package_activities.assert_awaited_once_with(1234)
    assert text.startswith("✅ Work Package #1234 Activities (5):")
    assert "Status changed from New to In progress" in text
    assert "Priorytet changed from Normal to High" in text


async def test_tool_through_mcp_without_new_parameters(mock_client, call_tool_mcp, load_fixture):
    mock_client.get_work_package_activities.return_value = load_fixture("ctx_activities")

    result = await call_tool_mcp("list_work_package_activities", {"work_package_id": 1234})

    assert not result.is_error
    assert "Activities (5)" in result.data


async def test_tool_full_long_comment(mock_client, call_tool):
    comment = "x" * 2000
    mock_client.get_work_package_activities.return_value = _collection(_activity(comment=comment))

    text = await call_tool("list_work_package_activities", work_package_id=1)

    assert comment in text


async def test_tool_comments_only(mock_client, call_tool, load_fixture):
    mock_client.get_work_package_activities.return_value = load_fixture("ctx_activities")

    text = await call_tool("list_work_package_activities", work_package_id=1234, comments_only=True)

    assert "Comments (2)" in text
    assert "Activity #1003" not in text
    assert "Activity #1002" in text


async def test_tool_api_error(mock_client, call_tool):
    mock_client.get_work_package_activities.side_effect = OpenProjectAPIError(404, '{"message": "Not found"}')

    text = await call_tool("list_work_package_activities", work_package_id=9)

    assert "404" in text and text.startswith("❌")
