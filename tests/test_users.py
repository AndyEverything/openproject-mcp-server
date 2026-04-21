"""Tests for src/tools/users.py."""

from unittest.mock import patch

from src.tools.users import (
    get_role,
    get_user,
    list_project_members,
    list_roles,
    list_user_projects,
    list_users,
)

_USER = {
    "id": 7,
    "name": "Bob Smith",
    "email": "bob@example.com",
    "login": "bob",
    "status": "active",
    "admin": False,
}

_MEMBERSHIP = {
    "_links": {
        "principal": {"title": "Bob Smith", "href": "/api/v3/users/7"},
        "project": {"title": "Alpha"},
        "roles": [{"title": "Developer"}],
    }
}


# ---------------------------------------------------------------------------
# list_users
# ---------------------------------------------------------------------------

async def test_list_users_success(mock_client):
    mock_client.get_users.return_value = {"_embedded": {"elements": [_USER]}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_users()

    assert "Bob Smith" in result
    assert "bob@example.com" in result


async def test_list_users_with_name_filter(mock_client):
    mock_client.get_users.return_value = {"_embedded": {"elements": [_USER]}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_users(name="Bob")

    assert "Bob Smith" in result
    # Confirm a filter JSON was passed to get_users
    call_args = mock_client.get_users.call_args
    assert call_args is not None
    filters_arg = call_args[0][0] if call_args[0] else call_args[1].get("filters_json")
    assert filters_arg is not None


async def test_list_users_empty(mock_client):
    mock_client.get_users.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_users()

    assert "No users found" in result


async def test_list_users_failure(mock_client):
    mock_client.get_users.side_effect = Exception("API error")
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_users()

    assert "❌" in result


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

async def test_get_user_success(mock_client):
    mock_client.get_user.return_value = _USER
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await get_user(user_id=7)

    assert "Bob Smith" in result
    assert "✅" in result


async def test_get_user_failure(mock_client):
    mock_client.get_user.side_effect = Exception("Not found")
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await get_user(user_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# list_roles
# ---------------------------------------------------------------------------

async def test_list_roles_success(mock_client):
    mock_client.get_roles.return_value = {
        "_embedded": {"elements": [{"id": 1, "name": "Developer"}, {"id": 2, "name": "Manager"}]}
    }
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_roles()

    assert "Developer" in result
    assert "Manager" in result


async def test_list_roles_empty(mock_client):
    mock_client.get_roles.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_roles()

    assert "No roles found" in result


# ---------------------------------------------------------------------------
# get_role
# ---------------------------------------------------------------------------

async def test_get_role_success(mock_client):
    mock_client.get_role.return_value = {
        "id": 1,
        "name": "Developer",
        "_embedded": {
            "permissions": [{"name": "view_work_packages"}, {"name": "edit_work_packages"}]
        },
    }
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await get_role(role_id=1)

    assert "Developer" in result
    assert "view_work_packages" in result


async def test_get_role_failure(mock_client):
    mock_client.get_role.side_effect = Exception("Not found")
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await get_role(role_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# list_project_members
# ---------------------------------------------------------------------------

async def test_list_project_members_success(mock_client):
    mock_client.get_memberships.return_value = {
        "_embedded": {"elements": [_MEMBERSHIP]}
    }
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_project_members(project_id=1)

    assert "Bob Smith" in result
    assert "Developer" in result


async def test_list_project_members_empty(mock_client):
    mock_client.get_memberships.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_project_members(project_id=1)

    assert "No members found" in result


# ---------------------------------------------------------------------------
# list_user_projects
# ---------------------------------------------------------------------------

async def test_list_user_projects_success(mock_client):
    mock_client.get_memberships.return_value = {
        "_embedded": {
            "elements": [
                {
                    "_embedded": {
                        "project": {"name": "Alpha"},
                        "roles": [{"name": "Developer"}],
                    }
                }
            ]
        }
    }
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_user_projects(user_id=7)

    assert "Alpha" in result
    assert "Developer" in result


async def test_list_user_projects_not_member(mock_client):
    mock_client.get_memberships.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.users.get_client", return_value=mock_client):
        result = await list_user_projects(user_id=99)

    assert "not a member" in result
