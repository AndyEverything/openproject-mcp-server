"""Sprint and backlog management tools (OpenProject 17.3+)."""

import json
from typing import Optional

from src.server import mcp, get_client
from src.utils.formatting import format_work_package_list, format_success, format_error


def _format_sprint(sprint: dict) -> str:
    """Format a single sprint for display."""
    sid = sprint.get("id", "N/A")
    name = sprint.get("name", "Unnamed")
    status = sprint.get("status", "unknown")
    start = sprint.get("startDate", "—")
    finish = sprint.get("finishDate", "—")

    status_icon = {"in_planning": "📋", "active": "🟢", "completed": "✅"}.get(status, "❓")

    workspace = sprint.get("_links", {}).get("definingWorkspace", {}).get("title", "")

    text = f"{status_icon} **{name}** (ID: {sid})\n"
    text += f"  Status: {status}\n"
    if workspace:
        text += f"  Project: {workspace}\n"
    if start != "—" or finish != "—":
        text += f"  Dates: {start} → {finish}\n"
    if sprint.get("description", {}).get("raw"):
        text += f"  Description: {sprint['description']['raw'][:120]}\n"
    return text


@mcp.tool
async def list_sprints(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    offset: int = 0,
    page_size: int = 25,
) -> str:
    """List sprints, optionally scoped to a project.

    Requires the Backlogs module to be enabled on the project (OpenProject 17.3+).

    Args:
        project_id: Optional project ID to list sprints for a specific project.
                    If omitted, lists all sprints visible to the current user.
        status: Filter by sprint status: 'in_planning', 'active', or 'completed'.
                If omitted, all statuses are returned.
        offset: Pagination offset (default: 0)
        page_size: Results per page (default: 25, max: 100)

    Returns:
        Formatted list of sprints with status, dates, and project info.

    Examples:
        List active sprints in project #5:
        {"project_id": 5, "status": "active"}

        List all sprints across all projects:
        {}
    """
    try:
        client = get_client()

        filters_list = []
        if status:
            valid = {"in_planning", "active", "completed"}
            if status not in valid:
                return format_error(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid))}")
            filters_list.append({"status": {"operator": "=", "values": [status]}})

        filters = json.dumps(filters_list) if filters_list else None

        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")

        result = await client.get_sprints(
            project_id=project_id,
            filters=filters,
            offset=offset,
            page_size=page_size,
        )

        sprints = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(sprints))

        if not sprints:
            scope = f"project #{project_id}" if project_id else "all projects"
            status_note = f" with status '{status}'" if status else ""
            return f"No sprints found for {scope}{status_note}."

        scope_label = f"Project #{project_id}" if project_id else "All Projects"
        status_label = f" ({status})" if status else ""
        text = f"🏃 **Sprints — {scope_label}{status_label}** ({total} total)\n\n"

        for sprint in sprints:
            text += _format_sprint(sprint) + "\n"

        if total > page_size:
            text += f"📄 Showing {offset + 1}–{offset + len(sprints)} of {total}. "
            text += f"Use `offset={offset + page_size}` for next page.\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list sprints: {str(e)}")


@mcp.tool
async def get_sprint(sprint_id: int) -> str:
    """Get details of a single sprint by ID.

    Args:
        sprint_id: The sprint ID

    Returns:
        Full sprint details including status, dates, and project.
    """
    try:
        client = get_client()
        sprint = await client.get_sprint(sprint_id)

        text = f"🏃 **Sprint Details**\n\n"
        text += _format_sprint(sprint)
        text += f"\n**Created**: {sprint.get('createdAt', 'N/A')}\n"
        text += f"**Updated**: {sprint.get('updatedAt', 'N/A')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get sprint #{sprint_id}: {str(e)}")


@mcp.tool
async def list_sprint_work_packages(
    sprint_id: int,
    project_id: Optional[int] = None,
    active_only: bool = False,
    page_size: int = 50,
) -> str:
    """List all work packages assigned to a specific sprint.

    Args:
        sprint_id: The sprint ID to list work packages for
        project_id: Optional project ID to narrow the search
        active_only: If True, only return open (non-closed) work packages
        page_size: Number of results per page (default: 50, max: 100)

    Returns:
        Formatted list of work packages in the sprint, with story points shown.

    Examples:
        List all work packages in sprint #12:
        {"sprint_id": 12}

        List open work packages in sprint #12 for project #5:
        {"sprint_id": 12, "project_id": 5, "active_only": true}
    """
    try:
        client = get_client()

        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")

        filters_list = [
            {"sprint": {"operator": "=", "values": [str(sprint_id)]}}
        ]

        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})

        filters = json.dumps(filters_list)

        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size,
        )

        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(work_packages))

        if not work_packages:
            return f"No work packages found in sprint #{sprint_id}."

        total_sp = sum(wp.get("storyPoints") or 0 for wp in work_packages)
        text = f"📋 **Sprint #{sprint_id} Work Packages** ({total} total"
        if total_sp:
            text += f", {total_sp} story points"
        text += ")\n\n"

        text += _format_wp_list_with_sprint_fields(work_packages)

        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total}.\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list sprint work packages: {str(e)}")


@mcp.tool
async def list_backlog_work_packages(
    project_id: int,
    type_ids: Optional[str] = None,
    priority_ids: Optional[str] = None,
    active_only: bool = True,
    page_size: int = 50,
) -> str:
    """List work packages in the product backlog (not assigned to any sprint).

    The product backlog (Inbox) contains all work packages in a project that
    are not yet assigned to a sprint. Use this for sprint planning.

    Args:
        project_id: Project ID to list the backlog for
        type_ids: Optional comma-separated type IDs to filter by (e.g. "1,2")
        priority_ids: Optional comma-separated priority IDs to filter by
        active_only: If True, only return open work packages (default: True)
        page_size: Number of results per page (default: 50, max: 100)

    Returns:
        Formatted backlog list with story points, sorted by backlog position.

    Examples:
        List full backlog for project #5:
        {"project_id": 5}

        List only high-priority bugs in backlog:
        {"project_id": 5, "type_ids": "1", "priority_ids": "3"}
    """
    try:
        client = get_client()

        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")

        filters_list = [
            {"sprint": {"operator": "!*", "values": []}}
        ]

        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})

        if type_ids:
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})

        if priority_ids:
            priority_list = [p.strip() for p in priority_ids.split(",") if p.strip()]
            if priority_list:
                filters_list.append({"priority": {"operator": "=", "values": priority_list}})

        filters = json.dumps(filters_list)

        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size,
        )

        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(work_packages))

        if not work_packages:
            return f"Product backlog for project #{project_id} is empty."

        total_sp = sum(wp.get("storyPoints") or 0 for wp in work_packages)
        text = f"📥 **Product Backlog — Project #{project_id}** ({total} items"
        if total_sp:
            text += f", {total_sp} story points"
        text += ")\n\n"

        text += _format_wp_list_with_sprint_fields(work_packages)

        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total}. "
            text += "Use `list_work_packages` with sprint filter for pagination.\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list backlog: {str(e)}")


def _format_wp_list_with_sprint_fields(work_packages: list) -> str:
    """Format work package list showing story points and sprint alongside standard fields."""
    text = ""
    for wp in work_packages:
        wp_id = wp.get("id", "N/A")
        subject = wp.get("subject", "Unnamed")
        story_points = wp.get("storyPoints")
        position = wp.get("position")

        embedded = wp.get("_embedded", {})
        status_name = embedded.get("status", {}).get("name", "—")
        priority_name = embedded.get("priority", {}).get("name", "—")
        assignee_name = embedded.get("assignee", {}).get("name", "Unassigned")
        type_name = embedded.get("type", {}).get("name", "")

        sprint_link = wp.get("_links", {}).get("sprint", {})
        sprint_title = sprint_link.get("title", "") if sprint_link else ""

        sp_badge = f" [{story_points} SP]" if story_points else ""
        pos_badge = f" #{position}" if position is not None else ""
        type_badge = f"[{type_name}] " if type_name else ""

        text += f"**#{wp_id}**{pos_badge}{sp_badge} {type_badge}{subject}\n"
        text += f"  Status: {status_name} | Priority: {priority_name} | Assignee: {assignee_name}\n"
        if sprint_title:
            text += f"  Sprint: {sprint_title}\n"
        if wp.get("dueDate"):
            text += f"  Due: {wp['dueDate']}\n"
        text += "\n"

    return text
