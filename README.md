![status](https://img.shields.io/badge/status-WIP-yellow) ![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)<br><br>⚠️ This is an early-stage project. Do not use it productively – contributions welcome!<br>

# OpenProject MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with [OpenProject](https://www.openproject.org/) API v3. This server enables LLM applications to interact with OpenProject for project management, work package tracking, and task creation.

## Features

- 🔌 **Full OpenProject API v3 Integration**
- 📋 **Project Management**: List and filter projects
- 📝 **Work Package Management**: Create, list, and filter work packages
- 🏷️ **Type Management**: List available work package types
- 🔐 **Secure Authentication**: API key-based authentication
- 🌐 **Proxy Support**: Optional HTTP proxy configuration
- 🚀 **Async Operations**: Built with modern async/await patterns
- 📊 **Comprehensive Logging**: Configurable logging levels

### 🤖 Agent Context Tools (for Claude Code and other coding agents)

- 🧠 **Full work package context in one call**: untruncated description, custom fields by name, full comments, attachments, relations and hierarchy ([details](#agent-context-tools-))
- 🖼️ **Screenshots the model can actually see**: images embedded in a description or attached to a work package are returned as viewable image content, automatically downscaled if too large
- 💬 **Complete comment history**: no more 150-character truncation – full comments, internal-comment markers and readable field-change history
- 📎 **Attachment handling by type**: images viewable inline, text files (JSON/CSV/logs/…) returned inline, everything else (PDF, DOCX, …) saved to a local folder – with path-safe file names
- 🔍 **Better work discovery**: your own open tasks, full-text search across subject + description + comments, saved views (queries), unread notifications, version/sprint scope
- 🔗 **Code & file links**: GitHub PRs, GitLab MRs/issues and external file links attached to a work package
- 🔒 **Read-only mode** (`OPENPROJECT_READ_ONLY=true`): removes every write tool, so an agent session can only read
- 📄 **JSON output** (`format="json"`) on every new read tool, for programmatic use
- 🧩 **MCP resource & prompts**: attach `openproject://work-packages/{id}` to a conversation, or use the `plan_work_package` / `summarize_work_package` prompts

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- An OpenProject instance (cloud or self-hosted)
- OpenProject API key (generated from your user profile)

## Installation

### 1. Install uv (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (using pip):**
```bash
pip install uv
```

### 2. Clone and Setup the Project

```bash
git clone https://github.com/yourusername/openproject-mcp.git
cd openproject-mcp
```

### 3. Create Virtual Environment and Install Dependencies

```bash
# Create virtual environment and install dependencies in one command
uv sync
```

**Alternative (manual steps):**
```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the environment template
cp env_example.txt .env
```

Edit `.env` and add your OpenProject configuration:
```env
OPENPROJECT_URL=https://your-instance.openproject.com
OPENPROJECT_API_KEY=your-api-key-here
```

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENPROJECT_URL` | Yes | Your OpenProject instance URL | `https://mycompany.openproject.com` |
| `OPENPROJECT_API_KEY` | Yes | API key from your OpenProject user profile | `8169846b42461e6e...` |
| `OPENPROJECT_PROXY` | No | HTTP proxy URL if needed | `http://proxy.company.com:8080` |
| `LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `TEST_CONNECTION_ON_STARTUP` | No | Test API connection when server starts | `true` |

### Optional Configuration Variables

All of the following variables are optional – an existing configuration with only `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` keeps working unchanged.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENPROJECT_READ_ONLY` | not set (off) | `true` / `1` / `yes` (case-insensitive) starts the server in **read-only mode**: every tool that modifies data in OpenProject (create/update/delete, comments, assignments, uploads, watchers, relations, hierarchy, memberships, time entries, news, projects, versions) is not registered. Recommended for agent sessions. |
| `OPENPROJECT_CACHE_TTL` | `600` | Lifetime (seconds) of the in-memory cache for statuses, types, priorities, work package schemas (custom fields) and the current user. `0` disables the cache. Work packages themselves are never cached. |
| `OPENPROJECT_ATTACHMENTS_DIR` | `<system temp>/openproject-attachments` | Directory where downloaded attachments that cannot be returned inline (e.g. PDF, DOCX, large text files) are saved. Files are never executed. |

> **Rule for contributors:** every new tool that writes to OpenProject **MUST** be added to `WRITE_TOOLS` in `src/utils/safety.py`. Otherwise it stays available in read-only mode. `tests/test_safety.py` fails for any registered tool whose name starts with `create_`, `update_`, `delete_`, `add_`, `remove_`, `set_`, `assign_`, `unassign_` or `upload_` and is missing from `WRITE_TOOLS`; write tools with other names must be added by hand (check this in code review).

### Getting an API Key

1. Log in to your OpenProject instance
2. Go to **My account** (click your avatar)
3. Navigate to **Access tokens**
4. Click **+ Add** to create a new token
5. Give it a name and copy the generated token

## Usage

### Deployment Options

This MCP server can be deployed in two ways:

1. **Local (stdio)**: Run on your local machine for personal use
2. **Cloud (SSE)**: Deploy to FastMCP Cloud for team/organization access

### Option 1: Local Deployment (stdio)

#### Running the Server

**Using uv (recommended):**
```bash
uv run python openproject-mcp-fastmcp.py
```

**Alternative (manual activation):**
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the server
python openproject-mcp-fastmcp.py
```

**File Structure:**
- `openproject-mcp-fastmcp.py` - Stdio transport (for local Claude Desktop)
- `openproject-mcp-sse.py` - SSE transport (for FastMCP Cloud)
- `src/` - Core implementation using FastMCP framework
  - `src/server.py` - FastMCP server initialization
  - `src/client.py` - OpenProject API client
  - `src/tools/` - All 40+ MCP tools organized by category

#### Integration with Claude Desktop

**Quick Install Using CLI (Recommended):**

This command works for both **Claude Desktop** and **Claude Code (VSCode extension)**.

```powershell
# Windows - Replace <YOUR_PROJECT_PATH> with your actual path
claude mcp add openproject-fastmcp "<YOUR_PROJECT_PATH>\.venv\Scripts\python.exe" "<YOUR_PROJECT_PATH>\openproject-mcp-fastmcp.py" -e "PYTHONPATH=<YOUR_PROJECT_PATH>" -e "OPENPROJECT_URL=https://your-instance.com" -e "OPENPROJECT_API_KEY=your-api-key"
```

```bash
# macOS/Linux - Replace <YOUR_PROJECT_PATH> with your actual path
claude mcp add openproject-fastmcp "<YOUR_PROJECT_PATH>/.venv/bin/python" "<YOUR_PROJECT_PATH>/openproject-mcp-fastmcp.py" -e "PYTHONPATH=<YOUR_PROJECT_PATH>" -e "OPENPROJECT_URL=https://your-instance.com" -e "OPENPROJECT_API_KEY=your-api-key"
```

**Example (Windows):**
```powershell
# If you cloned the project to C:\Users\YourName\openproject-mcp-server
claude mcp add openproject-fastmcp "C:\Users\YourName\openproject-mcp-server\.venv\Scripts\python.exe" "C:\Users\YourName\openproject-mcp-server\openproject-mcp-fastmcp.py" -e "PYTHONPATH=C:\Users\YourName\openproject-mcp-server" -e "OPENPROJECT_URL=https://manage.example.com" -e "OPENPROJECT_API_KEY=abc123xyz456"
```

**Example (macOS/Linux):**
```bash
# If you cloned the project to /home/yourname/openproject-mcp-server
claude mcp add openproject-fastmcp "/home/yourname/openproject-mcp-server/.venv/bin/python" "/home/yourname/openproject-mcp-server/openproject-mcp-fastmcp.py" -e "PYTHONPATH=/home/yourname/openproject-mcp-server" -e "OPENPROJECT_URL=https://manage.example.com" -e "OPENPROJECT_API_KEY=abc123xyz456"
```

**Important:** Replace the following values:
- `<YOUR_PROJECT_PATH>` with your actual installation directory
- `https://your-instance.com` with your OpenProject URL
- `your-api-key` with your API key from Account Settings

**Verify Installation:**
```powershell
claude mcp list
```

You should see:
```
openproject-fastmcp: ... - ✓ Connected
```

After running the command, restart Claude Desktop or reload VSCode window.

---

**Manual Configuration:**

Add this configuration to your Claude Desktop config file:

**Config file locations:**
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Windows Configuration:**
```json
{
  "mcpServers": {
    "openproject-fastmcp": {
      "command": "D:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["D:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "D:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server",
        "OPENPROJECT_URL": "https://your-instance.com",
        "OPENPROJECT_API_KEY": "your-api-key"
      }
    }
  }
}
```

**macOS/Linux Configuration:**
```json
{
  "mcpServers": {
    "openproject-fastmcp": {
      "command": "/path/to/project/.venv/bin/python",
      "args": ["/path/to/project/openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "/path/to/project",
        "OPENPROJECT_URL": "https://your-instance.com",
        "OPENPROJECT_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Note:** Using environment variables in config is more secure than storing credentials in `.env` file.

**Verification:**

Check if the server is connected:
```powershell
claude mcp list
```

You should see:
```
openproject-fastmcp: ... - ✓ Connected
```

If you see `✗ Failed to connect`, check:
1. Python path is correct
2. `openproject-mcp-fastmcp.py` file exists
3. Environment variables are set correctly
4. Restart Claude Desktop after configuration changes

### Option 2: Cloud Deployment (FastMCP Cloud) ☁️

Deploy to FastMCP Cloud for centralized access across your organization. This eliminates the need for each user to install Python and run the server locally.

**Benefits:**
- No local installation required for end users
- Centralized API key and configuration management
- Access from anywhere with internet
- Automatic scaling and monitoring
- Team collaboration features

**Quick Start:**

1. **Ensure you have the SSE entry point:**
   ```bash
   # The project includes openproject-mcp-sse.py for cloud deployment
   ls openproject-mcp-sse.py
   ```

2. **Create/update .fastmcp.yaml config:**
   ```yaml
   name: openproject-mcp
   version: "1.0.0"
   description: "OpenProject MCP Server for Claude Desktop"

   entry_point: openproject-mcp-sse.py

   runtime:
     python_version: "3.11"

   environment:
     - OPENPROJECT_URL
     - OPENPROJECT_API_KEY
     - OPENPROJECT_PROXY
   ```

3. **Deploy to FastMCP Cloud:**
   ```bash
   # Install FastMCP CLI (if not installed)
   pip install fastmcp

   # Login to FastMCP Cloud
   fastmcp login

   # Deploy your server
   fastmcp deploy
   ```

4. **Configure environment variables** on FastMCP Cloud dashboard:
   - `OPENPROJECT_URL`: Your OpenProject instance URL
   - `OPENPROJECT_API_KEY`: Your API key
   - `OPENPROJECT_PROXY`: (Optional) Proxy URL if needed

5. **Users connect via Claude Desktop** with SSE transport:
   ```json
   {
     "mcpServers": {
       "openproject": {
         "url": "https://mcp.fastmcp.com/sse/openproject-mcp",
         "transport": "sse"
       }
     }
   }
   ```

**📚 Detailed Documentation:**
- [Quick Start Guide](QUICK_START_CLOUD.md) - Fast setup in 5 minutes
- [FastMCP Cloud Deployment Guide (English)](FASTMCP_CLOUD_DEPLOYMENT.md) - Comprehensive guide
- [Hướng dẫn kết nối Cloud (Tiếng Việt)](HUONG_DAN_KET_NOI_CLOUD.md) - Vietnamese guide

For comprehensive deployment instructions, troubleshooting, and best practices, see the guides above.

### Available Tools

#### 1. `test_connection`
Test the connection to your OpenProject instance.

**Example:**
```
Test the OpenProject connection
```

#### 2. `list_projects`
List all projects you have access to.

**Parameters:**
- `active_only` (boolean, optional): Show only active projects (default: true)

**Example:**
```
List all active projects
```

#### 3. `list_work_packages` ⭐ ENHANCED
List work packages with advanced filtering capabilities - the most powerful search tool.

**Basic Parameters:**
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `active_only` (boolean, optional): Only open tasks (default: true)
- `offset` (integer, optional): Pagination offset (default: 0)
- `page_size` (integer, optional): Results per page (default: 20, max: 100)

**Advanced Filters (NEW - 18 parameters):**
- `priority_ids` (string, optional): Comma-separated priority IDs (e.g., "3,4")
- `type_ids` (string, optional): Comma-separated type IDs (e.g., "1,2")
- `status_ids` (string, optional): Comma-separated status IDs (overrides active_only)
- `version_ids` (string, optional): Comma-separated version/sprint IDs
- `due_before` (string, optional): Due before date (YYYY-MM-DD)
- `due_after` (string, optional): Due after date (YYYY-MM-DD)
- `created_after` (string, optional): Created after date (YYYY-MM-DD)
- `updated_after` (string, optional): Updated after date (YYYY-MM-DD)
- `unassigned_only` (boolean, optional): Only unassigned tasks
- `overdue_only` (boolean, optional): Only overdue tasks
- `percentage_done_min` (integer, optional): Min completion % (0-100)
- `percentage_done_max` (integer, optional): Max completion % (0-100)
- `author_id` (integer, optional): Filter by task creator
- `parent_id` (integer, optional): Child tasks of parent
- `no_parent_only` (boolean, optional): Only top-level tasks

**Features:**
- **23 total parameters** for ultimate flexibility
- All filters use AND logic
- 100% backward compatible
- Smart filter priority (e.g., status_ids > active_only)

**Examples:**
```
Find high-priority bugs due this week in project 5
```
```
Find overdue unassigned tasks
```
```
Show tasks 50-80% complete
```

#### 4. `search_work_packages`
Search work packages by subject or ID using server-side filtering.

**Parameters:**
- `query` (string, required): Search text to match against work package subject or ID
- `project_id` (integer, optional): Limit search to a specific project
- `active_only` (boolean, optional): Search only open work packages (default: true)
- `offset` (integer, optional): Starting index for pagination (default: 0)
- `page_size` (integer, optional): Number of results per page (default: 20, max: 100)
- `full_text` (boolean, optional): Also search description and comments (default: false) – see [Agent Context Tools](#agent-context-tools-)

**Example:**
```
Search for tasks containing "login"
```
```
Search for work package by ID: "123"
```

**Note:** This tool provides fast search without needing to paginate through all tasks. Use this when you need to find specific tasks by name or ID.

#### 5. `list_types`
List available work package types.

**Parameters:**
- `project_id` (integer, optional): Filter types by project

**Example:**
```
List all work package types
```

#### 6. `create_work_package`
Create a new work package.

**Parameters:**
- `project_id` (integer, required): The project ID
- `subject` (string, required): Work package title
- `type_id` (integer, required): Type ID (e.g., 1 for Task)
- `description` (string, optional): Description in Markdown format
- `priority_id` (integer, optional): Priority ID
- `assignee_id` (integer, optional): User ID to assign to

**Example:**
```
Create a new task in project 5 titled "Update documentation" with type ID 1
```

#### 7. `list_users`
List all users in the OpenProject instance.

**Parameters:**
- `active_only` (boolean, optional): Show only active users (default: true)

#### 8. `get_user`
Get detailed information about a specific user.

**Parameters:**
- `user_id` (integer, required): User ID

#### 9. `list_memberships`
List project memberships showing users and their roles.

**Parameters:**
- `project_id` (integer, optional): Filter by specific project
- `user_id` (integer, optional): Filter by specific user

#### 10. `list_statuses`
List all available work package statuses.

#### 11. `list_priorities`
List all available work package priorities.

#### 12. `get_work_package`
Get full details of a work package, including the untruncated description and custom fields by name.

**Parameters:**
- `work_package_id` (integer, required): Work package ID
- `format` (string, optional): `markdown` (default) or `json`

See [Agent Context Tools](#agent-context-tools-) for `get_work_package_context`, attachments, notifications, saved views and more.

#### 13. `update_work_package`
Update an existing work package.

**Parameters:**
- `work_package_id` (integer, required): Work package ID
- `subject` (string, optional): Work package title
- `description` (string, optional): Description in Markdown format
- `type_id` (integer, optional): Type ID
- `status_id` (integer, optional): Status ID
- `priority_id` (integer, optional): Priority ID
- `assignee_id` (integer, optional): User ID to assign to
- `percentage_done` (integer, optional): Completion percentage (0-100)

#### 13. `delete_work_package`
Delete a work package.

**Parameters:**
- `work_package_id` (integer, required): Work package ID

### Advanced Filters 🔍

The following tools provide specialized filtering capabilities for common work package search scenarios. All tools support flexible filtering by project, assignee, priority, and type.

#### 14. `list_overdue_work_packages`
List all work packages that are past their due date.

**Parameters:**
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `priority_ids` (string, optional): Comma-separated priority IDs (e.g., "3,4")
- `type_ids` (string, optional): Comma-separated type IDs (e.g., "1,2")
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Shows "X days overdue" for each task
- Sorted by most overdue first
- Only searches open (non-closed) tasks

**Example:**
```
Find all overdue high-priority tasks in project 5
```

#### 15. `list_work_packages_due_soon`
List work packages due within the next N days.

**Parameters:**
- `days` (integer, optional): Days to look ahead (default: 7, max: 365)
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `priority_ids` (string, optional): Comma-separated priority IDs
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Shows "Due in X days", "Due tomorrow", or "Due today!"
- Sorted by soonest first
- Configurable lookahead period

**Example:**
```
Show me tasks due in the next 3 days
```

#### 16. `list_unassigned_work_packages`
List work packages that have no assignee.

**Parameters:**
- `project_id` (integer, optional): Filter by project
- `priority_ids` (string, optional): Comma-separated priority IDs
- `type_ids` (string, optional): Comma-separated type IDs
- `active_only` (boolean, optional): Only open tasks (default: true)
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Identifies tasks needing assignment
- Useful for sprint planning
- Supports priority and type filtering

**Example:**
```
Find unassigned high-priority bugs in project 5
```

#### 17. `list_work_packages_created_recently`
List work packages created in the last N days.

**Parameters:**
- `days` (integer, optional): Days to look back (default: 7, max: 365)
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `type_ids` (string, optional): Comma-separated type IDs
- `active_only` (boolean, optional): Only open tasks (default: true)
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Track new task creation patterns
- Sorted by newest first
- Configurable lookback period

**Example:**
```
Show bugs created in the last 3 days
```

#### 18. `list_high_priority_work_packages`
List work packages with high priority.

**Parameters:**
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `type_ids` (string, optional): Comma-separated type IDs
- `active_only` (boolean, optional): Only open tasks (default: true)
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Assumes priority ID 3 = "High" (typical default)
- Includes helpful note about using `list_priorities` if needed
- Quick access to urgent tasks

**Example:**
```
Show all high-priority tasks in project 5
```

**Note:** If your OpenProject instance uses different priority IDs, use `list_priorities` to find the correct ID, then use the enhanced `list_work_packages` with specific `priority_ids` parameter.

#### 19. `list_work_packages_nearly_complete`
List work packages that are nearly complete (high percentage done).

**Parameters:**
- `project_id` (integer, optional): Filter by project
- `assignee_id` (integer, optional): Filter by assignee
- `min_percentage` (integer, optional): Minimum completion % (default: 80, range: 1-99)
- `active_only` (boolean, optional): Only open tasks (default: true)
- `page_size` (integer, optional): Results per page (default: 50, max: 100)

**Features:**
- Find tasks needing final push
- Sorted by highest percentage first
- Includes completion summary section
- Useful for sprint reviews

**Example:**
```
Show tasks more than 90% complete
```

#### 20. `list_time_entries`
List time entries with optional filtering.

**Parameters:**
- `work_package_id` (integer, optional): Filter by specific work package
- `user_id` (integer, optional): Filter by specific user

#### 15. `create_time_entry`
Create a new time entry.

**Parameters:**
- `work_package_id` (integer, required): Work package ID
- `hours` (number, required): Hours spent (e.g., 2.5)
- `spent_on` (string, required): Date when time was spent (YYYY-MM-DD format)
- `comment` (string, optional): Comment/description
- `activity_id` (integer, optional): Activity ID

#### 16. `update_time_entry`
Update an existing time entry.

**Parameters:**
- `time_entry_id` (integer, required): Time entry ID
- `hours` (number, optional): Hours spent
- `spent_on` (string, optional): Date when time was spent
- `comment` (string, optional): Comment/description
- `activity_id` (integer, optional): Activity ID

#### 17. `delete_time_entry`
Delete a time entry.

**Parameters:**
- `time_entry_id` (integer, required): Time entry ID

#### 18. `list_time_entry_activities`
List available time entry activities.

#### 19. `list_versions`
List project versions/milestones.

**Parameters:**
- `project_id` (integer, optional): Filter by specific project

#### 20. `create_version`
Create a new project version/milestone.

**Parameters:**
- `project_id` (integer, required): Project ID
- `name` (string, required): Version name
- `description` (string, optional): Version description
- `start_date` (string, optional): Start date (YYYY-MM-DD format)
- `end_date` (string, optional): End date (YYYY-MM-DD format)
- `status` (string, optional): Version status (open, locked, closed)

#### 21. `create_project`
Create a new project.

**Parameters:**
- `name` (string, required): Project name
- `identifier` (string, required): Project identifier (unique)
- `description` (string, optional): Project description
- `public` (boolean, optional): Whether the project is public
- `status` (string, optional): Project status
- `parent_id` (integer, optional): Parent project ID

**Example:**
```
Create a new project named "Website Redesign" with identifier "web-redesign"
```

#### 22. `update_project`
Update an existing project.

**Parameters:**
- `project_id` (integer, required): Project ID
- `name` (string, optional): Project name
- `identifier` (string, optional): Project identifier
- `description` (string, optional): Project description
- `public` (boolean, optional): Whether the project is public
- `status` (string, optional): Project status
- `parent_id` (integer, optional): Parent project ID

#### 23. `delete_project`
Delete a project.

**Parameters:**
- `project_id` (integer, required): Project ID

#### 24. `get_project`
Get detailed information about a specific project.

**Parameters:**
- `project_id` (integer, required): Project ID

#### 25. `create_membership`
Create a new project membership.

**Parameters:**
- `project_id` (integer, required): Project ID
- `user_id` (integer, optional): User ID (required if group_id not provided)
- `group_id` (integer, optional): Group ID (required if user_id not provided)
- `role_ids` (array, optional): Array of role IDs
- `role_id` (integer, optional): Single role ID (alternative to role_ids)
- `notification_message` (string, optional): Optional notification message

**Example:**
```
Add user 5 to project 2 with role ID 3 (Developer role)
```

#### 26. `update_membership`
Update an existing membership.

**Parameters:**
- `membership_id` (integer, required): Membership ID
- `role_ids` (array, optional): Array of role IDs
- `role_id` (integer, optional): Single role ID
- `notification_message` (string, optional): Optional notification message

#### 27. `delete_membership`
Delete a membership.

**Parameters:**
- `membership_id` (integer, required): Membership ID

#### 28. `get_membership`
Get detailed information about a specific membership.

**Parameters:**
- `membership_id` (integer, required): Membership ID

#### 29. `list_project_members`
List all members of a specific project.

**Parameters:**
- `project_id` (integer, required): Project ID

**Example:**
```
List all members of project 5
```

#### 30. `list_user_projects`
List all projects a specific user is assigned to.

**Parameters:**
- `user_id` (integer, required): User ID

#### 31. `list_roles`
List all available roles.

**Example:**
```
List all available roles in the OpenProject instance
```

#### 32. `get_role`
Get detailed information about a specific role.

**Parameters:**
- `role_id` (integer, required): Role ID

#### 33. `set_work_package_parent`
Set a parent for a work package (create parent-child relationship).

**Parameters:**
- `work_package_id` (integer, required): Work package ID to become a child
- `parent_id` (integer, required): Work package ID to become the parent

**Example:**
```
Set work package 15 as a child of work package 10
```

#### 34. `remove_work_package_parent`
Remove parent relationship from a work package (make it top-level).

**Parameters:**
- `work_package_id` (integer, required): Work package ID to remove parent from

#### 35. `list_work_package_children`
List all child work packages of a parent.

**Parameters:**
- `parent_id` (integer, required): Parent work package ID
- `include_descendants` (boolean, optional): Include grandchildren and all descendants (default: false)

**Example:**
```
List all children of work package 10 including descendants
```

#### 36. `create_work_package_relation`
Create a relationship between work packages.

**Parameters:**
- `from_id` (integer, required): Source work package ID
- `to_id` (integer, required): Target work package ID
- `relation_type` (string, required): Relation type (blocks, follows, precedes, relates, duplicates, includes, requires, partof)
- `lag` (integer, optional): Lag in working days (for follows/precedes)
- `description` (string, optional): Optional description of the relation

**Example:**
```
Create a "blocks" relation where work package 5 blocks work package 8
```

#### 37. `list_work_package_relations`
List work package relations with optional filtering.

**Parameters:**
- `work_package_id` (integer, optional): Filter relations involving this work package ID
- `relation_type` (string, optional): Filter by relation type

#### 38. `update_work_package_relation`
Update an existing work package relation.

**Parameters:**
- `relation_id` (integer, required): Relation ID
- `relation_type` (string, optional): New relation type
- `lag` (integer, optional): Lag in working days
- `description` (string, optional): Optional description

#### 39. `delete_work_package_relation`
Delete a work package relation.

**Parameters:**
- `relation_id` (integer, required): Relation ID

#### 40. `get_work_package_relation`
Get detailed information about a specific work package relation.

**Parameters:**
- `relation_id` (integer, required): Relation ID

## Agent Context Tools 🤖

Tools designed for coding agents (e.g. Claude Code) working on OpenProject tasks. All new read tools accept `format="markdown"` (default) or `format="json"` – JSON contains the same data. Write tools are marked ✏️ and are removed in read-only mode (`OPENPROJECT_READ_ONLY=true`).

### Work package context

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_work_package` | Full details of a single work package: subject, type, status, priority, project, assignee, responsible, author, version, dates, progress, parent, custom fields (by schema name, human-readable values) and the complete, untruncated description (raw markdown). | `work_package_id` (int), `format` |
| `get_work_package_context` | Everything an agent needs in one call: details + custom fields, full comments, attachment list (metadata only), relations, hierarchy (parent + children) and IDs of images referenced in the description (fetch them with `get_attachment`). Sections are fetched in parallel; a failing section (e.g. 403) is reported inline and does not break the others. | `work_package_id` (int), `include_comments`, `include_attachments`, `include_relations`, `include_hierarchy` (bool, default `true`), `format` |
| `get_allowed_statuses` | Statuses the current user may set on the work package according to the workflow; the current status is marked. Read-only (uses the form endpoint with the current `lockVersion`, nothing is saved). | `work_package_id` (int), `format` |
| `list_work_package_activities` | Activity history with full comments (no truncation), author, date, internal-comment marker and every field change as readable text. | `work_package_id` (int), `comments_only` (bool, default `false`) |

### Watchers

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_watchers` | Users watching a work package (ID and name). | `work_package_id` (int), `format` |
| `add_watcher` ✏️ | Add a user as a watcher. | `work_package_id` (int), `user_id` (int) |
| `remove_watcher` ✏️ | Remove a user from the watchers. | `work_package_id` (int), `user_id` (int) |

### Attachments

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_work_package_attachments` | Attachments of a work package: ID, file name, MIME type, size, author, date, description (size also in bytes in JSON). | `work_package_id` (int), `format` |
| `get_attachment` | Returns an attachment in the most useful form for the model: images as viewable image content, text as text, other files saved to a local directory (see below). | `attachment_id` (int), `max_dimension` (64–4096, default 1600) |
| `upload_attachment` ✏️ | Uploads a local file (max 25 MB) as a work package attachment and returns the new attachment ID. | `work_package_id` (int), `file_path` (str), `description` (str, optional) |

**How `get_attachment` handles file types**

- **Images** (`image/png`, `image/jpeg`, `image/gif`, `image/webp`) are returned as MCP image content with a short text summary (original → returned dimensions and size). Images whose longer side exceeds `max_dimension` or whose size exceeds ~750 KB are proportionally downscaled with Pillow; if still too large, they are re-encoded as JPEG with decreasing quality. For GIFs only the first frame is returned (as PNG). Without Pillow, images up to ~750 KB are returned unscaled and larger ones are saved to disk.
- **Text** (`text/*`, JSON, XML, YAML, and `.md`, `.csv`, `.log`, `.yml`, `.yaml`, `.json`, `.xml`, `.txt` when the MIME type is `application/octet-stream`) up to 200 KB is returned inline as UTF-8 in a code block.
- **Everything else** (PDF, DOCX, archives, executables, text over 200 KB) is saved to `OPENPROJECT_ATTACHMENTS_DIR` (default `<system temp>/openproject-attachments`) as `{attachment_id}_{sanitized_file_name}`; the response contains the full path, name, size and MIME type. Downloads larger than 25 MB are rejected.

**Security:** file names are sanitized (path components such as `../` and `..\` are stripped, `<>:"/\|?*` and control characters removed, max 150 characters) and the resolved path must stay inside the attachments directory. Saved files are **never opened or executed** by the server. When a download redirects to another host (e.g. an S3 presigned URL), the API key is not sent to that host. `upload_attachment` validates the local file before any request is sent – it can upload any file readable by the server process, so use read-only mode for agents that must not write.

### Work discovery

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_my_work_packages` | Work packages assigned to the API key owner (no user ID needed); open only by default. | `project_id?`, `include_closed=false`, `offset=1` (page, 1-based), `page_size=20` (max 100), `format` |
| `list_work_packages` | *(new parameter)* `assigned_to_me=true` limits results to your own tasks; cannot be combined with `assignee_id` / `unassigned_only`. | `assigned_to_me=false` + existing filters |
| `search_work_packages` | *(new parameter)* `full_text=true` searches subject, description and comments instead of subject/ID only. | `query`, `full_text=false` + existing parameters |
| `list_queries` | Saved work package views (queries): name, ID, project, public, starred. | `project_id?`, `format` |
| `run_query` | Runs a saved view with its own filters and sort order; returns the view name, total and a page of work packages. | `query_id`, `offset=1`, `page_size=20`, `format` |
| `list_notifications` | Your in-app notifications (reason, actor, date, work package ID + subject, project). Read only – never marks them as read. | `unread_only=true`, `reason?` (mentioned, assigned, responsible, watched, subscribed, commented, created, processed, prioritized, scheduled, dateAlert, shared, reminder), `offset=1`, `page_size=20`, `format` |

### Versions / sprints

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_version` | Version details: name, description, status, start/end date, sharing, defining project. | `version_id`, `format` |
| `list_version_work_packages` | Work packages assigned to a version (sprint scope), all statuses by default. Queried within the version's defining project and its subprojects (OpenProject 15 rejects the version filter on the global endpoint); for versions shared as `hierarchy`, `tree` or `system` the response includes a `scope_note` warning. | `version_id`, `include_closed=true`, `offset=1`, `page_size=20`, `format` |
| `update_version` ✏️ | Updates only the provided fields of a version. | `version_id`, `name?`, `description?`, `status?` (open, locked, closed), `start_date?`, `end_date?` (YYYY-MM-DD), `sharing?` (none, descendants, hierarchy, tree, system) |

### Code & file integrations

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_work_package_code_links` | Items linked to a work package, one section per source: GitHub pull requests, GitLab merge requests, GitLab issues and file links (external storages such as Nextcloud/OneDrive). Each item has title, state and URL, plus number/repository/author for code and storage/MIME type/size for files. A source is marked **unavailable** if the work package has no matching `_links` entry (no request is sent) or the endpoint returns 403/404 (module disabled or missing permission); the other sources are still returned. | `work_package_id` (int), `format` |

### MCP resources and prompts

| Name | Kind | Description |
|------|------|-------------|
| `openproject://work-packages/{work_package_id}` | resource | Aggregated work package context (same content as `get_work_package_context`) as markdown – attach it to a conversation, e.g. `openproject://work-packages/123`. |
| `plan_work_package(work_package_id)` | prompt | Tells the model to first call `get_work_package_context`, then `get_attachment` for images referenced in the description and `list_work_package_code_links`, and to produce an implementation plan: goal, steps, open questions, risks and acceptance criteria. |
| `summarize_work_package(work_package_id)` | prompt | Same context-gathering steps, then a concise summary: goal, current state, recent decisions from comments, and blockers. |

Prompts contain instructions only and make no API calls themselves; prompt arguments arrive as strings over MCP and are converted to integers automatically.

## Development

### Setting up Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Or install manually
uv pip install -e ".[dev]"
```

### Running Tests

```bash
uv sync --extra dev
uv run pytest
```

Unit tests live in `tests/` and run without a live OpenProject instance (HTTP is mocked with `aioresponses`). The `test_*.py` scripts in the repository root require a live instance and are not collected by `pytest`.

### Code Formatting

```bash
# Format code
uv run black openproject-mcp.py

# Lint code
uv run flake8 openproject-mcp.py
```

### Adding Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update dependencies
uv sync
```

## Tool Compatibility & Test Results

### ✅ Fully Working Tools (40/42)
All these tools have been tested and work correctly with admin privileges:

**Core Project Management:**
- `test_connection`, `check_permissions`, `list_projects`, `create_project`, `update_project`
- `delete_project`, `get_project`

**Work Package Management:**
- `list_work_packages`, `search_work_packages`, `list_types`, `create_work_package`, `update_work_package`
- `delete_work_package`, `get_work_package`, `list_statuses`, `list_priorities`

**Work Package Hierarchy & Relations:**
- `set_work_package_parent`, `remove_work_package_parent`, `list_work_package_children`
- `create_work_package_relation`, `list_work_package_relations`, `update_work_package_relation`
- `delete_work_package_relation`, `get_work_package_relation`

**User & Membership Management:**
- `list_users`, `get_user`, `create_membership`, `update_membership`, `delete_membership`
- `get_membership`, `list_project_members`, `list_user_projects`, `list_roles`, `get_role`

**Time Tracking:**
- `list_time_entries`, `create_time_entry`, `update_time_entry`, `delete_time_entry`

**Project Versions:**
- `list_versions`, `create_version`

### ⚠️ Partially Working Tools
- **`list_memberships`**: Works globally and with `project_id` filtering. User ID filtering (`user_id`) may not be supported in all OpenProject instances.

### ❌ Endpoint Limitations with Workarounds
- **`list_time_entry_activities`**: Returns 404 but time entry activities ARE functional! Use these predefined activity IDs:
  - **Management (ID: 1)**: Administrative and planning tasks
  - **Specification (ID: 2)**: Requirements and documentation  
  - **Development (ID: 3)**: Coding and implementation
  - **Testing (ID: 4)**: Quality assurance and testing

**Example**: `create_time_entry` with `activity_id: 3` for Development work

### Permission Requirements
Most create/update/delete operations require appropriate permissions:
- **Project Operations**: Require global "Create project" and "Edit project" permissions. Deletion typically requires admin rights
- **Work Package Operations**: Require "Create/Edit work packages" permission in target projects
- **Work Package Relations & Hierarchy**: Require "Edit work packages" permission for creating/modifying parent-child relationships and dependencies
- **Membership Management**: Require "Manage members" permission for target projects
- **Time Entry Operations**: Require time tracking permissions
- **Version Management**: Require project admin or version management permissions
- **User Operations**: Admin privileges may be needed for comprehensive user management
- **Role Management**: Read-only operations generally available; admin privileges may be needed for detailed role information

Use the `check_permissions` tool to diagnose permission-related issues.

## Troubleshooting

### Connection Issues

1. **401 Unauthorized**: Check your API key is correct and active
2. **403 Forbidden**: Ensure your user has the necessary permissions
3. **404 Not Found**: Verify the OpenProject URL and that resources exist
4. **Proxy Errors**: Check proxy settings and authentication

### Debug Mode

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

### Common Issues

- **No projects found**: Ensure your API user has project view permissions
- **SSL errors**: May occur with self-signed certificates or proxy SSL interception
- **Timeout errors**: Increase timeout or check network connectivity

## Security Considerations

- Never commit your `.env` file to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use HTTPS for all OpenProject connections
- Configure proxy authentication securely if needed

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the [Model Context Protocol](https://modelcontextprotocol.io/)
- Integrates with [OpenProject](https://www.openproject.org/)
- Inspired by the MCP community

## Support

- 🐛 Issues: [GitHub Issues](https://github.com/AndyEverything/openproject-mcp-server/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/AndyEverything/openproject-mcp-server/discussions)
