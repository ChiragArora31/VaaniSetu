# Quality Benchmarks

Quality claims for VaaniSetu must be backed by reviewed examples that represent BAIF field usage.

## Translation

`translation_seed.jsonl` covers every supported language direction. Expand it with BAIF-reviewed sentences before production acceptance; keep the checked-in seed unchanged as a reproducible engineering baseline.

```bash
python scripts/evaluate_quality.py
```

Higher chrF++ is better. The report also records per-direction terminology accuracy, preservation/script/untranslated failures, latency, peak memory, and backend provenance. It exits non-zero if any supported direction is absent, a preservation/script/backend critical occurs, or a direction misses the engineering chrF++ floor. A UTF-8 reviewer worksheet is generated beside the report with severity/category/correction fields.

The checked-in seed covers all six directions and includes agriculture terminology, numbers, units, a URL, and an email address. It is an engineering regression corpus, not BAIF linguistic approval. Reviewers should add representative dialect, names, safety instructions, measurements, and unchanged-text cases rather than editing predictions to make the gate pass.

## Speech recognition

Create an ASR JSONL manifest beside reviewed audio files:

```json
{"id":"hi-field-001","audio":"audio/hi-field-001.wav","source_language":"Hindi","reference":"किसान आज खेत में काम कर रहे हैं।"}
```

Run:

```bash
python scripts/evaluate_quality.py --task asr --manifest benchmarks/asr_reviewed.jsonl --output outputs/asr_quality_report.json
```

Lower word error rate is better. Include clean speech, noisy field recordings, different genders, dialects, code-switching, and phone microphones.
