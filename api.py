from __future__ import annotations

from pathlib import Path
from typing import Annotated, Union
import json
import logging
import threading
import time
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config.languages import language_names
from config.settings import (
    ACTIVE_MODEL_PROFILE,
    AUDIO_MAX_DURATION_SECONDS,
    BASE_DIR,
    COMPRESSED_AUDIO_MAX_UPLOAD_MB,
    DOCUMENT_MAX_UPLOAD_MB,
    JOB_WORKERS,
    MAX_PENDING_JOBS,
    MODEL_PROFILE,
    OUTPUT_DIR,
    TEXT_MAX_UPLOAD_MB,
    TEMP_DIR,
    UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB,
    VIDEO_MAX_DURATION_SECONDS,
    VIDEO_MAX_UPLOAD_MB,
    ensure_directories,
)
from core.file_utils import ValidationError, save_binary_upload
from core.health import collect_health_checks
from core.job_manager import JobManager, JobQueueFullError
from core.observability import configure_logging
from core.pipeline import PipelineError, PipelineResult, ProcessingOptions, TranslationPipeline
from core.user_messages import user_safe_error


ensure_directories()
configure_logging(OUTPUT_DIR / "logs")
logger = logging.getLogger("vaanisetu.api")
started_at = time.monotonic()

app = FastAPI(
    title="VaaniSetu BAIF Translation API",
    version="1.0.0",
    description="Open-source text/audio/video translation API for BAIF clients.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request, call_next):
    request_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request failure",
            extra={"event": "request_failed", "method": request.method, "path": request.url.path},
        )
        raise
    duration_ms = round((time.monotonic() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request completed",
        extra={
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

pipeline = TranslationPipeline()
pipeline_lock = threading.RLock()
job_manager = JobManager(
    OUTPUT_DIR / ".jobs",
    max_workers=JOB_WORKERS,
    max_pending=MAX_PENDING_JOBS,
)
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class TextRequest(BaseModel):
    text: str = Field(min_length=1)
    source_language: str = "English"
    target_language: str = "Hindi"
    make_subtitles: bool = True
    make_tts: bool = False
    allow_preview_translation: bool = False
    allow_model_download: bool = False


class Artifact(BaseModel):
    key: str
    filename: str
    download_url: str


class JobResponse(BaseModel):
    job_id: str
    input_type: str
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    warnings: list[str]
    metadata: dict[str, Union[str, int, float]]
    artifacts: list[Artifact]


class HistoryItem(BaseModel):
    created_at: str
    job_id: str
    input_type: str
    source_language: str
    target_language: str
    artifacts: dict[str, str]


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class JobAccepted(BaseModel):
    job_id: str
    status: str
    status_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    kind: str
    status: str
    progress: float
    message: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result: JobResponse | None = None
    error: str | None = None


def _validate_source_language(name: str) -> None:
    if name == "Auto detect":
        return
    if name not in language_names():
        raise HTTPException(status_code=400, detail=f"Unsupported language: {name}")


def _validate_target_language(name: str) -> None:
    if name not in language_names():
        raise HTTPException(status_code=400, detail=f"Unsupported language: {name}")


def _options(
    make_subtitles: bool,
    make_tts: bool,
    burn_captions: bool = False,
    merge_translated_audio: bool = False,
    allow_preview_translation: bool = False,
    allow_model_download: bool = True,
) -> ProcessingOptions:
    return ProcessingOptions(
        make_subtitles=make_subtitles,
        make_tts=make_tts or merge_translated_audio,
        burn_captions=burn_captions,
        merge_translated_audio=merge_translated_audio,
        allow_preview_translation=allow_preview_translation,
        allow_model_download=allow_model_download,
    )


def _response(result: PipelineResult) -> JobResponse:
    artifacts = [
        Artifact(
            key=key,
            filename=path.name,
            download_url=f"/jobs/{result.job_id}/artifacts/{key}",
        )
        for key, path in sorted(result.artifacts.items())
        if path.exists()
    ]
    return JobResponse(
        job_id=result.job_id,
        input_type=result.input_type,
        source_language=result.source_language,
        target_language=result.target_language,
        original_text=result.original_text,
        translated_text=result.translated_text,
        warnings=result.warnings,
        metadata=result.metadata,
        artifacts=artifacts,
    )


@app.get("/health")
def health(allow_model_download: bool = False):
    checks = collect_health_checks(allow_model_download=allow_model_download)
    checks_by_name = {check.name: check for check in checks}
    required_names = [
        "FFmpeg",
        "ffprobe",
        "faster-whisper package",
        "Whisper model",
        "Transformers package",
        "NLLB local translation",
        "PDF text extraction",
        "Automatic OCR",
    ]
    required_ok = all(checks_by_name[name].ok for name in required_names if name in checks_by_name)
    speech_ok = checks_by_name.get("Local speech fallback")
    piper_binary = checks_by_name.get("Piper binary")
    piper_voices = checks_by_name.get("Piper voices")
    espeak = checks_by_name.get("eSpeak NG")
    portable_speech_ready = bool(
        (piper_binary and piper_binary.ok and piper_voices and piper_voices.ok) or (espeak and espeak.ok)
    )
    quality_translation_ready = all(
        checks_by_name.get(f"IndicTrans2 {direction}") and checks_by_name[f"IndicTrans2 {direction}"].ok
        for direction in ("en-indic", "indic-en", "indic-indic")
    )
    return {
        "ok": required_ok,
        "speech_ready": bool(speech_ok and speech_ok.ok),
        "portable_speech_ready": portable_speech_ready,
        "quality_translation_ready": quality_translation_ready,
        "production_ready": required_ok and portable_speech_ready and quality_translation_ready,
        "model_profile": MODEL_PROFILE,
        "model_profile_detail": ACTIVE_MODEL_PROFILE["description"],
        "checks": [check.__dict__ for check in checks],
    }


@app.get("/metrics")
def metrics():
    return {
        "uptime_seconds": round(time.monotonic() - started_at, 1),
        "jobs": job_manager.summary(),
        "worker_threads": JOB_WORKERS,
        "storage": "local",
    }


def _accepted(record) -> JobAccepted:
    return JobAccepted(job_id=record.job_id, status=record.status, status_url=f"/jobs/{record.job_id}")


def _job_status(record) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=record.job_id,
        kind=record.kind,
        status=record.status,
        progress=record.progress,
        message=record.message,
        created_at=record.created_at,
        started_at=record.started_at,
        completed_at=record.completed_at,
        result=JobResponse.model_validate(record.result) if record.result else None,
        error=user_safe_error(record.error) if record.error else None,
    )


@app.get("/jobs", response_model=list[JobStatusResponse])
def queued_jobs(limit: int = 20):
    return [_job_status(record) for record in job_manager.recent(max(1, min(limit, 50)))]


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def queued_job(job_id: str):
    record = job_manager.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_status(record)


@app.post("/jobs/text", response_model=JobAccepted, status_code=202)
def queue_text_translation(request: TextRequest):
    _validate_source_language(request.source_language)
    _validate_target_language(request.target_language)

    def task(status):
        with pipeline_lock:
            result = pipeline.process_text(
                request.text,
                request.source_language,
                request.target_language,
                _options(
                    make_subtitles=request.make_subtitles,
                    make_tts=request.make_tts,
                    allow_preview_translation=request.allow_preview_translation,
                    allow_model_download=request.allow_model_download,
                ),
                status,
            )
        return _response(result).model_dump()

    try:
        return _accepted(job_manager.submit("text", task))
    except JobQueueFullError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.post("/jobs/file", response_model=JobAccepted, status_code=202)
async def queue_file_translation(
    file: Annotated[UploadFile, File()],
    source_language: Annotated[str, Form()] = "English",
    target_language: Annotated[str, Form()] = "Hindi",
    make_subtitles: Annotated[bool, Form()] = True,
    make_tts: Annotated[bool, Form()] = False,
    burn_captions: Annotated[bool, Form()] = False,
    merge_translated_audio: Annotated[bool, Form()] = False,
    allow_preview_translation: Annotated[bool, Form()] = False,
    allow_model_download: Annotated[bool, Form()] = False,
):
    _validate_source_language(source_language)
    _validate_target_language(target_language)
    try:
        saved = save_binary_upload(file.file, file.filename or "upload", TEMP_DIR / "queued_uploads")
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=user_safe_error(str(exc))) from exc

    def task(status):
        try:
            with pipeline_lock:
                result = pipeline.process_file(
                    saved.path,
                    source_language,
                    target_language,
                    _options(
                        make_subtitles=make_subtitles,
                        make_tts=make_tts,
                        burn_captions=burn_captions,
                        merge_translated_audio=merge_translated_audio,
                        allow_preview_translation=allow_preview_translation,
                        allow_model_download=allow_model_download,
                    ),
                    status,
                )
            return _response(result).model_dump()
        finally:
            saved.path.unlink(missing_ok=True)

    try:
        return _accepted(job_manager.submit("file", task))
    except JobQueueFullError as exc:
        saved.path.unlink(missing_ok=True)
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.get("/languages")
def languages():
    return {"languages": language_names()}


@app.get("/limits")
def limits():
    return {
        "audio": {
            "max_duration_seconds": AUDIO_MAX_DURATION_SECONDS,
            "compressed_max_mb": COMPRESSED_AUDIO_MAX_UPLOAD_MB,
            "uncompressed_max_mb": UNCOMPRESSED_AUDIO_MAX_UPLOAD_MB,
            "compressed_extensions": [".aac", ".m4a", ".mp3", ".ogg", ".wma"],
            "uncompressed_extensions": [".flac", ".wav"],
        },
        "video": {
            "max_duration_seconds": VIDEO_MAX_DURATION_SECONDS,
            "max_mb": VIDEO_MAX_UPLOAD_MB,
            "max_resolution": "1920x1080",
            "extensions": [".avi", ".flv", ".mkv", ".mov", ".mp4", ".webm", ".wmv"],
        },
        "text": {
            "max_mb": TEXT_MAX_UPLOAD_MB,
            "extensions": [".md", ".text", ".txt"],
        },
        "document": {
            "max_mb": DOCUMENT_MAX_UPLOAD_MB,
            "extensions": [".csv", ".docx", ".pdf", ".pptx", ".tsv", ".xlsx"],
            "ocr": "Scanned PDFs are detected and processed automatically with local OCR.",
        },
    }


@app.get("/history", response_model=HistoryResponse)
def history(limit: int = 10):
    manifest_path = OUTPUT_DIR / "manifest.jsonl"
    if not manifest_path.exists():
        return HistoryResponse(items=[])
    rows = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(
            HistoryItem(
                created_at=str(payload.get("created_at", "")),
                job_id=str(payload.get("job_id", "")),
                input_type=str(payload.get("input_type", "")),
                source_language=str(payload.get("source_language", "")),
                target_language=str(payload.get("target_language", "")),
                artifacts={str(key): str(value) for key, value in payload.get("artifacts", {}).items()},
            )
        )
    rows = [row for row in rows if row.job_id]
    return HistoryResponse(items=list(reversed(rows))[: max(1, min(limit, 50))])


@app.post("/translate/text", response_model=JobResponse)
def translate_text(request: TextRequest):
    _validate_source_language(request.source_language)
    _validate_target_language(request.target_language)
    try:
        with pipeline_lock:
            result = pipeline.process_text(
                request.text,
                request.source_language,
                request.target_language,
                _options(
                    make_subtitles=request.make_subtitles,
                    make_tts=request.make_tts,
                    allow_preview_translation=request.allow_preview_translation,
                    allow_model_download=request.allow_model_download,
                ),
            )
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=user_safe_error(str(exc))) from exc
    return _response(result)


@app.post("/translate/file", response_model=JobResponse)
async def translate_file(
    file: Annotated[UploadFile, File()],
    source_language: Annotated[str, Form()] = "English",
    target_language: Annotated[str, Form()] = "Hindi",
    make_subtitles: Annotated[bool, Form()] = True,
    make_tts: Annotated[bool, Form()] = False,
    burn_captions: Annotated[bool, Form()] = False,
    merge_translated_audio: Annotated[bool, Form()] = False,
    allow_preview_translation: Annotated[bool, Form()] = False,
    allow_model_download: Annotated[bool, Form()] = False,
):
    _validate_source_language(source_language)
    _validate_target_language(target_language)
    temp_upload_dir = TEMP_DIR / "api_uploads"
    try:
        saved = save_binary_upload(file.file, file.filename or "upload", temp_upload_dir)
        with pipeline_lock:
            result = pipeline.process_file(
                saved.path,
                source_language,
                target_language,
                _options(
                    make_subtitles=make_subtitles,
                    make_tts=make_tts,
                    burn_captions=burn_captions,
                    merge_translated_audio=merge_translated_audio,
                    allow_preview_translation=allow_preview_translation,
                    allow_model_download=allow_model_download,
                ),
            )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=user_safe_error(str(exc))) from exc
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=user_safe_error(str(exc))) from exc
    return _response(result)


@app.get("/", include_in_schema=False)
def web_app():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.head("/", include_in_schema=False)
def web_app_head():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/jobs/{job_id}/artifacts/{artifact_key}")
def download_artifact(job_id: str, artifact_key: str):
    job_dir = OUTPUT_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    report_path = job_dir / "job_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Job report not found")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    filename = report.get("artifacts", {}).get(artifact_key)
    if not filename:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = (job_dir / filename).resolve()
    if job_dir.resolve() not in path.parents:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing")
    return FileResponse(path, filename=path.name)
