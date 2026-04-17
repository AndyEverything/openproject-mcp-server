#!/usr/bin/env python3
"""
Unit Tests for OpenProject MCP Server

These tests focus on individual components and don't require a running OpenProject instance.
Adapted from PR #4 (addictivedev/openproject-mcp-server) to work with the modular src/ structure.
"""

import sys
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.client import OpenProjectClient


class TestOpenProjectClient:
    """Test cases for OpenProjectClient"""

    def test_init(self):
        """Test client initialization"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")
        assert client.base_url == "https://test.openproject.com"
        assert client.api_key == "test-key"
        assert client.proxy is None

    def test_init_with_proxy(self):
        """Test client initialization with proxy"""
        client = OpenProjectClient("https://test.openproject.com", "test-key", "http://proxy:8080")
        assert client.proxy == "http://proxy:8080"

    def test_encode_api_key(self):
        """Test API key encoding"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")
        encoded = client._encode_api_key()
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_format_error_message(self):
        """Test error message formatting"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        # Test 401 error
        error_msg = client._format_error_message(401, "Unauthorized")
        assert "Authentication failed" in error_msg

        # Test 403 error
        error_msg = client._format_error_message(403, "Forbidden")
        assert "Access denied" in error_msg

        # Test 404 error
        error_msg = client._format_error_message(404, "Not Found")
        assert "Resource not found" in error_msg

        # Test unknown error
        error_msg = client._format_error_message(999, "Unknown Error")
        assert "Unknown Error" in error_msg

    def test_trailing_slash_stripped(self):
        """Test that trailing slash is stripped from base_url"""
        client = OpenProjectClient("https://test.openproject.com/", "test-key")
        assert client.base_url == "https://test.openproject.com"

    def test_headers_set(self):
        """Test that required headers are set"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")
        assert "Authorization" in client.headers
        assert "Content-Type" in client.headers
        assert "Accept" in client.headers
        assert client.headers["Content-Type"] == "application/json"
        assert client.headers["Accept"] == "application/json"


class TestRelationClientMethods:
    """Test cases for work package relation client methods"""

    @pytest.mark.asyncio
    async def test_create_work_package_relation(self):
        """Test create_work_package_relation method"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        mock_result = {
            "id": 42,
            "type": "follows",
            "_embedded": {
                "from": {"id": 1, "subject": "Task A"},
                "to": {"id": 2, "subject": "Task B"},
            },
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_result

            data = {"from_id": 1, "to_id": 2, "type": "follows"}
            result = await client.create_work_package_relation(data)

            assert result["id"] == 42
            assert result["type"] == "follows"
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert "/work_packages/1/relations" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_list_work_package_relations(self):
        """Test list_work_package_relations method"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        mock_result = {
            "_embedded": {
                "elements": [
                    {"id": 1, "type": "follows"},
                    {"id": 2, "type": "blocks"},
                ]
            }
        }

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_result

            result = await client.list_work_package_relations()

            assert len(result["_embedded"]["elements"]) == 2
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert "/relations" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_delete_work_package_relation(self):
        """Test delete_work_package_relation method"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {}

            result = await client.delete_work_package_relation(42)

            assert result is True
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "DELETE"
            assert "/relations/42" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_work_package_relation(self):
        """Test get_work_package_relation method"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        mock_result = {"id": 42, "type": "blocks"}

        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_result

            result = await client.get_work_package_relation(42)

            assert result["id"] == 42
            assert result["type"] == "blocks"
            mock_request.assert_called_once_with("GET", "/relations/42")

    @pytest.mark.asyncio
    async def test_create_relation_missing_from_id(self):
        """Test that create_work_package_relation raises error without from_id"""
        client = OpenProjectClient("https://test.openproject.com", "test-key")

        with pytest.raises(ValueError, match="from_id is required"):
            await client.create_work_package_relation({"to_id": 2, "type": "follows"})


@pytest.mark.asyncio
async def test_async_operations():
    """Test that async operations work correctly"""
    client = OpenProjectClient("https://test.openproject.com", "test-key")

    with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"_type": "Root", "instanceVersion": "13.0.0"}

        result = await client.test_connection()

        assert result["_type"] == "Root"
        assert result["instanceVersion"] == "13.0.0"
        mock_request.assert_called_once_with("GET", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
