#!/usr/bin/env python3
"""
Test Data Setup Script for OpenProject

This script sets up test data in OpenProject for E2E testing.
It creates projects, users, and other necessary data.
"""

import os
import sys
import time
import requests
import base64
from typing import Dict, List


class OpenProjectSetup:
    """Setup class for OpenProject test data"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Basic {self._encode_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _encode_api_key(self) -> str:
        """Encode API key for Basic Auth"""
        credentials = f"apikey:{self.api_key}"
        return base64.b64encode(credentials.encode()).decode()

    def wait_for_ready(self, timeout: int = 300):
        """Wait for OpenProject to be ready"""
        print("Waiting for OpenProject to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/api/v3", headers=self.headers)
                response.raise_for_status()
                print("OpenProject is ready!")
                return
            except Exception as e:
                print(f"OpenProject not ready yet: {e}")
                time.sleep(10)

        raise Exception(f"OpenProject not ready after {timeout} seconds")

    def create_test_project(self) -> Dict:
        """Create a test project"""
        data = {
            "name": "E2E Test Project",
            "description": {"raw": "Test project for end-to-end testing"},
            "public": True,
        }
        response = requests.post(
            f"{self.base_url}/api/v3/projects", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def create_test_user(self) -> Dict:
        """Create a test user"""
        data = {
            "login": "test@example.com",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "password": "test123",
            "status": "active",
        }
        response = requests.post(
            f"{self.base_url}/api/v3/users", headers=self.headers, json=data
        )
        response.raise_for_status()
        return response.json()

    def create_test_work_package(self, project_id: int, type_id: int) -> Dict:
        """Create a test work package"""
        # First get the form
        form_data = {
            "_links": {
                "project": {"href": f"/api/v3/projects/{project_id}"},
                "type": {"href": f"/api/v3/types/{type_id}"},
            },
            "subject": "Test Work Package",
        }

        form_response = requests.post(
            f"{self.base_url}/api/v3/work_packages/form",
            headers=self.headers,
            json=form_data,
        )
        form_response.raise_for_status()
        form = form_response.json()

        # Create the work package
        payload = form.get("payload", form_data)
        payload["lockVersion"] = form.get("lockVersion", 0)

        response = requests.post(
            f"{self.base_url}/api/v3/work_packages", headers=self.headers, json=payload
        )
        response.raise_for_status()
        return response.json()

    def setup_test_data(self):
        """Set up all test data"""
        print("Setting up test data...")

        # Wait for OpenProject to be ready
        self.wait_for_ready()

        # Create test project
        project = self.create_test_project()
        print(f"Created test project: {project['id']} - {project['name']}")

        # Create test user
        user = self.create_test_user()
        print(f"Created test user: {user['id']} - {user['name']}")

        # Get work package types
        types_response = requests.get(
            f"{self.base_url}/api/v3/types", headers=self.headers
        )
        types_response.raise_for_status()
        types = types_response.json().get("_embedded", {}).get("elements", [])

        if types:
            # Create a test work package
            wp = self.create_test_work_package(project["id"], types[0]["id"])
            print(f"Created test work package: {wp['id']} - {wp['subject']}")

        print("Test data setup completed!")

        return {"project": project, "user": user, "types": types}


def main():
    """Main setup function"""
    base_url = os.getenv("OPENPROJECT_URL", "http://localhost:8080")
    api_key = os.getenv("OPENPROJECT_API_KEY", "test-api-key")

    setup = OpenProjectSetup(base_url, api_key)
    setup.setup_test_data()


if __name__ == "__main__":
    main()
