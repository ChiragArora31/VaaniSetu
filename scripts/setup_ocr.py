"""Cache official Tesseract language data for VaaniSetu OCR."""

from __future__ import annotations

import argparse
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "models" / "tessdata"
BASE_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main"
LANGUAGES = ("eng", "hin", "mar", "osd")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Tesseract OCR language data.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    args = parser.parse_args()
    args.target.mkdir(parents=True, exist_ok=True)

    for language in LANGUAGES:
        target = args.target / f"{language}.traineddata"
        if target.exists() and target.stat().st_size > 100_000:
            print(f"OCR language already ready: {language}")
            continue
        response = requests.get(f"{BASE_URL}/{language}.traineddata", timeout=120)
        response.raise_for_status()
        temporary = target.with_suffix(".traineddata.tmp")
        temporary.write_bytes(response.content)
        temporary.replace(target)
        print(f"Downloaded OCR language: {language}")

    print(f"OCR language data ready in {args.target}")


if __name__ == "__main__":
    main()
