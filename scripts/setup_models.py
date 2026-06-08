"""Download/cache open-source models used by VaaniSetu.

Run from the project root:
    python scripts/setup_models.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parents[1]


MODELS = {
    "whisper-fast": (
        "Systran/faster-whisper-base",
        ROOT / "models" / "whisper" / "faster-whisper-base",
    ),
    "whisper-balanced": (
        "Systran/faster-whisper-small",
        ROOT / "models" / "whisper" / "faster-whisper-small",
    ),
    "whisper-quality": (
        "Systran/faster-whisper-large-v3",
        ROOT / "models" / "whisper" / "faster-whisper-large-v3",
    ),
    "indictrans-en-indic": (
        "ai4bharat/indictrans2-en-indic-1B",
        ROOT / "models" / "indictrans2" / "indictrans2-en-indic-1B",
    ),
    "indictrans-indic-en": (
        "ai4bharat/indictrans2-indic-en-1B",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-en-1B",
    ),
    "indictrans-indic-indic": (
        "ai4bharat/indictrans2-indic-indic-1B",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-indic-1B",
    ),
}

PROFILE_MODELS = {
    "fast": ["whisper-fast"],
    "balanced": ["whisper-balanced"],
    "quality": ["whisper-quality"],
}

CORE_TRANSLATION_MODELS = [
    "indictrans-en-indic",
    "indictrans-indic-en",
    "indictrans-indic-indic",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download open-source VaaniSetu model assets.")
    parser.add_argument(
        "--only",
        choices=sorted(MODELS) + ["whisper"],
        action="append",
        help="Download only selected model(s). Can be passed more than once.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_MODELS),
        default="balanced",
        help="Download the Whisper model for a deployment profile.",
    )
    parser.add_argument(
        "--with-translation",
        action="store_true",
        help="Also download all IndicTrans2 translation models.",
    )
    args = parser.parse_args()

    if args.only:
        selected = ["whisper-balanced" if name == "whisper" else name for name in args.only]
    else:
        selected = list(PROFILE_MODELS[args.profile])
        if args.with_translation:
            selected.extend(CORE_TRANSLATION_MODELS)

    for name in selected:
        repo_id, target = MODELS[name]
        target.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {repo_id} -> {target}")
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(target),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
    print("Model setup complete.")


if __name__ == "__main__":
    main()
