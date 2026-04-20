# EC2 Deployment Guide

Deploy openproject-mcp on an existing EC2 instance using Caddy as reverse proxy, mirroring the bookstack MCP setup.

**Prerequisites:** Docker, Caddy, and a DNS record for `openproject-mcp.spacest.com` pointing to your EC2.

---

## Step 1 — Clone and configure on EC2

```bash
git clone https://github.com/YOUR-ORG/openproject-mcp-server.git
cd openproject-mcp-server
cp env_example.txt .env
```

Edit `.env`:

```env
OPENPROJECT_URL=https://YOUR-OPENPROJECT
OPENPROJECT_API_KEY=your-admin-api-key
READ_ONLY_MODE=true
LOG_LEVEL=INFO
```

---

## Step 2 — Build the Docker image

```bash
docker build -t openproject-mcp .
```

---

## Step 3 — Start the container

```bash
docker run -d \
  --name openprojectmcp \
  --restart unless-stopped \
  --env-file .env \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=8000 \
  openproject-mcp python openproject-mcp-http.py
```

Verify it is running:

```bash
docker ps | grep openprojectmcp
docker logs openprojectmcp
```

---

## Step 4 — Add Caddy block

Add this block to your Caddyfile (same file as bookstack):

```caddy
openproject-mcp.spacest.com {
    basicauth {
        {env.MCP_AUTH_USER} {env.MCP_AUTH_HASH}
    }
    reverse_proxy openprojectmcp:8000
}
```

This reuses the same `MCP_AUTH_USER` and `MCP_AUTH_HASH` env vars already set for bookstack, so no new credentials are needed.

Reload Caddy:

```bash
# If Caddy runs as a Docker container
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# If Caddy runs as a systemd service
systemctl reload caddy
```

---

## Step 5 — Verify the deployment

Test from the EC2 directly (no auth, direct to container):

```bash
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

Test via HTTPS through Caddy (from your machine):

```bash
curl -s -u YOUR_USER:YOUR_PASSWORD \
  -X POST https://openproject-mcp.spacest.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | python3 -m json.tool | grep '"name"'
```

Expected: list of 49 tool names.

---

## Step 6 — Configure Claude Desktop for each team member

Each person adds this to their `claude_desktop_config.json`
(`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "openproject": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://openproject-mcp.spacest.com/mcp",
        "--header",
        "Authorization: Basic REPLACE_WITH_BASE64"
      ]
    }
  }
}
```

To generate the `REPLACE_WITH_BASE64` value:

```bash
echo -n "your_user:your_password" | base64
```

Paste the output in place of `REPLACE_WITH_BASE64`.

Restart Claude Desktop after editing the config.

---

## Updating the server

When a new version is available:

```bash
cd openproject-mcp-server
git pull
docker build -t openproject-mcp .
docker stop openprojectmcp && docker rm openprojectmcp
docker run -d \
  --name openprojectmcp \
  --restart unless-stopped \
  --env-file .env \
  -e MCP_HTTP_HOST=0.0.0.0 \
  -e MCP_HTTP_PORT=8000 \
  openproject-mcp python openproject-mcp-http.py
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `502 Bad Gateway` from Caddy | Container not running or wrong name | `docker ps | grep openprojectmcp` |
| `401 Unauthorized` | Wrong basic auth credentials | Verify `MCP_AUTH_USER` / `MCP_AUTH_HASH` env vars |
| Tools return errors | Wrong OpenProject API key | Check `.env` on EC2 |
| `mcp-remote` can't connect | DNS not propagated | `nslookup openproject-mcp.spacest.com` |
