"""
OpenProject MCP Server - FastMCP Implementation

Main server file that initializes FastMCP and registers all tools.
"""

import os
import logging
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

try:
    base_url = os.getenv("OPENPROJECT_URL")
    api_key = os.getenv("OPENPROJECT_API_KEY")
    proxy = os.getenv("OPENPROJECT_PROXY")

    if not base_url or not api_key:
        raise ValueError(
            "Missing required environment variables: OPENPROJECT_URL and OPENPROJECT_API_KEY must be set"
        )

    _client = OpenProjectClient(
        base_url=base_url,
        api_key=api_key,
        proxy=proxy
    )

    logger.info(f"✅ OpenProject MCP Server initialized")
    logger.info(f"   Server: {base_url}")
    logger.info(f"   Proxy: {proxy if proxy else 'None'}")

except Exception as e:
    logger.error(f"❌ Failed to initialize OpenProject client: {e}")
    raise


# Dependency injection helper for tools
def get_client():
    """Get OpenProject client instance."""
    return _client


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

