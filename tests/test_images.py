"""Tests for src.utils.images (Pillow images generated in memory)."""

import os
from io import BytesIO

import pytest
from PIL import Image as PILImage

from src.utils import images
from src.utils.images import (
    MAX_IMAGE_BYTES,
    ImageTooLargeError,
    PillowUnavailableError,
    image_format_for,
    prepare_image,
)


def make_image(size, fmt="PNG", mode="RGB", noise=False, **save_kwargs) -> bytes:
    width, height = size
    if noise:
        image = PILImage.frombytes("RGB", size, os.urandom(width * height * 3))
    else:
        image = PILImage.new(mode, size, (30, 120, 200) if mode == "RGB" else None)
    buffer = BytesIO()
    image.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()


def open_image(data: bytes) -> PILImage.Image:
    return PILImage.open(BytesIO(data))


@pytest.mark.parametrize(
    "mime, expected",
    [
        ("image/png", "png"),
        ("IMAGE/JPEG; charset=binary", "jpeg"),
        ("image/gif", "gif"),
        ("image/webp", "webp"),
        ("image/svg+xml", None),
        ("application/pdf", None),
        (None, None),
    ],
)
def test_image_format_for(mime, expected):
    assert image_format_for(mime) == expected


def test_small_png_is_returned_unchanged():
    data = make_image((1200, 800))

    result = prepare_image(data, "image/png")

    assert result.data == data
    assert result.format == "png"
    assert result.size == result.original_size == (1200, 800)
    assert not result.changed


def test_large_jpeg_is_scaled_proportionally():
    data = make_image((4000, 3000), "JPEG")

    result = prepare_image(data, "image/jpeg", max_dimension=1600)

    assert result.original_size == (4000, 3000)
    assert result.size == (1600, 1200)
    assert open_image(result.data).size == (1600, 1200)
    assert result.format == "jpeg"
    assert len(result.data) <= MAX_IMAGE_BYTES


def test_custom_max_dimension_keeps_aspect_ratio_for_portrait():
    data = make_image((600, 1200))

    result = prepare_image(data, "image/png", max_dimension=300)

    assert result.size == (150, 300)


def test_png_over_byte_limit_is_reduced_below_limit():
    data = make_image((1500, 1000), noise=True)
    assert len(data) > MAX_IMAGE_BYTES

    result = prepare_image(data, "image/png")

    assert len(result.data) <= MAX_IMAGE_BYTES
    assert result.format == "jpeg"
    width, height = result.size
    assert abs(width / height - 1.5) < 0.01
    assert open_image(result.data).format == "JPEG"


def test_small_byte_limit_forces_further_downscaling():
    data = make_image((800, 800), noise=True)

    result = prepare_image(data, "image/png", max_bytes=20 * 1024)

    assert len(result.data) <= 20 * 1024
    assert max(result.size) < 800


def test_impossible_byte_limit_raises():
    data = make_image((400, 400), noise=True)

    with pytest.raises(ImageTooLargeError):
        prepare_image(data, "image/png", max_bytes=10)


def test_transparent_png_converted_to_jpeg_is_flattened():
    image = PILImage.frombytes("RGBA", (1200, 900), os.urandom(1200 * 900 * 4))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    result = prepare_image(buffer.getvalue(), "image/png")

    assert result.format == "jpeg"
    assert open_image(result.data).mode == "RGB"


def test_gif_returns_first_frame_as_png():
    frames = [PILImage.new("RGB", (200, 100), color) for color in ("red", "blue", "green")]
    buffer = BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:])

    result = prepare_image(buffer.getvalue(), "image/gif")

    assert result.format == "png"
    decoded = open_image(result.data).convert("RGB")
    assert decoded.size == (200, 100)
    assert getattr(open_image(result.data), "n_frames", 1) == 1
    red, green, blue = decoded.getpixel((10, 10))
    assert red > 200 and green < 50 and blue < 50


def test_webp_is_supported():
    data = make_image((2000, 1000), "WEBP")

    result = prepare_image(data, "image/webp")

    assert result.size == (1600, 800)
    assert result.format == "webp"


def test_unsupported_mime_raises_value_error():
    with pytest.raises(ValueError):
        prepare_image(b"<svg/>", "image/svg+xml")


def test_missing_pillow_raises_pillow_unavailable(monkeypatch):
    def no_pillow():
        raise PillowUnavailableError("Pillow is not installed")

    monkeypatch.setattr(images, "_load_pillow", no_pillow)

    with pytest.raises(PillowUnavailableError):
        prepare_image(make_image((10, 10)), "image/png")
