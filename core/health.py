"""Runtime readiness checks for model and media capabilities."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass
from pathlib import Path

from config.settings import (
    ACTIVE_MODEL_PROFILE,
    ALLOW_MODEL_DOWNLOAD,
    DEFAULT_WHISPER_MODEL,
    FFMPEG_BINARY,
    FFPROBE_BINARY,
    INDICTRANS_MODEL_BY_DIRECTION,
    INDICTRANS_REPO_BY_DIRECTION,
    PIPER_BINARY,
    PIPER_MODEL_DIR,
    MODEL_PROFILE,
    WHISPER_MODEL_ID,
)
from core.media_utils import MediaError, require_binary


@dataclass(frozen=True)
class HealthCheck:
    name: str
    ok: bool
    detail: str
    required_for: str


def _package_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _model_dir_ready(path: str | Path) -> bool:
    directory = Path(path)
    if not directory.exists() or not directory.is_dir():
        return False
    expected = {"config.json"}
    names = {child.name for child in directory.iterdir()}
    has_weights = any(child.suffix in {".bin", ".safetensors"} for child in directory.iterdir())
    return expected.issubset(names) and has_weights


def _ffmpeg_status() -> tuple[bool, str]:
    try:
        return True, require_binary(FFMPEG_BINARY, "FFmpeg")
    except MediaError:
        return False, f"Missing binary: {FFMPEG_BINARY}"


def _ffprobe_status() -> tuple[bool, str]:
    resolved = shutil.which(FFPROBE_BINARY)
    if resolved:
        return True, resolved
    if _package_available("av"):
        return True, "PyAV media inspection fallback available"
    return False, f"Missing binary: {FFPROBE_BINARY}"


def collect_health_checks(allow_model_download: bool = ALLOW_MODEL_DOWNLOAD) -> list[HealthCheck]:
    ffmpeg_ok, ffmpeg_detail = _ffmpeg_status()
    ffprobe_ok, ffprobe_detail = _ffprobe_status()
    checks = [
        HealthCheck(
            name="Model quality profile",
            ok=True,
            detail=f"{MODEL_PROFILE}: {ACTIVE_MODEL_PROFILE['description']}",
            required_for="deployment sizing and accuracy expectations",
        ),
        HealthCheck(
            name="FFmpeg",
            ok=ffmpeg_ok,
            detail=ffmpeg_detail,
            required_for="audio/video extraction, MP3 export, video processing",
        ),
        HealthCheck(
            name="ffprobe",
            ok=ffprobe_ok,
            detail=ffprobe_detail,
            required_for="media validation",
        ),
        HealthCheck(
            name="faster-whisper package",
            ok=_package_available("faster_whisper"),
            detail="Installed" if _package_available("faster_whisper") else "Install requirements.txt",
            required_for="audio/video transcription",
        ),
        HealthCheck(
            name="Whisper model",
            ok=Path(DEFAULT_WHISPER_MODEL).exists() or allow_model_download,
            detail=(
                str(DEFAULT_WHISPER_MODEL)
                if Path(DEFAULT_WHISPER_MODEL).exists()
                else f"Will download/cache {WHISPER_MODEL_ID}" if allow_model_download else str(DEFAULT_WHISPER_MODEL)
            ),
            required_for="audio/video transcription",
        ),
        HealthCheck(
            name="Transformers package",
            ok=_package_available("transformers"),
            detail="Installed" if _package_available("transformers") else "Install requirements-full.txt",
            required_for="IndicTrans2 translation",
        ),
        HealthCheck(
            name="IndicTrans toolkit",
            ok=_package_available("IndicTransToolkit"),
            detail="Installed" if _package_available("IndicTransToolkit") else "Install requirements-full.txt",
            required_for="IndicTrans2 translation",
        ),
    ]

    for direction, path in INDICTRANS_MODEL_BY_DIRECTION.items():
        local_ready = _model_dir_ready(path)
        checks.append(
            HealthCheck(
                name=f"IndicTrans2 {direction}",
                ok=local_ready or allow_model_download,
                detail=(
                    str(path)
                    if local_ready
                    else f"Will download/cache {INDICTRANS_REPO_BY_DIRECTION[direction]}"
                    if allow_model_download
                    else str(path)
                ),
                required_for="high-quality translation",
            )
        )

    checks.extend(
        [
            HealthCheck(
                name="Piper binary",
                ok=shutil.which(PIPER_BINARY) is not None,
                detail=shutil.which(PIPER_BINARY) or f"Missing binary: {PIPER_BINARY}",
                required_for="translated voice",
            ),
            HealthCheck(
                name="Piper voices",
                ok=any(PIPER_MODEL_DIR.glob("*.onnx")) if PIPER_MODEL_DIR.exists() else False,
                detail=str(PIPER_MODEL_DIR),
                required_for="translated voice",
            ),
        ]
    )
    return checks
