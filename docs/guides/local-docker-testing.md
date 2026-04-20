# Testing Locally with Docker

## Prerequisites

- Docker installed and running
- A self-hosted OpenProject instance reachable from your machine
- This repository cloned locally

---

## Step 1 — Get your OpenProject API Key

1. Go to `https://YOUR-OPENPROJECT/my/access_token`
2. Click **Generate** under *API access token*
3. Copy the token — you will use it in the next step

---

## Step 2 — Create the `.env` file

```bash
cp env_example.txt .env
```

Open `.env` and fill in your values:

```env
OPENPROJECT_URL=https://YOUR-OPENPROJECT
OPENPROJECT_API_KEY=your-token-here
READ_ONLY_MODE=false
LOG_LEVEL=INFO
```

> **Tip:** Set `READ_ONLY_MODE=true` if you want to explore safely without risk of modifying data.

---

## Step 3 — Build the Docker image

```bash
docker build -t openproject-mcp .
```

---

## Step 4 — Verify the connection

Run a quick connectivity check before starting the full server:

```bash
docker run --rm --env-file .env openproject-mcp python -c "
import os, asyncio, sys
sys.path.insert(0, '.')
from src.client import OpenProjectClient
async def test():
    c = OpenProjectClient(os.environ['OPENPROJECT_URL'], os.environ['OPENPROJECT_API_KEY'])
    r = await c.test_connection()
    print('Instance:', r.get('instanceName'))
    print('Version:', r.get('coreVersion'))
    print('User:', r.get('_links', {}).get('user', {}).get('title'))
asyncio.run(test())
"
```

Expected output:

```
Instance: YourInstanceName
Version: 12.x.x
User: Your Name
```

If you see your instance name and username, the credentials are correct and the server can reach OpenProject.

---

## Step 5 — Start the HTTP server

```bash
docker run --rm -p 8000:8000 --env-file .env \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=8000 \
  openproject-mcp python openproject-mcp-http.py
```

You should see:

```
🚀 Starting OpenProject MCP Server (HTTP)
   Host: 0.0.0.0
   Port: 8000
```

---

## Step 6 — Test a tool via curl

Open a second terminal and run:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"test_connection","arguments":{}}}' \
  | python3 -m json.tool
```

Expected: a JSON response containing the OpenProject version and connection status.

Try listing projects:

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}' \
  | python3 -m json.tool
```

---

## Step 7 — List all available tools

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}' \
  | python3 -m json.tool | grep '"name"'
```

This prints all 49 tool names the server exposes.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Connected as:` shows nothing | Wrong API key | Regenerate token in OpenProject |
| `Connection refused` on curl | Server not running | Check Step 5 output |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Self-signed cert | Add `OPENPROJECT_PROXY` or use `http://` URL |
| `403 Forbidden` | API key lacks permissions | Use an admin account's token |
| Container exits immediately | Missing env vars | Verify `.env` has both `OPENPROJECT_URL` and `OPENPROJECT_API_KEY` |

---

## Connect to Claude Desktop (stdio transport)

Add this to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "openproject": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/absolute/path/to/your/.env",
        "openproject-mcp",
        "python", "openproject-mcp-fastmcp.py"
      ]
    }
  }
}
```

Restart Claude Desktop. The OpenProject tools will appear automatically.
