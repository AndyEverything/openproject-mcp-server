"""Tests for OpenProjectClient."""


def test_client_import():
    """Verify OpenProjectClient can be imported."""
    from openproject_mcp import OpenProjectClient

    assert OpenProjectClient is not None


def test_client_initialization():
    """Test that OpenProjectClient can be instantiated."""
    from openproject_mcp import OpenProjectClient

    client = OpenProjectClient("https://test.example.com", "test-key")
    assert client.base_url == "https://test.example.com"
    assert client.api_key == "test-key"


def test_client_initialization_strips_trailing_slash():
    """Test that trailing slash is removed from base_url."""
    from openproject_mcp import OpenProjectClient

    client = OpenProjectClient("https://test.example.com/", "test-key")
    assert client.base_url == "https://test.example.com"


def test_client_with_proxy():
    """Test that proxy configuration is accepted."""
    from openproject_mcp import OpenProjectClient

    client = OpenProjectClient(
        "https://test.example.com", "test-key", proxy="http://proxy:8080"
    )
    assert client.proxy == "http://proxy:8080"
