"""Tests for src/tools/relations.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.relations import (
    CreateRelationInput,
    UpdateRelationInput,
    create_work_package_relation,
    delete_work_package_relation,
    get_work_package_relation,
    list_work_package_relations,
    update_work_package_relation,
)

_RELATION = {
    "id": 5,
    "type": "follows",
    "lag": 2,
    "description": "Wait 2 days",
    "_embedded": {
        "from": {"id": 10, "subject": "Task A"},
        "to": {"id": 20, "subject": "Task B"},
    },
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_relation_input_valid():
    inp = CreateRelationInput(from_id=10, to_id=20, type="follows")
    assert inp.from_id == 10
    assert inp.type == "follows"


def test_create_relation_input_invalid_zero_id():
    with pytest.raises(ValidationError):
        CreateRelationInput(from_id=0, to_id=20, type="follows")


def test_update_relation_input_valid():
    inp = UpdateRelationInput(relation_id=5, lag=3, description="Updated")
    assert inp.relation_id == 5
    assert inp.lag == 3


def test_update_relation_input_invalid_id():
    with pytest.raises(ValidationError):
        UpdateRelationInput(relation_id=0)


# ---------------------------------------------------------------------------
# create_work_package_relation
# ---------------------------------------------------------------------------

async def test_create_relation_success(mock_client):
    mock_client.create_work_package_relation.return_value = _RELATION
    with patch("src.tools.relations.get_client", return_value=mock_client):
        inp = CreateRelationInput(from_id=10, to_id=20, type="follows", lag=2)
        result = await create_work_package_relation(inp)

    assert "✅" in result
    assert "follows" in result
    assert "Task A" in result
    assert "Task B" in result


async def test_create_relation_failure(mock_client):
    mock_client.create_work_package_relation.side_effect = Exception("Conflict")
    with patch("src.tools.relations.get_client", return_value=mock_client):
        inp = CreateRelationInput(from_id=10, to_id=20, type="blocks")
        result = await create_work_package_relation(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# list_work_package_relations
# ---------------------------------------------------------------------------

async def test_list_relations_success(mock_client):
    mock_client.list_work_package_relations.return_value = {
        "_embedded": {"elements": [_RELATION]}
    }
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await list_work_package_relations(work_package_id=10)

    assert "follows" in result
    assert "Task A" in result


async def test_list_relations_empty(mock_client):
    mock_client.list_work_package_relations.return_value = {
        "_embedded": {"elements": []}
    }
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await list_work_package_relations(work_package_id=10)

    assert "no relations" in result.lower()


# ---------------------------------------------------------------------------
# get_work_package_relation
# ---------------------------------------------------------------------------

async def test_get_relation_success(mock_client):
    mock_client.get_work_package_relation.return_value = _RELATION
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await get_work_package_relation(relation_id=5)

    assert "✅" in result
    assert "follows" in result
    assert "Task A" in result


async def test_get_relation_failure(mock_client):
    mock_client.get_work_package_relation.side_effect = Exception("Not found")
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await get_work_package_relation(relation_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# update_work_package_relation
# ---------------------------------------------------------------------------

async def test_update_relation_success(mock_client):
    mock_client.update_work_package_relation.return_value = {
        "id": 5,
        "type": "follows",
        "lag": 3,
        "description": "Updated",
    }
    with patch("src.tools.relations.get_client", return_value=mock_client):
        inp = UpdateRelationInput(relation_id=5, lag=3, description="Updated")
        result = await update_work_package_relation(inp)

    assert "✅" in result
    assert "5" in result


async def test_update_relation_no_fields(mock_client):
    with patch("src.tools.relations.get_client", return_value=mock_client):
        inp = UpdateRelationInput(relation_id=5)
        result = await update_work_package_relation(inp)

    assert "❌" in result
    mock_client.update_work_package_relation.assert_not_called()


# ---------------------------------------------------------------------------
# delete_work_package_relation
# ---------------------------------------------------------------------------

async def test_delete_relation_success(mock_client):
    mock_client.delete_work_package_relation.return_value = True
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await delete_work_package_relation(relation_id=5)

    assert "✅" in result
    assert "5" in result


async def test_delete_relation_api_returns_false(mock_client):
    mock_client.delete_work_package_relation.return_value = False
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await delete_work_package_relation(relation_id=5)

    assert "❌" in result


async def test_delete_relation_failure(mock_client):
    mock_client.delete_work_package_relation.side_effect = Exception("Not found")
    with patch("src.tools.relations.get_client", return_value=mock_client):
        result = await delete_work_package_relation(relation_id=99)

    assert "❌" in result
