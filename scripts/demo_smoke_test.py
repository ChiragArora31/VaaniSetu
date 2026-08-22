"""Pre-demo health gate for the VaaniSetu judge journey.

Quick mode is model-free and safe to run immediately before entering the room.
Full mode additionally performs a real local English-to-Hindi translation and
verifies its offline package; it never enables model downloads or hosted APIs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.settings import (  # noqa: E402
    ALLOW_MODEL_DOWNLOAD,
    ENABLE_HOSTED_TRANSLATION,
    OUTPUT_DIR,
    TEMP_DIR,
    ensure_directories,
)
from core.health import collect_health_checks  # noqa: E402
from scripts.verify_package import verify as verify_package  # noqa: E402


REQUIRED_DEMO_FILES = (
    ROOT / "samples" / "demo_agriculture.txt",
    ROOT / "submission" / "VaaniSetu_Final_Hackathon_Deck.pptx",
    ROOT / "DEMO.md",
    ROOT / "SETUP.md",
    ROOT / "ACCEPTANCE.md",
)


def _writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=directory, delete=True):
            return True
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether VaaniSetu is healthy for the judge demo.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also run a real local translation and verify the generated offline ZIP.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "demo_smoke_report.json",
    )
    args = parser.parse_args()

    ensure_directories()
    health = collect_health_checks(allow_model_download=False)
    required_health = {"FFmpeg", "ffprobe", "Local translation route"}
    checks = {
        "hosted_translation_disabled": not ENABLE_HOSTED_TRANSLATION,
        "runtime_model_downloads_disabled": not ALLOW_MODEL_DOWNLOAD,
        "output_directory_writable": _writable(OUTPUT_DIR),
        "temp_directory_writable": _writable(TEMP_DIR),
        "demo_files_present": all(path.is_file() for path in REQUIRED_DEMO_FILES),
        "required_runtime_ready": all(item.ok for item in health if item.name in required_health),
    }
    details: dict[str, object] = {
        "missing_demo_files": [str(path.relative_to(ROOT)) for path in REQUIRED_DEMO_FILES if not path.is_file()],
        "required_runtime": [item.__dict__ for item in health if item.name in required_health],
        "ffmpeg": shutil.which("ffmpeg") or "not found",
    }

    if args.full and all(checks.values()):
        from core.pipeline import ProcessingOptions, TranslationPipeline

        source = (ROOT / "samples" / "demo_agriculture.txt").read_text(encoding="utf-8").strip()
        result = TranslationPipeline().process_text(
            source,
            "English",
            "Hindi",
            ProcessingOptions(
                make_subtitles=True,
                make_tts=False,
                allow_preview_translation=False,
                allow_model_download=False,
            ),
        )
        package = result.artifacts.get("bundle_zip")
        failures = verify_package(package) if package else ["Offline package was not generated."]
        checks["representative_translation_completed"] = bool(result.translated_text.strip())
        checks["offline_package_verified"] = not failures
        details["translation"] = {
            "job_id": result.job_id,
            "backend": result.metadata.get("translation_backend"),
            "artifacts": sorted(result.artifacts),
            "package_errors": failures,
        }
    elif args.full:
        checks["representative_translation_completed"] = False
        checks["offline_package_verified"] = False
        details["translation"] = {"skipped": "Quick prerequisite checks failed."}

    payload = {"mode": "full" if args.full else "quick", "ready": all(checks.values()), "checks": checks, "details": details}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
