"""Work package context tools (get_work_package, context, allowed statuses, resource)."""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from src.server import mcp, get_client
from src.utils.activities import activities_to_markdown, build_activities
from src.utils.custom_fields import extract_custom_fields
from src.utils.rendering import (
    VALID_FORMATS,
    extract_id,
    format_api_error,
    raise_fatal,
    render,
    section_error,
)

DESCRIPTION_IMAGE = re.compile(r"/api/v3/attachments/(\d+)/content")
IMAGE_HINT = "Pobierz je narzędziem get_attachment(attachment_id=<ID>)."


# ---------------------------------------------------------------------------
# Buildery modelu widoku
# ---------------------------------------------------------------------------


def _format_error(format: str) -> Optional[str]:
    """Error text for an unsupported format (checked before any API call)."""
    if (format or "").strip().lower() in VALID_FORMATS:
        return None
    return render(None, format, str)


def _link(wp: Dict, key: str) -> Dict:
    link = (wp.get("_links") or {}).get(key)
    return link if isinstance(link, dict) else {}


def _link_title(wp: Dict, key: str) -> Optional[str]:
    """Title of `_links.<key>` (or name of `_embedded.<key>`); None when unset."""
    link = _link(wp, key)
    if link.get("href") and link.get("title"):
        return str(link["title"])
    embedded = (wp.get("_embedded") or {}).get(key)
    if isinstance(embedded, dict) and embedded.get("name"):
        return str(embedded["name"])
    return None


def _ref(wp: Dict, key: str, title_field: str = "subject") -> Optional[Dict[str, Any]]:
    """{"id", title_field} of a linked resource; None when the link is empty."""
    link = _link(wp, key)
    ref_id = extract_id(link.get("href"))
    if ref_id is None:
        return None
    return {"id": ref_id, title_field: link.get("title")}


def _raw_text(value: Any) -> str:
    raw = value.get("raw") if isinstance(value, dict) else value
    return raw if isinstance(raw, str) else ""


def work_package_url(client, wp_id: Any) -> str:
    return f"{client.base_url}/work_packages/{wp_id}"


def details_from_work_package(client, wp: Dict) -> Dict[str, Any]:
    """Details view model of a raw HAL work package (custom_fields filled separately)."""
    status = _ref(wp, "status", "name")
    return {
        "id": wp.get("id"),
        "subject": wp.get("subject"),
        "type": _link_title(wp, "type"),
        "status": _link_title(wp, "status"),
        "status_id": status["id"] if status else None,
        "priority": _link_title(wp, "priority"),
        "project": _link_title(wp, "project"),
        "project_id": extract_id(_link(wp, "project").get("href")),
        "assignee": _link_title(wp, "assignee"),
        "responsible": _link_title(wp, "responsible"),
        "author": _link_title(wp, "author"),
        "version": _link_title(wp, "version"),
        "start_date": wp.get("startDate"),
        "due_date": wp.get("dueDate"),
        "percentage_done": wp.get("percentageDone"),
        "created_at": wp.get("createdAt"),
        "updated_at": wp.get("updatedAt"),
        "parent": _ref(wp, "parent"),
        "description": _raw_text(wp.get("description")),
        "custom_fields": [],
        "lock_version": wp.get("lockVersion"),
        "url": work_package_url(client, wp.get("id")),
    }


async def load_custom_fields(client, wp: Dict) -> List[Dict[str, str]]:
    """Custom fields of a work package read via its project/type schema."""
    project_id = extract_id(_link(wp, "project").get("href"))
    type_id = extract_id(_link(wp, "type").get("href"))
    if project_id is None or type_id is None:
        return []
    schema = await client.get_work_package_schema(project_id, type_id)
    return extract_custom_fields(wp, schema)


async def build_work_package_details(client, wp_id: int) -> Dict[str, Any]:
    """Details of a work package with custom fields; schema errors become a section error.

    Raises the client error when the work package itself cannot be fetched.
    """
    wp = await client.get_work_package(wp_id)
    details = details_from_work_package(client, wp)
    try:
        details["custom_fields"] = await load_custom_fields(client, wp)
    except Exception as e:
        details["custom_fields"] = section_error(e)
    return details


def attachments_from_collection(collection: Dict) -> List[Dict[str, Any]]:
    elements = ((collection or {}).get("_embedded") or {}).get("elements") or []
    return [
        {
            "id": item.get("id"),
            "name": item.get("fileName"),
            "content_type": item.get("contentType"),
            "size": item.get("fileSize"),
            "created_at": item.get("createdAt"),
        }
        for item in elements
    ]


def _relation_end(relation: Dict, key: str) -> Dict[str, Any]:
    link = ((relation.get("_links") or {}).get(key)) or {}
    embedded = ((relation.get("_embedded") or {}).get(key)) or {}
    return {
        "id": embedded.get("id") or extract_id(link.get("href")),
        "subject": embedded.get("subject") or link.get("title"),
    }


def relations_from_collection(collection: Dict, wp_id: int) -> List[Dict[str, Any]]:
    """Relations seen from `wp_id`: type (reverseType when it is the target) + the other work package."""
    elements = ((collection or {}).get("_embedded") or {}).get("elements") or []
    result: List[Dict[str, Any]] = []
    for relation in elements:
        source = _relation_end(relation, "from")
        target = _relation_end(relation, "to")
        is_source = source["id"] == wp_id
        result.append(
            {
                "id": relation.get("id"),
                "type": relation.get("type") if is_source else relation.get("reverseType") or relation.get("type"),
                "work_package": target if is_source else source,
                "description": relation.get("description") or None,
            }
        )
    return result


def children_from_collection(collection: Dict) -> List[Dict[str, Any]]:
    elements = ((collection or {}).get("_embedded") or {}).get("elements") or []
    return [
        {
            "id": child.get("id"),
            "subject": child.get("subject"),
            "type": _link_title(child, "type"),
            "status": _link_title(child, "status"),
        }
        for child in elements
    ]


def description_image_ids(description: str) -> List[int]:
    """Unique attachment IDs referenced as /api/v3/attachments/{id}/content (in order)."""
    return list(dict.fromkeys(int(match) for match in DESCRIPTION_IMAGE.findall(description or "")))


async def _fetch_comments(client, wp_id: int) -> List[Dict[str, Any]]:
    return build_activities(await client.get_work_package_activities(wp_id), comments_only=True)


async def _fetch_attachments(client, wp_id: int) -> List[Dict[str, Any]]:
    return attachments_from_collection(await client.get_work_package_attachments(wp_id))


async def _fetch_relations(client, wp_id: int) -> List[Dict[str, Any]]:
    filters = json.dumps([{"involved": {"operator": "=", "values": [str(wp_id)]}}])
    return relations_from_collection(await client.list_work_package_relations(filters), wp_id)


async def _fetch_children(client, wp_id: int) -> List[Dict[str, Any]]:
    return children_from_collection(await client.list_work_package_children(wp_id))


async def build_work_package_context(
    client,
    wp_id: int,
    include_comments: bool = True,
    include_attachments: bool = True,
    include_relations: bool = True,
    include_hierarchy: bool = True,
) -> Dict[str, Any]:
    """Aggregated context of a work package; failing sections carry {"error", "status"}.

    Raises the client error when the work package itself cannot be fetched.
    Disabled sections are omitted and trigger no API call.
    """
    wp = await client.get_work_package(wp_id)
    details = details_from_work_package(client, wp)

    tasks = {"custom_fields": load_custom_fields(client, wp)}
    if include_comments:
        tasks["comments"] = _fetch_comments(client, wp_id)
    if include_attachments:
        tasks["attachments"] = _fetch_attachments(client, wp_id)
    if include_relations:
        tasks["relations"] = _fetch_relations(client, wp_id)
    if include_hierarchy:
        tasks["children"] = _fetch_children(client, wp_id)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    raise_fatal(results)
    sections = {
        name: section_error(value) if isinstance(value, Exception) else value
        for name, value in zip(tasks.keys(), results)
    }

    details["custom_fields"] = sections.pop("custom_fields")
    context: Dict[str, Any] = {"details": details}
    for name in ("comments", "attachments", "relations"):
        if name in sections:
            context[name] = sections[name]
    if "children" in sections:
        context["hierarchy"] = {"parent": details["parent"], "children": sections["children"]}

    context["description_images"] = {
        "attachment_ids": description_image_ids(details["description"]),
        "hint": IMAGE_HINT,
    }
    return context


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

DETAIL_FIELDS = (
    ("project", "Projekt"),
    ("assignee", "Przypisany"),
    ("responsible", "Odpowiedzialny"),
    ("author", "Autor"),
    ("version", "Wersja"),
    ("start_date", "Data rozpoczęcia"),
    ("due_date", "Termin"),
    ("created_at", "Utworzono"),
    ("updated_at", "Zaktualizowano"),
)


def _is_error(section: Any) -> bool:
    return isinstance(section, dict) and "error" in section


def _error_line(section: Dict) -> str:
    return f"⚠️ {section['error']}"


def details_to_markdown(details: Dict[str, Any], level: int = 1) -> str:
    h = "#" * level
    lines = [f"{h} 📋 Work Package #{details.get('id')}: {details.get('subject') or ''}".rstrip(), ""]

    summary = [
        f"**{label}:** {details[key]}"
        for key, label in (("type", "Typ"), ("status", "Status"), ("priority", "Priorytet"))
        if details.get(key)
    ]
    if summary:
        lines += [" | ".join(summary), ""]

    for key, label in DETAIL_FIELDS:
        if details.get(key):
            lines.append(f"- **{label}:** {details[key]}")
    if details.get("percentage_done") is not None:
        lines.append(f"- **Postęp:** {details['percentage_done']}%")
    parent = details.get("parent")
    if parent:
        lines.append(f"- **Rodzic:** #{parent['id']} {parent.get('subject') or ''}".rstrip())
    if details.get("lock_version") is not None:
        lines.append(f"- **lockVersion:** {details['lock_version']}")
    lines.append(f"- **URL:** {details.get('url')}")

    custom_fields = details.get("custom_fields")
    lines += ["", f"{h}# 🏷️ Pola własne"]
    if _is_error(custom_fields):
        lines.append(_error_line(custom_fields))
    elif custom_fields:
        lines += [f"- **{field['name']}:** {field['value']}" for field in custom_fields]
    else:
        lines.append("Brak wypełnionych pól własnych.")

    lines += ["", f"{h}# 📝 Opis", details.get("description") or "_Brak opisu._"]
    return "\n".join(lines)


def _attachments_markdown(attachments: List[Dict[str, Any]]) -> List[str]:
    if not attachments:
        return ["Brak załączników."]
    return [
        f"- **#{item['id']}** {item.get('name')} ({item.get('content_type') or '?'}, {item.get('size') or 0} B)"
        for item in attachments
    ]


def _relations_markdown(relations: List[Dict[str, Any]]) -> List[str]:
    if not relations:
        return ["Brak relacji."]
    lines = []
    for relation in relations:
        other = relation.get("work_package") or {}
        line = f"- **{relation.get('type')}** → #{other.get('id')} {other.get('subject') or ''}".rstrip()
        if relation.get("description"):
            line += f" — {relation['description']}"
        lines.append(line)
    return lines


def _hierarchy_markdown(hierarchy: Dict[str, Any]) -> List[str]:
    parent = hierarchy.get("parent")
    lines = [f"- **Rodzic:** #{parent['id']} {parent.get('subject') or ''}".rstrip() if parent else "- **Rodzic:** brak"]
    children = hierarchy.get("children")
    if _is_error(children):
        lines.append(f"- **Dzieci:** {_error_line(children)}")
    elif children:
        lines.append(f"- **Dzieci ({len(children)}):**")
        lines += [
            f"  - #{child['id']} {child.get('subject') or ''} [{child.get('status') or '?'}]"
            for child in children
        ]
    else:
        lines.append("- **Dzieci:** brak")
    return lines


def _section(title: str, section: Any, body_fn) -> List[str]:
    count = f" ({len(section)})" if isinstance(section, list) else ""
    lines = ["", f"## {title}{count}"]
    lines += [_error_line(section)] if _is_error(section) else body_fn(section)
    return lines


def context_to_markdown(data: Dict[str, Any]) -> str:
    """Markdown of the aggregated context (used by the tool and the MCP resource)."""
    lines = [details_to_markdown(data["details"], level=1)]

    if "comments" in data:
        lines += _section(
            "💬 Komentarze",
            data["comments"],
            lambda items: [activities_to_markdown(items, "Brak komentarzy.")],
        )
    if "attachments" in data:
        lines += _section("📎 Załączniki", data["attachments"], _attachments_markdown)
    if "relations" in data:
        lines += _section("🔗 Relacje", data["relations"], _relations_markdown)
    if "hierarchy" in data:
        lines += _section("🌳 Hierarchia", data["hierarchy"], _hierarchy_markdown)

    image_ids = data.get("description_images", {}).get("attachment_ids") or []
    if image_ids:
        lines += [
            "",
            f"## 🖼️ Obrazy w opisie ({len(image_ids)})",
            "Załączniki: " + ", ".join(f"#{image_id}" for image_id in image_ids),
            IMAGE_HINT,
        ]
    return "\n".join(lines)


def allowed_statuses_to_markdown(data: Dict[str, Any]) -> str:
    lines = [f"✅ **Dozwolone statusy dla zadania #{data['work_package_id']} ({len(data['allowed_statuses'])}):**", ""]
    current = data.get("current_status") or {}
    if current.get("name"):
        lines += [f"Bieżący status: **{current['name']}** (ID {current.get('id')})", ""]
    if not data["allowed_statuses"]:
        lines.append("Brak dozwolonych przejść.")
    for status in data["allowed_statuses"]:
        marker = " ← bieżący" if status.get("current") else ""
        lines.append(f"- **{status.get('name')}** (ID {status.get('id')}){marker}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Narzędzia i zasób
# ---------------------------------------------------------------------------


@mcp.tool
async def get_work_package(work_package_id: int, format: str = "markdown") -> str:
    """Get full details of a single work package.

    Returns subject, type, status, priority, project, assignee, responsible, author,
    version, dates, progress, parent, custom fields (by their names) and the complete,
    untruncated description (raw markdown).

    Args:
        work_package_id: Work package ID
        format: "markdown" (default) or "json"
    """
    error = _format_error(format)
    if error:
        return error
    try:
        details = await build_work_package_details(get_client(), work_package_id)
    except Exception as e:
        return format_api_error(e)
    return render(details, format, details_to_markdown)


@mcp.tool
async def get_work_package_context(
    work_package_id: int,
    include_comments: bool = True,
    include_attachments: bool = True,
    include_relations: bool = True,
    include_hierarchy: bool = True,
    format: str = "markdown",
) -> str:
    """Get the complete context of a work package in one call.

    Sections: details with custom fields, comments (full text), attachments list
    (metadata only), relations, hierarchy (parent and children) and IDs of images
    referenced in the description. A failing section does not break the others.
    Use this before planning or implementing a work package.

    Args:
        work_package_id: Work package ID
        include_comments: Include comments (default True)
        include_attachments: Include attachment list (default True)
        include_relations: Include relations (default True)
        include_hierarchy: Include parent and children (default True)
        format: "markdown" (default) or "json"
    """
    error = _format_error(format)
    if error:
        return error
    try:
        data = await build_work_package_context(
            get_client(),
            work_package_id,
            include_comments=include_comments,
            include_attachments=include_attachments,
            include_relations=include_relations,
            include_hierarchy=include_hierarchy,
        )
    except Exception as e:
        return format_api_error(e)
    return render(data, format, context_to_markdown)


def _allowed_values(form: Dict) -> List[Dict]:
    status_schema = (((form or {}).get("_embedded") or {}).get("schema") or {}).get("status") or {}
    links = (status_schema.get("_links") or {}).get("allowedValues")
    if links:
        return [{"id": extract_id(link.get("href")), "name": link.get("title")} for link in links]
    embedded = (status_schema.get("_embedded") or {}).get("allowedValues") or []
    return [{"id": item.get("id"), "name": item.get("name")} for item in embedded]


@mcp.tool
async def get_allowed_statuses(work_package_id: int, format: str = "markdown") -> str:
    """List statuses the current user may set on a work package (workflow transitions).

    Read-only: uses the work package form endpoint, which validates without saving.

    Args:
        work_package_id: Work package ID
        format: "markdown" (default) or "json"
    """
    error = _format_error(format)
    if error:
        return error
    try:
        client = get_client()
        wp = await client.get_work_package(work_package_id)
        form = await client.get_work_package_form(work_package_id, wp.get("lockVersion"))
    except Exception as e:
        return format_api_error(e)

    current = _ref(wp, "status", "name")
    current_id = current["id"] if current else None
    statuses = [
        {**status, "current": status["id"] is not None and status["id"] == current_id}
        for status in _allowed_values(form)
    ]
    data = {
        "work_package_id": work_package_id,
        "lock_version": wp.get("lockVersion"),
        "current_status": current,
        "allowed_statuses": statuses,
    }
    return render(data, format, allowed_statuses_to_markdown)


@mcp.resource(
    "openproject://work-packages/{work_package_id}",
    name="work_package_context",
    description="Aggregated context of a work package (details, custom fields, comments, attachments, relations, hierarchy) as markdown.",
    mime_type="text/markdown",
)
async def work_package_resource(work_package_id: int) -> str:
    try:
        data = await build_work_package_context(get_client(), int(work_package_id))
    except Exception as e:
        return format_api_error(e)
    return context_to_markdown(data)
