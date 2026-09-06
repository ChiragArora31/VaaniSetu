"""Text-to-speech backends for translated voice output.

Piper is the preferred open-source runtime backend. On macOS development
machines, the built-in ``say`` command is used as a provider-side fallback so
audio-to-audio flows still produce a downloadable voice artifact when Piper
voices have not been installed yet.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from config.settings import (
    ALLOW_MODEL_DOWNLOAD,
    ESPEAK_BINARY,
    FFMPEG_BINARY,
    INDIC_PARLER_DEVICE,
    INDIC_PARLER_MODEL,
    INDIC_PARLER_MODEL_ID,
    MODEL_PROFILE,
    PIPER_BINARY,
    PIPER_MODEL_DIR,
    TTS_BACKEND,
    TTS_TIMEOUT_SECONDS,
)
from core.media_utils import MediaError
from core.media_utils import require_binary


class TTSError(RuntimeError):
    """Raised when TTS generation cannot be completed."""


_INDIC_PARLER_DESCRIPTIONS = {
    "en": (
        "An Indian speaker delivers clear, natural, moderately paced speech. "
        "The recording is very high quality, with no background noise."
    ),
    "hi": (
        "A Hindi speaker delivers clear, natural, moderately paced speech with accurate pronunciation. "
        "The recording is very high quality, with no background noise."
    ),
    "mr": (
        "A Marathi speaker delivers clear, natural, moderately paced speech with accurate pronunciation. "
        "The recording is very high quality, with no background noise."
    ),
}


@lru_cache(maxsize=1)
def _load_indic_parler():
    try:
        import torch
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise TTSError("Indic Parler TTS dependencies are not installed.") from exc

    device = INDIC_PARLER_DEVICE
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = Path(INDIC_PARLER_MODEL)
    model_ref = str(model_path) if model_path.exists() else INDIC_PARLER_MODEL_ID
    if not model_path.exists() and not ALLOW_MODEL_DOWNLOAD:
        raise TTSError(f"Indic Parler TTS model is missing: {model_path}")
    try:
        model = ParlerTTSForConditionalGeneration.from_pretrained(
            model_ref,
            local_files_only=not ALLOW_MODEL_DOWNLOAD,
        ).to(device)
        prompt_tokenizer = AutoTokenizer.from_pretrained(model_ref, local_files_only=not ALLOW_MODEL_DOWNLOAD)
        description_tokenizer = AutoTokenizer.from_pretrained(
            model.config.text_encoder._name_or_path,
            local_files_only=not ALLOW_MODEL_DOWNLOAD,
        )
    except Exception as exc:
        raise TTSError(f"Indic Parler TTS model is unavailable: {exc}") from exc
    return model, prompt_tokenizer, description_tokenizer, device


def synthesize_with_indic_parler(text: str, language_hint: str, output_path: Path) -> Path:
    try:
        import soundfile as sf
    except ImportError as exc:
        raise TTSError("soundfile is required for Indic Parler TTS output.") from exc

    model, prompt_tokenizer, description_tokenizer, device = _load_indic_parler()
    description = _INDIC_PARLER_DESCRIPTIONS.get(language_hint, _INDIC_PARLER_DESCRIPTIONS["en"])
    try:
        description_inputs = description_tokenizer(description, return_tensors="pt").to(device)
        prompt_inputs = prompt_tokenizer(text, return_tensors="pt").to(device)
        generation = model.generate(
            input_ids=description_inputs.input_ids,
            attention_mask=description_inputs.attention_mask,
            prompt_input_ids=prompt_inputs.input_ids,
            prompt_attention_mask=prompt_inputs.attention_mask,
        )
        audio = generation.detach().cpu().numpy().squeeze()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), audio, model.config.sampling_rate)
    except Exception as exc:
        raise TTSError(f"Indic Parler TTS synthesis failed: {exc}") from exc
    return output_path


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


def synthesize_with_espeak(text: str, language_hint: str, output_path: Path) -> Path:
    binary = resolve_espeak_binary()
    if not binary:
        raise TTSError("The compact open-source speech engine is not installed on this worker.")
    voice = {"en": "en", "hi": "hi", "mr": "mr"}.get(language_hint, "en")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [binary, "-v", voice, "-s", "155", "-w", str(output_path), "--stdin"],
            input=text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
            timeout=TTS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise TTSError("Compact speech synthesis timed out.") from exc
    if result.returncode != 0:
        raise TTSError(result.stderr.strip() or "Compact speech synthesis failed.")
    return output_path


def resolve_espeak_binary() -> str | None:
    """Find eSpeak NG, including the standard Windows MSI locations."""

    resolved = shutil.which(ESPEAK_BINARY)
    if resolved:
        return resolved
    if platform.system() != "Windows":
        return None
    candidates = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(variable)
        if root:
            candidates.append(Path(root) / "eSpeak NG" / "espeak-ng.exe")
    return next((str(path) for path in candidates if path.is_file()), None)


def synthesize_speech(text: str, language_hint: str, output_path: Path) -> tuple[Path, str, str | None]:
    if not text.strip():
        raise TTSError("No translated text was available for speech synthesis.")

    backends = {
        "indic-parler": lambda: synthesize_with_indic_parler(text, language_hint, output_path),
        "piper": lambda: synthesize_with_piper(text, language_hint, output_path),
        "espeak": lambda: synthesize_with_espeak(text, language_hint, output_path),
        "macos-say": lambda: synthesize_with_macos_say(text, language_hint, output_path),
    }
    if TTS_BACKEND == "auto":
        order = (
            ["indic-parler", "piper", "espeak", "macos-say"]
            if MODEL_PROFILE == "quality"
            else ["piper", "espeak", "macos-say"]
        )
    elif TTS_BACKEND in backends:
        order = [TTS_BACKEND]
    else:
        raise TTSError(f"Unknown TTS backend: {TTS_BACKEND}")

    errors: list[str] = []
    for backend in order:
        try:
            return backends[backend](), backend, None
        except TTSError as exc:
            errors.append(f"{backend}: {exc}")
    raise TTSError("No configured speech engine succeeded. " + " ".join(errors))


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
