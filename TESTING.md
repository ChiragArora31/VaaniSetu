# Testing and Evidence

Last reviewed: 15 August 2026

Local engineering environment: macOS 26.5 arm64, 8 CPU cores, 8 GB RAM, Python 3.10.5. This is intentionally recorded as a non-target machine; BAIF's clean Windows 11/16 GB acceptance remains external.

## Automated release gate

- **74/74 tests pass** locally, including scanned-PDF OCR, BAIF-media evidence privacy, private-model preflight, no-speech prompt regression and onboarding delivery checks.
- **20 adversarial regressions** cover corrupt/malformed state, traversal/symlink escape, queue saturation/cancellation races, hostile password cost, bounded auth/session state, partial uploads, filename boundaries, oversized/duplicate archives and malformed manifests.
- Python compilation, frontend JavaScript syntax, `pip check`, repository secret/generated-data policy and package verification pass.
- Full tests complete in roughly eight seconds on the local machine; focused failure drill completes in roughly eight seconds.
- The GitHub Actions workflow repeats the suite on a clean Ubuntu runner with FFmpeg and English/Hindi/Marathi OCR data.
- A detached clean checkout at commit `791ec1c5` completed the documented minimal/no-model setup from an empty virtual environment, migration, all 69 tests in 4.28 seconds, and repository policy checks.

Run:

```bash
python -m py_compile $(git ls-files '*.py')
node --check frontend/app.js
python -m unittest discover -s tests -v
python -m pip check
python scripts/release_check.py
```

## Defects closed in the final adversarial pass

- Corrupt review records are quarantined and recovered instead of crashing the workflow.
- Corrupt/non-object job reports fail with an actionable response instead of breaking history/download views.
- Final approval atomically persists exactly the visible correction; duplicate saves/approvals no longer create false versions or memory rows.
- Typed and auto-detected same-language jobs are rejected before model work.
- Hostile unbroken text is hard-split at the configured translation boundary.
- Request throttling no longer trusts a caller-controlled forwarding header.
- Deleting or switching jobs cannot leave stale download/action targets in the UI.
- Recorder start/reset failures release microphone tracks, timers and object URLs.
- Low disk rejects a job before partial job directories are created.
- Missing FFmpeg subtitle support now leaves SRT/VTT available, removes partial video and emits one concise warning instead of raw diagnostics.

## Translation quality

The 12-sample, six-direction engineering gate passed with local **NLLB-200 CTranslate2 INT8**:

| Direction | Mean chrF++ | Critical preservation/script/backend failures |
| --- | ---: | ---: |
| English → Hindi | 37.20 | 0 |
| English → Marathi | 88.10 | 0 |
| Hindi → English | 48.55 | 0 |
| Hindi → Marathi | 74.66 | 0 |
| Marathi → English | 48.62 | 0 |
| Marathi → Hindi | 79.41 | 0 |

Peak benchmark memory was 964 MB. Preferred terminology misses remain visible in `outputs/translation_reviewer_worksheet.csv`; these engineering scores are not IndicTrans2 readiness or bilingual approval.

## Real browser and media E2E

- Real browser English→Hindi processing used NLLB CTranslate2 INT8 in **43.8 seconds** and preserved `25 kg` plus `1800-123-456`.
- Atomic human approval created the approved package; the same source then reused the approved correction in **0.6 seconds**.
- Text, public TXT/CSV batch upload, library reopen, keyboard tabs and 390×844 mobile layout passed with no duplicate IDs, unlabeled controls, horizontal overflow or console errors.
- The first-admin onboarding checklist and printable BAIF runbook pass desktop/mobile browser checks with actionable state transitions, no horizontal overflow and no console warnings/errors.
- Canonical public video: [Agriculture First](https://commons.wikimedia.org/wiki/File:Agriculture_First.webm), CC BY 3.0, attribution Indian Diplomacy; 239.501 seconds, 600×480, 16,491,593 bytes, SHA-256 `f3c679682e325e4b35c9586f9f2b161e192458de609fe615bb1588da14b3bd9a`.
- That video completed local Whisper transcription, English→Hindi translation, SRT/VTT, speech, translated-audio video and verified offline ZIP in **120 seconds**.
- The full boundary harness generated and inspected 1,800-second audio and 900-second 1920×1080 video with 16.97 MB peak harness memory.

## BAIF-supplied media evidence

- Eight BAIF MP4 videos were inspected in place; no BAIF media or transcript was copied into Git or the submission candidate.
- All 8/8 pass the enforced file-size, duration, resolution, audio-stream and video-stream checks.
- Total material is 70.55 minutes and 200,997,684 bytes; every file is 1920×1080 H.264/AAC and remains below the 15-minute/200 MB per-video boundary.
- Privacy-safe hashes and metadata are generated with `python scripts/validate_baif_samples.py PATH_TO_VIDEOS` into the ignored `outputs/baif_sample_validation.json` report.
- Short probes identify Marathi narration. Whisper-small is error-heavy on this material; large-v3 materially improves audible speech and also exposed an instruction-prompt echo on quiet sections. The balanced profile now uses large-v3, and the prompt echo is removed with a regression test. Full-video quality still requires the target Windows run and Marathi transcript review before output approval.
- The shortest real video (`401.1.mp4`, 5:43) was also started through the complete local large-v3 pipeline on this 8 GB Mac with hosted translation and runtime downloads disabled. Transcription remained active inside CTranslate2 at the one-hour cutoff (about 10.5x wall-clock real time; roughly 4.4 GB peak process footprint), so the run was stopped without claiming a package or quality pass. This is an honest performance failure on a machine that preflight rejects, and makes the measured 16 GB Windows completion test a release gate rather than a formality.

## Failure and offline evidence

`python scripts/failure_drill.py` passes all six demo-day scenarios:

1. no-model privacy-safe setup error;
2. low-disk preflight refusal;
3. cancellation/completion race;
4. worker restart recovery;
5. corrupted/injected ZIP rejection; and
6. server-free `CONTENTS.html` playback/links.

Both the standard and approved review packages verify cleanly. Migration, backup/checksum restore, cleanup dry-run, redacted support bundle, model inventory, source manifest and SBOM generation also pass.

## Honest remaining proof

Preflight correctly marks this 8 GB Mac unsupported under BAIF's 16 GB minimum and reports the intended IndicTrans2 checkpoints absent. The only external evidence still required is accepted/cached IndicTrans2 inventory, Hindi/Marathi reviewer sign-off and a clean Windows 11 baseline/full-BAIF-video run.
