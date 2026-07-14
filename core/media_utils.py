"""Media format detection and FFmpeg availability helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from config.settings import AUDIO_EXTENSIONS, DOCUMENT_EXTENSIONS, FFMPEG_BINARY, FFPROBE_BINARY, TEXT_EXTENSIONS, VIDEO_EXTENSIONS


class MediaError(RuntimeError):
    """Raised for media inspection or conversion errors."""


@dataclass(frozen=True)
class MediaInfo:
    input_type: str
    extension: str
    duration_seconds: float | None = None
    has_audio: bool | None = None
    has_video: bool | None = None
    width: int | None = None
    height: int | None = None


def detect_input_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    raise MediaError(f"Unsupported media extension: {suffix}")


def require_binary(binary: str, label: str) -> str:
    resolved = shutil.which(binary)
    if resolved:
        return resolved
    if binary == FFMPEG_BINARY:
        try:
            import imageio_ffmpeg

            bundled = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            bundled = None
        if bundled and Path(bundled).exists():
            return bundled
    raise MediaError(f"{label} was not found. Install it and ensure '{binary}' is on PATH.")


def ensure_ffmpeg() -> str:
    return require_binary(FFMPEG_BINARY, "FFmpeg")


def ffprobe(path: Path, timeout_seconds: int = 30) -> dict:
    if not path.exists():
        raise MediaError(f"File does not exist: {path}")
    binary = require_binary(FFPROBE_BINARY, "ffprobe")
    cmd = [
        binary,
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        raise MediaError("ffprobe timed out while inspecting the file.") from exc
    if result.returncode != 0:
        raise MediaError(result.stderr.strip() or "ffprobe could not inspect the file.")
    return json.loads(result.stdout or "{}")


def inspect_media(path: Path) -> MediaInfo:
    input_type = detect_input_type(path)
    if input_type == "text":
        return MediaInfo(input_type=input_type, extension=path.suffix.lower())

    try:
        data = ffprobe(path)
    except MediaError:
        return inspect_media_with_pyav(path, input_type)
    streams = data.get("streams", [])
    duration_raw = data.get("format", {}).get("duration")
    duration = None
    if duration_raw is not None:
        try:
            duration = float(duration_raw)
        except ValueError:
            duration = None
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    return MediaInfo(
        input_type=input_type,
        extension=path.suffix.lower(),
        duration_seconds=duration,
        has_audio=has_audio,
        has_video=has_video,
        width=_safe_int(video_stream.get("width")),
        height=_safe_int(video_stream.get("height")),
    )


def _safe_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def inspect_media_with_pyav(path: Path, input_type: str | None = None) -> MediaInfo:
    try:
        import av
    except ImportError as exc:
        raise MediaError("Media inspection runtime is unavailable on the server.") from exc

    input_type = input_type or detect_input_type(path)
    try:
        with av.open(str(path)) as container:
            has_audio = any(stream.type == "audio" for stream in container.streams)
            has_video = any(stream.type == "video" for stream in container.streams)
            duration = None
            if container.duration is not None:
                duration = float(container.duration / av.time_base)
            video_stream = next((stream for stream in container.streams if stream.type == "video"), None)
    except Exception as exc:
        raise MediaError("The uploaded media file could not be inspected or decoded.") from exc

    return MediaInfo(
        input_type=input_type,
        extension=path.suffix.lower(),
        duration_seconds=duration,
        has_audio=has_audio,
        has_video=has_video,
        width=getattr(video_stream, "width", None) if video_stream else None,
        height=getattr(video_stream, "height", None) if video_stream else None,
    )
