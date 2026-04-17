"""Basic smoke tests for openproject-mcp-server package."""


def test_client_module_import():
    """Verify src.client module can be imported."""
    from src import client

    assert client is not None


def test_version_defined():
    """Verify version is defined in src.client."""
    from src.client import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)


def test_cli_entry_point():
    """Verify CLI entry point function exists in src.server."""
    from src.server import main

    assert callable(main)
