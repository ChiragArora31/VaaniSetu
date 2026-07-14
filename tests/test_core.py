from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
import time
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.file_utils import ValidationError, save_binary_upload, validate_size
from core.job_manager import JobManager
from core.observability import JsonFormatter
from core.asr_cleanup import clean_indic_asr_text
from core.document_processor import extract_document_text
from core.media_utils import MediaInfo
from core.pipeline import ProcessingOptions, TranslationPipeline, _validate_media_constraints
from core.subtitles import Segment, render_srt, render_vtt, segments_from_text, subtitle_safe_text
from core.text_utils import detect_language_name, normalize_text, split_for_translation
from core.translator import HostedHttpTranslator, TranslationError
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


class DocumentProcessorTest(unittest.TestCase):
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
