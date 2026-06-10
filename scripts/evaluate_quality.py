"""Evaluate translation quality against a reviewed JSONL benchmark."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.languages import get_language
from core.asr_cleanup import clean_indic_asr_text
from core.transcriber import TranscriptionError, get_transcriber
from core.translator import TranslationError, translate_text


def evaluate_translation(manifest: Path, output: Path, allow_model_download: bool) -> int:
    try:
        from sacrebleu.metrics import CHRF
    except ImportError as exc:
        raise SystemExit("Install requirements-quality.txt to run quality evaluation.") from exc

    chrf = CHRF(word_order=2)
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    results: list[dict] = []
    scores: list[float] = []

    for row in rows:
        try:
            result = translate_text(
                row["source"],
                row["source_language"],
                row["target_language"],
                allow_preview=False,
                allow_model_download=allow_model_download,
            )
            score = chrf.sentence_score(result.text, [row["reference"]]).score
            scores.append(score)
            results.append({**row, "prediction": result.text, "backend": result.backend, "chrf++": round(score, 2)})
        except TranslationError as exc:
            results.append({**row, "error": str(exc), "chrf++": 0.0})
            scores.append(0.0)

    payload = {
        "task": "translation",
        "manifest": str(manifest),
        "samples": len(results),
        "mean_chrf++": round(statistics.mean(scores), 2) if scores else 0.0,
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0 if all("error" not in row for row in results) else 1


def evaluate_asr(manifest: Path, output: Path, allow_model_download: bool) -> int:
    try:
        from jiwer import wer
    except ImportError as exc:
        raise SystemExit("Install requirements-quality.txt to run quality evaluation.") from exc

    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    transcriber = get_transcriber(allow_model_download=allow_model_download)
    results: list[dict] = []
    scores: list[float] = []

    for row in rows:
        audio_path = (manifest.parent / row["audio"]).resolve()
        language = get_language(row["source_language"])
        try:
            transcription = transcriber.transcribe(audio_path, language.whisper_code)
            prediction, _ = clean_indic_asr_text(transcription.text, language.whisper_code)
            score = wer(row["reference"], prediction)
            scores.append(score)
            results.append({**row, "prediction": prediction, "wer": round(score, 4)})
        except (TranscriptionError, OSError) as exc:
            results.append({**row, "error": str(exc), "wer": 1.0})
            scores.append(1.0)

    payload = {
        "task": "asr",
        "manifest": str(manifest),
        "samples": len(results),
        "mean_wer": round(statistics.mean(scores), 4) if scores else 0.0,
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0 if all("error" not in row for row in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VaaniSetu quality benchmarks.")
    parser.add_argument("--task", choices=("translation", "asr"), default="translation")
    parser.add_argument("--manifest", type=Path, default=ROOT / "benchmarks" / "translation_seed.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "quality_report.json")
    parser.add_argument("--offline", action="store_true", help="Do not download missing open-source models.")
    args = parser.parse_args()
    evaluator = evaluate_translation if args.task == "translation" else evaluate_asr
    return evaluator(args.manifest, args.output, allow_model_download=not args.offline)


if __name__ == "__main__":
    raise SystemExit(main())
