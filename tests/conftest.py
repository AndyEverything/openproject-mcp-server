"""
Shared pytest configuration and fixtures for all test modules.

Sets dummy environment variables BEFORE any src.server import so
OpenProjectClient initialises without hitting a real API.
"""

import os
import sys

# Must be set before src.server is imported (happens when tool modules load)
os.environ.setdefault("OPENPROJECT_URL", "http://openproject.test")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-api-key-00000000")
os.environ.setdefault("READ_ONLY_MODE", "false")

import pytest
from unittest.mock import AsyncMock

# Unwrap FunctionTool objects for all tool modules so tests can call functions directly
try:
    from fastmcp.tools.tool import FunctionTool
    from src.tools import (
        connection, work_packages, projects, users, memberships,
        hierarchy, relations, time_entries, versions, weekly_reports, news,
    )

    for module in (
        connection, work_packages, projects, users, memberships,
        hierarchy, relations, time_entries, versions, weekly_reports, news,
    ):
        for name in dir(module):
            attr = getattr(module, name)
            if isinstance(attr, FunctionTool):
                setattr(module, name, attr.fn)
except (ImportError, AttributeError):
    pass


@pytest.fixture
def mock_client():
    """Return a fresh AsyncMock that stands in for OpenProjectClient."""
    return AsyncMock()
