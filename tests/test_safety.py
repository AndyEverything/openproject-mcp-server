"""Tests for read-only mode (src.utils.safety + src.server)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.server import mcp
from src.utils.safety import WRITE_PREFIXES, WRITE_TOOLS, is_read_only_enabled

REPO_ROOT = Path(__file__).resolve().parent.parent

LIST_TOOLS_SCRIPT = (
    "import asyncio, json, logging\n"
    "logging.disable(logging.CRITICAL)\n"
    "from src.server import mcp\n"
    "print(json.dumps(sorted(asyncio.run(mcp.get_tools()).keys())))\n"
)


async def registered_tool_names():
    return set((await mcp.get_tools()).keys())


def tool_names_in_subprocess(extra_env):
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("OPENPROJECT_READ_ONLY",)
    }
    env.update(
        {
            "OPENPROJECT_URL": "https://op.example.test",
            "OPENPROJECT_API_KEY": "test-key",
            "PYTHONPATH": str(REPO_ROOT),
            **extra_env,
        }
    )
    completed = subprocess.run(
        [sys.executable, "-c", LIST_TOOLS_SCRIPT],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    return set(json.loads(completed.stdout.strip().splitlines()[-1]))


async def test_every_write_prefixed_tool_is_classified():
    unclassified = sorted(
        name
        for name in await registered_tool_names()
        if name.startswith(WRITE_PREFIXES) and name not in WRITE_TOOLS
    )

    assert unclassified == [], f"Add these tools to WRITE_TOOLS: {unclassified}"


async def test_every_write_tool_is_registered():
    missing = sorted(WRITE_TOOLS - await registered_tool_names())

    assert missing == [], f"WRITE_TOOLS contains unknown tools (typo?): {missing}"


def test_read_only_mode_removes_write_tools():
    names = tool_names_in_subprocess({"OPENPROJECT_READ_ONLY": "true"})

    for write_tool in ("delete_project", "create_work_package", "add_work_package_comment"):
        assert write_tool not in names
    assert names.isdisjoint(WRITE_TOOLS)
    assert "list_projects" in names


def test_default_mode_keeps_write_tools():
    names = tool_names_in_subprocess({})

    assert "delete_project" in names
    assert "list_projects" in names


@pytest.mark.parametrize(
    "value, expected",
    [
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("YES", True),
        (" true ", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("", False),
        (None, False),
    ],
)
def test_is_read_only_enabled(value, expected):
    env = {} if value is None else {"OPENPROJECT_READ_ONLY": value}

    assert is_read_only_enabled(env) is expected


def test_is_read_only_enabled_reads_os_environ(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_READ_ONLY", "yes")

    assert is_read_only_enabled() is True
