"""Live integration smoke test for the flattened work-package tools.

Skipped by default. It exercises the real flattened payload-building end to end
(create -> read-back -> update(status) -> delete) against a live OpenProject
instance, so the change is covered beyond signatures/imports. It cleans up the
work package it creates.

There is intentionally no standalone ``get_work_package`` tool in this server, so
the read-back uses ``search_work_packages`` (which matches by subject or ID). The
tool imports are at module top so a missing/renamed tool fails collection even
when this test is skipped.

Enable by pointing at a disposable test project with real credentials:

    OPENPROJECT_SMOKE=1 \\
    OPENPROJECT_URL=https://your.instance \\
    OPENPROJECT_API_KEY=... \\
    OPENPROJECT_TEST_PROJECT_ID=458 \\
    OPENPROJECT_TEST_TYPE_ID=1 \\
    OPENPROJECT_TEST_STATUS_ID=... \\  # optional; exercises the status update
    uv run pytest tests/test_integration_smoke.py -v
"""

import os
import re

import pytest

from src.tools.work_packages import (
    create_work_package,
    update_work_package,
    search_work_packages,
    delete_work_package,
)

SMOKE = os.getenv("OPENPROJECT_SMOKE") == "1"
PROJECT_ID = os.getenv("OPENPROJECT_TEST_PROJECT_ID")
TYPE_ID = os.getenv("OPENPROJECT_TEST_TYPE_ID")
STATUS_ID = os.getenv("OPENPROJECT_TEST_STATUS_ID")

pytestmark = pytest.mark.skipif(
    not (SMOKE and PROJECT_ID and TYPE_ID),
    reason=(
        "live smoke test disabled; set OPENPROJECT_SMOKE=1 + "
        "OPENPROJECT_TEST_PROJECT_ID + OPENPROJECT_TEST_TYPE_ID (and real creds)"
    ),
)


def _wp_id(text: str) -> int:
    match = re.search(r"#(\d+)", text)
    assert match, f"could not parse work package id from: {text!r}"
    return int(match.group(1))


async def test_work_package_crud_roundtrip():
    # @mcp.tool wraps the coroutine in a FunctionTool; the callable is at `.fn`.
    create = create_work_package.fn
    update = update_work_package.fn
    search = search_work_packages.fn
    delete = delete_work_package.fn

    created = await create(
        project_id=int(PROJECT_ID),
        subject="[smoke] flattened create/update payload",
        type_id=int(TYPE_ID),
        description="Temporary work package from the integration smoke test.",
    )
    assert "created successfully" in created.lower(), created
    wp_id = _wp_id(created)

    try:
        # No standalone get_work_package tool exists; read back via search by id.
        found = await search(query=str(wp_id), project_id=int(PROJECT_ID))
        assert str(wp_id) in found, found

        kwargs = {"work_package_id": wp_id, "subject": "[smoke] updated subject"}
        if STATUS_ID:
            kwargs["status_id"] = int(STATUS_ID)
        updated = await update(**kwargs)
        assert "updated successfully" in updated.lower(), updated
    finally:
        deleted = await delete(wp_id)
        assert "deleted successfully" in deleted.lower(), deleted
