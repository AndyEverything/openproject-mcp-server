"""Work package management tools - Priority CRITICAL tools for 12 users."""

import json
from typing import Optional
from pydantic import BaseModel, Field

from src.server import mcp, get_client
from src.utils.formatting import (
    format_work_package_list,
    format_work_package_detail,
    format_success,
    format_error,
)


# Pydantic models for type-safe input validation
class CreateWorkPackageInput(BaseModel):
    """Input model for creating work packages with validation."""

    project_id: int = Field(..., description="Project ID where work package will be created", gt=0)
    subject: str = Field(..., description="Work package title/subject", min_length=1, max_length=255)
    type_id: int = Field(..., description="Type ID (use list_types to see available types)", gt=0)
    description: Optional[str] = Field(None, description="Detailed description in raw format")
    start_date: Optional[str] = Field(None, description="Start date in ISO format (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Due date in ISO format (YYYY-MM-DD)")
    assignee_id: Optional[int] = Field(None, description="Assignee user ID", gt=0)
    status_id: Optional[int] = Field(None, description="Status ID", gt=0)
    priority_id: Optional[int] = Field(None, description="Priority ID", gt=0)
    version_id: Optional[int] = Field(None, description="Version/milestone ID to assign work package to", gt=0)


class UpdateWorkPackageInput(BaseModel):
    """Input model for updating work packages with validation."""

    work_package_id: int = Field(..., description="Work package ID to update", gt=0)
    subject: Optional[str] = Field(None, description="New subject/title", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="New description")
    type_id: Optional[int] = Field(None, description="New type ID", gt=0)
    status_id: Optional[int] = Field(None, description="New status ID", gt=0)
    priority_id: Optional[int] = Field(None, description="New priority ID", gt=0)
    assignee_id: Optional[int] = Field(None, description="New assignee user ID", gt=0)
    start_date: Optional[str] = Field(None, description="New start date (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="New due date (YYYY-MM-DD)")
    percentage_done: Optional[int] = Field(None, description="Progress percentage (0-100)", ge=0, le=100)
    version_id: Optional[int] = Field(None, description="Version/milestone ID to assign work package to", gt=0)


@mcp.tool
async def list_work_packages(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    active_only: bool = True,
    offset: int = 0,
    page_size: int = 20
) -> str:
    """List work packages (tasks) - CRITICAL tool for viewing all tasks.

    This is one of the most important tools for your 12 users to view and manage their work.

    Args:
        project_id: Optional project ID to filter work packages by project
        assignee_id: Optional user ID to filter work packages by assignee
        active_only: If True, only show work packages with open status (default: True)
        offset: Starting index for pagination (default: 0)
        page_size: Number of results per page (default: 20, max: 100)

    Returns:
        Formatted list of work packages with type, status, priority, assignee, and dates
    """
    try:
        client = get_client()

        # Build filters
        filters_list = []
        if active_only:
            # Filter for open statuses (not closed)
            filters_list.append({"status": {"operator": "o", "values": []}})
        if assignee_id:
            # Filter by assignee
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})

        filters = json.dumps(filters_list) if filters_list else None

        # Validate pagination parameters
        if offset < 0:
            return format_error("offset must be >= 0")
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")

        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            offset=offset,
            page_size=page_size
        )

        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(work_packages))

        # Format response
        text = format_work_package_list(work_packages)

        # Add pagination info
        if total > page_size:
            text += f"\n📄 **Pagination**: Showing {offset + 1}-{offset + len(work_packages)} of {total} total\n"
            text += f"   Use `offset={offset + page_size}` to see next page\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list work packages: {str(e)}")


@mcp.tool
async def create_work_package(input: CreateWorkPackageInput) -> str:
    """Create a new work package (task) - CRITICAL tool for creating tasks.

    This is one of the most important tools for your 12 users to create new work items.

    Args:
        input: Work package data including project_id, subject, type_id, and optional fields

    Returns:
        Success message with created work package ID and details

    Example:
        To create a bug in project 5:
        {
            "project_id": 5,
            "subject": "Fix login issue",
            "type_id": 1,
            "description": "Users cannot login with valid credentials",
            "priority_id": 3,
            "assignee_id": 7,
            "due_date": "2025-01-15"
        }
    """
    try:
        client = get_client()

        # Build data dict for API
        data = {
            "project": input.project_id,
            "subject": input.subject,
            "type": input.type_id,
        }

        # Add optional fields
        if input.description:
            data["description"] = input.description
        if input.priority_id:
            data["priority_id"] = input.priority_id
        if input.assignee_id:
            data["assignee_id"] = input.assignee_id
        if input.version_id:
            data["version_id"] = input.version_id

        # Add date fields (use camelCase for API)
        if input.start_date:
            data["startDate"] = input.start_date
        if input.due_date:
            data["dueDate"] = input.due_date

        # Create work package
        result = await client.create_work_package(data)

        # Format success response
        wp_id = result.get("id")
        wp_subject = result.get("subject")

        text = format_success(f"Work package #{wp_id} created successfully!\n\n")
        text += f"**Subject**: {wp_subject}\n"

        # Add embedded data
        embedded = result.get("_embedded", {})
        if "type" in embedded:
            text += f"**Type**: {embedded['type'].get('name', 'Unknown')}\n"
        if "status" in embedded:
            text += f"**Status**: {embedded['status'].get('name', 'Unknown')}\n"
        if "priority" in embedded:
            text += f"**Priority**: {embedded['priority'].get('name', 'Unknown')}\n"
        if "assignee" in embedded:
            text += f"**Assignee**: {embedded['assignee'].get('name', 'Unassigned')}\n"

        if result.get('startDate'):
            text += f"**Start Date**: {result['startDate']}\n"
        if result.get('dueDate'):
            text += f"**Due Date**: {result['dueDate']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create work package: {str(e)}")


@mcp.tool
async def update_work_package(input: UpdateWorkPackageInput) -> str:
    """Update an existing work package (task) - CRITICAL tool for updating tasks.

    This is one of the most important tools for your 12 users to update work items,
    including changing status, assignee, dates, and progress.

    Args:
        input: Work package update data including work_package_id and fields to update

    Returns:
        Success message with updated work package details

    Example:
        To update work package #123 status and assignee:
        {
            "work_package_id": 123,
            "status_id": 5,
            "assignee_id": 7,
            "percentage_done": 50,
            "due_date": "2025-01-20"
        }
    """
    try:
        client = get_client()

        # Build data dict for API (only include provided fields)
        data = {}

        if input.subject is not None:
            data["subject"] = input.subject
        if input.description is not None:
            data["description"] = input.description
        if input.type_id is not None:
            data["type_id"] = input.type_id
        if input.status_id is not None:
            data["status_id"] = input.status_id
        if input.priority_id is not None:
            data["priority_id"] = input.priority_id
        if input.assignee_id is not None:
            data["assignee_id"] = input.assignee_id
        if input.percentage_done is not None:
            data["percentage_done"] = input.percentage_done
        if input.version_id is not None:
            data["version_id"] = input.version_id

        # Add date fields (use camelCase for API)
        if input.start_date is not None:
            data["startDate"] = input.start_date
        if input.due_date is not None:
            data["dueDate"] = input.due_date

        if not data:
            return format_error("No fields provided to update")

        # Update work package
        result = await client.update_work_package(input.work_package_id, data)

        # Format success response
        wp_id = result.get("id")
        wp_subject = result.get("subject")

        text = format_success(f"Work package #{wp_id} updated successfully!\n\n")
        text += f"**Subject**: {wp_subject}\n"

        # Add embedded data
        embedded = result.get("_embedded", {})
        if "type" in embedded:
            text += f"**Type**: {embedded['type'].get('name', 'Unknown')}\n"
        if "status" in embedded:
            text += f"**Status**: {embedded['status'].get('name', 'Unknown')}\n"
        if "priority" in embedded:
            text += f"**Priority**: {embedded['priority'].get('name', 'Unknown')}\n"
        if "assignee" in embedded:
            text += f"**Assignee**: {embedded['assignee'].get('name', 'Unassigned')}\n"

        if result.get('startDate'):
            text += f"**Start Date**: {result['startDate']}\n"
        if result.get('dueDate'):
            text += f"**Due Date**: {result['dueDate']}\n"
        if 'percentageDone' in result:
            text += f"**Progress**: {result['percentageDone']}%\n"

        return text

    except Exception as e:
        return format_error(f"Failed to update work package: {str(e)}")


@mcp.tool
async def delete_work_package(work_package_id: int) -> str:
    """Delete a work package (task).

    Args:
        work_package_id: ID of the work package to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()

        success = await client.delete_work_package(work_package_id)

        if success:
            return format_success(f"Work package #{work_package_id} deleted successfully")
        else:
            return format_error(f"Failed to delete work package #{work_package_id}")

    except Exception as e:
        return format_error(f"Failed to delete work package: {str(e)}")


@mcp.tool
async def list_types(project_id: Optional[int] = None) -> str:
    """List available work package types (Bug, Task, Feature, etc.).

    Args:
        project_id: Optional project ID to filter types by project

    Returns:
        List of work package types with IDs
    """
    try:
        client = get_client()

        result = await client.get_types(project_id)
        types = result.get("_embedded", {}).get("elements", [])

        if not types:
            return "No work package types found."

        text = "✅ **Available Work Package Types:**\n\n"
        for type_item in types:
            text += f"- **{type_item.get('name', 'Unnamed')}** (ID: {type_item.get('id', 'N/A')})\n"
            if type_item.get("isDefault"):
                text += "  ✓ Default type\n"
            if type_item.get("isMilestone"):
                text += "  ✓ Milestone\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list work package types: {str(e)}")


@mcp.tool
async def list_statuses() -> str:
    """List available work package statuses (New, In Progress, Closed, etc.).

    Returns:
        List of work package statuses with IDs and properties
    """
    try:
        client = get_client()

        result = await client.get_statuses()
        statuses = result.get("_embedded", {}).get("elements", [])

        if not statuses:
            return "No statuses found."

        text = "✅ **Available Work Package Statuses:**\n\n"
        for status in statuses:
            text += f"- **{status.get('name', 'Unnamed')}** (ID: {status.get('id', 'N/A')})\n"
            text += f"  Position: {status.get('position', 'N/A')}\n"
            if status.get("isDefault"):
                text += "  ✓ Default status\n"
            if status.get("isClosed"):
                text += "  ✓ Closed status\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list work package statuses: {str(e)}")


@mcp.tool
async def list_priorities() -> str:
    """List available work package priorities (Low, Normal, High, Immediate).

    Returns:
        List of work package priorities with IDs
    """
    try:
        client = get_client()

        result = await client.get_priorities()
        priorities = result.get("_embedded", {}).get("elements", [])

        if not priorities:
            return "No priorities found."

        text = "✅ **Available Work Package Priorities:**\n\n"
        for priority in priorities:
            text += f"- **{priority.get('name', 'Unnamed')}** (ID: {priority.get('id', 'N/A')})\n"
            text += f"  Position: {priority.get('position', 'N/A')}\n"
            if priority.get("isDefault"):
                text += "  ✓ Default priority\n"
            if priority.get("isActive"):
                text += "  ✓ Active\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list work package priorities: {str(e)}")


@mcp.tool
async def assign_work_package(work_package_id: int, assignee_id: int) -> str:
    """Assign a work package (task) to a user.

    This is a convenience tool that makes it easy to assign tasks to team members.
    It's equivalent to updating the work package's assignee field.

    Args:
        work_package_id: ID of the work package to assign
        assignee_id: ID of the user to assign the work package to

    Returns:
        Success message with updated work package details

    Example:
        To assign work package #123 to user #7:
        {
            "work_package_id": 123,
            "assignee_id": 7
        }
    """
    try:
        client = get_client()

        # Update work package with new assignee
        data = {"assignee_id": assignee_id}
        result = await client.update_work_package(work_package_id, data)

        # Format success response
        wp_id = result.get("id")
        wp_subject = result.get("subject")

        text = format_success(f"Work package #{wp_id} assigned successfully!\n\n")
        text += f"**Subject**: {wp_subject}\n"

        embedded = result.get("_embedded", {})
        if "assignee" in embedded:
            assignee_name = embedded["assignee"].get("name", "Unknown")
            text += f"**Assigned to**: {assignee_name}\n"
        
        if "type" in embedded:
            text += f"**Type**: {embedded['type'].get('name', 'Unknown')}\n"
        if "status" in embedded:
            text += f"**Status**: {embedded['status'].get('name', 'Unknown')}\n"
        if "priority" in embedded:
            text += f"**Priority**: {embedded['priority'].get('name', 'Unknown')}\n"

        if result.get('dueDate'):
            text += f"**Due Date**: {result['dueDate']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to assign work package: {str(e)}")


@mcp.tool
async def unassign_work_package(work_package_id: int) -> str:
    """Unassign a work package (remove assignee from task).

    This removes the current assignee from a work package, making it unassigned.

    Args:
        work_package_id: ID of the work package to unassign

    Returns:
        Success message confirming the work package is now unassigned
    """
    try:
        client = get_client()

        # Update work package with null assignee (unassign)
        # Note: We need to use the API directly since setting to None might not work
        result = await client.update_work_package(work_package_id, {"assignee_id": None})

        wp_id = result.get("id")
        wp_subject = result.get("subject")

        text = format_success(f"Work package #{wp_id} unassigned successfully!\n\n")
        text += f"**Subject**: {wp_subject}\n"
        text += f"**Assigned to**: Unassigned\n"

        embedded = result.get("_embedded", {})
        if "type" in embedded:
            text += f"**Type**: {embedded['type'].get('name', 'Unknown')}\n"
        if "status" in embedded:
            text += f"**Status**: {embedded['status'].get('name', 'Unknown')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to unassign work package: {str(e)}")


@mcp.tool
async def add_work_package_comment(
    work_package_id: int,
    comment: str,
    internal: bool = False
) -> str:
    """Add a comment/activity to a work package - CRITICAL for reporting and communication.

    This allows users to add progress updates, notes, or communicate within a task.
    Comments support markdown formatting and can be marked as internal (team-only).

    Args:
        work_package_id: ID of the work package to comment on
        comment: Comment text (supports markdown formatting)
        internal: If True, comment is only visible to team members (default: False)

    Returns:
        Success message with the created comment details

    Example:
        To add a progress update:
        {
            "work_package_id": 123,
            "comment": "## Progress Update\\n\\n- Completed database migration\\n- Started API integration",
            "internal": false
        }
    """
    try:
        client = get_client()

        result = await client.add_work_package_comment(
            work_package_id=work_package_id,
            comment=comment,
            internal=internal
        )

        activity_id = result.get("id", "N/A")
        comment_data = result.get("comment", {})
        comment_html = comment_data.get("html", "")
        comment_raw = comment_data.get("raw", comment)

        text = format_success(f"Comment added to work package #{work_package_id} successfully!\n\n")
        text += f"**Activity ID**: {activity_id}\n"
        text += f"**Internal**: {'Yes' if internal else 'No'}\n"
        text += f"**Comment**: {comment_raw[:200]}{'...' if len(comment_raw) > 200 else ''}\n"

        # Show author info if available
        links = result.get("_links", {})
        user_link = links.get("user", {})
        if user_link:
            text += f"**Posted by**: {user_link.get('title', 'Unknown')}\n"

        if result.get("createdAt"):
            text += f"**Created**: {result['createdAt']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to add comment: {str(e)}")


@mcp.tool
async def list_work_package_activities(work_package_id: int) -> str:
    """List all activities (comments, changes) for a work package.

    This shows the activity history including comments, status changes, and field updates.
    Useful for reviewing task history and communication.

    Args:
        work_package_id: ID of the work package

    Returns:
        Formatted list of activities with details
    """
    try:
        client = get_client()

        result = await client.get_work_package_activities(work_package_id)
        activities = result.get("_embedded", {}).get("elements", [])

        if not activities:
            return f"No activities found for work package #{work_package_id}."

        text = format_success(f"Work Package #{work_package_id} Activities ({len(activities)}):\n\n")

        for activity in activities:
            activity_id = activity.get("id", "N/A")
            activity_type = activity.get("_type", "Activity")
            created_at = activity.get("createdAt", "Unknown")

            # Get user from _links
            links = activity.get("_links", {})
            user_link = links.get("user", {})
            user_name = user_link.get("title", "Unknown")

            text += f"**Activity #{activity_id}** - {activity_type}\n"
            text += f"  By: {user_name}\n"
            text += f"  Date: {created_at}\n"

            # Show comment if available
            comment_data = activity.get("comment", {})
            if comment_data:
                comment_raw = comment_data.get("raw", "")
                if comment_raw:
                    # Truncate long comments
                    comment_preview = comment_raw[:150]
                    if len(comment_raw) > 150:
                        comment_preview += "..."
                    text += f"  Comment: {comment_preview}\n"

            # Show if internal
            if activity.get("internal"):
                text += f"  🔒 Internal comment\n"

            # Show details of changes (if available)
            details = activity.get("details", [])
            if details:
                text += f"  Changes:\n"
                for detail in details[:3]:  # Show max 3 changes
                    text += f"    - {detail}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list activities: {str(e)}")
