"""Tests for MCP prompts (src.tools.prompts)."""

import pytest
from fastmcp import Client

import src.server

PROMPTS = ["plan_work_package", "summarize_work_package"]


async def _prompt_text(name: str, arguments: dict) -> str:
    async with Client(src.server.mcp) as client:
        result = await client.get_prompt(name, arguments)
    assert result.messages[0].role == "user"
    return result.messages[0].content.text


async def test_prompts_are_registered():
    async with Client(src.server.mcp) as client:
        prompts = await client.list_prompts()

    by_name = {p.name: p for p in prompts}
    for name in PROMPTS:
        assert name in by_name
        assert [a.name for a in by_name[name].arguments] == ["work_package_id"]
        assert by_name[name].arguments[0].required


@pytest.mark.parametrize("name", PROMPTS)
async def test_prompt_instructs_to_fetch_context_first(name):
    text = await _prompt_text(name, {"work_package_id": 123})

    assert "get_work_package_context" in text
    assert "123" in text
    assert "get_attachment" in text
    assert text.index("get_work_package_context") < text.index("list_work_package_code_links")


async def test_plan_prompt_sections():
    text = await _prompt_text("plan_work_package", {"work_package_id": 7})

    for section in ("Kroki implementacji", "Pytania otwarte", "Ryzyka", "Kryteria akceptacji"):
        assert section in text


async def test_summary_prompt_sections():
    text = await _prompt_text("summarize_work_package", {"work_package_id": 7})

    for section in ("Cel", "Stan", "Ostatnie decyzje", "Blokery"):
        assert section in text


async def test_prompt_accepts_string_argument():
    text = await _prompt_text("plan_work_package", {"work_package_id": "456"})

    assert "#456" in text
