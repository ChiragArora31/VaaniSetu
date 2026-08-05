"""One-command BAIF worker setup.

This installs Python requirements and optionally caches open-source models.
Run from the project root:
    python scripts/one_click_setup.py --profile balanced
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    if sys.version_info[:2] not in {(3, 10), (3, 11)}:
        raise SystemExit(
            "VaaniSetu requires Python 3.10 or 3.11. "
            f"This command is using Python {sys.version_info.major}.{sys.version_info.minor}."
        )
    parser = argparse.ArgumentParser(description="Set up the VaaniSetu BAIF translation worker.")
    parser.add_argument("--profile", choices=["fast", "balanced", "quality"], default="balanced")
    parser.add_argument("--skip-models", action="store_true", help="Install packages only; do not download model weights.")
    parser.add_argument("--minimal", action="store_true", help="Install only the lightweight base requirements.")
    args = parser.parse_args()

    python = sys.executable
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    requirements = "requirements.txt" if args.minimal else (
        "requirements-quality.txt" if args.profile == "quality" else "requirements-full.txt"
    )
    run([python, "-m", "pip", "install", "-r", requirements])

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("FFmpeg was not found on PATH. The Python imageio-ffmpeg fallback can handle many flows,")
        print("but BAIF production should install FFmpeg and ffprobe system-wide.")

    if not args.skip_models:
        run([python, "scripts/setup_ocr.py"])
        model_command = [python, "scripts/setup_models.py", "--profile", args.profile, "--with-translation"]
        if args.profile == "quality":
            model_command.extend(["--with-tts", "--with-indic-asr"])
        run(model_command)
        run([python, "scripts/convert_nllb_ct2.py"])

    run([python, "scripts/operations.py", "migrate"])

    print("")
    print("Setup complete. No further installation is needed for normal users.")
    print("Production preflight (must be green before handover):")
    print("  python scripts/operations.py preflight")
    print("Start VaaniSetu with:")
    print("  python -m uvicorn app:app --host 127.0.0.1 --port 8501")
    print("Then open http://127.0.0.1:8501 and follow Start here.")


if __name__ == "__main__":
    main()
