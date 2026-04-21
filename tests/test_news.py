"""Tests for src/tools/news.py — proper pytest rewrite of test_news_tools.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.news import (
    CreateNewsInput,
    UpdateNewsInput,
    create_news,
    delete_news,
    get_news,
    list_news,
    update_news,
)
from src.utils.formatting import format_news_detail, format_news_list

_NEWS_ITEM = {
    "id": 1,
    "title": "Sprint Review",
    "summary": "Completed user stories",
    "createdAt": "2025-03-15T10:00:00.000Z",
    "_links": {
        "project": {"title": "Alpha"},
        "author": {"title": "Alice"},
    },
}

_NEWS_DETAIL = {
    "id": 5,
    "title": "Release Notes",
    "summary": "Version 1.0 shipped",
    "description": {"raw": "# v1.0\n\nAll features complete."},
    "createdAt": "2025-03-20T09:00:00.000Z",
    "_links": {
        "self": {"href": "/api/v3/news/5"},
        "project": {"href": "/api/v3/projects/1", "title": "Alpha"},
        "author": {"href": "/api/v3/users/2", "title": "Alice"},
    },
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_news_input_valid():
    inp = CreateNewsInput(
        project_id=1, title="Test News",
        summary="Short summary", description="# Content"
    )
    assert inp.project_id == 1
    assert inp.title == "Test News"


def test_create_news_input_missing_summary():
    with pytest.raises(ValidationError):
        CreateNewsInput(project_id=1, title="Test", description="Content")


def test_create_news_input_title_too_long():
    with pytest.raises(ValidationError):
        CreateNewsInput(
            project_id=1, title="A" * 256,
            summary="S", description="D"
        )


def test_create_news_input_invalid_project_id():
    with pytest.raises(ValidationError):
        CreateNewsInput(project_id=0, title="T", summary="S", description="D")


def test_update_news_input_valid_partial():
    inp = UpdateNewsInput(news_id=5, title="New Title")
    assert inp.news_id == 5
    assert inp.summary is None


def test_update_news_input_description_only():
    inp = UpdateNewsInput(news_id=10, description="New desc")
    assert inp.title is None
    assert inp.description == "New desc"


# ---------------------------------------------------------------------------
# Formatting utilities
# ---------------------------------------------------------------------------

def test_format_news_list_empty():
    result = format_news_list([])
    assert "No news entries found" in result


def test_format_news_list_single_item():
    result = format_news_list([_NEWS_ITEM])
    assert "Sprint Review" in result
    assert "Alpha" in result
    assert "Alice" in result
    assert "2025-03-15" in result


def test_format_news_list_multiple_items():
    items = [
        dict(_NEWS_ITEM, id=1, title="News 1"),
        dict(_NEWS_ITEM, id=2, title="News 2"),
    ]
    result = format_news_list(items)
    assert "2 items" in result or "News 1" in result
    assert "News 2" in result


def test_format_news_list_long_summary_truncated():
    item = dict(_NEWS_ITEM, summary="X" * 200)
    result = format_news_list([item])
    assert "..." in result


def test_format_news_detail():
    result = format_news_detail(_NEWS_DETAIL)
    assert "Release Notes" in result
    assert "Alpha" in result
    assert "Alice" in result
    assert "v1.0" in result


# ---------------------------------------------------------------------------
# list_news
# ---------------------------------------------------------------------------

async def test_list_news_success(mock_client):
    mock_client.get_news.return_value = {
        "_embedded": {"elements": [_NEWS_ITEM]},
        "total": 1,
    }
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await list_news(project_id=1)

    assert "Sprint Review" in result


async def test_list_news_empty(mock_client):
    mock_client.get_news.return_value = {"_embedded": {"elements": []}, "total": 0}
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await list_news()

    assert "No news entries found" in result


async def test_list_news_failure(mock_client):
    mock_client.get_news.side_effect = Exception("API Error")
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await list_news()

    assert "❌" in result


# ---------------------------------------------------------------------------
# create_news
# ---------------------------------------------------------------------------

async def test_create_news_success(mock_client):
    mock_client.create_news.return_value = {
        "id": 10, "title": "Sprint Review",
        "summary": "Completed stories", "description": {"raw": "# Done"},
    }
    with patch("src.tools.news.get_client", return_value=mock_client):
        inp = CreateNewsInput(
            project_id=1, title="Sprint Review",
            summary="Completed stories", description="# Done"
        )
        result = await create_news(inp)

    assert "✅" in result
    assert "10" in result


async def test_create_news_failure(mock_client):
    mock_client.create_news.side_effect = Exception("Forbidden")
    with patch("src.tools.news.get_client", return_value=mock_client):
        inp = CreateNewsInput(
            project_id=1, title="T", summary="S", description="D"
        )
        result = await create_news(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# get_news
# ---------------------------------------------------------------------------

async def test_get_news_success(mock_client):
    mock_client.get_news_item.return_value = _NEWS_DETAIL
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await get_news(news_id=5)

    assert "Release Notes" in result
    assert "Alpha" in result


async def test_get_news_failure(mock_client):
    mock_client.get_news_item.side_effect = Exception("Not found")
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await get_news(news_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# update_news
# ---------------------------------------------------------------------------

async def test_update_news_success(mock_client):
    mock_client.update_news.return_value = {
        "id": 5, "title": "Updated Title", "summary": "New summary",
    }
    with patch("src.tools.news.get_client", return_value=mock_client):
        inp = UpdateNewsInput(news_id=5, title="Updated Title")
        result = await update_news(inp)

    assert "✅" in result
    assert "5" in result


async def test_update_news_failure(mock_client):
    mock_client.update_news.side_effect = Exception("Permission denied")
    with patch("src.tools.news.get_client", return_value=mock_client):
        inp = UpdateNewsInput(news_id=5, title="Updated")
        result = await update_news(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# delete_news
# ---------------------------------------------------------------------------

async def test_delete_news_success(mock_client):
    mock_client.delete_news.return_value = True
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await delete_news(news_id=5)

    assert "✅" in result
    assert "5" in result
    assert "deleted" in result.lower()


async def test_delete_news_failure(mock_client):
    mock_client.delete_news.side_effect = Exception("Not found")
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await delete_news(news_id=99)

    assert "❌" in result
