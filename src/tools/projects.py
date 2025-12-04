"""Project management tools."""

import json
from typing import Optional
from src.server import mcp, get_client
from pydantic import BaseModel, Field
from src.utils.formatting import format_success, format_error
from src.utils.formatting import format_project_list


@mcp.tool
async def list_projects(active_only: bool = True) -> str:
    """List all OpenProject projects.

    Args:
        active_only: If True, only show active projects (default: True)

    Returns:
        Formatted list of projects with their status and basic information
    """
    try:
        client = get_client()

        # Build filters
        filters = None
        if active_only:
            filters = json.dumps([{"active": {"operator": "=", "values": ["t"]}}])

        result = await client.get_projects(filters)
        projects = result.get("_embedded", {}).get("elements", [])

        return format_project_list(projects)

    except Exception as e:
        return f"❌ Failed to list projects: {str(e)}"


@mcp.tool
async def get_project(project_id: int) -> str:
    """Get detailed information about a specific project.

    Args:
        project_id: The project ID

    Returns:
        Detailed project information including description and settings
    """
    try:
        client = get_client()
        project = await client.get_project(project_id)

        text = f"✅ Project #{project.get('id')}\n\n"
        text += f"**Name**: {project.get('name', 'Unknown')}\n"
        text += f"**Identifier**: {project.get('identifier', 'N/A')}\n"
        text += f"**Status**: {'Active' if project.get('active') else 'Inactive'}\n"
        text += f"**Public**: {'Yes' if project.get('public') else 'No'}\n"

        if project.get('description'):
            desc = project['description']
            if isinstance(desc, dict):
                desc_text = desc.get('raw', '')
            else:
                desc_text = str(desc)
            if desc_text:
                text += f"\n**Description**:\n{desc_text}\n"

        if project.get('createdAt'):
            text += f"\n**Created**: {project['createdAt']}\n"
        if project.get('updatedAt'):
            text += f"**Updated**: {project['updatedAt']}\n"

        return text

    except Exception as e:
        return f"❌ Failed to get project: {str(e)}"


class CreateProjectInput(BaseModel):
    """Input model for creating projects."""
    name: str = Field(..., description="Project name", min_length=1, max_length=255)
    identifier: str = Field(..., description="Project identifier (lowercase, no spaces)", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Project description")
    public: Optional[bool] = Field(None, description="Whether project is public")
    status: Optional[str] = Field(None, description="Project status")
    parent_id: Optional[int] = Field(None, description="Parent project ID for sub-projects", gt=0)


class UpdateProjectInput(BaseModel):
    """Input model for updating projects."""
    project_id: int = Field(..., description="Project ID to update", gt=0)
    name: Optional[str] = Field(None, description="New project name", min_length=1, max_length=255)
    identifier: Optional[str] = Field(None, description="New project identifier", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="New project description")
    public: Optional[bool] = Field(None, description="Whether project is public")
    status: Optional[str] = Field(None, description="New project status")
    parent_id: Optional[int] = Field(None, description="New parent project ID", gt=0)


@mcp.tool
async def create_project(input: CreateProjectInput) -> str:
    """Create a new project.

    Args:
        input: Project data including name, identifier, and optional fields

    Returns:
        Success message with created project details

    Example:
        {
            "name": "New Project",
            "identifier": "new-project",
            "description": "This is a new project",
            "public": false
        }
    """
    try:
        client = get_client()

        data = {
            "name": input.name,
            "identifier": input.identifier,
        }

        if input.description is not None:
            data["description"] = input.description
        if input.public is not None:
            data["public"] = input.public
        if input.status is not None:
            data["status"] = input.status
        if input.parent_id is not None:
            data["parent_id"] = input.parent_id

        result = await client.create_project(data)

        text = format_success("Project created successfully!\n\n")
        text += f"**Name**: {result.get('name', 'N/A')}\n"
        text += f"**ID**: #{result.get('id', 'N/A')}\n"
        text += f"**Identifier**: {result.get('identifier', 'N/A')}\n"
        text += f"**Public**: {'Yes' if result.get('public') else 'No'}\n"
        text += f"**Status**: {result.get('status', 'N/A')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create project: {str(e)}")


@mcp.tool
async def update_project(input: UpdateProjectInput) -> str:
    """Update an existing project.

    Args:
        input: Project update data including project_id and fields to update

    Returns:
        Success message with updated project details
    """
    try:
        client = get_client()

        update_data = {}

        if input.name is not None:
            update_data["name"] = input.name
        if input.identifier is not None:
            update_data["identifier"] = input.identifier
        if input.description is not None:
            update_data["description"] = input.description
        if input.public is not None:
            update_data["public"] = input.public
        if input.status is not None:
            update_data["status"] = input.status
        if input.parent_id is not None:
            update_data["parent_id"] = input.parent_id

        if not update_data:
            return format_error("No fields provided to update")

        result = await client.update_project(input.project_id, update_data)

        text = format_success(f"Project #{input.project_id} updated successfully!\n\n")
        text += f"**Name**: {result.get('name', 'N/A')}\n"
        text += f"**Identifier**: {result.get('identifier', 'N/A')}\n"
        text += f"**Public**: {'Yes' if result.get('public') else 'No'}\n"
        text += f"**Status**: {result.get('status', 'N/A')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to update project: {str(e)}")


@mcp.tool
async def delete_project(project_id: int) -> str:
    """Delete a project.

    Args:
        project_id: ID of the project to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()

        success = await client.delete_project(project_id)

        if success:
            return format_success(f"Project #{project_id} deleted successfully")
        else:
            return format_error(f"Failed to delete project #{project_id}")

    except Exception as e:
        return format_error(f"Failed to delete project: {str(e)}")
