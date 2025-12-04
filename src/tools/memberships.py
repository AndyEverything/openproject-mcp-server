"""Membership management tools."""

from typing import Optional, List
from pydantic import BaseModel, Field
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


class CreateMembershipInput(BaseModel):
    """Input model for creating memberships."""
    project_id: int = Field(..., description="Project ID", gt=0)
    user_id: Optional[int] = Field(None, description="User ID (required if group_id not provided)", gt=0)
    group_id: Optional[int] = Field(None, description="Group ID (required if user_id not provided)", gt=0)
    role_ids: Optional[List[int]] = Field(None, description="List of role IDs")
    role_id: Optional[int] = Field(None, description="Single role ID (alternative to role_ids)", gt=0)
    notification_message: Optional[str] = Field(None, description="Optional notification message")


class UpdateMembershipInput(BaseModel):
    """Input model for updating memberships."""
    membership_id: int = Field(..., description="Membership ID to update", gt=0)
    role_ids: Optional[List[int]] = Field(None, description="New list of role IDs")
    role_id: Optional[int] = Field(None, description="Single role ID (alternative to role_ids)", gt=0)
    notification_message: Optional[str] = Field(None, description="Optional notification message")


@mcp.tool
async def list_memberships(
    project_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> str:
    """List memberships (project members).

    Args:
        project_id: Optional project ID to filter by project
        user_id: Optional user ID to filter by user

    Returns:
        List of memberships with project, user, and role information
    """
    try:
        client = get_client()

        result = await client.get_memberships(project_id=project_id, user_id=user_id)
        memberships = result.get("_embedded", {}).get("elements", [])

        if not memberships:
            return "No memberships found."

        text = f"✅ **Found {len(memberships)} membership(s):**\n\n"
        for member in memberships:
            links = member.get("_links", {})

            # Get principal (user/group) information from _links
            principal_link = links.get("principal", {})
            principal_name = principal_link.get("title", "Unknown")
            # Extract user ID from href: "/api/v3/users/7" -> 7
            principal_href = principal_link.get("href", "")
            principal_id = principal_href.split("/")[-1] if principal_href else "N/A"

            text += f"- **{principal_name}** (User ID: {principal_id})\n"

            # Get project information (only if not filtered by single project)
            if not project_id:
                project_link = links.get("project", {})
                project_name = project_link.get("title", "Unknown")
                text += f"  Project: {project_name}\n"

            # Get roles from _links
            role_links = links.get("roles", [])
            if role_links:
                role_names = [r.get("title", "Unknown") for r in role_links]
                text += f"  Roles: {', '.join(role_names)}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list memberships: {str(e)}")


@mcp.tool
async def get_membership(membership_id: int) -> str:
    """Get detailed information about a specific membership.

    Args:
        membership_id: The membership ID

    Returns:
        Detailed membership information
    """
    try:
        client = get_client()
        member = await client.get_membership(membership_id)

        text = f"✅ **Membership #{member.get('id')}**\n\n"

        links = member.get("_links", {})

        # Get project from _links
        project_link = links.get("project", {})
        if project_link:
            text += f"**Project**: {project_link.get('title', 'Unknown')}\n"

        # Get principal (user/group) from _links
        principal_link = links.get("principal", {})
        if principal_link:
            text += f"**User/Group**: {principal_link.get('title', 'Unknown')}\n"

        # Get roles from _links
        role_links = links.get("roles", [])
        if role_links:
            role_names = [r.get("title", "Unknown") for r in role_links]
            text += f"**Roles**: {', '.join(role_names)}\n"

        if member.get('createdAt'):
            text += f"**Created**: {member['createdAt']}\n"
        if member.get('updatedAt'):
            text += f"**Updated**: {member['updatedAt']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get membership: {str(e)}")


@mcp.tool
async def create_membership(input: CreateMembershipInput) -> str:
    """Create a new membership (add user/group to project).

    Args:
        input: Membership data including project_id, user_id/group_id, and role(s)

    Returns:
        Success message with created membership details

    Example:
        {
            "project_id": 5,
            "user_id": 7,
            "role_ids": [1, 3]
        }
    """
    try:
        client = get_client()

        data = {"project_id": input.project_id}

        # Add user or group
        if input.user_id:
            data["user_id"] = input.user_id
        elif input.group_id:
            data["group_id"] = input.group_id
        else:
            return format_error("Either user_id or group_id is required")

        # Add roles
        if input.role_ids:
            data["role_ids"] = input.role_ids
        elif input.role_id:
            data["role_id"] = input.role_id
        else:
            return format_error("Either role_ids or role_id is required")

        if input.notification_message:
            data["notification_message"] = input.notification_message

        result = await client.create_membership(data)

        text = format_success("Membership created successfully!\n\n")
        text += f"**ID**: #{result.get('id', 'N/A')}\n"

        embedded = result.get("_embedded", {})
        if "project" in embedded:
            text += f"**Project**: {embedded['project'].get('name', 'Unknown')}\n"
        if "principal" in embedded:
            text += f"**User/Group**: {embedded['principal'].get('name', 'Unknown')}\n"
        if "roles" in embedded:
            roles = [r.get("name", "Unknown") for r in embedded["roles"]]
            text += f"**Roles**: {', '.join(roles)}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create membership: {str(e)}")


@mcp.tool
async def update_membership(input: UpdateMembershipInput) -> str:
    """Update an existing membership (change roles).

    Args:
        input: Membership update data including membership_id and new role(s)

    Returns:
        Success message with updated membership details
    """
    try:
        client = get_client()

        update_data = {}

        if input.role_ids:
            update_data["role_ids"] = input.role_ids
        elif input.role_id:
            update_data["role_id"] = input.role_id

        if input.notification_message:
            update_data["notification_message"] = input.notification_message

        if not update_data:
            return format_error("No fields provided to update")

        result = await client.update_membership(input.membership_id, update_data)

        text = format_success(f"Membership #{input.membership_id} updated successfully!\n\n")

        embedded = result.get("_embedded", {})
        if "roles" in embedded:
            roles = [r.get("name", "Unknown") for r in embedded["roles"]]
            text += f"**Roles**: {', '.join(roles)}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to update membership: {str(e)}")


@mcp.tool
async def delete_membership(membership_id: int) -> str:
    """Delete a membership (remove user/group from project).

    Args:
        membership_id: ID of the membership to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()

        success = await client.delete_membership(membership_id)

        if success:
            return format_success(f"Membership #{membership_id} deleted successfully")
        else:
            return format_error(f"Failed to delete membership #{membership_id}")

    except Exception as e:
        return format_error(f"Failed to delete membership: {str(e)}")
