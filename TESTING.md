# Testing and Evidence

Last reviewed: 22 August 2026

Local engineering environment: macOS 26.5 arm64, 8 CPU cores, 8 GB RAM, Python 3.10.5. This is intentionally recorded as a non-target machine; BAIF's clean Windows 11/16 GB acceptance remains external.

## Automated release gate

- **77/77 tests pass** locally, including scanned-PDF OCR, BAIF-media evidence privacy, native macOS memory detection, ASR progress reporting, no-speech retry regression and onboarding delivery checks.
- **20 adversarial regressions** cover corrupt/malformed state, traversal/symlink escape, queue saturation/cancellation races, hostile password cost, bounded auth/session state, partial uploads, filename boundaries, oversized/duplicate archives and malformed manifests.
- Python compilation, frontend JavaScript syntax, `pip check`, repository secret/generated-data policy and package verification pass.
- Full tests complete in roughly eight seconds on the local machine; focused failure drill completes in roughly eight seconds.
- The GitHub Actions workflow repeats the suite on a clean Ubuntu runner with FFmpeg and English/Hindi/Marathi OCR data.
- The final release gate validates all local Markdown/HTML documentation links in addition to required guides, generated/private paths and credential patterns.

Run:

```bash
python -m py_compile $(git ls-files '*.py')
node --check frontend/app.js
python -m unittest discover -s tests -v
python -m pip check
python scripts/release_check.py
```

## Defects closed in the final adversarial pass

- A clean Windows setup exposed IndicTransToolkit's native C++ compiler requirement. The public prerequisites now name the exact **Desktop development with C++** workload, and the setup script checks for the MSVC x64/x86 toolchain before creating/downloading the environment instead of failing deep inside `pip`.
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

Peak benchmark memory was approximately 1.2 GB in the final run. Preferred terminology misses remain visible in `outputs/translation_reviewer_worksheet.csv`; English→Hindi terminology was the weakest seed result. These engineering scores are not IndicTrans2 readiness or bilingual approval.

## Real browser and media E2E

- Final real browser English→Hindi processing used NLLB CTranslate2 INT8 in **10.6 seconds**, preserved `25 kg`, `1800-123-456` and `BAIF`, and produced a verified nine-file package when optional speech was enabled for that test.
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
- Short probes identify Marathi narration. Whisper-small is error-heavy on this material. The original balanced large-v3/beam-3 configuration retained better speech but exceeded one hour on the 8 GB Mac and exposed an instruction-prompt echo on quiet sections. That configuration is no longer the laptop default; large-v3 remains available only through the explicit `quality` profile.
- The corrected `balanced` profile uses multilingual large-v3-turbo INT8 with deterministic single-beam decoding, VAD, no instruction prompt and no second full-file retry after an empty VAD result. It emits segment-level progress/ETA and stops at a configurable elapsed-time guard instead of continuing indefinitely.
- A 60-second excerpt of the real `401.1.mp4` completed ASR in **35.03 seconds** (0.584× real time). In the final audit, the full 5:43 audio reached translation after **237.0 seconds**, producing 33 timed segments.
- The final 22 August run passed the complete 5:43 application path on the 8 GB Mac in **259.61 seconds**: inspection, audio extraction, multilingual large-v3-turbo ASR, local NLLB CTranslate2 INT8 Marathi→Hindi translation, SRT/VTT and a verified offline ZIP. Runtime downloads and hosted translation were disabled; there were no warnings. The privacy-safe report excludes transcript/translation content. This is engineering completion evidence, not Marathi/Hindi linguistic approval.

## Failure and offline evidence

`python scripts/failure_drill.py` passes all six demo-day scenarios:

1. no-model privacy-safe setup error;
2. low-disk preflight refusal;
3. cancellation/completion race;
4. worker restart recovery;
5. corrupted/injected ZIP rejection; and
6. server-free `CONTENTS.html` playback/links.

Both the standard and approved review packages verify cleanly. Migration, backup/checksum restore, cleanup dry-run, redacted support bundle, model inventory, source manifest and SBOM generation also pass.

The final dependency audit closed the two pypdf denial-of-service advisories by upgrading to 6.15.0. Remaining findings are constrained to the PyTorch/Transformers model toolchain and the newest setuptools fix that conflicts with the pinned PyTorch compatibility bound. VaaniSetu never accepts user-supplied models/checkpoints and normal runtime downloads are disabled; these versions remain a post-demo compatibility-tested upgrade item rather than a rushed release change.

## Honest remaining proof

Preflight correctly marks this 8 GB Mac unsupported under BAIF's 16 GB production minimum and reports the intended IndicTrans2 checkpoints absent. The performance defect is closed on the real shortest video; the remaining external evidence is accepted/cached IndicTrans2 inventory, Hindi/Marathi reviewer sign-off and a clean Windows 11 baseline/full-BAIF-video run.
