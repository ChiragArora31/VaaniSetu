"""Generate repeatable media workloads and record CPU, memory, disk and stage timing."""

from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.settings import OUTPUT_DIR
from core.media_utils import inspect_media, require_binary


def _memory_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(value / (1024 * 1024) if sys.platform == "darwin" else value / 1024, 2)


def _run(command: list[str]) -> float:
    started = time.monotonic()
    subprocess.run(command, check=True, capture_output=True, text=True)
    return round(time.monotonic() - started, 3)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VaaniSetu media stress fixtures.")
    parser.add_argument("--profile", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "stress_report.json")
    parser.add_argument("--keep-fixtures", action="store_true")
    args = parser.parse_args()
    ffmpeg = require_binary("ffmpeg", "FFmpeg")
    fixture_dir = OUTPUT_DIR / ".stress"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    audio_seconds, video_seconds = (1800, 900) if args.profile == "full" else (8, 5)
    audio = fixture_dir / "stress_audio.wav"
    video = fixture_dir / "stress_video.mp4"
    disk_before = shutil.disk_usage(OUTPUT_DIR).free
    stages = {}
    stages["generate_audio_seconds"] = _run([ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000", "-t", str(audio_seconds), "-c:a", "pcm_s16le", str(audio)])
    stages["generate_video_seconds"] = _run([ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=0x355d3a:s=1920x1080:r=1", "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=16000", "-t", str(video_seconds), "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(video)])
    started = time.monotonic(); audio_info = inspect_media(audio); stages["inspect_audio_seconds"] = round(time.monotonic() - started, 3)
    started = time.monotonic(); video_info = inspect_media(video); stages["inspect_video_seconds"] = round(time.monotonic() - started, 3)
    disk_after = shutil.disk_usage(OUTPUT_DIR).free
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "profile": args.profile,
        "limits_exercised": {"audio_seconds": audio_seconds, "video_seconds": video_seconds, "video_resolution": "1920x1080"},
        "observed": {"audio_duration": audio_info.duration_seconds, "video_duration": video_info.duration_seconds, "video_width": video_info.width, "video_height": video_info.height},
        "stage_timings": stages, "peak_memory_mb": _memory_mb(), "cpu_count": os.cpu_count(),
        "fixture_disk_bytes": disk_before - disk_after, "passed": audio_info.duration_seconds >= audio_seconds - 1 and video_info.duration_seconds >= video_seconds - 1 and video_info.width == 1920 and video_info.height == 1080,
        "note": "This harness validates boundary media generation/inspection. Run a representative spoken BAIF file through the E2E UAT for ASR/translation quality."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if not args.keep_fixtures:
        shutil.rmtree(fixture_dir, ignore_errors=True)
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
