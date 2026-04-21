"""Tests for src/tools/memberships.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.memberships import (
    CreateMembershipInput,
    UpdateMembershipInput,
    create_membership,
    delete_membership,
    get_membership,
    list_memberships,
    update_membership,
)

_MEMBER = {
    "_links": {
        "principal": {"title": "Bob", "href": "/api/v3/users/7"},
        "project": {"title": "Alpha"},
        "roles": [{"title": "Developer"}],
    }
}

_MEMBER_DETAIL = {
    "id": 11,
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-02T00:00:00Z",
    "_links": {
        "project": {"title": "Alpha"},
        "principal": {"title": "Bob"},
        "roles": [{"title": "Developer"}],
    },
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_membership_input_valid():
    inp = CreateMembershipInput(project_id=1, user_id=7, role_ids=[2])
    assert inp.project_id == 1
    assert inp.user_id == 7


def test_create_membership_input_invalid_project_id():
    with pytest.raises(ValidationError):
        CreateMembershipInput(project_id=0, user_id=7, role_ids=[2])


def test_update_membership_input_valid():
    inp = UpdateMembershipInput(membership_id=11, role_ids=[3])
    assert inp.membership_id == 11


def test_update_membership_input_invalid_id():
    with pytest.raises(ValidationError):
        UpdateMembershipInput(membership_id=0, role_ids=[1])


# ---------------------------------------------------------------------------
# list_memberships
# ---------------------------------------------------------------------------

async def test_list_memberships_success(mock_client):
    mock_client.get_memberships.return_value = {"_embedded": {"elements": [_MEMBER]}}
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await list_memberships()

    assert "Bob" in result
    assert "Developer" in result


async def test_list_memberships_filtered_by_project(mock_client):
    mock_client.get_memberships.return_value = {"_embedded": {"elements": [_MEMBER]}}
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await list_memberships(project_id=1)

    assert "Bob" in result
    # project name should not appear when filtering by single project
    assert "Alpha" not in result


async def test_list_memberships_empty(mock_client):
    mock_client.get_memberships.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await list_memberships()

    assert "No memberships found" in result


# ---------------------------------------------------------------------------
# get_membership
# ---------------------------------------------------------------------------

async def test_get_membership_success(mock_client):
    mock_client.get_membership.return_value = _MEMBER_DETAIL
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await get_membership(membership_id=11)

    assert "✅" in result
    assert "Alpha" in result
    assert "Bob" in result
    assert "Developer" in result


async def test_get_membership_failure(mock_client):
    mock_client.get_membership.side_effect = Exception("Not found")
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await get_membership(membership_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# create_membership
# ---------------------------------------------------------------------------

async def test_create_membership_success(mock_client):
    mock_client.create_membership.return_value = {
        "id": 20,
        "_embedded": {
            "project": {"name": "Alpha"},
            "principal": {"name": "Bob"},
            "roles": [{"name": "Developer"}],
        },
    }
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        inp = CreateMembershipInput(project_id=1, user_id=7, role_id=2)
        result = await create_membership(inp)

    assert "✅" in result
    assert "20" in result


async def test_create_membership_missing_principal(mock_client):
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        # No user_id or group_id
        inp = CreateMembershipInput(project_id=1, role_id=2)
        result = await create_membership(inp)

    assert "❌" in result
    mock_client.create_membership.assert_not_called()


async def test_create_membership_missing_role(mock_client):
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        # No role_ids or role_id
        inp = CreateMembershipInput(project_id=1, user_id=7)
        result = await create_membership(inp)

    assert "❌" in result
    mock_client.create_membership.assert_not_called()


# ---------------------------------------------------------------------------
# update_membership
# ---------------------------------------------------------------------------

async def test_update_membership_success(mock_client):
    mock_client.update_membership.return_value = {
        "id": 11,
        "_embedded": {"roles": [{"name": "Manager"}]},
    }
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        inp = UpdateMembershipInput(membership_id=11, role_ids=[4])
        result = await update_membership(inp)

    assert "✅" in result
    assert "11" in result


async def test_update_membership_no_fields(mock_client):
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        inp = UpdateMembershipInput(membership_id=11)
        result = await update_membership(inp)

    assert "❌" in result
    mock_client.update_membership.assert_not_called()


# ---------------------------------------------------------------------------
# delete_membership
# ---------------------------------------------------------------------------

async def test_delete_membership_success(mock_client):
    mock_client.delete_membership.return_value = True
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await delete_membership(membership_id=11)

    assert "✅" in result
    assert "11" in result


async def test_delete_membership_failure(mock_client):
    mock_client.delete_membership.side_effect = Exception("Permission denied")
    with patch("src.tools.memberships.get_client", return_value=mock_client):
        result = await delete_membership(membership_id=11)

    assert "❌" in result
