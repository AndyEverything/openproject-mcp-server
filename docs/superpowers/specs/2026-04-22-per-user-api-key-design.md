# Per-User OpenProject API Key — Design Spec

## Context

The server is deployed on EC2 and shared by 5-6 team members via the HTTP transport. Currently a single admin OpenProject API key is baked into the server's `.env`. The goal is to let each user pass their own personal OpenProject API key per request, so actions are attributed to the correct user in OpenProject.

## Scope

- HTTP transport only (`openproject-mcp-http.py`)
- STDIO transport (`openproject-mcp-fastmcp.py`) continues to use the shared key from `.env` — no change
- Zero changes to any of the 49 tool modules
- Personal key is **required** on the HTTP transport — missing header returns an explicit error

---

## Architecture

```
mcp-remote (Claude Desktop)
  ├── Authorization: Basic <caddy-auth>
  └── X-OpenProject-Api-Key: <personal-token>
          │
    Caddy (basicauth)
          │
    Starlette Middleware (ApiKeyMiddleware)
    ├── sets _http_mode ContextVar = True
    └── sets _request_api_key ContextVar = token (or None if header absent)
          │
    FastMCP tool dispatch
          │
    get_client() [src/server.py]
    ├── _http_mode=True, no key → raise ValueError (error returned to user)
    ├── _http_mode=True, key present → ephemeral OpenProjectClient(personal key)
    └── _http_mode=False (STDIO) → return global _client (shared key)
          │
    OpenProjectClient → OpenProject API
```

---

## Components

### `src/server.py` — changes

Add two module-level ContextVars:

```python
from contextvars import ContextVar
from typing import Optional

_http_mode: ContextVar[bool] = ContextVar("http_mode", default=False)
_request_api_key: ContextVar[Optional[str]] = ContextVar("request_api_key", default=None)
```

Replace `get_client()`:

```python
def get_client() -> OpenProjectClient:
    if _http_mode.get():
        api_key = _request_api_key.get()
        if not api_key:
            raise ValueError(
                "X-OpenProject-Api-Key header is required for HTTP transport. "
                "Add it to your Claude Desktop mcp-remote configuration."
            )
        return OpenProjectClient(
            base_url=_client.base_url,
            api_key=api_key,
            proxy=_client.proxy,
            readonly=_client.readonly,
        )
    return _client
```

### `openproject-mcp-http.py` — changes

Add `ApiKeyMiddleware` before `mcp.run()`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from src.server import _http_mode, _request_api_key

class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        api_key = request.headers.get("X-OpenProject-Api-Key")
        t1 = _http_mode.set(True)
        t2 = _request_api_key.set(api_key)
        try:
            return await call_next(request)
        finally:
            _http_mode.reset(t1)
            _request_api_key.reset(t2)

mcp_app = mcp.http_app()
mcp_app.add_middleware(ApiKeyMiddleware)
# use uvicorn to serve mcp_app instead of mcp.run()
```

### `tests/test_per_user_api_key.py` — new file

Tests:
1. HTTP mode + valid key → ephemeral client created with that key
2. HTTP mode + no key → `get_client()` raises `ValueError`
3. STDIO mode (no ContextVar set) → global client returned

---

## Client Desktop Config (per team member)

```json
{
  "mcpServers": {
    "openproject": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "https://openproject-mcp.spacest.com/mcp",
        "--header", "Authorization: Basic <base64>",
        "--header", "X-OpenProject-Api-Key: <personal-openproject-token>"
      ]
    }
  }
}
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| HTTP request, header present | Ephemeral client created with personal key |
| HTTP request, header absent | `get_client()` raises `ValueError` with clear message |
| STDIO request | Global `_client` returned (shared key from env) |
| Invalid personal key | OpenProject API returns 401 — propagated as tool error |

---

## What Does NOT Change

- All 49 tool modules — untouched
- `src/client.py` — untouched
- `src/auth.py` — untouched
- STDIO transport entry point — untouched
- Caddy configuration — untouched
- `READ_ONLY_MODE` enforcement — still enforced by `_client.readonly` on ephemeral clients

---

## Testing Strategy

- Unit tests with mocked ContextVars for the three scenarios above
- Manual end-to-end: connect via `mcp-remote` with personal token, call `test_connection`, verify response attributes match the personal account
