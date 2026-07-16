from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
import time
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BAIF_MIN_FREE_DISK_GB", "1")

import api as api_module
from core.auth import AuthError, AuthStore
from core.file_utils import ValidationError, save_binary_upload, validate_size
from core.job_manager import JobManager
from core.observability import JsonFormatter
from core.quality import glossary_findings, protect_invariants, restore_invariants, validate_translation
from core.export_utils import create_artifact_zip
from core.asr_cleanup import clean_indic_asr_text
from core.document_processor import DocumentProcessingError, extract_document_text
from core.media_utils import MediaInfo
from core.pipeline import ProcessingOptions, TranslationPipeline, _validate_media_constraints
from core.review_store import ReviewStore
from core.subtitles import Segment, render_srt, render_vtt, segments_from_text, subtitle_safe_text
from core.text_utils import detect_language_name, normalize_text, split_for_translation
from core.translator import HostedHttpTranslator, TranslationError
from scripts.verify_package import verify as verify_package
from core.user_messages import user_safe_error
from core.transcriber import WhisperTranscriber, get_transcriber


class TextUtilsTest(unittest.TestCase):
    def test_normalize_and_split_for_translation(self):
        text = " hello   farmer water\n\nThis is a long sentence. " * 20
        normalized = normalize_text(text)
        chunks = split_for_translation(normalized, max_chars=120)
        self.assertTrue(chunks)
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks))
        self.assertNotIn("  ", normalized)

    def test_clean_indic_asr_text(self):
        cleaned, changed = clean_indic_asr_text(
            "नमस्ति, अच मोसम अचा है, आर कि सान केद में काम कर रही है।",
            "hi",
        )
        self.assertTrue(changed)
        self.assertIn("नमस्ते", cleaned)
        self.assertIn("आज मौसम अच्छा है और किसान खेत में काम कर रहे हैं", cleaned)

    def test_detect_language_name(self):
        self.assertEqual(detect_language_name("The farmer needs clean water."), "English")
        self.assertEqual(detect_language_name("किसान खेत में काम कर रहे हैं।"), "Hindi")
        self.assertEqual(detect_language_name("शेतकरी माती आणि पाणी तपासत आहेत."), "Marathi")


class TranslationQualityTest(unittest.TestCase):
    def test_protects_and_restores_numbers_units_urls_and_email(self):
        source = "Apply 25 kg on 2.5 acres; see https://baif.org or ask field@example.org."
        protected = protect_invariants(source)
        self.assertNotIn("25 kg", protected.text)
        restored = restore_invariants("Translated " + protected.text, protected.values)
        for value in ("25 kg", "2.5 acres", "https://baif.org", "field@example.org"):
            self.assertIn(value, restored)

    def test_translation_gate_finds_missing_values_wrong_script_and_glossary(self):
        findings = validate_translation("Apply 25 kg compost", "apply compost", "English", "Hindi")
        kinds = {finding.kind for finding in findings}
        self.assertIn("preservation", kinds)
        self.assertIn("script", kinds)
        self.assertIn("terminology", kinds)

    def test_glossary_accepts_expected_term(self):
        self.assertEqual(glossary_findings("Use drip irrigation", "ठिबक सिंचन वापरा", "English", "Marathi"), [])


class SubtitleTest(unittest.TestCase):
    def test_subtitle_rendering(self):
        segments = [Segment(0, 1.25, "hello world"), Segment(1.25, 3.5, "farmer water")]
        srt = render_srt(segments)
        vtt = render_vtt(segments)
        self.assertIn("00:00:00,000 --> 00:00:01,250", srt)
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertIn("farmer water", vtt)

    def test_subtitle_safe_text_caps_long_lines(self):
        text = " ".join(["agriculture"] * 20)
        safe = subtitle_safe_text(text, line_width=20, max_lines=2)
        self.assertLessEqual(len(safe.splitlines()), 2)

    def test_segments_from_text(self):
        segments = segments_from_text("hello farmer water " * 20)
        self.assertGreater(len(segments), 1)
        self.assertEqual(segments[0].start, 0)


class FileUtilsTest(unittest.TestCase):
    def test_rejects_bad_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValidationError):
                save_binary_upload(io.BytesIO(b"bad"), "payload.exe", Path(directory))

    def test_saves_supported_file(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = save_binary_upload(io.BytesIO(b"hello"), "notes.txt", Path(directory))
            self.assertEqual(saved.extension, ".txt")
            self.assertTrue(saved.path.exists())

    def test_saves_supported_document_file(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = save_binary_upload(io.BytesIO(b"Name,Value\nFarmer,Water"), "training.csv", Path(directory))
            self.assertEqual(saved.extension, ".csv")
            self.assertTrue(saved.path.exists())

    def test_enforces_baif_file_size_limits_by_media_type(self):
        with self.assertRaises(ValidationError):
            validate_size((50 * 1024 * 1024) + 1, ".mp3")
        validate_size(150 * 1024 * 1024, ".wav")
        with self.assertRaises(ValidationError):
            validate_size((200 * 1024 * 1024) + 1, ".mp4")

    def test_safe_filename_removes_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = save_binary_upload(io.BytesIO(b"safe"), "../../private.txt", Path(directory))
            self.assertEqual(saved.path.parent, Path(directory))
            self.assertEqual(saved.path.name, "private.txt")


class OfflinePackageTest(unittest.TestCase):
    def test_integrity_verifier_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "translation.txt"
            artifact.write_text("नमस्ते", encoding="utf-8")
            package = create_artifact_zip({"translated_txt": artifact}, root / "package.zip")
            self.assertEqual(verify_package(package), [])
            tampered = root / "tampered.zip"
            with zipfile.ZipFile(package) as source, zipfile.ZipFile(tampered, "w") as target:
                for name in source.namelist():
                    target.writestr(name, "tampered" if name == "translation.txt" else source.read(name))
            self.assertTrue(any("mismatch" in item.lower() for item in verify_package(tampered)))


class MediaConstraintTest(unittest.TestCase):
    def test_audio_duration_limit_is_30_minutes(self):
        with self.assertRaisesRegex(Exception, "30 minutes"):
            _validate_media_constraints("audio", MediaInfo("audio", ".mp3", duration_seconds=1801, has_audio=True))

    def test_video_duration_limit_is_15_minutes(self):
        with self.assertRaisesRegex(Exception, "15 minutes"):
            _validate_media_constraints("video", MediaInfo("video", ".mp4", duration_seconds=901, has_audio=True, has_video=True))

    def test_audio_only_webm_uses_audio_duration_rule(self):
        media_type = _validate_media_constraints(
            "video",
            MediaInfo("video", ".webm", duration_seconds=1200, has_audio=True, has_video=False),
        )
        self.assertEqual(media_type, "audio")

    def test_rejects_above_1080p_video(self):
        with self.assertRaisesRegex(Exception, "720p or 1080p"):
            _validate_media_constraints(
                "video",
                MediaInfo("video", ".mp4", duration_seconds=60, has_audio=True, has_video=True, width=3840, height=2160),
            )


class PipelineTest(unittest.TestCase):
    def test_text_pipeline_generates_artifacts(self):
        pipeline = TranslationPipeline()
        result = pipeline.process_text(
            "hello farmer water",
            "English",
            "Hindi",
            ProcessingOptions(make_subtitles=True, allow_preview_translation=True, allow_model_download=False),
        )
        self.assertEqual(result.input_type, "text")
        self.assertTrue(result.translated_text)
        self.assertIn("translated_txt", result.artifacts)
        self.assertIn("srt", result.artifacts)
        self.assertIn("vtt", result.artifacts)
        self.assertIn("job_report", result.artifacts)
        self.assertIn("bundle_zip", result.artifacts)
        for path in result.artifacts.values():
            self.assertTrue(path.exists())
        self.assertEqual(verify_package(result.artifacts["bundle_zip"]), [])
        report = json.loads(result.artifacts["job_report"].read_text(encoding="utf-8"))
        self.assertIn("bundle_zip", report["artifacts"])
        self.assertIn("job_report", report["artifacts"])

    def test_document_pipeline_generates_artifacts_with_auto_detect(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "module.csv"
            source.write_text("Topic,Line\nWater,hello farmer water\n", encoding="utf-8")
            pipeline = TranslationPipeline()
            result = pipeline.process_file(
                source,
                "Auto detect",
                "Hindi",
                ProcessingOptions(make_subtitles=False, allow_preview_translation=True, allow_model_download=False),
            )
            self.assertEqual(result.input_type, "document")
            self.assertEqual(result.source_language, "English")
            self.assertIn("translated_txt", result.artifacts)
            self.assertIn("translated_markdown", result.artifacts)
            self.assertIn("translated_table", result.artifacts)

    def test_approved_memory_pipeline_generates_auditable_package(self):
        pipeline = TranslationPipeline()
        result = pipeline.process_approved_memory(
            "hello farmer water",
            "सुधारित अनुवाद",
            "English",
            "Hindi",
            {"job_id": "reviewed123", "version": 2, "approved_at": "2026-07-15T00:00:00+00:00"},
            ProcessingOptions(make_subtitles=True, allow_model_download=False),
        )
        self.assertEqual(result.metadata["translation_backend"], "approved-memory")
        self.assertEqual(result.metadata["translation_memory_job_id"], "reviewed123")
        self.assertIn("exact approved correction", result.warnings[0])
        self.assertIn("bundle_zip", result.artifacts)
        self.assertTrue(result.artifacts["bundle_zip"].exists())


class DocumentProcessorTest(unittest.TestCase):
    def test_extracts_selectable_pdf_text(self):
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "module.pdf"
            writer = PdfWriter()
            page = writer.add_blank_page(width=612, height=792)
            font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
            font_ref = writer._add_object(font)
            page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
            stream = DecodedStreamObject()
            stream.set_data(b"BT /F1 14 Tf 72 720 Td (Use clean water for the field.) Tj ET")
            page[NameObject("/Contents")] = writer._add_object(stream)
            with path.open("wb") as handle:
                writer.write(handle)
            extracted = extract_document_text(path)
            self.assertEqual(extracted.kind, "pdf")
            self.assertIn("clean water", extracted.text)

    def test_extracts_docx_text_without_external_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "module.docx"
            document_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Farmer training module</w:t></w:r></w:p></w:body></w:document>"
            )
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            extracted = extract_document_text(path)
            self.assertEqual(extracted.kind, "docx")
            self.assertIn("Farmer training module", extracted.text)

    def test_extracts_pptx_slide_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "training.pptx"
            slide_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                '<p:cSld><a:t>Apply compost before sowing</a:t></p:cSld></p:sld>'
            )
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("ppt/slides/slide1.xml", slide_xml)
            extracted = extract_document_text(path)
            self.assertEqual(extracted.kind, "pptx")
            self.assertIn("Apply compost", extracted.text)

    def test_extracts_xlsx_shared_and_numeric_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "crop-plan.xlsx"
            shared_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<si><t>Crop</t></si><si><t>Millet</t></si></sst>'
            )
            sheet_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                '<row><c t="s"><v>0</v></c><c t="s"><v>1</v></c><c><v>25</v></c></row>'
                '</sheetData></worksheet>'
            )
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("xl/sharedStrings.xml", shared_xml)
                archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
            extracted = extract_document_text(path)
            self.assertEqual(extracted.kind, "xlsx")
            self.assertIn("Crop | Millet | 25", extracted.text)

    def test_extracts_csv_and_tsv_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            csv_path = directory_path / "crop.csv"
            tsv_path = directory_path / "crop.tsv"
            csv_path.write_text("Crop,Advice\nMillet,Water early\n", encoding="utf-8")
            tsv_path.write_text("Crop\tAdvice\nMillet\tWater early\n", encoding="utf-8")
            for path, kind in ((csv_path, "csv"), (tsv_path, "tsv")):
                with self.subTest(kind=kind):
                    extracted = extract_document_text(path)
                    self.assertEqual(extracted.kind, kind)
                    self.assertIn("Millet | Water early", extracted.text)

    def test_corrupted_office_and_non_utf8_table_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for suffix in (".docx", ".pptx", ".xlsx"):
                path = root / f"broken{suffix}"
                path.write_bytes(b"not a zip")
                with self.subTest(suffix=suffix), self.assertRaises(DocumentProcessingError):
                    extract_document_text(path)
            table = root / "broken.csv"
            table.write_bytes(b"\xff\xfe\x00")
            with self.assertRaises(DocumentProcessingError):
                extract_document_text(table)

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract is required for the OCR integration test")
    def test_extracts_text_from_a_scanned_pdf_with_local_ocr(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
            import pypdfium2  # noqa: F401
        except ImportError:
            self.skipTest("PDF rendering dependencies are not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scan.pdf"
            image = Image.new("RGB", (1200, 800), "white")
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default(size=32)
            draw.text((80, 100), "Use organic mulch to retain soil moisture.", font=font, fill="black")
            image.save(path, "PDF", resolution=150)
            extracted = extract_document_text(path)
            self.assertEqual(extracted.kind, "pdf-ocr")
            self.assertIn("organic mulch", extracted.text.lower())


class TranslationGuardTest(unittest.TestCase):
    def test_rejects_unchanged_cross_language_output(self):
        with self.assertRaises(TranslationError):
            HostedHttpTranslator._validate_output("how are you", "how are you", "Hindi")

    def test_rejects_wrong_target_script(self):
        with self.assertRaises(TranslationError):
            HostedHttpTranslator._validate_output("hello", "namaste", "Hindi")

    def test_accepts_target_script(self):
        HostedHttpTranslator._validate_output("hello", "नमस्ते", "Hindi")

    def test_setup_error_is_local_and_privacy_clear(self):
        message = user_safe_error("IndicTrans2 dependencies are not installed")
        self.assertIn("local worker", message.lower())
        self.assertIn("not sent", message.lower())


class AuthStoreTest(unittest.TestCase):
    def test_first_admin_user_approval_and_deactivation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AuthStore(Path(directory) / "auth.json")
            admin, _ = store.create_first_admin("Admin.User", "correct horse battery", "Admin")
            pending = store.register_user("trainer", "approved trainer password", "Trainer")

            self.assertEqual(admin.username, "admin.user")
            self.assertEqual(pending.status, "pending")
            with self.assertRaises(AuthError):
                store.login("trainer", "approved trainer password")

            approved = store.approve_user("trainer", admin_username=admin.username)
            self.assertEqual(approved.status, "active")
            user, session = store.login("trainer", "approved trainer password")
            self.assertEqual(user.username, "trainer")
            store.authenticate(session.session_id)

            store.deactivate_user("trainer", admin_username=admin.username)
            with self.assertRaises(AuthError):
                store.authenticate(session.session_id)

    def test_login_throttling_blocks_repeated_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AuthStore(Path(directory) / "auth.json")
            store.create_first_admin("admin", "correct horse battery")
            for _ in range(5):
                with self.assertRaisesRegex(AuthError, "incorrect"):
                    store.login("admin", "wrong password", throttle_key="local")
            with self.assertRaisesRegex(AuthError, "Too many"):
                store.login("admin", "correct horse battery", throttle_key="local")

    def test_expired_session_requires_login_again(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AuthStore(Path(directory) / "auth.json", session_ttl_seconds=-1)
            _, session = store.create_first_admin("admin", "correct horse battery")
            with self.assertRaisesRegex(AuthError, "expired"):
                store.authenticate(session.session_id)


class ApiAuthTest(unittest.TestCase):
    def test_auth_flow_blocks_content_until_approval_and_csrf(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_store = api_module.auth_store
            api_module.auth_store = AuthStore(Path(directory) / "auth.json")
            try:
                client = TestClient(api_module.app)
                self.assertEqual(client.get("/auth/session").json()["setup_required"], True)
                self.assertEqual(client.post("/jobs/text", json={"text": "hello"}).status_code, 401)

                setup = client.post(
                    "/auth/setup",
                    json={"username": "admin", "password": "correct horse battery", "display_name": "Admin"},
                )
                self.assertEqual(setup.status_code, 200)
                self.assertEqual(setup.headers["x-content-type-options"], "nosniff")
                self.assertIn("frame-ancestors 'none'", setup.headers["content-security-policy"])
                admin_csrf = setup.json()["csrf_token"]
                self.assertTrue(admin_csrf)

                missing_csrf = client.post("/jobs/text", json={"text": "hello farmer water"})
                self.assertEqual(missing_csrf.status_code, 403)

                register = client.post(
                    "/auth/register",
                    json={"username": "trainer", "password": "approved trainer password", "display_name": "Trainer"},
                )
                self.assertEqual(register.status_code, 201)
                self.assertEqual(register.json()["status"], "pending")

                pending_client = TestClient(api_module.app)
                pending_login = pending_client.post(
                    "/auth/login",
                    json={"username": "trainer", "password": "approved trainer password"},
                )
                self.assertEqual(pending_login.status_code, 401)
                self.assertIn("approval", pending_login.json()["detail"].lower())

                approve = client.post(
                    "/auth/users/trainer/approve",
                    headers={"X-CSRF-Token": admin_csrf},
                )
                self.assertEqual(approve.status_code, 200)
                self.assertEqual(approve.json()["status"], "active")

                user_client = TestClient(api_module.app)
                login = user_client.post(
                    "/auth/login",
                    json={"username": "trainer", "password": "approved trainer password"},
                )
                self.assertEqual(login.status_code, 200)
                self.assertEqual(user_client.get("/history").status_code, 200)

                deactivate = client.post(
                    "/auth/users/trainer/deactivate",
                    headers={"X-CSRF-Token": admin_csrf},
                )
                self.assertEqual(deactivate.status_code, 200)
                self.assertEqual(user_client.get("/history").status_code, 401)
            finally:
                api_module.auth_store = previous_store


class ReviewWorkflowTest(unittest.TestCase):
    def test_review_store_versions_approval_memory_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job_dir = root / "job123"
            job_dir.mkdir()
            (job_dir / "job_report.json").write_text(
                json.dumps({"artifacts": {"translated_txt": "translated_text.txt"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            store = ReviewStore(root / ".reviews")

            draft = store.save_correction("job123", "सुधारित अनुवाद", "trainer", job_dir)
            self.assertEqual(len(draft.versions), 1)
            self.assertTrue((job_dir / "corrected_translation_v1.txt").exists())

            approved = store.approve(
                "job123",
                None,
                "trainer",
                "hello farmer water",
                "English",
                "Hindi",
                job_dir,
            )
            self.assertEqual(approved.status, "approved")
            memory = store.find_memory("hello farmer water", "English", "Hindi")
            self.assertIsNotNone(memory)
            self.assertEqual(memory.corrected_text, "सुधारित अनुवाद")
            self.assertTrue((job_dir / "approved_corrected_package.zip").exists())

            store.delete("job123")
            self.assertIsNone(store.find_memory("hello farmer water", "English", "Hindi"))

    def test_api_review_library_and_safe_delete_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_dir = root / "outputs"
            job_dir = output_dir / "job123"
            job_dir.mkdir(parents=True)
            (job_dir / "translated_text.txt").write_text("मशीन अनुवाद", encoding="utf-8")
            (job_dir / "source_text.txt").write_text("hello farmer water", encoding="utf-8")
            (job_dir / "job_report.json").write_text(
                json.dumps(
                    {
                        "artifacts": {
                            "translated_txt": "translated_text.txt",
                            "source_txt": "source_text.txt",
                            "job_report": "job_report.json",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            previous_auth = api_module.auth_store
            previous_jobs = api_module.job_manager
            previous_reviews = api_module.review_store
            previous_output = api_module.OUTPUT_DIR
            api_module.auth_store = AuthStore(root / "auth.json")
            api_module.job_manager = JobManager(root / ".jobs", max_workers=1)
            api_module.review_store = ReviewStore(output_dir / ".reviews")
            api_module.OUTPUT_DIR = output_dir
            try:
                from core.job_manager import JobRecord

                api_module.job_manager._jobs["queue123"] = JobRecord(
                    job_id="queue123",
                    kind="text",
                    status="succeeded",
                    progress=1.0,
                    message="Translation ready",
                    result={
                        "job_id": "job123",
                        "input_type": "text",
                        "source_language": "English",
                        "target_language": "Hindi",
                        "original_text": "hello farmer water",
                        "translated_text": "मशीन अनुवाद",
                        "warnings": [],
                        "metadata": {"source_filename": "farmer.txt"},
                        "artifacts": [
                            {"key": "translated_txt", "filename": "translated_text.txt", "download_url": "/jobs/job123/artifacts/translated_txt"},
                            {"key": "source_txt", "filename": "source_text.txt", "download_url": "/jobs/job123/artifacts/source_txt"},
                            {"key": "job_report", "filename": "job_report.json", "download_url": "/jobs/job123/artifacts/job_report"},
                        ],
                    },
                )

                client = TestClient(api_module.app)
                setup = client.post(
                    "/auth/setup",
                    json={"username": "admin", "password": "correct horse battery", "display_name": "Admin"},
                )
                csrf = setup.json()["csrf_token"]

                library = client.get("/library?q=farmer")
                self.assertEqual(library.status_code, 200)
                self.assertEqual(library.json()["items"][0]["job_id"], "queue123")
                self.assertEqual(client.get("/jobs/job123").status_code, 200)

                correction = client.post(
                    "/jobs/queue123/review/corrections",
                    headers={"X-CSRF-Token": csrf},
                    json={"corrected_text": "सुधारित अनुवाद"},
                )
                self.assertEqual(correction.status_code, 200)
                self.assertEqual(correction.json()["versions"][0]["version"], 1)

                approval = client.post(
                    "/jobs/job123/review/approve",
                    headers={"X-CSRF-Token": csrf},
                    json={},
                )
                self.assertEqual(approval.status_code, 200)
                self.assertEqual(approval.json()["status"], "approved")
                self.assertIsNotNone(api_module.review_store.find_memory("hello farmer water", "English", "Hindi"))

                delete = client.delete("/jobs/job123", headers={"X-CSRF-Token": csrf})
                self.assertEqual(delete.status_code, 200)
                self.assertIsNone(api_module.review_store.find_memory("hello farmer water", "English", "Hindi"))
                self.assertFalse(job_dir.exists())
            finally:
                api_module.auth_store = previous_auth
                api_module.job_manager.shutdown()
                api_module.job_manager = previous_jobs
                api_module.review_store = previous_reviews
                api_module.OUTPUT_DIR = previous_output


class TranscriberSelectionTest(unittest.TestCase):
    def test_default_transcriber_is_whisper(self):
        self.assertIsInstance(get_transcriber(allow_model_download=False), WhisperTranscriber)


class JobManagerTest(unittest.TestCase):
    def test_runs_and_persists_a_job_with_real_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = JobManager(Path(directory), max_workers=1, max_pending=2)

            def task(status):
                status("Halfway", 0.5)
                return {"translated_text": "नमस्ते"}

            record = manager.submit("text", task)
            deadline = time.time() + 3
            while manager.get(record.job_id).status not in {"succeeded", "failed"} and time.time() < deadline:
                time.sleep(0.01)
            completed = manager.get(record.job_id)
            self.assertEqual(completed.status, "succeeded")
            self.assertEqual(completed.progress, 1.0)
            self.assertEqual(completed.result["translated_text"], "नमस्ते")
            self.assertTrue((Path(directory) / f"{record.job_id}.json").exists())
            self.assertEqual(manager.summary()["succeeded"], 1)
            self.assertIn("total", completed.stage_timings)
            manager.shutdown()

    def test_restart_marks_interrupted_job_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / "stuck.json").write_text(
                json.dumps({"job_id": "stuck", "kind": "file", "status": "running"}), encoding="utf-8"
            )
            manager = JobManager(state)
            self.assertEqual(manager.get("stuck").status, "failed")
            self.assertIn("restarted", manager.get("stuck").error)
            manager.shutdown()


class ObservabilityTest(unittest.TestCase):
    def test_json_log_formatter_emits_machine_readable_events(self):
        import json
        import logging

        record = logging.LogRecord("vaanisetu.test", logging.INFO, __file__, 1, "Ready", (), None)
        record.event = "readiness_checked"
        payload = json.loads(JsonFormatter().format(record))
        self.assertEqual(payload["event"], "readiness_checked")
        self.assertEqual(payload["message"], "Ready")


if __name__ == "__main__":
    unittest.main()
