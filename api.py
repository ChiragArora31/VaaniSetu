from __future__ import annotations

from pathlib import Path
from typing import Annotated, Union
import json
import logging
import shutil
import threading
import time
import uuid

from fastapi import Cookie, Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
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
    SECURE_SESSION_COOKIE,
)
from core.auth import AuthError, AuthStore, SESSION_COOKIE_NAME, SESSION_TTL_SECONDS, SessionRecord, UserRecord
from core.file_utils import ValidationError, save_binary_upload
from core.health import collect_health_checks
from core.job_manager import JobManager, JobQueueFullError
from core.observability import configure_logging
from core.pipeline import PipelineError, PipelineResult, ProcessingOptions, TranslationPipeline
from core.review_store import ReviewRecord, ReviewStore
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
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
        "style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
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
auth_store = AuthStore(OUTPUT_DIR / ".auth" / "auth.json")
review_store = ReviewStore(OUTPUT_DIR / ".reviews")
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
    use_translation_memory: bool = True


class AuthRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=256)
    display_name: str = Field(default="", max_length=120)


class UserPublic(BaseModel):
    username: str
    display_name: str
    role: str
    status: str
    created_at: str
    approved_at: str | None = None
    approved_by: str | None = None
    deactivated_at: str | None = None


class SessionResponse(BaseModel):
    setup_required: bool
    user: UserPublic | None = None
    csrf_token: str | None = None


class AuthMessage(BaseModel):
    message: str


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


class ReviewVersionResponse(BaseModel):
    version: int
    created_at: str
    created_by: str
    artifact_key: str


class ReviewResponse(BaseModel):
    status: str
    versions: list[ReviewVersionResponse]
    approved_version: int | None = None
    approved_at: str | None = None
    approved_by: str | None = None


class CorrectionRequest(BaseModel):
    corrected_text: str = Field(min_length=1)


class ApprovalRequest(BaseModel):
    version: int | None = None


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
    stage_timings: dict[str, float] = Field(default_factory=dict)


class LibraryResponse(BaseModel):
    items: list[JobStatusResponse]
    storage_bytes: int


def _public_user(user: UserRecord) -> UserPublic:
    return UserPublic(
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        approved_at=user.approved_at,
        approved_by=user.approved_by,
        deactivated_at=user.deactivated_at,
    )


def _auth_exception(exc: AuthError, status_code: int = 401) -> HTTPException:
    return HTTPException(status_code=status_code, detail=str(exc))


def _set_session_cookie(response: Response, session: SessionRecord) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session.session_id,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=SECURE_SESSION_COOKIE,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")


def _session_response(user: UserRecord | None, session: SessionRecord | None = None) -> SessionResponse:
    return SessionResponse(
        setup_required=auth_store.setup_required(),
        user=_public_user(user) if user else None,
        csrf_token=session.csrf_token if session else None,
    )


def _client_throttle_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "local"


def require_user(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> tuple[UserRecord, SessionRecord]:
    try:
        return auth_store.authenticate(session_id)
    except AuthError as exc:
        raise _auth_exception(exc) from exc


def require_admin(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> tuple[UserRecord, SessionRecord]:
    try:
        return auth_store.require_admin(session_id)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=403 if "Admin" in str(exc) else 401) from exc


def require_csrf_user(
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> tuple[UserRecord, SessionRecord]:
    try:
        auth_store.require_csrf(auth[1], csrf_token)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=403) from exc
    return auth


def require_csrf_admin(
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_admin)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> tuple[UserRecord, SessionRecord]:
    try:
        auth_store.require_csrf(auth[1], csrf_token)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=403) from exc
    return auth


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
def metrics(_auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_admin)]):
    disk = shutil.disk_usage(OUTPUT_DIR)
    return {
        "uptime_seconds": round(time.monotonic() - started_at, 1),
        "jobs": job_manager.summary(),
        "worker_threads": JOB_WORKERS,
        "storage": {"mode": "local", "used_bytes": _storage_bytes(OUTPUT_DIR), "disk_free_bytes": disk.free},
    }


@app.get("/auth/session", response_model=SessionResponse)
def auth_session(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
):
    if not session_id:
        return _session_response(None)
    try:
        user, session = auth_store.authenticate(session_id)
    except AuthError:
        return _session_response(None)
    return _session_response(user, session)


@app.post("/auth/setup", response_model=SessionResponse)
def auth_setup(request: AuthRequest, response: Response):
    try:
        user, session = auth_store.create_first_admin(
            request.username,
            request.password,
            request.display_name,
        )
    except AuthError as exc:
        raise _auth_exception(exc, status_code=409 if "already" in str(exc) else 400) from exc
    _set_session_cookie(response, session)
    return _session_response(user, session)


@app.post("/auth/register", response_model=UserPublic, status_code=201)
def auth_register(request: AuthRequest):
    try:
        user = auth_store.register_user(request.username, request.password, request.display_name)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=400) from exc
    return _public_user(user)


@app.post("/auth/login", response_model=SessionResponse)
def auth_login(request: AuthRequest, fastapi_request: Request, response: Response):
    try:
        user, session = auth_store.login(
            request.username,
            request.password,
            throttle_key=_client_throttle_key(fastapi_request),
        )
    except AuthError as exc:
        raise _auth_exception(exc, status_code=429 if "Too many" in str(exc) else 401) from exc
    _set_session_cookie(response, session)
    return _session_response(user, session)


@app.post("/auth/logout", response_model=AuthMessage)
def auth_logout(
    response: Response,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
):
    auth_store.logout(session_id)
    _clear_session_cookie(response)
    return AuthMessage(message="Signed out.")


@app.get("/auth/users", response_model=list[UserPublic])
def auth_users(_auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_admin)]):
    return [_public_user(user) for user in auth_store.list_users()]


@app.post("/auth/users/{username}/approve", response_model=UserPublic)
def auth_approve_user(
    username: str,
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_admin)],
):
    try:
        user = auth_store.approve_user(username, admin_username=auth[0].username)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=404 if "not found" in str(exc).lower() else 400) from exc
    return _public_user(user)


@app.post("/auth/users/{username}/deactivate", response_model=UserPublic)
def auth_deactivate_user(
    username: str,
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_admin)],
):
    try:
        user = auth_store.deactivate_user(username, admin_username=auth[0].username)
    except AuthError as exc:
        raise _auth_exception(exc, status_code=404 if "not found" in str(exc).lower() else 400) from exc
    return _public_user(user)


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
        result=_fresh_job_response(record) if record.result else None,
        error=user_safe_error(record.error) if record.error else None,
        stage_timings=record.stage_timings,
    )


def _fresh_job_response(record) -> JobResponse:
    response = JobResponse.model_validate(record.result)
    output_job_id = response.job_id
    report_path = OUTPUT_DIR / output_job_id / "job_report.json"
    if not report_path.exists():
        return response
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return response
    artifacts = []
    for key, filename in sorted(report.get("artifacts", {}).items()):
        path = OUTPUT_DIR / output_job_id / str(filename)
        if path.exists():
            artifacts.append(
                Artifact(
                    key=str(key),
                    filename=path.name,
                    download_url=f"/jobs/{output_job_id}/artifacts/{key}",
                )
            )
    if artifacts:
        response.artifacts = artifacts
    return response


def _record_for_job_id(job_id: str):
    record = job_manager.get(job_id)
    if record:
        return record
    for candidate in job_manager.recent(1000):
        result = candidate.result or {}
        if str(result.get("job_id", "")) == job_id:
            return candidate
    return None


def _review_response(review: ReviewRecord) -> ReviewResponse:
    return ReviewResponse(
        status=review.status,
        versions=[
            ReviewVersionResponse(
                version=item.version,
                created_at=item.created_at,
                created_by=item.created_by,
                artifact_key=item.artifact_key,
            )
            for item in review.versions
        ],
        approved_version=review.approved_version,
        approved_at=review.approved_at,
        approved_by=review.approved_by,
    )


def _job_result_or_404(job_id: str) -> JobResponse:
    record = _record_for_job_id(job_id)
    if not record or not record.result:
        raise HTTPException(status_code=404, detail="Completed job not found")
    return _fresh_job_response(record)


def _storage_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def _matches_filter(record, query: str, input_type: str, source_language: str, target_language: str, status: str) -> bool:
    if status and record.status != status:
        return False
    result = record.result or {}
    if input_type and str(result.get("input_type", record.kind)) != input_type:
        return False
    if source_language and str(result.get("source_language", "")) != source_language:
        return False
    if target_language and str(result.get("target_language", "")) != target_language:
        return False
    if query:
        haystack = " ".join(
            [
                record.job_id,
                record.kind,
                str(result.get("input_type", "")),
                str(result.get("source_language", "")),
                str(result.get("target_language", "")),
                str(result.get("original_text", ""))[:500],
                str(result.get("translated_text", ""))[:500],
                " ".join(str(value) for value in result.get("metadata", {}).values()),
            ]
        ).lower()
        return query.lower() in haystack
    return True


@app.get("/jobs", response_model=list[JobStatusResponse])
def queued_jobs(
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
    limit: int = 20,
):
    return [_job_status(record) for record in job_manager.recent(max(1, min(limit, 50)))]


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def queued_job(
    job_id: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
):
    record = _record_for_job_id(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_status(record)


@app.get("/library", response_model=LibraryResponse)
def library(
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
    q: str = "",
    input_type: str = "",
    source_language: str = "",
    target_language: str = "",
    status: str = "",
    limit: int = 50,
):
    records = [
        record
        for record in job_manager.recent(max(1, min(limit, 200)))
        if _matches_filter(record, q.strip(), input_type, source_language, target_language, status)
    ]
    return LibraryResponse(items=[_job_status(record) for record in records], storage_bytes=_storage_bytes(OUTPUT_DIR))


@app.post("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
def cancel_job(
    job_id: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    existing = _record_for_job_id(job_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Job not found")
    record = job_manager.cancel(existing.job_id)
    return _job_status(record)


@app.post("/jobs/{job_id}/retry", response_model=JobAccepted, status_code=202)
def retry_job(
    job_id: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    previous = _job_result_or_404(job_id)
    if not previous.original_text.strip():
        raise HTTPException(status_code=422, detail="This job does not have reusable source text.")

    def task(status):
        with pipeline_lock:
            result = pipeline.process_text(
                previous.original_text,
                previous.source_language,
                previous.target_language,
                ProcessingOptions(
                    make_subtitles=any(artifact.key in {"srt", "vtt"} for artifact in previous.artifacts),
                    make_tts=False,
                    allow_preview_translation=False,
                    allow_model_download=False,
                ),
                status,
            )
        return _response(result).model_dump()

    try:
        return _accepted(job_manager.submit("retry", task))
    except JobQueueFullError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.delete("/jobs/{job_id}", response_model=AuthMessage)
def delete_job(
    job_id: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    record = _record_for_job_id(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    output_job_id = str((record.result or {}).get("job_id") or record.job_id)
    try:
        deleted = job_manager.delete(record.job_id, None)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    import shutil

    shutil.rmtree(OUTPUT_DIR / output_job_id, ignore_errors=True)
    review_store.delete(output_job_id)
    return AuthMessage(message="Job deleted.")


@app.get("/jobs/{job_id}/review", response_model=ReviewResponse)
def get_review(
    job_id: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
):
    job = _job_result_or_404(job_id)
    return _review_response(review_store.get_review(job.job_id))


@app.post("/jobs/{job_id}/review/corrections", response_model=ReviewResponse)
def save_correction(
    job_id: str,
    request: CorrectionRequest,
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    job = _job_result_or_404(job_id)
    try:
        review = review_store.save_correction(job.job_id, request.corrected_text, auth[0].username, OUTPUT_DIR / job.job_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _review_response(review)


@app.post("/jobs/{job_id}/review/approve", response_model=ReviewResponse)
def approve_correction(
    job_id: str,
    request: ApprovalRequest,
    auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    job = _job_result_or_404(job_id)
    try:
        review = review_store.approve(
            job.job_id,
            request.version,
            auth[0].username,
            job.original_text,
            job.source_language,
            job.target_language,
            OUTPUT_DIR / job.job_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _review_response(review)


@app.post("/jobs/text", response_model=JobAccepted, status_code=202)
def queue_text_translation(
    request: TextRequest,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    _validate_source_language(request.source_language)
    _validate_target_language(request.target_language)

    def task(status):
        with pipeline_lock:
            options = _options(
                make_subtitles=request.make_subtitles,
                make_tts=request.make_tts,
                allow_preview_translation=request.allow_preview_translation,
                allow_model_download=request.allow_model_download,
            )
            memory = None
            if request.use_translation_memory and request.source_language != "Auto detect":
                memory = review_store.find_memory(request.text, request.source_language, request.target_language)
            if memory:
                result = pipeline.process_approved_memory(
                    request.text,
                    memory.corrected_text,
                    request.source_language,
                    request.target_language,
                    {
                        "job_id": memory.job_id,
                        "version": memory.version,
                        "approved_at": memory.approved_at,
                    },
                    options,
                    status,
                )
            else:
                result = pipeline.process_text(
                    request.text,
                    request.source_language,
                    request.target_language,
                    options,
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
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
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
def history(
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
    limit: int = 10,
):
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
def translate_text(
    request: TextRequest,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
):
    _validate_source_language(request.source_language)
    _validate_target_language(request.target_language)
    try:
        with pipeline_lock:
            options = _options(
                make_subtitles=request.make_subtitles,
                make_tts=request.make_tts,
                allow_preview_translation=request.allow_preview_translation,
                allow_model_download=request.allow_model_download,
            )
            memory = None
            if request.use_translation_memory and request.source_language != "Auto detect":
                memory = review_store.find_memory(request.text, request.source_language, request.target_language)
            if memory:
                result = pipeline.process_approved_memory(
                    request.text,
                    memory.corrected_text,
                    request.source_language,
                    request.target_language,
                    {
                        "job_id": memory.job_id,
                        "version": memory.version,
                        "approved_at": memory.approved_at,
                    },
                    options,
                )
            else:
                result = pipeline.process_text(
                    request.text,
                    request.source_language,
                    request.target_language,
                    options,
                )
    except PipelineError as exc:
        raise HTTPException(status_code=422, detail=user_safe_error(str(exc))) from exc
    return _response(result)


@app.post("/translate/file", response_model=JobResponse)
async def translate_file(
    file: Annotated[UploadFile, File()],
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_csrf_user)],
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
    saved = None
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
    finally:
        if saved is not None:
            saved.path.unlink(missing_ok=True)
    return _response(result)


@app.get("/", include_in_schema=False)
def web_app():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.head("/", include_in_schema=False)
def web_app_head():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/jobs/{job_id}/artifacts/{artifact_key}")
def download_artifact(
    job_id: str,
    artifact_key: str,
    _auth: Annotated[tuple[UserRecord, SessionRecord], Depends(require_user)],
):
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
