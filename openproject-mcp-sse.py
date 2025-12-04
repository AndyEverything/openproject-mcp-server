#!/usr/bin/env python3
"""
OpenProject MCP Server - SSE Transport Entry Point

This is the entry point for SSE transport (FastMCP Cloud).
FastMCP-based implementation with automatic tool registration.
"""

from src.server import mcp

if __name__ == "__main__":
    # Run with SSE transport (for FastMCP Cloud deployment)
    mcp.run(transport="sse")
