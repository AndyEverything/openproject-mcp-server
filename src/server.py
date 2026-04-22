"""
OpenProject MCP Server - FastMCP Implementation

Main server file that initializes FastMCP and registers all tools.
"""

import os
import logging
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

from src.client import OpenProjectClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="openproject-mcp"
)

# Initialize OpenProject client as global variable
_client = None

# ContextVars for per-user API key support in HTTP transport
_http_mode: ContextVar[bool] = ContextVar("http_mode", default=False)
_request_api_key: ContextVar[Optional[str]] = ContextVar("request_api_key", default=None)

try:
    base_url = os.getenv("OPENPROJECT_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY")
    proxy = os.getenv("OPENPROJECT_PROXY")
    readonly = os.getenv("READ_ONLY_MODE", "false").strip().lower() == "true"

    if not base_url or not api_key:
        raise ValueError(
            "Missing required environment variables: OPENPROJECT_URL and OPENPROJECT_API_KEY must be set"
        )

    _client = OpenProjectClient(
        base_url=base_url,
        api_key=api_key,
        proxy=proxy,
        readonly=readonly,
    )

    # Note: in HTTP transport mode, _client.api_key is never used for API calls.
    # get_client() reads base_url/proxy/readonly from _client but creates an ephemeral
    # client with the per-user key from the X-OpenProject-Api-Key header.
    # OPENPROJECT_API_KEY in .env is still required at startup for config resolution.

    logger.info(f"✅ OpenProject MCP Server initialized")
    logger.info(f"   Server: {base_url}")
    logger.info(f"   Proxy: {proxy if proxy else 'None'}")
    if readonly:
        logger.warning("⚠️  READ-ONLY mode: write operations are blocked")
    else:
        logger.info("   Mode: Read-Write")

except Exception as e:
    logger.error(f"❌ Failed to initialize OpenProject client: {e}")
    raise


# Dependency injection helpers for tools
def get_client() -> "OpenProjectClient":
    """Return the OpenProjectClient for the current request context.

    HTTP transport: requires X-OpenProject-Api-Key header — returns ephemeral client.
    STDIO transport: returns the global shared client.
    """
    if _http_mode.get():
        api_key = _request_api_key.get()
        if not api_key:
            raise ValueError(
                "X-OpenProject-Api-Key header is required for HTTP transport. "
                "Add --header 'X-OpenProject-Api-Key: YOUR_TOKEN' to your mcp-remote config."
            )
        if _client is None:
            raise RuntimeError("OpenProjectClient was not initialised — check startup logs")
        return OpenProjectClient(
            base_url=_client.base_url,
            api_key=api_key,
            proxy=_client.proxy,
            readonly=_client.readonly,
        )
    return _client


def is_readonly() -> bool:
    """Return True if the server is running in read-only mode (READ_ONLY_MODE=true)."""
    return _client.readonly if _client else False


# Import ALL tool modules (decorators auto-register tools)
logger.info("Loading tool modules...")

try:
    # Phase 1: Priority tools (7 tools)
    from src.tools import connection      # 2 tools: test_connection, check_permissions
    from src.tools import work_packages   # 7 tools: list, create, update, delete, list_types, list_statuses, list_priorities
    from src.tools import projects        # 5 tools: list, get, create, update, delete

    # Phase 2: Additional tools (28 tools)
    from src.tools import users           # 6 tools: list_users, get_user, list_roles, get_role, list_project_members, list_user_projects
    from src.tools import memberships     # 5 tools: list, get, create, update, delete
    from src.tools import hierarchy       # 3 tools: set_parent, remove_parent, list_children
    from src.tools import relations       # 5 tools: create, list, get, update, delete
    from src.tools import time_entries    # 5 tools: list, create, update, delete, list_activities
    from src.tools import versions        # 2 tools: list, create
    from src.tools import weekly_reports   # 4 tools: generate_weekly_report, get_report_data, generate_this_week_report, generate_last_week_report
    from src.tools import news             # 5 tools: list_news, create_news, get_news, update_news, delete_news

    logger.info("✅ All 49 tool modules loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  Some tool modules failed to import: {e}")
    raise

