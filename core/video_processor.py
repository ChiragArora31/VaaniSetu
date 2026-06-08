"""Video post-processing helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from config.settings import FFMPEG_TIMEOUT_SECONDS
from core.media_utils import MediaError, ensure_ffmpeg


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
        raise MediaError("FFmpeg timed out while burning subtitles.") from exc
    if result.returncode != 0:
        raise MediaError(result.stderr.strip() or "FFmpeg could not burn subtitles.")
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
        raise MediaError("FFmpeg timed out while merging translated audio.") from exc
    if result.returncode != 0:
        raise MediaError(result.stderr.strip() or "FFmpeg could not merge translated audio into the video.")
    return output_path
