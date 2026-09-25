"""Work package watcher tools."""

from typing import Any, Dict, List

from src.server import mcp, get_client
from src.utils.formatting import format_success
from src.utils.rendering import VALID_FORMATS, format_api_error, render


def watchers_from_collection(collection: Dict) -> List[Dict[str, Any]]:
    elements = ((collection or {}).get("_embedded") or {}).get("elements") or []
    return [
        {"id": user.get("id"), "name": user.get("name"), "login": user.get("login")}
        for user in elements
    ]


def watchers_to_markdown(data: Dict[str, Any]) -> str:
    watchers = data["watchers"]
    if not watchers:
        return f"Work package #{data['work_package_id']} has no watchers."
    lines = [f"✅ **Obserwatorzy zadania #{data['work_package_id']} ({len(watchers)}):**", ""]
    lines += [f"- 👀 **{user.get('name')}** (ID {user.get('id')})" for user in watchers]
    return "\n".join(lines)


@mcp.tool
async def list_watchers(work_package_id: int, format: str = "markdown") -> str:
    """List users watching a work package.

    Args:
        work_package_id: Work package ID
        format: "markdown" (default) or "json"
    """
    if (format or "").strip().lower() not in VALID_FORMATS:
        return render(None, format, str)
    try:
        result = await get_client().get_watchers(work_package_id)
    except Exception as e:
        return format_api_error(e)
    data = {"work_package_id": work_package_id, "watchers": watchers_from_collection(result)}
    return render(data, format, watchers_to_markdown)


@mcp.tool
async def add_watcher(work_package_id: int, user_id: int) -> str:
    """Add a user as a watcher of a work package.

    Args:
        work_package_id: Work package ID
        user_id: ID of the user to add as watcher
    """
    try:
        await get_client().add_watcher(work_package_id, user_id)
    except Exception as e:
        return format_api_error(e)
    return format_success(f"User #{user_id} is now watching work package #{work_package_id}")


@mcp.tool
async def remove_watcher(work_package_id: int, user_id: int) -> str:
    """Remove a user from the watchers of a work package.

    Args:
        work_package_id: Work package ID
        user_id: ID of the watcher to remove
    """
    try:
        await get_client().remove_watcher(work_package_id, user_id)
    except Exception as e:
        return format_api_error(e)
    return format_success(f"User #{user_id} removed from watchers of work package #{work_package_id}")
