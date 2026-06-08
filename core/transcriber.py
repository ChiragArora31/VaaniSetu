"""Offline speech-to-text wrapper around faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.settings import (
    ALLOW_MODEL_DOWNLOAD,
    ASR_BEAM_SIZE,
    ASR_BEST_OF,
    ASR_CONDITION_ON_PREVIOUS_TEXT,
    ASR_LOG_PROB_THRESHOLD,
    ASR_NO_SPEECH_THRESHOLD,
    ASR_VAD_MIN_SILENCE_MS,
    DEFAULT_WHISPER_MODEL,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS,
    WHISPER_DEVICE,
    WHISPER_MODEL_ID,
)
from core.subtitles import Segment


class TranscriptionError(RuntimeError):
    """Raised when transcription cannot be completed."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    segments: list[Segment]
    language: str | None


_SCRIPT_PROMPTS = {
    "hi": (
        "यह हिन्दी भाषण है। प्रतिलेखन केवल देवनागरी लिपि में करें। "
        "उर्दू, अरबी या रोमन लिपि का उपयोग न करें।"
    ),
    "mr": (
        "हे मराठी भाषण आहे. प्रतिलेखन फक्त देवनागरी लिपीत करा. "
        "उर्दू, अरबी किंवा रोमन लिपी वापरू नका."
    ),
    "en": "This is English speech. Transcribe clearly in English.",
}


class WhisperTranscriber:
    def __init__(
        self,
        model_path: str = DEFAULT_WHISPER_MODEL,
        model_id: str = WHISPER_MODEL_ID,
        device: str = WHISPER_DEVICE,
        compute_type: str = WHISPER_COMPUTE_TYPE,
        cpu_threads: int = WHISPER_CPU_THREADS,
        allow_model_download: bool = ALLOW_MODEL_DOWNLOAD,
    ):
        self.model_path = model_path
        self.model_id = model_id
        self.device = device
        self.compute_type = compute_type
        self.cpu_threads = cpu_threads
        self.allow_model_download = allow_model_download
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "faster-whisper is not installed. Run 'pip install -r requirements.txt' first."
            ) from exc

        path = Path(self.model_path)
        model_ref = self.model_path if path.exists() else self.model_id
        if not path.exists() and not self.allow_model_download:
            raise TranscriptionError(
                "Whisper model folder is missing. Download a faster-whisper model into "
                f"'{self.model_path}' or enable open-source model download."
            )
        try:
            kwargs = {
                "device": self.device,
                "compute_type": self.compute_type,
                "local_files_only": not self.allow_model_download,
            }
            if self.cpu_threads > 0:
                kwargs["cpu_threads"] = self.cpu_threads
            self._model = WhisperModel(model_ref, **kwargs)
        except Exception as exc:
            raise TranscriptionError(
                "Whisper model is not available. Install/cache the faster-whisper model or enable internet-backed "
                f"open-source model download. Tried: {model_ref}"
            ) from exc
        return self._model

    def transcribe(self, audio_path: Path, source_language_code: str) -> TranscriptionResult:
        model = self._load_model()
        try:
            result = self._transcribe_once(model, audio_path, source_language_code, vad_filter=True)
            if result.text:
                return result
            return self._transcribe_once(model, audio_path, source_language_code, vad_filter=False)
        except Exception as exc:
            raise TranscriptionError(f"Transcription failed: {exc}") from exc

    @staticmethod
    def _transcribe_once(
        model,
        audio_path: Path,
        source_language_code: str,
        vad_filter: bool,
    ) -> TranscriptionResult:
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=source_language_code,
            task="transcribe",
            initial_prompt=_SCRIPT_PROMPTS.get(source_language_code),
            vad_filter=vad_filter,
            vad_parameters={"min_silence_duration_ms": ASR_VAD_MIN_SILENCE_MS},
            beam_size=ASR_BEAM_SIZE,
            best_of=ASR_BEST_OF,
            condition_on_previous_text=ASR_CONDITION_ON_PREVIOUS_TEXT,
            no_speech_threshold=ASR_NO_SPEECH_THRESHOLD,
            log_prob_threshold=ASR_LOG_PROB_THRESHOLD,
            word_timestamps=False,
        )
        segments: list[Segment] = []
        transcript_parts: list[str] = []
        for segment in segments_iter:
            text = (segment.text or "").strip()
            if not text:
                continue
            segments.append(Segment(start=float(segment.start), end=float(segment.end), text=text))
            transcript_parts.append(text)
        return TranscriptionResult(
            text=" ".join(transcript_parts).strip(),
            segments=segments,
            language=getattr(info, "language", source_language_code),
        )
