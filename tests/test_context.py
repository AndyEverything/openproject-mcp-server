"""Tests for src.tools.context: get_work_package, get_work_package_context, get_allowed_statuses."""

import asyncio
import json

import pytest

from src.client import OpenProjectAPIError


@pytest.fixture
def wp_client(mock_client, load_fixture):
    mock_client.get_work_package.return_value = load_fixture("wp_basic")
    mock_client.get_work_package_schema.return_value = load_fixture("wp_schema")
    mock_client.get_work_package_activities.return_value = load_fixture("ctx_activities")
    mock_client.get_work_package_attachments.return_value = load_fixture("ctx_attachments")
    mock_client.list_work_package_relations.return_value = load_fixture("ctx_relations")
    mock_client.list_work_package_children.return_value = load_fixture("ctx_children")
    mock_client.get_work_package_form.return_value = load_fixture("ctx_form")
    return mock_client


# --- get_work_package ---


async def test_get_work_package_markdown(wp_client, call_tool):
    text = await call_tool("get_work_package", work_package_id=1234)

    wp_client.get_work_package.assert_awaited_once_with(1234)
    wp_client.get_work_package_schema.assert_awaited_once_with(118, 7)
    assert "#1234" in text
    assert "**Status:** Approved" in text
    assert "**Przypisany:** Jan Testowy" in text
    assert "**Rodzic:** #1200 Epik testowy" in text
    assert "**Kategoria (rozwój):** 06. Ulepszenie UI i UX" in text
    assert "customField40" not in text
    assert "![zrzut](/api/v3/attachments/42/content)" in text


async def test_get_work_package_skips_empty_fields(wp_client, call_tool):
    text = await call_tool("get_work_package", work_package_id=1234)

    assert "Odpowiedzialny" not in text
    assert "Wersja:" not in text
    assert "Termin:" not in text


async def test_get_work_package_long_description_is_complete(wp_client, call_tool, load_fixture):
    wp = load_fixture("wp_basic")
    description = "\n".join(f"Linia {i}: " + "treść " * 20 for i in range(60))
    assert len(description) > 5000
    wp["description"]["raw"] = description
    wp_client.get_work_package.return_value = wp

    text = await call_tool("get_work_package", work_package_id=1234)
    data = json.loads(await call_tool("get_work_package", work_package_id=1234, format="json"))

    assert description in text
    assert data["description"] == description


async def test_get_work_package_json(wp_client, call_tool):
    data = json.loads(await call_tool("get_work_package", work_package_id=1234, format="json"))

    assert data["id"] == 1234
    assert data["subject"]
    assert data["description"].startswith("# Opis")
    assert data["parent"] == {"id": 1200, "subject": "Epik testowy"}
    assert data["lock_version"] == 15
    assert data["url"].endswith("/work_packages/1234")
    fields = {item["name"]: item["value"] for item in data["custom_fields"]}
    assert fields["Kategoria (rozwój)"] == "06. Ulepszenie UI i UX"


async def test_get_work_package_not_found(mock_client, call_tool_mcp):
    mock_client.get_work_package.side_effect = OpenProjectAPIError(
        404, '{"message": "The requested resource could not be found."}'
    )

    result = await call_tool_mcp("get_work_package", {"work_package_id": 999999})

    assert not result.is_error
    assert result.data.startswith("❌")
    assert "404" in result.data
    mock_client.get_work_package_schema.assert_not_awaited()


async def test_get_work_package_schema_error_keeps_details(wp_client, call_tool):
    wp_client.get_work_package_schema.side_effect = OpenProjectAPIError(403, "")

    text = await call_tool("get_work_package", work_package_id=1234)
    data = json.loads(await call_tool("get_work_package", work_package_id=1234, format="json"))

    assert "Brak dostępu (403)" in text
    assert "# Opis" in text
    assert data["custom_fields"] == {"error": "Brak dostępu (403)", "status": 403}


async def test_get_work_package_invalid_format(mock_client, call_tool):
    text = await call_tool("get_work_package", work_package_id=1, format="xml")

    assert text.startswith("❌")
    mock_client.get_work_package.assert_not_awaited()


# --- get_work_package_context ---


async def test_context_full(wp_client, call_tool):
    text = await call_tool("get_work_package_context", work_package_id=1234)

    for heading in ("# 📋 Work Package #1234", "## 🏷️ Pola własne", "## 💬 Komentarze (2)",
                    "## 📎 Załączniki (2)", "## 🔗 Relacje (2)", "## 🌳 Hierarchia"):
        assert heading in text
    assert "> Komentarz wewnętrzny dla zespołu." in text
    assert "zrzut.png" in text
    assert "**blocks** → #1300 Zadanie blokowane" in text
    assert "**duplicated** → #1301 Duplikat zadania" in text
    assert "#1240 Podzadanie A" in text
    assert "**Rodzic:** #1200 Epik testowy" in text


async def test_context_json(wp_client, call_tool):
    data = json.loads(await call_tool("get_work_package_context", work_package_id=1234, format="json"))

    assert set(data) == {"details", "comments", "attachments", "relations", "hierarchy", "description_images"}
    assert data["details"]["id"] == 1234
    assert data["details"]["custom_fields"]
    assert [item["id"] for item in data["comments"]] == [1002, 1004]
    assert data["attachments"][0] == {
        "id": 42, "name": "zrzut.png", "content_type": "image/png", "size": 606425,
        "created_at": "2026-06-12T08:00:00.000Z",
    }
    assert data["relations"][1]["work_package"] == {"id": 1301, "subject": "Duplikat zadania"}
    assert data["hierarchy"]["parent"]["id"] == 1200
    assert [child["id"] for child in data["hierarchy"]["children"]] == [1240, 1241]
    wp_client.list_work_package_children.assert_awaited_once_with(1234)
    filters = json.loads(wp_client.list_work_package_relations.await_args.args[0])
    assert filters == [{"involved": {"operator": "=", "values": ["1234"]}}]


async def test_context_relations_403_does_not_break_other_sections(wp_client, call_tool):
    wp_client.list_work_package_relations.side_effect = OpenProjectAPIError(403, "")

    text = await call_tool("get_work_package_context", work_package_id=1234)
    data = json.loads(await call_tool("get_work_package_context", work_package_id=1234, format="json"))

    assert data["relations"] == {"error": "Brak dostępu (403)", "status": 403}
    assert len(data["comments"]) == 2
    assert len(data["attachments"]) == 2
    assert data["details"]["custom_fields"]
    assert "## 🔗 Relacje\n⚠️ Brak dostępu (403)" in text


async def test_context_description_images(wp_client, call_tool):
    text = await call_tool("get_work_package_context", work_package_id=1234)
    data = json.loads(await call_tool("get_work_package_context", work_package_id=1234, format="json"))

    assert data["description_images"]["attachment_ids"] == [42]
    assert "get_attachment" in data["description_images"]["hint"]
    assert "## 🖼️ Obrazy w opisie (1)" in text
    assert "#42" in text and "get_attachment" in text


@pytest.mark.parametrize(
    "flag, method, key",
    [
        ("include_comments", "get_work_package_activities", "comments"),
        ("include_attachments", "get_work_package_attachments", "attachments"),
        ("include_relations", "list_work_package_relations", "relations"),
        ("include_hierarchy", "list_work_package_children", "hierarchy"),
    ],
)
async def test_context_disabled_section_does_not_call_api(wp_client, call_tool, flag, method, key):
    data = json.loads(
        await call_tool("get_work_package_context", work_package_id=1234, format="json", **{flag: False})
    )

    getattr(wp_client, method).assert_not_awaited()
    assert key not in data
    assert "details" in data


async def test_context_work_package_error_is_tool_error(mock_client, call_tool):
    mock_client.get_work_package.side_effect = OpenProjectAPIError(404, "")

    text = await call_tool("get_work_package_context", work_package_id=5)

    assert text.startswith("❌") and "404" in text
    mock_client.get_work_package_activities.assert_not_awaited()


async def test_context_children_error_keeps_parent(wp_client, call_tool):
    wp_client.list_work_package_children.side_effect = RuntimeError("timeout")

    data = json.loads(await call_tool("get_work_package_context", work_package_id=1234, format="json"))

    assert data["hierarchy"]["parent"]["id"] == 1200
    assert data["hierarchy"]["children"] == {"error": "timeout", "status": None}


# --- get_allowed_statuses ---


async def test_allowed_statuses(wp_client, call_tool):
    text = await call_tool("get_allowed_statuses", work_package_id=1234)

    wp_client.get_work_package_form.assert_awaited_once_with(1234, 15)
    wp_client.update_work_package.assert_not_awaited()
    assert "**Approved** (ID 2) ← bieżący" in text
    assert "**In progress** (ID 7)" in text
    assert "**Closed** (ID 12)" in text


async def test_allowed_statuses_json(wp_client, call_tool):
    data = json.loads(await call_tool("get_allowed_statuses", work_package_id=1234, format="json"))

    assert data["lock_version"] == 15
    assert data["current_status"] == {"id": 2, "name": "Approved"}
    assert data["allowed_statuses"] == [
        {"id": 2, "name": "Approved", "current": True},
        {"id": 7, "name": "In progress", "current": False},
        {"id": 12, "name": "Closed", "current": False},
    ]


async def test_allowed_statuses_form_error(wp_client, call_tool):
    wp_client.get_work_package_form.side_effect = OpenProjectAPIError(403, "")

    text = await call_tool("get_allowed_statuses", work_package_id=1234)

    assert text.startswith("❌") and "403" in text
    wp_client.update_work_package.assert_not_awaited()


async def test_context_propagates_cancellation(wp_client, call_tool):
    wp_client.list_work_package_relations.side_effect = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await call_tool("get_work_package_context", work_package_id=1234)
