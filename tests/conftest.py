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

# Unwrap FunctionTool objects immediately after module loads so test imports get unwrapped functions
try:
    from src.tools import work_packages
    from fastmcp.tools.tool import FunctionTool

    # For each function in the module that's wrapped as FunctionTool,
    # replace it with the underlying function in the module namespace
    for name in dir(work_packages):
        attr = getattr(work_packages, name)
        if isinstance(attr, FunctionTool):
            setattr(work_packages, name, attr.fn)
except (ImportError, AttributeError):
    pass  # Safe to ignore if import fails


@pytest.fixture
def mock_client():
    """Return a fresh AsyncMock that stands in for OpenProjectClient."""
    return AsyncMock()
