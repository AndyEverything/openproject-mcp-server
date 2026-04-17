"""
Shared pytest configuration and fixtures for all test modules.

Sets dummy environment variables BEFORE any src.server import so
OpenProjectClient initialises without hitting a real API.
"""

import os

# Must be set before src.server is imported (happens when tool modules load)
os.environ.setdefault("OPENPROJECT_URL", "http://openproject.test")
os.environ.setdefault("OPENPROJECT_API_KEY", "test-api-key-00000000")
os.environ.setdefault("READ_ONLY_MODE", "false")

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_client():
    """Return a fresh AsyncMock that stands in for OpenProjectClient."""
    return AsyncMock()
