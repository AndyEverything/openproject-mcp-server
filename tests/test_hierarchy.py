"""Tests for src/tools/hierarchy.py."""

from unittest.mock import patch

from src.tools.hierarchy import (
    list_work_package_children,
    remove_work_package_parent,
    set_work_package_parent,
)

_CHILD_WP = {
    "id": 50,
    "subject": "Sub-task",
    "_embedded": {
        "type": {"name": "Task"},
        "status": {"name": "New"},
    },
}


# ---------------------------------------------------------------------------
# set_work_package_parent
# ---------------------------------------------------------------------------

async def test_set_parent_success(mock_client):
    mock_client.update_work_package.return_value = {
        "id": 50,
        "subject": "Sub-task",
        "_embedded": {
            "parent": {"subject": "Main task"},
        },
    }
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await set_work_package_parent(child_id=50, parent_id=10)

    assert "✅" in result
    assert "50" in result
    assert "10" in result


async def test_set_parent_failure(mock_client):
    mock_client.update_work_package.side_effect = Exception("Circular dependency")
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await set_work_package_parent(child_id=50, parent_id=10)

    assert "❌" in result


# ---------------------------------------------------------------------------
# remove_work_package_parent
# ---------------------------------------------------------------------------

async def test_remove_parent_success(mock_client):
    mock_client.update_work_package.return_value = {"id": 50, "subject": "Sub-task"}
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await remove_work_package_parent(work_package_id=50)

    assert "✅" in result
    assert "50" in result


async def test_remove_parent_failure(mock_client):
    mock_client.update_work_package.side_effect = Exception("Not found")
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await remove_work_package_parent(work_package_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# list_work_package_children
# ---------------------------------------------------------------------------

async def test_list_children_success(mock_client):
    mock_client.get_work_package_children.return_value = {
        "_embedded": {"elements": [_CHILD_WP]},
        "total": 1,
    }
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await list_work_package_children(work_package_id=10)

    assert "Sub-task" in result


async def test_list_children_empty(mock_client):
    mock_client.get_work_package_children.return_value = {
        "_embedded": {"elements": []},
        "total": 0,
    }
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await list_work_package_children(work_package_id=10)

    assert "no children" in result.lower()


async def test_list_children_pagination_hint(mock_client):
    children = [dict(_CHILD_WP, id=i, subject=f"Task {i}") for i in range(1, 6)]
    mock_client.get_work_package_children.return_value = {
        "_embedded": {"elements": children},
        "total": 50,
    }
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await list_work_package_children(work_package_id=10, page_size=5)

    assert "Pagination" in result or "offset" in result


async def test_list_children_failure(mock_client):
    mock_client.get_work_package_children.side_effect = Exception("Not found")
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await list_work_package_children(work_package_id=99)

    assert "❌" in result
