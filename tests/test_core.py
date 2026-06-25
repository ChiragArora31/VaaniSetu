from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.file_utils import ValidationError, save_binary_upload, validate_size
from core.asr_cleanup import clean_indic_asr_text
from core.media_utils import MediaInfo
from core.pipeline import ProcessingOptions, TranslationPipeline, _validate_media_constraints
from core.subtitles import Segment, render_srt, render_vtt, segments_from_text, subtitle_safe_text
from core.text_utils import normalize_text, split_for_translation
from core.translator import HostedHttpTranslator, TranslationError
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


class TranslationGuardTest(unittest.TestCase):
    def test_rejects_unchanged_cross_language_output(self):
        with self.assertRaises(TranslationError):
            HostedHttpTranslator._validate_output("how are you", "how are you", "Hindi")

    def test_rejects_wrong_target_script(self):
        with self.assertRaises(TranslationError):
            HostedHttpTranslator._validate_output("hello", "namaste", "Hindi")

    def test_accepts_target_script(self):
        HostedHttpTranslator._validate_output("hello", "नमस्ते", "Hindi")


class TranscriberSelectionTest(unittest.TestCase):
    def test_default_transcriber_is_whisper(self):
        self.assertIsInstance(get_transcriber(allow_model_download=False), WhisperTranscriber)


if __name__ == "__main__":
    unittest.main()
