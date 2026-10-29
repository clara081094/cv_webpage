"""Local filesystem media storage.

Files land in ``UPLOAD_FOLDER`` (a Docker volume in compose) and the database
keeps filename + checksum. Swapping this module for S3 later only requires
changing ``save_upload``/``delete_file``.
"""

import hashlib
import io
import os
import uuid
from pathlib import Path

from app.errors import ApiError
from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

EXTENSION_BY_FORMAT = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "GIF": "gif"}
MIME_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}


def upload_dir() -> Path:
    path = Path(current_app.config["UPLOAD_FOLDER"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def inspect_image(raw: bytes) -> tuple[str, int, int]:
    """Validate by decoding the bytes, not by trusting the filename extension."""
    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.verify()
        with Image.open(io.BytesIO(raw)) as img:
            fmt = (img.format or "").upper()
            width, height = img.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ApiError("File is not a readable image", code="INVALID_IMAGE") from exc

    allowed = current_app.config["ALLOWED_IMAGE_FORMATS"]
    if fmt not in allowed:
        raise ApiError(
            f"Image format {fmt or 'unknown'} not allowed",
            code="INVALID_IMAGE_FORMAT",
            details={"allowed": sorted(allowed)},
        )
    return fmt, width, height


def strip_metadata(raw: bytes, fmt: str) -> bytes:
    """Re-encode without EXIF/XMP so phone photos don't publish GPS or device data.

    Rotation from the EXIF orientation tag is baked into the pixels first, since
    the tag itself is dropped. GIFs are kept as-is so animations survive.
    """
    if fmt == "GIF":
        return raw
    with Image.open(io.BytesIO(raw)) as img:
        clean = ImageOps.exif_transpose(img)
        out = io.BytesIO()
        options = {"quality": 90} if fmt in {"JPEG", "WEBP"} else {}
        clean.save(out, format=fmt, **options)
    return out.getvalue()


def save_upload(file_storage) -> dict:
    raw = file_storage.read()
    if not raw:
        raise ApiError("Empty file", code="EMPTY_FILE")

    max_size = current_app.config["MAX_CONTENT_LENGTH"]
    if len(raw) > max_size:
        raise ApiError(
            f"File exceeds {max_size} bytes", code="FILE_TOO_LARGE", status_code=413
        )

    fmt, _, _ = inspect_image(raw)
    raw = strip_metadata(raw, fmt)
    with Image.open(io.BytesIO(raw)) as img:
        width, height = img.size
    checksum = hashlib.sha256(raw).hexdigest()
    extension = EXTENSION_BY_FORMAT[fmt]
    filename = f"{uuid.uuid4().hex}.{extension}"

    target = upload_dir() / filename
    target.write_bytes(raw)

    return {
        "filename": filename,
        "original_filename": file_storage.filename,
        "mime_type": MIME_BY_FORMAT[fmt],
        "size_bytes": len(raw),
        "width": width,
        "height": height,
        "checksum_sha256": checksum,
    }


def delete_file(filename: str) -> None:
    try:
        os.remove(upload_dir() / filename)
    except FileNotFoundError:
        current_app.logger.warning("media file already gone: %s", filename)
