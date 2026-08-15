"""Validate approved BAIF media without copying its content into the repository.

The default inventory mode is fast and model-free.  It records only technical
metadata and file hashes.  ``--process-shortest`` additionally runs the
shortest valid video through the real local pipeline and records privacy-safe
provenance; transcripts and translations stay inside the ignored output job.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import OUTPUT_DIR
from core.file_utils import ValidationError, validate_size
from core.media_utils import MediaError, inspect_media
from core.pipeline import PipelineError, ProcessingOptions, TranslationPipeline, _validate_media_constraints
from scripts.verify_package import verify as verify_package


SUPPORTED_LANGUAGES = ("English", "Hindi", "Marathi")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_sample(path: Path, sample_root: Path) -> dict:
    relative = path.relative_to(sample_root).as_posix()
    record = {
        "file": relative,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "status": "failed",
        "issues": [],
    }
    try:
        validate_size(path.stat().st_size, path.suffix.lower())
        media = inspect_media(path)
        effective_type = _validate_media_constraints("video", media)
        if effective_type != "video":
            raise PipelineError("The file has no video stream.")
        record.update(
            {
                "duration_seconds": round(float(media.duration_seconds or 0), 3),
                "resolution": f"{media.width}x{media.height}" if media.width and media.height else "unknown",
                "has_audio": media.has_audio,
                "has_video": media.has_video,
                "status": "passed",
            }
        )
    except (ValidationError, MediaError, PipelineError, OSError) as exc:
        record["issues"].append(str(exc))
    return record


def inventory_samples(sample_root: Path) -> list[dict]:
    videos = sorted(path for path in sample_root.rglob("*") if path.is_file() and path.suffix.lower() == ".mp4")
    return [inspect_sample(path, sample_root) for path in videos]


def process_shortest(sample_root: Path, records: list[dict], source_language: str, target_language: str) -> dict:
    valid = [record for record in records if record["status"] == "passed"]
    if not valid:
        return {"status": "not_run", "reason": "No valid BAIF MP4 sample was available."}
    selected = min(valid, key=lambda item: (item.get("duration_seconds", float("inf")), item["file"]))
    source_path = sample_root / selected["file"]
    started = time.monotonic()
    stages: list[dict] = []

    def status(message: str, progress: float) -> None:
        stages.append({"at_seconds": round(time.monotonic() - started, 2), "progress": progress, "stage": message})
        print(f"[{progress:>4.0%}] {message}", flush=True)

    try:
        result = TranslationPipeline().process_file(
            source_path,
            source_language,
            target_language,
            ProcessingOptions(
                make_subtitles=True,
                make_tts=False,
                burn_captions=False,
                merge_translated_audio=False,
                allow_preview_translation=False,
                allow_model_download=False,
            ),
            status,
        )
        package = result.artifacts.get("bundle_zip")
        package_errors = verify_package(package) if package else ["Offline ZIP was not created."]
        return {
            "status": "passed" if not package_errors else "failed",
            "sample": selected["file"],
            "source_language": source_language,
            "target_language": target_language,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "job_id": result.job_id,
            "metadata": result.metadata,
            "warnings": result.warnings,
            "artifacts": sorted(result.artifacts),
            "offline_package_verified": not package_errors,
            "package_errors": package_errors,
            "stages": stages,
            "content_excluded": True,
        }
    except (PipelineError, OSError) as exc:
        return {
            "status": "failed",
            "sample": selected["file"],
            "source_language": source_language,
            "target_language": target_language,
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "error": str(exc),
            "stages": stages,
            "content_excluded": True,
        }


def build_report(
    sample_root: Path,
    records: list[dict],
    processing: dict | None = None,
) -> dict:
    passed = [record for record in records if record["status"] == "passed"]
    return {
        "schema_version": 1,
        "generated_at": _utc(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "privacy": (
            "Technical metadata, hashes and model provenance only. BAIF video, transcript and translation content "
            "are intentionally excluded."
        ),
        "sample_root_label": sample_root.name,
        "summary": {
            "found": len(records),
            "passed": len(passed),
            "failed": len(records) - len(passed),
            "total_bytes": sum(record["bytes"] for record in records),
            "total_duration_minutes": round(sum(record.get("duration_seconds", 0) for record in passed) / 60, 2),
            "resolutions": sorted({record["resolution"] for record in passed}),
        },
        "files": records,
        "processing": processing or {"status": "not_run", "reason": "Inventory-only validation requested."},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate approved BAIF sample videos and record privacy-safe evidence.")
    parser.add_argument("sample_root", type=Path, help="Folder containing BAIF-provided MP4 files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "baif_sample_validation.json",
        help="Privacy-safe JSON evidence path.",
    )
    parser.add_argument(
        "--process-shortest",
        action="store_true",
        help="Run the shortest valid video through local ASR, translation, subtitles and offline packaging.",
    )
    parser.add_argument("--source-language", choices=SUPPORTED_LANGUAGES, default="Marathi")
    parser.add_argument("--target-language", choices=SUPPORTED_LANGUAGES, default="Hindi")
    args = parser.parse_args()

    sample_root = args.sample_root.expanduser().resolve()
    if not sample_root.is_dir():
        parser.error(f"BAIF sample folder does not exist: {sample_root}")
    if args.source_language == args.target_language:
        parser.error("Source and target languages must be different.")

    records = inventory_samples(sample_root)
    if not records:
        parser.error(f"No MP4 files were found under: {sample_root}")
    processing = None
    if args.process_shortest:
        processing = process_shortest(sample_root, records, args.source_language, args.target_language)
    report = build_report(sample_root, records, processing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"BAIF sample validation: {report['summary']['passed']}/{report['summary']['found']} passed; "
        f"{report['summary']['total_duration_minutes']} minutes inspected."
    )
    print(f"Privacy-safe evidence: {args.output}")
    return 0 if report["summary"]["failed"] == 0 and report["processing"]["status"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
