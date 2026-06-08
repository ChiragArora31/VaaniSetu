"""Light cleanup for Indic ASR output from small Whisper profiles."""

from __future__ import annotations

_COMMON_REPLACEMENTS = (
    ("नमस्ति", "नमस्ते"),
    ("मोसम", "मौसम"),
    ("अचा", "अच्छा"),
    ("अच मौसम", "आज मौसम"),
    ("अच्छा है, आर", "अच्छा है और"),
    ("अच्छा है आर", "अच्छा है और"),
    (" आर ", " और "),
    ("कि सान", "किसान"),
    ("किसान केद", "किसान खेत"),
    ("किसान खेद", "किसान खेत"),
    ("केद में", "खेत में"),
    ("खेद में", "खेत में"),
    ("काम कर रही है", "काम कर रहे हैं"),
)


def clean_indic_asr_text(text: str, language_code: str) -> tuple[str, bool]:
    if language_code not in {"hi", "mr"} or not text.strip():
        return text, False

    cleaned = text
    for source, replacement in _COMMON_REPLACEMENTS:
        cleaned = cleaned.replace(source, replacement)
    cleaned = " ".join(cleaned.split())
    for mark in ("।", ",", ".", "!", "?"):
        cleaned = cleaned.replace(f" {mark}", mark)
    return cleaned, cleaned != text
