"""Connection and permission checking tools."""

from src.server import mcp, get_client


@mcp.tool
async def test_connection() -> str:
    """Test the connection to the OpenProject API.

    Returns connection status and instance version information.
    This is useful for validating your API credentials and server connectivity.
    """
    try:
        client = get_client()
        result = await client.test_connection()

        text = "✅ API connection successful!\n\n"
        text += f"**Instance Version**: {result.get('instanceVersion', 'Unknown')}\n"
        text += f"**Core Version**: {result.get('coreVersion', 'Unknown')}\n"

        return text

    except Exception as e:
        return f"❌ Connection failed: {str(e)}"


@mcp.tool
async def check_permissions() -> str:
    """Check current user permissions and capabilities.

    Returns information about the authenticated user including their permissions.
    Useful for debugging permission-related issues.
    """
    try:
        client = get_client()
        result = await client.check_permissions()

        if not result:
            return "❌ Failed to retrieve permissions information"

        text = "✅ User Permissions Retrieved\n\n"
        text += f"**Name**: {result.get('name', 'Unknown')}\n"
        text += f"**Email**: {result.get('email', 'N/A')}\n"
        text += f"**Login**: {result.get('login', 'N/A')}\n"
        text += f"**Status**: {result.get('status', 'Unknown')}\n"
        text += f"**Admin**: {'Yes' if result.get('admin') else 'No'}\n"

        return text

    except Exception as e:
        return f"❌ Failed to check permissions: {str(e)}"
