"""Video post-processing helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from config.settings import FFMPEG_TIMEOUT_SECONDS
from core.media_utils import MediaError, ensure_ffmpeg


def _ffmpeg_failure(operation: str, stderr: str) -> MediaError:
    detail = (stderr or "").strip()
    if "No such filter: 'subtitles'" in detail or "Filter not found" in detail:
        return MediaError(
            "Captioned video is unavailable because this local FFmpeg build does not include "
            "the subtitles filter. The downloadable SRT and VTT captions are still ready."
        )
    useful_lines = [line.strip() for line in detail.splitlines() if line.strip()]
    useful = useful_lines[-1] if useful_lines else "the media command did not complete"
    return MediaError(f"{operation} failed in local FFmpeg: {useful[:240]}")


def burn_subtitles(video_path: Path, subtitle_path: Path, output_path: Path) -> Path:
    ffmpeg_binary = ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    escaped_subtitle_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
    subtitle_filter = f"subtitles='{escaped_subtitle_path}'"
    cmd = [
        ffmpeg_binary,
        "-y",
        "-i",
        str(video_path),
        "-vf",
        subtitle_filter,
        "-c:a",
        "copy",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=FFMPEG_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise MediaError("FFmpeg timed out while burning subtitles.") from exc
    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        raise _ffmpeg_failure("Caption rendering", result.stderr)
    return output_path


def mux_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    ffmpeg_binary = ensure_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_binary,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=FFMPEG_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise MediaError("FFmpeg timed out while merging translated audio.") from exc
    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        raise _ffmpeg_failure("Translated-audio video", result.stderr)
    return output_path
