"""User-facing error sanitization.

Backend dependency/model failures are provider operations concerns. They should
not leak installation commands or internal package names into the public UI.
"""

from __future__ import annotations


_BACKEND_SETUP_MARKERS = (
    "pip install",
    "requirements.txt",
    "dependencies are not installed",
    "model folder is missing",
    "model files are not available",
    "install/cache",
    "ffmpeg was not found",
    "ffprobe was not found",
    "piper tts was not found",
    "missing binary",
)


def user_safe_error(message: str) -> str:
    lowered = message.lower()
    if any(marker in lowered for marker in _BACKEND_SETUP_MARKERS):
        return (
            "The translation service is not fully ready on the server yet. "
            "Please try again shortly while the provider backend finishes preparing the required processing engine."
        )
    return message
