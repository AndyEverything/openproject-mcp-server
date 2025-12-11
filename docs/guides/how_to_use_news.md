# How to Use News Tools

This guide explains how to use the News management tools in the OpenProject MCP server.

## Overview

News tools allow you to create, read, update, and delete news entries for OpenProject projects. News entries are announcements or important updates visible to all project members.

## Available Tools

### 1. `list_news` - List News Entries

List all news entries with optional filtering and sorting.

**Parameters:**
- `project_id` (optional): Filter by specific project
- `sort_by_created` (optional): Sort by creation date (default: true, newest first)
- `offset` (optional): Pagination offset (default: 0)
- `page_size` (optional): Items per page (default: 20)

**Example:**
```json
{
  "project_id": 1,
  "page_size": 10
}
```

### 2. `create_news` - Create News Entry

Create a new news announcement for a project.

**Required Permissions:**
- Administrator, OR
- "Manage news" permission in the project

**Parameters:**
- `project_id` (required): Project ID
- `title` (required): News headline (max 255 characters)
- `summary` (required): Short summary
- `description` (required): Full content (supports Markdown)

**Example:**
```json
{
  "project_id": 1,
  "title": "Weekly Report Published",
  "summary": "Week 50 report is now available",
  "description": "# Weekly Report\n\nThe weekly report for week 50 has been completed.\n\n**Highlights:**\n- Feature X completed\n- Bug fixes deployed"
}
```

### 3. `get_news` - Get News Detail

Get detailed information about a specific news entry.

**Parameters:**
- `news_id` (required): The news entry ID

**Example:**
```json
{
  "news_id": 5
}
```

### 4. `update_news` - Update News Entry

Update an existing news entry. Only provide fields you want to change.

**Required Permissions:**
- Administrator, OR
- "Manage news" permission in the project

**Parameters:**
- `news_id` (required): News entry ID
- `title` (optional): New headline
- `summary` (optional): New summary
- `description` (optional): New content

**Example:**
```json
{
  "news_id": 5,
  "title": "Updated: Weekly Report Published",
  "description": "# Updated Weekly Report\n\nThe report has been updated with new information."
}
```

### 5. `delete_news` - Delete News Entry

Permanently delete a news entry.

**⚠️ WARNING:** This action cannot be undone!

**Required Permissions:**
- Administrator, OR
- "Manage news" permission in the project

**Parameters:**
- `news_id` (required): News entry ID to delete

**Example:**
```json
{
  "news_id": 5
}
```

## Use Cases

### Use Case 1: Weekly Report Announcement

After generating a weekly report, create a news entry to notify the team:

```json
{
  "project_id": 1,
  "title": "Weekly Progress Report - Week 50",
  "summary": "This week's report shows great progress on Feature X",
  "description": "# Week 50 Progress\n\n## Completed:\n- Feature X implementation\n- Bug #123 fixed\n\n## In Progress:\n- Feature Y design"
}
```

### Use Case 2: Milestone Announcement

Announce when a project milestone is reached:

```json
{
  "project_id": 5,
  "title": "Milestone: v2.0 Release Complete!",
  "summary": "We've successfully released version 2.0",
  "description": "# Version 2.0 Released\n\n🎉 Great work team!\n\n**New Features:**\n- User authentication\n- Dashboard\n- Reports\n\n**Next Steps:**\n- Start planning v2.1\n- Collect user feedback"
}
```

### Use Case 3: Important Update

Notify team about critical project changes:

```json
{
  "project_id": 3,
  "title": "IMPORTANT: Deadline Change",
  "summary": "Project deadline has been moved to December 20th",
  "description": "# Deadline Update\n\nDue to client request, the project deadline has been **extended to December 20th**.\n\nThis gives us 2 more weeks to complete:\n- Final testing\n- Documentation\n- Deployment preparation"
}
```

## Tips

1. **Use Markdown**: The description field supports full Markdown formatting including headers, lists, bold, italic, links, and code blocks.

2. **Keep Summaries Brief**: The summary appears in news lists, so keep it concise (1-2 sentences).

3. **Structure Content**: Use Markdown headers to organize longer news entries.

4. **Check Permissions**: Ensure you have "Manage news" permission before attempting to create, update, or delete news.

5. **Regular Updates**: Use news for regular updates like weekly reports to keep the team informed.

## Integration with Weekly Reports

The news tools work great with weekly report generation. After generating a report, create a news entry to notify the team:

1. Generate weekly report
2. Create news entry with report summary
3. Link to full report in the description

## Troubleshooting

### Error: "Failed to create news: 403"
**Solution:** You don't have "Manage news" permission. Contact your project administrator.

### Error: "Failed to create news: 422"
**Solution:** Check that all required fields (project_id, title, summary, description) are provided and valid.

### Error: "Failed to get news entry: 404"
**Solution:** The news entry ID doesn't exist. Use `list_news` to see available entries.
