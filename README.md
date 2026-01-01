# OpenProject MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server providing seamless integration with [OpenProject](https://www.openproject.org/) API v3. Enable AI assistants to interact with your OpenProject instance for project management, work package tracking, and task automation.

## Features

- 🔌 **Full OpenProject API v3 Integration**
- 📋 **Project Management**: List and filter projects
- 📝 **Work Package Management**: Create, list, update, and filter work packages
- 👥 **User & Team Management**: List users, memberships, and roles
- ⏱️ **Time Tracking**: Create and manage time entries
- 🏷️ **Type Management**: List available work package types, statuses, and priorities
- 🔐 **Secure Authentication**: API key-based authentication with HTTP Basic Auth
- 🌐 **Proxy Support**: Optional HTTP proxy configuration
- 🚀 **Async Operations**: Built with modern async/await patterns

## Quick Start

### Installation

```bash
# Install with uvx (recommended - no installation required)
uvx openproject-mcp

# Or install globally with pip
pip install openproject-mcp
```

### Configuration

Get your OpenProject API key:
1. Log into your OpenProject instance
2. Go to **My Account** → **Access Tokens**
3. Click **+ API** to create a new token
4. Copy the generated token

## Installation Guides by Editor/IDE

### Claude Code

**Config file:** `~/.claude.json`

Add the MCP server to the `mcpServers` section:

```json
{
  "mcpServers": {
    "openproject": {
      "type": "stdio",
      "command": "uvx",
      "args": ["openproject-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Code after saving.

---

### Claude Desktop

**Config file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openproject": {
      "command": "openproject-mcp",
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

---

### Cursor

**Config file:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-specific)

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uvx",
      "args": ["openproject-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

You can also configure MCP servers through Cursor's GUI:
1. Open **Settings** → **Features** → **Model Context Protocol**
2. Click **Add MCP Server**
3. Configure the server with the command and environment variables above

---

### Zed

**Config file locations:**
- **macOS**: `~/.zed/settings.json`
- **Linux**: `~/.config/zed/settings.json`

Add to your settings file (open with `cmd-,` on macOS or `ctrl-,` on Linux):

```json
{
  "context_servers": {
    "openproject": {
      "settings": {},
      "command": {
        "path": "uvx",
        "args": ["openproject-mcp"],
        "env": {
          "OPENPROJECT_URL": "https://your-instance.openproject.com",
          "OPENPROJECT_API_KEY": "your-api-key-here"
        }
      }
    }
  }
}
```

MCP tools will be available through Zed's AI assistant.

---

### VS Code (with GitHub Copilot)

**Requires**: VS Code 1.99+ with GitHub Copilot extension

**Config file:** `.vscode/mcp.json` (workspace) or User Profile's `mcp.json`

```json
{
  "servers": {
    "openproject": {
      "type": "stdio",
      "command": "uvx",
      "args": ["openproject-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

You can also use the Command Palette: `MCP: Add Server` to configure servers through the GUI.

---

### IntelliJ IDEA (2025.1+) & JetBrains IDEs (2025.2+)

**Requires**: IntelliJ IDEA 2025.1+ or JetBrains IDE 2025.2+

1. Go to **Settings/Preferences** → **Tools** → **Model Context Protocol**
2. Click **Add MCP Server**
3. Configure:
   - **Command**: `openproject-mcp`
   - **Environment Variables**:
     - `OPENPROJECT_URL`: `https://your-instance.openproject.com`
     - `OPENPROJECT_API_KEY`: `your-api-key-here`

Or edit the MCP configuration file directly (location varies by IDE).

---

### Continue (VS Code & JetBrains)

**Continue** is an open-source AI coding assistant.

**Config location:** `.continue/mcpServers/` folder in your workspace

Create a file `.continue/mcpServers/openproject.json`:

```json
{
  "name": "openproject",
  "version": "1.0.0",
  "schema": "1.0.0",
  "type": "stdio",
  "command": "uvx",
  "args": ["openproject-mcp"],
  "env": {
    "OPENPROJECT_URL": "https://your-instance.openproject.com",
    "OPENPROJECT_API_KEY": "your-api-key-here"
  }
}
```

Alternatively, you can use YAML format (`.continue/mcpServers/openproject.yaml`) which is the preferred format in newer versions.

---

### Windsurf

**Config file locations:**
- **macOS/Linux**: `~/.codeium/windsurf/mcp_config.json`
- **Windows**: `%USERPROFILE%\.codeium\windsurf\mcp_config.json`

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uvx",
      "args": ["openproject-mcp"],
      "env": {
        "OPENPROJECT_URL": "https://your-instance.openproject.com",
        "OPENPROJECT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

You can also access this through Windsurf's GUI:
1. Go to **Settings** → **Manage MCPs**
2. Click **View raw config** to edit the `mcp_config.json` file

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENPROJECT_URL` | Yes | Your OpenProject instance URL | `https://mycompany.openproject.com` |
| `OPENPROJECT_API_KEY` | Yes | API key from your user profile | `8169846b42461e6e...` |
| `OPENPROJECT_PROXY` | No | HTTP proxy URL if needed | `http://proxy.company.com:8080` |
| `LOG_LEVEL` | No | Logging level | `INFO`, `DEBUG`, `WARNING`, `ERROR` |
| `TEST_CONNECTION_ON_STARTUP` | No | Test API connection on startup | `true` or `false` |

## Important: Reverse Proxy / Authentication Gateway Setup

If your OpenProject instance is behind an authentication gateway (Authelia, Authentik, Keycloak, etc.), you **must** configure it to bypass authentication for API endpoints.

### Problem

Authentication gateways intercept ALL requests, including API calls, redirecting them to login pages. This breaks API token authentication.

### Solution

Configure your reverse proxy to bypass authentication for `/api/` paths, allowing OpenProject's native API authentication to work.

#### Example: Traefik + Authelia

Create a higher-priority route for API endpoints:

**File:** `/path/to/traefik/config/openproject-api.yml`

```yaml
http:
  routers:
    openproject-api:
      rule: "Host(`projects.example.com`) && PathPrefix(`/api/`)"
      service: openproject
      priority: 100  # Higher than main route
      tls: true
      # No Authelia middleware - OpenProject handles API auth

  services:
    openproject:
      loadBalancer:
        servers:
          - url: "http://openproject:80"
```

This configuration:
- ✅ Web UI requests → Authenticated via Authelia (2FA, SSO, etc.)
- ✅ API requests → Authenticated via OpenProject API keys

#### Other Reverse Proxies

**Nginx:**
```nginx
location /api/ {
    # Bypass auth for API
    proxy_pass http://openproject:80;
}

location / {
    # Require auth for web UI
    auth_request /auth;
    proxy_pass http://openproject:80;
}
```

**Caddy:**
```
projects.example.com {
    @api path /api/*
    handle @api {
        reverse_proxy openproject:80
    }

    handle {
        forward_auth authelia:9091
        reverse_proxy openproject:80
    }
}
```

### Authentication Format

OpenProject uses **HTTP Basic Authentication** for API access:
- **Username:** `apikey`
- **Password:** Your API key
- **Header Format:** `Authorization: Basic base64(apikey:YOUR_API_KEY)`

The MCP server handles this automatically.

## Available Tools

### `test_connection`
Test connection to your OpenProject instance.

**Example:** "Test the OpenProject connection"

---

### `list_projects`
List all projects you have access to.

**Parameters:**
- `active_only` (boolean, optional): Show only active projects (default: true)

**Example:** "List all active OpenProject projects"

---

### `list_work_packages`
List work packages with optional filtering.

**Parameters:**
- `project_id` (integer, optional): Filter by project ID
- `status` (string, optional): Filter by status name
- `assignee_id` (integer, optional): Filter by assignee user ID
- `page_size` (integer, optional): Number of results (default: 20)

**Example:** "Show all work packages in project 3"

---

### `create_work_package`
Create a new work package.

**Parameters:**
- `project_id` (integer, required): Project ID
- `subject` (string, required): Work package title
- `type_id` (integer, required): Work package type ID
- `description` (string, optional): Description in markdown
- `assignee_id` (integer, optional): User ID to assign
- `status_id` (integer, optional): Status ID

**Example:** "Create a task in project 3 called 'Fix login bug'"

---

### `update_work_package`
Update an existing work package.

**Parameters:**
- `work_package_id` (integer, required): Work package ID
- `subject` (string, optional): New title
- `description` (string, optional): New description
- `status_id` (integer, optional): New status
- `assignee_id` (integer, optional): New assignee

**Example:** "Update work package #42 status to 'In Progress'"

---

### `list_users`
List all users in the OpenProject instance.

**Example:** "Show all OpenProject users"

---

### `list_work_package_types`
List available work package types.

**Example:** "What work package types are available?"

---

### `list_work_package_statuses`
List available work package statuses.

**Example:** "Show all available statuses"

---

### `create_time_entry`
Create a time entry for a work package.

**Parameters:**
- `work_package_id` (integer, required): Work package ID
- `hours` (float, required): Hours spent
- `comment` (string, optional): Comment/description
- `spent_on` (string, optional): Date (YYYY-MM-DD)

**Example:** "Log 2.5 hours on work package #39 for today"

---

### `list_memberships`
List project memberships.

**Parameters:**
- `project_id` (integer, optional): Filter by project

**Example:** "Show who has access to project 3"

---

## Development

### Install from Source

```bash
# Clone repository
git clone https://github.com/Compass-Rose-Systems/openproject-mcp.git
cd openproject-mcp

# Build package
uv build

# Install locally
pip install dist/openproject_mcp-1.0.0-py3-none-any.whl
```

### Run Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
pytest
```

## Roadmap

Based on community contributions and open pull requests, here are planned improvements:

### 🐳 Docker Containerization ([#14](https://github.com/AndyEverything/openproject-mcp-server/pull/14))
- Simplified deployment with Docker
- Environment consistency
- Easy scaling and orchestration

### 📊 Project Grid & Research Features ([#11](https://github.com/AndyEverything/openproject-mcp-server/pull/11))
- Enhanced data visualization
- Grid-based project management
- Advanced filtering and sorting

### 🤖 Tool Automation ([#10](https://github.com/AndyEverything/openproject-mcp-server/pull/10))
- Automated update and upgrade workflows
- Streamlined maintenance

### 🔧 Additional Tools ([#4](https://github.com/AndyEverything/openproject-mcp-server/pull/4))
- Expanded tool capabilities
- More OpenProject API coverage

### Future Enhancements
- Webhook support for real-time notifications
- Bulk operations for work packages
- Custom field support
- Advanced query builder
- Export functionality (CSV, PDF)
- Integration with external tools (Slack, email, etc.)

## Troubleshooting

### "Unauthenticated" errors

**Cause:** API key format incorrect or authentication gateway blocking requests.

**Solutions:**
1. Verify API key is correct (check OpenProject → My Account → Access Tokens)
2. Ensure authentication gateway bypasses `/api/` paths (see setup guide above)
3. Check `OPENPROJECT_URL` is correct and accessible

### Connection timeouts

**Cause:** Network issues, firewall, or proxy misconfiguration.

**Solutions:**
1. Test direct access: `curl -u "apikey:YOUR_KEY" https://your-instance/api/v3/projects`
2. If behind corporate proxy, set `OPENPROJECT_PROXY` environment variable
3. Check firewall rules allow outbound HTTPS

### MCP server not appearing in editor

**Cause:** Configuration file syntax error or incorrect path.

**Solutions:**
1. Validate JSON syntax (use online JSON validator)
2. Check config file location for your editor
3. Restart editor after configuration changes
4. Check editor logs for MCP loading errors

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

**Original Author:** [AndyEverything](https://github.com/AndyEverything/openproject-mcp-server)
**Current Maintainer:** [cleanspin](https://github.com/cleanspin)
**Organization:** [Compass Rose Systems](https://github.com/Compass-Rose-Systems)

This project is a maintained fork with active development, easy installation via PyPI, comprehensive documentation, and ongoing feature improvements.
