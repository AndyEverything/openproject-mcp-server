"""Filtry wysyłane przez list_work_packages / search_work_packages (zgodność wstecz + nowe parametry)."""

import json

import pytest

EMPTY_RESULT = {"_embedded": {"elements": []}, "total": 0}


def sent_filters(mock_client):
    kwargs = mock_client.get_work_packages.await_args.kwargs
    return json.loads(kwargs["filters"]) if kwargs["filters"] else None


@pytest.fixture
def wp_client(mock_client):
    mock_client.get_work_packages.return_value = dict(EMPTY_RESULT)
    return mock_client


# Oczekiwania spisane z kodu sprzed zmiany (fala 1B) - stare wywołania muszą dawać te same filtry.
LEGACY_CASES = [
    ({}, [{"status": {"operator": "o", "values": []}}]),
    ({"active_only": False}, [{"status": {"operator": "*", "values": []}}]),
    (
        {"project_id": 5, "assignee_id": 7},
        [
            {"status": {"operator": "o", "values": []}},
            {"assignee": {"operator": "=", "values": ["7"]}},
        ],
    ),
    (
        {"assignee_id": 7, "unassigned_only": True},
        [
            {"status": {"operator": "o", "values": []}},
            {"assignee": {"operator": "!*", "values": []}},
        ],
    ),
    (
        {"status_ids": "1, 2", "priority_ids": "3", "type_ids": "1,2", "version_ids": "9"},
        [
            {"status": {"operator": "=", "values": ["1", "2"]}},
            {"priority": {"operator": "=", "values": ["3"]}},
            {"type": {"operator": "=", "values": ["1", "2"]}},
            {"version": {"operator": "=", "values": ["9"]}},
        ],
    ),
    (
        {"due_after": "2026-01-01", "due_before": "2026-02-01", "author_id": 3, "parent_id": 11},
        [
            {"status": {"operator": "o", "values": []}},
            {"dueDate": {"operator": "<>d", "values": ["2026-01-01", "2026-02-01"]}},
            {"author": {"operator": "=", "values": ["3"]}},
            {"parent": {"operator": "=", "values": ["11"]}},
        ],
    ),
    (
        {"percentage_done_min": 10, "percentage_done_max": 90, "no_parent_only": True},
        [
            {"status": {"operator": "o", "values": []}},
            {"percentageDone": {"operator": ">=", "values": ["10"]}},
            {"percentageDone": {"operator": "<=", "values": ["90"]}},
            {"parent": {"operator": "!*", "values": []}},
        ],
    ),
]


@pytest.mark.parametrize("kwargs, expected", LEGACY_CASES)
async def test_list_work_packages_legacy_calls_send_same_filters(wp_client, call_tool, kwargs, expected):
    await call_tool("list_work_packages", **kwargs)

    assert sent_filters(wp_client) == expected
    call = wp_client.get_work_packages.await_args.kwargs
    assert call["project_id"] == kwargs.get("project_id")
    assert call["offset"] == 0
    assert call["page_size"] == 20


async def test_list_work_packages_assigned_to_me_adds_me_filter(wp_client, call_tool):
    await call_tool("list_work_packages", assigned_to_me=True)

    assert sent_filters(wp_client) == [
        {"status": {"operator": "o", "values": []}},
        {"assignee": {"operator": "=", "values": ["me"]}},
    ]


async def test_list_work_packages_assigned_to_me_conflicts_with_assignee_id(wp_client, call_tool):
    result = await call_tool("list_work_packages", assigned_to_me=True, assignee_id=7)

    assert result.startswith("❌")
    assert "assigned_to_me" in result and "assignee_id" in result
    wp_client.get_work_packages.assert_not_awaited()


async def test_list_work_packages_assigned_to_me_conflicts_with_unassigned_only(wp_client, call_tool):
    result = await call_tool("list_work_packages", assigned_to_me=True, unassigned_only=True)

    assert result.startswith("❌")
    wp_client.get_work_packages.assert_not_awaited()


async def test_search_default_uses_subject_or_id_filter(wp_client, call_tool):
    await call_tool("search_work_packages", query="  login ")

    assert sent_filters(wp_client) == [
        {"subjectOrId": {"operator": "**", "values": ["login"]}},
        {"status": {"operator": "o", "values": []}},
    ]


async def test_search_default_all_statuses_unchanged(wp_client, call_tool):
    await call_tool("search_work_packages", query="123", active_only=False, project_id=4)

    assert sent_filters(wp_client) == [
        {"subjectOrId": {"operator": "**", "values": ["123"]}},
        {"status": {"operator": "*", "values": []}},
    ]
    assert wp_client.get_work_packages.await_args.kwargs["project_id"] == 4


async def test_search_full_text_uses_search_filter(wp_client, call_tool):
    await call_tool("search_work_packages", query="fraza z opisu", full_text=True)

    assert sent_filters(wp_client) == [
        {"search": {"operator": "**", "values": ["fraza z opisu"]}},
        {"status": {"operator": "o", "values": []}},
    ]


async def test_search_full_text_returns_match_found_only_in_description(wp_client, call_tool):
    wp_client.get_work_packages.return_value = {
        "_embedded": {
            "elements": [
                {
                    "id": 42,
                    "subject": "Zadanie bez frazy w temacie",
                    "description": {"raw": "Tu jest unikalna fraza"},
                    "_links": {"status": {"title": "New"}},
                }
            ]
        },
        "total": 1,
    }

    result = await call_tool("search_work_packages", query="unikalna fraza", full_text=True)

    assert "#42" in result
    assert "full-text" in result
