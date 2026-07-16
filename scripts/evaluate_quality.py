"""Reproducible six-direction translation and ASR release-quality gate."""

from __future__ import annotations

import argparse
import csv
import json
import resource
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.languages import get_language
from core.asr_cleanup import clean_indic_asr_text
from core.quality import validate_translation
from core.transcriber import TranscriptionError, get_transcriber
from core.translator import TranslationError, translate_text


def _chrf_metric():
    try:
        from sacrebleu.metrics import CHRF
    except ImportError as exc:
        raise SystemExit("Install requirements-quality.txt to run quality evaluation.") from exc
    return CHRF(word_order=2)


def _max_memory_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(value / (1024 * 1024) if sys.platform == "darwin" else value / 1024, 2)


def _reviewer_csv(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "source_language", "target_language", "source", "reference", "prediction", "backend", "chrf++", "findings", "reviewer", "severity", "category", "correction", "notes"]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key, "") for key in fields})


def _direction_summary(rows: list[dict]) -> dict:
    scores = [float(row.get("chrf++", 0)) for row in rows]
    findings = [finding for row in rows for finding in row.get("finding_details", [])]
    terminology_checks = [finding for finding in findings if finding["kind"] == "terminology"]
    return {
        "samples": len(rows),
        "mean_chrf++": round(statistics.mean(scores), 2) if scores else 0.0,
        "terminology_accuracy": round(100 * (1 - len(terminology_checks) / max(1, len(rows))), 2),
        "preservation_failures": sum(finding["kind"] == "preservation" for finding in findings),
        "script_failures": sum(finding["kind"] == "script" for finding in findings),
        "untranslated_failures": sum(finding["kind"] == "untranslated" for finding in findings),
        "mean_latency_seconds": round(statistics.mean(float(row.get("latency_seconds", 0)) for row in rows), 3) if rows else 0.0,
        "backends": dict(Counter(str(row.get("backend", "error")) for row in rows)),
    }


def evaluate_translation(manifest: Path, output: Path, allow_model_download: bool, reviewer_output: Path | None = None) -> int:
    chrf = _chrf_metric()
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    results: list[dict] = []
    by_direction: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        started = time.monotonic()
        try:
            result = translate_text(row["source"], row["source_language"], row["target_language"], allow_preview=False, allow_model_download=allow_model_download)
            score = chrf.sentence_score(result.text, [row["reference"]]).score
            finding_objects = validate_translation(row["source"], result.text, row["source_language"], row["target_language"])
            finding_details = [finding.__dict__ for finding in finding_objects]
            item = {**row, "prediction": result.text, "backend": result.backend, "chrf++": round(score, 2), "latency_seconds": round(time.monotonic() - started, 3), "finding_details": finding_details, "findings": " | ".join(f"{finding.severity}:{finding.kind}:{finding.message}" for finding in finding_objects)}
        except TranslationError as exc:
            item = {**row, "error": str(exc), "chrf++": 0.0, "latency_seconds": round(time.monotonic() - started, 3), "finding_details": [{"kind": "backend", "severity": "critical", "message": str(exc)}], "findings": f"critical:backend:{exc}"}
        results.append(item)
        by_direction[f"{row['source_language']}->{row['target_language']}"] .append(item)

    directions = {key: _direction_summary(value) for key, value in sorted(by_direction.items())}
    critical_count = sum(finding["severity"] == "critical" for row in results for finding in row["finding_details"])
    required_directions = {"English->Hindi", "English->Marathi", "Hindi->English", "Hindi->Marathi", "Marathi->English", "Marathi->Hindi"}
    gate_reasons: list[str] = []
    if set(directions) != required_directions:
        gate_reasons.append("Benchmark does not cover all six supported directions.")
    if critical_count:
        gate_reasons.append(f"{critical_count} critical preservation, script, untranslated, or backend failure(s).")
    if any(summary["mean_chrf++"] < 35 for summary in directions.values()):
        gate_reasons.append("At least one direction is below the engineering chrF++ floor of 35.")
    payload = {
        "schema_version": 2,
        "task": "translation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest),
        "review_status": "engineering gate only; bilingual BAIF approval remains external",
        "samples": len(results),
        "directions": directions,
        "peak_memory_mb": _max_memory_mb(),
        "gate": {"passed": not gate_reasons, "reasons": gate_reasons},
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _reviewer_csv(results, reviewer_output or output.with_name("translation_reviewer_worksheet.csv"))
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0 if payload["gate"]["passed"] else 1


def evaluate_asr(manifest: Path, output: Path, allow_model_download: bool) -> int:
    try:
        from jiwer import wer
    except ImportError as exc:
        raise SystemExit("Install requirements-quality.txt to run quality evaluation.") from exc
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    transcriber = get_transcriber(allow_model_download=allow_model_download)
    results: list[dict] = []
    for row in rows:
        audio_path = (manifest.parent / row["audio"]).resolve()
        language = get_language(row["source_language"])
        started = time.monotonic()
        try:
            transcription = transcriber.transcribe(audio_path, language.whisper_code)
            prediction, _ = clean_indic_asr_text(transcription.text, language.whisper_code)
            results.append({**row, "prediction": prediction, "wer": round(wer(row["reference"], prediction), 4), "latency_seconds": round(time.monotonic() - started, 3)})
        except (TranscriptionError, OSError) as exc:
            results.append({**row, "error": str(exc), "wer": 1.0, "latency_seconds": round(time.monotonic() - started, 3)})
    scores = [row["wer"] for row in results]
    payload = {"schema_version": 2, "task": "asr", "generated_at": datetime.now(timezone.utc).isoformat(), "manifest": str(manifest), "samples": len(results), "mean_wer": round(statistics.mean(scores), 4) if scores else 0.0, "peak_memory_mb": _max_memory_mb(), "gate": {"passed": bool(results) and all("error" not in row for row in results), "reasons": []}, "results": results}
    if not payload["gate"]["passed"]:
        payload["gate"]["reasons"].append("ASR backend errors occurred or the reviewed manifest is empty.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, ensure_ascii=False, indent=2))
    return 0 if payload["gate"]["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VaaniSetu release-quality benchmarks.")
    parser.add_argument("--task", choices=("translation", "asr"), default="translation")
    parser.add_argument("--manifest", type=Path, default=ROOT / "benchmarks" / "translation_seed.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "quality_report.json")
    parser.add_argument("--reviewer-output", type=Path)
    parser.add_argument("--offline", action="store_true", help="Do not download missing open-source models.")
    args = parser.parse_args()
    if not args.manifest.exists():
        raise SystemExit(f"Manifest not found: {args.manifest}")
    if args.task == "translation":
        return evaluate_translation(args.manifest, args.output, not args.offline, args.reviewer_output)
    return evaluate_asr(args.manifest, args.output, not args.offline)


if __name__ == "__main__":
    raise SystemExit(main())
