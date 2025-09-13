#!/usr/bin/env python3
"""
OpenProject MCP Server

A Model Context Protocol (MCP) server that provides integration with OpenProject API v3.
Supports project management, work package tracking, and task creation through a
standardized interface.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import aiohttp
from urllib.parse import quote
import base64
import ssl
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Version information
__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"


class OpenProjectClient:
    """Client for the OpenProject API v3 with optional proxy support"""

    def __init__(self, base_url: str, api_key: str, proxy: Optional[str] = None):
        """
        Initialize the OpenProject client.

        Args:
            base_url: The base URL of the OpenProject instance
            api_key: API key for authentication
            proxy: Optional HTTP proxy URL
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.proxy = proxy

        # Setup headers with Basic Auth
        self.headers = {
            "Authorization": f"Basic {self._encode_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"OpenProject-MCP/{__version__}",
        }

        logger.info(f"OpenProject Client initialized for: {self.base_url}")
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")

    def _encode_api_key(self) -> str:
        """Encode API key for Basic Auth"""
        credentials = f"apikey:{self.api_key}"
        return base64.b64encode(credentials.encode()).decode()

    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Execute an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Optional request body data

        Returns:
            Dict: Response data from the API

        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/api/v3{endpoint}"

        logger.debug(f"API Request: {method} {url}")
        if data:
            logger.debug(f"Request body: {json.dumps(data, indent=2)}")

        # Configure SSL and timeout
        ssl_context = ssl.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            try:
                # Build request parameters
                request_params = {
                    "method": method,
                    "url": url,
                    "headers": self.headers,
                    "json": data,
                }

                # Add proxy if configured
                if self.proxy:
                    request_params["proxy"] = self.proxy

                async with session.request(**request_params) as response:
                    response_text = await response.text()

                    logger.debug(f"Response status: {response.status}")

                    # Parse response
                    try:
                        response_json = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response: {response_text[:200]}...")
                        response_json = {}

                    # Handle errors
                    if response.status >= 400:
                        error_msg = self._format_error_message(response.status, response_text)
                        raise Exception(error_msg)

                    return response_json

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {str(e)}")
                raise Exception(f"Network error accessing {url}: {str(e)}")

    def _format_error_message(self, status: int, response_text: str) -> str:
        """Format error message based on HTTP status code"""
        base_msg = f"API Error {status}: {response_text}"

        error_hints = {
            401: "Authentication failed. Please check your API key.",
            403: "Access denied. The user lacks required permissions.",
            404: "Resource not found. Please verify the URL and resource exists.",
            407: "Proxy authentication required.",
            500: "Internal server error. Please try again later.",
            502: "Bad gateway. The server or proxy is not responding correctly.",
            503: "Service unavailable. The server might be under maintenance.",
        }

        if status in error_hints:
            base_msg += f"\n\n{error_hints[status]}"

        return base_msg

    async def test_connection(self) -> Dict:
        """Test the API connection and authentication"""
        logger.info("Testing API connection...")
        return await self._request("GET", "")

    async def get_projects(self, filters: Optional[str] = None) -> Dict:
        """
        Retrieve all projects.

        Args:
            filters: Optional JSON-encoded filter string

        Returns:
            Dict: API response containing projects
        """
        endpoint = "/projects"
        if filters:
            encoded_filters = quote(filters)
            endpoint += f"?filters={encoded_filters}"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_work_packages(self, project_id: Optional[int] = None, filters: Optional[str] = None) -> Dict:
        """
        Retrieve work packages.

        Args:
            project_id: Optional project ID to filter by
            filters: Optional JSON-encoded filter string

        Returns:
            Dict: API response containing work packages
        """
        if project_id:
            endpoint = f"/projects/{project_id}/work_packages"
        else:
            endpoint = "/work_packages"

        if filters:
            encoded_filters = quote(filters)
            endpoint += f"?filters={encoded_filters}"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def create_work_package(self, data: Dict) -> Dict:
        """
        Create a new work package.

        Args:
            data: Work package data including project, subject, type, etc.

        Returns:
            Dict: Created work package data
        """
        # Prepare initial payload for form
        form_payload = {"_links": {}}

        # Set required links
        if "project" in data:
            form_payload["_links"]["project"] = {"href": f"/api/v3/projects/{data['project']}"}
        if "type" in data:
            form_payload["_links"]["type"] = {"href": f"/api/v3/types/{data['type']}"}

        # Set subject if provided
        if "subject" in data:
            form_payload["subject"] = data["subject"]

        # Get form with initial payload
        form = await self._request("POST", "/work_packages/form", form_payload)

        # Use form payload and add additional fields
        payload = form.get("payload", form_payload)
        payload["lockVersion"] = form.get("lockVersion", 0)

        # Add optional fields
        if "description" in data:
            payload["description"] = {"raw": data["description"]}
        if "priority_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{data['priority_id']}"}
        if "assignee_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["assignee"] = {"href": f"/api/v3/users/{data['assignee_id']}"}

        # Create work package
        return await self._request("POST", "/work_packages", payload)

    async def get_types(self, project_id: Optional[int] = None) -> Dict:
        """
        Retrieve available work package types.

        Args:
            project_id: Optional project ID to filter types by

        Returns:
            Dict: API response containing types
        """
        if project_id:
            endpoint = f"/projects/{project_id}/types"
        else:
            endpoint = "/types"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def create_work_package_relation(
        self,
        work_package_id: int,
        relation_type: str,
        target_work_package_id: int,
        description: Optional[str] = None,
        lag: Optional[int] = None,
    ) -> Dict:
        """
        Create a relationship between two work packages.

        Args:
            work_package_id: ID of the source work package
            relation_type: Type of relationship ("blocks", "follows", "relates",
                "duplicates", "includes", "requires")
            target_work_package_id: ID of the target work package
            description: Optional description of the relationship
            lag: Optional lag in days (for "follows" relationships)

        Returns:
            Dict: Created relationship data
        """
        endpoint = f"/work_packages/{work_package_id}/relations"

        payload = {
            "_links": {"to": {"href": f"/api/v3/work_packages/{target_work_package_id}"}},
            "type": relation_type,
        }

        if description:
            payload["description"] = description
        if lag is not None:
            payload["lag"] = lag

        return await self._request("POST", endpoint, payload)

    async def get_work_package_relations(self, work_package_id: int) -> Dict:
        """
        Get all relationships for a work package.

        Args:
            work_package_id: ID of the work package

        Returns:
            Dict: API response containing relationships
        """
        endpoint = f"/work_packages/{work_package_id}/relations"
        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def delete_work_package_relation(self, relation_id: int) -> Dict:
        """
        Delete a work package relationship.

        Args:
            relation_id: ID of the relationship to delete

        Returns:
            Dict: API response
        """
        endpoint = f"/relations/{relation_id}"
        return await self._request("DELETE", endpoint)

    async def get_users(self, filters: Optional[str] = None) -> Dict:
        """
        Retrieve users.

        Args:
            filters: Optional JSON-encoded filter string

        Returns:
            Dict: API response containing users
        """
        endpoint = "/users"
        if filters:
            encoded_filters = quote(filters)
            endpoint += f"?filters={encoded_filters}"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_priorities(self) -> Dict:
        """
        Retrieve work package priorities.

        Returns:
            Dict: API response containing priorities
        """
        endpoint = "/priorities"
        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def update_work_package(self, work_package_id: int, data: Dict) -> Dict:
        """
        Update an existing work package.

        Args:
            work_package_id: ID of the work package to update
            data: Updated work package data

        Returns:
            Dict: Updated work package data
        """
        endpoint = f"/work_packages/{work_package_id}"

        # Prepare payload for form
        form_payload = {"_links": {}}

        # Set links for updated fields
        if "project" in data:
            form_payload["_links"]["project"] = {"href": f"/api/v3/projects/{data['project']}"}
        if "type" in data:
            form_payload["_links"]["type"] = {"href": f"/api/v3/types/{data['type']}"}
        if "status" in data:
            form_payload["_links"]["status"] = {"href": f"/api/v3/statuses/{data['status']}"}
        if "priority_id" in data:
            form_payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{data['priority_id']}"}
        if "assignee_id" in data:
            form_payload["_links"]["assignee"] = {"href": f"/api/v3/users/{data['assignee_id']}"}

        # Set other fields
        if "subject" in data:
            form_payload["subject"] = data["subject"]
        if "description" in data:
            form_payload["description"] = {"raw": data["description"]}

        # Get form with payload
        form = await self._request("POST", f"/work_packages/{work_package_id}/form", form_payload)

        # Use form payload and add lock version
        payload = form.get("payload", form_payload)
        payload["lockVersion"] = form.get("lockVersion", 0)

        # Update work package
        return await self._request("PATCH", endpoint, payload)

    async def get_statuses(self) -> Dict:
        """
        Retrieve work package statuses.

        Returns:
            Dict: API response containing statuses
        """
        endpoint = "/statuses"
        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def create_work_package_with_fallback_assignee(self, data: Dict) -> Dict:
        """
        Create a work package with fallback handling for assignee permission issues.

        Args:
            data: Work package data including project, subject, type, etc.

        Returns:
            Dict: Created work package data
        """
        try:
            return await self.create_work_package(data)
        except Exception as e:
            # If assignee is not allowed, retry without assignee
            if "assignee" in str(e) and "assignee_id" in data:
                logger.warning(f"Assignee not allowed for work package, retrying without assignee: {e}")
                data_copy = data.copy()
                data_copy.pop("assignee_id", None)
                return await self.create_work_package(data_copy)
            else:
                raise


class OpenProjectMCPServer:
    """MCP Server for OpenProject integration"""

    def __init__(self):
        self.server = Server("openproject-mcp")
        self.client: Optional[OpenProjectClient] = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Register all MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="test_connection",
                    description="Test the connection to the OpenProject API",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="list_projects",
                    description="List all OpenProject projects",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active_only": {
                                "type": "boolean",
                                "description": "Show only active projects",
                                "default": True,
                            }
                        },
                    },
                ),
                Tool(
                    name="list_work_packages",
                    description="List work packages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID (optional, for project-specific work packages)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status filter (open, closed, all)",
                                "enum": ["open", "closed", "all"],
                                "default": "open",
                            },
                        },
                    },
                ),
                Tool(
                    name="list_types",
                    description="List available work package types",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID (optional, for project-specific types)",
                            }
                        },
                    },
                ),
                Tool(
                    name="create_work_package",
                    description="Create a new work package",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID",
                            },
                            "subject": {
                                "type": "string",
                                "description": "Work package title",
                            },
                            "description": {
                                "type": "string",
                                "description": "Description (Markdown supported)",
                            },
                            "type_id": {
                                "type": "integer",
                                "description": "Type ID (e.g., 1 for Task, 2 for Bug)",
                            },
                            "priority_id": {
                                "type": "integer",
                                "description": "Priority ID (optional)",
                            },
                            "assignee_id": {
                                "type": "integer",
                                "description": "Assignee user ID (optional)",
                            },
                        },
                        "required": ["project_id", "subject", "type_id"],
                    },
                ),
                Tool(
                    name="create_work_package_relation",
                    description="Create a relationship between two work packages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_package_id": {
                                "type": "integer",
                                "description": "ID of the source work package",
                            },
                            "relation_type": {
                                "type": "string",
                                "description": "Type of relationship",
                                "enum": [
                                    "blocks",
                                    "follows",
                                    "relates",
                                    "duplicates",
                                    "includes",
                                    "requires",
                                ],
                            },
                            "target_work_package_id": {
                                "type": "integer",
                                "description": "ID of the target work package",
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional description of the relationship",
                            },
                            "lag": {
                                "type": "integer",
                                "description": "Lag in days (for 'follows' relationships)",
                            },
                        },
                        "required": [
                            "work_package_id",
                            "relation_type",
                            "target_work_package_id",
                        ],
                    },
                ),
                Tool(
                    name="list_work_package_relations",
                    description="List all relationships for a work package",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_package_id": {
                                "type": "integer",
                                "description": "ID of the work package",
                            }
                        },
                        "required": ["work_package_id"],
                    },
                ),
                Tool(
                    name="delete_work_package_relation",
                    description="Delete a work package relationship",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relation_id": {
                                "type": "integer",
                                "description": "ID of the relationship to delete",
                            }
                        },
                        "required": ["relation_id"],
                    },
                ),
                Tool(
                    name="list_users",
                    description="List users in the OpenProject instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active_only": {
                                "type": "boolean",
                                "description": "Show only active users",
                                "default": True,
                            }
                        },
                    },
                ),
                Tool(
                    name="list_priorities",
                    description="List available work package priorities",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="list_statuses",
                    description="List available work package statuses",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="update_work_package",
                    description="Update an existing work package",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_package_id": {
                                "type": "integer",
                                "description": "ID of the work package to update",
                            },
                            "subject": {
                                "type": "string",
                                "description": "Updated work package title",
                            },
                            "description": {
                                "type": "string",
                                "description": "Updated description (Markdown supported)",
                            },
                            "status_id": {
                                "type": "integer",
                                "description": "Status ID to update to",
                            },
                            "priority_id": {
                                "type": "integer",
                                "description": "Priority ID to update to",
                            },
                            "assignee_id": {
                                "type": "integer",
                                "description": "Assignee user ID to update to",
                            },
                        },
                        "required": ["work_package_id"],
                    },
                ),
                Tool(
                    name="create_meeting",
                    description="Create a meeting work package with agenda and attendees",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID",
                            },
                            "meeting_title": {
                                "type": "string",
                                "description": "Meeting title",
                            },
                            "meeting_date": {
                                "type": "string",
                                "description": "Meeting date (YYYY-MM-DD format)",
                            },
                            "meeting_time": {
                                "type": "string",
                                "description": "Meeting time (HH:MM format)",
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Meeting duration in minutes",
                                "default": 60,
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Array of user IDs for attendees",
                            },
                            "agenda": {
                                "type": "string",
                                "description": "Meeting agenda items",
                            },
                            "meeting_type": {
                                "type": "string",
                                "description": "Type of meeting",
                                "enum": [
                                    "standup",
                                    "sprint_planning",
                                    "retrospective",
                                    "review",
                                    "general",
                                ],
                                "default": "general",
                            },
                            "location": {
                                "type": "string",
                                "description": "Meeting location or video call link",
                            },
                        },
                        "required": [
                            "project_id",
                            "meeting_title",
                            "meeting_date",
                            "meeting_time",
                        ],
                    },
                ),
                Tool(
                    name="add_meeting_minutes",
                    description="Add minutes and outcomes to a meeting work package",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "meeting_work_package_id": {
                                "type": "integer",
                                "description": "ID of the meeting work package",
                            },
                            "minutes": {
                                "type": "string",
                                "description": "Meeting minutes and discussion points",
                            },
                            "decisions": {
                                "type": "string",
                                "description": "Decisions made during the meeting",
                            },
                            "action_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "assignee_id": {"type": "integer"},
                                        "due_date": {"type": "string"},
                                    },
                                    "required": ["description"],
                                },
                                "description": "Action items from the meeting",
                            },
                            "next_meeting_date": {
                                "type": "string",
                                "description": "Date for next meeting (YYYY-MM-DD format)",
                            },
                        },
                        "required": ["meeting_work_package_id", "minutes"],
                    },
                ),
                Tool(
                    name="create_follow_up_tasks",
                    description="Create follow-up tasks from meeting action items",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "meeting_work_package_id": {
                                "type": "integer",
                                "description": "ID of the meeting work package",
                            },
                            "action_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "assignee_id": {"type": "integer"},
                                        "due_date": {"type": "string"},
                                        "priority_id": {"type": "integer"},
                                    },
                                    "required": ["description"],
                                },
                                "description": "Action items to create as work packages",
                            },
                        },
                        "required": ["meeting_work_package_id", "action_items"],
                    },
                ),
                Tool(
                    name="list_meetings",
                    description="List meeting work packages",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID (optional, for project-specific meetings)",
                            },
                            "meeting_type": {
                                "type": "string",
                                "description": "Filter by meeting type",
                                "enum": [
                                    "standup",
                                    "sprint_planning",
                                    "retrospective",
                                    "review",
                                    "general",
                                ],
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Filter meetings from this date (YYYY-MM-DD)",
                            },
                            "date_to": {
                                "type": "string",
                                "description": "Filter meetings to this date (YYYY-MM-DD)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Filter by status",
                                "enum": ["scheduled", "completed", "cancelled"],
                                "default": "scheduled",
                            },
                        },
                    },
                ),
                Tool(
                    name="schedule_recurring_meeting",
                    description="Schedule a recurring meeting series",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "integer",
                                "description": "Project ID",
                            },
                            "meeting_title": {
                                "type": "string",
                                "description": "Meeting title",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "First meeting date (YYYY-MM-DD format)",
                            },
                            "meeting_time": {
                                "type": "string",
                                "description": "Meeting time (HH:MM format)",
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Meeting duration in minutes",
                                "default": 60,
                            },
                            "frequency": {
                                "type": "string",
                                "description": "Meeting frequency",
                                "enum": ["daily", "weekly", "biweekly", "monthly"],
                                "default": "weekly",
                            },
                            "occurrences": {
                                "type": "integer",
                                "description": "Number of meetings to create",
                                "default": 10,
                            },
                            "attendees": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Array of user IDs for attendees",
                            },
                            "agenda_template": {
                                "type": "string",
                                "description": "Template agenda for all meetings",
                            },
                            "meeting_type": {
                                "type": "string",
                                "description": "Type of meeting",
                                "enum": [
                                    "standup",
                                    "sprint_planning",
                                    "retrospective",
                                    "review",
                                    "general",
                                ],
                                "default": "general",
                            },
                            "location": {
                                "type": "string",
                                "description": "Meeting location or video call link",
                            },
                        },
                        "required": [
                            "project_id",
                            "meeting_title",
                            "start_date",
                            "meeting_time",
                            "frequency",
                        ],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool"""
            if not self.client:
                return [
                    TextContent(
                        type="text",
                        text="Error: OpenProject Client not initialized. Please set environment variables:\n"
                        "- OPENPROJECT_URL=https://your-instance.openproject.com\n"
                        "- OPENPROJECT_API_KEY=your-api-key",
                    )
                ]

            try:
                if name == "test_connection":
                    result = await self.client.test_connection()

                    text = "✅ API connection successful!\n\n"
                    if self.client.proxy:
                        text += f"Connected via proxy: {self.client.proxy}\n"
                    text += f"API Version: {result.get('_type', 'Unknown')}\n"
                    text += f"Instance Version: {result.get('instanceVersion', 'Unknown')}\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_projects":
                    filters = None
                    if arguments.get("active_only", True):
                        filters = json.dumps([{"active": {"operator": "=", "values": ["t"]}}])

                    result = await self.client.get_projects(filters)
                    projects = result.get("_embedded", {}).get("elements", [])

                    if not projects:
                        text = "No projects found."
                    else:
                        text = f"Found {len(projects)} project(s):\n\n"
                        for project in projects:
                            text += f"- **{project['name']}** (ID: {project['id']})\n"
                            if project.get("description", {}).get("raw"):
                                text += f"  {project['description']['raw']}\n"
                            text += f"  Status: {'Active' if project.get('active') else 'Inactive'}\n"
                            text += f"  Public: {'Yes' if project.get('public') else 'No'}\n\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_work_packages":
                    project_id = arguments.get("project_id")
                    status = arguments.get("status", "open")

                    filters = None
                    if status == "open":
                        filters = json.dumps([{"status": {"operator": "open", "values": []}}])
                    elif status == "closed":
                        filters = json.dumps([{"status": {"operator": "closed", "values": []}}])

                    result = await self.client.get_work_packages(project_id, filters)
                    work_packages = result.get("_embedded", {}).get("elements", [])

                    if not work_packages:
                        text = "No work packages found."
                    else:
                        text = f"Found {len(work_packages)} work package(s):\n\n"
                        for wp in work_packages:
                            text += f"- **{wp.get('subject', 'No title')}** (#{wp.get('id', 'N/A')})\n"

                            if "_embedded" in wp:
                                embedded = wp["_embedded"]
                                if "type" in embedded:
                                    text += f"  Type: {embedded['type'].get('name', 'Unknown')}\n"
                                if "status" in embedded:
                                    text += f"  Status: {embedded['status'].get('name', 'Unknown')}\n"
                                if "project" in embedded:
                                    text += f"  Project: {embedded['project'].get('name', 'Unknown')}\n"
                                if "assignee" in embedded and embedded["assignee"]:
                                    text += f"  Assignee: {embedded['assignee'].get('name', 'Unassigned')}\n"

                            if "percentageDone" in wp:
                                text += f"  Progress: {wp['percentageDone']}%\n"

                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_types":
                    result = await self.client.get_types(arguments.get("project_id"))
                    types = result.get("_embedded", {}).get("elements", [])

                    if not types:
                        text = "No work package types found."
                    else:
                        text = "Available work package types:\n\n"
                        for type_item in types:
                            text += f"- **{type_item.get('name', 'Unnamed')}** (ID: {type_item.get('id', 'N/A')})\n"
                            if type_item.get("isDefault"):
                                text += "  ✓ Default type\n"
                            if type_item.get("isMilestone"):
                                text += "  ✓ Milestone\n"
                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "create_work_package":
                    data = {
                        "project": arguments["project_id"],
                        "subject": arguments["subject"],
                        "type": arguments["type_id"],
                    }

                    # Add optional fields
                    for field in ["description", "priority_id", "assignee_id"]:
                        if field in arguments:
                            data[field] = arguments[field]

                    result = await self.client.create_work_package(data)

                    text = "✅ Work package created successfully:\n\n"
                    text += f"- **Title**: {result.get('subject', 'N/A')}\n"
                    text += f"- **ID**: #{result.get('id', 'N/A')}\n"

                    if "_embedded" in result:
                        embedded = result["_embedded"]
                        if "type" in embedded:
                            text += f"- **Type**: {embedded['type'].get('name', 'Unknown')}\n"
                        if "status" in embedded:
                            text += f"- **Status**: {embedded['status'].get('name', 'Unknown')}\n"
                        if "project" in embedded:
                            text += f"- **Project**: {embedded['project'].get('name', 'Unknown')}\n"

                    return [TextContent(type="text", text=text)]

                elif name == "create_work_package_relation":
                    work_package_id = arguments["work_package_id"]
                    relation_type = arguments["relation_type"]
                    target_work_package_id = arguments["target_work_package_id"]
                    description = arguments.get("description")
                    lag = arguments.get("lag")

                    result = await self.client.create_work_package_relation(
                        work_package_id,
                        relation_type,
                        target_work_package_id,
                        description,
                        lag,
                    )

                    text = "✅ Work package relationship created successfully:\n\n"
                    text += f"- **From Work Package**: #{work_package_id}\n"
                    text += f"- **To Work Package**: #{target_work_package_id}\n"
                    text += f"- **Relationship Type**: {relation_type}\n"
                    text += f"- **Relationship ID**: {result.get('id', 'N/A')}\n"

                    if description:
                        text += f"- **Description**: {description}\n"
                    if lag is not None:
                        text += f"- **Lag**: {lag} days\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_work_package_relations":
                    work_package_id = arguments["work_package_id"]

                    result = await self.client.get_work_package_relations(work_package_id)
                    relations = result.get("_embedded", {}).get("elements", [])

                    if not relations:
                        text = f"No relationships found for work package #{work_package_id}."
                    else:
                        text = f"Found {len(relations)} relationship(s) for work package #{work_package_id}:\n\n"

                        for relation in relations:
                            text += f"- **Relationship #{relation.get('id', 'N/A')}**\n"
                            text += f"  Type: {relation.get('type', 'Unknown')}\n"

                            if "_embedded" in relation:
                                embedded = relation["_embedded"]
                                if "to" in embedded:
                                    to_wp = embedded["to"]
                                    text += (
                                        f"  Target: #{to_wp.get('id', 'N/A')} - "
                                        f"{to_wp.get('subject', 'No title')}\n"
                                    )
                                if "from" in embedded:
                                    from_wp = embedded["from"]
                                    text += (
                                        f"  Source: #{from_wp.get('id', 'N/A')} - "
                                        f"{from_wp.get('subject', 'No title')}\n"
                                    )

                            if relation.get("description"):
                                text += f"  Description: {relation['description']}\n"
                            if relation.get("lag") is not None:
                                text += f"  Lag: {relation['lag']} days\n"

                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "delete_work_package_relation":
                    relation_id = arguments["relation_id"]

                    await self.client.delete_work_package_relation(relation_id)

                    text = f"✅ Work package relationship #{relation_id} deleted successfully."

                    return [TextContent(type="text", text=text)]

                elif name == "list_users":
                    filters = None
                    if arguments.get("active_only", True):
                        filters = json.dumps([{"status": {"operator": "=", "values": ["active"]}}])

                    result = await self.client.get_users(filters)
                    users = result.get("_embedded", {}).get("elements", [])

                    if not users:
                        text = "No users found."
                    else:
                        text = f"Found {len(users)} user(s):\n\n"
                        for user in users:
                            text += f"- **{user.get('name', 'Unknown')}** (ID: {user.get('id', 'N/A')})\n"
                            text += f"  Email: {user.get('email', 'N/A')}\n"
                            text += f"  Status: {user.get('status', 'Unknown')}\n"
                            text += f"  Admin: {'Yes' if user.get('admin') else 'No'}\n\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_priorities":
                    result = await self.client.get_priorities()
                    priorities = result.get("_embedded", {}).get("elements", [])

                    if not priorities:
                        text = "No priorities found."
                    else:
                        text = "Available work package priorities:\n\n"
                        for priority in priorities:
                            text += f"- **{priority.get('name', 'Unnamed')}** (ID: {priority.get('id', 'N/A')})\n"
                            if priority.get("isDefault"):
                                text += "  ✓ Default priority\n"
                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_statuses":
                    result = await self.client.get_statuses()
                    statuses = result.get("_embedded", {}).get("elements", [])

                    if not statuses:
                        text = "No statuses found."
                    else:
                        text = "Available work package statuses:\n\n"
                        for status in statuses:
                            text += f"- **{status.get('name', 'Unnamed')}** (ID: {status.get('id', 'N/A')})\n"
                            if status.get("isDefault"):
                                text += "  ✓ Default status\n"
                            if status.get("isClosed"):
                                text += "  ✓ Closed status\n"
                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "update_work_package":
                    work_package_id = arguments["work_package_id"]
                    data = {}

                    # Map arguments to data structure
                    if "subject" in arguments:
                        data["subject"] = arguments["subject"]
                    if "description" in arguments:
                        data["description"] = arguments["description"]
                    if "status_id" in arguments:
                        data["status"] = arguments["status_id"]
                    if "priority_id" in arguments:
                        data["priority_id"] = arguments["priority_id"]
                    if "assignee_id" in arguments:
                        data["assignee_id"] = arguments["assignee_id"]

                    result = await self.client.update_work_package(work_package_id, data)

                    text = f"✅ Work package #{work_package_id} updated successfully:\n\n"
                    text += f"- **Title**: {result.get('subject', 'N/A')}\n"
                    text += f"- **ID**: #{result.get('id', 'N/A')}\n"

                    if "_embedded" in result:
                        embedded = result["_embedded"]
                        if "type" in embedded:
                            text += f"- **Type**: {embedded['type'].get('name', 'Unknown')}\n"
                        if "status" in embedded:
                            text += f"- **Status**: {embedded['status'].get('name', 'Unknown')}\n"
                        if "project" in embedded:
                            text += f"- **Project**: {embedded['project'].get('name', 'Unknown')}\n"

                    return [TextContent(type="text", text=text)]

                elif name == "create_meeting":
                    project_id = arguments["project_id"]
                    meeting_title = arguments["meeting_title"]
                    meeting_date = arguments["meeting_date"]
                    meeting_time = arguments["meeting_time"]
                    duration_minutes = arguments.get("duration_minutes", 60)
                    attendees = arguments.get("attendees", [])
                    agenda = arguments.get("agenda", "")
                    meeting_type = arguments.get("meeting_type", "general")
                    location = arguments.get("location", "")

                    # Create meeting description with all details
                    description = f"""## Meeting Details
- **Date**: {meeting_date}
- **Time**: {meeting_time}
- **Duration**: {duration_minutes} minutes
- **Type**: {meeting_type.title()}
- **Location**: {location if location else 'TBD'}

## Attendees
{', '.join([f"User ID {user_id}" for user_id in attendees]) if attendees else 'TBD'}

## Agenda
{agenda if agenda else 'To be determined'}

---
*This work package represents a meeting. Use 'add_meeting_minutes' to add minutes and outcomes after the meeting.*"""

                    # Create work package data
                    data = {
                        "project": project_id,
                        "subject": f"Meeting: {meeting_title}",
                        "type": 1,  # Assuming type 1 is Task - this should be configurable
                        "description": description,
                    }

                    # Try to assign to first attendee, but don't fail if not allowed
                    if attendees:
                        data["assignee_id"] = attendees[0]

                    result = await self.client.create_work_package_with_fallback_assignee(data)

                    text = "✅ Meeting work package created successfully:\n\n"
                    text += f"- **Meeting**: {meeting_title}\n"
                    text += f"- **Date**: {meeting_date} at {meeting_time}\n"
                    text += f"- **Duration**: {duration_minutes} minutes\n"
                    text += f"- **Work Package ID**: #{result.get('id', 'N/A')}\n"
                    text += f"- **Type**: {meeting_type.title()}\n"
                    if location:
                        text += f"- **Location**: {location}\n"
                    if attendees:
                        text += f"- **Attendees**: {len(attendees)} people\n"

                    # Check if assignee was actually set
                    if attendees and "_embedded" in result and "assignee" in result["_embedded"]:
                        text += (
                            f"- **Organizer**: "
                            f"{result['_embedded']['assignee'].get('name', 'User ID ' + str(attendees[0]))}\n"
                        )
                    elif attendees:
                        text += "- **Note**: Could not assign organizer due to permission constraints\n"

                    return [TextContent(type="text", text=text)]

                elif name == "add_meeting_minutes":
                    meeting_work_package_id = arguments["meeting_work_package_id"]
                    minutes = arguments["minutes"]
                    decisions = arguments.get("decisions", "")
                    action_items = arguments.get("action_items", [])
                    next_meeting_date = arguments.get("next_meeting_date", "")

                    # Create minutes description
                    minutes_description = f"""## Meeting Minutes

### Discussion Points
{minutes}

### Decisions Made
{decisions if decisions else 'None recorded'}

### Action Items
"""

                    if action_items:
                        for i, item in enumerate(action_items, 1):
                            minutes_description += f"{i}. {item['description']}"
                            if item.get("assignee_id"):
                                minutes_description += f" (Assigned to User ID {item['assignee_id']})"
                            if item.get("due_date"):
                                minutes_description += f" (Due: {item['due_date']})"
                            minutes_description += "\n"
                    else:
                        minutes_description += "None recorded\n"

                    if next_meeting_date:
                        minutes_description += f"\n### Next Meeting\nScheduled for: {next_meeting_date}\n"

                    minutes_description += "\n---\n*Minutes added on " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*"

                    # Update the work package with minutes
                    update_data = {"description": minutes_description}

                    result = await self.client.update_work_package(meeting_work_package_id, update_data)

                    text = f"✅ Meeting minutes added to work package #{meeting_work_package_id}:\n\n"
                    text += "- **Minutes**: Added discussion points and outcomes\n"
                    if decisions:
                        text += f"- **Decisions**: {len(decisions.split('.'))} decisions recorded\n"
                    if action_items:
                        text += f"- **Action Items**: {len(action_items)} items recorded\n"
                    if next_meeting_date:
                        text += f"- **Next Meeting**: {next_meeting_date}\n"

                    return [TextContent(type="text", text=text)]

                elif name == "create_follow_up_tasks":
                    meeting_work_package_id = arguments["meeting_work_package_id"]
                    action_items = arguments["action_items"]

                    created_tasks = []

                    for item in action_items:
                        task_data = {
                            "project": 1,  # This should be derived from the meeting work package
                            "subject": item["description"],
                            "type": 1,  # Task type
                            "description": f"Follow-up task from meeting work package #{meeting_work_package_id}",
                        }

                        if item.get("assignee_id"):
                            task_data["assignee_id"] = item["assignee_id"]
                        if item.get("priority_id"):
                            task_data["priority_id"] = item["priority_id"]

                        result = await self.client.create_work_package(task_data)
                        created_tasks.append(
                            {
                                "id": result.get("id"),
                                "subject": result.get("subject"),
                                "assignee": item.get("assignee_id"),
                                "due_date": item.get("due_date"),
                            }
                        )

                    text = (
                        f"✅ Created {len(created_tasks)} follow-up task(s) "
                        f"from meeting #{meeting_work_package_id}:\n\n"
                    )

                    for task in created_tasks:
                        text += f"- **Task #{task['id']}**: {task['subject']}\n"
                        if task["assignee"]:
                            text += f"  Assigned to: User ID {task['assignee']}\n"
                        if task["due_date"]:
                            text += f"  Due: {task['due_date']}\n"
                        text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "list_meetings":
                    project_id = arguments.get("project_id")
                    meeting_type = arguments.get("meeting_type")
                    date_from = arguments.get("date_from")
                    date_to = arguments.get("date_to")
                    status = arguments.get("status", "scheduled")

                    # Build filters for meeting work packages
                    filters = []

                    # Filter by project if specified
                    if project_id:
                        filters.append({"project": {"operator": "=", "values": [str(project_id)]}})

                    # Filter by meeting type (assuming it's in the subject)
                    if meeting_type:
                        filters.append(
                            {
                                "subject": {
                                    "operator": "~",
                                    "values": [f"Meeting:.*{meeting_type.title()}"],
                                }
                            }
                        )

                    # Filter by date range - use proper OpenProject date filter format
                    if date_from:
                        filters.append(
                            {
                                "createdAt": {
                                    "operator": ">=",
                                    "values": [f"{date_from}T00:00:00Z"],
                                }
                            }
                        )
                    if date_to:
                        filters.append(
                            {
                                "createdAt": {
                                    "operator": "<=",
                                    "values": [f"{date_to}T23:59:59Z"],
                                }
                            }
                        )

                    # Don't add status filter by default - let OpenProject return all statuses
                    # The status filtering will be done in post-processing

                    filters_json = json.dumps(filters) if filters else None

                    result = await self.client.get_work_packages(project_id, filters_json)
                    meetings = result.get("_embedded", {}).get("elements", [])

                    # Filter meetings by subject containing "Meeting:"
                    meetings = [m for m in meetings if m.get("subject", "").startswith("Meeting:")]

                    # Post-process status filtering
                    if status == "completed":
                        meetings = [
                            m for m in meetings if m.get("_embedded", {}).get("status", {}).get("isClosed", False)
                        ]
                    elif status == "scheduled":
                        meetings = [
                            m for m in meetings if not m.get("_embedded", {}).get("status", {}).get("isClosed", True)
                        ]
                    elif status == "cancelled":
                        meetings = [
                            m
                            for m in meetings
                            if "cancelled" in m.get("_embedded", {}).get("status", {}).get("name", "").lower()
                        ]

                    if not meetings:
                        text = "No meetings found."
                    else:
                        text = f"Found {len(meetings)} meeting(s):\n\n"
                        for meeting in meetings:
                            subject = meeting.get("subject", "No title")
                            if subject.startswith("Meeting: "):
                                meeting_title = subject[9:]  # Remove "Meeting: " prefix
                            else:
                                meeting_title = subject

                            text += f"- **{meeting_title}** (#{meeting.get('id', 'N/A')})\n"

                            if "_embedded" in meeting:
                                embedded = meeting["_embedded"]
                                if "status" in embedded:
                                    text += f"  Status: {embedded['status'].get('name', 'Unknown')}\n"
                                if "project" in embedded:
                                    text += f"  Project: {embedded['project'].get('name', 'Unknown')}\n"
                                if "assignee" in embedded and embedded["assignee"]:
                                    text += f"  Organizer: {embedded['assignee'].get('name', 'Unassigned')}\n"

                            text += f"  Created: {meeting.get('createdAt', 'Unknown')[:10]}\n"
                            text += "\n"

                    return [TextContent(type="text", text=text)]

                elif name == "schedule_recurring_meeting":
                    project_id = arguments["project_id"]
                    meeting_title = arguments["meeting_title"]
                    start_date = arguments["start_date"]
                    meeting_time = arguments["meeting_time"]
                    duration_minutes = arguments.get("duration_minutes", 60)
                    frequency = arguments["frequency"]
                    occurrences = arguments.get("occurrences", 10)
                    attendees = arguments.get("attendees", [])
                    agenda_template = arguments.get("agenda_template", "")
                    meeting_type = arguments.get("meeting_type", "general")
                    location = arguments.get("location", "")

                    from datetime import datetime, timedelta

                    # Calculate meeting dates based on frequency
                    meeting_dates = []
                    current_date = datetime.strptime(start_date, "%Y-%m-%d")

                    for i in range(occurrences):
                        meeting_dates.append(current_date.strftime("%Y-%m-%d"))

                        if frequency == "daily":
                            current_date += timedelta(days=1)
                        elif frequency == "weekly":
                            current_date += timedelta(weeks=1)
                        elif frequency == "biweekly":
                            current_date += timedelta(weeks=2)
                        elif frequency == "monthly":
                            current_date += timedelta(days=30)  # Approximate month

                    created_meetings = []

                    for i, meeting_date in enumerate(meeting_dates, 1):
                        # Create meeting description
                        description = f"""## Meeting Details
- **Date**: {meeting_date}
- **Time**: {meeting_time}
- **Duration**: {duration_minutes} minutes
- **Type**: {meeting_type.title()}
- **Location**: {location if location else 'TBD'}
- **Series**: {i} of {occurrences}

## Attendees
{', '.join([f"User ID {user_id}" for user_id in attendees]) if attendees else 'TBD'}

## Agenda
{agenda_template if agenda_template else 'To be determined'}

---
---
---
*This work package represents a recurring meeting.
Use 'add_meeting_minutes' to add minutes and outcomes after the meeting.*"""

                        # Create work package data
                        data = {
                            "project": project_id,
                            "subject": f"Meeting: {meeting_title} ({i}/{occurrences})",
                            "type": 1,  # Assuming type 1 is Task
                            "description": description,
                        }

                        # Try to assign to first attendee, but don't fail if not allowed
                        if attendees:
                            data["assignee_id"] = attendees[0]

                        result = await self.client.create_work_package_with_fallback_assignee(data)
                        created_meetings.append(
                            {
                                "id": result.get("id"),
                                "date": meeting_date,
                                "title": f"{meeting_title} ({i}/{occurrences})",
                            }
                        )

                    text = f"✅ Created {len(created_meetings)} recurring meeting(s):\n\n"
                    text += f"- **Series**: {meeting_title}\n"
                    text += f"- **Frequency**: {frequency}\n"
                    text += f"- **Total Meetings**: {len(created_meetings)}\n"
                    text += f"- **Start Date**: {start_date}\n"
                    text += f"- **Time**: {meeting_time}\n"
                    text += f"- **Duration**: {duration_minutes} minutes\n\n"

                    text += "Created meetings:\n"
                    for meeting in created_meetings[:5]:  # Show first 5
                        text += f"- #{meeting['id']}: {meeting['title']} on {meeting['date']}\n"

                    if len(created_meetings) > 5:
                        text += f"... and {len(created_meetings) - 5} more meetings\n"

                    return [TextContent(type="text", text=text)]

                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)

                error_text = f"❌ Error executing tool '{name}':\n\n{str(e)}"

                return [TextContent(type="text", text=error_text)]

    async def run(self):
        """Start the MCP server"""
        # Initialize OpenProject client from environment variables
        base_url = os.getenv("OPENPROJECT_URL")
        api_key = os.getenv("OPENPROJECT_API_KEY")
        proxy = os.getenv("OPENPROJECT_PROXY")  # Optional proxy

        if not base_url or not api_key:
            logger.error("OPENPROJECT_URL or OPENPROJECT_API_KEY not set!")
            logger.info("Please set the required environment variables in .env file")
        else:
            self.client = OpenProjectClient(base_url, api_key, proxy)
            logger.info(f"✅ OpenProject Client initialized for {base_url}")

            # Optional: Test connection on startup
            if os.getenv("TEST_CONNECTION_ON_STARTUP", "false").lower() == "true":
                try:
                    await self.client.test_connection()
                    logger.info("✅ API connection test successful!")
                except Exception as e:
                    logger.error(f"❌ API connection test failed: {e}")

        # Start the server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main():
    """Main entry point"""
    logger.info(f"Starting OpenProject MCP Server v{__version__}")

    server = OpenProjectMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
