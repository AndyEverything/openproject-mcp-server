"""Basic smoke tests for openproject-mcp package."""


def test_import():
    """Verify package can be imported."""
    import openproject_mcp

    assert openproject_mcp is not None


def test_version():
    """Verify package version is defined."""
    import openproject_mcp

    assert hasattr(openproject_mcp, "__version__")
    assert openproject_mcp.__version__ is not None
    assert openproject_mcp.__version__ == "1.0.2"


def test_cli_entry():
    """Verify CLI entry point exists."""
    from openproject_mcp import cli_entry

    assert callable(cli_entry)
