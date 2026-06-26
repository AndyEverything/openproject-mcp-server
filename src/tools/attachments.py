"""Attachment management tools (list, get, download, upload, delete)."""

import os
import mimetypes
from typing import Dict, Optional
from pydantic import BaseModel, Field

from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


# Content types that are safe to render inline as text.
_TEXT_CONTENT_TYPES = {
    "application/json",
    "application/xml",
    "application/x-yaml",
    "application/yaml",
    "application/markdown",
    "image/svg+xml",
}
_TEXT_EXTENSIONS = (
    ".md",
    ".txt",
    ".csv",
    ".tsv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
)


class UploadAttachmentInput(BaseModel):
    """Input model for uploading an attachment."""

    work_package_id: int = Field(..., description="Work package ID", gt=0)
    file_path: str = Field(
        ..., description="Absolute path to the local file to upload", min_length=1
    )
    file_name: Optional[str] = Field(
        None,
        description="Override the stored file name (defaults to the local file name)",
    )
    description: Optional[str] = Field(
        None, description="Optional attachment description"
    )


def _format_attachment(att: Dict) -> str:
    """Format a single attachment resource as markdown."""
    aid = att.get("id", "N/A")
    name = att.get("fileName", "unnamed")
    size = att.get("fileSize", "?")
    ctype = att.get("contentType", "unknown")

    text = f"- **{name}** (ID: {aid})\n"
    text += f"  Size: {size} bytes | Type: {ctype}\n"

    desc = att.get("description", {})
    if isinstance(desc, dict) and desc.get("raw"):
        text += f"  Description: {desc['raw']}\n"

    author = att.get("_links", {}).get("author", {}).get("title")
    if author:
        text += f"  Author: {author}\n"

    if att.get("createdAt"):
        text += f"  Created: {att['createdAt']}\n"

    return text + "\n"


def _looks_like_text(file_name: str, content_type: str) -> bool:
    """Heuristically decide whether content can be shown inline as text."""
    ctype = (content_type or "").lower()
    if ctype.startswith("text/"):
        return True
    if ctype in _TEXT_CONTENT_TYPES:
        return True
    return file_name.lower().endswith(_TEXT_EXTENSIONS)


@mcp.tool
async def list_attachments(work_package_id: int) -> str:
    """List all attachments of a work package.

    Args:
        work_package_id: The work package ID

    Returns:
        List of attachments with id, file name, size and type
    """
    try:
        client = get_client()
        result = await client.list_work_package_attachments(work_package_id)
        elements = result.get("_embedded", {}).get("elements", [])

        if not elements:
            return f"No attachments found for work package #{work_package_id}."

        text = (
            f"✅ **Attachments for Work Package #{work_package_id} "
            f"({len(elements)}):**\n\n"
        )
        for att in elements:
            text += _format_attachment(att)
        return text

    except Exception as e:
        return format_error(f"Failed to list attachments: {str(e)}")


@mcp.tool
async def get_attachment(attachment_id: int) -> str:
    """Get metadata for a single attachment.

    Args:
        attachment_id: The attachment ID

    Returns:
        Attachment details
    """
    try:
        client = get_client()
        att = await client.get_attachment(attachment_id)

        text = f"✅ **Attachment #{att.get('id', attachment_id)}**\n\n"
        text += _format_attachment(att)
        return text

    except Exception as e:
        return format_error(f"Failed to get attachment: {str(e)}")


@mcp.tool
async def download_attachment(
    attachment_id: int,
    save_path: Optional[str] = None,
    max_inline_chars: int = 50000,
) -> str:
    """Download an attachment's content.

    Behaviour:
    - If ``save_path`` is given, the file is written to disk (a directory path is
      allowed; the original file name is appended).
    - Otherwise, text content is returned inline and binary content asks you to
      re-run with ``save_path``.

    Args:
        attachment_id: The attachment ID
        save_path: Optional file or directory path to save the content to
        max_inline_chars: Maximum number of characters to return inline for text

    Returns:
        The saved path, or the inline text content
    """
    try:
        client = get_client()
        result = await client.download_attachment(attachment_id)
        content = result["content"]
        file_name = result["file_name"]
        content_type = result["content_type"]
        size = len(content)

        if save_path:
            path = save_path
            if os.path.isdir(path):
                path = os.path.join(path, file_name)
            with open(path, "wb") as f:
                f.write(content)
            return format_success(
                f"Downloaded '{file_name}' ({size} bytes) to {path}"
            )

        if _looks_like_text(file_name, content_type):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None:
                if len(text) > max_inline_chars:
                    text = (
                        text[:max_inline_chars]
                        + f"\n\n... [truncated, {size} bytes total]"
                    )
                return (
                    f"✅ **{file_name}** ({content_type}, {size} bytes):\n\n{text}"
                )

        return format_error(
            f"'{file_name}' is binary ({content_type}, {size} bytes). "
            f"Re-run with save_path to download it to disk."
        )

    except Exception as e:
        return format_error(f"Failed to download attachment: {str(e)}")


@mcp.tool
async def upload_attachment(input: UploadAttachmentInput) -> str:
    """Upload a local file as an attachment to a work package.

    Args:
        input: Upload data including work_package_id and file_path

    Returns:
        Success message with the created attachment details

    Example:
        {
            "work_package_id": 1024,
            "file_path": "/path/to/report.pdf",
            "description": "Monthly report"
        }
    """
    try:
        client = get_client()

        if not os.path.isfile(input.file_path):
            return format_error(f"File not found: {input.file_path}")

        file_name = input.file_name or os.path.basename(input.file_path)
        content_type, _ = mimetypes.guess_type(file_name)

        with open(input.file_path, "rb") as f:
            content = f.read()

        result = await client.upload_attachment(
            work_package_id=input.work_package_id,
            file_content=content,
            file_name=file_name,
            description=input.description,
            content_type=content_type,
        )

        text = format_success("Attachment uploaded successfully!\n\n")
        text += f"**ID**: #{result.get('id', 'N/A')}\n"
        text += f"**File**: {result.get('fileName', file_name)}\n"
        text += f"**Size**: {result.get('fileSize', len(content))} bytes\n"
        if result.get("contentType"):
            text += f"**Type**: {result['contentType']}\n"
        return text

    except Exception as e:
        return format_error(f"Failed to upload attachment: {str(e)}")


@mcp.tool
async def delete_attachment(attachment_id: int) -> str:
    """Delete an attachment.

    Args:
        attachment_id: The attachment ID

    Returns:
        Success message
    """
    try:
        client = get_client()
        await client.delete_attachment(attachment_id)
        return format_success(f"Attachment #{attachment_id} deleted successfully.")

    except Exception as e:
        return format_error(f"Failed to delete attachment: {str(e)}")
