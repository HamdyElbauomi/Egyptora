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
DOCUMENT_TYPES = {**IMAGE_TYPES, "application/pdf": ".pdf"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024  # 10 MB
URL_PREFIX = "/uploads"


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


async def _save(file: UploadFile, folder: str, allowed: dict[str, str], max_bytes: int, kinds: str) -> str:
    ext = allowed.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{file.filename}: only {kinds} files are allowed")
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"{file.filename}: file is larger than {max_bytes // (1024 * 1024)} MB"
        )
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{file.filename}: file is empty")

    target_dir = upload_root() / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"  # random name: nobody can guess another file's URL
    (target_dir / name).write_bytes(content)
    return f"{URL_PREFIX}/{folder}/{name}"


async def save_image(file: UploadFile, folder: str) -> str:
    """Validates and saves one image (JPEG, PNG, WebP, max 5 MB). Returns its public URL. Raises 400 otherwise."""
    return await _save(file, folder, IMAGE_TYPES, MAX_IMAGE_BYTES, "JPEG, PNG or WebP")


async def save_document(file: UploadFile, folder: str) -> str:
    """Validates and saves a document such as a license (PDF or image, max 10 MB). Returns its public URL."""
    return await _save(file, folder, DOCUMENT_TYPES, MAX_DOCUMENT_BYTES, "PDF, JPEG, PNG or WebP")


def delete_file(url: str | None) -> None:
    """Deletes a file previously saved by this module. Ignores URLs that point elsewhere."""
    if not url or not url.startswith(URL_PREFIX + "/"):
        return
    relative = url.removeprefix(URL_PREFIX + "/")
    path = (upload_root() / relative).resolve()
    if upload_root().resolve() in path.parents and path.is_file():
        path.unlink()
