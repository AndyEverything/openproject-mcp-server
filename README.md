<br>![status](https://img.shields.io/badge/status-WIP-yellow) ![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)<br><br>⚠️ This is an early-stage project. Do not use it productively – contributions welcome!<br>

# OpenProject MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with [OpenProject](https://www.openproject.org/) API v3. This server enables LLM applications to interact with OpenProject for project management, work package tracking, and task creation.

## Features

- 🔌 **Full OpenProject API v3 Integration**
- 📋 **Project Management**: List and filter projects
- 📝 **Work Package Management**: Create, list, and filter work packages
- 🔗 **Work Package Relationships**: Create, list, and delete relationships (blocks, follows, relates to, etc.)
- 🏷️ **Type Management**: List available work package types
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

### Work Package Relationship Types

OpenProject supports several types of relationships between work packages:

- **`blocks`**: The source work package blocks the target work package from being completed
- **`follows`**: The source work package follows (comes after) the target work package
- **`relates`**: A general relationship between work packages
- **`duplicates`**: The source work package duplicates the target work package
- **`includes`**: The source work package includes the target work package
- **`requires`**: The source work package requires the target work package

**Note**: When you create a relationship, OpenProject automatically creates the reverse relationship on the target work package. For example, if you create a "blocks" relationship from A to B, work package B will automatically have a "blocked by" relationship to A.

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
uv run pytest tests/
```

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
