"""Filesystem helpers for uploaded files and generated artifacts."""

from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from config.settings import (
    ALLOWED_EXTENSIONS,
    COMPRESSED_AUDIO_EXTENSIONS,
    COMPRESSED_AUDIO_MAX_UPLOAD_MB,
    DOCUMENT_EXTENSIONS,
    DOCUMENT_MAX_UPLOAD_MB,
    MIN_FREE_DISK_GB,
    TEXT_EXTENSIONS,
    TEXT_MAX_UPLOAD_MB,
    UNCOMPRESSED_AUDIO_EXTENSIONS,
    UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB,
    VIDEO_EXTENSIONS,
    VIDEO_MAX_UPLOAD_MB,
)


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


def max_upload_bytes_for_extension(suffix: str) -> int:
    if suffix in COMPRESSED_AUDIO_EXTENSIONS:
        return COMPRESSED_AUDIO_MAX_UPLOAD_MB * 1024 * 1024
    if suffix in UNCOMPRESSED_AUDIO_EXTENSIONS:
        return UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB * 1024 * 1024
    if suffix in VIDEO_EXTENSIONS:
        return VIDEO_MAX_UPLOAD_MB * 1024 * 1024
    if suffix in TEXT_EXTENSIONS:
        return TEXT_MAX_UPLOAD_MB * 1024 * 1024
    if suffix in DOCUMENT_EXTENSIONS:
        return DOCUMENT_MAX_UPLOAD_MB * 1024 * 1024
    return max(VIDEO_MAX_UPLOAD_MB, UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB) * 1024 * 1024


def upload_limit_label(suffix: str) -> str:
    if suffix in COMPRESSED_AUDIO_EXTENSIONS:
        return f"{COMPRESSED_AUDIO_MAX_UPLOAD_MB} MB for compressed audio"
    if suffix in UNCOMPRESSED_AUDIO_EXTENSIONS:
        return f"{UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB} MB for WAV/FLAC audio"
    if suffix in VIDEO_EXTENSIONS:
        return f"{VIDEO_MAX_UPLOAD_MB} MB for video"
    if suffix in TEXT_EXTENSIONS:
        return f"{TEXT_MAX_UPLOAD_MB} MB for text"
    if suffix in DOCUMENT_EXTENSIONS:
        return f"{DOCUMENT_MAX_UPLOAD_MB} MB for documents"
    return "the configured upload limit"


def validate_size(size_bytes: int, suffix: str) -> None:
    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty.")
    max_bytes = max_upload_bytes_for_extension(suffix)
    if size_bytes > max_bytes:
        raise ValidationError(f"File is too large. Maximum allowed size is {upload_limit_label(suffix)}.")


def create_job_dirs(temp_root: Path, output_root: Path) -> tuple[str, Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output_root).free < MIN_FREE_DISK_GB * 1024**3:
        raise ValidationError(
            f"The worker has less than {MIN_FREE_DISK_GB} GB free. "
            "Ask an administrator to archive old jobs or run cleanup before retrying."
        )
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
            if size > max_upload_bytes_for_extension(suffix):
                out.close()
                target.unlink(missing_ok=True)
                validate_size(size, suffix)
            out.write(chunk)
    validate_size(size, suffix)
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
