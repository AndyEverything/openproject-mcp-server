"""Tests for src/tools/connection.py — test_connection and check_permissions."""

from unittest.mock import patch

from src.tools.connection import check_permissions, test_connection


async def test_connection_success(mock_client):
    mock_client.test_connection.return_value = {
        "instanceVersion": "13.4.0",
        "coreVersion": "13.4.0",
    }
    with patch("src.tools.connection.get_client", return_value=mock_client):
        result = await test_connection()

    assert "✅" in result
    assert "13.4.0" in result


async def test_connection_failure(mock_client):
    mock_client.test_connection.side_effect = Exception("Connection refused")
    with patch("src.tools.connection.get_client", return_value=mock_client):
        result = await test_connection()

    assert "❌" in result
    assert "Connection refused" in result


async def test_check_permissions_success(mock_client):
    mock_client.check_permissions.return_value = {
        "name": "Alice",
        "email": "alice@example.com",
        "login": "alice",
        "status": "active",
        "admin": True,
    }
    with patch("src.tools.connection.get_client", return_value=mock_client):
        result = await check_permissions()

    assert "✅" in result
    assert "Alice" in result
    assert "alice@example.com" in result
    assert "Yes" in result  # admin


async def test_check_permissions_empty_result(mock_client):
    mock_client.check_permissions.return_value = {}
    with patch("src.tools.connection.get_client", return_value=mock_client):
        result = await check_permissions()

    assert "❌" in result


async def test_check_permissions_failure(mock_client):
    mock_client.check_permissions.side_effect = Exception("Unauthorized")
    with patch("src.tools.connection.get_client", return_value=mock_client):
        result = await check_permissions()

    assert "❌" in result
    assert "Unauthorized" in result
