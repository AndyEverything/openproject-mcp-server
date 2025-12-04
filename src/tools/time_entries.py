"""Time entry management tools for time tracking."""

from typing import Optional
from pydantic import BaseModel, Field
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


class CreateTimeEntryInput(BaseModel):
    """Input model for creating time entries."""
    work_package_id: int = Field(..., description="Work package ID", gt=0)
    hours: float = Field(..., description="Hours spent", gt=0)
    spent_on: str = Field(..., description="Date spent (YYYY-MM-DD)")
    activity_id: int = Field(..., description="Activity ID (1=Management, 2=Specification, 3=Development, 4=Testing)", gt=0)
    comment: Optional[str] = Field(None, description="Optional comment")


class UpdateTimeEntryInput(BaseModel):
    """Input model for updating time entries."""
    time_entry_id: int = Field(..., description="Time entry ID to update", gt=0)
    hours: Optional[float] = Field(None, description="New hours spent", gt=0)
    spent_on: Optional[str] = Field(None, description="New date (YYYY-MM-DD)")
    activity_id: Optional[int] = Field(None, description="New activity ID", gt=0)
    comment: Optional[str] = Field(None, description="New comment")


@mcp.tool
async def list_time_entries(
    work_package_id: Optional[int] = None,
    user_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> str:
    """List time entries with optional filters.

    Args:
        work_package_id: Optional filter by work package
        user_id: Optional filter by user
        from_date: Optional start date (YYYY-MM-DD)
        to_date: Optional end date (YYYY-MM-DD)

    Returns:
        List of time entries
    """
    try:
        client = get_client()

        import json
        filters = []
        if work_package_id:
            filters.append({"work_package": {"operator": "=", "values": [str(work_package_id)]}})
        if user_id:
            filters.append({"user": {"operator": "=", "values": [str(user_id)]}})
        if from_date:
            filters.append({"spent_on": {"operator": ">=", "values": [from_date]}})
        if to_date:
            filters.append({"spent_on": {"operator": "<=", "values": [to_date]}})

        filters_json = json.dumps(filters) if filters else None

        result = await client.get_time_entries(filters_json)
        entries = result.get("_embedded", {}).get("elements", [])

        if not entries:
            return "No time entries found."

        text = f"✅ **Found {len(entries)} time entr{'y' if len(entries) == 1 else 'ies'}:**\n\n"
        total_hours = 0

        for entry in entries:
            text += f"**Time Entry #{entry.get('id', 'N/A')}**\n"
            text += f"  Hours: {entry.get('hours', 0)}\n"
            text += f"  Date: {entry.get('spentOn', 'N/A')}\n"

            embedded = entry.get("_embedded", {})
            if "workPackage" in embedded:
                text += f"  Work Package: {embedded['workPackage'].get('subject', 'Unknown')}\n"
            if "user" in embedded:
                text += f"  User: {embedded['user'].get('name', 'Unknown')}\n"
            if "activity" in embedded:
                text += f"  Activity: {embedded['activity'].get('name', 'Unknown')}\n"

            if entry.get('comment', {}).get('raw'):
                text += f"  Comment: {entry['comment']['raw']}\n"

            total_hours += entry.get('hours', 0)
            text += "\n"

        text += f"**Total Hours**: {total_hours}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list time entries: {str(e)}")


@mcp.tool
async def create_time_entry(input: CreateTimeEntryInput) -> str:
    """Create a new time entry for a work package.

    Activity IDs (common values):
    - 1: Management
    - 2: Specification
    - 3: Development
    - 4: Testing

    Args:
        input: Time entry data including work_package_id, hours, date, activity, and optional comment

    Returns:
        Success message with created time entry details

    Example:
        {
            "work_package_id": 123,
            "hours": 2.5,
            "spent_on": "2025-01-15",
            "activity_id": 3,
            "comment": "Implemented feature X"
        }
    """
    try:
        client = get_client()

        data = {
            "work_package_id": input.work_package_id,
            "hours": str(input.hours),
            "spent_on": input.spent_on,
            "activity_id": input.activity_id,
        }

        if input.comment:
            data["comment"] = input.comment

        result = await client.create_time_entry(data)

        text = format_success(f"Time entry created successfully!\n\n")
        text += f"**ID**: #{result.get('id', 'N/A')}\n"
        text += f"**Hours**: {result.get('hours', 0)}\n"
        text += f"**Date**: {result.get('spentOn', 'N/A')}\n"

        embedded = result.get("_embedded", {})
        if "workPackage" in embedded:
            text += f"**Work Package**: {embedded['workPackage'].get('subject', 'Unknown')}\n"
        if "activity" in embedded:
            text += f"**Activity**: {embedded['activity'].get('name', 'Unknown')}\n"

        if result.get('comment', {}).get('raw'):
            text += f"**Comment**: {result['comment']['raw']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create time entry: {str(e)}")


@mcp.tool
async def update_time_entry(input: UpdateTimeEntryInput) -> str:
    """Update an existing time entry.

    Args:
        input: Time entry update data including time_entry_id and fields to update

    Returns:
        Success message with updated time entry details
    """
    try:
        client = get_client()

        update_data = {}

        if input.hours is not None:
            update_data["hours"] = str(input.hours)
        if input.spent_on is not None:
            update_data["spent_on"] = input.spent_on
        if input.activity_id is not None:
            update_data["activity_id"] = input.activity_id
        if input.comment is not None:
            update_data["comment"] = input.comment

        if not update_data:
            return format_error("No fields provided to update")

        result = await client.update_time_entry(input.time_entry_id, update_data)

        text = format_success(f"Time entry #{input.time_entry_id} updated successfully!\n\n")
        text += f"**Hours**: {result.get('hours', 0)}\n"
        text += f"**Date**: {result.get('spentOn', 'N/A')}\n"

        embedded = result.get("_embedded", {})
        if "activity" in embedded:
            text += f"**Activity**: {embedded['activity'].get('name', 'Unknown')}\n"

        if result.get('comment', {}).get('raw'):
            text += f"**Comment**: {result['comment']['raw']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to update time entry: {str(e)}")


@mcp.tool
async def delete_time_entry(time_entry_id: int) -> str:
    """Delete a time entry.

    Args:
        time_entry_id: ID of the time entry to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()

        success = await client.delete_time_entry(time_entry_id)

        if success:
            return format_success(f"Time entry #{time_entry_id} deleted successfully")
        else:
            return format_error(f"Failed to delete time entry #{time_entry_id}")

    except Exception as e:
        return format_error(f"Failed to delete time entry: {str(e)}")


@mcp.tool
async def list_time_entry_activities() -> str:
    """List available time entry activities.

    Note: This endpoint may return 404 on some OpenProject instances, but
    common activity IDs are: 1=Management, 2=Specification, 3=Development, 4=Testing

    Returns:
        List of available activities or common activity IDs
    """
    try:
        client = get_client()

        result = await client.get_time_entry_activities()
        activities = result.get("_embedded", {}).get("elements", [])

        if not activities:
            # Fallback to common activity IDs
            text = "⚠️  **Common Time Entry Activities:**\n\n"
            text += "- **Management** (ID: 1)\n"
            text += "- **Specification** (ID: 2)\n"
            text += "- **Development** (ID: 3)\n"
            text += "- **Testing** (ID: 4)\n"
            text += "\nNote: Use these IDs when creating/updating time entries.\n"
            return text

        text = "✅ **Available Time Entry Activities:**\n\n"
        for activity in activities:
            text += f"- **{activity.get('name', 'Unnamed')}** (ID: {activity.get('id', 'N/A')})\n"
            if activity.get("isDefault"):
                text += "  ✓ Default activity\n"

        return text

    except Exception as e:
        # Return common activities on error
        text = "⚠️  **Common Time Entry Activities:**\n\n"
        text += "- **Management** (ID: 1)\n"
        text += "- **Specification** (ID: 2)\n"
        text += "- **Development** (ID: 3)\n"
        text += "- **Testing** (ID: 4)\n"
        text += "\nNote: API endpoint unavailable. Use these common IDs.\n"
        return text
