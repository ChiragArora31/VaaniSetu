"""Subtitle segment models and SRT/VTT rendering."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import textwrap


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


def normalize_segments(segments: list[Segment], fallback_text: str = "") -> list[Segment]:
    if segments:
        return segments
    text = fallback_text.strip()
    if not text:
        return []
    seconds = max(5.0, min(30.0, len(text) / 16.0))
    return [Segment(start=0.0, end=seconds, text=text)]


def subtitle_safe_text(text: str, line_width: int = 42, max_lines: int = 2) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""
    wrapped = textwrap.wrap(clean, width=line_width, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) <= max_lines:
        return "\n".join(wrapped)
    kept = wrapped[:max_lines]
    kept[-1] = kept[-1].rstrip(". ") + "..."
    return "\n".join(kept)


def segments_from_text(text: str, seconds_per_segment: float = 5.0) -> list[Segment]:
    chunks = textwrap.wrap(
        " ".join(text.split()),
        width=84,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if not chunks:
        return []
    segments: list[Segment] = []
    for index, chunk in enumerate(chunks):
        start = index * seconds_per_segment
        segments.append(Segment(start=start, end=start + seconds_per_segment, text=chunk))
    return segments


def _format_srt_time(seconds: float) -> str:
    millis = int(round(max(seconds, 0.0) * 1000))
    hours, rem = divmod(millis, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def _format_vtt_time(seconds: float) -> str:
    return _format_srt_time(seconds).replace(",", ".")


def render_srt(segments: list[Segment]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = subtitle_safe_text(segment.text)
        if not text:
            continue
        blocks.append(
            f"{index}\n"
            f"{_format_srt_time(segment.start)} --> {_format_srt_time(segment.end)}\n"
            f"{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_vtt(segments: list[Segment]) -> str:
    blocks = ["WEBVTT\n"]
    for segment in segments:
        text = escape(subtitle_safe_text(segment.text))
        if not text:
            continue
        blocks.append(f"{_format_vtt_time(segment.start)} --> {_format_vtt_time(segment.end)}\n{text}")
    return "\n\n".join(blocks) + ("\n" if len(blocks) > 1 else "")
