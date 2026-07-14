# BAIF Delivery Compatibility

This project is aligned with the technical and delivery clarifications shared for the BAIF translation solution.

## Target Environment

Minimum target machine:

- CPU: Intel Core i5 11th Gen or equivalent, or AMD Ryzen 5 with 6+ cores
- RAM: 16 GB DDR4/DDR5 minimum
- Storage: 512 GB or 1 TB SSD/HDD
- OS: Windows 11
- Office suite: Microsoft Office 2020 or later for BAIF-side document workflows

Recommended production worker while remaining within the stated CPU-only constraint:

- 8+ CPU cores, 32 GB RAM, SSD storage
- Native Python environment with pinned dependencies and locally cached model assets
- No GPU dependency

## Connectivity

Internet access may be used at BAIF premises to download/cache open-source model weights and run translation on the local/on-prem worker. No paid APIs or usage-cost services are required. Generated outputs are designed for offline field playback or reuse.

## Enforced Input Limits

The backend enforces these limits before processing:

| Input | Supported formats | Duration | Size |
| --- | --- | --- | --- |
| Audio field recordings/training guides | MP3, AAC, M4A, WMA, OGG | 30 min | 50 MB |
| Audio lossless/uncompressed | WAV, FLAC | 30 min | 150 MB |
| Video agricultural demos | MP4, MOV, AVI, WMV, MKV, FLV, WebM | 15 min | 200 MB |
| Text | TXT, MD, TEXT | n/a | 10 MB |
| Documents / learning modules | PDF, DOCX, PPTX, XLSX, CSV, TSV | n/a | 50 MB |

Selectable-text PDFs are extracted directly. Scanned PDFs use automatic local Tesseract OCR when the OCR runtime is installed; otherwise the app gives a clear fallback instruction instead of returning an empty translation.

Video uploads are validated for 720p/1080p delivery. Higher-than-1080p uploads are rejected with a user-safe error.

## Outputs

Supported outputs:

- Source transcript
- Translated text
- Translated document TXT/Markdown/table exports
- SRT subtitles
- VTT subtitles
- Translated speech when a server or browser speech backend is available
- Optional captioned video and translated-audio video on full FFmpeg deployments
- ZIP bundle containing generated artifacts
- Job report JSON with model/backend metadata

## Storage And Reuse

Every completed job writes artifacts under `outputs/<job_id>/`. The app also appends a durable reuse ledger at `outputs/manifest.jsonl` with job metadata, language pair, backend metadata, and artifact references. BAIF can archive this folder for future reference and reuse.

## Handover Package

For final handover to BAIF IT, provide:

- Complete source repository
- `README.md`
- `DELIVERY_COMPATIBILITY.md`
- `OPEN_SOURCE_COMPLIANCE.md`
- `benchmarks/README.md`
- Reviewed benchmark manifests and quality reports
- Model setup command history
- Deployment environment variables
- Training walkthrough for recording, uploading, translating, exporting, and reusing outputs

## One-command Setup

Preferred BAIF worker setup:

```bash
python scripts/one_click_setup.py --profile balanced
```

Windows and macOS/Linux wrappers are available under `scripts/setup_baif_worker.ps1` and `scripts/setup_baif_worker.sh`.

## Quality Gates

Before final submission:

```bash
python -m py_compile $(git ls-files '*.py')
python -m unittest discover -s tests
python scripts/evaluate_quality.py
```

For the winning-quality backend, run reviewed BAIF audio through both Whisper large-v3 and IndicConformer, then choose the lower-WER backend per language.
