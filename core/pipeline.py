"""End-to-end processing pipeline for text, audio, and video inputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from config.languages import get_language
from config.settings import (
    ALLOW_MODEL_DOWNLOAD,
    MODEL_PROFILE,
    MAX_MEDIA_SECONDS,
    MAX_TEXT_CHARS,
    OUTPUT_DIR,
    TEMP_DIR,
    WHISPER_MODEL_ID,
    ensure_directories,
)
from core.audio_extractor import extract_audio_to_wav
from core.asr_cleanup import clean_indic_asr_text
from core.export_utils import create_artifact_zip
from core.file_utils import create_job_dirs, write_text
from core.media_utils import MediaError, detect_input_type, inspect_media
from core.subtitles import Segment, normalize_segments, render_srt, render_vtt, segments_from_text
from core.text_utils import enforce_text_limit, normalize_text, split_for_translation
from core.transcriber import TranscriptionError, WhisperTranscriber
from core.translator import TranslationError, translate_segments
from core.tts import TTSError, convert_wav_to_mp3, synthesize_speech
from core.video_processor import burn_subtitles, mux_audio


StatusCallback = Callable[[str, float], None]


class PipelineError(RuntimeError):
    """Raised for recoverable end-to-end processing failures."""


@dataclass(frozen=True)
class ProcessingOptions:
    make_subtitles: bool = True
    make_tts: bool = False
    burn_captions: bool = False
    merge_translated_audio: bool = False
    allow_preview_translation: bool = False
    allow_model_download: bool = ALLOW_MODEL_DOWNLOAD


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


def _write_metadata(result: PipelineResult, output_dir: Path) -> None:
    payload = {
        "job_id": result.job_id,
        "input_type": result.input_type,
        "source_language": result.source_language,
        "target_language": result.target_language,
        "warnings": result.warnings,
        "metadata": result.metadata,
        "artifacts": {key: path.name for key, path in result.artifacts.items()},
    }
    result.artifacts["job_report"] = write_text(
        output_dir / "job_report.json",
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


def _finalize_artifacts(result: PipelineResult, output_dir: Path) -> None:
    _write_metadata(result, output_dir)
    result.artifacts["bundle_zip"] = create_artifact_zip(result.artifacts, output_dir / "vaanisetu_outputs.zip")


class TranslationPipeline:
    def __init__(self):
        ensure_directories()
        self.transcriber = WhisperTranscriber()

    def process_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, _temp_dir, output_dir = create_job_dirs(TEMP_DIR, OUTPUT_DIR)
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

    def process_file(
        self,
        input_path: Path,
        source_language: str,
        target_language: str,
        options: ProcessingOptions,
        status: StatusCallback | None = None,
    ) -> PipelineResult:
        job_id, temp_dir, output_dir = create_job_dirs(TEMP_DIR, OUTPUT_DIR)
        input_type = detect_input_type(input_path)
        result = PipelineResult(
            job_id=job_id,
            input_type=input_type,
            source_language=source_language,
            target_language=target_language,
        )
        result.metadata["model_download"] = "enabled" if options.allow_model_download else "disabled"
        result.metadata["model_profile"] = MODEL_PROFILE

        if input_type == "text":
            return self.process_text(input_path.read_text(encoding="utf-8"), source_language, target_language, options, status)

        try:
            _status(status, "Inspecting media...", 0.05)
            try:
                media_info = inspect_media(input_path)
                if media_info.has_audio is False:
                    raise PipelineError("This media file does not contain an audio stream.")
                if media_info.duration_seconds and media_info.duration_seconds > MAX_MEDIA_SECONDS:
                    raise PipelineError(
                        "Media is too long for this deployment configuration. Maximum duration is "
                        f"{MAX_MEDIA_SECONDS // 60} minutes."
                    )
                if media_info.duration_seconds:
                    result.metadata["duration_seconds"] = round(media_info.duration_seconds, 2)
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
            result.metadata["asr_model"] = WHISPER_MODEL_ID
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
