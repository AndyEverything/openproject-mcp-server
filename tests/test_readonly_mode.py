"""
Tests for READ_ONLY_MODE feature.

Three layers:
  Layer 1 — OpenProjectClient._request unit tests (no HTTP mock needed;
             the guard raises before any network call is attempted)
  Layer 2 — Tool-level tests: write tools return ❌ when the client raises
             the readonly exception; read tools are unaffected
  Layer 3 — server.py integration: READ_ONLY_MODE env var is wired correctly
"""

import os
import pytest
from unittest.mock import AsyncMock, patch

from src.client import OpenProjectClient

# Shared exception that simulates what _request raises in read-only mode
_READONLY_EXC = Exception(
    "Read-only mode is enabled: POST operations are not permitted. "
    "Set READ_ONLY_MODE=false to allow write operations."
)


# ---------------------------------------------------------------------------
# Layer 1: OpenProjectClient unit tests
# ---------------------------------------------------------------------------

def test_client_readonly_false_by_default():
    client = OpenProjectClient(base_url="http://test.local", api_key="key")
    assert client.readonly is False


def test_client_readonly_true_when_set():
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    assert client.readonly is True


async def test_request_blocks_post_in_readonly():
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    with pytest.raises(Exception, match="Read-only mode"):
        await client._request("POST", "/projects", data={"name": "X"})


async def test_request_blocks_patch_in_readonly():
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    with pytest.raises(Exception, match="Read-only mode"):
        await client._request("PATCH", "/projects/1", data={})


async def test_request_blocks_put_in_readonly():
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    with pytest.raises(Exception, match="Read-only mode"):
        await client._request("PUT", "/work_packages/5", data={})


async def test_request_blocks_delete_in_readonly():
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    with pytest.raises(Exception, match="Read-only mode"):
        await client._request("DELETE", "/projects/1")


async def test_request_does_not_block_get_in_readonly():
    """GET is allowed; the guard must NOT raise for read-only GET requests."""
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=True)
    # The request will fail with a network error (no real server), but NOT
    # with the read-only guard — that's what we assert.
    with pytest.raises(Exception) as exc_info:
        await client._request("GET", "/projects")
    assert "Read-only mode" not in str(exc_info.value)


async def test_request_not_blocked_when_not_readonly():
    """In read-write mode, the guard never fires even for POST/DELETE."""
    client = OpenProjectClient(base_url="http://test.local", api_key="key", readonly=False)
    with pytest.raises(Exception) as exc_info:
        await client._request("POST", "/projects", data={"name": "X"})
    assert "Read-only mode" not in str(exc_info.value)


def test_write_methods_constant_covers_all_mutating_verbs():
    from src.client import _WRITE_METHODS
    assert "POST" in _WRITE_METHODS
    assert "PATCH" in _WRITE_METHODS
    assert "PUT" in _WRITE_METHODS
    assert "DELETE" in _WRITE_METHODS
    assert "GET" not in _WRITE_METHODS
    assert "HEAD" not in _WRITE_METHODS


# ---------------------------------------------------------------------------
# Layer 2: Tool-level tests
# ---------------------------------------------------------------------------

# --- projects ---------------------------------------------------------------

async def test_create_project_blocked(mock_client):
    from src.tools.projects import create_project, CreateProjectInput
    mock_client.create_project.side_effect = _READONLY_EXC
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await create_project(CreateProjectInput(name="X", identifier="x"))
    assert "❌" in result
    assert "Read-only mode" in result


async def test_update_project_blocked(mock_client):
    from src.tools.projects import update_project, UpdateProjectInput
    mock_client.update_project.side_effect = _READONLY_EXC
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await update_project(UpdateProjectInput(project_id=1, name="Y"))
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_project_blocked(mock_client):
    from src.tools.projects import delete_project
    mock_client.delete_project.side_effect = _READONLY_EXC
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await delete_project(project_id=1)
    assert "❌" in result
    assert "Read-only mode" in result


# --- work_packages ----------------------------------------------------------

async def test_create_work_package_blocked(mock_client):
    from src.tools.work_packages import create_work_package, CreateWorkPackageInput
    mock_client.create_work_package.side_effect = _READONLY_EXC
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await create_work_package(
            CreateWorkPackageInput(project_id=1, subject="T", type_id=1)
        )
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_work_package_blocked(mock_client):
    from src.tools.work_packages import delete_work_package
    mock_client.delete_work_package.side_effect = _READONLY_EXC
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await delete_work_package(work_package_id=42)
    assert "❌" in result
    assert "Read-only mode" in result


# --- memberships ------------------------------------------------------------

async def test_create_membership_blocked(mock_client):
    from src.tools.memberships import create_membership, CreateMembershipInput
    mock_client.create_membership.side_effect = _READONLY_EXC
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await create_membership(
            CreateMembershipInput(project_id=1, user_id=2, role_id=3)
        )
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_membership_blocked(mock_client):
    from src.tools.memberships import delete_membership
    mock_client.delete_membership.side_effect = _READONLY_EXC
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await delete_membership(membership_id=5)
    assert "❌" in result
    assert "Read-only mode" in result


# --- hierarchy --------------------------------------------------------------

async def test_set_work_package_parent_blocked(mock_client):
    from src.tools.hierarchy import set_work_package_parent
    mock_client.update_work_package.side_effect = _READONLY_EXC
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await set_work_package_parent(child_id=10, parent_id=5)
    assert "❌" in result
    assert "Read-only mode" in result


async def test_remove_work_package_parent_blocked(mock_client):
    from src.tools.hierarchy import remove_work_package_parent
    mock_client.update_work_package.side_effect = _READONLY_EXC
    with patch("src.tools.hierarchy.get_client", return_value=mock_client):
        result = await remove_work_package_parent(work_package_id=10)
    assert "❌" in result
    assert "Read-only mode" in result


# --- relations --------------------------------------------------------------

async def test_create_relation_blocked(mock_client):
    from src.tools.relations import create_work_package_relation, CreateRelationInput
    mock_client.create_work_package_relation.side_effect = _READONLY_EXC
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await create_work_package_relation(
            CreateRelationInput(from_id=1, to_id=2, type="follows")
        )
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_relation_blocked(mock_client):
    from src.tools.relations import delete_work_package_relation
    mock_client.delete_work_package_relation.side_effect = _READONLY_EXC
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await delete_work_package_relation(relation_id=7)
    assert "❌" in result
    assert "Read-only mode" in result


# --- time_entries -----------------------------------------------------------

async def test_create_time_entry_blocked(mock_client):
    from src.tools.time_entries import create_time_entry, CreateTimeEntryInput
    mock_client.create_time_entry.side_effect = _READONLY_EXC
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await create_time_entry(
            CreateTimeEntryInput(
                work_package_id=1, hours=2.0, spent_on="2026-01-01", activity_id=3
            )
        )
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_time_entry_blocked(mock_client):
    from src.tools.time_entries import delete_time_entry
    mock_client.delete_time_entry.side_effect = _READONLY_EXC
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await delete_time_entry(time_entry_id=3)
    assert "❌" in result
    assert "Read-only mode" in result


# --- versions ---------------------------------------------------------------

async def test_create_version_blocked(mock_client):
    from src.tools.versions import create_version, CreateVersionInput
    mock_client.create_version.side_effect = _READONLY_EXC
    with patch("src.tools.versions.get_client", return_value=mock_client):
        result = await create_version(CreateVersionInput(project_id=1, name="v1.0"))
    assert "❌" in result
    assert "Read-only mode" in result


# --- news -------------------------------------------------------------------

async def test_create_news_blocked(mock_client):
    from src.tools.news import create_news, CreateNewsInput
    mock_client.create_news.side_effect = _READONLY_EXC
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await create_news(
            CreateNewsInput(project_id=1, title="T", summary="S", description="D")
        )
    assert "❌" in result
    assert "Read-only mode" in result


async def test_update_news_blocked(mock_client):
    from src.tools.news import update_news, UpdateNewsInput
    mock_client.update_news.side_effect = _READONLY_EXC
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await update_news(UpdateNewsInput(news_id=1, title="New"))
    assert "❌" in result
    assert "Read-only mode" in result


async def test_delete_news_blocked(mock_client):
    from src.tools.news import delete_news
    mock_client.delete_news.side_effect = _READONLY_EXC
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await delete_news(news_id=1)
    assert "❌" in result
    assert "Read-only mode" in result


# ---------------------------------------------------------------------------
# Read tools must NOT be affected by the readonly mode
# ---------------------------------------------------------------------------

async def test_list_projects_allowed_in_readonly(mock_client):
    from src.tools.projects import list_projects
    mock_client.get_projects.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.projects.get_client", return_value=mock_client):
        result = await list_projects()
    assert "Read-only mode" not in result


async def test_list_work_packages_allowed_in_readonly(mock_client):
    from src.tools.work_packages import list_work_packages
    mock_client.get_work_packages.return_value = {"_embedded": {"elements": []}, "total": 0}
    with patch("src.tools.work_packages.get_client", return_value=mock_client):
        result = await list_work_packages()
    assert "Read-only mode" not in result


async def test_list_news_allowed_in_readonly(mock_client):
    from src.tools.news import list_news
    mock_client.get_news.return_value = {"_embedded": {"elements": []}, "total": 0}
    with patch("src.tools.news.get_client", return_value=mock_client):
        result = await list_news()
    assert "Read-only mode" not in result


# ---------------------------------------------------------------------------
# Layer 3: server.py — is_readonly() helper
# ---------------------------------------------------------------------------

def test_is_readonly_returns_false_by_default():
    from src.server import is_readonly
    # conftest sets READ_ONLY_MODE=false, so the loaded server has readonly=False
    assert is_readonly() is False


def test_client_has_readonly_attribute():
    from src.server import get_client
    client = get_client()
    assert hasattr(client, "readonly")
    assert client.readonly is False
