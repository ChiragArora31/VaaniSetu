from __future__ import annotations

import base64
import io
import json
import tempfile
import threading
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

import api as api_module
from core.auth import AuthError, AuthStore, verify_password
from core.document_processor import DocumentProcessingError, extract_document_text
from core.export_utils import create_artifact_zip
from core.file_utils import ValidationError, save_binary_upload
from core.job_manager import JobManager, JobQueueFullError
from core.review_store import ReviewStore
from scripts.verify_package import verify as verify_package


class JobQueueAdversarialTest(unittest.TestCase):
    def test_cancellation_wins_race_with_task_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = JobManager(Path(directory), max_workers=1)
            task_started = threading.Event()
            allow_return = threading.Event()

            def task(_update):
                task_started.set()
                self.assertTrue(allow_return.wait(timeout=2))
                return {"translated_text": "must not be published"}

            record = manager.submit("text", task)
            self.assertTrue(task_started.wait(timeout=2))
            manager.cancel(record.job_id)
            allow_return.set()
            manager.shutdown()

            completed = manager.get(record.job_id)
            self.assertEqual(completed.status, "cancelled")
            self.assertIsNone(completed.result)

    def test_restore_rejects_record_whose_identity_does_not_match_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            state.mkdir()
            (state / "legitimate.json").write_text(
                json.dumps({"job_id": "../escaped", "kind": "text", "status": "running"}),
                encoding="utf-8",
            )
            (state / "poison.json").write_text(
                json.dumps({"job_id": "poison", "kind": "text", "status": []}),
                encoding="utf-8",
            )

            manager = JobManager(state)
            manager.shutdown()

            self.assertIsNone(manager.get("../escaped"))
            self.assertIsNone(manager.get("poison"))
            self.assertFalse((root / "escaped.json").exists())

    def test_non_json_task_results_become_durable_failures(self):
        for label, invalid_value in (("object", object()), ("non-finite number", float("nan"))):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                state = Path(directory)
                manager = JobManager(state, max_workers=1)
                record = manager.submit("text", lambda _update, value=invalid_value: {"invalid": value})
                manager.shutdown()

                completed = manager.get(record.job_id)
                self.assertEqual(completed.status, "failed")
                self.assertIn("serializable", completed.error.lower())
                persisted = json.loads((state / f"{record.job_id}.json").read_text(encoding="utf-8"))
                self.assertEqual(persisted["status"], "failed")

    def test_capacity_boundary_rejects_work_without_creating_orphan_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            manager = JobManager(state, max_workers=1, max_pending=1)
            task_started = threading.Event()
            allow_return = threading.Event()

            def blocking_task(_update):
                task_started.set()
                self.assertTrue(allow_return.wait(timeout=2))
                return {}

            accepted = manager.submit("text", blocking_task)
            self.assertTrue(task_started.wait(timeout=2))
            with self.assertRaises(JobQueueFullError):
                manager.submit("text", lambda _update: {})
            self.assertEqual(len(list(state.glob("*.json"))), 1)
            manager.cancel(accepted.job_id)
            allow_return.set()
            manager.shutdown()


class AuthenticationStateAdversarialTest(unittest.TestCase):
    def test_malformed_user_and_session_records_do_not_break_valid_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auth.json"
            store = AuthStore(path)
            admin, session = store.create_first_admin("admin", "correct horse battery")
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["users"]["broken"] = {"role": "admin"}
            payload["sessions"]["broken"] = {"username": "admin"}
            payload["sessions"]["poison"] = {
                "session_id": "poison",
                "username": "admin",
                "csrf_token": "token",
                "created_at": "not-a-number",
                "expires_at": session.expires_at,
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            restored = AuthStore(path)

            self.assertFalse(restored.setup_required())
            user, restored_session = restored.authenticate(session.session_id)
            self.assertEqual(user.username, admin.username)
            self.assertEqual(restored_session.session_id, session.session_id)
            self.assertNotIn("poison", restored._sessions)
            self.assertNotIn("broken", {item.username for item in restored.list_users()})

    def test_hostile_password_hash_cost_is_rejected_before_pbkdf2(self):
        encoded = "pbkdf2_sha256$999999999${}${}".format(
            base64.b64encode(b"salt").decode("ascii"),
            base64.b64encode(b"digest").decode("ascii"),
        )
        with patch("core.auth.hashlib.pbkdf2_hmac", side_effect=AssertionError("PBKDF2 must not run")):
            self.assertFalse(verify_password("irrelevant", encoded))

    def test_failure_cache_is_bounded_when_attacker_rotates_usernames(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AuthStore(Path(directory) / "auth.json")
            store.create_first_admin("admin", "correct horse battery")
            with patch("core.auth.MAX_LOGIN_FAILURE_KEYS", 3):
                for index in range(8):
                    with self.assertRaises(AuthError):
                        store.login(f"attacker{index}", "wrong password", throttle_key="same-client")
            self.assertLessEqual(len(store._failures), 3)

    def test_session_count_per_user_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AuthStore(Path(directory) / "auth.json")
            _, first_session = store.create_first_admin("admin", "correct horse battery")
            with patch("core.auth.MAX_SESSIONS_PER_USER", 2):
                store.login("admin", "correct horse battery")
                _, newest = store.login("admin", "correct horse battery")
            self.assertEqual(len(store._sessions), 2)
            with self.assertRaises(AuthError):
                store.authenticate(first_session.session_id)
            self.assertEqual(store.authenticate(newest.session_id)[0].username, "admin")


class UploadAdversarialTest(unittest.TestCase):
    def test_stream_failure_removes_partial_upload(self):
        class FailingStream:
            def __init__(self):
                self.calls = 0

            def seek(self, _offset):
                return None

            def read(self, _size):
                self.calls += 1
                if self.calls == 1:
                    return b"partial"
                raise OSError("simulated read failure")

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with self.assertRaisesRegex(OSError, "simulated"):
                save_binary_upload(FailingStream(), "training.txt", target)
            self.assertEqual(list(target.iterdir()), [])

    def test_extreme_filename_is_bounded_and_remains_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = save_binary_upload(io.BytesIO(b"safe"), ("a" * 400) + ".txt", Path(directory))
            self.assertLessEqual(len(saved.path.name.encode("utf-8")), 255)
            self.assertEqual(saved.path.read_bytes(), b"safe")

    def test_malformed_filename_is_rejected_without_filesystem_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with self.assertRaises(ValidationError):
                save_binary_upload(io.BytesIO(b"safe"), "invalid\x00.txt", target)
            self.assertEqual(list(target.iterdir()), [])


class OfflinePackageAdversarialTest(unittest.TestCase):
    def test_packager_rejects_duplicate_archive_filenames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "one" / "translation.txt"
            second = root / "two" / "translation.txt"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("first", encoding="utf-8")
            second.write_text("second", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate"):
                create_artifact_zip({"first": first, "second": second}, root / "package.zip")

    def test_verifier_rejects_duplicate_members_even_when_content_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "translation.txt"
            artifact.write_text("safe", encoding="utf-8")
            package = create_artifact_zip({"translated_txt": artifact}, root / "package.zip")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(package, "a") as archive:
                    archive.writestr("translation.txt", b"safe")

            failures = verify_package(package)

            self.assertTrue(any("duplicate" in failure.lower() for failure in failures), failures)

    def test_verifier_does_not_read_member_above_resource_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "translation.txt"
            artifact.write_bytes(b"01234567890")
            package = create_artifact_zip({"translated_txt": artifact}, root / "package.zip")

            with patch("scripts.verify_package.MAX_PACKAGE_MEMBER_BYTES", 10, create=True):
                failures = verify_package(package)

            self.assertTrue(any("too large" in failure.lower() for failure in failures), failures)

    def test_verifier_rejects_malformed_manifest_and_unsafe_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = {
                "missing manifest": {"translation.txt": b"safe"},
                "invalid structure": {"integrity_manifest.json": b"[]"},
                "invalid record": {
                    "integrity_manifest.json": json.dumps({"files": ["not-an-object"]}).encode("utf-8")
                },
                "unsafe path": {
                    "../escape.txt": b"unsafe",
                    "integrity_manifest.json": json.dumps({"files": []}).encode("utf-8"),
                },
            }
            for index, (label, members) in enumerate(cases.items()):
                package = root / f"malformed-{index}.zip"
                with zipfile.ZipFile(package, "w") as archive:
                    for name, data in members.items():
                        archive.writestr(name, data)
                with self.subTest(label=label):
                    self.assertTrue(verify_package(package))


class DocumentArchiveAdversarialTest(unittest.TestCase):
    def test_office_extractor_rejects_oversized_xml_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.docx"
            xml = b'<w:document xmlns:w="urn:test"><w:t>content</w:t></w:document>'
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)

            with patch("core.document_processor.MAX_OFFICE_MEMBER_BYTES", 10, create=True):
                with self.assertRaisesRegex(DocumentProcessingError, "large"):
                    extract_document_text(path)

    def test_office_extractor_rejects_duplicate_members(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ambiguous.docx"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("word/document.xml", b'<w:document xmlns:w="urn:test"><w:t>first</w:t></w:document>')
                    archive.writestr("word/document.xml", b'<w:document xmlns:w="urn:test"><w:t>second</w:t></w:document>')
            with self.assertRaisesRegex(DocumentProcessingError, "duplicate"):
                extract_document_text(path)


class ApiFilesystemAdversarialTest(unittest.TestCase):
    def test_artifact_download_rejects_parent_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "outputs"
            output.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("secret", encoding="utf-8")
            (outside / "job_report.json").write_text(
                json.dumps({"artifacts": {"secret": "secret.txt"}}),
                encoding="utf-8",
            )
            (output / "linked").symlink_to(outside, target_is_directory=True)
            previous_output = api_module.OUTPUT_DIR
            api_module.OUTPUT_DIR = output
            try:
                for job_id in ("..", "linked"):
                    with self.subTest(job_id=job_id), self.assertRaises(HTTPException) as raised:
                        api_module.download_artifact(job_id, "secret", (None, None))
                    self.assertEqual(raised.exception.status_code, 404)
            finally:
                api_module.OUTPUT_DIR = previous_output

    def test_corrupt_report_and_history_state_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "outputs"
            job_dir = output / "job123"
            job_dir.mkdir(parents=True)
            report = job_dir / "job_report.json"
            report.write_text("{not-json", encoding="utf-8")
            (output / "manifest.jsonl").write_text(
                "not-json\n[]\n" + json.dumps({"job_id": "safe", "artifacts": []}) + "\n",
                encoding="utf-8",
            )
            previous_output = api_module.OUTPUT_DIR
            api_module.OUTPUT_DIR = output
            try:
                with self.assertRaises(HTTPException) as raised:
                    api_module.download_artifact("job123", "translation", (None, None))
                self.assertEqual(raised.exception.status_code, 409)
                history = api_module.history((None, None), limit=10)
                self.assertEqual([item.job_id for item in history.items], ["safe"])
                self.assertEqual(history.items[0].artifacts, {})
            finally:
                api_module.OUTPUT_DIR = previous_output


class ReviewStateAdversarialTest(unittest.TestCase):
    def test_corrupt_review_is_quarantined_and_workflow_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reviews = root / ".reviews"
            reviews.mkdir()
            (reviews / "job123.json").write_text(
                json.dumps({"job_id": "different", "status": "approved", "versions": []}),
                encoding="utf-8",
            )
            job_dir = root / "job123"
            job_dir.mkdir()
            (job_dir / "job_report.json").write_text(json.dumps({"artifacts": {}}), encoding="utf-8")

            store = ReviewStore(reviews)
            recovered = store.get_review("job123")
            self.assertEqual(recovered.status, "draft")
            self.assertEqual(recovered.versions, [])
            self.assertEqual(len(list(reviews.glob("job123.corrupt-*.json"))), 1)

            saved = store.save_correction("job123", "सुरक्षित सुधार", "trainer", job_dir)
            self.assertEqual(saved.versions[0].corrected_text, "सुरक्षित सुधार")
            self.assertTrue((reviews / "job123.json").is_file())
