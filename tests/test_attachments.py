"""Tests for attachment tools (src.tools.attachments) - no network."""

import base64
import json
import os
from io import BytesIO
from pathlib import Path

import pytest
from fastmcp.utilities.types import Image
from mcp.types import ImageContent, TextContent
from PIL import Image as PILImage

from src.client import DownloadTooLargeError, OpenProjectAPIError
from src.tools import attachments
from src.tools.attachments import (
    MAX_TEXT_BYTES,
    MAX_UPLOAD_BYTES,
    get_attachments_dir,
    human_size,
    is_text_attachment,
    sanitize_filename,
    save_attachment_file,
)
from src.utils import images
from src.utils.images import MAX_IMAGE_BYTES, PillowUnavailableError


@pytest.fixture(autouse=True)
def attachments_dir(tmp_path, monkeypatch) -> Path:
    directory = tmp_path / "op-attachments"
    monkeypatch.setenv("OPENPROJECT_ATTACHMENTS_DIR", str(directory))
    return directory


def make_image(size, fmt="PNG", noise=False) -> bytes:
    width, height = size
    if noise:
        image = PILImage.frombytes("RGB", size, os.urandom(width * height * 3))
    else:
        image = PILImage.new("RGB", size, (200, 40, 40))
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def setup_attachment(mock_client, attachment_id, file_name, content_type, data):
    mock_client.get_attachment.return_value = {
        "id": attachment_id,
        "fileName": file_name,
        "contentType": content_type,
        "fileSize": len(data),
    }
    mock_client.download_attachment.return_value = (data, content_type, file_name)


def decoded_image(result) -> PILImage.Image:
    image = result[1]
    assert isinstance(image, Image)
    return PILImage.open(BytesIO(image.data))


# ============================================================
# Helpers
# ============================================================


@pytest.mark.parametrize(
    "size, expected",
    [(0, "0 B"), (512, "512 B"), (2048, "2.0 KB"), (606425, "592.2 KB"), (5 * 1024 * 1024, "5.0 MB"), (None, "?")],
)
def test_human_size(size, expected):
    assert human_size(size) == expected


@pytest.mark.parametrize(
    "mime, name, expected",
    [
        ("text/plain", "a.bin", True),
        ("text/csv; charset=utf-8", "a.csv", True),
        ("application/json", "x", True),
        ("application/xml", "x", True),
        ("application/x-yaml", "x", True),
        ("application/octet-stream", "notes.md", True),
        ("application/octet-stream", "data.CSV", True),
        ("", "app.log", True),
        ("application/octet-stream", "setup.exe", False),
        ("application/pdf", "doc.txt", False),
        ("application/pdf", "doc.pdf", False),
    ],
)
def test_is_text_attachment(mime, name, expected):
    assert is_text_attachment(mime, name) is expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("..\\..\\evil.exe", "evil.exe"),
        ("../x", "x"),
        ("C:\\Windows\\system32\\cmd.exe", "cmd.exe"),
        ('a<b>c:d"e|f?g*h.txt', "abcdefgh.txt"),
        ("tab\tnew\nline.log", "tabnewline.log"),
        ("...hidden", "hidden"),
        ("  ..  ", "attachment"),
        ("..", "attachment"),
        ("", "attachment"),
        (None, "attachment"),
        ("raport.pdf.", "raport.pdf"),
    ],
)
def test_sanitize_filename(name, expected):
    assert sanitize_filename(name) == expected


def test_sanitize_filename_truncates_and_keeps_extension():
    result = sanitize_filename("a" * 300 + ".png")

    assert len(result) == 150
    assert result.endswith(".png")


def test_attachments_dir_empty_env_uses_system_temp(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENPROJECT_ATTACHMENTS_DIR", "")
    monkeypatch.setattr(attachments.tempfile, "gettempdir", lambda: str(tmp_path))

    directory = get_attachments_dir()

    assert directory == (tmp_path / "openproject-attachments").resolve()
    assert directory.is_dir()


@pytest.mark.parametrize(
    "name",
    ["..\\..\\evil.exe", "../x", "/etc/passwd", "C:\\x\\..\\..\\y.bat", "CON", "NUL.txt", "COM1", "a.txt:stream"],
)
def test_save_attachment_stays_inside_directory(attachments_dir, name):
    path = save_attachment_file(7, name, b"data")

    assert path.parent == attachments_dir.resolve()
    assert path.name.startswith("7_")
    assert path.read_bytes() == b"data"


# ============================================================
# list_work_package_attachments
# ============================================================


async def test_list_attachments_with_four_pngs(mock_client, call_tool, load_fixture):
    mock_client.get_work_package_attachments.return_value = load_fixture("att_with_images")

    result = await call_tool("list_work_package_attachments", work_package_id=1001)

    mock_client.get_work_package_attachments.assert_awaited_once_with(1001)
    for att_id in (131868, 131870, 131867, 131869):
        assert f"ID: {att_id}" in result
    assert result.count("`image/png`") == 4
    assert "592.2 KB" in result
    assert "Tester 1" in result
    assert "Zrzut ekranu błędu" in result
    assert "get_attachment" in result


async def test_list_attachments_empty(mock_client, call_tool, load_fixture):
    mock_client.get_work_package_attachments.return_value = load_fixture("att_empty")

    result = await call_tool("list_work_package_attachments", work_package_id=1002)

    assert "Brak załączników" in result


async def test_list_attachments_json_is_parseable(mock_client, call_tool, load_fixture):
    mock_client.get_work_package_attachments.return_value = load_fixture("att_with_images")

    result = await call_tool("list_work_package_attachments", work_package_id=1001, format="json")

    data = json.loads(result)
    assert data["work_package_id"] == 1001
    assert data["total"] == 4
    first = data["attachments"][0]
    assert first["id"] == 131868
    assert first["file_name"] == "image.png"
    assert first["content_type"] == "image/png"
    assert first["file_size"] == 606425
    assert first["author"] == "Tester 1"
    assert first["author_id"] == 901
    assert first["created_at"] == "2024-11-29T16:11:24.645Z"
    assert first["description"] == "Zrzut ekranu błędu"


async def test_list_attachments_api_error(mock_client, call_tool):
    mock_client.get_work_package_attachments.side_effect = OpenProjectAPIError(404, '{"message": "Brak zadania."}')

    result = await call_tool("list_work_package_attachments", work_package_id=5)

    assert result == "❌ Błąd API 404: Brak zadania."


# ============================================================
# get_attachment - images
# ============================================================


async def test_png_1200x800_returned_in_original_size(mock_client, call_tool):
    data = make_image((1200, 800))
    setup_attachment(mock_client, 11, "screen.png", "image/png", data)

    result = await call_tool("get_attachment", attachment_id=11)

    assert isinstance(result, list) and len(result) == 2
    assert "screen.png" in result[0]
    assert "1200×800" in result[0]
    assert result[1].data == data
    assert result[1]._mime_type == "image/png"
    mock_client.get_attachment.assert_awaited_once_with(11)
    mock_client.download_attachment.assert_awaited_once_with(11)


async def test_jpeg_4000x3000_scaled_to_1600(mock_client, call_tool):
    setup_attachment(mock_client, 12, "photo.jpg", "image/jpeg", make_image((4000, 3000), "JPEG"))

    result = await call_tool("get_attachment", attachment_id=12)

    image = decoded_image(result)
    assert max(image.size) <= 1600
    assert image.size == (1600, 1200)
    assert "4000×3000 → 1600×1200" in result[0]


async def test_custom_max_dimension(mock_client, call_tool):
    setup_attachment(mock_client, 12, "photo.jpg", "image/jpeg", make_image((1000, 500), "JPEG"))

    result = await call_tool("get_attachment", attachment_id=12, max_dimension=200)

    assert decoded_image(result).size == (200, 100)


async def test_image_over_byte_limit_is_reduced(mock_client, call_tool):
    data = make_image((1500, 1000), noise=True)
    assert len(data) > MAX_IMAGE_BYTES
    setup_attachment(mock_client, 13, "noise.png", "image/png", data)

    result = await call_tool("get_attachment", attachment_id=13)

    assert len(result[1].data) <= MAX_IMAGE_BYTES
    assert result[1]._mime_type.startswith("image/")


@pytest.mark.parametrize("value", [0, 63, 4097, -1])
async def test_invalid_max_dimension_rejected_before_request(mock_client, call_tool, value):
    result = await call_tool("get_attachment", attachment_id=1, max_dimension=value)

    assert result.startswith("❌")
    assert "max_dimension" in result
    mock_client.get_attachment.assert_not_awaited()


async def test_image_via_mcp_pipeline_is_image_content(mock_client, call_tool_mcp):
    data = make_image((1200, 800))
    setup_attachment(mock_client, 14, "screen.png", "image/png", data)

    result = await call_tool_mcp("get_attachment", {"attachment_id": 14})

    assert not result.is_error
    kinds = [type(block) for block in result.content]
    assert kinds == [TextContent, ImageContent]
    image_block = result.content[1]
    assert image_block.mimeType == "image/png"
    assert base64.b64decode(image_block.data) == data


async def test_without_pillow_small_image_returned_unscaled(mock_client, call_tool, monkeypatch):
    monkeypatch.setattr(images, "_load_pillow", _no_pillow)
    data = make_image((100, 100))
    setup_attachment(mock_client, 15, "small.png", "image/png", data)

    result = await call_tool("get_attachment", attachment_id=15)

    assert result[1].data == data
    assert "Pillow" in result[0]


async def test_without_pillow_large_image_saved_to_disk(mock_client, call_tool, monkeypatch, attachments_dir):
    monkeypatch.setattr(images, "_load_pillow", _no_pillow)
    data = b"\x89PNG" + b"0" * (MAX_IMAGE_BYTES + 1)
    setup_attachment(mock_client, 16, "big.png", "image/png", data)

    result = await call_tool("get_attachment", attachment_id=16)

    assert isinstance(result, str)
    assert "Pillow" in result
    assert (attachments_dir / "16_big.png").read_bytes() == data


def _no_pillow():
    raise PillowUnavailableError("Pillow is not installed")


async def test_corrupted_image_returns_error(mock_client, call_tool):
    setup_attachment(mock_client, 17, "broken.png", "image/png", b"not an image")

    result = await call_tool("get_attachment", attachment_id=17)

    assert isinstance(result, str) and result.startswith("❌")


# ============================================================
# get_attachment - text and binary files
# ============================================================


async def test_json_returned_as_text(mock_client, call_tool, attachments_dir):
    payload = '{"klucz": "wartość"}'
    setup_attachment(mock_client, 21, "config.json", "application/json", payload.encode("utf-8"))

    result = await call_tool("get_attachment", attachment_id=21)

    assert "```json\n" in result
    assert payload in result
    assert not attachments_dir.exists() or not any(attachments_dir.iterdir())


async def test_csv_octet_stream_returned_as_text(mock_client, call_tool):
    content = b"id;nazwa\n1;Kowalski\n"
    setup_attachment(mock_client, 22, "dane.csv", "application/octet-stream", content)

    result = await call_tool("get_attachment", attachment_id=22)

    assert "```csv\n" in result
    assert "1;Kowalski" in result


async def test_invalid_utf8_replaced(mock_client, call_tool):
    setup_attachment(mock_client, 23, "log.txt", "text/plain", b"ok \xff\xfe koniec")

    result = await call_tool("get_attachment", attachment_id=23)

    assert "ok \ufffd\ufffd koniec" in result


async def test_text_with_backticks_uses_longer_fence(mock_client, call_tool):
    setup_attachment(mock_client, 24, "readme.md", "text/markdown", b"```python\nx = 1\n```")

    result = await call_tool("get_attachment", attachment_id=24)

    assert "````markdown\n" in result


async def test_text_over_200kb_saved_to_disk(mock_client, call_tool, attachments_dir):
    data = b"a" * (MAX_TEXT_BYTES + 1)
    setup_attachment(mock_client, 25, "huge.log", "text/plain", data)

    result = await call_tool("get_attachment", attachment_id=25)

    saved = attachments_dir.resolve() / "25_huge.log"
    assert saved.read_bytes() == data
    assert str(saved) in result


async def test_pdf_saved_with_path_name_and_size(mock_client, call_tool, attachments_dir):
    data = b"%PDF-1.7\n" + b"x" * 2000
    setup_attachment(mock_client, 31, "Specyfikacja.pdf", "application/pdf", data)

    result = await call_tool("get_attachment", attachment_id=31)

    saved = attachments_dir.resolve() / "31_Specyfikacja.pdf"
    assert saved.read_bytes() == data
    assert str(saved) in result
    assert "Specyfikacja.pdf" in result
    assert f"{len(data)} B" in result
    assert "application/pdf" in result


@pytest.mark.parametrize("name, expected", [("..\\..\\evil.exe", "32_evil.exe"), ("../x", "32_x")])
async def test_malicious_names_saved_inside_directory(mock_client, call_tool, attachments_dir, name, expected):
    setup_attachment(mock_client, 32, name, "application/octet-stream", b"MZ")

    result = await call_tool("get_attachment", attachment_id=32)

    saved = attachments_dir.resolve() / expected
    assert saved.exists()
    assert str(saved) in result
    assert [p.name for p in attachments_dir.iterdir()] == [expected]


async def test_saved_file_is_never_executed(mock_client, call_tool, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("attachment must not be executed")

    monkeypatch.setattr(os, "startfile", forbidden, raising=False)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    setup_attachment(mock_client, 33, "run.exe", "application/x-msdownload", b"MZ")

    result = await call_tool("get_attachment", attachment_id=33)

    assert "33_run.exe" in result


async def test_declared_size_over_limit_skips_download(mock_client, call_tool):
    mock_client.get_attachment.return_value = {
        "id": 34, "fileName": "film.mp4", "contentType": "video/mp4", "fileSize": 100 * 1024 * 1024,
    }

    result = await call_tool("get_attachment", attachment_id=34)

    assert result.startswith("❌")
    assert "limit" in result
    mock_client.download_attachment.assert_not_awaited()


async def test_download_too_large_error_is_readable(mock_client, call_tool):
    mock_client.get_attachment.return_value = {"id": 35, "fileName": "a.zip", "contentType": "application/zip"}
    mock_client.download_attachment.side_effect = DownloadTooLargeError("too large")

    result = await call_tool("get_attachment", attachment_id=35)

    assert result.startswith("❌")
    assert "a.zip" in result and "limit" in result


async def test_get_attachment_metadata_404(mock_client, call_tool):
    mock_client.get_attachment.side_effect = OpenProjectAPIError(404, '{"message": "Nie znaleziono."}')

    result = await call_tool("get_attachment", attachment_id=36)

    assert result == "❌ Błąd API 404: Nie znaleziono."
    mock_client.download_attachment.assert_not_awaited()


# ============================================================
# upload_attachment
# ============================================================


async def test_upload_existing_file_returns_new_id(mock_client, call_tool, tmp_path):
    file_path = tmp_path / "zrzut.png"
    file_path.write_bytes(make_image((50, 50)))
    mock_client.upload_attachment.return_value = {
        "id": 555, "fileName": "zrzut.png", "fileSize": file_path.stat().st_size, "contentType": "image/png",
    }

    result = await call_tool("upload_attachment", work_package_id=1001, file_path=str(file_path), description="Błąd")

    mock_client.upload_attachment.assert_awaited_once_with(1001, str(file_path), "Błąd")
    assert "555" in result
    assert result.startswith("✅")


async def test_upload_missing_file_sends_no_request(mock_client, call_tool, tmp_path):
    result = await call_tool("upload_attachment", work_package_id=1, file_path=str(tmp_path / "brak.png"))

    assert result.startswith("❌")
    assert "nie istnieje" in result
    mock_client.upload_attachment.assert_not_awaited()


async def test_upload_directory_rejected(mock_client, call_tool, tmp_path):
    result = await call_tool("upload_attachment", work_package_id=1, file_path=str(tmp_path))

    assert result.startswith("❌")
    mock_client.upload_attachment.assert_not_awaited()


async def test_upload_too_large_rejected(mock_client, call_tool, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments, "MAX_UPLOAD_BYTES", 10)
    file_path = tmp_path / "big.bin"
    file_path.write_bytes(b"x" * 11)

    result = await call_tool("upload_attachment", work_package_id=1, file_path=str(file_path))

    assert result.startswith("❌")
    assert "za duży" in result
    mock_client.upload_attachment.assert_not_awaited()


async def test_upload_api_error(mock_client, call_tool, tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("x")
    mock_client.upload_attachment.side_effect = OpenProjectAPIError(403, '{"message": "Brak uprawnień."}')

    result = await call_tool("upload_attachment", work_package_id=1, file_path=str(file_path))

    assert result == "❌ Błąd API 403: Brak uprawnień."


def test_upload_limit_matches_download_limit():
    from src.client import MAX_DOWNLOAD_BYTES

    assert MAX_UPLOAD_BYTES == MAX_DOWNLOAD_BYTES
