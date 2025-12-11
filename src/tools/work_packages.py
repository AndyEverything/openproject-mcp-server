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
    # Existing parameters (backward compatible)
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    active_only: bool = True,
    offset: int = 0,
    page_size: int = 20,
    
    # NEW: Multi-value filters (comma-separated IDs)
    priority_ids: Optional[str] = None,
    type_ids: Optional[str] = None,
    status_ids: Optional[str] = None,
    version_ids: Optional[str] = None,
    
    # NEW: Date filters
    due_before: Optional[str] = None,  # YYYY-MM-DD
    due_after: Optional[str] = None,   # YYYY-MM-DD
    created_after: Optional[str] = None,  # YYYY-MM-DD
    updated_after: Optional[str] = None,  # YYYY-MM-DD
    
    # NEW: Boolean filters
    unassigned_only: bool = False,
    overdue_only: bool = False,
    
    # NEW: Percentage filters
    percentage_done_min: Optional[int] = None,
    percentage_done_max: Optional[int] = None,
    
    # NEW: Additional filters
    author_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    no_parent_only: bool = False
) -> str:
    """List work packages (tasks) with advanced filtering - CRITICAL tool for flexible task search.
    
    This is the most powerful search tool with 20+ filter parameters for finding exactly
    the tasks you need. Supports multiple filters combined with AND logic.
    
    Args:
        # Basic filters
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee (ignored if unassigned_only=True)
        active_only: If True, only show open work packages (default: True)
        offset: Starting index for pagination (default: 0)
        page_size: Number of results per page (default: 20, max: 100)
        
        # Multi-value filters (comma-separated IDs)
        priority_ids: Comma-separated priority IDs (e.g., "3,4" for high+urgent)
        type_ids: Comma-separated type IDs (e.g., "1,2" for bugs+features)
        status_ids: Comma-separated status IDs (overrides active_only if provided)
        version_ids: Comma-separated version/sprint IDs
        
        # Date filters
        due_before: Due date before this date (YYYY-MM-DD format)
        due_after: Due date after this date (YYYY-MM-DD format)
        created_after: Created after this date (YYYY-MM-DD format)
        updated_after: Updated after this date (YYYY-MM-DD format)
        
        # Boolean filters
        unassigned_only: If True, only show tasks without assignee
        overdue_only: If True, only show tasks past their due date
        
        # Percentage filters
        percentage_done_min: Minimum completion percentage (0-100)
        percentage_done_max: Maximum completion percentage (0-100)
        
        # Additional filters
        author_id: Filter by task creator/author
        parent_id: Filter by parent work package ID (child tasks)
        no_parent_only: If True, only show top-level tasks (no parent)
    
    Returns:
        Formatted list of work packages matching all specified filters
        
    Examples:
        Find high-priority bugs due this week:
        {
            "priority_ids": "3",
            "type_ids": "1",
            "due_before": "2025-12-15",
            "due_after": "2025-12-08"
        }
        
        Find overdue unassigned tasks in project #5:
        {
            "project_id": 5,
            "unassigned_only": true,
            "overdue_only": true
        }
        
        Find nearly complete tasks (>80%):
        {
            "percentage_done_min": 80,
            "active_only": true
        }
    """
    try:
        from datetime import date, datetime
        
        client = get_client()

        # Build filters list
        filters_list = []
        
        # === STATUS FILTER ===
        # Priority: status_ids > overdue_only > active_only
        if status_ids:
            # Explicit status IDs provided
            status_list = [s.strip() for s in status_ids.split(",") if s.strip()]
            if status_list:
                filters_list.append({"status": {"operator": "=", "values": status_list}})
        elif overdue_only:
            # Overdue mode: must be open
            filters_list.append({"status": {"operator": "o", "values": []}})
        elif active_only:
            # Open status only
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            # All statuses (open + closed)
            filters_list.append({"status": {"operator": "*", "values": []}})
        
        # === ASSIGNEE FILTER ===
        if unassigned_only:
            # Unassigned takes priority over assignee_id
            filters_list.append({"assignee": {"operator": "!*", "values": []}})
        elif assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        # === PRIORITY FILTER ===
        if priority_ids:
            priority_list = [p.strip() for p in priority_ids.split(",") if p.strip()]
            if priority_list:
                filters_list.append({"priority": {"operator": "=", "values": priority_list}})
        
        # === TYPE FILTER ===
        if type_ids:
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})
        
        # === VERSION FILTER ===
        if version_ids:
            version_list = [v.strip() for v in version_ids.split(",") if v.strip()]
            if version_list:
                filters_list.append({"version": {"operator": "=", "values": version_list}})
        
        # === DATE FILTERS ===
        # Overdue filter (special case)
        if overdue_only:
            # Due date < today
            today = date.today().isoformat()
            filters_list.append({"dueDate": {"operator": "<>d", "values": ["2000-01-01", today]}})
        else:
            # Regular due date filters
            if due_before and due_after:
                # Date range
                filters_list.append({"dueDate": {"operator": "<>d", "values": [due_after, due_before]}})
            elif due_before:
                # Before specific date (use range from old date to due_before)
                filters_list.append({"dueDate": {"operator": "<>d", "values": ["2000-01-01", due_before]}})
            elif due_after:
                # After specific date (use range from due_after to far future)
                filters_list.append({"dueDate": {"operator": "<>d", "values": [due_after, "2099-12-31"]}})
        
        # Created after filter
        if created_after:
            # Use date range from created_after to far future
            filters_list.append({"createdAt": {"operator": "<>d", "values": [created_after, "2099-12-31"]}})
        
        # Updated after filter
        if updated_after:
            # Use date range from updated_after to far future
            filters_list.append({"updatedAt": {"operator": "<>d", "values": [updated_after, "2099-12-31"]}})
        
        # === PERCENTAGE FILTER ===
        if percentage_done_min is not None and percentage_done_max is not None:
            # Range filter
            if percentage_done_min > percentage_done_max:
                return format_error("percentage_done_min cannot be greater than percentage_done_max")
            # Use two filters: >= min AND <= max
            filters_list.append({"percentageDone": {"operator": ">=", "values": [str(percentage_done_min)]}})
            filters_list.append({"percentageDone": {"operator": "<=", "values": [str(percentage_done_max)]}})
        elif percentage_done_min is not None:
            # Minimum only
            if percentage_done_min < 0 or percentage_done_min > 100:
                return format_error("percentage_done_min must be between 0 and 100")
            filters_list.append({"percentageDone": {"operator": ">=", "values": [str(percentage_done_min)]}})
        elif percentage_done_max is not None:
            # Maximum only
            if percentage_done_max < 0 or percentage_done_max > 100:
                return format_error("percentage_done_max must be between 0 and 100")
            filters_list.append({"percentageDone": {"operator": "<=", "values": [str(percentage_done_max)]}})
        
        # === AUTHOR FILTER ===
        if author_id:
            filters_list.append({"author": {"operator": "=", "values": [str(author_id)]}})
        
        # === PARENT FILTER ===
        if no_parent_only:
            # Top-level tasks only (no parent)
            filters_list.append({"parent": {"operator": "!*", "values": []}})
        elif parent_id:
            # Specific parent
            filters_list.append({"parent": {"operator": "=", "values": [str(parent_id)]}})
        
        # Convert filters to JSON
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
async def search_work_packages(
    query: str,
    project_id: Optional[int] = None,
    active_only: bool = True,
    offset: int = 0,
    page_size: int = 20
) -> str:
    """Search work packages by subject or ID - Fast search without pagination.

    This tool provides quick search functionality using OpenProject's server-side filtering.
    Use this when you need to find specific tasks by name or ID instead of listing all tasks.

    Args:
        query: Search text to match against work package subject or ID
        project_id: Optional project ID to limit search to a specific project
        active_only: If True, only search open work packages (default: True)
        offset: Starting index for pagination (default: 0)
        page_size: Number of results per page (default: 20, max: 100)

    Returns:
        Formatted list of matching work packages

    Example:
        To search for tasks containing "login":
        {
            "query": "login"
        }

        To search by work package ID:
        {
            "query": "123"
        }
    """
    try:
        client = get_client()

        # Validate input
        if not query or not query.strip():
            return format_error("Search query cannot be empty")

        # Build filters
        filters_list = []

        # Add subjectOrId filter for search
        filters_list.append({
            "subjectOrId": {
                "operator": "**",
                "values": [query.strip()]
            }
        })

        # Add active_only filter if requested (same fix as list_work_packages)
        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            # Explicitly include ALL statuses (open + closed)
            filters_list.append({"status": {"operator": "*", "values": []}})

        filters = json.dumps(filters_list)

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

        # Format response with search context
        if not work_packages:
            text = f"🔍 No work packages found matching '{query}'"
            if project_id:
                text += f" in project #{project_id}"
            if active_only:
                text += " (active only)"
            return text

        text = f"🔍 **Search Results for '{query}'**: Found {total} work package(s)\n\n"
        text += format_work_package_list(work_packages)

        # Add pagination info
        if total > page_size:
            text += f"\n📄 **Pagination**: Showing {offset + 1}-{offset + len(work_packages)} of {total} total\n"
            text += f"   Use `offset={offset + page_size}` to see next page\n"

        return text

    except Exception as e:
        return format_error(f"Failed to search work packages: {str(e)}")


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


# ============================================================================
# ADVANCED FILTERS - New high-priority tools for better task discovery
# ============================================================================

@mcp.tool
async def list_overdue_work_packages(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    priority_ids: Optional[str] = None,  # Comma-separated IDs like "3,4"
    type_ids: Optional[str] = None,  # Comma-separated IDs like "1,2"
    page_size: int = 50
) -> str:
    """List all overdue work packages (tasks past their due date).
    
    This tool helps identify tasks that are past their due date and need urgent attention.
    Only searches through open (non-closed) work packages.
    
    Args:
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee
        priority_ids: Optional comma-separated priority IDs (e.g., "3" for high, or "3,4" for high+urgent)
        type_ids: Optional comma-separated type IDs (e.g., "1" for bugs, or "1,2" for bugs+features)
        page_size: Number of results to return (default: 50, max: 100)
    
    Returns:
        Formatted list of overdue work packages sorted by most overdue first
        
    Example:
        Find all high-priority overdue tasks assigned to user #5:
        {
            "assignee_id": 5,
            "priority_ids": "3"
        }
    """
    try:
        from datetime import date, datetime
        
        client = get_client()
        
        # Build filters list
        filters_list = [
            # Status must be open (not closed)
            {"status": {"operator": "o", "values": []}},
            # Due date < today (overdue)
            # Note: OpenProject API doesn't support "<d" operator with single value
            # Workaround: Use "<>d" (between) with old start date and today
            {"dueDate": {"operator": "<>d", "values": ["2000-01-01", date.today().isoformat()]}}
        ]
        
        # Add optional filters
        if assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        if priority_ids:
            # Parse comma-separated IDs
            priority_list = [p.strip() for p in priority_ids.split(",") if p.strip()]
            if priority_list:
                filters_list.append({"priority": {"operator": "=", "values": priority_list}})
        
        if type_ids:
            # Parse comma-separated IDs
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return "✅ No overdue work packages found!"
        
        # Calculate days overdue for each task
        today = date.today()
        for wp in work_packages:
            due_date_str = wp.get("dueDate")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    days_overdue = (today - due_date).days
                    wp["_days_overdue"] = days_overdue
                except:
                    wp["_days_overdue"] = 0
            else:
                wp["_days_overdue"] = 0
        
        # Sort by most overdue first
        work_packages.sort(key=lambda w: w.get("_days_overdue", 0), reverse=True)
        
        # Format response
        text = f"⚠️ **Overdue Work Packages**: {total} task(s) past due date\n\n"
        text += format_work_package_list(work_packages, show_days_overdue=True)
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list overdue work packages: {str(e)}")


@mcp.tool
async def list_work_packages_due_soon(
    days: int = 7,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    priority_ids: Optional[str] = None,
    page_size: int = 50
) -> str:
    """List work packages due within the next N days.
    
    This helps identify upcoming deadlines and prioritize work accordingly.
    Only searches through open (non-closed) work packages.
    
    Args:
        days: Number of days to look ahead (default: 7)
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee
        priority_ids: Optional comma-separated priority IDs (e.g., "3,4")
        page_size: Number of results to return (default: 50)
    
    Returns:
        Formatted list of work packages due soon, sorted by soonest first
        
    Example:
        Show my tasks due in the next 3 days:
        {
            "days": 3,
            "assignee_id": 5
        }
    """
    try:
        from datetime import date, timedelta, datetime
        
        client = get_client()
        
        # Validate days parameter
        if days < 1:
            return format_error("days must be at least 1")
        if days > 365:
            return format_error("days cannot exceed 365")
        
        # Calculate date range
        today = date.today()
        target_date = today + timedelta(days=days)
        
        # Build filters
        filters_list = [
            # Status must be open
            {"status": {"operator": "o", "values": []}},
            # Due date between today and target_date
            {"dueDate": {"operator": "<>d", "values": [today.isoformat(), target_date.isoformat()]}}
        ]
        
        # Add optional filters
        if assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        if priority_ids:
            priority_list = [p.strip() for p in priority_ids.split(",") if p.strip()]
            if priority_list:
                filters_list.append({"priority": {"operator": "=", "values": priority_list}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return f"✅ No work packages due in the next {days} day(s)!"
        
        # Calculate days until due
        for wp in work_packages:
            due_date_str = wp.get("dueDate")
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    days_until = (due_date - today).days
                    wp["_days_until"] = days_until
                except:
                    wp["_days_until"] = 999
            else:
                wp["_days_until"] = 999
        
        # Sort by soonest first
        work_packages.sort(key=lambda w: w.get("_days_until", 999))
        
        # Format response
        text = f"⏰ **Work Packages Due Soon**: {total} task(s) due in next {days} day(s)\n\n"
        text += format_work_package_list(work_packages, show_days_until=True)
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list work packages due soon: {str(e)}")


@mcp.tool
async def list_unassigned_work_packages(
    project_id: Optional[int] = None,
    priority_ids: Optional[str] = None,
    type_ids: Optional[str] = None,
    active_only: bool = True,
    page_size: int = 50
) -> str:
    """List work packages that have no assignee.
    
    This helps identify tasks that need to be assigned to team members.
    Useful for sprint planning and workload distribution.
    
    Args:
        project_id: Optional project ID to filter by
        priority_ids: Optional comma-separated priority IDs (e.g., "3,4" for high+urgent)
        type_ids: Optional comma-separated type IDs (e.g., "1" for bugs only)
        active_only: If True, only show open work packages (default: True)
        page_size: Number of results to return (default: 50, max: 100)
    
    Returns:
        Formatted list of unassigned work packages
        
    Example:
        Find all unassigned high-priority bugs in project #5:
        {
            "project_id": 5,
            "priority_ids": "3",
            "type_ids": "1"
        }
    """
    try:
        client = get_client()
        
        # Build filters list
        filters_list = [
            # Assignee must be empty (unassigned)
            {"assignee": {"operator": "!*", "values": []}}
        ]
        
        # Add status filter
        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})
        
        # Add optional filters
        if priority_ids:
            priority_list = [p.strip() for p in priority_ids.split(",") if p.strip()]
            if priority_list:
                filters_list.append({"priority": {"operator": "=", "values": priority_list}})
        
        if type_ids:
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return "✅ No unassigned work packages found!"
        
        # Format response
        text = f"👤 **Unassigned Work Packages**: {total} task(s) without assignee\n\n"
        text += format_work_package_list(work_packages)
        
        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total} total unassigned tasks\n"
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list unassigned work packages: {str(e)}")


@mcp.tool
async def list_work_packages_created_recently(
    days: int = 7,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    type_ids: Optional[str] = None,
    active_only: bool = True,
    page_size: int = 50
) -> str:
    """List work packages created in the last N days.
    
    This helps identify new tasks and track task creation patterns.
    
    Args:
        days: Number of days to look back (default: 7)
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee
        type_ids: Optional comma-separated type IDs (e.g., "1,2" for bugs+features)
        active_only: If True, only show open work packages (default: True)
        page_size: Number of results to return (default: 50, max: 100)
    
    Returns:
        Formatted list of recently created work packages, sorted by newest first
        
    Example:
        Show all bugs created in the last 3 days:
        {
            "days": 3,
            "type_ids": "1"
        }
    """
    try:
        from datetime import date, timedelta, datetime
        
        client = get_client()
        
        # Validate days parameter
        if days < 1:
            return format_error("days must be at least 1")
        if days > 365:
            return format_error("days cannot exceed 365")
        
        # Calculate date range
        # Note: Use <t operator for "ago" (created less than N days ago)
        filters_list = [
            # Created at < N days ago (i.e., within last N days)
            {"createdAt": {"operator": "<t", "values": [str(days)]}}
        ]
        
        # Add status filter
        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})
        
        # Add optional filters
        if assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        if type_ids:
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return f"✅ No work packages created in the last {days} day(s)!"
        
        # Sort by creation date (newest first)
        work_packages.sort(key=lambda w: w.get("createdAt", ""), reverse=True)
        
        # Format response
        text = f"🆕 **Recently Created Work Packages**: {total} task(s) created in last {days} day(s)\n\n"
        text += format_work_package_list(work_packages)
        
        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total} total\n"
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list recently created work packages: {str(e)}")


@mcp.tool
async def list_high_priority_work_packages(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    type_ids: Optional[str] = None,
    active_only: bool = True,
    page_size: int = 50
) -> str:
    """List work packages with high priority.
    
    This tool finds tasks marked as high priority or urgent. Note that you need to know
    the priority ID for "High" in your OpenProject instance (typically 3 or 4).
    Use list_priorities tool first if you don't know the priority IDs.
    
    Args:
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee
        type_ids: Optional comma-separated type IDs (e.g., "1" for bugs only)
        active_only: If True, only show open work packages (default: True)
        page_size: Number of results to return (default: 50, max: 100)
    
    Returns:
        Formatted list of high priority work packages
        
    Example:
        Show all high-priority bugs in project #5:
        {
            "project_id": 5,
            "type_ids": "1"
        }
        
    Note:
        This assumes priority ID 3 = "High". If your instance uses different IDs,
        use list_priorities to find the correct ID, then use list_work_packages
        with priority_ids parameter instead.
    """
    try:
        client = get_client()
        
        # Build filters - assume priority ID 3 is "High"
        # Users can override by using list_work_packages with specific priority_ids
        filters_list = [
            # Priority = 3 (typically "High" in OpenProject)
            {"priority": {"operator": "=", "values": ["3"]}}
        ]
        
        # Add status filter
        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})
        
        # Add optional filters
        if assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        if type_ids:
            type_list = [t.strip() for t in type_ids.split(",") if t.strip()]
            if type_list:
                filters_list.append({"type": {"operator": "=", "values": type_list}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return "✅ No high priority work packages found!"
        
        # Format response
        text = f"🔴 **High Priority Work Packages**: {total} task(s)\n\n"
        text += "💡 Note: This lists tasks with priority ID 3 (typically 'High').\n"
        text += "   Use list_priorities to see all priority IDs in your instance.\n\n"
        text += format_work_package_list(work_packages)
        
        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total} total\n"
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list high priority work packages: {str(e)}")


@mcp.tool
async def list_work_packages_nearly_complete(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    min_percentage: int = 80,
    active_only: bool = True,
    page_size: int = 50
) -> str:
    """List work packages that are nearly complete (high percentage done).
    
    This helps identify tasks that are almost finished and may need a final push.
    Useful for sprint reviews and workload tracking.
    
    Args:
        project_id: Optional project ID to filter by
        assignee_id: Optional user ID to filter by assignee
        min_percentage: Minimum completion percentage (default: 80, range: 1-99)
        active_only: If True, only show open work packages (default: True)
        page_size: Number of results to return (default: 50, max: 100)
    
    Returns:
        Formatted list of nearly complete work packages
        
    Example:
        Show tasks >90% complete in project #5:
        {
            "project_id": 5,
            "min_percentage": 90
        }
    """
    try:
        client = get_client()
        
        # Validate min_percentage
        if min_percentage < 1 or min_percentage > 99:
            return format_error("min_percentage must be between 1 and 99")
        
        # Build filters
        filters_list = [
            # Percentage done >= min_percentage
            {"percentageDone": {"operator": ">=", "values": [str(min_percentage)]}}
        ]
        
        # Add status filter
        if active_only:
            filters_list.append({"status": {"operator": "o", "values": []}})
        else:
            filters_list.append({"status": {"operator": "*", "values": []}})
        
        # Add optional filters
        if assignee_id:
            filters_list.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
        
        filters = json.dumps(filters_list)
        
        # Validate page_size
        if page_size < 1 or page_size > 100:
            return format_error("page_size must be between 1 and 100")
        
        result = await client.get_work_packages(
            project_id=project_id,
            filters=filters,
            page_size=page_size
        )
        
        work_packages = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", 0)
        
        if not work_packages:
            return f"✅ No work packages with ≥{min_percentage}% completion found!"
        
        # Sort by percentage done (highest first)
        work_packages.sort(key=lambda w: w.get("percentageDone", 0), reverse=True)
        
        # Format response
        text = f"📊 **Nearly Complete Work Packages**: {total} task(s) ≥{min_percentage}% done\n\n"
        text += format_work_package_list(work_packages)
        
        # Add completion percentages in summary
        if work_packages:
            text += "\n**Completion Summary**:\n"
            for wp in work_packages[:10]:  # Show first 10
                percentage = wp.get("percentageDone", 0)
                subject = wp.get("subject", "Unknown")[:50]
                text += f"  - #{wp.get('id')}: {percentage}% - {subject}\n"
            if len(work_packages) > 10:
                text += f"  ... and {len(work_packages) - 10} more\n"
        
        if total > page_size:
            text += f"\n📄 Showing first {page_size} of {total} total\n"
        
        return text
        
    except Exception as e:
        return format_error(f"Failed to list nearly complete work packages: {str(e)}")


