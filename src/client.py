"""
OpenProject API Client

A comprehensive async client for OpenProject API v3 with proxy support.
"""

import os
import json
import logging
import mimetypes
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import aiohttp
from urllib.parse import quote, urljoin, urlsplit
import base64
import ssl

from src.utils.cache import TTLCache

# Configure logging
logger = logging.getLogger(__name__)

# Version information
__version__ = "2.0.0"

DEFAULT_TIMEOUT_SECONDS = 30
DOWNLOAD_TIMEOUT_SECONDS = 120
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 3
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
DOWNLOAD_CHUNK_SIZE = 64 * 1024


class OpenProjectAPIError(Exception):
    """HTTP error returned by the OpenProject API (status >= 400)."""

    def __init__(self, status: int, body: str, message: Optional[str] = None):
        self.status = status
        self.body = body
        super().__init__(message if message is not None else f"API Error {status}: {body}")


class DownloadTooLargeError(Exception):
    """Raised when a binary download exceeds the size limit."""


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
        self.cache = TTLCache()

        logger.info(f"OpenProject Client initialized for: {self.base_url}")
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")

    def _encode_api_key(self) -> str:
        """Encode API key for Basic Auth"""
        credentials = f"apikey:{self.api_key}"
        return base64.b64encode(credentials.encode()).decode()

    def _create_session(
        self, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    ) -> aiohttp.ClientSession:
        """Create an aiohttp session with shared SSL and timeout configuration."""
        ssl_context = ssl.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        return aiohttp.ClientSession(connector=connector, timeout=timeout)

    def _proxy_params(self) -> Dict[str, str]:
        """Request kwargs with the proxy, if configured."""
        return {"proxy": self.proxy} if self.proxy else {}

    def _api_url(self, endpoint: str) -> str:
        """Build an absolute URL from an API endpoint, API href or absolute URL."""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        if endpoint.startswith("/api/v3"):
            return f"{self.base_url}{endpoint}"
        return f"{self.base_url}/api/v3{endpoint}"

    def _is_same_origin(self, url: str) -> bool:
        """Whether the URL points to the configured OpenProject origin."""
        target = urlsplit(url)
        base = urlsplit(self.base_url)
        return (target.scheme.lower(), target.netloc.lower()) == (
            base.scheme.lower(),
            base.netloc.lower(),
        )

    async def _parse_json_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Parse a JSON response; raise OpenProjectAPIError for status >= 400."""
        response_text = await response.text()

        logger.debug(f"Response status: {response.status}")

        try:
            response_json = json.loads(response_text) if response_text else {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response_text[:200]}...")
            response_json = {}

        if response.status >= 400:
            raise OpenProjectAPIError(
                response.status,
                response_text,
                self._format_error_message(response.status, response_text),
            )

        return response_json

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
            OpenProjectAPIError: If the API responds with status >= 400
            Exception: On network errors
        """
        url = f"{self.base_url}/api/v3{endpoint}"

        logger.debug(f"API Request: {method} {url}")
        if data:
            logger.debug(f"Request body: {json.dumps(data, indent=2)}")

        async with self._create_session() as session:
            try:
                request_params = {
                    "method": method,
                    "url": url,
                    "headers": self.headers,
                    "json": data,
                    **self._proxy_params(),
                }

                async with session.request(**request_params) as response:
                    return await self._parse_json_response(response)

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {str(e)}")
                raise Exception(f"Network error accessing {url}: {str(e)}")

    async def _request_bytes(
        self, endpoint: str, max_bytes: int = MAX_DOWNLOAD_BYTES
    ) -> Tuple[bytes, str, Optional[str]]:
        """
        Download binary content (e.g. attachment content).

        Redirects are followed manually (max MAX_REDIRECTS); the Authorization
        header is sent only to the configured OpenProject origin.

        Args:
            endpoint: API endpoint ("/attachments/1/content"), API href
                ("/api/v3/...") or absolute URL
            max_bytes: Maximum number of bytes to download

        Returns:
            Tuple of (content, content_type without parameters, filename from
            Content-Disposition or None)

        Raises:
            OpenProjectAPIError: If the server responds with status >= 400
            DownloadTooLargeError: If the content exceeds max_bytes
        """
        url = self._api_url(endpoint)
        current_url = url

        async with self._create_session(DOWNLOAD_TIMEOUT_SECONDS) as session:
            try:
                for _ in range(MAX_REDIRECTS + 1):
                    headers = {
                        "Accept": "*/*",
                        "User-Agent": self.headers["User-Agent"],
                    }
                    # Klucz API tylko do własnej instancji (presigned URL-e S3 itp. bez auth)
                    if self._is_same_origin(current_url):
                        headers["Authorization"] = self.headers["Authorization"]

                    logger.debug(f"API Download: GET {current_url}")
                    async with session.get(
                        current_url,
                        headers=headers,
                        allow_redirects=False,
                        **self._proxy_params(),
                    ) as response:
                        if response.status in REDIRECT_STATUSES:
                            location = response.headers.get("Location")
                            if not location:
                                raise OpenProjectAPIError(
                                    response.status,
                                    "",
                                    f"API Error {response.status}: redirect without Location header",
                                )
                            current_url = urljoin(current_url, location)
                            continue

                        if response.status >= 400:
                            body = await response.text(errors="replace")
                            raise OpenProjectAPIError(
                                response.status,
                                body,
                                self._format_error_message(response.status, body),
                            )

                        content = await self._read_limited(response, max_bytes)
                        return (
                            content,
                            response.content_type,
                            self._content_disposition_filename(response),
                        )

                raise Exception(
                    f"Too many redirects (more than {MAX_REDIRECTS}) while downloading {url}"
                )

            except aiohttp.ClientError as e:
                logger.error(f"Network error: {str(e)}")
                raise Exception(f"Network error accessing {url}: {str(e)}")

    @staticmethod
    async def _read_limited(response: aiohttp.ClientResponse, max_bytes: int) -> bytes:
        """Read the response body in chunks, aborting once max_bytes is exceeded."""
        too_large_msg = (
            f"Download exceeds the size limit of {max_bytes} bytes "
            f"({max_bytes / (1024 * 1024):.1f} MB); download aborted"
        )
        if response.content_length is not None and response.content_length > max_bytes:
            raise DownloadTooLargeError(too_large_msg)

        buffer = bytearray()
        async for chunk in response.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
            buffer.extend(chunk)
            if len(buffer) > max_bytes:
                raise DownloadTooLargeError(too_large_msg)
        return bytes(buffer)

    @staticmethod
    def _content_disposition_filename(response: aiohttp.ClientResponse) -> Optional[str]:
        """Filename from the Content-Disposition header, if present."""
        try:
            disposition = response.content_disposition
        except Exception:
            return None
        return disposition.filename if disposition else None

    async def _request_multipart(
        self, endpoint: str, metadata: Dict, file_path: str
    ) -> Dict:
        """
        POST multipart/form-data with a JSON "metadata" part and a "file" part.

        Args:
            endpoint: API endpoint path
            metadata: Dict sent as the JSON "metadata" part
            file_path: Path of the file sent as the "file" part

        Returns:
            Dict: Response data from the API
        """
        url = f"{self.base_url}/api/v3{endpoint}"
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        with open(file_path, "rb") as file:
            file_content = file.read()

        form = aiohttp.FormData()
        form.add_field(
            "metadata", json.dumps(metadata), content_type="application/json"
        )
        form.add_field(
            "file", file_content, filename=file_name, content_type=content_type
        )
        # Content-Type z boundary ustawia aiohttp
        headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}

        logger.debug(f"API Multipart Request: POST {url} ({file_name})")

        async with self._create_session(DOWNLOAD_TIMEOUT_SECONDS) as session:
            try:
                async with session.post(
                    url, data=form, headers=headers, **self._proxy_params()
                ) as response:
                    return await self._parse_json_response(response)
            except aiohttp.ClientError as e:
                logger.error(f"Network error: {str(e)}")
                raise Exception(f"Network error accessing {url}: {str(e)}")

    @staticmethod
    def _ensure_elements(result: Dict) -> Dict:
        """Guarantee the `_embedded.elements` list in a collection response."""
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []
        return result

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
        Retrieve available work package types (cached per project, see TTLCache).

        Args:
            project_id: Optional project ID to filter types by

        Returns:
            Dict: API response containing types
        """
        return await self.cache.get_or_set(
            f"types:{project_id or 'all'}", lambda: self._fetch_types(project_id)
        )

    async def _fetch_types(self, project_id: Optional[int] = None) -> Dict:
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
        Retrieve available work package statuses (cached, see TTLCache).

        Returns:
            Dict: API response containing statuses
        """
        return await self.cache.get_or_set("statuses", self._fetch_statuses)

    async def _fetch_statuses(self) -> Dict:
        result = await self._request("GET", "/statuses")

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    async def get_priorities(self) -> Dict:
        """
        Retrieve available work package priorities (cached, see TTLCache).

        Returns:
            Dict: API response containing priorities
        """
        return await self.cache.get_or_set("priorities", self._fetch_priorities)

    async def _fetch_priorities(self) -> Dict:
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

    async def get_subprojects(self, parent_id: int) -> Dict:
        """
        Retrieve direct subprojects of a parent project.

        Args:
            parent_id: The parent project ID

        Returns:
            Dict: API response containing direct child projects
        """
        # Use parent_id filter for direct children only
        filters = json.dumps([{
            "parent_id": {"operator": "=", "values": [str(parent_id)]}
        }])
        return await self.get_projects(filters)

    async def validate_parent_project(self, parent_id: int, child_id: Optional[int] = None) -> bool:
        """
        Validate if a project can be a parent.
        Uses the available_parent_projects endpoint.

        Args:
            parent_id: The parent project ID to validate
            child_id: Optional child project ID (for existing projects)

        Returns:
            bool: True if valid parent
        """
        endpoint = "/projects/available_parent_projects"
        if child_id:
            endpoint += f"?of={child_id}"

        result = await self._request("GET", endpoint)
        candidates = result.get("_embedded", {}).get("elements", [])

        return any(p.get("id") == parent_id for p in candidates)

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
        self,
        parent_id: int,
        include_descendants: bool = False,
        offset: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict:
        """
        List all child work packages of a parent.

        Args:
            parent_id: The parent work package ID
            include_descendants: If True, includes grandchildren and below
            offset: Optional starting index for pagination
            page_size: Optional number of results per page

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

        # Build query parameters
        query_params = [f"filters={quote(filters)}"]
        if offset is not None:
            query_params.append(f"offset={offset}")
        if page_size is not None:
            query_params.append(f"pageSize={page_size}")

        endpoint = f"/work_packages?" + "&".join(query_params)
        result = await self._request("GET", endpoint)

        # Ensure proper response structure
        if "_embedded" not in result:
            result["_embedded"] = {"elements": []}
        elif "elements" not in result.get("_embedded", {}):
            result["_embedded"]["elements"] = []

        return result

    # Alias for backward compatibility and consistency with tool naming
    async def get_work_package_children(
        self,
        parent_id: int,
        include_descendants: bool = False,
        offset: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict:
        """Alias for list_work_package_children."""
        return await self.list_work_package_children(
            parent_id, include_descendants, offset, page_size
        )

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

    # ============================================================
    # News API Methods
    # ============================================================

    async def get_news(
        self,
        filters: Optional[str] = None,
        sort_by: Optional[str] = None,
        offset: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict:
        """
        Retrieve news entries with filtering and pagination.

        Args:
            filters: Optional JSON-encoded filter string (e.g., project_id filter)
            sort_by: Optional JSON-encoded sort criteria (e.g., [["created_at", "asc"]])
            offset: Optional starting index for pagination
            page_size: Optional number of results per page

        Returns:
            Dict: API response containing news entries
        """
        endpoint = "/news"

        # Build query parameters
        query_params = []
        if filters:
            encoded_filters = quote(filters)
            query_params.append(f"filters={encoded_filters}")
        if sort_by:
            encoded_sort = quote(sort_by)
            query_params.append(f"sortBy={encoded_sort}")
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

    async def get_news_item(self, news_id: int) -> Dict:
        """
        Retrieve a specific news entry by ID.

        Args:
            news_id: The news ID

        Returns:
            Dict: News entry data
        """
        return await self._request("GET", f"/news/{news_id}")

    async def create_news(self, data: Dict) -> Dict:
        """
        Create a new news entry.

        Args:
            data: News data including:
                - project (int): Project ID (required)
                - title (str): News headline (required)
                - summary (str): Short summary (required)
                - description (str): Main body content, supports markdown (required)

        Returns:
            Dict: Created news entry data
        """
        # Prepare payload
        payload = {}

        # Set required fields
        if "title" in data:
            payload["title"] = data["title"]
        if "summary" in data:
            payload["summary"] = data["summary"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}

        # Set project link (required)
        if "project" in data:
            payload["_links"] = {
                "project": {"href": f"/api/v3/projects/{data['project']}"}
            }

        return await self._request("POST", "/news", payload)

    async def update_news(self, news_id: int, data: Dict) -> Dict:
        """
        Update an existing news entry.

        Args:
            news_id: The news ID
            data: Update data including fields to modify:
                - title (str): New headline (optional)
                - summary (str): New summary (optional)
                - description (str): New content, supports markdown (optional)

        Returns:
            Dict: Updated news entry data
        """
        # First get current news to get lock version
        current_news = await self.get_news_item(news_id)

        # Prepare payload with lock version
        payload = {"lockVersion": current_news.get("lockVersion", 0)}

        # Add fields to update
        if "title" in data:
            payload["title"] = data["title"]
        if "summary" in data:
            payload["summary"] = data["summary"]
        if "description" in data:
            payload["description"] = {"raw": data["description"]}

        return await self._request("PATCH", f"/news/{news_id}", payload)

    async def delete_news(self, news_id: int) -> bool:
        """
        Delete a news entry.

        Args:
            news_id: The news ID

        Returns:
            bool: True if successful
        """
        await self._request("DELETE", f"/news/{news_id}")
        return True

    # ------------------------------------------------------------------
    # Agent context: current user, schema, attachments, watchers,
    # queries, notifications, versions, link collections
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_filters(filters: List[Dict]) -> str:
        """URL-encode an OpenProject filter list (same convention as get_memberships)."""
        return quote(json.dumps(filters))

    async def get_current_user(self) -> Dict:
        """Retrieve the authenticated user (GET /users/me, cached)."""
        return await self.cache.get_or_set(
            "users:me", lambda: self._request("GET", "/users/me")
        )

    async def get_work_package_schema(self, project_id: int, type_id: int) -> Dict:
        """Retrieve the work package schema for a project/type pair (cached)."""
        return await self.cache.get_or_set(
            f"schema:{project_id}-{type_id}",
            lambda: self._request(
                "GET", f"/work_packages/schemas/{project_id}-{type_id}"
            ),
        )

    async def get_work_package_attachments(self, work_package_id: int) -> Dict:
        """Retrieve the attachment collection of a work package."""
        result = await self._request(
            "GET", f"/work_packages/{work_package_id}/attachments"
        )
        return self._ensure_elements(result)

    async def get_attachment(self, attachment_id: int) -> Dict:
        """Retrieve attachment metadata (name, contentType, fileSize, ...)."""
        return await self._request("GET", f"/attachments/{attachment_id}")

    async def download_attachment(
        self, attachment_id: int
    ) -> Tuple[bytes, str, Optional[str]]:
        """Download attachment content; returns (bytes, content_type, filename)."""
        return await self._request_bytes(f"/attachments/{attachment_id}/content")

    async def upload_attachment(
        self, work_package_id: int, file_path: str, description: Optional[str] = None
    ) -> Dict:
        """Upload a file as a work package attachment (multipart POST)."""
        metadata: Dict[str, Any] = {"fileName": os.path.basename(file_path)}
        if description:
            metadata["description"] = {"raw": description}
        return await self._request_multipart(
            f"/work_packages/{work_package_id}/attachments", metadata, file_path
        )

    async def get_work_package_form(
        self, work_package_id: int, lock_version: int
    ) -> Dict:
        """Retrieve the work package form (validates only, does not save)."""
        return await self._request(
            "POST",
            f"/work_packages/{work_package_id}/form",
            {"lockVersion": lock_version},
        )

    async def get_watchers(self, work_package_id: int) -> Dict:
        """Retrieve watchers of a work package."""
        result = await self._request(
            "GET", f"/work_packages/{work_package_id}/watchers"
        )
        return self._ensure_elements(result)

    async def add_watcher(self, work_package_id: int, user_id: int) -> Dict:
        """Add a user as a watcher of a work package."""
        return await self._request(
            "POST",
            f"/work_packages/{work_package_id}/watchers",
            {"user": {"href": f"/api/v3/users/{user_id}"}},
        )

    async def remove_watcher(self, work_package_id: int, user_id: int) -> bool:
        """Remove a watcher from a work package."""
        await self._request(
            "DELETE", f"/work_packages/{work_package_id}/watchers/{user_id}"
        )
        return True

    async def get_queries(self, project_id: Optional[int] = None) -> Dict:
        """Retrieve saved queries (views), optionally filtered by project."""
        endpoint = "/queries"
        if project_id:
            filters = [{"project": {"operator": "=", "values": [str(project_id)]}}]
            endpoint += f"?filters={self._encode_filters(filters)}"
        result = await self._request("GET", endpoint)
        return self._ensure_elements(result)

    async def get_query(
        self, query_id: int, offset: int = 1, page_size: int = 20
    ) -> Dict:
        """Retrieve a saved query with its results (`_embedded.results`); offset is 1-based."""
        return await self._request(
            "GET", f"/queries/{query_id}?offset={offset}&pageSize={page_size}"
        )

    async def get_notifications(
        self,
        unread_only: bool = True,
        reason: Optional[str] = None,
        offset: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """Retrieve in-app notifications (read only; never marks them as read)."""
        filters: List[Dict] = []
        if unread_only:
            filters.append({"readIAN": {"operator": "=", "values": ["f"]}})
        if reason:
            filters.append({"reason": {"operator": "=", "values": [reason]}})

        query_params = []
        if filters:
            query_params.append(f"filters={self._encode_filters(filters)}")
        query_params.append(f"offset={offset}")
        query_params.append(f"pageSize={page_size}")

        result = await self._request(
            "GET", "/notifications?" + "&".join(query_params)
        )
        return self._ensure_elements(result)

    async def get_version(self, version_id: int) -> Dict:
        """Retrieve a specific version by ID."""
        return await self._request("GET", f"/versions/{version_id}")

    async def update_version(self, version_id: int, data: Dict) -> Dict:
        """Update a version (PATCH); `data` is sent as the request body as-is."""
        return await self._request("PATCH", f"/versions/{version_id}", data)

    async def get_work_package_link_collection(
        self, work_package_id: int, link_path: str
    ) -> Dict:
        """Retrieve a work package sub-collection, e.g. "github_pull_requests" or "file_links"."""
        result = await self._request(
            "GET", f"/work_packages/{work_package_id}/{link_path.lstrip('/')}"
        )
        return self._ensure_elements(result)
