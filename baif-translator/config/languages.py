"""Language metadata used across the translation pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    label: str
    code: str
    indictrans_code: str
    whisper_code: str
    piper_hint: str


SUPPORTED_LANGUAGES: dict[str, Language] = {
    "Marathi": Language(
        label="Marathi",
        code="mr",
        indictrans_code="mar_Deva",
        whisper_code="mr",
        piper_hint="mr",
    ),
    "Hindi": Language(
        label="Hindi",
        code="hi",
        indictrans_code="hin_Deva",
        whisper_code="hi",
        piper_hint="hi",
    ),
    "English": Language(
        label="English",
        code="en",
        indictrans_code="eng_Latn",
        whisper_code="en",
        piper_hint="en",
    ),
}


def language_names() -> list[str]:
    return list(SUPPORTED_LANGUAGES.keys())


def get_language(name: str) -> Language:
    try:
        return SUPPORTED_LANGUAGES[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported language: {name}") from exc
