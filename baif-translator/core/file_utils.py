"""Filesystem helpers for uploaded files and generated artifacts."""

from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from config.settings import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES


class ValidationError(ValueError):
    """Raised when an uploaded file is not acceptable."""


@dataclass(frozen=True)
class SavedUpload:
    original_name: str
    path: Path
    size_bytes: int
    extension: str


def safe_filename(filename: str) -> str:
    stem = Path(filename).stem or "upload"
    suffix = Path(filename).suffix.lower()
    clean_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._")
    return f"{clean_stem or 'upload'}{suffix}"


def validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if not suffix:
        raise ValidationError("File has no extension. Please upload a supported file type.")
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(f"Unsupported file type '{suffix}'. Supported types: {allowed}")
    return suffix


def validate_size(size_bytes: int) -> None:
    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty.")
    if size_bytes > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ValidationError(f"File is too large. Maximum allowed size is {max_mb} MB.")


def create_job_dirs(temp_root: Path, output_root: Path) -> tuple[str, Path, Path]:
    job_id = uuid.uuid4().hex[:12]
    temp_dir = temp_root / job_id
    output_dir = output_root / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    return job_id, temp_dir, output_dir


def save_binary_upload(file_obj: BinaryIO, filename: str, temp_dir: Path) -> SavedUpload:
    suffix = validate_extension(filename)
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass

    safe_name = safe_filename(filename)
    target = temp_dir / safe_name
    if target.exists():
        target = temp_dir / f"{Path(safe_name).stem}_{uuid.uuid4().hex[:8]}{suffix}"
    size = 0
    with target.open("wb") as out:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                target.unlink(missing_ok=True)
                validate_size(size)
            out.write(chunk)
    validate_size(size)
    return SavedUpload(original_name=filename, path=target, size_bytes=size, extension=suffix)


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def copy_to_output(source: Path, output_dir: Path, name: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / (name or source.name)
    shutil.copy2(source, target)
    return target
