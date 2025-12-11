"""News management tools for OpenProject."""

import json
from typing import Optional
from pydantic import BaseModel, Field

from src.server import mcp, get_client
from src.utils.formatting import (
    format_news_list,
    format_news_detail,
    format_success,
    format_error,
)


# ============================================================
# Pydantic Models for Input Validation
# ============================================================


class CreateNewsInput(BaseModel):
    """Input model for creating news."""

    project_id: int = Field(..., description="Project ID", gt=0)
    title: str = Field(
        ..., description="News headline", min_length=1, max_length=255
    )
    summary: str = Field(..., description="Short summary", min_length=1)
    description: str = Field(..., description="Main content (supports Markdown)")


class UpdateNewsInput(BaseModel):
    """Input model for updating news."""

    news_id: int = Field(..., description="News ID to update", gt=0)
    title: Optional[str] = Field(
        None, description="New headline", min_length=1, max_length=255
    )
    summary: Optional[str] = Field(None, description="New summary", min_length=1)
    description: Optional[str] = Field(
        None, description="New content (supports Markdown)"
    )


# ============================================================
# News Tools
# ============================================================


@mcp.tool()
async def list_news(
    project_id: Optional[int] = None,
    sort_by_created: bool = True,
    offset: int = 0,
    page_size: int = 20,
) -> str:
    """List news entries with filtering and pagination.

    Args:
        project_id: Optional project ID to filter news by project
        sort_by_created: If True, sort by creation date descending (newest first)
        offset: Starting index for pagination (default: 0)
        page_size: Number of results per page (default: 20)

    Returns:
        Formatted list of news entries

    Example:
        To list news for project #1:
        {
            "project_id": 1,
            "page_size": 10
        }
    """
    try:
        client = get_client()

        # Build filters if project_id provided
        filters = None
        if project_id:
            filters = json.dumps(
                [{"project_id": {"operator": "=", "values": [str(project_id)]}}]
            )

        # Build sort criteria
        sort_by = None
        if sort_by_created:
            sort_by = json.dumps([["created_at", "desc"]])

        # Fetch news
        result = await client.get_news(
            filters=filters, sort_by=sort_by, offset=offset, page_size=page_size
        )

        # Extract news items
        news_items = result.get("_embedded", {}).get("elements", [])

        if not news_items:
            return format_success("No news entries found.")

        # Format and return
        formatted = format_news_list(news_items)
        total = result.get("total", len(news_items))
        formatted += f"\n---\nShowing {len(news_items)} of {total} total news entries"

        return formatted

    except Exception as e:
        return format_error(f"Failed to list news: {str(e)}")


@mcp.tool()
async def create_news(input: CreateNewsInput) -> str:
    """Create a new news entry for a project.

    This tool creates a news announcement for a project. News entries are visible
    to all project members and can be used for important announcements, updates,
    or milestone notifications.

    Required permissions: Administrator or "Manage news" permission in the project

    Args:
        input: News creation data including project_id, title, summary, and description

    Returns:
        Success message with created news details

    Example:
        {
            "project_id": 1,
            "title": "Weekly Report Published",
            "summary": "Week 50 report is now available",
            "description": "# Weekly Report\\n\\nThe weekly report for week 50 has been completed.\\n\\n**Highlights:**\\n- Feature X completed\\n- Bug fixes deployed"
        }
    """
    try:
        client = get_client()

        # Prepare data for API
        data = {
            "project": input.project_id,
            "title": input.title,
            "summary": input.summary,
            "description": input.description,
        }

        # Create news
        news = await client.create_news(data)

        # Format response
        news_id = news.get("id")
        title = news.get("title")

        result = format_success(f"News entry created successfully!")
        result += f"\n\n**ID**: {news_id}"
        result += f"\n**Title**: {title}"
        result += f"\n**Summary**: {input.summary[:100]}..."

        return result

    except Exception as e:
        return format_error(f"Failed to create news: {str(e)}")


@mcp.tool()
async def get_news(news_id: int) -> str:
    """Get detailed information about a specific news entry.

    Args:
        news_id: The news entry ID

    Returns:
        Detailed news entry information with full content

    Example:
        To get news entry #5:
        {
            "news_id": 5
        }
    """
    try:
        client = get_client()

        # Fetch news entry
        news = await client.get_news_item(news_id)

        # Format and return
        return format_news_detail(news)

    except Exception as e:
        return format_error(f"Failed to get news entry: {str(e)}")


@mcp.tool()
async def update_news(input: UpdateNewsInput) -> str:
    """Update an existing news entry.

    This tool allows you to modify the title, summary, or description of a news entry.
    You only need to provide the fields you want to update.

    Required permissions: Administrator or "Manage news" permission in the project

    Args:
        input: Update data including news_id and fields to modify

    Returns:
        Success message with updated news details

    Example:
        To update only the title and description:
        {
            "news_id": 5,
            "title": "Updated: Weekly Report Published",
            "description": "# Updated Weekly Report\\n\\nThe report has been updated with new information."
        }
    """
    try:
        client = get_client()

        # Build update data (only include provided fields)
        data = {}
        if input.title is not None:
            data["title"] = input.title
        if input.summary is not None:
            data["summary"] = input.summary
        if input.description is not None:
            data["description"] = input.description

        if not data:
            return format_error(
                "No fields provided to update. Please provide at least one field (title, summary, or description)."
            )

        # Update news
        news = await client.update_news(input.news_id, data)

        # Format response
        result = format_success(f"News entry #{input.news_id} updated successfully!")
        result += f"\n\n**Title**: {news.get('title')}"
        if input.summary:
            result += f"\n**Summary**: {news.get('summary', '')[:100]}..."

        return result

    except Exception as e:
        return format_error(f"Failed to update news: {str(e)}")


@mcp.tool()
async def delete_news(news_id: int) -> str:
    """Delete a news entry permanently.

    WARNING: This action cannot be undone. The news entry will be permanently removed
    from the project.

    Required permissions: Administrator or "Manage news" permission in the project

    Args:
        news_id: ID of the news entry to delete

    Returns:
        Success or error message

    Example:
        To delete news entry #5:
        {
            "news_id": 5
        }
    """
    try:
        client = get_client()

        # Delete news
        await client.delete_news(news_id)

        return format_success(
            f"News entry #{news_id} has been permanently deleted."
        )

    except Exception as e:
        return format_error(f"Failed to delete news: {str(e)}")
