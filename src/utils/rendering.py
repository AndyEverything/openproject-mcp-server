"""Shared view-model rendering (markdown/JSON) and API error helpers for read tools."""

import json
import re
from typing import Any, Callable, Dict, Iterable, Optional

from src.client import OpenProjectAPIError
from src.utils.formatting import format_error

FORMAT_MARKDOWN = "markdown"
FORMAT_JSON = "json"
VALID_FORMATS = (FORMAT_MARKDOWN, FORMAT_JSON)

SECTION_ERROR_MESSAGES = {
    403: "Brak dostępu (403)",
    404: "Niedostępne (404)",
}


def raise_fatal(results: Iterable[Any]) -> None:
    """Re-raise BaseException (e.g. CancelledError) from gather(return_exceptions=True) results."""
    for value in results:
        if isinstance(value, BaseException) and not isinstance(value, Exception):
            raise value


_ID_FROM_HREF = re.compile(r"/api/v3/[^?#]*?/(\d+)/?(?:[?#].*)?$")


def render(data: Any, format: str, markdown_fn: Callable[[Any], str]) -> str:
    """Render a view model as markdown (default) or JSON; unknown format -> error text."""
    normalized = (format or FORMAT_MARKDOWN).strip().lower()
    if normalized == FORMAT_JSON:
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if normalized == FORMAT_MARKDOWN:
        return markdown_fn(data)
    return format_error(
        f"Invalid format '{format}'. Allowed values: {', '.join(VALID_FORMATS)}"
    )


def format_api_error(e: Exception) -> str:
    """Readable error message; includes the HTTP status for OpenProjectAPIError."""
    if isinstance(e, OpenProjectAPIError):
        return f"❌ Błąd API {e.status}: {api_error_text(e.body) or str(e)}"
    return format_error(str(e))


def section_error(e: Exception) -> Dict[str, Optional[Any]]:
    """Error payload for a failed context section: {"error": str, "status": int | None}."""
    if isinstance(e, OpenProjectAPIError):
        message = SECTION_ERROR_MESSAGES.get(e.status)
        if message is None:
            message = f"Błąd API {e.status}: {api_error_text(e.body) or str(e)}"
        return {"error": message, "status": e.status}
    return {"error": str(e) or e.__class__.__name__, "status": None}


def extract_id(href: Optional[str]) -> Optional[int]:
    """Numeric ID from an API href such as "/api/v3/users/123"; None if absent."""
    if not href or not isinstance(href, str):
        return None
    match = _ID_FROM_HREF.search(href)
    return int(match.group(1)) if match else None


def api_error_text(body: Optional[str]) -> str:
    """Error text from an OpenProject HAL error body (its `message`) or the raw body."""
    if not body:
        return ""
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict) and parsed.get("message"):
            return str(parsed["message"])
    except (ValueError, TypeError):
        pass
    return body.strip().splitlines()[0][:500] if body.strip() else ""
