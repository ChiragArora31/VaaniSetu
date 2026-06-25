from __future__ import annotations

from pathlib import Path
from typing import Annotated

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
from core.pipeline import PipelineError, PipelineResult, ProcessingOptions, TranslationPipeline
from core.user_messages import user_safe_error


ensure_directories()

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

pipeline = TranslationPipeline()
FRONTEND_DIR = BASE_DIR / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class TextRequest(BaseModel):
    text: str = Field(min_length=1)
    source_language: str = "English"
    target_language: str = "Hindi"
    make_subtitles: bool = True
    make_tts: bool = False
    allow_preview_translation: bool = False
    allow_model_download: bool = True


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
    metadata: dict[str, str | int | float]
    artifacts: list[Artifact]


def _validate_language(name: str) -> None:
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
def health(allow_model_download: bool = True):
    checks = collect_health_checks(allow_model_download=allow_model_download)
    return {
        "ok": all(check.ok for check in checks),
        "model_profile": MODEL_PROFILE,
        "model_profile_detail": ACTIVE_MODEL_PROFILE["description"],
        "checks": [check.__dict__ for check in checks],
    }


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
    }


@app.post("/translate/text", response_model=JobResponse)
def translate_text(request: TextRequest):
    _validate_language(request.source_language)
    _validate_language(request.target_language)
    try:
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
    allow_model_download: Annotated[bool, Form()] = True,
):
    _validate_language(source_language)
    _validate_language(target_language)
    temp_upload_dir = TEMP_DIR / "api_uploads"
    try:
        saved = save_binary_upload(file.file, file.filename or "upload", temp_upload_dir)
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

    import json

    report = json.loads(report_path.read_text(encoding="utf-8"))
    filename = report.get("artifacts", {}).get(artifact_key)
    if not filename:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = job_dir / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing")
    return FileResponse(path, filename=path.name)
