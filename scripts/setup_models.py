"""Download/cache open-source models used by VaaniSetu.

Run from the project root:
    python scripts/setup_models.py
"""

from __future__ import annotations

import argparse
import shutil
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
    "indictrans-en-indic-dist": (
        "ai4bharat/indictrans2-en-indic-dist-200M",
        ROOT / "models" / "indictrans2" / "indictrans2-en-indic-dist-200M",
    ),
    "indictrans-indic-en": (
        "ai4bharat/indictrans2-indic-en-1B",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-en-1B",
    ),
    "indictrans-indic-en-dist": (
        "ai4bharat/indictrans2-indic-en-dist-200M",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-en-dist-200M",
    ),
    "indictrans-indic-indic": (
        "ai4bharat/indictrans2-indic-indic-1B",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-indic-1B",
    ),
    "indictrans-indic-indic-dist": (
        "ai4bharat/indictrans2-indic-indic-dist-320M",
        ROOT / "models" / "indictrans2" / "indictrans2-indic-indic-dist-320M",
    ),
    "indic-parler-tts": (
        "ai4bharat/indic-parler-tts",
        ROOT / "models" / "indic-parler-tts",
    ),
    "indic-conformer": (
        "ai4bharat/indic-conformer-600m-multilingual",
        ROOT / "models" / "indic-conformer-600m-multilingual",
    ),
    "nllb": (
        "facebook/nllb-200-distilled-600M",
        ROOT / "models" / "nllb" / "nllb-200-distilled-600M",
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

DIST_TRANSLATION_MODELS = [
    "indictrans-en-indic-dist",
    "indictrans-indic-en-dist",
    "indictrans-indic-indic-dist",
]

GATED_OPTIONAL_MODELS = set(
    CORE_TRANSLATION_MODELS
    + DIST_TRANSLATION_MODELS
    + ["indic-parler-tts", "indic-conformer"]
)


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
    parser.add_argument(
        "--with-tts",
        action="store_true",
        help="Also download the Indic Parler TTS quality model.",
    )
    parser.add_argument(
        "--with-indic-asr",
        action="store_true",
        help="Also download the IndicConformer multilingual ASR model.",
    )
    args = parser.parse_args()

    if args.only:
        selected = ["whisper-balanced" if name == "whisper" else name for name in args.only]
    else:
        selected = list(PROFILE_MODELS[args.profile])
        if args.with_translation:
            selected.append("nllb")
            selected.extend(CORE_TRANSLATION_MODELS if args.profile == "quality" else DIST_TRANSLATION_MODELS)
        if args.with_tts:
            selected.append("indic-parler-tts")
        if args.with_indic_asr:
            selected.append("indic-conformer")

    failures: list[str] = []
    for name in dict.fromkeys(selected):
        repo_id, target = MODELS[name]
        target.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {repo_id} -> {target}")
        try:
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(target),
                local_dir_use_symlinks=False,
            )
        except Exception as exc:
            if not (target / "config.json").exists():
                shutil.rmtree(target, ignore_errors=True)
            if name not in GATED_OPTIONAL_MODELS:
                raise
            failures.append(name)
            print(f"Optional model unavailable: {name} ({exc.__class__.__name__})")
            print("Accept its Hugging Face access conditions and set HF_TOKEN, then rerun setup.")
    print("Model setup complete.")
    if failures:
        print("The local NLLB translation fallback remains available.")
        print("Quality upgrades still pending: " + ", ".join(failures))


if __name__ == "__main__":
    main()
