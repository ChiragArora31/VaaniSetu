"""End-to-end processing pipeline for text, audio, and video inputs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from config.languages import get_language
from config.settings import (
    ALLOW_MODEL_DOWNLOAD,
    AUDIO_MAX_DURATION_SECONDS,
    MODEL_PROFILE,
    MAX_TEXT_CHARS,
    OUTPUT_DIR,
    TEMP_DIR,
    VIDEO_MAX_DURATION_SECONDS,
    ensure_directories,
)
from core.audio_extractor import extract_audio_to_wav
from core.asr_cleanup import clean_indic_asr_text
from core.document_processor import DocumentProcessingError, extract_document_text, write_document_exports
from core.export_utils import create_artifact_zip
from core.file_utils import ValidationError, create_job_dirs, write_text
from core.media_utils import MediaError, detect_input_type, inspect_media
from core.subtitles import Segment, normalize_segments, render_srt, render_vtt, segments_from_text
from core.text_utils import detect_language_name, enforce_text_limit, normalize_text, split_for_translation
from core.transcriber import TranscriptionError, get_transcriber
from core.translator import TranslationError, translate_segments
from core.tts import TTSError, convert_wav_to_mp3, synthesize_speech
from core.video_processor import burn_subtitles, mux_audio


StatusCallback = Callable[[str, float], None]


class PipelineError(RuntimeError):
    """Raised for recoverable end-to-end processing failures."""


def _job_dirs() -> tuple[str, Path, Path]:
    try:
        return create_job_dirs(TEMP_DIR, OUTPUT_DIR)
    except ValidationError as exc:
        raise PipelineError(str(exc)) from exc


@dataclass(frozen=True)
class ProcessingOptions:
    make_subtitles: bool = True
    make_tts: bool = False
    burn_captions: bool = False
    merge_translated_audio: bool = False
    allow_preview_translation: bool = False
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD
    auto_detect_source: bool = False


@dataclass
class PipelineResult:
    job_id: str
    input_type: str
    source_language: str
    target_language: str
    original_text: str = ""
    translated_text: str = ""
    translated_segments: list[Segment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, Path] = field(default_factory=dict)
    metadata: dict[str, str | int | float] = field(default_factory=dict)


def _status(callback: StatusCallback | None, message: str, progress: float) -> None:
    if callback:
        callback(message, progress)


def _split_translated_lines(text: str, count: int) -> list[str]:
    lines = text.splitlines()
    if len(lines) == count:
        return lines
    if count == 1:
        return [text.strip()]
    cleaned = [line.strip() for line in lines if line.strip()]
    if len(cleaned) >= count:
        return cleaned[: count - 1] + [" ".join(cleaned[count - 1 :])]
    if cleaned:
        return cleaned + [""] * (count - len(cleaned))
    return [text.strip()] + [""] * (count - 1)


def _has_meaningful_speech(text: str) -> bool:
    return bool(re.search(r"[\w\u0900-\u097F]", text))


def _resolved_source_language(text: str, source_language: str, result: PipelineResult) -> str:
    if source_language != "Auto detect":
        return source_language
    detected = detect_language_name(text)
    result.source_language = detected
    result.metadata["source_language_detection"] = detected
    return detected


def _effective_media_type(input_type: str, has_video: bool | None) -> str:
    if input_type == "video" and has_video is False:
        return "audio"
    return input_type


def _validate_media_constraints(input_type: str, media_info) -> str:
    effective_type = _effective_media_type(input_type, media_info.has_video)
    if media_info.has_audio is False:
        raise PipelineError("This media file does not contain an audio stream.")

    if media_info.duration_seconds:
        limit = AUDIO_MAX_DURATION_SECONDS if effective_type == "audio" else VIDEO_MAX_DURATION_SECONDS
        if media_info.duration_seconds > limit:
            minutes = limit // 60
            label = "audio" if effective_type == "audio" else "video"
            raise PipelineError(f"{label.capitalize()} is too long. Maximum supported duration is {minutes} minutes.")

    if effective_type == "video" and media_info.has_video:
        if media_info.height and media_info.height > 1080:
            raise PipelineError("Video resolution is too high. Please upload a 720p or 1080p video.")
        if media_info.width and media_info.width > 1920:
            raise PipelineError("Video resolution is too high. Please upload a 720p or 1080p video.")
    return effective_type


def _write_metadata(result: PipelineResult, output_dir: Path) -> None:
    result.artifacts["job_report"] = output_dir / "job_report.json"
    result.artifacts["bundle_zip"] = output_dir / "vaanisetu_outputs.zip"
    payload = {
        "job_id": result.job_id,
        "input_type": result.input_type,
        "source_language": result.source_language,
        "target_language": result.target_language,
        "warnings": result.warnings,
        "metadata": result.metadata,
        "artifacts": {key: path.name for key, path in result.artifacts.items()},
    }
    write_text(
        result.artifacts["job_report"],
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


def _finalize_artifacts(result: PipelineResult, output_dir: Path) -> None:
    _write_metadata(result, output_dir)
    create_artifact_zip(result.artifacts, result.artifacts["bundle_zip"])
    _append_reuse_manifest(result, output_dir)


def _append_reuse_manifest(result: PipelineResult, output_dir: Path) -> None:
    def artifact_ref(path: Path) -> str:
        try:
            return str(path.relative_to(output_dir.parent))
        except ValueError:
            return path.name

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job_id": result.job_id,
        "input_type": result.input_type,
        "source_language": result.source_language,
        "target_language": result.target_language,
        "metadata": result.metadata,
        "artifacts": {key: artifact_ref(path) for key, path in sorted(result.artifacts.items())},
    }
    manifest_path = output_dir.parent / "manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class TranslationPipeline:
    def __init__(self):
        ensure_directories()
        self.transcriber = get_transcriber()

    def process_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, _temp_dir, output_dir = _job_dirs()
        result = PipelineResult(
            job_id=job_id,
            input_type="text",
            source_language=source_language,
            target_language=target_language,
            original_text=normalize_text(text),
        )
        result.metadata["model_download"] = "enabled" if options.allow_model_download else "disabled"
        result.metadata["model_profile"] = MODEL_PROFILE
        if not result.original_text:
            raise PipelineError("Please enter text to translate.")
        source_language = _resolved_source_language(result.original_text, source_language, result)
        try:
            enforce_text_limit(result.original_text, MAX_TEXT_CHARS)
        except ValueError as exc:
            raise PipelineError(str(exc)) from exc

        _status(status, "Translating text with open-source model...", 0.35)
        try:
            chunks = split_for_translation(result.original_text)
            translated = translate_segments(
                chunks,
                source_language,
                target_language,
                allow_preview=options.allow_preview_translation,
                allow_model_download=options.allow_model_download,
            )
        except TranslationError as exc:
            raise PipelineError(str(exc)) from exc
        result.translated_text = translated.text
        result.metadata["translation_backend"] = translated.backend
        result.metadata["text_chunks"] = len(chunks)
        if translated.warning:
            result.warnings.append(translated.warning)

        _status(status, "Writing text outputs...", 0.75)
        result.artifacts["translated_txt"] = write_text(output_dir / "translated_text.txt", result.translated_text)
        result.artifacts["source_txt"] = write_text(output_dir / "source_text.txt", result.original_text)

        if options.make_subtitles:
            segments = segments_from_text(result.translated_text) or normalize_segments([], result.translated_text)
            result.translated_segments = segments
            result.artifacts["srt"] = write_text(output_dir / "translated_subtitles.srt", render_srt(segments))
            result.artifacts["vtt"] = write_text(output_dir / "translated_subtitles.vtt", render_vtt(segments))

        if options.make_tts:
            self._maybe_make_tts(result, output_dir)

        _finalize_artifacts(result, output_dir)
        _status(status, "Done.", 1.0)
        return result

    def process_approved_memory(
        self,
        source_text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
        provenance: dict[str, str | int],
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, _temp_dir, output_dir = _job_dirs()
        result = PipelineResult(
            job_id=job_id,
            input_type="text",
            source_language=source_language,
            target_language=target_language,
            original_text=normalize_text(source_text),
            translated_text=normalize_text(translated_text),
        )
        if not result.original_text or not result.translated_text:
            raise PipelineError("Approved translation memory entry is incomplete.")
        result.metadata["translation_backend"] = "approved-memory"
        result.metadata["model_download"] = "disabled"
        result.metadata["model_profile"] = MODEL_PROFILE
        for key, value in provenance.items():
            result.metadata[f"translation_memory_{key}"] = value
        result.warnings.append(
            "This output reused an exact approved correction from the local translation memory."
        )

        _status(status, "Reusing approved local correction...", 0.7)
        result.artifacts["translated_txt"] = write_text(output_dir / "translated_text.txt", result.translated_text)
        result.artifacts["source_txt"] = write_text(output_dir / "source_text.txt", result.original_text)
        if options.make_subtitles:
            segments = segments_from_text(result.translated_text) or normalize_segments([], result.translated_text)
            result.translated_segments = segments
            result.artifacts["srt"] = write_text(output_dir / "translated_subtitles.srt", render_srt(segments))
            result.artifacts["vtt"] = write_text(output_dir / "translated_subtitles.vtt", render_vtt(segments))
        if options.make_tts:
            self._maybe_make_tts(result, output_dir)
        _finalize_artifacts(result, output_dir)
        _status(status, "Done.", 1.0)
        return result

    def process_file(
        self,
        input_path: Path,
        source_language: str,
        target_language: str,
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, temp_dir, output_dir = _job_dirs()
        input_type = detect_input_type(input_path)
        result = PipelineResult(
            job_id=job_id,
            input_type=input_type,
            source_language=source_language,
            target_language=target_language,
        )
        result.metadata["model_download"] = "enabled" if options.allow_model_download else "disabled"
        result.metadata["model_profile"] = MODEL_PROFILE
        result.metadata["asr_backend"] = self.transcriber.__class__.__name__

        if input_type == "text":
            return self.process_text(input_path.read_text(encoding="utf-8"), source_language, target_language, options, status)

        if input_type == "document":
            return self.process_document(input_path, source_language, target_language, options, status)

        if source_language == "Auto detect":
            raise PipelineError(
                "Auto source-language detection is available for text and document files. "
                "Please choose Hindi, Marathi, or English for audio/video transcription quality."
            )

        try:
            _status(status, "Inspecting media...", 0.05)
            try:
                media_info = inspect_media(input_path)
                effective_type = _validate_media_constraints(input_type, media_info)
                result.metadata["effective_media_type"] = effective_type
                if media_info.duration_seconds:
                    result.metadata["duration_seconds"] = round(media_info.duration_seconds, 2)
                if media_info.width and media_info.height:
                    result.metadata["resolution"] = f"{media_info.width}x{media_info.height}"
                result.metadata["media_inspection"] = "ffprobe"
            except MediaError as exc:
                if input_type != "audio":
                    raise exc
                result.metadata["media_inspection"] = "extension-only"

            _status(status, "Preparing audio for transcription...", 0.15)
            try:
                transcription_input = extract_audio_to_wav(input_path, temp_dir)
                result.artifacts["extracted_wav"] = transcription_input
                result.metadata["audio_preparation"] = "ffmpeg-wav"
            except MediaError as exc:
                if input_type in {"audio", "video"}:
                    transcription_input = input_path
                    result.metadata["audio_preparation"] = "direct-media-decode"
                else:
                    raise exc

            _status(status, "Transcribing speech with open-source model...", 0.35)
            source = get_language(source_language)
            self.transcriber.allow_model_download = options.allow_model_download
            transcription = self.transcriber.transcribe(transcription_input, source.whisper_code)
            cleaned_text, did_cleanup = clean_indic_asr_text(transcription.text, source.whisper_code)
            result.original_text = cleaned_text
            if not _has_meaningful_speech(result.original_text):
                raise PipelineError(
                    "No clear speech was detected in this file. Please upload audio with audible speech; "
                    "music-only or heavily mixed songs may not contain transcribable spoken content."
                )
            try:
                enforce_text_limit(result.original_text, MAX_TEXT_CHARS)
            except ValueError as exc:
                raise PipelineError(f"Transcript is too long. {exc}") from exc
            result.artifacts["transcript_txt"] = write_text(output_dir / "source_transcript.txt", result.original_text)
            result.metadata["transcription_language"] = transcription.language or source.whisper_code
            result.metadata["transcript_segments"] = len(transcription.segments)
            result.metadata["asr_model"] = getattr(
                self.transcriber,
                "model_id",
                self.transcriber.__class__.__name__,
            )
            if did_cleanup:
                result.metadata["asr_cleanup"] = "enabled"

            _status(status, "Translating transcript segments...", 0.62)
            segment_texts = [
                clean_indic_asr_text(segment.text, source.whisper_code)[0] for segment in transcription.segments
            ] or [result.original_text]
            translated = translate_segments(
                segment_texts,
                source_language,
                target_language,
                allow_preview=options.allow_preview_translation,
                allow_model_download=options.allow_model_download,
            )
            result.metadata["translation_backend"] = translated.backend
            if translated.warning:
                result.warnings.append(translated.warning)

            translated_lines = _split_translated_lines(translated.text, len(segment_texts))
            result.translated_text = "\n".join(translated_lines).strip()
            result.artifacts["translated_txt"] = write_text(output_dir / "translated_text.txt", result.translated_text)

            base_segments = transcription.segments or normalize_segments([], result.original_text)
            result.translated_segments = [
                Segment(start=segment.start, end=segment.end, text=translated_lines[index] if index < len(translated_lines) else "")
                for index, segment in enumerate(base_segments)
            ]

            if options.make_subtitles:
                _status(status, "Generating SRT and VTT subtitles...", 0.78)
                result.artifacts["srt"] = write_text(output_dir / "translated_subtitles.srt", render_srt(result.translated_segments))
                result.artifacts["vtt"] = write_text(output_dir / "translated_subtitles.vtt", render_vtt(result.translated_segments))

            if options.make_tts:
                _status(status, "Synthesizing translated speech...", 0.86)
                self._maybe_make_tts(result, output_dir)

            if input_type == "video" and options.burn_captions and "srt" in result.artifacts:
                _status(status, "Burning translated captions into video...", 0.91)
                try:
                    result.artifacts["captioned_video"] = burn_subtitles(
                        input_path,
                        result.artifacts["srt"],
                        output_dir / "captioned_video.mp4",
                    )
                except MediaError as exc:
                    result.warnings.append(str(exc))

            if input_type == "video" and options.merge_translated_audio and "tts_wav" in result.artifacts:
                _status(status, "Merging translated audio into video...", 0.95)
                try:
                    source_video = result.artifacts.get("captioned_video", input_path)
                    result.artifacts["translated_video"] = mux_audio(
                        source_video,
                        result.artifacts["tts_wav"],
                        output_dir / "translated_audio_video.mp4",
                    )
                except MediaError as exc:
                    result.warnings.append(str(exc))

        except (MediaError, TranscriptionError, TranslationError, TTSError) as exc:
            raise PipelineError(str(exc)) from exc

        _finalize_artifacts(result, output_dir)
        _status(status, "Done.", 1.0)
        return result

    def process_document(
        self,
        input_path: Path,
        source_language: str,
        target_language: str,
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, _temp_dir, output_dir = _job_dirs()
        result = PipelineResult(
            job_id=job_id,
            input_type="document",
            source_language=source_language,
            target_language=target_language,
        )
        result.metadata["model_download"] = "enabled" if options.allow_model_download else "disabled"
        result.metadata["model_profile"] = MODEL_PROFILE
        result.metadata["source_filename"] = input_path.name
        result.metadata["document_extension"] = input_path.suffix.lower()

        try:
            _status(status, "Extracting document text...", 0.12)
            document = extract_document_text(input_path)
            result.metadata["document_kind"] = document.kind
            result.original_text = normalize_text(document.text)
            if document.warning:
                result.warnings.append(document.warning)
            if not result.original_text:
                raise PipelineError("No translatable text was found in this document.")
            source_language = _resolved_source_language(result.original_text, source_language, result)
            enforce_text_limit(result.original_text, MAX_TEXT_CHARS)

            _status(status, "Translating document text...", 0.52)
            chunks = split_for_translation(result.original_text)
            translated = translate_segments(
                chunks,
                source_language,
                target_language,
                allow_preview=options.allow_preview_translation,
                allow_model_download=options.allow_model_download,
            )
            result.translated_text = translated.text
            result.metadata["translation_backend"] = translated.backend
            result.metadata["text_chunks"] = len(chunks)
            if translated.warning:
                result.warnings.append(translated.warning)

            _status(status, "Writing translated document exports...", 0.82)
            result.artifacts["source_txt"] = write_text(output_dir / "source_document_text.txt", result.original_text)
            result.artifacts.update(write_document_exports(input_path, result.translated_text, output_dir))
            result.warnings.append(
                "Document export is format-preserving best effort for text content. "
                "Use the Markdown/TXT export for review, or reflow into the original BAIF template when exact layout is required."
            )

            if options.make_subtitles:
                segments = segments_from_text(result.translated_text) or normalize_segments([], result.translated_text)
                result.translated_segments = segments
                result.artifacts["srt"] = write_text(output_dir / "translated_subtitles.srt", render_srt(segments))
                result.artifacts["vtt"] = write_text(output_dir / "translated_subtitles.vtt", render_vtt(segments))

        except (DocumentProcessingError, TranslationError, ValueError) as exc:
            raise PipelineError(str(exc)) from exc

        _finalize_artifacts(result, output_dir)
        _status(status, "Done.", 1.0)
        return result

    def _maybe_make_tts(self, result: PipelineResult, output_dir: Path) -> None:
        target = get_language(result.target_language)
        try:
            wav_path, backend, warning = synthesize_speech(
                result.translated_text,
                target.piper_hint,
                output_dir / "translated_voice.wav",
            )
            result.artifacts["tts_wav"] = wav_path
            result.metadata["tts_backend"] = backend
            if warning:
                result.warnings.append(warning)
            try:
                result.artifacts["tts_mp3"] = convert_wav_to_mp3(wav_path, output_dir / "translated_voice.mp3")
            except TTSError as exc:
                result.warnings.append(str(exc))
        except TTSError as exc:
            result.metadata["tts_backend"] = "browser-fallback"
