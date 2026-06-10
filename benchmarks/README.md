# Quality Benchmarks

Quality claims for VaaniSetu must be backed by reviewed examples that represent BAIF field usage.

## Translation

`translation_seed.jsonl` covers every supported language direction. Replace and expand the seed with BAIF-reviewed sentences before final judging.

```bash
python scripts/evaluate_quality.py
```

Higher chrF++ is better.

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
