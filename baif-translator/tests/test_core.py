from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.file_utils import ValidationError, save_binary_upload
from core.pipeline import ProcessingOptions, TranslationPipeline
from core.subtitles import Segment, render_srt, render_vtt, segments_from_text, subtitle_safe_text
from core.text_utils import normalize_text, split_for_translation


class TextUtilsTest(unittest.TestCase):
    def test_normalize_and_split_for_translation(self):
        text = " hello   farmer water\n\nThis is a long sentence. " * 20
        normalized = normalize_text(text)
        chunks = split_for_translation(normalized, max_chars=120)
        self.assertTrue(chunks)
        self.assertTrue(all(len(chunk) <= 120 for chunk in chunks))
        self.assertNotIn("  ", normalized)


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


if __name__ == "__main__":
    unittest.main()
