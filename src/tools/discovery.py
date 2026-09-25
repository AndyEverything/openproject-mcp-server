"""Work discovery tools (my work packages, saved queries, notifications)."""

import json
from typing import Any, Dict, List, Optional

from src.server import get_client, mcp
from src.utils.formatting import format_error
from src.utils.rendering import (
    FORMAT_MARKDOWN,
    VALID_FORMATS,
    extract_id,
    format_api_error,
    render,
)

MAX_PAGE_SIZE = 100

# Przyczyny powiadomień w OpenProject API v3 (filtr `reason`)
NOTIFICATION_REASONS = (
    "mentioned",
    "assigned",
    "responsible",
    "watched",
    "subscribed",
    "commented",
    "created",
    "processed",
    "prioritized",
    "scheduled",
    "dateAlert",
    "shared",
    "reminder",
)


# ---------------------------------------------------------------------------
# Wspólne helpery (używane też przez src/tools/versions.py)
# ---------------------------------------------------------------------------


def invalid_format_error(format: Optional[str]) -> Optional[str]:
    """Error text for an unsupported `format`, None when valid (checked before any API call)."""
    if (format or FORMAT_MARKDOWN).strip().lower() in VALID_FORMATS:
        return None
    return render(None, format, lambda _: "")


def validate_pagination(offset: int, page_size: int) -> Optional[str]:
    """Error text for invalid 1-based page `offset` / `page_size`, None when valid."""
    if offset < 1:
        return format_error("offset must be >= 1 (page number, 1-based)")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        return format_error(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
    return None


def _ref(resource: Dict, key: str) -> Dict[str, Any]:
    """{"id", "name"} of a linked resource, from `_embedded` (name) or `_links` (title)."""
    embedded = (resource.get("_embedded") or {}).get(key) or {}
    link = (resource.get("_links") or {}).get(key) or {}
    name = embedded.get("name") or link.get("title")
    ref_id = embedded.get("id") or extract_id(link.get("href"))
    return {"id": ref_id, "name": name}


def build_work_package_item(wp: Dict) -> Dict[str, Any]:
    """Compact work package view model for lists."""
    return {
        "id": wp.get("id"),
        "subject": wp.get("subject"),
        "status": _ref(wp, "status")["name"],
        "type": _ref(wp, "type")["name"],
        "priority": _ref(wp, "priority")["name"],
        "assignee": _ref(wp, "assignee")["name"],
        "project": _ref(wp, "project"),
        "due_date": wp.get("dueDate") or wp.get("date"),
        "percentage_done": wp.get("percentageDone"),
    }


def build_pagination(total: Optional[int], count: int, offset: int, page_size: int) -> Dict[str, Any]:
    """Pagination block: 1-based page `offset`, `next_offset` None on the last page."""
    total = count if total is None else total
    has_next = offset * page_size < total
    return {
        "total": total,
        "count": count,
        "offset": offset,
        "page_size": page_size,
        "next_offset": offset + 1 if has_next else None,
    }


def build_work_package_page(
    collection: Dict, offset: int, page_size: int, **extra: Any
) -> Dict[str, Any]:
    """View model for a HAL work package collection page."""
    elements = (collection.get("_embedded") or {}).get("elements") or []
    return {
        **extra,
        "work_packages": [build_work_package_item(wp) for wp in elements],
        "pagination": build_pagination(collection.get("total"), len(elements), offset, page_size),
    }


def _work_package_line(item: Dict[str, Any]) -> str:
    details = [
        item.get("status"),
        item.get("type"),
        item.get("priority") and f"priorytet: {item['priority']}",
        (item.get("project") or {}).get("name") and f"projekt: {item['project']['name']}",
        item.get("assignee") and f"przypisany: {item['assignee']}",
        item.get("due_date") and f"termin: {item['due_date']}",
        item.get("percentage_done") is not None and f"{item['percentage_done']}%",
    ]
    detail_text = " | ".join(str(d) for d in details if d)
    line = f"- **#{item.get('id')}** {item.get('subject') or '(bez tematu)'}"
    return f"{line} — {detail_text}" if detail_text else line


def pagination_markdown(pagination: Dict[str, Any]) -> str:
    """Markdown footer with page info and the next `offset` hint."""
    text = (
        f"\n📄 **Strona {pagination['offset']}** "
        f"(page_size={pagination['page_size']}, łącznie: {pagination['total']})"
    )
    if pagination.get("next_offset"):
        text += f" – następna strona: `offset={pagination['next_offset']}`"
    return text + "\n"


def work_packages_markdown(title: str, data: Dict[str, Any], empty_text: str) -> str:
    """Markdown for a work package page built by `build_work_package_page`."""
    items = data["work_packages"]
    if not items:
        return f"{empty_text}\n"
    lines = [f"✅ **{title}** ({data['pagination']['total']}):", ""]
    lines += [_work_package_line(item) for item in items]
    return "\n".join(lines) + "\n" + pagination_markdown(data["pagination"])


# ---------------------------------------------------------------------------
# Moje zadania
# ---------------------------------------------------------------------------


@mcp.tool
async def list_my_work_packages(
    project_id: Optional[int] = None,
    include_closed: bool = False,
    offset: int = 1,
    page_size: int = 20,
    format: str = "markdown",
) -> str:
    """List work packages assigned to the current user (the API key owner).

    No user ID is needed - OpenProject resolves "me" on the server side.

    Args:
        project_id: Optional project ID to limit the list to one project
        include_closed: If True, also include closed work packages (default: open only)
        offset: Page number, 1-based (default: 1)
        page_size: Number of results per page (default: 20, max: 100)
        format: "markdown" (default) or "json"

    Returns:
        Work packages (ID, subject, status, type, priority, project, due date, % done)
    """
    error = invalid_format_error(format) or validate_pagination(offset, page_size)
    if error:
        return error

    filters = [
        {"assignee": {"operator": "=", "values": ["me"]}},
        {"status": {"operator": "*" if include_closed else "o", "values": []}},
    ]
    try:
        result = await get_client().get_work_packages(
            project_id=project_id,
            filters=json.dumps(filters),
            offset=offset,
            page_size=page_size,
        )
    except Exception as e:
        return format_api_error(e)

    data = build_work_package_page(
        result,
        offset,
        page_size,
        project_id=project_id,
        include_closed=include_closed,
    )
    scope = "Moje zadania" if include_closed else "Moje otwarte zadania"
    if project_id:
        scope += f" w projekcie #{project_id}"
    return render(
        data,
        format,
        lambda d: work_packages_markdown(scope, d, f"📭 {scope}: brak zadań."),
    )


# ---------------------------------------------------------------------------
# Zapisane widoki (queries)
# ---------------------------------------------------------------------------


def build_query_item(query: Dict) -> Dict[str, Any]:
    """Saved query (view) summary."""
    project = _ref(query, "project")
    return {
        "id": query.get("id"),
        "name": query.get("name"),
        "project": project if project["id"] or project["name"] else None,
        "public": bool(query.get("public")),
        "starred": bool(query.get("starred")),
    }


def _queries_markdown(data: Dict[str, Any]) -> str:
    queries = data["queries"]
    if not queries:
        return "📭 Brak zapisanych widoków.\n"
    lines = [f"✅ **Zapisane widoki** ({len(queries)}):", ""]
    for query in queries:
        flags = ["⭐" if query["starred"] else "", "🌐 publiczny" if query["public"] else "🔒 prywatny"]
        project = query["project"]
        project_text = f"projekt: {project['name']} (#{project['id']})" if project else "globalny"
        lines.append(
            f"- **{query['name']}** (ID: {query['id']}) — {project_text} | "
            + " ".join(f for f in flags if f)
        )
    return "\n".join(lines) + "\n\n💡 Użyj `run_query(query_id)`, aby pobrać zadania widoku.\n"


@mcp.tool
async def list_queries(project_id: Optional[int] = None, format: str = "markdown") -> str:
    """List saved work package views (queries) visible to the current user.

    Args:
        project_id: Optional project ID to list only that project's views
        format: "markdown" (default) or "json"

    Returns:
        Views with name, ID, project, public flag and starred flag
    """
    error = invalid_format_error(format)
    if error:
        return error
    try:
        result = await get_client().get_queries(project_id)
    except Exception as e:
        return format_api_error(e)

    elements = (result.get("_embedded") or {}).get("elements") or []
    data = {"project_id": project_id, "queries": [build_query_item(q) for q in elements]}
    return render(data, format, _queries_markdown)


@mcp.tool
async def run_query(
    query_id: int, offset: int = 1, page_size: int = 20, format: str = "markdown"
) -> str:
    """Run a saved view (query) and return its work packages.

    OpenProject applies the view's own filters and sort order.

    Args:
        query_id: Saved query (view) ID, see list_queries
        offset: Page number, 1-based (default: 1)
        page_size: Number of results per page (default: 20, max: 100)
        format: "markdown" (default) or "json"

    Returns:
        View name, total count and the requested page of work packages
    """
    error = invalid_format_error(format) or validate_pagination(offset, page_size)
    if error:
        return error
    try:
        query = await get_client().get_query(query_id, offset=offset, page_size=page_size)
    except Exception as e:
        return format_api_error(e)

    results = (query.get("_embedded") or {}).get("results") or {}
    data = build_work_package_page(
        results, offset, page_size, query=build_query_item(query)
    )
    title = f"Widok „{data['query']['name']}” (ID: {query_id})"
    return render(
        data,
        format,
        lambda d: work_packages_markdown(title, d, f"📭 {title}: brak zadań."),
    )


# ---------------------------------------------------------------------------
# Powiadomienia
# ---------------------------------------------------------------------------


def build_notification_item(notification: Dict) -> Dict[str, Any]:
    """Notification view model: reason, actor, date, work package (or other resource), project."""
    links = notification.get("_links") or {}
    resource = links.get("resource") or {}
    href = resource.get("href") or ""
    target = {"id": extract_id(href), "subject": resource.get("title")}
    project = _ref(notification, "project")
    return {
        "id": notification.get("id"),
        "reason": notification.get("reason"),
        "read": bool(notification.get("readIAN")),
        "created_at": notification.get("createdAt"),
        "actor": (links.get("actor") or {}).get("title"),
        "work_package": target if "/work_packages/" in href else None,
        "resource": None if "/work_packages/" in href else (resource or None),
        "project": project if project["id"] or project["name"] else None,
    }


def _notifications_markdown(data: Dict[str, Any]) -> str:
    items = data["notifications"]
    scope = "nieprzeczytane" if data["unread_only"] else "wszystkie"
    if data.get("reason"):
        scope += f", przyczyna: {data['reason']}"
    if not items:
        return f"📭 Brak powiadomień ({scope}).\n"
    lines = [f"🔔 **Powiadomienia** ({scope}; łącznie: {data['pagination']['total']}):", ""]
    for item in items:
        wp = item["work_package"]
        if wp:
            target = f"#{wp['id']} {wp['subject'] or ''}".strip()
        else:
            target = (item["resource"] or {}).get("title") or "(brak zasobu)"
        project = item["project"]
        suffix = f" | projekt: {project['name']}" if project else ""
        read = "" if item["read"] else "🆕 "
        lines.append(
            f"- {read}**{item['reason']}** — {target} | autor: {item['actor'] or '?'}"
            f" | {item['created_at']}{suffix}"
        )
    return "\n".join(lines) + "\n" + pagination_markdown(data["pagination"])


@mcp.tool
async def list_notifications(
    unread_only: bool = True,
    reason: Optional[str] = None,
    offset: int = 1,
    page_size: int = 20,
    format: str = "markdown",
) -> str:
    """List in-app notifications of the current user (read only - nothing is marked as read).

    Args:
        unread_only: If True (default), only unread notifications
        reason: Optional reason filter: mentioned, assigned, responsible, watched,
            subscribed, commented, created, processed, prioritized, scheduled,
            dateAlert, shared, reminder
        offset: Page number, 1-based (default: 1)
        page_size: Number of results per page (default: 20, max: 100)
        format: "markdown" (default) or "json"

    Returns:
        Notifications with reason, actor, date, work package (ID + subject) and project
    """
    error = invalid_format_error(format) or validate_pagination(offset, page_size)
    if error:
        return error
    reason = reason.strip() if reason else None
    if reason and reason not in NOTIFICATION_REASONS:
        return format_error(
            f"Invalid reason '{reason}'. Allowed values: {', '.join(NOTIFICATION_REASONS)}"
        )
    try:
        result = await get_client().get_notifications(
            unread_only=unread_only, reason=reason, offset=offset, page_size=page_size
        )
    except Exception as e:
        return format_api_error(e)

    elements: List[Dict] = (result.get("_embedded") or {}).get("elements") or []
    data = {
        "unread_only": unread_only,
        "reason": reason,
        "notifications": [build_notification_item(n) for n in elements],
        "pagination": build_pagination(result.get("total"), len(elements), offset, page_size),
    }
    return render(data, format, _notifications_markdown)
