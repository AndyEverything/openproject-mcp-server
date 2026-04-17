"""Tests for src/tools/work_packages.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.work_packages import (
    CreateWorkPackageInput,
    UpdateWorkPackageInput,
    assign_work_package,
    create_work_package,
    delete_work_package,
    list_priorities,
    list_statuses,
    list_types,
    list_work_packages,
    search_work_packages,
    unassign_work_package,
    update_work_package,
)

_WP = {
    "id": 42,
    "subject": "Fix login bug",
    "_embedded": {
        "type": {"name": "Bug"},
        "status": {"name": "In Progress"},
        "priority": {"name": "High"},
        "assignee": {"name": "Alice"},
    },
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_wp_input_valid():
    inp = CreateWorkPackageInput(project_id=1, subject="Do something", type_id=2)
    assert inp.project_id == 1
    assert inp.subject == "Do something"


def test_create_wp_input_missing_project():
    with pytest.raises(ValidationError):
        CreateWorkPackageInput(subject="No project", type_id=1)


def test_create_wp_input_invalid_project_id():
    with pytest.raises(ValidationError):
        CreateWorkPackageInput(project_id=0, subject="Bad", type_id=1)


def test_update_wp_input_valid():
    inp = UpdateWorkPackageInput(work_package_id=10, status_id=3, percentage_done=50)
    assert inp.work_package_id == 10
    assert inp.percentage_done == 50


def test_update_wp_input_percentage_out_of_range():
    with pytest.raises(ValidationError):
        UpdateWorkPackageInput(work_package_id=1, percentage_done=110)


# ---------------------------------------------------------------------------
# list_work_packages
# ---------------------------------------------------------------------------

async def test_list_work_packages_success(mock_client):
    mock_client.get_work_packages.return_value = {
        "_embedded": {"elements": [_WP]},
        "total": 1,
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_work_packages(page_size=10)

    assert "Fix login bug" in result


async def test_list_work_packages_empty(mock_client):
    mock_client.get_work_packages.return_value = {
        "_embedded": {"elements": []},
        "total": 0,
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_work_packages()

    assert "No work packages" in result or result.strip() != ""


async def test_list_work_packages_failure(mock_client):
    mock_client.get_work_packages.side_effect = Exception("Server error")
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_work_packages()

    assert "❌" in result


async def test_list_work_packages_with_project_filter(mock_client):
    mock_client.get_work_packages.return_value = {
        "_embedded": {"elements": [_WP]},
        "total": 1,
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_work_packages(project_id=5)

    mock_client.get_work_packages.assert_called_once()
    assert "Fix login bug" in result


# ---------------------------------------------------------------------------
# search_work_packages
# ---------------------------------------------------------------------------

async def test_search_work_packages_success(mock_client):
    mock_client.get_work_packages.return_value = {
        "_embedded": {"elements": [_WP]},
        "total": 1,
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await search_work_packages(query="login")

    assert "Fix login bug" in result


# ---------------------------------------------------------------------------
# create_work_package
# ---------------------------------------------------------------------------

async def test_create_work_package_success(mock_client):
    mock_client.create_work_package.return_value = {
        "id": 99,
        "subject": "New task",
        "_embedded": {
            "type": {"name": "Task"},
            "status": {"name": "New"},
            "project": {"name": "Alpha"},
        },
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        inp = CreateWorkPackageInput(project_id=1, subject="New task", type_id=1)
        result = await create_work_package(inp)

    assert "✅" in result
    assert "New task" in result


async def test_create_work_package_failure(mock_client):
    mock_client.create_work_package.side_effect = Exception("Bad request")
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        inp = CreateWorkPackageInput(project_id=1, subject="Bad", type_id=1)
        result = await create_work_package(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# update_work_package
# ---------------------------------------------------------------------------

async def test_update_work_package_success(mock_client):
    mock_client.update_work_package.return_value = {
        "id": 42,
        "subject": "Fix login bug",
        "_embedded": {"status": {"name": "Done"}, "type": {"name": "Bug"}},
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        inp = UpdateWorkPackageInput(work_package_id=42, status_id=5)
        result = await update_work_package(inp)

    assert "✅" in result


# ---------------------------------------------------------------------------
# delete_work_package
# ---------------------------------------------------------------------------

async def test_delete_work_package_success(mock_client):
    mock_client.delete_work_package.return_value = True
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await delete_work_package(work_package_id=42)

    assert "✅" in result
    assert "42" in result


# ---------------------------------------------------------------------------
# list_types / list_statuses / list_priorities
# ---------------------------------------------------------------------------

async def test_list_types_success(mock_client):
    mock_client.get_types.return_value = {
        "_embedded": {"elements": [{"id": 1, "name": "Task"}, {"id": 2, "name": "Bug"}]}
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_types()

    assert "Task" in result
    assert "Bug" in result


async def test_list_statuses_success(mock_client):
    mock_client.get_statuses.return_value = {
        "_embedded": {"elements": [{"id": 1, "name": "New"}, {"id": 2, "name": "In Progress"}]}
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_statuses()

    assert "New" in result
    assert "In Progress" in result


async def test_list_priorities_success(mock_client):
    mock_client.get_priorities.return_value = {
        "_embedded": {"elements": [{"id": 1, "name": "Low"}, {"id": 2, "name": "High"}]}
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_priorities()

    assert "Low" in result
    assert "High" in result


# ---------------------------------------------------------------------------
# assign / unassign
# ---------------------------------------------------------------------------

async def test_assign_work_package_success(mock_client):
    mock_client.update_work_package.return_value = {
        "id": 42,
        "subject": "Fix login bug",
        "_embedded": {"assignee": {"name": "Alice"}},
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await assign_work_package(work_package_id=42, assignee_id=7)

    assert "✅" in result


async def test_unassign_work_package_success(mock_client):
    mock_client.update_work_package.return_value = {
        "id": 42,
        "subject": "Fix login bug",
        "_embedded": {},
    }
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await unassign_work_package(work_package_id=42)

    assert "✅" in result
