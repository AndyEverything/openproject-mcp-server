#!/usr/bin/env python3
"""
OpenProject MCP Server - HTTP Transport Entry Point

Runs the Streamable HTTP transport with per-user OpenProject API key support.
Each client passes their personal API key via the X-OpenProject-Api-Key header.
"""

import logging
import os

import uvicorn
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.server import _http_mode, _request_api_key, mcp

logger = logging.getLogger(__name__)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Extract X-OpenProject-Api-Key header and store in ContextVar per request."""

    async def dispatch(self, request, call_next):
        api_key = request.headers.get("X-OpenProject-Api-Key")
        if not api_key:
            return Response("X-OpenProject-Api-Key header required", status_code=401)
        t1 = _http_mode.set(True)
        t2 = _request_api_key.set(api_key)
        try:
            return await call_next(request)
        finally:
            _http_mode.reset(t1)
            _request_api_key.reset(t2)


if __name__ == "__main__":
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8000"))

    logger.info("Starting OpenProject MCP Server (HTTP)")
    logger.info("Host: %s  Port: %d", host, port)
    logger.info("Per-user API key: enabled (X-OpenProject-Api-Key header required)")

    app = mcp.http_app(
        middleware=[Middleware(ApiKeyMiddleware)]
    )

    log_level = os.getenv("LOG_LEVEL", "INFO").lower()
    uvicorn.run(app, host=host, port=port, log_level=log_level)
