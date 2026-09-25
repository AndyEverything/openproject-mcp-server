"""Image preparation for MCP responses: proportional downscaling and recompression (Pillow)."""

from dataclasses import dataclass
from io import BytesIO
from typing import Any, Optional, Tuple

# ~750 KB surowych bajtów -> ~1 MB po base64 w odpowiedzi MCP
MAX_IMAGE_BYTES = 750 * 1024
MIN_IMAGE_DIMENSION = 64
MAX_IMAGE_DIMENSION = 4096
DEFAULT_MAX_DIMENSION = 1600

IMAGE_FORMATS = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/gif": "gif",
    "image/webp": "webp",
}

_JPEG_QUALITIES = (85, 70, 55, 40)
_SCALE_STEP = 0.75


class PillowUnavailableError(Exception):
    """Pillow is not installed, images cannot be processed."""


class ImageTooLargeError(Exception):
    """Image could not be reduced below the byte limit."""


@dataclass
class PreparedImage:
    data: bytes
    format: str
    original_size: Tuple[int, int]
    size: Tuple[int, int]
    original_bytes: int

    @property
    def mime_type(self) -> str:
        return f"image/{self.format}"

    @property
    def changed(self) -> bool:
        return self.size != self.original_size or len(self.data) != self.original_bytes


def image_format_for(mime_type: Optional[str]) -> Optional[str]:
    """Pillow/MCP format name for a supported image MIME type, else None."""
    return IMAGE_FORMATS.get((mime_type or "").split(";")[0].strip().lower())


def _load_pillow() -> Any:
    try:
        from PIL import Image as PILImage
    except ImportError as e:
        raise PillowUnavailableError("Pillow is not installed") from e
    return PILImage


def prepare_image(
    data: bytes,
    mime_type: str,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    max_bytes: int = MAX_IMAGE_BYTES,
) -> PreparedImage:
    """Return the image unchanged if it fits both limits, otherwise downscale/recompress it.

    GIF is always reduced to its first frame (encoded as PNG). If PNG is still too
    large, it is converted to JPEG with decreasing quality and further downscaled
    down to MIN_IMAGE_DIMENSION.

    Raises:
        PillowUnavailableError: Pillow is not installed
        ImageTooLargeError: the image cannot be made smaller than max_bytes
        ValueError: unsupported MIME type
        Exception: Pillow errors for corrupted images
    """
    source_format = image_format_for(mime_type)
    if source_format is None:
        raise ValueError(f"Unsupported image type: {mime_type}")

    PILImage = _load_pillow()
    image = PILImage.open(BytesIO(data))
    image.seek(0)
    image.load()
    original_size = image.size

    fits = max(original_size) <= max_dimension and len(data) <= max_bytes
    if fits and source_format != "gif":
        return PreparedImage(data, source_format, original_size, original_size, len(data))

    if source_format == "gif":
        image = image.convert("RGBA")
        source_format = "png"

    if max(image.size) > max_dimension:
        image = image.copy()
        image.thumbnail((max_dimension, max_dimension), PILImage.LANCZOS)

    encoded = _encode(image, source_format)
    if len(encoded) <= max_bytes:
        return PreparedImage(encoded, source_format, original_size, image.size, len(data))

    current = image
    while True:
        for quality in _JPEG_QUALITIES:
            encoded = _encode(current, "jpeg", quality)
            if len(encoded) <= max_bytes:
                return PreparedImage(encoded, "jpeg", original_size, current.size, len(data))

        new_size = tuple(max(1, int(side * _SCALE_STEP)) for side in current.size)
        if max(new_size) < MIN_IMAGE_DIMENSION:
            raise ImageTooLargeError(
                f"Image cannot be reduced below {max_bytes} bytes"
            )
        current = image.resize(new_size, PILImage.LANCZOS)


def _encode(image: Any, fmt: str, quality: int = 90) -> bytes:
    buffer = BytesIO()
    if fmt == "jpeg":
        _to_rgb(image).save(buffer, format="JPEG", quality=quality, optimize=True)
    elif fmt == "png":
        image.save(buffer, format="PNG", optimize=True)
    elif fmt == "webp":
        image.save(buffer, format="WEBP", quality=quality)
    else:
        raise ValueError(f"Unsupported output format: {fmt}")
    return buffer.getvalue()


def _to_rgb(image: Any) -> Any:
    """RGB copy; transparency is flattened onto a white background."""
    if image.mode == "RGB":
        return image
    if image.mode in ("RGBA", "LA", "P") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        PILImage = _load_pillow()
        background = PILImage.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")
