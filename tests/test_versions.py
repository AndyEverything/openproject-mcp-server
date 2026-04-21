"""Tests for src/tools/versions.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.versions import CreateVersionInput, create_version, list_versions

_VERSION = {
    "id": 3,
    "name": "v1.0",
    "status": "open",
    "startDate": "2025-01-01",
    "endDate": "2025-03-31",
    "description": {"raw": "First release"},
    "_embedded": {"definingProject": {"name": "Alpha"}},
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_version_input_valid():
    inp = CreateVersionInput(
        project_id=1, name="v1.0", due_date="2025-03-31", status="open"
    )
    assert inp.name == "v1.0"
    assert inp.project_id == 1


def test_create_version_input_empty_name():
    with pytest.raises(ValidationError):
        CreateVersionInput(project_id=1, name="")


def test_create_version_input_invalid_project_id():
    with pytest.raises(ValidationError):
        CreateVersionInput(project_id=0, name="v1.0")


def test_create_version_input_name_too_long():
    with pytest.raises(ValidationError):
        CreateVersionInput(project_id=1, name="x" * 256)


# ---------------------------------------------------------------------------
# list_versions
# ---------------------------------------------------------------------------

async def test_list_versions_success(mock_client):
    mock_client.get_versions.return_value = {"_embedded": {"elements": [_VERSION]}}
    with patch("src.tools.versions.get_client", return_value=mock_client):
        result = await list_versions(project_id=1)

    assert "v1.0" in result
    assert "open" in result
    assert "Alpha" in result


async def test_list_versions_empty(mock_client):
    mock_client.get_versions.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.versions.get_client", return_value=mock_client):
        result = await list_versions(project_id=1)

    assert "No versions found" in result


async def test_list_versions_failure(mock_client):
    mock_client.get_versions.side_effect = Exception("Not found")
    with patch("src.tools.versions.get_client", return_value=mock_client):
        result = await list_versions(project_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# create_version
# ---------------------------------------------------------------------------

async def test_create_version_success(mock_client):
    mock_client.create_version.return_value = _VERSION
    with patch("src.tools.versions.get_client", return_value=mock_client):
        inp = CreateVersionInput(
            project_id=1, name="v1.0",
            description="First release", due_date="2025-03-31", status="open"
        )
        result = await create_version(inp)

    assert "✅" in result
    assert "v1.0" in result
    assert "open" in result


async def test_create_version_with_dates(mock_client):
    mock_client.create_version.return_value = {
        "id": 4, "name": "v2.0", "status": "open",
        "startDate": "2025-04-01", "endDate": "2025-06-30",
    }
    with patch("src.tools.versions.get_client", return_value=mock_client):
        inp = CreateVersionInput(
            project_id=1, name="v2.0",
            start_date="2025-04-01", due_date="2025-06-30"
        )
        result = await create_version(inp)

    assert "2025-04-01" in result
    assert "2025-06-30" in result


async def test_create_version_failure(mock_client):
    mock_client.create_version.side_effect = Exception("Name already taken")
    with patch("src.tools.versions.get_client", return_value=mock_client):
        inp = CreateVersionInput(project_id=1, name="v1.0")
        result = await create_version(inp)

    assert "❌" in result
