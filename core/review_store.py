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
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("job_id") != job_id:
                raise ValueError("Review identity does not match its file.")
            versions_payload = payload.get("versions", [])
            if not isinstance(versions_payload, list):
                raise ValueError("Review versions must be a list.")
            versions = [ReviewVersion(**item) for item in versions_payload]
            record = ReviewRecord(
                job_id=payload["job_id"],
                status=payload.get("status", "draft"),
                versions=versions,
                approved_version=payload.get("approved_version"),
                approved_at=payload.get("approved_at"),
                approved_by=payload.get("approved_by"),
            )
            if record.status not in {"draft", "approved"}:
                raise ValueError("Review status is invalid.")
            if [item.version for item in record.versions] != list(range(1, len(record.versions) + 1)):
                raise ValueError("Review version sequence is invalid.")
            if record.approved_version is not None and record.approved_version not in {
                item.version for item in record.versions
            }:
                raise ValueError("Approved review version is missing.")
            return record
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            # Preserve corrupt state for diagnosis without allowing it to break the
            # trainer workflow or be silently overwritten on the next correction.
            suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            quarantine = path.with_name(f"{path.stem}.corrupt-{suffix}.json")
            try:
                path.replace(quarantine)
            except OSError:
                pass
            return ReviewRecord(job_id=job_id)

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
            if record.versions and record.versions[-1].corrected_text == corrected_text:
                return record
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
            already_approved = record.status == "approved" and record.approved_version == selected.version
            record.status = "approved"
            record.approved_version = selected.version
            if not already_approved or not record.approved_at:
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
            self._upsert_memory(
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

    def finalize(
        self,
        job_id: str,
        corrected_text: str,
        username: str,
        source_text: str,
        source_language: str,
        target_language: str,
        job_dir: Path,
    ) -> ReviewRecord:
        """Save and approve the exact visible correction as one locked action."""
        with self._lock:
            draft = self.save_correction(job_id, corrected_text, username, job_dir)
            if not draft.versions:
                raise ValueError("Save a corrected translation before approval.")
            return self.approve(
                job_id,
                draft.versions[-1].version,
                username,
                source_text,
                source_language,
                target_language,
                job_dir,
            )

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

    def _upsert_memory(self, record: MemoryRecord) -> None:
        rows: list[str] = []
        if self.memory_path.exists():
            for line in self.memory_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(existing, dict) and existing.get("source_hash") != record.source_hash:
                    rows.append(json.dumps(existing, ensure_ascii=False))
        rows.append(json.dumps(asdict(record), ensure_ascii=False))
        temporary = self.memory_path.with_suffix(".jsonl.tmp")
        temporary.write_text("\n".join(rows) + "\n", encoding="utf-8")
        temporary.replace(self.memory_path)

    @staticmethod
    def _merge_report_artifacts(job_dir: Path, artifacts: dict[str, str]) -> None:
        report_path = job_dir / "job_report.json"
        if not report_path.exists():
            return
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(report, dict):
            return
        report_artifacts = report.get("artifacts")
        if not isinstance(report_artifacts, dict):
            report_artifacts = {}
            report["artifacts"] = report_artifacts
        report_artifacts.update(artifacts)
        temporary = report_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(report_path)
