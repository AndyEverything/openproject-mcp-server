"""Tests for list_work_package_code_links (src.tools.integrations)."""

import asyncio
import json

import pytest

from src.client import OpenProjectAPIError

WP_ID = 1234

COLLECTION_FIXTURES = {
    "github_pull_requests": "int_github_pull_requests",
    "gitlab_merge_requests": "int_gitlab_merge_requests",
    "gitlab_issues": "int_gitlab_issues",
    "file_links": "int_file_links",
}


def _forbidden(load_fixture) -> OpenProjectAPIError:
    return OpenProjectAPIError(403, json.dumps(load_fixture("int_error_403")))


def _collections(load_fixture, overrides=None):
    """side_effect for get_work_package_link_collection: path -> fixture or exception."""
    overrides = overrides or {}

    async def fetch(work_package_id, path):
        assert work_package_id == WP_ID
        outcome = overrides.get(path, COLLECTION_FIXTURES[path])
        if isinstance(outcome, BaseException):
            raise outcome
        return load_fixture(outcome)

    return fetch


def _section(markdown: str, heading: str) -> str:
    return markdown.split(f"## {heading}")[1].split("\n## ")[0]


@pytest.fixture
def wp(load_fixture):
    data = load_fixture("wp_basic")
    data["id"] = WP_ID
    return data


async def test_gitlab_merge_request_listed_with_title_state_and_url(
    mock_client, call_tool, load_fixture, wp
):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(load_fixture)

    result = await call_tool("list_work_package_code_links", work_package_id=WP_ID)

    gitlab_section = _section(result, "GitLab – merge requesty")
    assert "Poprawka walidacji formularza" in gitlab_section
    assert "stan: merged" in gitlab_section
    assert "https://gitlab.example.test/team/app/-/merge_requests/7" in gitlab_section
    assert "## GitHub – pull requesty (1)" in result
    assert "https://github.com/example/app/pull/42" in result
    assert "## GitLab – issues (1)" in result
    assert "specyfikacja.pdf" in result
    assert "https://op.example.test/api/v3/file_links/1337/open" in result
    assert mock_client.get_work_package_link_collection.await_count == 4


async def test_github_403_marks_source_unavailable_and_keeps_others(
    mock_client, call_tool, load_fixture, wp
):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(
        load_fixture, {"github_pull_requests": _forbidden(load_fixture)}
    )

    result = await call_tool("list_work_package_code_links", work_package_id=WP_ID)

    github_section = _section(result, "GitHub – pull requesty")
    assert "niedostępne" in github_section
    assert "403" in github_section
    assert "## GitLab – merge requesty (1)" in result
    assert "Poprawka walidacji formularza" in result


@pytest.mark.parametrize("status", [403, 404])
async def test_403_and_404_are_unavailable_in_json(
    mock_client, call_tool, load_fixture, wp, status
):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(
        load_fixture, {"gitlab_issues": OpenProjectAPIError(status, "")}
    )

    data = json.loads(
        await call_tool("list_work_package_code_links", work_package_id=WP_ID, format="json")
    )

    assert data["sources"]["gitlab_issues"]["available"] is False
    assert data["sources"]["gitlab_issues"]["status"] == status
    assert data["sources"]["gitlab_merge_requests"]["available"] is True


async def test_missing_link_skips_request_for_that_source(
    mock_client, call_tool, load_fixture, wp
):
    del wp["_links"]["github_pull_requests"]
    wp["_links"]["gitlab_issues"] = {"href": None}
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(load_fixture)

    data = json.loads(
        await call_tool("list_work_package_code_links", work_package_id=WP_ID, format="json")
    )

    requested = {c.args[1] for c in mock_client.get_work_package_link_collection.await_args_list}
    assert requested == {"gitlab_merge_requests", "file_links"}
    assert data["sources"]["github_pull_requests"]["available"] is False
    assert data["sources"]["gitlab_issues"]["available"] is False
    assert data["sources"]["file_links"]["count"] == 1


async def test_other_error_is_reported_in_section(mock_client, call_tool, load_fixture, wp):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(
        load_fixture,
        {"file_links": OpenProjectAPIError(500, json.dumps({"message": "Internal error"}))},
    )

    result = await call_tool("list_work_package_code_links", work_package_id=WP_ID)

    files_section = _section(result, "Pliki powiązane (file links)")
    assert "Błąd API 500: Internal error" in files_section
    assert "## GitHub – pull requesty (1)" in result


async def test_work_package_fetch_error_returns_message(mock_client, call_tool):
    mock_client.get_work_package.side_effect = OpenProjectAPIError(
        404, json.dumps({"message": "Zasób nie istnieje."})
    )

    result = await call_tool("list_work_package_code_links", work_package_id=WP_ID)

    assert result.startswith("❌")
    assert "404" in result
    mock_client.get_work_package_link_collection.assert_not_awaited()


async def test_json_is_parseable_with_common_item_model(
    mock_client, call_tool_mcp, load_fixture, wp
):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(load_fixture)

    res = await call_tool_mcp(
        "list_work_package_code_links", {"work_package_id": WP_ID, "format": "json"}
    )

    assert not res.is_error
    data = json.loads(res.data)
    assert data["id"] == WP_ID
    assert set(data["sources"]) == set(COLLECTION_FIXTURES)
    pr = data["sources"]["github_pull_requests"]["items"][0]
    assert pr["title"] == "Obsługa eksportu raportu"
    assert pr["state"] == "open"
    assert pr["url"] == "https://github.com/example/app/pull/42"
    assert pr["number"] == 42
    assert pr["repository"] == "example/app"
    assert pr["author"] == "jan-kowalski"
    file_item = data["sources"]["file_links"]["items"][0]
    assert file_item["storage"] == "Nextcloud"
    assert file_item["mime"] == "application/pdf"


async def test_empty_collection_shows_no_links(mock_client, call_tool, wp):
    mock_client.get_work_package.return_value = wp

    async def fetch(work_package_id, path):
        return {"_type": "Collection", "total": 0, "_embedded": {"elements": []}}

    mock_client.get_work_package_link_collection.side_effect = fetch

    result = await call_tool("list_work_package_code_links", work_package_id=WP_ID)

    assert "## Pliki powiązane (file links) (0)" in result
    assert "_Brak powiązań._" in result


async def test_code_links_propagate_cancellation(mock_client, call_tool, load_fixture, wp):
    mock_client.get_work_package.return_value = wp
    mock_client.get_work_package_link_collection.side_effect = _collections(
        load_fixture, {"gitlab_issues": asyncio.CancelledError()}
    )

    with pytest.raises(asyncio.CancelledError):
        await call_tool("list_work_package_code_links", work_package_id=WP_ID)
