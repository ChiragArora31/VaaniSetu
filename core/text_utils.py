"""Text normalization and chunking helpers."""

from __future__ import annotations

import re
import textwrap


_MARATHI_HINTS = {
    "आहे",
    "आहेत",
    "आणि",
    "शेतकरी",
    "गाव",
    "माती",
    "पाणी",
    "महिला",
    "बैठक",
    "आरोग्य",
}

_HINDI_HINTS = {
    "है",
    "हैं",
    "और",
    "किसान",
    "गांव",
    "मिट्टी",
    "पानी",
    "महिला",
    "बैठक",
    "स्वास्थ्य",
}


def normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(line for line in lines if line).strip()


def split_for_translation(text: str, max_chars: int = 700) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    chunks: list[str] = []
    for paragraph in normalized.split("\n"):
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?।])\s+", paragraph)
        current = ""
        for sentence in sentences:
            if not sentence:
                continue
            candidate = f"{current} {sentence}".strip()
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append(current)
            if len(sentence) <= max_chars:
                current = sentence
            else:
                chunks.extend(
                    textwrap.wrap(
                        sentence,
                        width=max_chars,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                )
                current = ""
        if current:
            chunks.append(current)
    return [chunk for chunk in chunks if chunk.strip()]


def enforce_text_limit(text: str, max_chars: int) -> None:
    if len(text) > max_chars:
        raise ValueError(f"Text is too long. Maximum allowed length is {max_chars:,} characters.")


def detect_language_name(text: str) -> str:
    normalized = normalize_text(text).casefold()
    if not normalized:
        return "English"
    devanagari = len(re.findall(r"[\u0900-\u097F]", normalized))
    latin = len(re.findall(r"[a-z]", normalized))
    if devanagari == 0 or latin > devanagari:
        return "English"

    tokens = set(re.findall(r"[\u0900-\u097F]+", normalized))
    marathi_score = len(tokens & _MARATHI_HINTS)
    hindi_score = len(tokens & _HINDI_HINTS)
    return "Marathi" if marathi_score > hindi_score else "Hindi"
