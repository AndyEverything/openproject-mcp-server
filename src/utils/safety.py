"""Read-only mode: registry of tools that modify data in OpenProject.

Every new write tool MUST be added to WRITE_TOOLS (tests/test_safety.py enforces it
for names starting with one of WRITE_PREFIXES).
"""

import os
from typing import Mapping, Optional

READ_ONLY_ENV = "OPENPROJECT_READ_ONLY"
TRUTHY_VALUES = frozenset({"true", "1", "yes"})

WRITE_PREFIXES = (
    "create_",
    "update_",
    "delete_",
    "add_",
    "remove_",
    "set_",
    "assign_",
    "unassign_",
    "upload_",
)

WRITE_TOOLS: frozenset[str] = frozenset(
    {
        # work_packages
        "create_work_package",
        "update_work_package",
        "delete_work_package",
        "assign_work_package",
        "unassign_work_package",
        "add_work_package_comment",
        # projects
        "create_project",
        "add_subproject",
        "update_project",
        "delete_project",
        # memberships
        "create_membership",
        "update_membership",
        "delete_membership",
        # hierarchy
        "set_work_package_parent",
        "remove_work_package_parent",
        # relations
        "create_work_package_relation",
        "update_work_package_relation",
        "delete_work_package_relation",
        # time_entries
        "create_time_entry",
        "update_time_entry",
        "delete_time_entry",
        # versions
        "create_version",
        "update_version",
        # news
        "create_news",
        "update_news",
        "delete_news",
        # watchers
        "add_watcher",
        "remove_watcher",
        # attachments
        "upload_attachment",
    }
)


def is_read_only_enabled(env: Optional[Mapping[str, str]] = None) -> bool:
    """True when OPENPROJECT_READ_ONLY is "true", "1" or "yes" (case-insensitive)."""
    env = os.environ if env is None else env
    return (env.get(READ_ONLY_ENV) or "").strip().lower() in TRUTHY_VALUES
