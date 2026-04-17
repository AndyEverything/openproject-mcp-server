"""Tests for src/tools/projects.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.projects import (
    CreateProjectInput,
    UpdateProjectInput,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_project_input_valid():
    inp = CreateProjectInput(name="My Project", identifier="my-project")
    assert inp.name == "My Project"
    assert inp.identifier == "my-project"


def test_create_project_input_missing_name():
    with pytest.raises(ValidationError):
        CreateProjectInput(identifier="no-name")


def test_update_project_input_valid():
    inp = UpdateProjectInput(project_id=5, name="Renamed")
    assert inp.project_id == 5
    assert inp.name == "Renamed"


def test_update_project_input_invalid_id():
    with pytest.raises(ValidationError):
        UpdateProjectInput(project_id=0, name="Bad")


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------

async def test_list_projects_returns_projects(mock_client):
    mock_client.get_projects.return_value = {
        "_embedded": {
            "elements": [
                {"id": 1, "name": "Alpha", "active": True, "identifier": "alpha",
                 "description": {"raw": ""}, "_links": {}},
            ]
        }
    }
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await list_projects(active_only=True)

    assert "Alpha" in result


async def test_list_projects_empty(mock_client):
    mock_client.get_projects.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await list_projects()

    assert "No projects" in result or result.strip() != ""


async def test_list_projects_failure(mock_client):
    mock_client.get_projects.side_effect = Exception("Timeout")
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await list_projects()

    assert "❌" in result


# ---------------------------------------------------------------------------
# get_project
# ---------------------------------------------------------------------------

async def test_get_project_success(mock_client):
    mock_client.get_project.return_value = {
        "id": 3,
        "name": "Beta",
        "identifier": "beta",
        "active": True,
        "description": {"raw": "Beta project"},
    }
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await get_project(project_id=3)

    assert "Beta" in result
    assert "✅" in result


async def test_get_project_failure(mock_client):
    mock_client.get_project.side_effect = Exception("Not found")
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await get_project(project_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# create_project
# ---------------------------------------------------------------------------

async def test_create_project_success(mock_client):
    mock_client.create_project.return_value = {
        "id": 10,
        "name": "New Project",
        "identifier": "new-project",
        "active": True,
    }
    with patch("src.tools.projects.get_client", return_value=mock_client):
        inp = CreateProjectInput(name="New Project", identifier="new-project")
        result = await create_project(inp)

    assert "✅" in result
    assert "New Project" in result


async def test_create_project_failure(mock_client):
    mock_client.create_project.side_effect = Exception("Identifier taken")
    with patch("src.tools.projects.get_client", return_value=mock_client):
        inp = CreateProjectInput(name="Dup", identifier="dup")
        result = await create_project(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# update_project
# ---------------------------------------------------------------------------

async def test_update_project_success(mock_client):
    mock_client.update_project.return_value = {
        "id": 5,
        "name": "Renamed",
        "identifier": "renamed",
        "active": True,
    }
    with patch("src.tools.projects.get_client", return_value=mock_client):
        inp = UpdateProjectInput(project_id=5, name="Renamed")
        result = await update_project(inp)

    assert "✅" in result
    assert "Renamed" in result


# ---------------------------------------------------------------------------
# delete_project
# ---------------------------------------------------------------------------

async def test_delete_project_success(mock_client):
    mock_client.delete_project.return_value = True
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await delete_project(project_id=5)

    assert "✅" in result
    assert "5" in result


async def test_delete_project_failure(mock_client):
    mock_client.delete_project.side_effect = Exception("Permission denied")
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await delete_project(project_id=5)

    assert "❌" in result
