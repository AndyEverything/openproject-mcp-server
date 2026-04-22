"""Tests for per-user OpenProject API key via ContextVar."""
import pytest
from contextvars import copy_context
from unittest.mock import patch, MagicMock


def run_in_context(fn, **ctx_values):
    """Run fn in a fresh context with given ContextVar values set."""
    from src.server import _http_mode, _request_api_key
    ctx = copy_context()

    def _inner():
        if "http_mode" in ctx_values:
            _http_mode.set(ctx_values["http_mode"])
        if "api_key" in ctx_values:
            _request_api_key.set(ctx_values["api_key"])
        return fn()

    return ctx.run(_inner)


def test_stdio_mode_returns_global_client():
    """When ContextVars are at default (STDIO), get_client() returns global _client."""
    from src import server
    from src.server import get_client

    mock_global = MagicMock()
    with patch.object(server, "_client", mock_global):
        result = run_in_context(get_client)

    assert result is mock_global


def test_http_mode_with_key_returns_ephemeral_client():
    """HTTP mode + valid key -> ephemeral OpenProjectClient with that key."""
    from src import server
    from src.server import get_client

    mock_global = MagicMock()
    mock_global.base_url = "https://openproject.example.com"
    mock_global.proxy = None
    mock_global.readonly = True

    with patch.object(server, "_client", mock_global), \
         patch("src.server.OpenProjectClient") as MockClient:
        MockClient.return_value = MagicMock()
        result = run_in_context(get_client, http_mode=True, api_key="personal-token-abc")

    MockClient.assert_called_once_with(
        base_url="https://openproject.example.com",
        api_key="personal-token-abc",
        proxy=None,
        readonly=True,
    )
    assert result is MockClient.return_value


def test_http_mode_without_key_raises():
    """HTTP mode + missing key -> ValueError with clear message."""
    from src.server import get_client

    with pytest.raises(ValueError, match="X-OpenProject-Api-Key"):
        run_in_context(get_client, http_mode=True, api_key=None)
