"""Durable human-review and approved translation-memory records."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core.export_utils import create_artifact_zip
from core.file_utils import write_text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_hash(text: str, source_language: str, target_language: str) -> str:
    payload = "\n".join([source_language.strip(), target_language.strip(), " ".join(text.split())])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ReviewVersion:
    version: int
    corrected_text: str
    created_at: str
    created_by: str
    artifact_key: str


@dataclass
class ReviewRecord:
    job_id: str
    status: str = "draft"
    versions: list[ReviewVersion] = field(default_factory=list)
    approved_version: int | None = None
    approved_at: str | None = None
    approved_by: str | None = None


@dataclass
class MemoryRecord:
    source_hash: str
    source_language: str
    target_language: str
    source_text: str
    corrected_text: str
    job_id: str
    version: int
    approved_at: str
    approved_by: str


class ReviewStore:
    def __init__(self, review_dir: Path):
        self.review_dir = review_dir
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.review_dir / "translation_memory.jsonl"
        self._lock = threading.RLock()

    def _review_path(self, job_id: str) -> Path:
        return self.review_dir / f"{job_id}.json"

    def _read_review(self, job_id: str) -> ReviewRecord:
        path = self._review_path(job_id)
        if not path.exists():
            return ReviewRecord(job_id=job_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        versions = [ReviewVersion(**item) for item in payload.get("versions", [])]
        return ReviewRecord(
            job_id=payload["job_id"],
            status=payload.get("status", "draft"),
            versions=versions,
            approved_version=payload.get("approved_version"),
            approved_at=payload.get("approved_at"),
            approved_by=payload.get("approved_by"),
        )

    def _write_review(self, record: ReviewRecord) -> None:
        path = self._review_path(record.job_id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def get_review(self, job_id: str) -> ReviewRecord:
        with self._lock:
            return self._read_review(job_id)

    def save_correction(
        self,
        job_id: str,
        corrected_text: str,
        username: str,
        job_dir: Path,
    ) -> ReviewRecord:
        corrected_text = corrected_text.strip()
        if not corrected_text:
            raise ValueError("Corrected translation cannot be empty.")
        if not job_dir.exists():
            raise FileNotFoundError("Job output folder is missing.")
        with self._lock:
            record = self._read_review(job_id)
            version_number = len(record.versions) + 1
            artifact_key = f"corrected_txt_v{version_number}"
            corrected_path = write_text(job_dir / f"corrected_translation_v{version_number}.txt", corrected_text)
            record.versions.append(
                ReviewVersion(
                    version=version_number,
                    corrected_text=corrected_text,
                    created_at=_now_iso(),
                    created_by=username,
                    artifact_key=artifact_key,
                )
            )
            record.status = "draft"
            self._write_review(record)
            self._merge_report_artifacts(job_dir, {artifact_key: corrected_path.name})
            return record

    def approve(
        self,
        job_id: str,
        version: int | None,
        username: str,
        source_text: str,
        source_language: str,
        target_language: str,
        job_dir: Path,
    ) -> ReviewRecord:
        with self._lock:
            record = self._read_review(job_id)
            if not record.versions:
                raise ValueError("Save a corrected translation before approval.")
            selected = record.versions[-1] if version is None else next(
                (item for item in record.versions if item.version == version),
                None,
            )
            if selected is None:
                raise ValueError("Correction version not found.")
            record.status = "approved"
            record.approved_version = selected.version
            record.approved_at = _now_iso()
            record.approved_by = username
            self._write_review(record)
            bundle_path = create_artifact_zip(
                {
                    selected.artifact_key: job_dir / f"corrected_translation_v{selected.version}.txt",
                    "job_report": job_dir / "job_report.json",
                },
                job_dir / "approved_corrected_package.zip",
            )
            self._merge_report_artifacts(job_dir, {"approved_corrected_package": bundle_path.name})
            self._append_memory(
                MemoryRecord(
                    source_hash=_source_hash(source_text, source_language, target_language),
                    source_language=source_language,
                    target_language=target_language,
                    source_text=source_text,
                    corrected_text=selected.corrected_text,
                    job_id=job_id,
                    version=selected.version,
                    approved_at=record.approved_at,
                    approved_by=username,
                )
            )
            return record

    def find_memory(self, source_text: str, source_language: str, target_language: str) -> MemoryRecord | None:
        key = _source_hash(source_text, source_language, target_language)
        match: MemoryRecord | None = None
        with self._lock:
            if not self.memory_path.exists():
                return None
            for line in self.memory_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    item = MemoryRecord(**json.loads(line))
                except (TypeError, json.JSONDecodeError):
                    continue
                if item.source_hash == key:
                    match = item
            return match

    def delete(self, job_id: str) -> None:
        with self._lock:
            self._review_path(job_id).unlink(missing_ok=True)
            if not self.memory_path.exists():
                return
            kept = []
            for line in self.memory_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("job_id") != job_id:
                    kept.append(json.dumps(item, ensure_ascii=False))
            self.memory_path.write_text(("\n".join(kept) + "\n") if kept else "", encoding="utf-8")

    def _append_memory(self, record: MemoryRecord) -> None:
        with self.memory_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    @staticmethod
    def _merge_report_artifacts(job_dir: Path, artifacts: dict[str, str]) -> None:
        report_path = job_dir / "job_report.json"
        if not report_path.exists():
            return
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        report.setdefault("artifacts", {}).update(artifacts)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
