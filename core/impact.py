"""Privacy-safe operational impact summaries for trainers and judges."""

from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable


def build_impact_summary(records: Iterable, review_lookup: Callable[[str], object], storage_bytes: int) -> dict:
    records = list(records)
    status_counts = Counter(record.status for record in records)
    terminal = sum(status_counts[name] for name in ("succeeded", "failed", "cancelled"))
    succeeded = status_counts["succeeded"]
    input_counts: Counter[str] = Counter()
    direction_counts: Counter[str] = Counter()
    media_seconds = 0.0
    approved_jobs = 0
    correction_versions = 0
    reused_jobs = 0
    offline_packages = 0
    artifact_count = 0
    total_processing_seconds = 0.0

    for record in records:
        if record.status != "succeeded" or not record.result:
            continue
        result = record.result
        input_type = str(result.get("input_type") or record.kind or "unknown")
        source = str(result.get("source_language") or "Unknown")
        target = str(result.get("target_language") or "Unknown")
        input_counts[input_type] += 1
        direction_counts[f"{source} → {target}"] += 1
        metadata = result.get("metadata") or {}
        try:
            media_seconds += max(0.0, float(metadata.get("duration_seconds") or 0.0))
        except (TypeError, ValueError):
            pass
        if metadata.get("translation_backend") == "approved-memory":
            reused_jobs += 1
        artifacts = result.get("artifacts") or []
        artifact_keys = {
            str(item.get("key")) for item in artifacts if isinstance(item, dict) and item.get("key")
        }
        artifact_count += len(artifact_keys)
        offline_packages += int("bundle_zip" in artifact_keys)
        try:
            total_processing_seconds += max(0.0, float((record.stage_timings or {}).get("total") or 0.0))
        except (TypeError, ValueError):
            pass
        job_id = str(result.get("job_id") or record.job_id)
        review = review_lookup(job_id)
        correction_versions += len(getattr(review, "versions", []) or [])
        approved_jobs += int(getattr(review, "status", "") == "approved")

    return {
        "privacy": "Aggregated operational counts only; no source or translated content is included.",
        "jobs": {
            "total": len(records),
            "succeeded": succeeded,
            "failed": status_counts["failed"],
            "cancelled": status_counts["cancelled"],
            "queued": status_counts["queued"],
            "running": status_counts["running"],
            "success_rate_percent": round((succeeded / terminal * 100.0) if terminal else 0.0, 1),
        },
        "delivery": {
            "media_minutes": round(media_seconds / 60.0, 1),
            "offline_packages": offline_packages,
            "artifacts_created": artifact_count,
            "average_processing_seconds": round(total_processing_seconds / succeeded, 1) if succeeded else 0.0,
        },
        "review": {
            "approved_jobs": approved_jobs,
            "correction_versions": correction_versions,
            "approval_rate_percent": round((approved_jobs / succeeded * 100.0) if succeeded else 0.0, 1),
            "approved_memory_reuses": reused_jobs,
            "reuse_rate_percent": round((reused_jobs / succeeded * 100.0) if succeeded else 0.0, 1),
        },
        "input_types": dict(sorted(input_counts.items())),
        "language_directions": dict(sorted(direction_counts.items())),
        "storage_bytes": max(0, int(storage_bytes)),
    }
