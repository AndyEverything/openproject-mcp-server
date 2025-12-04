"""Response formatting utilities for consistent output across all tools."""

from typing import List, Dict, Any, Optional


def format_project_list(projects: List[Dict]) -> str:
    """Format project list with consistent styling.

    Args:
        projects: List of project dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not projects:
        return "No projects found."

    text = f"✅ Found {len(projects)} project(s):\n\n"
    for project in projects:
        text += f"- **{project.get('name', 'Unnamed')}** (ID: {project.get('id')})\n"
        text += f"  Status: {'Active' if project.get('active') else 'Inactive'}\n"
        if project.get('description'):
            desc = project.get('description', {})
            if isinstance(desc, dict):
                desc_text = desc.get('raw', '')[:100]
            else:
                desc_text = str(desc)[:100]
            if desc_text:
                text += f"  Description: {desc_text}...\n"
        text += "\n"
    return text


def format_work_package_list(work_packages: List[Dict]) -> str:
    """Format work package list with embedded data.

    Args:
        work_packages: List of work package dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not work_packages:
        return "No work packages found."

    text = f"✅ Found {len(work_packages)} work package(s):\n\n"
    for wp in work_packages:
        text += f"- **{wp.get('subject', 'No title')}** (#{wp.get('id', 'N/A')})\n"

        # Extract data from both _embedded and _links (OpenProject uses both)
        embedded = wp.get("_embedded", {})
        links = wp.get("_links", {})

        # Type, Status, Priority are in _embedded
        if "type" in embedded:
            text += f"  Type: {embedded['type'].get('name', 'Unknown')}\n"
        if "status" in embedded:
            text += f"  Status: {embedded['status'].get('name', 'Unknown')}\n"
        if "priority" in embedded:
            text += f"  Priority: {embedded['priority'].get('name', 'Unknown')}\n"

        # Assignee is in _links
        assignee_link = links.get("assignee")
        if assignee_link:
            assignee_name = assignee_link.get("title", "Unknown")
            text += f"  Assignee: {assignee_name}\n"
        else:
            text += f"  Assignee: Unassigned\n"

        # Date fields
        if wp.get('startDate'):
            text += f"  Start: {wp['startDate']}\n"
        if wp.get('dueDate'):
            text += f"  Due: {wp['dueDate']}\n"

        text += "\n"
    return text


def format_work_package_detail(wp: Dict) -> str:
    """Format single work package with full details.

    Args:
        wp: Work package dictionary from API

    Returns:
        Formatted markdown string
    """
    text = f"✅ Work Package #{wp.get('id')}\n\n"
    text += f"**Subject**: {wp.get('subject', 'No title')}\n\n"

    # Extract data from both _embedded and _links
    embedded = wp.get("_embedded", {})
    links = wp.get("_links", {})

    # Type, Status, Priority, Project are in _embedded
    if "type" in embedded:
        text += f"**Type**: {embedded['type'].get('name', 'Unknown')}\n"
    if "status" in embedded:
        text += f"**Status**: {embedded['status'].get('name', 'Unknown')}\n"
    if "priority" in embedded:
        text += f"**Priority**: {embedded['priority'].get('name', 'Unknown')}\n"
    if "project" in embedded:
        project = embedded['project']
        text += f"**Project**: {project.get('name', 'Unknown')}\n"

    # Assignee is in _links
    assignee_link = links.get("assignee")
    if assignee_link:
        assignee_name = assignee_link.get("title", "Unknown")
        text += f"**Assignee**: {assignee_name}\n"
    else:
        text += f"**Assignee**: Unassigned\n"

    # Dates
    if wp.get('startDate'):
        text += f"**Start Date**: {wp['startDate']}\n"
    if wp.get('dueDate'):
        text += f"**Due Date**: {wp['dueDate']}\n"
    if wp.get('createdAt'):
        text += f"**Created**: {wp['createdAt']}\n"
    if wp.get('updatedAt'):
        text += f"**Updated**: {wp['updatedAt']}\n"

    # Description
    if wp.get('description'):
        desc = wp['description']
        if isinstance(desc, dict):
            desc_text = desc.get('raw', '')
        else:
            desc_text = str(desc)
        if desc_text:
            text += f"\n**Description**:\n{desc_text}\n"

    # Progress
    if 'percentageDone' in wp:
        text += f"\n**Progress**: {wp['percentageDone']}%\n"

    return text


def format_user_list(users: List[Dict]) -> str:
    """Format user list.

    Args:
        users: List of user dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not users:
        return "No users found."

    text = f"✅ Found {len(users)} user(s):\n\n"
    for user in users:
        text += f"- **{user.get('name', 'Unknown')}** (ID: {user.get('id')})\n"
        if user.get('email'):
            text += f"  Email: {user['email']}\n"
        if user.get('login'):
            text += f"  Login: {user['login']}\n"
        text += f"  Status: {'Active' if user.get('status') == 'active' else 'Inactive'}\n"
        text += "\n"
    return text


def format_time_entry_list(time_entries: List[Dict]) -> str:
    """Format time entry list.

    Args:
        time_entries: List of time entry dictionaries from API

    Returns:
        Formatted markdown string
    """
    if not time_entries:
        return "No time entries found."

    text = f"✅ Found {len(time_entries)} time entr{'y' if len(time_entries) == 1 else 'ies'}:\n\n"
    for entry in time_entries:
        text += f"- **{entry.get('hours', 'N/A')}** on {entry.get('spentOn', 'N/A')}\n"

        # Extract embedded data
        embedded = entry.get("_embedded", {})
        if "workPackage" in embedded:
            wp = embedded['workPackage']
            text += f"  Work Package: {wp.get('subject', 'Unknown')} (#{wp.get('id')})\n"
        if "activity" in embedded:
            activity = embedded['activity']
            text += f"  Activity: {activity.get('name', 'Unknown')}\n"
        if "user" in embedded:
            user = embedded['user']
            text += f"  User: {user.get('name', 'Unknown')}\n"

        # Comment
        if entry.get('comment'):
            comment = entry['comment']
            if isinstance(comment, dict):
                comment_text = comment.get('raw', '')[:100]
            else:
                comment_text = str(comment)[:100]
            if comment_text:
                text += f"  Comment: {comment_text}...\n"

        text += "\n"
    return text


def format_error(error_message: str) -> str:
    """Format error message consistently.

    Args:
        error_message: Error message string

    Returns:
        Formatted error string with ❌ prefix
    """
    return f"❌ Error: {error_message}"


def format_success(message: str) -> str:
    """Format success message consistently.

    Args:
        message: Success message string

    Returns:
        Formatted success string with ✅ prefix
    """
    return f"✅ {message}"
