"""Convert the local NLLB fallback to an INT8 CTranslate2 CPU model."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "models" / "nllb" / "nllb-200-distilled-600M"
DEFAULT_TARGET = ROOT / "models" / "nllb" / "nllb-200-distilled-600M-ct2-int8"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare the optimized local NLLB CPU fallback.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if (args.target / "model.bin").exists() and not args.force:
        print(f"Optimized NLLB model is already ready: {args.target}")
        return
    if not (args.source / "config.json").exists():
        raise SystemExit(f"Local NLLB source model is missing: {args.source}")

    try:
        from ctranslate2.converters import TransformersConverter
    except ImportError as exc:
        raise SystemExit("Install requirements-full.txt before converting NLLB.") from exc

    args.target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Converting NLLB to INT8 CTranslate2 format: {args.target}")
    TransformersConverter(
        str(args.source),
        low_cpu_mem_usage=True,
    ).convert(str(args.target), quantization="int8", force=args.force)
    print("Optimized NLLB fallback is ready.")


if __name__ == "__main__":
    main()
