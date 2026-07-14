# VaaniSetu Implementation Roadmap

Implementation window: 15 July to 21 August 2026

## Product north star

A BAIF trainer should be able to turn English, Hindi, or Marathi learning content into a reviewable, reusable offline package without understanding models, codecs, or infrastructure. The office worker may use internet for setup, but processing must remain local by default and every field-facing output must work without internet.

## Definition of done

- Windows 11 setup succeeds on the stated i5/Ryzen 5, 16 GB RAM, CPU-only baseline.
- Text, recording, audio, video, PDF, scanned PDF, DOCX, PPTX, XLSX, CSV, and TSV inputs are handled gracefully within BAIF limits.
- All six English/Hindi/Marathi translation directions pass a BAIF-reviewed agriculture benchmark.
- Audio/video jobs produce reviewable transcripts, subtitles, translated speech, and offline packages.
- Admin and Authorised User roles are enforced, with admin approval and local session expiry.
- Jobs survive restart, expose real progress, support retry/cancellation, and never silently download models.
- Logs contain operational metadata but no source or translated content by default.
- Setup, backup, restore, troubleshooting, and handover are documented and rehearsed by someone other than the developer.

## Milestones

### M1: Reliable local foundation - complete

- Durable single-worker CPU queue with persisted job state and real progress.
- Automatic scanned-PDF OCR with local English, Hindi, and Marathi language data.
- Local faster-whisper transcription, license-documented NLLB evaluation translation, eSpeak speech, and FFmpeg media outputs.
- CTranslate2 INT8 NLLB evaluation fallback for responsive CPU inference while IndicTrans2 access is completed.
- Structured local logs, readiness checks, queue metrics, artifact path protection.
- Clean record, text, and upload workflows with selectable offline outputs.

Exit evidence: 28 automated tests pass; real captioned and translated-audio video package verified; all six language directions exercised.

### M2: Judged translation quality - 15 to 24 July

- Complete authorised download of distilled IndicTrans2 models after the model terms are accepted.
- Build a versioned BAIF agriculture set covering crops, livestock, soil, irrigation, measurements, names, and safety instructions.
- Have bilingual reviewers provide references and severity-tagged error notes.
- Measure chrF++, terminology accuracy, number/measurement preservation, untranslated rate, and human adequacy.
- Add a BAIF-approved glossary and deterministic protection for crop names, units, URLs, and proper nouns.
- Select backend and beam settings per direction using measured accuracy and CPU latency.

Exit evidence: signed benchmark report with per-direction quality, latency, memory, and known limitations.

### M3: Access and reusable library - 25 July to 1 August

- First-run local admin creation; Admin and Authorised User roles; admin approval and deactivation.
- Local sessions with expiry, password hashing, CSRF protection, and login throttling.
- Searchable translation library with source, direction, type, date, status, warnings, and output package.
- Retry, cancellation, deletion, storage usage, and safe cleanup controls.
- Review-and-correct workflow that preserves the approved final version separately from model output.

Exit evidence: role matrix tests, restart tests, and user journey test from approval through offline export.

### M4: Production and Windows hardening - 2 to 9 August

- Test the installer and launcher on a clean Windows 11 CPU-only machine.
- Bundle or install exact open-source FFmpeg, Tesseract, eSpeak, OCR data, and model versions with checksums.
- Validate every stated size/duration boundary and corrupted/unsupported inputs.
- Add disk-space preflight, low-space warnings, stale temporary-file cleanup, graceful shutdown, and backup/restore.
- Add job stage timings, failure counts, queue depth, storage health, and a support bundle with content redaction.

Exit evidence: clean-machine installation recording, 15-minute video stress run, 30-minute audio stress run, restart recovery, and resource report.

### M5: BAIF pilot and final polish - 10 to 18 August

- Observe BAIF trainers completing representative tasks without coaching.
- Fix confusing language, accessibility, keyboard, mobile, and low-connectivity handoff issues.
- Run bilingual quality review on real or approved representative material.
- Freeze dependencies and models; complete SBOM, licenses, privacy note, admin guide, user guide, and KT runbook.
- Prepare a deterministic demo package and a second-machine recovery rehearsal.

Exit evidence: BAIF UAT checklist, zero open critical/high defects, and signed release candidate.

### M6: Submission readiness - 19 to 21 August

- Re-run automated, security, benchmark, stress, and clean-install checks on the release candidate.
- Verify every claim in the presentation against captured evidence.
- Package source, installer, model/setup manifest, sample outputs, documentation, and handover materials.

## Current risks and controls

| Risk | Current truth | Control |
| --- | --- | --- |
| IndicTrans2 access | Official model repositories require account acceptance; not yet installed here. | Accept terms through the team account, record licenses/model revisions, then benchmark before claiming quality readiness. |
| Natural speech on CPU | eSpeak is reliable and compact but not natural enough for every learning module. | Benchmark approved Indic Parler/Piper options; retain eSpeak as the always-available fallback and disclose the active voice backend. |
| Field audio quality | Noise, dialect, code-switching, and agricultural names can reduce ASR accuracy. | Representative evaluation set, glossary, transcript review, confidence/warning cues, and editable approval step. |
| CPU throughput | One 15-minute video can occupy the worker for a meaningful period. | One model worker by default, persistent queue, measured profiles, batch translation, stage timings, and no unbounded parallelism. |
| Office document fidelity | Text extraction is reliable, but layout-perfect reconstruction is not guaranteed. | Preserve source, provide reviewable TXT/Markdown/table output, label best-effort formatting, and prioritise content correctness. |
| Windows packaging | Current development verification is on macOS. | A clean Windows 11 baseline test is mandatory before release; no production-ready claim until it passes. |

## Claim discipline

Demo and documentation must distinguish implemented, tested, planned, and blocked capabilities. Seed benchmarks are engineering checks, not BAIF quality evidence. A green readiness state means the worker can process content locally; the separate quality-readiness signal only turns green after all required IndicTrans2 models and benchmark evidence are present.
