# Release Engineering Test Evidence — 16 July 2026

Environment: macOS 26.5 arm64, 8 CPU cores, 8 GB RAM, Python 3.10.5. This is engineering evidence, not the required clean Windows 11 acceptance run.

## Automated and policy checks

- Python compile: passed for all tracked/new Python files.
- Frontend JavaScript syntax: passed with bundled Node.js.
- Unit/integration/security/format suite: 43 passed; scanned-PDF OCR skipped locally because Tesseract is absent. GitHub CI installs Tesseract plus English/Hindi/Marathi data and runs the same test.
- Clean-install GitHub CI: run #6 passed on Ubuntu with the pinned dependency set and all 43 tests, including scanned-PDF OCR.
- Winning-sprint regression: 47 tests passed locally after adding privacy-safe impact calculations, glossary preflight, hardware recommendation and offline landing-page playback/link coverage; clean CI confirmation follows the push.
- Release/secret/generated-data policy: passed.
- Offline package verifier: passed on real video job `466ad9a8fd58`; deliberate tampering is rejected by automated test.

## Translation quality

`scripts/evaluate_quality.py --offline` passed its 12-sample, six-direction engineering gate using `NLLB-200 CTranslate2 INT8`: no preservation, script, untranslated, or backend failures; every direction exceeded chrF++ 35. The report and reviewer worksheet remain under `outputs/`. Preferred terminology misses remain visible, especially English→Hindi; the report is not bilingual approval or IndicTrans2 production evidence.

## Real media E2E

- Audio job `03741573d403`: local Whisper transcribed Hindi “हेलो किसान पानी”; local NLLB returned “Hello farmer water”; TXT/SRT/VTT/report/integrity ZIP generated.
- Video job `466ad9a8fd58`: 1280×720 Hindi speech video produced transcript, translation, SRT/VTT, WAV/MP3, captioned MP4, translated-audio MP4, report, and verified ZIP with no warnings.
- Full boundary harness: generated/inspected 1,800-second WAV and 900-second 1920×1080 MP4; passed while recording generation/inspection timings, peak memory, CPU count, and disk bytes. The harness validates boundaries; representative spoken content supplies the ASR/translation E2E evidence above.

## Browser E2E

In the in-app browser against an isolated Python 3.10/local-model worker:

- First-admin setup and authenticated workspace passed.
- English→Hindi text with `25 kg` passed local translation and invariant preservation.
- Correction v1/v2 save, persistence after reload, approval v2, approved package, and library reopen passed.
- Retry completed and increased the library count; cooperative cancellation displayed “Cancellation requested” during the current model batch.
- 390×844 responsive audit had no horizontal overflow; desktop/mobile controls were labelled, IDs unique, no positive tab indices or unnamed buttons, reduced-motion CSS was present, and browser console errors/warnings were empty.
- Testing found and fixed the correction editor reverting visually to machine output after save/approve.
- The new result trust card and impact dashboard rendered correctly on desktop and 390×844 mobile. The audit found no horizontal overflow, duplicate IDs, unlabeled controls, unnamed buttons, positive tab indices, or console warnings/errors. Multi-file selection is enabled and deliberately capped at ten sequential items.
- Browser job `192c1516caeb` verified English→Marathi agriculture-term suggestions with an explicit bilingual-review warning, one-word correction highlighting, save/approval, and the journey advancing to **Take offline**. Nested terminology is resolved longest-first so “drip irrigation” is not double-counted as “irrigation.”

## Winning-sprint offline proof

Real browser job `9deb1b6398d4` produced a checksum-valid ZIP. Its server-free `CONTENTS.html` exposed the offline badge, direct translated-text link, integrity instructions and an embedded audio player. The landing page itself is now checksummed, and the verifier rejects unexpected injected files. The impact endpoint/dashboard reported one completed English→Hindi job without exposing source or translated content.

## Operational recovery

Migration, backup, checksum validation, forced restore to an isolated runtime, cleanup dry-run, redacted support-bundle generation, model-file checksum inventory, and source/SBOM evidence generation passed. Production preflight correctly fails this Mac because it has 8 GB RAM, low disk, no Tesseract binary, and no accepted/cached production IndicTrans2 set.

The hardware recommender independently classified this 8 GB machine as unsupported, keeps one worker, and explains the confirmed 16 GB BAIF minimum. Automated tests cover unsupported, balanced-baseline and quality-headroom recommendations.
