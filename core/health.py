"""Runtime readiness checks for model and media capabilities."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from config.settings import (
    ACTIVE_MODEL_PROFILE,
    ALLOW_MODEL_DOWNLOAD,
    DEFAULT_WHISPER_MODEL,
    ESPEAK_BINARY,
    FFMPEG_BINARY,
    FFPROBE_BINARY,
    INDICTRANS_MODEL_BY_DIRECTION,
    INDICTRANS_REPO_BY_DIRECTION,
    NLLB_CT2_MODEL,
    NLLB_MODEL,
    NLLB_MODEL_ID,
    PIPER_BINARY,
    PIPER_MODEL_DIR,
    TESSDATA_DIR,
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


def _ocr_status() -> tuple[bool, str]:
    binary = shutil.which("tesseract")
    if not binary or not _package_available("pypdfium2"):
        return False, "Install Tesseract and the local PDF renderer"
    required = {"eng", "hin", "mar"}
    local_languages = {
        path.stem for path in TESSDATA_DIR.glob("*.traineddata")
    } if TESSDATA_DIR.exists() else set()
    if required.issubset(local_languages):
        return True, f"Local OCR languages ready: {', '.join(sorted(required))}"
    try:
        result = subprocess.run(
            [binary, "--list-langs"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        system_languages = set(result.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        system_languages = set()
    missing = sorted(required - system_languages)
    if not missing:
        return True, f"System OCR languages ready: {', '.join(sorted(required))}"
    return False, "Missing OCR language data: " + ", ".join(missing)


def collect_health_checks(allow_model_download: bool = ALLOW_MODEL_DOWNLOAD) -> list[HealthCheck]:
    ffmpeg_ok, ffmpeg_detail = _ffmpeg_status()
    ffprobe_ok, ffprobe_detail = _ffprobe_status()
    ocr_ok, ocr_detail = _ocr_status()
    nllb_ready = _model_dir_ready(NLLB_MODEL)
    nllb_ct2_ready = (Path(NLLB_CT2_MODEL) / "model.bin").exists()
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
        HealthCheck(
            name="NLLB local translation",
            ok=nllb_ready or allow_model_download,
            detail=(
                str(NLLB_MODEL)
                if nllb_ready
                else f"Will download/cache {NLLB_MODEL_ID}" if allow_model_download else str(NLLB_MODEL)
            ),
            required_for="non-gated local translation fallback",
        ),
        HealthCheck(
            name="NLLB optimized CPU runtime",
            ok=nllb_ct2_ready,
            detail=str(NLLB_CT2_MODEL) if nllb_ct2_ready else "Run scripts/convert_nllb_ct2.py",
            required_for="fast INT8 CPU translation fallback",
        ),
        HealthCheck(
            name="Local translation route",
            ok=nllb_ready or any(_model_dir_ready(path) for path in INDICTRANS_MODEL_BY_DIRECTION.values()),
            detail=(
                "Ready through optimized local NLLB fallback"
                if nllb_ct2_ready
                else "Ready through local NLLB fallback"
                if nllb_ready
                else "Install NLLB or authenticated IndicTrans2 models"
            ),
            required_for="text, document, audio, and video translation",
        ),
        HealthCheck(
            name="PDF text extraction",
            ok=_package_available("pypdf"),
            detail="Installed" if _package_available("pypdf") else "Install requirements.txt",
            required_for="PDF learning-module translation",
        ),
        HealthCheck(
            name="Automatic OCR",
            ok=ocr_ok,
            detail=ocr_detail,
            required_for="scanned PDF translation",
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
            HealthCheck(
                name="eSpeak NG",
                ok=shutil.which(ESPEAK_BINARY) is not None,
                detail=shutil.which(ESPEAK_BINARY) or f"Missing binary: {ESPEAK_BINARY}",
                required_for="compact cross-platform translated voice",
            ),
            HealthCheck(
                name="Local speech fallback",
                ok=shutil.which("say") is not None and shutil.which("afconvert") is not None,
                detail=shutil.which("say") or "macOS speech fallback unavailable",
                required_for="translated voice on this Mac",
            ),
        ]
    )
    return checks
