"""
OpenProject API Client

A comprehensive async client for OpenProject API v3 with proxy support.
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

# Configure logging
logger = logging.getLogger(__name__)

# Version information
__version__ = "2.0.0"


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

    async def _request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
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

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
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
                        response_json = (
                            json.loads(response_text) if response_text else {}
                        )
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response: {response_text[:200]}...")
                        response_json = {}

                    # Handle errors
                    if response.status >= 400:
                        error_msg = self._format_error_message(
                            response.status, response_text
                        )
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

    async def get_work_packages(
        self,
        project_id: Optional[int] = None,
        filters: Optional[str] = None,
        offset: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict:
        """
        Retrieve work packages.

        Args:
            project_id: Optional project ID to filter by
            filters: Optional JSON-encoded filter string
            offset: Optional starting index for pagination
            page_size: Optional number of results per page

        Returns:
            Dict: API response containing work packages
        """
        if project_id:
            endpoint = f"/projects/{project_id}/work_packages"
        else:
            endpoint = "/work_packages"

        # Build query parameters
        query_params = []
        if filters:
            encoded_filters = quote(filters)
            query_params.append(f"filters={encoded_filters}")
        if offset is not None:
            query_params.append(f"offset={offset}")
        if page_size is not None:
            query_params.append(f"pageSize={page_size}")

        if query_params:
            endpoint += "?" + "&".join(query_params)

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
            form_payload["_links"]["project"] = {
                "href": f"/api/v3/projects/{data['project']}"
            }
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
            payload["_links"]["priority"] = {
                "href": f"/api/v3/priorities/{data['priority_id']}"
            }
        if "assignee_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["assignee"] = {
                "href": f"/api/v3/users/{data['assignee_id']}"
            }
        if "version_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["version"] = {
                "href": f"/api/v3/versions/{data['version_id']}"
            }

        # Add date fields (ISO 8601 format: YYYY-MM-DD)
        if "startDate" in data:
            payload["startDate"] = data["startDate"]
        if "dueDate" in data:
            payload["dueDate"] = data["dueDate"]
        if "date" in data:
            payload["date"] = data["date"]

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

    async def get_user(self, user_id: int) -> Dict:
        """
        Retrieve a specific user by ID.

        Args:
            user_id: The user ID

        Returns:
            Dict: User data
        """
        return await self._request("GET", f"/users/{user_id}")

    async def get_memberships(
        self, project_id: Optional[int] = None, user_id: Optional[int] = None
    ) -> Dict:
        """
        Retrieve memberships.

        Args:
            project_id: Optional project ID to filter memberships by project
            user_id: Optional user ID to filter memberships by user

        Returns:
            Dict: API response containing memberships
        """
        endpoint = "/memberships"

        # Use filters instead of path-based filtering for better compatibility
        filters = []
        if project_id:
            filters.append({"project": {"operator": "=", "values": [project_id]}})
        if user_id:
            filters.append({"user": {"operator": "=", "values": [str(user_id)]}})

        if filters:
            filter_string = quote(json.dumps(filters))
            endpoint += f"?filters={filter_string}"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_statuses(self) -> Dict:
        """
        Retrieve available work package statuses.

        Returns:
            Dict: API response containing statuses
        """
        result = await self._request("GET", "/statuses")

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_priorities(self) -> Dict:
        """
        Retrieve available work package priorities.

        Returns:
            Dict: API response containing priorities
        """
        result = await self._request("GET", "/priorities")

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_work_package(self, work_package_id: int) -> Dict:
        """
        Retrieve a specific work package by ID.

        Args:
            work_package_id: The work package ID

        Returns:
            Dict: Work package data
        """
        return await self._request("GET", f"/work_packages/{work_package_id}")

    async def update_work_package(self, work_package_id: int, data: Dict) -> Dict:
        """
        Update an existing work package.

        Args:
            work_package_id: The work package ID
            data: Update data including fields to modify

        Returns:
            Dict: Updated work package data
        """
        # First get current work package to get lock version
        current_wp = await self.get_work_package(work_package_id)

        # Prepare payload with lock version
        payload = {"lockVersion": current_wp.get("lockVersion", 0)}

        # Add fields to update
        if "subject" in data:
            payload["subject"] = data["subject"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}
        if "type_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["type"] = {"href": f"/api/v3/types/{data['type_id']}"}
        if "status_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["status"] = {
                "href": f"/api/v3/statuses/{data['status_id']}"
            }
        if "priority_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["priority"] = {
                "href": f"/api/v3/priorities/{data['priority_id']}"
            }
        if "assignee_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["assignee"] = {
                "href": f"/api/v3/users/{data['assignee_id']}"
            }
        if "version_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["version"] = {
                "href": f"/api/v3/versions/{data['version_id']}"
            }
        if "percentage_done" in data:
            payload["percentageDone"] = data["percentage_done"]
        if "parent_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            if data["parent_id"] is None:
                # Remove parent
                payload["_links"]["parent"] = {"href": None}
            else:
                # Set parent
                payload["_links"]["parent"] = {
                    "href": f"/api/v3/work_packages/{data['parent_id']}"
                }

        # Add date fields (ISO 8601 format: YYYY-MM-DD)
        if "startDate" in data:
            payload["startDate"] = data["startDate"]
        if "dueDate" in data:
            payload["dueDate"] = data["dueDate"]
        if "date" in data:
            payload["date"] = data["date"]

        return await self._request(
            "PATCH", f"/work_packages/{work_package_id}", payload
        )

    async def delete_work_package(self, work_package_id: int) -> bool:
        """
        Delete a work package.

        Args:
            work_package_id: The work package ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/work_packages/{work_package_id}")
        return True

    async def add_work_package_comment(
        self, work_package_id: int, comment: str, internal: bool = False
    ) -> Dict:
        """
        Add a comment/activity to a work package.

        Args:
            work_package_id: The work package ID
            comment: Comment text (supports markdown)
            internal: Whether the comment is internal (visible only to team members)

        Returns:
            Dict: API response containing the created activity
        """
        payload = {
            "comment": {
                "format": "markdown",
                "raw": comment
            }
        }

        if internal:
            payload["internal"] = internal

        return await self._request(
            "POST", f"/work_packages/{work_package_id}/activities", payload
        )

    async def get_work_package_activities(self, work_package_id: int) -> Dict:
        """
        Retrieve activities (comments, changes) for a work package.

        Args:
            work_package_id: The work package ID

        Returns:
            Dict: API response containing activities
        """
        result = await self._request(
            "GET", f"/work_packages/{work_package_id}/activities"
        )

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_time_entries(self, filters: Optional[str] = None) -> Dict:
        """
        Retrieve time entries.

        Args:
            filters: Optional JSON-encoded filter string

        Returns:
            Dict: API response containing time entries
        """
        endpoint = "/time_entries"
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

    async def create_time_entry(self, data: Dict) -> Dict:
        """
        Create a new time entry.

        Args:
            data: Time entry data including work package, hours, etc.

        Returns:
            Dict: Created time entry data
        """
        # Prepare payload
        payload = {}

        # Set required fields
        if "work_package_id" in data:
            payload["_links"] = {
                "workPackage": {
                    "href": f"/api/v3/work_packages/{data['work_package_id']}"
                }
            }
        if "hours" in data:
            payload["hours"] = f"PT{data['hours']}H"
        if "spent_on" in data:
            payload["spentOn"] = data["spent_on"]
        if "comment" in data:
            payload["comment"] = {"raw": data["comment"]}
        if "activity_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["activity"] = {
                "href": f"/api/v3/time_entries/activities/{data['activity_id']}"
            }

        return await self._request("POST", "/time_entries", payload)

    async def update_time_entry(self, time_entry_id: int, data: Dict) -> Dict:
        """
        Update an existing time entry.

        Args:
            time_entry_id: The time entry ID
            data: Update data including fields to modify

        Returns:
            Dict: Updated time entry data
        """
        # First get current time entry to get lock version
        current_te = await self._request("GET", f"/time_entries/{time_entry_id}")

        # Prepare payload with lock version
        payload = {"lockVersion": current_te.get("lockVersion", 0)}

        # Add fields to update
        if "hours" in data:
            payload["hours"] = f"PT{data['hours']}H"
        if "spent_on" in data:
            payload["spentOn"] = data["spent_on"]
        if "comment" in data:
            payload["comment"] = {"raw": data["comment"]}
        if "activity_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["activity"] = {
                "href": f"/api/v3/time_entries/activities/{data['activity_id']}"
            }

        return await self._request("PATCH", f"/time_entries/{time_entry_id}", payload)

    async def delete_time_entry(self, time_entry_id: int) -> bool:
        """
        Delete a time entry.

        Args:
            time_entry_id: The time entry ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/time_entries/{time_entry_id}")
        return True

    async def get_time_entry_activities(self) -> Dict:
        """
        Retrieve available time entry activities.

        Returns:
            Dict: API response containing activities
        """
        result = await self._request("GET", "/time_entries/activities")

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_versions(self, project_id: Optional[int] = None) -> Dict:
        """
        Retrieve project versions.

        Args:
            project_id: Optional project ID to filter versions by project

        Returns:
            Dict: API response containing versions
        """
        if project_id:
            endpoint = f"/projects/{project_id}/versions"
        else:
            endpoint = "/versions"

        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def create_version(self, project_id: int, data: Dict) -> Dict:
        """
        Create a new project version.

        Args:
            project_id: The project ID
            data: Version data including name, description, etc.

        Returns:
            Dict: Created version data
        """
        # Prepare payload
        payload = {
            "_links": {"definingProject": {"href": f"/api/v3/projects/{project_id}"}}
        }

        # Set required fields
        if "name" in data:
            payload["name"] = data["name"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}
        if "start_date" in data:
            payload["startDate"] = data["start_date"]
        if "end_date" in data:
            payload["endDate"] = data["end_date"]
        if "status" in data:
            payload["status"] = data["status"]

        return await self._request("POST", "/versions", payload)

    async def check_permissions(self) -> Dict:
        """
        Check user permissions and capabilities.

        Returns:
            Dict: User information including permissions
        """
        try:
            # Get current user info which includes permissions
            return await self._request("GET", "/users/me")
        except Exception as e:
            logger.error(f"Failed to check permissions: {e}")
            return {}

    async def create_project(self, data: Dict) -> Dict:
        """
        Create a new project.

        Args:
            data: Project data including name, identifier, description, etc.

        Returns:
            Dict: Created project data
        """
        # Prepare payload
        payload = {}

        # Set required fields
        if "name" in data:
            payload["name"] = data["name"]
        if "identifier" in data:
            payload["identifier"] = data["identifier"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}
        if "public" in data:
            payload["public"] = data["public"]
        if "status" in data:
            payload["status"] = data["status"]
        if "parent_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["parent"] = {
                "href": f"/api/v3/projects/{data['parent_id']}"
            }

        return await self._request("POST", "/projects", payload)

    async def update_project(self, project_id: int, data: Dict) -> Dict:
        """
        Update an existing project.

        Args:
            project_id: The project ID
            data: Update data including fields to modify

        Returns:
            Dict: Updated project data
        """
        # First get current project to get lock version if needed
        try:
            current_project = await self.get_project(project_id)
            lock_version = current_project.get("lockVersion", 0)
        except:
            lock_version = 0

        # Prepare payload with lock version
        payload = {"lockVersion": lock_version}

        # Add fields to update
        if "name" in data:
            payload["name"] = data["name"]
        if "identifier" in data:
            payload["identifier"] = data["identifier"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}
        if "public" in data:
            payload["public"] = data["public"]
        if "status" in data:
            payload["status"] = data["status"]
        if "parent_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["parent"] = {
                "href": f"/api/v3/projects/{data['parent_id']}"
            }

        return await self._request("PATCH", f"/projects/{project_id}", payload)

    async def delete_project(self, project_id: int) -> bool:
        """
        Delete a project.

        Args:
            project_id: The project ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/projects/{project_id}")
        return True

    async def get_project(self, project_id: int) -> Dict:
        """
        Retrieve a specific project by ID.

        Args:
            project_id: The project ID

        Returns:
            Dict: Project data
        """
        return await self._request("GET", f"/projects/{project_id}")

    async def get_roles(self) -> Dict:
        """
        Retrieve available roles.

        Returns:
            Dict: API response containing roles
        """
        result = await self._request("GET", "/roles")

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_role(self, role_id: int) -> Dict:
        """
        Retrieve a specific role by ID.

        Args:
            role_id: The role ID

        Returns:
            Dict: Role data
        """
        return await self._request("GET", f"/roles/{role_id}")

    async def create_membership(self, data: Dict) -> Dict:
        """
        Create a new membership.

        Args:
            data: Membership data including project, user/group, and roles

        Returns:
            Dict: Created membership data
        """
        # Prepare payload
        payload = {"_links": {}}

        # Set required fields
        if "project_id" in data:
            payload["_links"]["project"] = {
                "href": f"/api/v3/projects/{data['project_id']}"
            }
        if "user_id" in data:
            payload["_links"]["principal"] = {
                "href": f"/api/v3/users/{data['user_id']}"
            }
        elif "group_id" in data:
            payload["_links"]["principal"] = {
                "href": f"/api/v3/groups/{data['group_id']}"
            }
        if "role_ids" in data:
            payload["_links"]["roles"] = [
                {"href": f"/api/v3/roles/{role_id}"} for role_id in data["role_ids"]
            ]
        elif "role_id" in data:
            payload["_links"]["roles"] = [{"href": f"/api/v3/roles/{data['role_id']}"}]
        if "notification_message" in data:
            payload["notificationMessage"] = {"raw": data["notification_message"]}

        return await self._request("POST", "/memberships", payload)

    async def update_membership(self, membership_id: int, data: Dict) -> Dict:
        """
        Update an existing membership.

        Args:
            membership_id: The membership ID
            data: Update data including fields to modify

        Returns:
            Dict: Updated membership data
        """
        # First get current membership to get lock version if needed
        try:
            current_membership = await self.get_membership(membership_id)
            lock_version = current_membership.get("lockVersion", 0)
        except:
            lock_version = 0

        # Prepare payload with lock version
        payload = {"lockVersion": lock_version}

        # Add fields to update
        if "role_ids" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["roles"] = [
                {"href": f"/api/v3/roles/{role_id}"} for role_id in data["role_ids"]
            ]
        elif "role_id" in data:
            if "_links" not in payload:
                payload["_links"] = {}
            payload["_links"]["roles"] = [{"href": f"/api/v3/roles/{data['role_id']}"}]
        if "notification_message" in data:
            payload["notificationMessage"] = {"raw": data["notification_message"]}

        return await self._request("PATCH", f"/memberships/{membership_id}", payload)

    async def delete_membership(self, membership_id: int) -> bool:
        """
        Delete a membership.

        Args:
            membership_id: The membership ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/memberships/{membership_id}")
        return True

    async def get_membership(self, membership_id: int) -> Dict:
        """
        Retrieve a specific membership by ID.

        Args:
            membership_id: The membership ID

        Returns:
            Dict: Membership data
        """
        return await self._request("GET", f"/memberships/{membership_id}")

    async def set_work_package_parent(
        self, work_package_id: int, parent_id: int
    ) -> Dict:
        """
        Set a parent for a work package (create parent-child relationship).

        Args:
            work_package_id: The work package ID to become a child
            parent_id: The work package ID to become the parent

        Returns:
            Dict: Updated work package data
        """
        # First get current work package to get lock version
        try:
            current_wp = await self.get_work_package(work_package_id)
            lock_version = current_wp.get("lockVersion", 0)
        except:
            lock_version = 0

        # Prepare payload with parent link
        payload = {
            "lockVersion": lock_version,
            "_links": {"parent": {"href": f"/api/v3/work_packages/{parent_id}"}},
        }

        return await self._request(
            "PATCH", f"/work_packages/{work_package_id}", payload
        )

    async def remove_work_package_parent(self, work_package_id: int) -> Dict:
        """
        Remove parent relationship from a work package (make it top-level).

        Args:
            work_package_id: The work package ID to remove parent from

        Returns:
            Dict: Updated work package data
        """
        # First get current work package to get lock version
        try:
            current_wp = await self.get_work_package(work_package_id)
            lock_version = current_wp.get("lockVersion", 0)
        except:
            lock_version = 0

        # Prepare payload with null parent link
        payload = {"lockVersion": lock_version, "_links": {"parent": None}}

        return await self._request(
            "PATCH", f"/work_packages/{work_package_id}", payload
        )

    async def list_work_package_children(
        self, parent_id: int, include_descendants: bool = False
    ) -> Dict:
        """
        List all child work packages of a parent.

        Args:
            parent_id: The parent work package ID
            include_descendants: If True, includes grandchildren and below

        Returns:
            Dict: API response containing child work packages
        """
        if include_descendants:
            # Use descendants filter to get all levels
            filters = json.dumps(
                [{"descendantsOf": {"operator": "=", "values": [str(parent_id)]}}]
            )
        else:
            # Use parent filter to get direct children only
            filters = json.dumps(
                [{"parent": {"operator": "=", "values": [str(parent_id)]}}]
            )

        endpoint = f"/work_packages?filters={quote(filters)}"
        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def create_work_package_relation(self, data: Dict) -> Dict:
        """
        Create a relationship between work packages.

        Args:
            data: Relation data including from_id, to_id, type, lag, description

        Returns:
            Dict: Created relation data
        """
        from_id = data.get("from_id")
        if not from_id:
            raise ValueError("from_id is required")

        # Prepare payload according to OpenProject API v3 spec
        payload = {"_links": {}}

        # Set required fields
        if "to_id" in data:
            payload["_links"]["to"] = {
                "href": f"/api/v3/work_packages/{data['to_id']}"
            }
        if "type" in data:
            payload["type"] = data["type"]
        if "lag" in data:
            payload["lag"] = data["lag"]
        if "description" in data:
            payload["description"] = data["description"]

        # POST to /api/v3/work_packages/{id}/relations
        return await self._request(
            "POST", f"/work_packages/{from_id}/relations", payload
        )

    async def list_work_package_relations(self, filters: Optional[str] = None) -> Dict:
        """
        List work package relations.

        Args:
            filters: Optional JSON-encoded filter string

        Returns:
            Dict: API response containing relations
        """
        endpoint = "/relations"
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

    async def update_work_package_relation(self, relation_id: int, data: Dict) -> Dict:
        """
        Update an existing work package relation.

        Args:
            relation_id: The relation ID
            data: Update data including fields to modify

        Returns:
            Dict: Updated relation data
        """
        # First get current relation to get lock version if needed
        try:
            current_relation = await self.get_work_package_relation(relation_id)
            lock_version = current_relation.get("lockVersion", 0)
        except:
            lock_version = 0

        # Prepare payload with lock version
        payload = {"lockVersion": lock_version}

        # Add fields to update
        if "relation_type" in data:
            payload["type"] = data["relation_type"]
        if "lag" in data:
            payload["lag"] = data["lag"]
        if "description" in data:
            payload["description"] = data["description"]

        return await self._request("PATCH", f"/relations/{relation_id}", payload)

    async def delete_work_package_relation(self, relation_id: int) -> bool:
        """
        Delete a work package relation.

        Args:
            relation_id: The relation ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/relations/{relation_id}")
        return True

    async def get_work_package_relation(self, relation_id: int) -> Dict:
        """
        Retrieve a specific work package relation by ID.

        Args:
            relation_id: The relation ID

        Returns:
            Dict: Relation data
        """
        return await self._request("GET", f"/relations/{relation_id}")
