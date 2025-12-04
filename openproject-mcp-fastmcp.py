#!/usr/bin/env python3
"""
OpenProject MCP Server - Stdio Transport Entry Point

This is the entry point for stdio transport (Claude Code desktop).
FastMCP-based implementation with automatic tool registration.
"""

from src.server import mcp

if __name__ == "__main__":
    # Run with stdio transport (default for Claude Code)
    mcp.run(transport="stdio")
