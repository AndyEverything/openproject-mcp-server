<br>![status](https://img.shields.io/badge/status-WIP-yellow) ![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)<br><br>⚠️ This is an early-stage project. Do not use it productively – contributions welcome!<br>

# OpenProject MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with [OpenProject](https://www.openproject.org/) API v3. This server enables LLM applications to interact with OpenProject for project management, work package tracking, and task creation.

## Features

- 🔌 **Full OpenProject API v3 Integration**
- 📋 **Project Management**: List and filter projects
- 📝 **Work Package Management**: Create, list, and filter work packages
- 🔗 **Work Package Relationships**: Create, list, and delete relationships (blocks, follows, relates to, etc.)
- 🏷️ **Type Management**: List available work package types
- 👥 **User Management**: List users and manage assignments
- 📅 **Meeting Management**: Create meetings, manage agendas, track minutes, and schedule recurring meetings
- ✅ **Task Management**: Create follow-up tasks from meeting action items
- 🔐 **Secure Authentication**: API key-based authentication
- 🌐 **Proxy Support**: Optional HTTP proxy configuration
- 🚀 **Async Operations**: Built with modern async/await patterns
- 📊 **Comprehensive Logging**: Configurable logging levels

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

### Getting an API Key

1. Log in to your OpenProject instance
2. Go to **My account** (click your avatar)
3. Navigate to **Access tokens**
4. Click **+ Add** to create a new token
5. Give it a name and copy the generated token

## Usage

### Running the Server

**Using uv (recommended):**
```bash
uv run python openproject-mcp.py
```

**Alternative (manual activation):**
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the server
python openproject-mcp.py
```

**Note:** If you renamed the file from `openproject_mcp_server.py`, update your configuration accordingly.

### Integration with Claude Desktop

Add this configuration to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openproject": {
      "command": "/path/to/your/project/.venv/bin/python",
      "args": ["/path/to/your/project/openproject-mcp.py"]
    }
  }
}
```

**Note:** Replace `/path/to/your/project/` with the actual path to your project directory.

**Alternative with uv (if uv is in your system PATH):**
```json
{
  "mcpServers": {
    "openproject": {
      "command": "uv",
      "args": ["run", "python", "/path/to/your/project/openproject-mcp.py"]
    }
  }
}
```

**Why use the direct Python path?**
The direct Python path approach is more reliable because:
- It doesn't require `uv` to be in the system PATH
- It avoids potential issues with `uv run` trying to install the project as a package
- It's simpler and more straightforward for MCP server configurations

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

#### 3. `list_work_packages`
List work packages with optional filtering.

**Parameters:**
- `project_id` (integer, optional): Filter by specific project
- `status` (string, optional): Filter by status - "open", "closed", or "all" (default: "open")

**Example:**
```
Show all open work packages in project 5
```

#### 4. `list_types`
List available work package types.

**Parameters:**
- `project_id` (integer, optional): Filter types by project

**Example:**
```
List all work package types
```

#### 5. `create_work_package`
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

#### 6. `create_work_package_relation`
Create a relationship between two work packages.

**Parameters:**
- `work_package_id` (integer, required): ID of the source work package
- `relation_type` (string, required): Type of relationship - "blocks", "follows", "relates", "duplicates", "includes", or "requires"
- `target_work_package_id` (integer, required): ID of the target work package
- `description` (string, optional): Description of the relationship
- `lag` (integer, optional): Lag in days (for "follows" relationships)

**Example:**
```
Create a "blocks" relationship from work package 123 to work package 456
```

#### 7. `list_work_package_relations`
List all relationships for a work package.

**Parameters:**
- `work_package_id` (integer, required): ID of the work package

**Example:**
```
List all relationships for work package 123
```

#### 8. `delete_work_package_relation`
Delete a work package relationship.

**Parameters:**
- `relation_id` (integer, required): ID of the relationship to delete

**Example:**
```
Delete relationship 789
```

#### 9. `list_users`
List users in the OpenProject instance.

**Parameters:**
- `active_only` (boolean, optional): Show only active users (default: true)

**Example:**
```
List all active users
```

#### 10. `list_priorities`
List available work package priorities.

**Example:**
```
List all work package priorities
```

#### 11. `list_statuses`
List available work package statuses.

**Example:**
```
List all work package statuses
```

#### 12. `update_work_package`
Update an existing work package.

**Parameters:**
- `work_package_id` (integer, required): ID of the work package to update
- `subject` (string, optional): Updated work package title
- `description` (string, optional): Updated description in Markdown format
- `status_id` (integer, optional): Status ID to update to
- `priority_id` (integer, optional): Priority ID to update to
- `assignee_id` (integer, optional): User ID to assign to

**Example:**
```
Update work package 123 with new subject "Updated task title"
```

#### 13. `create_meeting`
Create a meeting work package with agenda and attendees.

**Parameters:**
- `project_id` (integer, required): Project ID
- `meeting_title` (string, required): Meeting title
- `meeting_date` (string, required): Meeting date (YYYY-MM-DD format)
- `meeting_time` (string, required): Meeting time (HH:MM format)
- `duration_minutes` (integer, optional): Meeting duration in minutes (default: 60)
- `attendees` (array, optional): Array of user IDs for attendees
- `agenda` (string, optional): Meeting agenda items
- `meeting_type` (string, optional): Type of meeting - "standup", "sprint_planning", "retrospective", "review", or "general" (default: "general")
- `location` (string, optional): Meeting location or video call link

**Example:**
```
Create a standup meeting for project 5 titled "Daily Standup" on 2024-01-15 at 09:00 with 30 minutes duration
```

#### 14. `add_meeting_minutes`
Add minutes and outcomes to a meeting work package.

**Parameters:**
- `meeting_work_package_id` (integer, required): ID of the meeting work package
- `minutes` (string, required): Meeting minutes and discussion points
- `decisions` (string, optional): Decisions made during the meeting
- `action_items` (array, optional): Action items from the meeting
- `next_meeting_date` (string, optional): Date for next meeting (YYYY-MM-DD format)

**Example:**
```
Add minutes to meeting work package 456 with discussion points and 3 action items
```

#### 15. `create_follow_up_tasks`
Create follow-up tasks from meeting action items.

**Parameters:**
- `meeting_work_package_id` (integer, required): ID of the meeting work package
- `action_items` (array, required): Action items to create as work packages

**Example:**
```
Create follow-up tasks from meeting 456 with action items for John and Sarah
```

#### 16. `list_meetings`
List meeting work packages.

**Parameters:**
- `project_id` (integer, optional): Project ID (for project-specific meetings)
- `meeting_type` (string, optional): Filter by meeting type
- `date_from` (string, optional): Filter meetings from this date (YYYY-MM-DD)
- `date_to` (string, optional): Filter meetings to this date (YYYY-MM-DD)
- `status` (string, optional): Filter by status - "scheduled", "completed", or "cancelled" (default: "scheduled")

**Example:**
```
List all standup meetings in project 5 scheduled for this week
```

#### 17. `schedule_recurring_meeting`
Schedule a recurring meeting series.

**Parameters:**
- `project_id` (integer, required): Project ID
- `meeting_title` (string, required): Meeting title
- `start_date` (string, required): First meeting date (YYYY-MM-DD format)
- `meeting_time` (string, required): Meeting time (HH:MM format)
- `frequency` (string, required): Meeting frequency - "daily", "weekly", "biweekly", or "monthly"
- `occurrences` (integer, optional): Number of meetings to create (default: 10)
- `duration_minutes` (integer, optional): Meeting duration in minutes (default: 60)
- `attendees` (array, optional): Array of user IDs for attendees
- `agenda_template` (string, optional): Template agenda for all meetings
- `meeting_type` (string, optional): Type of meeting (default: "general")
- `location` (string, optional): Meeting location or video call link

**Example:**
```
Schedule weekly sprint planning meetings for project 5 starting 2024-01-15 at 10:00 for 8 occurrences
```

### Work Package Relationship Types

OpenProject supports several types of relationships between work packages:

- **`blocks`**: The source work package blocks the target work package from being completed
- **`follows`**: The source work package follows (comes after) the target work package
- **`relates`**: A general relationship between work packages
- **`duplicates`**: The source work package duplicates the target work package
- **`includes`**: The source work package includes the target work package
- **`requires`**: The source work package requires the target work package

**Note**: When you create a relationship, OpenProject automatically creates the reverse relationship on the target work package. For example, if you create a "blocks" relationship from A to B, work package B will automatically have a "blocked by" relationship to A.

### Meeting Management Workflow

The meeting management tools provide a complete workflow for managing meetings within OpenProject:

#### 1. **Planning Phase**
- Use `create_meeting` to schedule individual meetings with agenda and attendees
- Use `schedule_recurring_meeting` for regular meetings (standups, sprint planning, etc.)
- Use `list_users` to identify meeting attendees

#### 2. **Meeting Execution**
- Meetings are created as work packages with structured descriptions
- Each meeting includes date, time, duration, type, location, and agenda
- Attendees are tracked and can be assigned as work package assignees

#### 3. **Post-Meeting Follow-up**
- Use `add_meeting_minutes` to record discussion points, decisions, and action items
- Use `create_follow_up_tasks` to convert action items into trackable work packages
- Meeting work packages can be updated with status changes

#### 4. **Meeting Tracking**
- Use `list_meetings` to view scheduled, completed, or cancelled meetings
- Filter by project, meeting type, date range, or status
- Track meeting series and recurring patterns

#### Meeting Types Supported
- **Standup**: Daily team synchronization meetings
- **Sprint Planning**: Sprint planning and estimation sessions
- **Retrospective**: Sprint retrospectives and team improvement discussions
- **Review**: Sprint reviews and demos
- **General**: General purpose meetings

#### Best Practices
1. **Consistent Naming**: Use descriptive meeting titles that include the meeting type
2. **Agenda Preparation**: Always include an agenda to keep meetings focused
3. **Action Item Tracking**: Convert discussion points into actionable tasks
4. **Regular Reviews**: Use `list_meetings` to review meeting patterns and effectiveness
5. **Follow-up**: Ensure action items are tracked and completed

## Development

### Setting up Development Environment

```bash
# Install development dependencies
uv sync --extra dev

# Or install manually
uv pip install -e ".[dev]"
```

### Testing

This project includes comprehensive testing with both unit tests and end-to-end tests using Docker Compose.

#### Unit Tests

Run unit tests locally:

```bash
uv run pytest tests/test_unit.py -v
```

#### End-to-End Tests

Run the complete E2E test suite:

```bash
# Make the test runner executable
chmod +x run-e2e-tests.sh

# Run E2E tests (requires Docker)
./run-e2e-tests.sh
```

The E2E tests spin up a complete OpenProject instance and test all MCP server functionality against it.

For detailed testing information, see [TESTING.md](TESTING.md).

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
- **Status filter errors**: The `list_meetings` tool uses post-processing for status filtering to avoid OpenProject API validation issues
- **Assignee permission errors**: Meeting creation automatically falls back to unassigned if the specified user cannot be assigned

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
