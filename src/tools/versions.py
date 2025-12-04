"""Version/milestone management tools."""

from typing import Optional
from pydantic import BaseModel, Field
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


class CreateVersionInput(BaseModel):
    """Input model for creating versions."""
    project_id: int = Field(..., description="Project ID", gt=0)
    name: str = Field(..., description="Version name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Version description")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Status (open, locked, closed)")


@mcp.tool
async def list_versions(project_id: int) -> str:
    """List all versions/milestones in a project.

    Args:
        project_id: The project ID

    Returns:
        List of versions with their details
    """
    try:
        client = get_client()

        result = await client.get_versions(project_id)
        versions = result.get("_embedded", {}).get("elements", [])

        if not versions:
            return f"No versions found for project #{project_id}."

        text = f"✅ **Versions for Project #{project_id} ({len(versions)}):**\n\n"
        for version in versions:
            text += f"**{version.get('name', 'Unnamed')}** (ID: {version.get('id', 'N/A')})\n"

            if version.get('description', {}).get('raw'):
                text += f"  Description: {version['description']['raw']}\n"

            if version.get('startDate'):
                text += f"  Start: {version['startDate']}\n"
            if version.get('endDate'):
                text += f"  End: {version['endDate']}\n"

            text += f"  Status: {version.get('status', 'Unknown')}\n"

            if "_embedded" in version and "definingProject" in version["_embedded"]:
                project = version["_embedded"]["definingProject"]
                text += f"  Project: {project.get('name', 'Unknown')}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list versions: {str(e)}")


@mcp.tool
async def create_version(input: CreateVersionInput) -> str:
    """Create a new version/milestone in a project.

    Args:
        input: Version data including project_id, name, and optional fields

    Returns:
        Success message with created version details

    Example:
        {
            "project_id": 5,
            "name": "Version 1.0",
            "description": "First major release",
            "due_date": "2025-03-31",
            "status": "open"
        }
    """
    try:
        client = get_client()

        data = {
            "name": input.name,
        }

        if input.description:
            data["description"] = input.description
        if input.start_date:
            data["start_date"] = input.start_date
        if input.due_date:
            data["due_date"] = input.due_date
        if input.status:
            data["status"] = input.status

        result = await client.create_version(input.project_id, data)

        text = format_success("Version created successfully!\n\n")
        text += f"**Name**: {result.get('name', 'N/A')}\n"
        text += f"**ID**: #{result.get('id', 'N/A')}\n"

        if result.get('description', {}).get('raw'):
            text += f"**Description**: {result['description']['raw']}\n"

        if result.get('startDate'):
            text += f"**Start Date**: {result['startDate']}\n"
        if result.get('endDate'):
            text += f"**End Date**: {result['endDate']}\n"

        text += f"**Status**: {result.get('status', 'Unknown')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create version: {str(e)}")
