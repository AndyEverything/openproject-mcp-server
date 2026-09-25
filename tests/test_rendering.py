"""Tests for src.utils.rendering."""

import json

import pytest

from src.client import OpenProjectAPIError
from src.utils.rendering import (
    VALID_FORMATS,
    extract_id,
    format_api_error,
    render,
    section_error,
)

DATA = {"id": 1, "subject": "Zażółć gęślą jaźń", "created": None}


def markdown(data):
    return f"# {data['subject']}"


def test_render_json_is_parseable_and_keeps_polish_characters():
    output = render(DATA, "json", markdown)

    assert json.loads(output) == DATA
    assert "Zażółć gęślą jaźń" in output


def test_render_json_serializes_unknown_types_with_str():
    from datetime import date

    assert json.loads(render({"d": date(2026, 1, 2)}, "json", markdown)) == {"d": "2026-01-02"}


@pytest.mark.parametrize("fmt", ["markdown", "MARKDOWN", " markdown ", None, ""])
def test_render_markdown_uses_markdown_fn(fmt):
    assert render(DATA, fmt, markdown) == "# Zażółć gęślą jaźń"


def test_render_unknown_format_returns_error_message():
    output = render(DATA, "xml", markdown)

    assert output.startswith("❌ Error:")
    assert "xml" in output
    for fmt in VALID_FORMATS:
        assert fmt in output


def test_format_api_error_includes_status_and_hal_message():
    error = OpenProjectAPIError(404, '{"message": "Nie znaleziono zasobu."}', "API Error 404: ...")

    assert format_api_error(error) == "❌ Błąd API 404: Nie znaleziono zasobu."


def test_format_api_error_with_plain_body():
    assert format_api_error(OpenProjectAPIError(500, "boom")) == "❌ Błąd API 500: boom"


def test_format_api_error_for_other_exceptions():
    assert format_api_error(ValueError("zła wartość")) == "❌ Error: zła wartość"


@pytest.mark.parametrize(
    "status, expected",
    [(403, "Brak dostępu (403)"), (404, "Niedostępne (404)")],
)
def test_section_error_friendly_texts(status, expected):
    assert section_error(OpenProjectAPIError(status, "x")) == {"error": expected, "status": status}


def test_section_error_other_status_and_exception():
    assert section_error(OpenProjectAPIError(500, "boom")) == {
        "error": "Błąd API 500: boom",
        "status": 500,
    }
    assert section_error(RuntimeError("timeout")) == {"error": "timeout", "status": None}


@pytest.mark.parametrize(
    "href, expected",
    [
        ("/api/v3/users/123", 123),
        ("/api/v3/work_packages/74986", 74986),
        ("https://op.example.test/api/v3/attachments/42/", 42),
        ("/api/v3/versions/9?x=1", 9),
        ("/api/v3/work_packages/schemas/118-7", None),
        ("/api/v3/users/me", None),
        (None, None),
        ("", None),
    ],
)
def test_extract_id(href, expected):
    assert extract_id(href) == expected
