"""Work package attachment tools."""

import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastmcp.utilities.types import Image

from src.client import MAX_DOWNLOAD_BYTES, DownloadTooLargeError
from src.server import mcp, get_client
from src.utils.formatting import format_error
from src.utils.images import (
    DEFAULT_MAX_DIMENSION,
    MAX_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    MIN_IMAGE_DIMENSION,
    ImageTooLargeError,
    PillowUnavailableError,
    image_format_for,
    prepare_image,
)
from src.utils.rendering import extract_id, format_api_error, render

ATTACHMENTS_DIR_ENV = "OPENPROJECT_ATTACHMENTS_DIR"
DEFAULT_ATTACHMENTS_SUBDIR = "openproject-attachments"
MAX_TEXT_BYTES = 200 * 1024
# Upload korzysta z tego samego limitu co pobieranie (plik wczytywany do pamięci)
MAX_UPLOAD_BYTES = MAX_DOWNLOAD_BYTES
MAX_FILENAME_LENGTH = 150

TEXT_MIME_TYPES = frozenset(
    {"application/json", "application/xml", "application/yaml", "application/x-yaml"}
)
TEXT_EXTENSIONS = {
    ".md": "markdown",
    ".csv": "csv",
    ".log": "text",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".txt": "text",
}
GENERIC_MIME_TYPES = frozenset({"", "application/octet-stream", "binary/octet-stream"})

_FORBIDDEN_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')

ToolResult = Union[str, List[Union[str, Image]]]


# ============================================================
# Helpers
# ============================================================


def human_size(size: Optional[int]) -> str:
    """Readable size: B / KB / MB."""
    if size is None:
        return "?"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _normalize_mime(mime_type: Optional[str]) -> str:
    return (mime_type or "").split(";")[0].strip().lower()


def is_text_attachment(mime_type: Optional[str], file_name: Optional[str]) -> bool:
    """Text by MIME, or by extension when the MIME type is generic (octet-stream)."""
    mime = _normalize_mime(mime_type)
    if mime.startswith("text/") or mime in TEXT_MIME_TYPES:
        return True
    extension = os.path.splitext(file_name or "")[1].lower()
    return mime in GENERIC_MIME_TYPES and extension in TEXT_EXTENSIONS


def sanitize_filename(name: Optional[str]) -> str:
    """Safe file name: basename only, no path/control characters, max 150 chars."""
    base = os.path.basename((name or "").replace("\\", "/"))
    base = _FORBIDDEN_FILENAME_CHARS.sub("", base)
    # Windows po cichu obcina końcowe kropki i spacje
    base = base.lstrip(". ").rstrip(". ")
    if not base:
        return "attachment"
    if len(base) > MAX_FILENAME_LENGTH:
        stem, extension = os.path.splitext(base)
        if len(extension) > 20:
            stem, extension = base, ""
        base = stem[: MAX_FILENAME_LENGTH - len(extension)] + extension
    return base


def get_attachments_dir() -> Path:
    """Target directory (OPENPROJECT_ATTACHMENTS_DIR, empty = system temp), created if missing."""
    configured = os.getenv(ATTACHMENTS_DIR_ENV, "").strip()
    directory = (
        Path(configured).expanduser()
        if configured
        else Path(tempfile.gettempdir()) / DEFAULT_ATTACHMENTS_SUBDIR
    )
    directory.mkdir(parents=True, exist_ok=True)
    return directory.resolve()


def save_attachment_file(attachment_id: int, file_name: Optional[str], data: bytes) -> Path:
    """Write the attachment into the attachments directory; the file is never executed."""
    directory = get_attachments_dir()
    target = (directory / f"{attachment_id}_{sanitize_filename(file_name)}").resolve()
    if target.parent != directory:
        raise ValueError(f"Unsafe attachment path outside {directory}: {target}")
    target.write_bytes(data)
    return target


def _code_fence(content: str) -> str:
    longest = max((len(m) for m in re.findall(r"`+", content)), default=0)
    return "`" * max(3, longest + 1)


def _text_language(file_name: Optional[str], mime_type: str) -> str:
    extension = os.path.splitext(file_name or "")[1].lower()
    if extension in TEXT_EXTENSIONS:
        return TEXT_EXTENSIONS[extension]
    if "json" in mime_type:
        return "json"
    if "xml" in mime_type:
        return "xml"
    if "yaml" in mime_type:
        return "yaml"
    return "text"


def _description_raw(description: Any) -> str:
    if isinstance(description, dict):
        return (description.get("raw") or "").strip()
    return str(description or "").strip()


# ============================================================
# View model + markdown
# ============================================================


def build_attachment_list(work_package_id: int, collection: Dict) -> Dict[str, Any]:
    """View model of a HAL attachment collection."""
    elements = collection.get("_embedded", {}).get("elements", []) or []
    attachments = []
    for element in elements:
        links = element.get("_links", {}) or {}
        author = links.get("author", {}) or {}
        download = links.get("downloadLocation", {}) or {}
        size = element.get("fileSize")
        attachments.append(
            {
                "id": element.get("id"),
                "file_name": element.get("fileName"),
                "content_type": element.get("contentType"),
                "file_size": size,
                "file_size_human": human_size(size),
                "author": author.get("title"),
                "author_id": extract_id(author.get("href")),
                "created_at": element.get("createdAt"),
                "description": _description_raw(element.get("description")),
                "download_href": download.get("href"),
            }
        )
    return {
        "work_package_id": work_package_id,
        "total": len(attachments),
        "attachments": attachments,
    }


def attachment_list_markdown(data: Dict[str, Any]) -> str:
    wp_id = data["work_package_id"]
    attachments = data["attachments"]
    if not attachments:
        return f"📭 Brak załączników w zadaniu #{wp_id}."

    lines = [f"📎 **Załączniki zadania #{wp_id}** ({len(attachments)}):", ""]
    for att in attachments:
        lines.append(f"- **{att['file_name']}** (ID: {att['id']})")
        lines.append(
            f"  Typ: `{att['content_type'] or '?'}` · Rozmiar: {att['file_size_human']}"
        )
        lines.append(
            f"  Autor: {att['author'] or '?'} · Dodano: {att['created_at'] or '?'}"
        )
        if att["description"]:
            lines.append(f"  Opis: {att['description']}")
    lines.append("")
    lines.append(
        "💡 Obraz (zrzut ekranu) lub treść pliku pobierzesz przez "
        "`get_attachment(attachment_id)`."
    )
    return "\n".join(lines)


# ============================================================
# Attachment tools
# ============================================================


@mcp.tool
async def list_work_package_attachments(
    work_package_id: int, format: str = "markdown"
) -> str:
    """List attachments of a work package (ID, file name, MIME type, size, author, date, description).

    Use get_attachment(attachment_id) to view an image or read/save a file.

    Args:
        work_package_id: Work package ID
        format: "markdown" (default) or "json"
    """
    try:
        client = get_client()
        collection = await client.get_work_package_attachments(work_package_id)
    except Exception as e:
        return format_api_error(e)
    data = build_attachment_list(work_package_id, collection)
    return render(data, format, attachment_list_markdown)


@mcp.tool
async def get_attachment(
    attachment_id: int, max_dimension: int = DEFAULT_MAX_DIMENSION
) -> ToolResult:
    """Get an attachment's content so the model can use it.

    - Images (PNG, JPEG, GIF, WEBP) are returned as viewable image content,
      proportionally downscaled when the longer side exceeds max_dimension or the
      data exceeds ~750 KB (GIF: first frame).
    - Text files (text/*, JSON, XML, YAML, CSV, markdown, log) up to 200 KB are
      returned as text.
    - Other files (PDF, DOCX, archives, larger text...) are saved to the local
      attachments directory (OPENPROJECT_ATTACHMENTS_DIR, default: system temp
      dir/openproject-attachments); the response contains the full path. Saved
      files are never opened or executed.

    Args:
        attachment_id: Attachment ID (see list_work_package_attachments)
        max_dimension: Max length in px of the longer image side (64-4096, default 1600)
    """
    if not MIN_IMAGE_DIMENSION <= max_dimension <= MAX_IMAGE_DIMENSION:
        return format_error(
            f"max_dimension musi mieścić się w zakresie {MIN_IMAGE_DIMENSION}–"
            f"{MAX_IMAGE_DIMENSION} (podano {max_dimension})"
        )

    try:
        client = get_client()
        meta = await client.get_attachment(attachment_id)
    except Exception as e:
        return format_api_error(e)

    file_name = meta.get("fileName") or f"attachment-{attachment_id}"
    declared_size = meta.get("fileSize")
    mime_type = _normalize_mime(meta.get("contentType"))

    if isinstance(declared_size, int) and declared_size > MAX_DOWNLOAD_BYTES:
        return _too_large_message(file_name, declared_size)

    try:
        data, downloaded_type, _ = await client.download_attachment(attachment_id)
    except DownloadTooLargeError:
        return _too_large_message(file_name, declared_size)
    except Exception as e:
        return format_api_error(e)

    mime_type = mime_type or _normalize_mime(downloaded_type)

    try:
        if image_format_for(mime_type):
            return _image_result(attachment_id, file_name, mime_type, data, max_dimension)
        if is_text_attachment(mime_type, file_name) and len(data) <= MAX_TEXT_BYTES:
            return _text_result(attachment_id, file_name, mime_type, data)
        note = (
            f"Plik tekstowy większy niż {human_size(MAX_TEXT_BYTES)} – zapisano na dysk."
            if is_text_attachment(mime_type, file_name)
            else None
        )
        return _saved_result(attachment_id, file_name, mime_type, data, note)
    except Exception as e:
        return format_error(f"Nie udało się przetworzyć załącznika {attachment_id}: {e}")


def _too_large_message(file_name: str, size: Optional[int]) -> str:
    size_text = f" ({human_size(size)})" if isinstance(size, int) else ""
    return format_error(
        f"Załącznik '{file_name}'{size_text} przekracza limit pobierania "
        f"{human_size(MAX_DOWNLOAD_BYTES)}. Pobierz go bezpośrednio z OpenProject."
    )


def _image_result(
    attachment_id: int, file_name: str, mime_type: str, data: bytes, max_dimension: int
) -> ToolResult:
    try:
        prepared = prepare_image(data, mime_type, max_dimension)
    except PillowUnavailableError:
        if len(data) <= MAX_IMAGE_BYTES:
            text = (
                f"🖼️ **{file_name}** (ID: {attachment_id}, `{mime_type}`, {human_size(len(data))})\n"
                "⚠️ Pillow niedostępny – obraz zwrócony bez skalowania."
            )
            return [text, Image(data=data, format=image_format_for(mime_type))]
        return _saved_result(
            attachment_id, file_name, mime_type, data,
            "⚠️ Pillow niedostępny, a obraz przekracza limit odpowiedzi – zapisano na dysk.",
        )
    except ImageTooLargeError:
        return _saved_result(
            attachment_id, file_name, mime_type, data,
            "⚠️ Nie udało się zmniejszyć obrazu poniżej limitu odpowiedzi – zapisano na dysk.",
        )

    ow, oh = prepared.original_size
    w, h = prepared.size
    lines = [f"🖼️ **{file_name}** (ID: {attachment_id})"]
    if prepared.changed:
        lines.append(f"Wymiary: {ow}×{oh} → {w}×{h} px")
        lines.append(
            f"Rozmiar: {human_size(prepared.original_bytes)} → {human_size(len(prepared.data))} "
            f"(`{mime_type}` → `{prepared.mime_type}`)"
        )
    else:
        lines.append(f"Wymiary: {w}×{h} px (oryginalne)")
        lines.append(f"Rozmiar: {human_size(len(prepared.data))} (`{prepared.mime_type}`)")
    return ["\n".join(lines), Image(data=prepared.data, format=prepared.format)]


def _text_result(attachment_id: int, file_name: str, mime_type: str, data: bytes) -> str:
    content = data.decode("utf-8", errors="replace")
    fence = _code_fence(content)
    language = _text_language(file_name, mime_type)
    return (
        f"📄 **{file_name}** (ID: {attachment_id}, `{mime_type or 'unknown'}`, "
        f"{human_size(len(data))})\n\n"
        f"{fence}{language}\n{content}\n{fence}"
    )


def _saved_result(
    attachment_id: int, file_name: str, mime_type: str, data: bytes, note: Optional[str] = None
) -> str:
    path = save_attachment_file(attachment_id, file_name, data)
    lines = [
        "💾 Załącznik zapisany na dysku (plik nie został otwarty ani uruchomiony).",
        f"- **Ścieżka:** `{path}`",
        f"- **Nazwa:** {file_name}",
        f"- **Rozmiar:** {human_size(len(data))} ({len(data)} B)",
        f"- **Typ MIME:** `{mime_type or 'unknown'}`",
    ]
    if note:
        lines.append("")
        lines.append(note)
    return "\n".join(lines)


@mcp.tool
async def upload_attachment(
    work_package_id: int, file_path: str, description: Optional[str] = None
) -> str:
    """Upload a local file as a work package attachment.

    The file must exist, be a regular file and be at most 25 MB; this is checked
    before any request is sent to OpenProject.

    Args:
        work_package_id: Work package ID
        file_path: Path of the local file to upload
        description: Optional attachment description
    """
    if not file_path or not file_path.strip():
        return format_error("Parametr file_path jest wymagany")
    path = Path(file_path.strip()).expanduser()
    if not path.exists():
        return format_error(f"Plik nie istnieje: {path}")
    if not path.is_file():
        return format_error(f"Ścieżka nie jest zwykłym plikiem: {path}")
    size = path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        return format_error(
            f"Plik jest za duży ({human_size(size)}); limit uploadu to "
            f"{human_size(MAX_UPLOAD_BYTES)}"
        )

    try:
        client = get_client()
        result = await client.upload_attachment(work_package_id, str(path), description)
    except Exception as e:
        return format_api_error(e)

    return (
        f"✅ Dodano załącznik do zadania #{work_package_id}\n"
        f"- **ID załącznika:** {result.get('id')}\n"
        f"- **Nazwa:** {result.get('fileName') or path.name}\n"
        f"- **Rozmiar:** {human_size(result.get('fileSize', size))}\n"
        f"- **Typ MIME:** `{result.get('contentType') or '?'}`"
    )
