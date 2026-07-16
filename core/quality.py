"""Deterministic translation safety checks and agriculture terminology support."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOSSARY = ROOT / "config" / "agriculture_glossary.json"

_URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>()]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_NUMBER_UNIT_RE = re.compile(
    r"(?<![\w])(?:₹\s*)?\d+(?:[.,]\d+)*(?:\s*(?:%|°[CF]|kg|mg|g|ml|l|km|cm|mm|m|ha|"
    r"litres|litre|liters|liter|acres|acre|किलो|किग्रा|ग्राम|लिटर|लीटर|हेक्टर|एकर))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProtectedText:
    text: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class QualityFinding:
    kind: str
    severity: str
    message: str


def protect_invariants(text: str) -> ProtectedText:
    """Replace values that must survive translation with model-resistant tokens."""
    spans: list[tuple[int, int, str]] = []
    for pattern in (_URL_RE, _EMAIL_RE, _NUMBER_UNIT_RE):
        for match in pattern.finditer(text):
            if not any(match.start() < end and match.end() > start for start, end, _ in spans):
                spans.append((match.start(), match.end(), match.group(0)))
    spans.sort()
    values: list[str] = []
    output: list[str] = []
    cursor = 0
    for start, end, value in spans:
        output.append(text[cursor:start])
        token = f"ZXQ{len(values):04d}QXZ"
        output.append(token)
        values.append(value)
        cursor = end
    output.append(text[cursor:])
    return ProtectedText("".join(output), tuple(values))


def restore_invariants(text: str, values: tuple[str, ...]) -> str:
    output = text
    for index, value in enumerate(values):
        token = f"ZXQ{index:04d}QXZ"
        flexible = re.compile(r"Z\s*X\s*Q\s*" + f"{index:04d}" + r"\s*Q\s*X\s*Z", re.IGNORECASE)
        output, count = flexible.subn(lambda _match, replacement=value: replacement, output)
        if count == 0 and value not in output:
            output = f"{output.rstrip()} {value}".strip()
    return output


def extract_invariants(text: str) -> list[str]:
    protected = protect_invariants(text)
    return list(protected.values)


def load_glossary(path: Path = DEFAULT_GLOSSARY) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def glossary_findings(source: str, translated: str, source_language: str, target_language: str, glossary: dict | None = None) -> list[QualityFinding]:
    glossary = glossary or load_glossary()
    findings: list[QualityFinding] = []
    for entry in glossary.get("terms", []):
        source_term = str(entry.get(source_language, "")).strip()
        target_term = str(entry.get(target_language, "")).strip()
        if not source_term or not target_term:
            continue
        if source_term.casefold() in source.casefold() and target_term.casefold() not in translated.casefold():
            findings.append(QualityFinding("terminology", "major", f"Expected glossary term '{target_term}' for '{source_term}'."))
    return findings


def script_ratio(text: str, language: str) -> float:
    letters = [character for character in text if character.isalpha()]
    if not letters:
        return 1.0
    if language in {"Hindi", "Marathi"}:
        matching = sum("\u0900" <= character <= "\u097f" for character in letters)
    else:
        matching = sum(("a" <= character.casefold() <= "z") for character in letters)
    return matching / len(letters)


def validate_translation(source: str, translated: str, source_language: str, target_language: str, *, check_glossary: bool = True) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    missing = [value for value in extract_invariants(source) if value not in translated]
    if missing:
        findings.append(QualityFinding("preservation", "critical", "Missing unchanged value(s): " + ", ".join(missing)))
    if source_language != target_language and " ".join(source.casefold().split()) == " ".join(translated.casefold().split()):
        findings.append(QualityFinding("untranslated", "critical", "Output is unchanged from the source."))
    script_text = translated
    for invariant in extract_invariants(source):
        script_text = script_text.replace(invariant, "")
    ratio = script_ratio(script_text, target_language)
    if ratio < 0.55:
        findings.append(QualityFinding("script", "critical", f"Only {ratio:.0%} of output letters use the expected {target_language} script."))
    if check_glossary:
        findings.extend(glossary_findings(source, translated, source_language, target_language))
    return findings
