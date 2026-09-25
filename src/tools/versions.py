"""Version/milestone management tools."""

import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from src.server import get_client, mcp
from src.tools.discovery import (
    build_work_package_page,
    invalid_format_error,
    validate_pagination,
    work_packages_markdown,
)
from src.utils.formatting import format_error, format_success
from src.utils.rendering import extract_id, format_api_error, render


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


VERSION_STATUSES = ("open", "locked", "closed")
VERSION_SHARINGS = ("none", "descendants", "hierarchy", "tree", "system")


def build_version(version: Dict) -> Dict[str, Any]:
    """Version (sprint/milestone) view model."""
    project_link = (version.get("_links") or {}).get("definingProject") or {}
    embedded_project = (version.get("_embedded") or {}).get("definingProject") or {}
    return {
        "id": version.get("id"),
        "name": version.get("name"),
        "description": (version.get("description") or {}).get("raw") or "",
        "status": version.get("status"),
        "start_date": version.get("startDate"),
        "end_date": version.get("endDate"),
        "sharing": version.get("sharing"),
        "project": {
            "id": embedded_project.get("id") or extract_id(project_link.get("href")),
            "name": embedded_project.get("name") or project_link.get("title"),
        },
    }


def _version_markdown(data: Dict[str, Any]) -> str:
    project = data["project"]
    lines = [
        f"🏁 **Wersja: {data['name']}** (ID: {data['id']})",
        "",
        f"**Status**: {data['status'] or '-'}",
        f"**Start**: {data['start_date'] or '-'}",
        f"**Koniec**: {data['end_date'] or '-'}",
        f"**Udostępnianie**: {data['sharing'] or '-'}",
        f"**Projekt**: {project['name'] or '-'} (#{project['id'] or '-'})",
        "",
        "**Opis**:",
        data["description"] or "_(brak opisu)_",
    ]
    return "\n".join(lines) + "\n"


@mcp.tool
async def get_version(version_id: int, format: str = "markdown") -> str:
    """Get version (sprint/milestone) details.

    Args:
        version_id: The version ID
        format: "markdown" (default) or "json"

    Returns:
        Name, description (raw), status, start/end date, sharing and defining project
    """
    error = invalid_format_error(format)
    if error:
        return error
    try:
        version = await get_client().get_version(version_id)
    except Exception as e:
        return format_api_error(e)
    return render(build_version(version), format, _version_markdown)


@mcp.tool
async def list_version_work_packages(
    version_id: int,
    include_closed: bool = True,
    offset: int = 1,
    page_size: int = 20,
    format: str = "markdown",
) -> str:
    """List work packages assigned to a version (sprint scope).

    Args:
        version_id: The version ID
        include_closed: If True (default), all statuses; False - open only
        offset: Page number, 1-based (default: 1)
        page_size: Number of results per page (default: 20, max: 100)
        format: "markdown" (default) or "json"

    Returns:
        Work packages of the version with status, type, priority, assignee and due date
    """
    error = invalid_format_error(format) or validate_pagination(offset, page_size)
    if error:
        return error
    filters = [
        {"version": {"operator": "=", "values": [str(version_id)]}},
        {"status": {"operator": "*" if include_closed else "o", "values": []}},
    ]
    client = get_client()
    try:
        # OP odrzuca filtr wersji na globalnym /work_packages (400) – zapytanie w zakresie projektu wersji
        version = await client.get_version(version_id)
        project_id = extract_id(version.get("_links", {}).get("definingProject", {}).get("href"))
        result = await client.get_work_packages(
            project_id=project_id,
            filters=json.dumps(filters),
            offset=offset,
            page_size=page_size,
        )
    except Exception as e:
        return format_api_error(e)

    data = build_work_package_page(
        result, offset, page_size, version_id=version_id, include_closed=include_closed
    )
    sharing = version.get("sharing")
    # descendants mieści się w projekcie wersji z podprojektami
    if sharing in ("hierarchy", "tree", "system"):
        data["scope_note"] = (
            f"Wersja jest współdzielona ({sharing}) – wynik obejmuje tylko projekt #{project_id} "
            "i jego podprojekty; zadania z innych projektów mogą nie być widoczne."
        )
    title = f"Zadania wersji #{version_id}"
    if not include_closed:
        title += " (otwarte)"

    def to_markdown(d: Dict[str, Any]) -> str:
        text = work_packages_markdown(title, d, f"📭 {title}: brak zadań.")
        if d.get("scope_note"):
            text += f"\n\n⚠️ {d['scope_note']}"
        return text

    return render(data, format, to_markdown)


@mcp.tool
async def update_version(
    version_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sharing: Optional[str] = None,
) -> str:
    """Update a version (sprint/milestone). Only the provided fields are changed.

    Args:
        version_id: The version ID
        name: New name
        description: New description (markdown)
        status: open, locked or closed
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        sharing: none, descendants, hierarchy, tree or system

    Returns:
        Success message with updated version details
    """
    if status is not None and status not in VERSION_STATUSES:
        return format_error(
            f"Invalid status '{status}'. Allowed values: {', '.join(VERSION_STATUSES)}"
        )
    if sharing is not None and sharing not in VERSION_SHARINGS:
        return format_error(
            f"Invalid sharing '{sharing}'. Allowed values: {', '.join(VERSION_SHARINGS)}"
        )

    payload: Dict[str, Any] = {}
    if name is not None:
        if not name.strip():
            return format_error("name cannot be empty")
        payload["name"] = name
    if description is not None:
        payload["description"] = {"raw": description}
    if status is not None:
        payload["status"] = status
    if start_date is not None:
        payload["startDate"] = start_date
    if end_date is not None:
        payload["endDate"] = end_date
    if sharing is not None:
        payload["sharing"] = sharing
    if not payload:
        return format_error("No fields to update - provide at least one field")

    try:
        result = await get_client().update_version(version_id, payload)
    except Exception as e:
        return format_api_error(e)

    changed = ", ".join(payload)
    return format_success(f"Version #{version_id} updated ({changed})\n\n") + _version_markdown(
        build_version(result)
    )
