"""Application settings and filesystem paths."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_STORAGE_DIR = Path(os.getenv("BAIF_RUNTIME_STORAGE_DIR", str(BASE_DIR)))
TEMP_DIR = Path(os.getenv("BAIF_TEMP_DIR", str(RUNTIME_STORAGE_DIR / "temp")))
OUTPUT_DIR = Path(os.getenv("BAIF_OUTPUT_DIR", str(RUNTIME_STORAGE_DIR / "outputs")))
MODEL_DIR = Path(os.getenv("BAIF_MODEL_DIR", str(RUNTIME_STORAGE_DIR / "models")))
SAMPLE_DIR = BASE_DIR / "samples"

TEXT_MAX_UPLOAD_MB = int(os.getenv("BAIF_TEXT_MAX_UPLOAD_MB", "10"))
COMPRESSED_AUDIO_MAX_UPLOAD_MB = int(os.getenv("BAIF_COMPRESSED_AUDIO_MAX_UPLOAD_MB", "50"))
UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB = int(os.getenv("BAIF_UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB", "150"))
VIDEO_MAX_UPLOAD_MB = int(os.getenv("BAIF_VIDEO_MAX_UPLOAD_MB", "200"))
MAX_TEXT_CHARS = int(os.getenv("BAIF_MAX_TEXT_CHARS", "20000"))
AUDIO_MAX_DURATION_SECONDS = int(os.getenv("BAIF_AUDIO_MAX_DURATION_SECONDS", "1800"))
VIDEO_MAX_DURATION_SECONDS = int(os.getenv("BAIF_VIDEO_MAX_DURATION_SECONDS", "900"))
FFMPEG_TIMEOUT_SECONDS = int(os.getenv("BAIF_FFMPEG_TIMEOUT_SECONDS", "1800"))
TTS_TIMEOUT_SECONDS = int(os.getenv("BAIF_TTS_TIMEOUT_SECONDS", "900"))
TTS_BACKEND = os.getenv("BAIF_TTS_BACKEND", "auto").strip().lower()
INDIC_PARLER_MODEL = os.getenv("BAIF_INDIC_PARLER_MODEL", str(MODEL_DIR / "indic-parler-tts"))
INDIC_PARLER_MODEL_ID = os.getenv("BAIF_INDIC_PARLER_MODEL_ID", "ai4bharat/indic-parler-tts")
INDIC_PARLER_DEVICE = os.getenv("BAIF_INDIC_PARLER_DEVICE", "auto").strip().lower()

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".aac",
    ".m4a",
    ".flac",
    ".wma",
    ".ogg",
}

COMPRESSED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".aac",
    ".m4a",
    ".wma",
    ".ogg",
}

UNCOMPRESSED_AUDIO_EXTENSIONS = {
    ".wav",
    ".flac",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".wmv",
    ".mkv",
    ".flv",
    ".webm",
}

TEXT_EXTENSIONS = {".txt", ".md", ".text"}

ALLOWED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | TEXT_EXTENSIONS

MODEL_PROFILE = os.getenv("BAIF_MODEL_PROFILE", "balanced").strip().lower()

MODEL_PROFILES = {
    "fast": {
        "label": "Fast CPU",
        "description": "Low-latency laptop/server mode for quick tests and short clips.",
        "whisper_repo": "Systran/faster-whisper-base",
        "whisper_dir": MODEL_DIR / "whisper" / "faster-whisper-base",
        "whisper_compute_type": "int8",
        "asr_beam_size": 3,
    },
    "balanced": {
        "label": "Balanced",
        "description": "Recommended default for provider CPU or small GPU machines.",
        "whisper_repo": "Systran/faster-whisper-small",
        "whisper_dir": MODEL_DIR / "whisper" / "faster-whisper-small",
        "whisper_compute_type": "int8",
        "asr_beam_size": 5,
    },
    "quality": {
        "label": "Production Quality",
        "description": "Highest open-source accuracy profile for provider/backend deployment.",
        "whisper_repo": "Systran/faster-whisper-large-v3",
        "whisper_dir": MODEL_DIR / "whisper" / "faster-whisper-large-v3",
        "whisper_compute_type": "auto",
        "asr_beam_size": 5,
    },
}

if MODEL_PROFILE not in MODEL_PROFILES:
    MODEL_PROFILE = "balanced"

ACTIVE_MODEL_PROFILE = MODEL_PROFILES[MODEL_PROFILE]

DEFAULT_WHISPER_MODEL = os.getenv("BAIF_WHISPER_MODEL", str(ACTIVE_MODEL_PROFILE["whisper_dir"]))
WHISPER_MODEL_ID = os.getenv("BAIF_WHISPER_MODEL_ID", str(ACTIVE_MODEL_PROFILE["whisper_repo"]))
WHISPER_DEVICE = os.getenv("BAIF_WHISPER_DEVICE", "auto")
WHISPER_COMPUTE_TYPE = os.getenv("BAIF_WHISPER_COMPUTE_TYPE", str(ACTIVE_MODEL_PROFILE["whisper_compute_type"]))
WHISPER_CPU_THREADS = int(os.getenv("BAIF_WHISPER_CPU_THREADS", "0"))
ASR_BEAM_SIZE = int(os.getenv("BAIF_ASR_BEAM_SIZE", str(ACTIVE_MODEL_PROFILE["asr_beam_size"])))
ASR_BEST_OF = int(os.getenv("BAIF_ASR_BEST_OF", "5"))
ASR_VAD_MIN_SILENCE_MS = int(os.getenv("BAIF_ASR_VAD_MIN_SILENCE_MS", "500"))
ASR_CONDITION_ON_PREVIOUS_TEXT = os.getenv("BAIF_ASR_CONDITION_ON_PREVIOUS_TEXT", "0") == "1"
ASR_NO_SPEECH_THRESHOLD = float(os.getenv("BAIF_ASR_NO_SPEECH_THRESHOLD", "0.65"))
ASR_LOG_PROB_THRESHOLD = float(os.getenv("BAIF_ASR_LOG_PROB_THRESHOLD", "-1.0"))
ASR_BACKEND = os.getenv("BAIF_ASR_BACKEND", "whisper").strip().lower()
INDIC_CONFORMER_MODEL = os.getenv(
    "BAIF_INDIC_CONFORMER_MODEL",
    str(MODEL_DIR / "indic-conformer-600m-multilingual"),
)
INDIC_CONFORMER_MODEL_ID = os.getenv(
    "BAIF_INDIC_CONFORMER_MODEL_ID",
    "ai4bharat/indic-conformer-600m-multilingual",
)
INDIC_CONFORMER_DECODER = os.getenv("BAIF_INDIC_CONFORMER_DECODER", "rnnt").strip().lower()
INDIC_CONFORMER_DEVICE = os.getenv("BAIF_INDIC_CONFORMER_DEVICE", "auto").strip().lower()

TRANSLATION_BACKEND = os.getenv("BAIF_TRANSLATION_BACKEND", "auto").lower()
ALLOW_PREVIEW_TRANSLATOR = os.getenv("BAIF_ALLOW_PREVIEW_TRANSLATOR", "0") == "1"
ALLOW_MODEL_DOWNLOAD = os.getenv("BAIF_ALLOW_MODEL_DOWNLOAD", "1") == "1"
ENABLE_HOSTED_TRANSLATION = os.getenv("BAIF_ENABLE_HOSTED_TRANSLATION", "1") == "1"
HOSTED_TRANSLATION_PROVIDER = os.getenv("BAIF_HOSTED_TRANSLATION_PROVIDER", "mymemory").lower()
HOSTED_TRANSLATION_TIMEOUT_SECONDS = int(os.getenv("BAIF_HOSTED_TRANSLATION_TIMEOUT_SECONDS", "20"))
MYMEMORY_EMAIL = os.getenv("BAIF_MYMEMORY_EMAIL", "")
TRANSLATION_BATCH_SIZE = int(os.getenv("BAIF_TRANSLATION_BATCH_SIZE", "8"))

INDICTRANS_MODEL_BY_DIRECTION = {
    "en-indic": os.getenv(
        "BAIF_INDICTRANS_EN_INDIC_MODEL",
        str(MODEL_DIR / "indictrans2" / "indictrans2-en-indic-1B"),
    ),
    "indic-en": os.getenv(
        "BAIF_INDICTRANS_INDIC_EN_MODEL",
        str(MODEL_DIR / "indictrans2" / "indictrans2-indic-en-1B"),
    ),
    "indic-indic": os.getenv(
        "BAIF_INDICTRANS_INDIC_INDIC_MODEL",
        str(MODEL_DIR / "indictrans2" / "indictrans2-indic-indic-1B"),
    ),
}

INDICTRANS_REPO_BY_DIRECTION = {
    "en-indic": os.getenv("BAIF_INDICTRANS_EN_INDIC_REPO", "ai4bharat/indictrans2-en-indic-1B"),
    "indic-en": os.getenv("BAIF_INDICTRANS_INDIC_EN_REPO", "ai4bharat/indictrans2-indic-en-1B"),
    "indic-indic": os.getenv("BAIF_INDICTRANS_INDIC_INDIC_REPO", "ai4bharat/indictrans2-indic-indic-1B"),
}

PIPER_BINARY = os.getenv("BAIF_PIPER_BINARY", "piper")
PIPER_MODEL_DIR = Path(os.getenv("BAIF_PIPER_MODEL_DIR", str(MODEL_DIR / "piper")))

FFMPEG_BINARY = os.getenv("BAIF_FFMPEG_BINARY", "ffmpeg")
FFPROBE_BINARY = os.getenv("BAIF_FFPROBE_BINARY", "ffprobe")


def ensure_directories() -> None:
    for directory in (TEMP_DIR, OUTPUT_DIR, MODEL_DIR, SAMPLE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
