"""Mapping of work package custom fields (customFieldN) to readable values via the schema."""

import re
from typing import Any, Dict, List, Optional

CUSTOM_FIELD_KEY = re.compile(r"^customField\d+$")

BOOLEAN_LABELS = {True: "Tak", False: "Nie"}
LINK_TYPES = ("CustomOption", "User", "Version")


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _link_titles(link: Any) -> Optional[str]:
    """Titles of a single link or a list of links (empty links skipped)."""
    links = link if isinstance(link, list) else [link]
    titles = [
        str(item.get("title"))
        for item in links
        if isinstance(item, dict) and item.get("href") and item.get("title")
    ]
    return ", ".join(titles) if titles else None


def _body_value(field_type: str, value: Any) -> Optional[str]:
    if field_type == "Formattable":
        raw = value.get("raw") if isinstance(value, dict) else value
        return raw if isinstance(raw, str) and raw.strip() else None
    if field_type == "Boolean":
        return BOOLEAN_LABELS.get(value) if isinstance(value, bool) else None
    if _is_empty(value):
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if not _is_empty(item)) or None
    return str(value)


def _is_link_type(field_type: str) -> bool:
    return field_type.lstrip("[]") in LINK_TYPES


def extract_custom_fields(work_package: Dict, schema: Dict) -> List[Dict[str, str]]:
    """Return non-empty custom fields of a work package in schema order.

    Each item: {"key": "customField40", "name": "...", "type": "CustomOption", "value": "..."}.
    Link-typed fields (CustomOption, User, Version and their "[]" lists) are read from
    `_links.customFieldN` titles; other types from the work package body.
    """
    links = work_package.get("_links", {}) or {}
    result: List[Dict[str, str]] = []

    for key, definition in schema.items():
        if not CUSTOM_FIELD_KEY.match(key) or not isinstance(definition, dict):
            continue

        field_type = str(definition.get("type", ""))
        if _is_link_type(field_type) or (key in links and key not in work_package):
            value = _link_titles(links.get(key))
        else:
            value = _body_value(field_type, work_package.get(key))

        if value is None:
            continue

        result.append(
            {
                "key": key,
                "name": definition.get("name") or key,
                "type": field_type,
                "value": value,
            }
        )

    return result
