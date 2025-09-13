#!/usr/bin/env python3
"""
End-to-End Test Suite for OpenProject MCP Server

This test suite validates the complete functionality of the MCP server
by testing against a real OpenProject instance running in Docker.
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
import aiohttp
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenProjectTestClient:
    """Test client for OpenProject API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Basic {self._encode_api_key()}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def _encode_api_key(self) -> str:
        """Encode API key for Basic Auth"""
        import base64
        credentials = f"apikey:{self.api_key}"
        return base64.b64encode(credentials.encode()).decode()
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        response = requests.get(f"{self.base_url}/api/v3", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_project(self, name: str, description: str = "") -> Dict:
        """Create a test project"""
        data = {
            "name": name,
            "description": {"raw": description},
            "public": True
        }
        response = requests.post(f"{self.base_url}/api/v3/projects", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_user(self, email: str, name: str, password: str) -> Dict:
        """Create a test user"""
        data = {
            "login": email,
            "email": email,
            "firstName": name.split()[0],
            "lastName": name.split()[-1] if len(name.split()) > 1 else "",
            "password": password,
            "status": "active"
        }
        response = requests.post(f"{self.base_url}/api/v3/users", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_projects(self) -> List[Dict]:
        """Get all projects"""
        response = requests.get(f"{self.base_url}/api/v3/projects", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("_embedded", {}).get("elements", [])
    
    def get_users(self) -> List[Dict]:
        """Get all users"""
        response = requests.get(f"{self.base_url}/api/v3/users", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("_embedded", {}).get("elements", [])
    
    def get_types(self) -> List[Dict]:
        """Get work package types"""
        response = requests.get(f"{self.base_url}/api/v3/types", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("_embedded", {}).get("elements", [])
    
    def get_priorities(self) -> List[Dict]:
        """Get work package priorities"""
        response = requests.get(f"{self.base_url}/api/v3/priorities", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("_embedded", {}).get("elements", [])
    
    def get_statuses(self) -> List[Dict]:
        """Get work package statuses"""
        response = requests.get(f"{self.base_url}/api/v3/statuses", headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get("_embedded", {}).get("elements", [])
    
    def cleanup_project(self, project_id: int):
        """Delete a project"""
        try:
            requests.delete(f"{self.base_url}/api/v3/projects/{project_id}", 
                          headers=self.headers)
        except Exception as e:
            logger.warning(f"Failed to cleanup project {project_id}: {e}")
    
    def cleanup_user(self, user_id: int):
        """Delete a user"""
        try:
            requests.delete(f"{self.base_url}/api/v3/users/{user_id}", 
                          headers=self.headers)
        except Exception as e:
            logger.warning(f"Failed to cleanup user {user_id}: {e}")


class MCPTestClient:
    """Test client for MCP server"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        # Import the MCP server module
        sys.path.append('/app')
        from openproject_mcp import OpenProjectMCPServer, OpenProjectClient
        
        # Create server instance
        server = OpenProjectMCPServer()
        
        # Initialize client
        base_url = os.getenv("OPENPROJECT_URL")
        api_key = os.getenv("OPENPROJECT_API_KEY")
        if base_url and api_key:
            server.client = OpenProjectClient(base_url, api_key)
        
        # Call the tool
        result = await server.call_tool(tool_name, arguments)
        return {"content": result}


class E2ETestSuite:
    """End-to-end test suite"""
    
    def __init__(self):
        self.openproject_url = os.getenv("OPENPROJECT_URL", "http://localhost:8080")
        self.api_key = os.getenv("OPENPROJECT_API_KEY", "test-api-key")
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
        
        # For testing, we'll use the admin user credentials
        self.admin_username = "admin"
        self.admin_password = "admin123"
        
        self.op_client = OpenProjectTestClient(self.openproject_url, self.api_key)
        self.mcp_client = MCPTestClient(self.mcp_server_url)
        
        # Test data
        self.test_project = None
        self.test_user = None
        self.created_work_packages = []
        
    async def setup_test_data(self):
        """Set up test data"""
        logger.info("Setting up test data...")
        
        # Wait for OpenProject to be ready
        await self.wait_for_openproject()
        
        # Wait a bit more for full initialization
        await asyncio.sleep(30)
        
        # Try to create test project
        try:
            self.test_project = self.op_client.create_project(
                "E2E Test Project",
                "Test project for end-to-end testing"
            )
            logger.info(f"Created test project: {self.test_project['id']}")
        except Exception as e:
            logger.warning(f"Failed to create test project: {e}")
            # Try to get existing projects
            projects = self.op_client.get_projects()
            if projects:
                self.test_project = projects[0]
                logger.info(f"Using existing project: {self.test_project['id']}")
            else:
                raise Exception("No projects available for testing")
        
        # Try to create test user
        try:
            self.test_user = self.op_client.create_user(
                "test@example.com",
                "Test User",
                "test123"
            )
            logger.info(f"Created test user: {self.test_user['id']}")
        except Exception as e:
            logger.warning(f"Failed to create test user: {e}")
            # Try to get existing users
            users = self.op_client.get_users()
            if users:
                self.test_user = users[0]
                logger.info(f"Using existing user: {self.test_user['id']}")
            else:
                raise Exception("No users available for testing")
        
    async def wait_for_openproject(self, timeout: int = 300):
        """Wait for OpenProject to be ready"""
        logger.info("Waiting for OpenProject to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if OpenProject is responding (use public endpoint)
                response = requests.get(f"{self.openproject_url}/", timeout=10)
                if response.status_code == 200:
                    logger.info("OpenProject is ready!")
                    return
            except Exception as e:
                logger.debug(f"OpenProject not ready yet: {e}")
                await asyncio.sleep(10)
        
        raise Exception(f"OpenProject not ready after {timeout} seconds")
    
    async def test_connection(self):
        """Test MCP server connection to OpenProject"""
        logger.info("Testing MCP server connection...")
        
        result = await self.mcp_client.call_tool("test_connection", {})
        
        assert "content" in result
        assert len(result["content"]) > 0
        assert "API connection successful" in result["content"][0].text
        
        logger.info("✅ Connection test passed")
    
    async def test_list_projects(self):
        """Test listing projects"""
        logger.info("Testing list_projects tool...")
        
        result = await self.mcp_client.call_tool("list_projects", {"active_only": True})
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "project(s)" in content
        assert self.test_project["name"] in content
        
        logger.info("✅ List projects test passed")
    
    async def test_list_users(self):
        """Test listing users"""
        logger.info("Testing list_users tool...")
        
        result = await self.mcp_client.call_tool("list_users", {"active_only": True})
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "user(s)" in content
        assert self.test_user["name"] in content
        
        logger.info("✅ List users test passed")
    
    async def test_list_types(self):
        """Test listing work package types"""
        logger.info("Testing list_types tool...")
        
        result = await self.mcp_client.call_tool("list_types", {})
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "work package types" in content
        
        logger.info("✅ List types test passed")
    
    async def test_list_priorities(self):
        """Test listing priorities"""
        logger.info("Testing list_priorities tool...")
        
        result = await self.mcp_client.call_tool("list_priorities", {})
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "priorities" in content
        
        logger.info("✅ List priorities test passed")
    
    async def test_list_statuses(self):
        """Test listing statuses"""
        logger.info("Testing list_statuses tool...")
        
        result = await self.mcp_client.call_tool("list_statuses", {})
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "statuses" in content
        
        logger.info("✅ List statuses test passed")
    
    async def test_create_work_package(self):
        """Test creating a work package"""
        logger.info("Testing create_work_package tool...")
        
        # Get types and priorities
        types = self.op_client.get_types()
        priorities = self.op_client.get_priorities()
        
        assert len(types) > 0, "No work package types available"
        assert len(priorities) > 0, "No priorities available"
        
        # Create work package
        result = await self.mcp_client.call_tool("create_work_package", {
            "project_id": self.test_project["id"],
            "subject": "E2E Test Work Package",
            "description": "This is a test work package created by the E2E test suite",
            "type_id": types[0]["id"],
            "priority_id": priorities[0]["id"],
            "assignee_id": self.test_user["id"]
        })
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "Work package created successfully" in content
        assert "E2E Test Work Package" in content
        
        # Extract work package ID from response
        import re
        id_match = re.search(r'#(\d+)', content)
        if id_match:
            wp_id = int(id_match.group(1))
            self.created_work_packages.append(wp_id)
        
        logger.info("✅ Create work package test passed")
    
    async def test_list_work_packages(self):
        """Test listing work packages"""
        logger.info("Testing list_work_packages tool...")
        
        result = await self.mcp_client.call_tool("list_work_packages", {
            "project_id": self.test_project["id"],
            "status": "open"
        })
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "work package(s)" in content
        assert "E2E Test Work Package" in content
        
        logger.info("✅ List work packages test passed")
    
    async def test_create_meeting(self):
        """Test creating a meeting"""
        logger.info("Testing create_meeting tool...")
        
        # Get types
        types = self.op_client.get_types()
        assert len(types) > 0, "No work package types available"
        
        # Create meeting
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        result = await self.mcp_client.call_tool("create_meeting", {
            "project_id": self.test_project["id"],
            "meeting_title": "E2E Test Meeting",
            "meeting_date": tomorrow,
            "meeting_time": "10:00",
            "duration_minutes": 60,
            "attendees": [self.test_user["id"]],
            "agenda": "Test agenda for E2E testing",
            "meeting_type": "general",
            "location": "Test Room"
        })
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "Meeting work package created successfully" in content
        assert "E2E Test Meeting" in content
        
        logger.info("✅ Create meeting test passed")
    
    async def test_list_meetings(self):
        """Test listing meetings"""
        logger.info("Testing list_meetings tool...")
        
        result = await self.mcp_client.call_tool("list_meetings", {
            "project_id": self.test_project["id"],
            "status": "scheduled"
        })
        
        assert "content" in result
        assert len(result["content"]) > 0
        content = result["content"][0].text
        
        assert "meeting(s)" in content
        assert "E2E Test Meeting" in content
        
        logger.info("✅ List meetings test passed")
    
    async def cleanup(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        # Clean up work packages (if any were created)
        for wp_id in self.created_work_packages:
            try:
                requests.delete(f"{self.openproject_url}/api/v3/work_packages/{wp_id}", 
                              headers=self.op_client.headers)
            except Exception as e:
                logger.warning(f"Failed to cleanup work package {wp_id}: {e}")
        
        # Clean up project
        if self.test_project:
            self.op_client.cleanup_project(self.test_project["id"])
        
        # Clean up user
        if self.test_user:
            self.op_client.cleanup_user(self.test_user["id"])
        
        logger.info("Cleanup completed")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting E2E test suite...")
        
        try:
            # Setup
            await self.setup_test_data()
            
            # Run tests
            await self.test_connection()
            await self.test_list_projects()
            await self.test_list_users()
            await self.test_list_types()
            await self.test_list_priorities()
            await self.test_list_statuses()
            await self.test_create_work_package()
            await self.test_list_work_packages()
            await self.test_create_meeting()
            await self.test_list_meetings()
            
            logger.info("🎉 All tests passed!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    test_suite = E2ETestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
