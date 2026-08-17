# Compatibility

## Target environment

Confirmed minimum:

- Windows 11
- Intel Core i5 11th Gen/equivalent or AMD Ryzen 5 with 6+ cores
- 16 GB DDR4/DDR5 RAM
- 512 GB or 1 TB SSD/HDD
- Microsoft Office 2020 or later for BAIF-side document workflows
- No GPU assumption

VaaniSetu keeps one heavy model worker by default. Preflight recommends `balanced` on the minimum baseline, permits `quality` only with measured headroom (normally at least 32 GB RAM/eight cores), and rejects systems below 16 GB.

macOS arm64 can be used for engineering and team testing with Python 3.10/3.11, FFmpeg and Tesseract. It is not the formal BAIF production target: an 8 GB Mac completed the corrected balanced pipeline on the shortest real BAIF sample, but production acceptance must still run on the Windows baseline above. Use the developer setup in [README.md](README.md), then validate private samples with `python scripts/validate_baif_samples.py PATH_TO_VIDEOS --process-shortest`; keep generated content under ignored `outputs/`.

Internet may be used at BAIF premises during controlled installation/model caching. Normal jobs run locally without paid APIs or silent model downloads. Translation happens at the office; exported packages work offline in the field.

## Enforced inputs

| Input | Formats | Duration | Size |
| --- | --- | ---: | ---: |
| Compressed audio | MP3, AAC, M4A, WMA, OGG | 30 min | 50 MB |
| Lossless/uncompressed audio | WAV, FLAC | 30 min | 150 MB |
| Agricultural video | MP4, MOV, AVI, WMV, MKV, FLV, WebM | 15 min | 200 MB |
| Text | TXT, MD, TEXT | n/a | 10 MB |
| Documents/tables | PDF, DOCX, PPTX, XLSX, CSV, TSV | n/a | 50 MB |

Video is limited to 720p/1080p; higher resolutions are rejected. Selectable PDFs are read directly. Scanned PDFs use local Tesseract OCR when ready and otherwise return an actionable error.

## Outputs

- Source transcript and translated text
- Reviewable TXT/Markdown/table exports
- SRT and VTT subtitles
- Optional translated speech, captioned video and translated-audio video
- Job report containing backend/provenance, warnings and artifact metadata
- Integrity-protected ZIP with a server-free landing page, direct links and audio/video playback

Completed jobs, review versions and approved-memory records remain under the configured worker storage until BAIF retention/cleanup removes them. Multi-file batches are sequential and do not increase the one-worker CPU budget.

## Acceptance

Engineering compatibility is proven by automated limits, browser/media E2E and full boundary stress tests. Final production acceptance still requires:

1. accepted/cached IndicTrans2 checkpoints and model inventory;
2. Hindi/Marathi reviewer sign-off; and
3. clean Windows 11 baseline installation, preflight and UAT.

Setup and acceptance commands are maintained in [README.md](README.md), [SETUP.md](SETUP.md), [OPERATIONS.md](OPERATIONS.md) and [ACCEPTANCE.md](ACCEPTANCE.md).
