"""Tests for src/tools/time_entries.py."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.time_entries import (
    CreateTimeEntryInput,
    UpdateTimeEntryInput,
    create_time_entry,
    delete_time_entry,
    list_time_entries,
    list_time_entry_activities,
    update_time_entry,
)

_ENTRY = {
    "id": 7,
    "hours": 2.5,
    "spentOn": "2025-03-01",
    "comment": {"raw": "Worked on login"},
    "_embedded": {
        "workPackage": {"subject": "Fix login bug"},
        "user": {"name": "Alice"},
        "activity": {"name": "Development"},
    },
}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_create_time_entry_input_valid():
    inp = CreateTimeEntryInput(
        work_package_id=42, hours=3.0, spent_on="2025-03-01", activity_id=3
    )
    assert inp.hours == 3.0


def test_create_time_entry_input_zero_hours():
    with pytest.raises(ValidationError):
        CreateTimeEntryInput(
            work_package_id=42, hours=0, spent_on="2025-03-01", activity_id=3
        )


def test_create_time_entry_input_negative_hours():
    with pytest.raises(ValidationError):
        CreateTimeEntryInput(
            work_package_id=42, hours=-1.5, spent_on="2025-03-01", activity_id=3
        )


def test_update_time_entry_input_valid():
    inp = UpdateTimeEntryInput(time_entry_id=7, hours=4.0, spent_on="2025-03-02")
    assert inp.time_entry_id == 7
    assert inp.hours == 4.0


def test_update_time_entry_input_invalid_id():
    with pytest.raises(ValidationError):
        UpdateTimeEntryInput(time_entry_id=0, hours=1.0)


# ---------------------------------------------------------------------------
# list_time_entries
# ---------------------------------------------------------------------------

async def test_list_time_entries_success(mock_client):
    mock_client.get_time_entries.return_value = {"_embedded": {"elements": [_ENTRY]}}
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entries()

    assert "Fix login bug" in result
    assert "2.5" in result


async def test_list_time_entries_with_filters(mock_client):
    mock_client.get_time_entries.return_value = {"_embedded": {"elements": [_ENTRY]}}
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entries(
            work_package_id=42, user_id=5,
            from_date="2025-03-01", to_date="2025-03-31"
        )

    assert "Fix login bug" in result


async def test_list_time_entries_empty(mock_client):
    mock_client.get_time_entries.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entries()

    assert "No time entries found" in result


async def test_list_time_entries_failure(mock_client):
    mock_client.get_time_entries.side_effect = Exception("Server error")
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entries()

    assert "❌" in result


# ---------------------------------------------------------------------------
# create_time_entry
# ---------------------------------------------------------------------------

async def test_create_time_entry_success(mock_client):
    mock_client.create_time_entry.return_value = _ENTRY
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        inp = CreateTimeEntryInput(
            work_package_id=42, hours=2.5, spent_on="2025-03-01",
            activity_id=3, comment="Worked on login"
        )
        result = await create_time_entry(inp)

    assert "✅" in result
    assert "2.5" in result


async def test_create_time_entry_failure(mock_client):
    mock_client.create_time_entry.side_effect = Exception("Invalid activity")
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        inp = CreateTimeEntryInput(
            work_package_id=42, hours=1.0, spent_on="2025-03-01", activity_id=99
        )
        result = await create_time_entry(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# update_time_entry
# ---------------------------------------------------------------------------

async def test_update_time_entry_success(mock_client):
    mock_client.update_time_entry.return_value = {
        "id": 7, "hours": 4.0, "spentOn": "2025-03-02",
        "_embedded": {"activity": {"name": "Testing"}},
    }
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        inp = UpdateTimeEntryInput(time_entry_id=7, hours=4.0)
        result = await update_time_entry(inp)

    assert "✅" in result
    assert "4.0" in result


async def test_update_time_entry_no_fields(mock_client):
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        inp = UpdateTimeEntryInput(time_entry_id=7)
        result = await update_time_entry(inp)

    assert "❌" in result
    mock_client.update_time_entry.assert_not_called()


# ---------------------------------------------------------------------------
# delete_time_entry
# ---------------------------------------------------------------------------

async def test_delete_time_entry_success(mock_client):
    mock_client.delete_time_entry.return_value = True
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await delete_time_entry(time_entry_id=7)

    assert "✅" in result
    assert "7" in result


async def test_delete_time_entry_failure(mock_client):
    mock_client.delete_time_entry.side_effect = Exception("Not found")
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await delete_time_entry(time_entry_id=99)

    assert "❌" in result


# ---------------------------------------------------------------------------
# list_time_entry_activities
# ---------------------------------------------------------------------------

async def test_list_time_entry_activities_success(mock_client):
    mock_client.get_time_entry_activities.return_value = {
        "_embedded": {
            "elements": [
                {"id": 3, "name": "Development", "isDefault": True},
                {"id": 4, "name": "Testing"},
            ]
        }
    }
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entry_activities()

    assert "Development" in result
    assert "Testing" in result


async def test_list_time_entry_activities_empty_fallback(mock_client):
    """When the API returns no activities the tool should show common IDs."""
    mock_client.get_time_entry_activities.return_value = {"_embedded": {"elements": []}}
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entry_activities()

    # Falls back to hardcoded common activities
    assert "Management" in result
    assert "Development" in result


async def test_list_time_entry_activities_api_error_fallback(mock_client):
    """On API error the tool should still return common activities."""
    mock_client.get_time_entry_activities.side_effect = Exception("404 Not Found")
    with patch("src.tools.time_entries.get_client", return_value=mock_client):
        result = await list_time_entry_activities()

    assert "Management" in result
    assert "Development" in result
