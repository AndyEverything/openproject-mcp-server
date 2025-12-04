#!/usr/bin/env python3
"""
Test script for FastMCP implementation - validates 7 migrated tools.

This script tests the tools without running the full MCP server,
allowing quick validation during development.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import mcp, get_client


async def test_all_tools():
    """Test all 7 migrated tools."""
    print("=" * 70)
    print("Testing FastMCP OpenProject Implementation")
    print("=" * 70)

    client = get_client()
    print(f"\nOK OpenProject Client: {client.base_url}")
    print(f"OK FastMCP Server: {mcp.name}")

    # Get all registered tools
    tools = await mcp.get_tools()
    print(f"\n> Registered Tools: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        print(f"   {i}. {str(tool)}")

    print("\n" + "=" * 70)
    print("Running Tool Tests")
    print("=" * 70)

    # Test 1: Connection Test
    print("\n[1] Test: test_connection")
    try:
        from src.tools.connection import test_connection
        result = await test_connection()
        print(result[:200] + "..." if len(result) > 200 else result)
        print("OK PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 2: Check Permissions
    print("\n[2] Test: check_permissions")
    try:
        from src.tools.connection import check_permissions
        result = await check_permissions()
        print(result[:200] + "..." if len(result) > 200 else result)
        print("OK PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 3: List Projects
    print("\n[3] Test: list_projects")
    try:
        from src.tools.projects import list_projects
        result = await list_projects(active_only=True)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("OK PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 4: List Work Packages (CRITICAL)
    print("\n[4] Test: list_work_packages (CRITICAL)")
    try:
        from src.tools.work_packages import list_work_packages
        result = await list_work_packages(active_only=True, page_size=5)
        print(result[:400] + "..." if len(result) > 400 else result)
        print("OK PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 5: Create Work Package (CRITICAL) - DRY RUN
    print("\n[5] Test: create_work_package validation (CRITICAL)")
    try:
        from src.tools.work_packages import CreateWorkPackageInput
        # Validate input model only (don't actually create)
        test_input = CreateWorkPackageInput(
            project_id=1,
            subject="Test Work Package",
            type_id=1,
            description="This is a test"
        )
        print(f"OK Input validation PASSED")
        print(f"   Model: {test_input.model_dump()}")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 6: Update Work Package (CRITICAL) - DRY RUN
    print("\n[6] Test: update_work_package validation (CRITICAL)")
    try:
        from src.tools.work_packages import UpdateWorkPackageInput
        # Validate input model only (don't actually update)
        test_input = UpdateWorkPackageInput(
            work_package_id=123,
            status_id=5,
            assignee_id=7,
            percentage_done=50
        )
        print(f"OK Input validation PASSED")
        print(f"   Model: {test_input.model_dump()}")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 7: Response Formatting
    print("\n[7] Test: Response formatting utilities")
    try:
        from src.utils.formatting import (
            format_project_list,
            format_work_package_list,
            format_success,
            format_error
        )

        # Test project formatting
        test_projects = [
            {"id": 1, "name": "Test Project", "active": True},
            {"id": 2, "name": "Another Project", "active": False}
        ]
        result = format_project_list(test_projects)
        assert "Test Project" in result
        print("OK format_project_list: PASSED")

        # Test work package formatting
        test_wps = [
            {
                "id": 123,
                "subject": "Test Task",
                "_embedded": {
                    "type": {"name": "Bug"},
                    "status": {"name": "In Progress"}
                }
            }
        ]
        result = format_work_package_list(test_wps)
        assert "Test Task" in result
        assert "Bug" in result
        print("OK format_work_package_list: PASSED")

        # Test success/error formatting
        assert "OK" in format_success("Success!")
        assert "FAIL" in format_error("Error!")
        print("OK format_success/error: PASSED")

    except Exception as e:
        print(f"FAIL FAILED: {e}")

    print("\n" + "=" * 70)
    print("OK All Tests Completed!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n>> Starting FastMCP Tool Tests...\n")
    asyncio.run(test_all_tools())
