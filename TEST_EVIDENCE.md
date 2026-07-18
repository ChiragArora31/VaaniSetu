# Test Evidence

Last reviewed: 18 July 2026
Local engineering environment: macOS 26.5 arm64, 8 CPU cores, 8 GB RAM, Python 3.10.5. This is not the required Windows 11 acceptance machine.

## Automated release gate

- 65 tests pass in clean Ubuntu CI, including scanned-PDF OCR with English/Hindi/Marathi Tesseract data.
- Locally, 64 tests pass and only OCR is skipped because Tesseract is absent.
- 18 adversarial regressions cover malformed/corrupt state, traversal and symlink escape, queue saturation and cancellation races, hostile password cost, bounded login/session state, partial uploads, filename boundaries, ambiguous/oversized archives and malformed manifests.
- The adversarial module passed 25 consecutive randomized-hash runs—450 focused executions—with no race flake.
- Branch-inclusive diagnostic coverage across the modified safety boundary was 74%; deterministic critical modules measured 72–94% without mocking model-runtime work merely to inflate line coverage.
- Python compilation, frontend syntax, secret/generated-data policy and package verification pass.

The latest code-bearing verification release is `787f1f87`; [GitHub CI run 29599126528](https://github.com/ChiragArora31/VaaniSetu/actions/runs/29599126528) completed successfully.

## Defects closed by adversarial testing

- Cancellation now wins if it races with task completion.
- Restart recovery rejects mismatched/path-like queue identities and malformed records.
- Non-JSON/non-finite results cannot corrupt durable terminal state.
- Malformed auth records are isolated; PBKDF2 cost, failure-cache size and sessions per user are bounded.
- Interrupted uploads leave no partial file; control-character and excessive filenames are handled safely.
- Package and Office readers reject duplicate/oversized members before ambiguous or excessive reads.
- Artifact access is constrained to a direct child of the configured output root.

## Quality and media

- The 12-sample, six-direction engineering gate passed with local NLLB-200 CTranslate2 INT8: no preservation, script, unchanged-output or backend-provenance failure; every direction exceeded chrF++ 35.
- The report is engineering evidence, not IndicTrans2 readiness or bilingual approval. Preferred terminology misses—especially English→Hindi—remain visible for reviewers.
- Real Hindi audio produced a transcript, English translation, subtitles, report and verified package.
- Real Hindi video produced transcript, translation, subtitles, speech, captioned video, translated-audio video, report and verified package.
- The boundary harness generated and inspected a 1,800-second WAV and 900-second 1920×1080 MP4 successfully.

## Browser and offline journey

- First-admin setup, pending-user rejection, approval, sign-in and CSRF controls passed.
- Text translation, invariant preservation, correction versions, approval, approved-memory reuse, retry/cancel/delete and library reopen passed.
- Impact, trust/provenance, batch and glossary/difference surfaces rendered correctly on desktop and 390×844 mobile.
- The accessibility audit found no horizontal overflow, duplicate IDs, unlabeled controls, unnamed buttons, positive tab indices or console errors/warnings.
- A real ZIP opened through its server-free `CONTENTS.html`, exposed direct files and media playback, verified cleanly and rejected deliberate tampering/injected files.

## Operations and remaining proof

Migration, backup/checksum validation, forced restore, cleanup dry-run, redacted support bundle, model inventory and source/SBOM generation passed. Preflight correctly marks this 8 GB Mac unsupported under BAIF's confirmed 16 GB minimum.

External evidence still required: the accepted/cached IndicTrans2 inventory, Hindi/Marathi reviewer sign-off and a clean Windows 11 baseline run.
