"""
Secure File Handling & Validation Utilities.
Section 35: File validation, MIME validation, path traversal prevention, file-size limits.
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationException


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> str:
    """Validate and return normalized lower-case file extension."""
    if not filename or "." not in filename:
        raise ValidationException("Invalid file: missing file extension.")

    ext = filename.rsplit(".", 1)[-1].lower().strip()
    if ext not in allowed_extensions:
        raise ValidationException(
            f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )
    return ext


def sanitize_filename(filename: str) -> str:
    """Strip path traversal attempts and special characters."""
    base = os.path.basename(filename)
    clean_name = "".join(c for c in base if c.isalnum() or c in "._- ")
    return clean_name or "uploaded_file"


async def save_uploaded_file(
    file: UploadFile,
    subfolder: str = "audio",
    allowed_extensions: Optional[List[str]] = None,
    max_size_bytes: Optional[int] = None,
) -> Tuple[str, int]:
    """
    Safely save an uploaded file and return relative URL/path and byte size.
    Prevents directory traversal and enforces maximum size limits.
    """
    max_bytes = max_size_bytes or settings.MAX_FILE_SIZE_BYTES
    allowed = allowed_extensions or (settings.ALLOWED_AUDIO_EXTENSIONS if subfolder == "audio" else settings.ALLOWED_FILE_EXTENSIONS)

    ext = validate_file_extension(file.filename or "", allowed)
    safe_name = sanitize_filename(file.filename or f"upload.{ext}")

    # Build unique filename with UUID
    unique_filename = f"{uuid.uuid4().hex}_{safe_name}"

    upload_dir = Path(settings.UPLOAD_DIR) / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    target_path = upload_dir / unique_filename

    # Read and enforce file size in chunks
    total_bytes = 0
    with open(target_path, "wb") as destination:
        while chunk := await file.read(65536):  # 64KB chunks
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                # Remove partially written file
                destination.close()
                if target_path.exists():
                    target_path.unlink()
                raise ValidationException(
                    f"File exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB."
                )
            destination.write(chunk)

    rel_url = f"/uploads/{subfolder}/{unique_filename}"
    return rel_url, total_bytes
