"""Small durable job queue for the CPU-only BAIF worker."""

from __future__ import annotations

import json
import logging
import threading
import uuid
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ProgressCallback = Callable[[str, float], None]
JobTask = Callable[[ProgressCallback], dict]
logger = logging.getLogger("vaanisetu.jobs")


class JobQueueFullError(RuntimeError):
    """Raised when the worker cannot safely accept more queued work."""


class JobCancelledError(RuntimeError):
    """Raised when a queued or running job is cooperatively cancelled."""


@dataclass
class JobRecord:
    job_id: str
    kind: str
    status: str = "queued"
    progress: float = 0.0
    message: str = "Waiting for the worker..."
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    result: dict | None = None
    error: str | None = None
    cancel_requested: bool = False
    stage_timings: dict[str, float] = field(default_factory=dict)


class JobManager:
    def __init__(self, state_dir: Path, max_workers: int = 1, max_pending: int = 20):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.max_pending = max(1, max_pending)
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix="vaanisetu")
        self._restore()

    def _path(self, job_id: str) -> Path:
        return self.state_dir / f"{job_id}.json"

    def _persist(self, record: JobRecord) -> None:
        target = self._path(record.job_id)
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)

    def _restore(self) -> None:
        for path in self.state_dir.glob("*.json"):
            try:
                record = JobRecord(**json.loads(path.read_text(encoding="utf-8")))
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                continue
            if record.status in {"queued", "running"}:
                record.status = "failed"
                record.error = "Processing was interrupted because the worker restarted. Please submit the item again."
                record.message = "Interrupted"
                record.completed_at = datetime.now(timezone.utc).isoformat()
                self._persist(record)
            self._jobs[record.job_id] = record

    def _pending_count(self) -> int:
        return sum(record.status in {"queued", "running"} for record in self._jobs.values())

    def submit(self, kind: str, task: JobTask) -> JobRecord:
        with self._lock:
            if self._pending_count() >= self.max_pending:
                raise JobQueueFullError("The worker queue is full. Please wait for an active translation to finish.")
            record = JobRecord(job_id=uuid.uuid4().hex[:12], kind=kind)
            self._jobs[record.job_id] = record
            self._persist(record)
            self._executor.submit(self._run, record.job_id, task)
            logger.info(
                "Job queued",
                extra={"event": "job_queued", "job_id": record.job_id, "kind": kind},
            )
            return record

    def _run(self, job_id: str, task: JobTask) -> None:
        run_started = time.monotonic()
        stage_started = run_started
        previous_stage = "startup"
        with self._lock:
            record = self._jobs[job_id]
            if record.cancel_requested:
                record.status = "cancelled"
                record.progress = 0.0
                record.message = "Cancelled"
                record.completed_at = datetime.now(timezone.utc).isoformat()
                self._persist(record)
                return
            record.status = "running"
            record.progress = max(record.progress, 0.01)
            record.message = "Starting processing..."
            record.started_at = datetime.now(timezone.utc).isoformat()
            self._persist(record)
            logger.info(
                "Job started",
                extra={"event": "job_started", "job_id": record.job_id, "kind": record.kind},
            )

        def update(message: str, progress: float) -> None:
            nonlocal stage_started, previous_stage
            with self._lock:
                current = self._jobs[job_id]
                if current.cancel_requested:
                    raise JobCancelledError("Translation was cancelled.")
                now = time.monotonic()
                current.stage_timings[previous_stage] = round(
                    current.stage_timings.get(previous_stage, 0.0) + (now - stage_started), 3
                )
                previous_stage = message.rstrip(".")[:80]
                stage_started = now
                current.progress = max(current.progress, min(0.99, max(0.0, float(progress))))
                current.message = message
                self._persist(current)

        try:
            result = task(update)
        except JobCancelledError as exc:
            with self._lock:
                record = self._jobs[job_id]
                record.stage_timings[previous_stage] = round(
                    record.stage_timings.get(previous_stage, 0.0) + (time.monotonic() - stage_started), 3
                )
                record.stage_timings["total"] = round(time.monotonic() - run_started, 3)
                record.status = "cancelled"
                record.message = "Cancelled"
                record.error = str(exc)
                record.completed_at = datetime.now(timezone.utc).isoformat()
                self._persist(record)
                logger.info(
                    "Job cancelled",
                    extra={"event": "job_cancelled", "job_id": record.job_id, "kind": record.kind},
                )
            return
        except Exception as exc:
            with self._lock:
                record = self._jobs[job_id]
                record.stage_timings[previous_stage] = round(
                    record.stage_timings.get(previous_stage, 0.0) + (time.monotonic() - stage_started), 3
                )
                record.stage_timings["total"] = round(time.monotonic() - run_started, 3)
                record.status = "failed"
                record.message = "Translation could not be completed."
                record.error = str(exc)
                record.completed_at = datetime.now(timezone.utc).isoformat()
                self._persist(record)
                logger.exception(
                    "Job failed",
                    extra={"event": "job_failed", "job_id": record.job_id, "kind": record.kind},
                )
            return

        with self._lock:
            record = self._jobs[job_id]
            record.stage_timings[previous_stage] = round(
                record.stage_timings.get(previous_stage, 0.0) + (time.monotonic() - stage_started), 3
            )
            record.stage_timings["total"] = round(time.monotonic() - run_started, 3)
            record.status = "succeeded"
            record.progress = 1.0
            record.message = "Translation ready"
            record.result = result
            record.completed_at = datetime.now(timezone.utc).isoformat()
            self._persist(record)
            logger.info(
                "Job completed",
                extra={"event": "job_completed", "job_id": record.job_id, "kind": record.kind},
            )

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def recent(self, limit: int = 20) -> list[JobRecord]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda record: record.created_at, reverse=True)[:limit]

    def summary(self) -> dict[str, int]:
        with self._lock:
            counts = {"queued": 0, "running": 0, "succeeded": 0, "failed": 0, "cancelled": 0}
            for record in self._jobs.values():
                if record.status in counts:
                    counts[record.status] += 1
            counts["capacity"] = self.max_pending
            return counts

    def cancel(self, job_id: str) -> JobRecord | None:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return None
            if record.status in {"succeeded", "failed", "cancelled"}:
                return record
            record.cancel_requested = True
            record.message = "Cancellation requested"
            if record.status == "queued":
                record.status = "cancelled"
                record.completed_at = datetime.now(timezone.utc).isoformat()
            self._persist(record)
            return record

    def delete(self, job_id: str, output_dir: Path | None = None) -> bool:
        with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return False
            if record.status in {"queued", "running"}:
                raise RuntimeError("Cancel the active job before deleting it.")
            self._jobs.pop(job_id, None)
            self._path(job_id).unlink(missing_ok=True)
        if output_dir:
            shutil.rmtree(output_dir / job_id, ignore_errors=True)
        return True

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)
