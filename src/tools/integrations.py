"""Code integration tools (GitHub/GitLab/file links)."""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from src.client import OpenProjectAPIError
from src.server import mcp, get_client
from src.utils.rendering import api_error_text, format_api_error, raise_fatal, render

# Klucz w `_links` zadania -> ścieżka pod /work_packages/{id}/
CODE_LINK_SOURCES: Dict[str, str] = {
    "github_pull_requests": "github_pull_requests",
    "gitlab_merge_requests": "gitlab_merge_requests",
    "gitlab_issues": "gitlab_issues",
    "fileLinks": "file_links",
}

SOURCE_LABELS: Dict[str, str] = {
    "github_pull_requests": "GitHub – pull requesty",
    "gitlab_merge_requests": "GitLab – merge requesty",
    "gitlab_issues": "GitLab – issues",
    "fileLinks": "Pliki powiązane (file links)",
}

UNAVAILABLE_REASONS: Dict[int, str] = {
    403: "brak uprawnień lub moduł wyłączony (403)",
    404: "moduł wyłączony lub endpoint nie istnieje (404)",
}
NO_LINK_REASON = "zadanie nie udostępnia tego linku (moduł wyłączony lub brak uprawnień)"


def _embedded_elements(collection: Dict) -> List[Dict]:
    return (collection.get("_embedded") or {}).get("elements") or []


def _absolute_url(base_url: str, href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    if href.startswith("/"):
        return f"{base_url}{href}"
    return href


def _code_item(element: Dict, url_key: str) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "title": element.get("title"),
        "state": element.get("state"),
        "url": element.get(url_key),
        "number": element.get("number"),
        "repository": element.get("repository"),
    }
    for flag in ("draft", "merged"):
        if flag in element:
            item[flag] = element.get(flag)
    return item


def _github_pr_item(element: Dict, _base_url: str) -> Dict[str, Any]:
    item = _code_item(element, "htmlUrl")
    author = ((element.get("_embedded") or {}).get("githubUser") or {}).get("login")
    if author:
        item["author"] = author
    return item


def _gitlab_item(element: Dict, _base_url: str) -> Dict[str, Any]:
    return _code_item(element, "webUrl")


def _file_link_item(element: Dict, base_url: str) -> Dict[str, Any]:
    origin = element.get("originData") or {}
    links = element.get("_links") or {}
    href = (links.get("staticOriginOpen") or {}).get("href") or (
        links.get("originOpen") or {}
    ).get("href")
    return {
        "title": origin.get("name") or element.get("originName"),
        "state": None,
        "url": _absolute_url(base_url, href),
        "storage": (links.get("storage") or {}).get("title"),
        "mime": origin.get("mimeType"),
        "size": origin.get("size"),
        "modified": origin.get("lastModifiedAt"),
    }


ITEM_MAPPERS: Dict[str, Callable[[Dict, str], Dict[str, Any]]] = {
    "github_pull_requests": _github_pr_item,
    "gitlab_merge_requests": _gitlab_item,
    "gitlab_issues": _gitlab_item,
    "fileLinks": _file_link_item,
}


def _has_link(work_package: Dict, link_key: str) -> bool:
    link = (work_package.get("_links") or {}).get(link_key)
    return isinstance(link, dict) and bool(link.get("href"))


def _section_from_error(e: Exception) -> Dict[str, Any]:
    if isinstance(e, OpenProjectAPIError):
        reason = UNAVAILABLE_REASONS.get(e.status)
        if reason:
            return {"available": False, "reason": reason, "status": e.status}
        message = f"Błąd API {e.status}: {api_error_text(e.body) or str(e)}"
        return {"available": True, "error": message, "status": e.status, "count": 0, "items": []}
    return {"available": True, "error": str(e) or e.__class__.__name__, "count": 0, "items": []}


def build_code_links(
    work_package_id: int,
    work_package: Dict,
    results: Dict[str, Any],
    base_url: str,
) -> Dict[str, Any]:
    """View model: per source either items, "unavailable" reason or error text.

    `results` maps a `_links` key to a collection, an exception, or None (no link).
    """
    sources: Dict[str, Any] = {}
    for link_key in CODE_LINK_SOURCES:
        result = results.get(link_key)
        section: Dict[str, Any] = {"label": SOURCE_LABELS[link_key]}
        if result is None:
            section.update({"available": False, "reason": NO_LINK_REASON})
        elif isinstance(result, Exception):
            section.update(_section_from_error(result))
        else:
            items = [ITEM_MAPPERS[link_key](el, base_url) for el in _embedded_elements(result)]
            section.update({"available": True, "count": len(items), "items": items})
        sources[CODE_LINK_SOURCES[link_key]] = section

    return {
        "id": work_package_id,
        "subject": work_package.get("subject"),
        "sources": sources,
    }


def _format_item_markdown(item: Dict[str, Any]) -> str:
    title = item.get("title") or "(bez tytułu)"
    if item.get("number") is not None:
        title = f"#{item['number']} {title}"
    parts = [f"**{title}**"]
    details = []
    if item.get("state"):
        state = item["state"]
        if item.get("merged"):
            state = f"{state}, merged"
        if item.get("draft"):
            state = f"{state}, draft"
        details.append(f"stan: {state}")
    for key, label in (
        ("repository", "repozytorium"),
        ("author", "autor"),
        ("storage", "magazyn"),
        ("mime", "typ"),
        ("size", "rozmiar"),
        ("modified", "zmieniony"),
    ):
        if item.get(key) not in (None, ""):
            details.append(f"{label}: {item[key]}")
    if details:
        parts.append(f"({'; '.join(details)})")
    line = "- " + " ".join(parts)
    if item.get("url"):
        line += f"\n  {item['url']}"
    return line


def format_code_links_markdown(data: Dict[str, Any]) -> str:
    subject = f" – {data['subject']}" if data.get("subject") else ""
    lines = [f"# 🔗 Powiązania z kodem i plikami: #{data['id']}{subject}", ""]
    for section in data["sources"].values():
        label = section["label"]
        if not section.get("available"):
            lines.append(f"## {label}")
            lines.append(f"⚠️ Źródło niedostępne: {section.get('reason')}")
        elif section.get("error"):
            lines.append(f"## {label}")
            lines.append(f"❌ {section['error']}")
        else:
            lines.append(f"## {label} ({section['count']})")
            if section["items"]:
                lines.extend(_format_item_markdown(item) for item in section["items"])
            else:
                lines.append("_Brak powiązań._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


@mcp.tool
async def list_work_package_code_links(work_package_id: int, format: str = "markdown") -> str:
    """List code and file integrations linked to a work package.

    Sources: GitHub pull requests, GitLab merge requests, GitLab issues and file links
    (external storages). Each source is returned separately with title, state and URL.
    A source the instance or user cannot access (module disabled, missing permission,
    403/404, or no matching link on the work package) is marked as unavailable while
    the remaining sources are returned normally.

    Args:
        work_package_id: Work package ID
        format: "markdown" (default) or "json" (same data as a JSON document)

    Returns:
        Sections per source with linked items, or an error message
    """
    client = get_client()
    try:
        work_package = await client.get_work_package(work_package_id)
    except Exception as e:
        return format_api_error(e)

    link_keys = [key for key in CODE_LINK_SOURCES if _has_link(work_package, key)]
    responses = await asyncio.gather(
        *(
            client.get_work_package_link_collection(work_package_id, CODE_LINK_SOURCES[key])
            for key in link_keys
        ),
        return_exceptions=True,
    )
    raise_fatal(responses)
    results: Dict[str, Any] = dict(zip(link_keys, responses))

    data = build_code_links(work_package_id, work_package, results, client.base_url)
    return render(data, format, format_code_links_markdown)
