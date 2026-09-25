"""View model and markdown rendering of work package activities (comments + change history)."""

import re
from typing import Any, Dict, List, Optional

from src.utils.rendering import extract_id

# Znaczniki emfazy z `details[].raw`, np. "**Status** changed from *New* to *In progress*"
_BOLD = re.compile(r"(\*\*|__)(.+?)\1")
_ITALIC_STAR = re.compile(r"\*(\S(?:.*?\S)?)\*")
_ITALIC_UNDERSCORE = re.compile(r"(?<!\w)_(\S(?:.*?\S)?)_(?!\w)")


def strip_emphasis(text: str) -> str:
    """Remove markdown emphasis markers (**, __, *, _) keeping the enclosed text."""
    text = _BOLD.sub(r"\2", text)
    text = _ITALIC_STAR.sub(r"\1", text)
    return _ITALIC_UNDERSCORE.sub(r"\1", text)


def _user_name(activity: Dict) -> str:
    link = (activity.get("_links") or {}).get("user") or {}
    if link.get("title"):
        return str(link["title"])
    user_id = extract_id(link.get("href"))
    return f"Użytkownik #{user_id}" if user_id is not None else "Nieznany użytkownik"


def _comment(activity: Dict) -> str:
    comment = activity.get("comment")
    raw = comment.get("raw") if isinstance(comment, dict) else comment
    return raw if isinstance(raw, str) else ""


def _changes(activity: Dict) -> List[str]:
    changes: List[str] = []
    for detail in activity.get("details") or []:
        raw = detail.get("raw") if isinstance(detail, dict) else detail
        if isinstance(raw, str) and raw.strip():
            changes.append(strip_emphasis(raw.strip()))
    return changes


def build_activities(raw_collection: Dict, comments_only: bool = False) -> List[Dict[str, Any]]:
    """Map a HAL activity collection to [{id, created_at, user, user_id, comment, internal, changes}].

    Comments are kept in full (raw markdown); `comments_only` skips entries without a comment.
    """
    elements = ((raw_collection or {}).get("_embedded") or {}).get("elements") or []
    result: List[Dict[str, Any]] = []

    for activity in elements:
        comment = _comment(activity)
        if comments_only and not comment.strip():
            continue
        user_link = (activity.get("_links") or {}).get("user") or {}
        result.append(
            {
                "id": activity.get("id"),
                "created_at": activity.get("createdAt"),
                "user": _user_name(activity),
                "user_id": extract_id(user_link.get("href")),
                "comment": comment,
                "internal": bool(activity.get("internal")),
                "changes": _changes(activity),
            }
        )

    return result


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def activity_to_markdown(activity: Dict[str, Any]) -> str:
    """Markdown block of a single activity (full comment, all changes)."""
    lines = [
        f"**Activity #{activity.get('id', 'N/A')}** - {activity.get('user')}"
        f" · {activity.get('created_at') or 'brak daty'}"
    ]
    if activity.get("internal"):
        lines.append("🔒 Komentarz wewnętrzny")
    if activity.get("comment", "").strip():
        lines.append("💬 Komentarz:")
        lines.append(_quote(activity["comment"]))
    if activity.get("changes"):
        lines.append("✏️ Zmiany:")
        lines.extend(f"  - {change}" for change in activity["changes"])
    return "\n".join(lines)


def activities_to_markdown(activities: List[Dict[str, Any]], empty_text: Optional[str] = None) -> str:
    """Markdown list of activities separated by blank lines."""
    if not activities:
        return empty_text or "Brak aktywności."
    return "\n\n".join(activity_to_markdown(activity) for activity in activities)
