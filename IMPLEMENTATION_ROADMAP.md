# VaaniSetu 72-Hour Implementation Sprint

Sprint window: Wednesday 15 July 2026, 08:00 IST to Friday 17 July 2026, end of day

Last updated: Thursday 16 July 2026, 09:00 IST

## Mission

Ship a release candidate that a BAIF trainer can use to turn English, Hindi, or Marathi learning content into a reviewed, reusable offline package without understanding models, codecs, or infrastructure. The office worker may use internet during controlled setup; normal jobs remain local and every field-facing output works without internet.

Speed matters. So do evidence, privacy, license compliance, and honest readiness. A feature counts as complete only when its acceptance checks pass and the result is pushed to `origin/main` with green CI.

Organiser implementation-phase guidance received on 15 July adds an explicit assessment lens: the submission must be a production-ready web application deployable in the BAIF environment, aligned to agreed access, dependency, and operational constraints, plus a handover pack covering solution overview, assumptions/scope, architecture or process flow, setup/install, access/dependencies, operating guide including support model, and known limitations/risks.

## Live Scoreboard

| Workstream | Start | Friday target | Current evidence |
| --- | ---: | ---: | --- |
| Local translation and media foundation | 85% | 100% | Durable queue, OCR, six directions, TTS, subtitles, captioned/dubbed video, offline ZIP |
| Judged translation quality | 90%* | 90%* | Versioned agriculture glossary, invariant protection, 12-sample/six-direction chrF++/terminology/script/preservation/latency/memory gate passing on local NLLB; bilingual approval and IndicTrans2 access pending |
| Access, review, and reusable library | 100% | 100% | Roles/auth, durable review/version/approval, safe delete, cooperative cancel, retry, corrected-text persistence, searchable library, exact approved-memory reuse and opt-out |
| Production and Windows hardening | 90%* | 90%* | Cross-platform preflight, disk guard, stage timings, metrics, cleanup, migration, full backup/restore, redacted support bundle, model inventory; clean Windows proof pending |
| UX, accessibility, and field handoff | 100% | 100% | Desktop/mobile browser flow, structural accessibility audit, long Indic content, retry/cancel, integrity-signed offline packages, full boundary stress harness and UAT scripts verified |
| Evidence, documentation, and handover | 100% | 100% | Complete handover index, user/admin/privacy/support/troubleshooting/UAT/release guides, SBOM/source evidence generator and CI release-policy gate |
| Overall release readiness | 95%* | 95%* | Clean Ubuntu CI is green with all 43 tests including OCR, plus real audio/video E2E, 12-sample quality gate, full stress, browser E2E, and operations recovery proof; external model/reviewer/Windows evidence remains |

`*` External acceptance can only reach 100% after the team accepts the official model terms, bilingual reviewers approve quality, and a clean Windows 11 machine is available. Everything not dependent on those people or machines is targeted for completion by Friday night.

## Completion Audit — 16 July 2026

- [x] Text, audio, video, TXT, PDF, DOCX, PPTX, XLSX, CSV, and TSV success/failure/limit paths are covered by automated or real E2E evidence; scanned-PDF OCR executes in Linux CI with Tesseract.
- [x] All six language directions run through a reproducible gate covering chrF++, terminology, invariant preservation, target script, unchanged output, latency, memory, and backend provenance.
- [x] IndicTrans2 authenticated setup and per-direction readiness are implemented and cannot be confused with NLLB fallback readiness.
- [ ] External: Hindi and Marathi reviewers approve the seed/corrections and production terminology.
- [ ] External: the team account accepts and caches all three intended IndicTrans2 checkpoints.
- [x] Auth/RBAC, review/version/approval, library/search, retry, cooperative cancellation, safe delete, storage visibility, and exact approved-memory reuse/opt-out are implemented and tested.
- [x] Durable jobs, restart interruption handling, one-worker default, stage timings, failure/queue/disk metrics, no silent model download, and no hosted service by default are implemented.
- [x] Windows-oriented preflight, pinned dependencies, revision-aware model setup, checksummed inventory, disk guard, cleanup, migration, backup/restore, and privacy-safe support bundle are implemented.
- [ ] External: clean Windows 11 CPU-only installation/preflight/UAT evidence is recorded.
- [x] Desktop/mobile/keyboard structure, labelled controls, focus/target rules, reduced motion, long Indic text, loading/error/retry/cancel/empty states, offline integrity and persona UAT are implemented/tested.
- [x] 30-minute audio and 15-minute 1080p video boundary stress harness passes; real local audio and full video output E2E pass.
- [x] Dependency/model governance, SBOM/source evidence generation, user/admin/privacy/troubleshooting/support/KT/UAT/release documents, and claim reconciliation are complete.
- [x] Release administration: the release slice and clean-install dependency fix are pushed to `origin/main`; GitHub CI run #6 is green.
- [ ] External release governance: create the release tag only after the model-access, bilingual-review, and clean-Windows acceptance boxes are complete.

## Friday Definition Of Done

- Text, recording, audio, video, PDF, scanned PDF, DOCX, PPTX, XLSX, CSV, and TSV paths pass success, limit, and failure tests.
- All six English/Hindi/Marathi directions are benchmarked for quality, latency, terminology, numbers, units, names, and unchanged text.
- The intended IndicTrans2 path is installable and readiness-checked; model access blockers are explicit and cannot be mistaken for production readiness.
- Admin and Authorised User roles, first-run admin setup, approval/deactivation, secure sessions, CSRF protection, and login throttling work locally.
- Trainers can search previous work, inspect warnings, edit a translation, approve a final version, retry/cancel jobs, download outputs, and delete data safely.
- Jobs survive restart, show stage timings, respect one-worker CPU limits, and never silently download models or call hosted translation services.
- Windows setup has dependency/model preflight, checksums, disk checks, cleanup, backup/restore, and a support bundle with content redaction.
- A release candidate passes automated tests, security checks, browser/mobile/accessibility checks, stress tooling, documentation review, and GitHub CI.

## Six Shipping Sessions

### Wednesday 08:00 - Secure access and role enforcement

Deliver:

- First-run admin creation with no default credentials.
- Password hashing, secure local sessions, expiry, logout, CSRF protection, and login throttling.
- Admin and Authorised User roles with approval, deactivation, and route-level enforcement.
- Minimal, calm sign-in/onboarding UI and role-aware navigation.
- Auth persistence, role matrix, brute-force, session-expiry, and restart tests.

Exit gate: an unapproved user cannot process or download content; an admin can approve a user; all auth tests and CI pass.

### Wednesday 20:00 - Reusable library and human review

Deliver:

- Search/filter by language, input type, date, status, and filename.
- Job details with transcript, translation, warnings, backend, timings, and artifacts.
- Edit, approve, and version corrected translations without overwriting raw model output.
- Retry, cooperative cancellation, safe deletion, and storage-usage controls.
- Translation-memory reuse for exact approved segments, with visible provenance and opt-out.

Exit gate: a trainer can move from an old job to an approved corrected offline package without touching the filesystem.

### Thursday 08:00 - Judged quality system

Deliver:

- Versioned agriculture glossary covering crops, livestock, soil, irrigation, safety, measurements, and BAIF terminology.
- Deterministic protection and validation for numbers, units, URLs, names, and glossary terms.
- Six-direction benchmark runner with chrF++, terminology accuracy, preservation failures, untranslated rate, latency, and memory.
- IndicTrans2 authenticated setup/readiness path and per-direction backend selection.
- Reviewer worksheet and severity-tagged error workflow; no seed result presented as BAIF approval.

Exit gate: one command produces a reproducible per-direction report and blocks a release when preservation or script checks fail.

### Thursday 20:00 - CPU and Windows production hardening

Deliver:

- Clean Windows setup preflight for Python, FFmpeg, Tesseract, eSpeak, disk, RAM, model files, ports, and permissions.
- Pinned dependency/model manifest with source, license, revision, size, and checksum.
- Low-space guardrails, stale-temp cleanup, graceful shutdown, backup, restore, and migration commands.
- Stage timings, failure counters, queue depth, disk health, and privacy-safe support bundle.
- Corrupted upload, ZIP/path traversal, oversized input, missing binary/model, and restart recovery tests.

Exit gate: a non-developer can diagnose readiness and recover local data using documented commands without exposing BAIF content.

### Friday 08:00 - Stress, UX, accessibility, and offline proof

Deliver:

- Repeatable 30-minute audio and 15-minute 1080p video stress harness with CPU, memory, disk, and stage-time report.
- Mobile and desktop browser tests for record, text, upload, review, library, and download flows.
- Keyboard navigation, focus, labels, contrast, long Hindi/Marathi text, loading, empty, failure, retry, and offline states.
- Offline package integrity manifest and verifier; prove playback and documents need no server connection after download.
- UAT scripts for trainer, admin, and field recipient personas.

Exit gate: no critical/high issue remains open; unsupported or failed work always has an actionable, non-technical recovery path.

### Friday 20:00 - Release candidate and handover

Deliver:

- Freeze dependency/model versions and generate license/SBOM evidence.
- Re-run unit, integration, security, format, media, benchmark, stress, browser, and clean-setup checks.
- Reconcile every README/deck claim with implemented evidence and known limitations.
- Complete user guide, admin guide, privacy note, troubleshooting, backup/restore, KT runbook, and release checklist.
- Package source, setup, model manifest, approved samples, benchmark report, and offline demonstration outputs.
- Tag the release candidate after green GitHub CI and confirm local/main synchronization.

Exit gate: the repository can be handed to another team member who can install, operate, diagnose, and demonstrate it from documentation.

## Parallel Blockers Requiring Chirag Or BAIF

These do not pause independent engineering work:

1. Accept the official AI4Bharat IndicTrans2 model access conditions in the team Hugging Face account and provide authenticated local access without sharing the token in chat or Git.
2. Identify at least one Hindi and one Marathi reviewer for the agriculture benchmark and corrected terminology list.
3. Provide access to a clean Windows 11 CPU-only machine matching the BAIF baseline for final installation evidence.
4. Obtain approved representative BAIF material when possible; public agriculture material remains the non-confidential engineering test source.

## Brownie-Point Queue

Only start these after the critical session exit gates are green:

- Approved translation memory that reduces repeated work and shows where reused text came from.
- Glossary coverage insights and a preflight warning before processing terminology-heavy content.
- Side-by-side source, machine output, corrected output, and subtitle timing review.
- Offline package integrity verifier with checksums and a human-readable contents page.
- Batch processing for a folder of learning modules while preserving the one-model-worker CPU limit.
- Exportable, privacy-safe impact dashboard: minutes translated, languages, reuse rate, correction rate, and processing time.

## Session Ledger

Every 08:00 and 20:00 session appends an entry here before pushing:

| Session | Completed | Evidence | Blockers | Next three priorities | Overall |
| --- | --- | --- | --- | --- | ---: |
| 15 Jul 01:13 planning reset | Compressed roadmap to 72 hours; created twice-daily execution automation; established hard exit gates and external blocker lane | Automation scheduled for 08:00/20:00 IST through Friday; `main` began synchronized with green CI | IndicTrans2 acceptance, bilingual reviewers, Windows machine | Auth/RBAC; review library; quality harness | 42% |
| 15 Jul 01:39 secure access slice | Added no-default first-run admin setup, PBKDF2 password hashes, HttpOnly local sessions, session expiry, CSRF checks, login throttling, pending user registration, admin approval/deactivation, protected content routes, admin metrics gate, and simple role-aware UI | `python -m py_compile` for tracked Python passed; `node --check frontend/app.js` passed; full unittest suite passed 32 tests; HTTP smoke on `127.0.0.1:8787` verified setup, 401 unauthenticated job, 403 missing CSRF, pending login block, approval, authorised login, and protected history | Browser screenshot tooling unavailable in this runtime; Tesseract integration test skipped locally; CI still pending after push; external IndicTrans2 acceptance, bilingual reviewers, and Windows machine remain | Reusable library and review workflow; retry/cancel/delete controls; corrected-output approval and translation memory | 48% |
| 15 Jul 14:01 review-library slice | Captured organiser implementation/handover guidance; added durable review store, corrected translation versions, approval state, approved corrected package, exact approved-translation memory reuse with opt-out request flag, searchable library endpoint, storage usage, retry, cooperative cancel, safe delete including memory cleanup, queue/output-ID resolution, and minimal UI for searchable library plus human review | `.venv/bin/python -m py_compile api.py app.py core/*.py scripts/*.py` passed; `node --check frontend/app.js` passed; full unittest suite passed 35 tests with 1 OCR dependency skip; HTTP smoke on isolated `127.0.0.1:8791` verified first admin setup, queued preview text job, queue/output job lookup, library search, correction save, approval, and approved package artifact visibility | Tesseract/PDF OCR integration dependency still skipped locally; browser screenshot/mobile verification still not available in this runtime; GitHub CI pending after push; external IndicTrans2 acceptance, bilingual reviewers, and Windows machine remain | Finish review UX edge cases and delete/retry controls in UI; start judged quality glossary/protection/benchmark gate; draft handover pack aligned to organiser criteria | 56% |
| 16 Jul 09:00 release-engineering slice | Added invariant-safe translation and versioned agriculture glossary; six-direction quality/reviewer gate; integrity ZIP/verifier; retry/cancel/delete UX and corrected-text persistence; stage timings/disk metrics; preflight/cleanup/migrate/backup/restore/support/model inventory; pinned dependencies/revisions; stress harness; security headers; complete handover pack | Python 3.10 compile and frontend syntax passed; 43 tests passed locally with the OCR dependency skip and all 43 passed in clean Ubuntu CI including OCR; 12-sample six-direction NLLB engineering gate passed with no preservation/script/backend failure; real audio and full video E2E passed; 30-minute audio/15-minute 1080p stress passed; desktop/mobile browser auth/text/review/approve/retry/cancel/accessibility checks passed with no console errors; backup/restore/support and offline package verification passed | External IndicTrans2 terms/model cache, bilingual approval, and clean Windows 11 proof remain; this Mac correctly fails production preflight for low disk/missing gated assets | Obtain three external acceptances; run clean Windows UAT; tag release candidate | 95% |

## Operating Rules

- Finish the highest-risk required capability before decorative additions.
- Keep at most one model-heavy job active by default on the 16 GB CPU baseline.
- Never log raw source or translated content by default.
- Never commit credentials, model weights, generated media, virtual environments, or private BAIF data.
- Commit coherent slices with meaningful messages; fetch before push; never overwrite teammate history.
- A session is incomplete until tests pass, the ledger is updated, commits are pushed, and GitHub CI is checked.
- Implemented, tested, externally validated, blocked, and planned must remain visibly distinct.
