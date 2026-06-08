"""Text-to-speech backends for translated voice output.

Piper is the preferred open-source runtime backend. On macOS development
machines, the built-in ``say`` command is used as a provider-side fallback so
audio-to-audio flows still produce a downloadable voice artifact when Piper
voices have not been installed yet.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from config.settings import FFMPEG_BINARY, PIPER_BINARY, PIPER_MODEL_DIR, TTS_TIMEOUT_SECONDS
from core.media_utils import MediaError
from core.media_utils import require_binary


class TTSError(RuntimeError):
    """Raised when TTS generation cannot be completed."""


def find_piper_model(language_hint: str) -> Path:
    candidates = sorted(PIPER_MODEL_DIR.glob(f"*{language_hint}*.onnx"))
    if not candidates:
        candidates = sorted(PIPER_MODEL_DIR.glob("*.onnx"))
    if not candidates:
        raise TTSError(
            f"No Piper voice model found in '{PIPER_MODEL_DIR}'. Download a .onnx voice model first."
        )
    return candidates[0]


def synthesize_with_piper(text: str, language_hint: str, output_path: Path) -> Path:
    try:
        binary = require_binary(PIPER_BINARY, "Piper TTS")
    except MediaError as exc:
        raise TTSError(str(exc)) from exc
    model_path = find_piper_model(language_hint)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [binary, "--model", str(model_path), "--output_file", str(output_path)]
    try:
        result = subprocess.run(
            cmd,
            input=text,
            capture_output=True,
            text=True,
            check=False,
            timeout=TTS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise TTSError("Piper timed out while synthesizing speech.") from exc
    if result.returncode != 0:
        raise TTSError(result.stderr.strip() or "Piper could not synthesize speech.")
    return output_path


def _macos_voice(language_hint: str) -> str:
    return {
        "en": "Rishi",
        "hi": "Lekha",
        "mr": "Lekha",
    }.get(language_hint, "Rishi")


def synthesize_with_macos_say(text: str, language_hint: str, output_path: Path) -> Path:
    say_binary = shutil.which("say")
    afconvert_binary = shutil.which("afconvert")
    if not say_binary or not afconvert_binary:
        raise TTSError("No local fallback speech engine is available on this server.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    voice = _macos_voice(language_hint)
    with tempfile.TemporaryDirectory(prefix="vaanisetu_tts_") as directory:
        aiff_path = Path(directory) / "speech.aiff"
        try:
            say_result = subprocess.run(
                [say_binary, "-v", voice, "-o", str(aiff_path), text],
                capture_output=True,
                text=True,
                check=False,
                timeout=TTS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise TTSError("Fallback speech synthesis timed out.") from exc
        if say_result.returncode != 0:
            raise TTSError(say_result.stderr.strip() or "Fallback speech synthesis failed.")

        try:
            convert_result = subprocess.run(
                [
                    afconvert_binary,
                    "-f",
                    "WAVE",
                    "-d",
                    "LEI16@22050",
                    str(aiff_path),
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=TTS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise TTSError("Fallback speech conversion timed out.") from exc
        if convert_result.returncode != 0:
            raise TTSError(convert_result.stderr.strip() or "Fallback speech conversion failed.")
    return output_path


def synthesize_speech(text: str, language_hint: str, output_path: Path) -> tuple[Path, str, str | None]:
    if not text.strip():
        raise TTSError("No translated text was available for speech synthesis.")

    try:
        return synthesize_with_piper(text, language_hint, output_path), "piper", None
    except TTSError as piper_error:
        try:
            return (
                synthesize_with_macos_say(text, language_hint, output_path),
                "macos-say",
                None,
            )
        except TTSError as fallback_error:
            raise TTSError(f"{piper_error} Fallback TTS also failed: {fallback_error}") from fallback_error


def _convert_wav_to_mp3_with_pyav(wav_path: Path, output_path: Path) -> Path:
    try:
        import av
    except ImportError as exc:
        raise TTSError("MP3 export runtime is unavailable on this server.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with av.open(str(wav_path)) as input_container:
            input_stream = input_container.streams.audio[0]
            with av.open(str(output_path), "w") as output_container:
                output_stream = output_container.add_stream("mp3", rate=22050)
                output_stream.bit_rate = 128000
                output_stream.layout = "mono"
                for frame in input_container.decode(input_stream):
                    frame.pts = None
                    for packet in output_stream.encode(frame):
                        output_container.mux(packet)
                for packet in output_stream.encode(None):
                    output_container.mux(packet)
    except Exception as exc:
        raise TTSError("MP3 export failed.") from exc
    return output_path


def convert_wav_to_mp3(wav_path: Path, output_path: Path) -> Path:
    try:
        ffmpeg_binary = require_binary(FFMPEG_BINARY, "FFmpeg")
    except MediaError as exc:
        try:
            return _convert_wav_to_mp3_with_pyav(wav_path, output_path)
        except TTSError:
            pass
        afconvert_binary = shutil.which("afconvert")
        if not afconvert_binary:
            raise TTSError("MP3 export is unavailable on this server; WAV voice output was generated.") from exc
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                [afconvert_binary, "-f", "MPG3", "-d", ".mp3", str(wav_path), str(output_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=TTS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as timeout_exc:
            raise TTSError("MP3 export timed out.") from timeout_exc
        if result.returncode != 0:
            raise TTSError(result.stderr.strip() or "MP3 export failed.")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_binary,
        "-y",
        "-i",
        str(wav_path),
        "-codec:a",
        "libmp3lame",
        "-qscale:a",
        "2",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=TTS_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        raise TTSError("FFmpeg timed out while converting speech to MP3.") from exc
    if result.returncode != 0:
        raise TTSError(result.stderr.strip() or "FFmpeg could not convert speech to MP3.")
    return output_path
