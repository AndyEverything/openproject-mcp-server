"""Tests for src/tools/weekly_reports.py."""

import json
import pytest
from pydantic import ValidationError
from unittest.mock import patch

from src.tools.weekly_reports import (
    GenerateWeeklyReportInput,
    GetReportDataInput,
    generate_last_week_report,
    generate_this_week_report,
    generate_weekly_report,
    get_report_data,
)

_PROJECT = {"id": 1, "name": "Alpha", "identifier": "alpha"}

_WP_DONE = {
    "id": 10,
    "subject": "Implement login",
    "updatedAt": "2025-03-05T12:00:00Z",
    "createdAt": "2025-03-01T08:00:00Z",
    "_embedded": {"status": {"name": "Done"}, "type": {"name": "Task"}},
}

_WP_IN_PROGRESS = {
    "id": 11,
    "subject": "Add dashboard",
    "updatedAt": "2025-03-06T14:00:00Z",
    "createdAt": "2025-03-02T09:00:00Z",
    "_embedded": {"status": {"name": "In Progress"}, "type": {"name": "Feature"}},
}


def _make_wp_page(elements, total=None):
    return {
        "_embedded": {"elements": elements},
        "total": total if total is not None else len(elements),
    }


def _setup_report_mocks(mock_client):
    """Configure mock_client for a typical generate_weekly_report call."""
    mock_client.get_project.return_value = _PROJECT
    # _fetch_all_project_work_packages loops; return one page then empty
    mock_client.get_work_packages.side_effect = [
        _make_wp_page([_WP_DONE, _WP_IN_PROGRESS], total=2),
        _make_wp_page([]),  # terminates loop
    ]
    mock_client.get_memberships.return_value = {
        "_embedded": {"elements": []}
    }
    mock_client.get_time_entries.return_value = {
        "_embedded": {"elements": []}
    }
    # Suppress unawaited-coroutine warnings from the optional relations fetch
    mock_client.get_relations.return_value = {"_embedded": {"elements": []}}


# ---------------------------------------------------------------------------
# Input model validation
# ---------------------------------------------------------------------------

def test_generate_weekly_report_input_valid():
    inp = GenerateWeeklyReportInput(
        project_id=1, from_date="2025-03-03", to_date="2025-03-09"
    )
    assert inp.format == "markdown"


def test_generate_weekly_report_input_invalid_project():
    with pytest.raises(ValidationError):
        GenerateWeeklyReportInput(project_id=0, from_date="2025-03-03", to_date="2025-03-09")


def test_get_report_data_input_valid():
    inp = GetReportDataInput(project_id=1, from_date="2025-03-03", to_date="2025-03-09")
    assert inp.project_id == 1


def test_get_report_data_input_invalid_project():
    with pytest.raises(ValidationError):
        GetReportDataInput(project_id=0, from_date="2025-03-03", to_date="2025-03-09")


# ---------------------------------------------------------------------------
# generate_weekly_report (markdown)
# ---------------------------------------------------------------------------

async def test_generate_weekly_report_markdown(mock_client):
    _setup_report_mocks(mock_client)
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GenerateWeeklyReportInput(
            project_id=1, from_date="2025-03-03", to_date="2025-03-09",
            team_name="Backend Team", format="markdown"
        )
        result = await generate_weekly_report(inp)

    assert "Alpha" in result
    assert isinstance(result, str)
    assert len(result) > 50


async def test_generate_weekly_report_json_format(mock_client):
    _setup_report_mocks(mock_client)
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GenerateWeeklyReportInput(
            project_id=1, from_date="2025-03-03", to_date="2025-03-09",
            format="json"
        )
        result = await generate_weekly_report(inp)

    data = json.loads(result)
    assert isinstance(data, dict)


async def test_generate_weekly_report_invalid_date_format(mock_client):
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GenerateWeeklyReportInput(
            project_id=1, from_date="03-03-2025", to_date="03-09-2025"
        )
        result = await generate_weekly_report(inp)

    assert "❌" in result or "Invalid date" in result


async def test_generate_weekly_report_date_range_inverted(mock_client):
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GenerateWeeklyReportInput(
            project_id=1, from_date="2025-03-09", to_date="2025-03-03"
        )
        result = await generate_weekly_report(inp)

    assert "❌" in result or "before" in result


async def test_generate_weekly_report_api_failure(mock_client):
    mock_client.get_project.side_effect = Exception("Not found")
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GenerateWeeklyReportInput(
            project_id=99, from_date="2025-03-03", to_date="2025-03-09"
        )
        result = await generate_weekly_report(inp)

    assert "❌" in result


# ---------------------------------------------------------------------------
# get_report_data
# ---------------------------------------------------------------------------

async def test_get_report_data_returns_json(mock_client):
    _setup_report_mocks(mock_client)
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GetReportDataInput(
            project_id=1, from_date="2025-03-03", to_date="2025-03-09"
        )
        result = await get_report_data(inp)

    data = json.loads(result)
    assert isinstance(data, dict)


async def test_get_report_data_invalid_dates(mock_client):
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        inp = GetReportDataInput(
            project_id=1, from_date="bad-date", to_date="2025-03-09"
        )
        result = await get_report_data(inp)

    assert "❌" in result or "Invalid date" in result


# ---------------------------------------------------------------------------
# generate_this_week_report / generate_last_week_report
# ---------------------------------------------------------------------------

async def test_generate_this_week_report(mock_client):
    _setup_report_mocks(mock_client)
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        result = await generate_this_week_report(project_id=1, team_name="Team X")

    assert "Alpha" in result
    assert isinstance(result, str)


async def test_generate_last_week_report(mock_client):
    _setup_report_mocks(mock_client)
    with patch("src.tools.weekly_reports.get_client", return_value=mock_client):
        result = await generate_last_week_report(project_id=1)

    assert "Alpha" in result
    assert isinstance(result, str)
