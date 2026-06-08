"""Audio extraction and normalization through FFmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from config.settings import FFMPEG_BINARY, FFMPEG_TIMEOUT_SECONDS
from core.media_utils import MediaError, ensure_ffmpeg, inspect_media


def extract_audio_to_wav(input_path: Path, temp_dir: Path, sample_rate: int = 16000) -> Path:
    """Convert audio or video input into a mono WAV file suitable for ASR."""

    ensure_ffmpeg()
    info = inspect_media(input_path)
    if info.input_type not in {"audio", "video"}:
        raise MediaError("Audio extraction requires an audio or video file.")
    if info.has_audio is False:
        raise MediaError("No audio stream was found in this file.")

    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / f"{input_path.stem}_asr.wav"
    cmd = [
        FFMPEG_BINARY,
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "wav",
        str(output_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaError("FFmpeg timed out while extracting audio.") from exc
    if result.returncode != 0:
        raise MediaError(result.stderr.strip() or "FFmpeg could not extract audio.")
    return output_path
