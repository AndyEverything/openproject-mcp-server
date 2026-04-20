"""Tests for auth module logging behaviour."""
import logging
import pytest
from unittest.mock import patch
from src.auth import load_api_keys_from_env


def test_no_keys_logs_warning_not_print(caplog):
    """load_api_keys_from_env must use logging.warning, not print."""
    with patch.dict("os.environ", {"MCP_API_KEYS": ""}, clear=False):
        with caplog.at_level(logging.WARNING, logger="src.auth"):
            result = load_api_keys_from_env()
    assert result == {}
    assert any("No MCP_API_KEYS" in r.message for r in caplog.records)


def test_keys_loaded_logs_info_not_print(caplog):
    """load_api_keys_from_env must use logging.info, not print."""
    with patch.dict("os.environ", {"MCP_API_KEYS": "abc:Alice,def:Bob"}, clear=False):
        with caplog.at_level(logging.INFO, logger="src.auth"):
            result = load_api_keys_from_env()
    assert len(result) == 2
    assert any("2" in r.message for r in caplog.records)
