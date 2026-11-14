#!/usr/bin/env python3
"""
Test script for the attachment tools (offline validation).

Validates input models and formatting helpers without hitting the API,
mirroring the dry-run style of test_tools.py.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_attachment_tools():
    """Validate attachment input models and formatting helpers."""
    print("=" * 70)
    print("Testing Attachment Tools (offline)")
    print("=" * 70)

    # Test 1: Module imports & tool registration
    print("\n[1] Test: import attachments module")
    try:
        from src.tools import attachments  # noqa: F401
        from src.tools.attachments import (
            UploadAttachmentInput,
            _format_attachment,
            _looks_like_text,
        )
        print("OK PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")
        return

    # Test 2: UploadAttachmentInput validation
    print("\n[2] Test: UploadAttachmentInput validation")
    try:
        model = UploadAttachmentInput(
            work_package_id=1024,
            file_path="/tmp/report.pdf",
            description="Monthly report",
        )
        assert model.work_package_id == 1024
        assert model.file_name is None
        print("OK Input validation PASSED")
        print(f"   Model: {model.model_dump()}")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 3: UploadAttachmentInput rejects bad input
    print("\n[3] Test: UploadAttachmentInput rejects invalid work_package_id")
    try:
        UploadAttachmentInput(work_package_id=0, file_path="/tmp/x")
        print("FAIL FAILED: expected validation error")
    except Exception:
        print("OK Validation correctly rejected work_package_id=0")

    # Test 4: _format_attachment
    print("\n[4] Test: _format_attachment")
    try:
        sample = {
            "id": 577,
            "fileName": "protocol.md",
            "fileSize": 20801,
            "contentType": "text/plain",
            "description": {"raw": "Meeting protocol"},
            "createdAt": "2026-06-26T12:16:05.168Z",
            "_links": {"author": {"title": "Ivan Matveev"}},
        }
        out = _format_attachment(sample)
        assert "protocol.md" in out
        assert "577" in out
        assert "Ivan Matveev" in out
        assert "Meeting protocol" in out
        print("OK _format_attachment PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    # Test 5: _looks_like_text heuristic
    print("\n[5] Test: _looks_like_text heuristic")
    try:
        assert _looks_like_text("a.md", "text/plain") is True
        assert _looks_like_text("a.json", "application/json") is True
        assert _looks_like_text("notes", "text/markdown") is True
        assert _looks_like_text("photo.png", "image/png") is False
        assert _looks_like_text("doc.pdf", "application/pdf") is False
        print("OK _looks_like_text PASSED")
    except Exception as e:
        print(f"FAIL FAILED: {e}")

    print("\n" + "=" * 70)
    print("OK Attachment Tests Completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_attachment_tools()
