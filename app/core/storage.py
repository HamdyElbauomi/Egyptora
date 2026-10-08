"""Saving uploaded files to disk and serving them under /uploads.

Files are stored in settings.upload_dir (default: ./uploads, ignored by Git) and the database keeps only
the public URL, e.g. "/uploads/places/12/3f9c...e1.jpg". Swap this module for S3 / Cloudinary later
without touching the routers.
"""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
URL_PREFIX = "/uploads"


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


async def save_image(file: UploadFile, folder: str) -> str:
    """Validates and saves one image. Returns its public URL. Raises 400 for wrong type or size."""
    ext = IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{file.filename}: only JPEG, PNG or WebP images are allowed",
        )
    content = await file.read()
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{file.filename}: image is larger than 5 MB")
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{file.filename}: file is empty")

    target_dir = upload_root() / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (target_dir / name).write_bytes(content)
    return f"{URL_PREFIX}/{folder}/{name}"


def delete_file(url: str | None) -> None:
    """Deletes a file previously saved by this module. Ignores URLs that point elsewhere."""
    if not url or not url.startswith(URL_PREFIX + "/"):
        return
    relative = url.removeprefix(URL_PREFIX + "/")
    path = (upload_root() / relative).resolve()
    if upload_root().resolve() in path.parents and path.is_file():
        path.unlink()
