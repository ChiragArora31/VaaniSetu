# VaaniSetu Winning Roadmap

Last updated: 16 July 2026
Implementation window: 9 July–14 August 2026
Finals (tentative): 17 August 2026

## 1. The goal

Deliver the best production-ready, open-source translation workflow for BAIF's CPU-only Windows office environment. A trainer should be able to translate English, Hindi or Marathi learning content, review it, and send a trustworthy package for offline field use without needing technical knowledge.

The complete organiser alignment audit is in [HACKATHON_REQUIREMENTS_AUDIT.md](HACKATHON_REQUIREMENTS_AUDIT.md).

## 2. Non-negotiable organiser rules

- Run on BAIF's existing Windows 11, 16 GB RAM, CPU-only infrastructure; no GPU assumption.
- Require no paid licence or software purchase by BAIF.
- Translation happens at the BAIF office. Downloaded outputs must work offline in the field.
- Support audio up to 30 minutes and video up to 15 minutes/200 MB at 720p or 1080p.
- Preserve previous translations for reference and reuse.
- Use public agriculture/crop material for testing unless BAIF supplies approved samples.
- Protect confidential content and follow the personal-laptop/DLP guidance.
- Provide production-ready source, deployment guidance, handover documents and KT material.
- Optimise for the five evaluation pillars: impact, production readiness, usability, safety/fairness/inclusivity and zero cost.

## 3. What is already achieved

### Core trainer journey — complete

- [x] Text, microphone recording, audio, video, TXT, PDF/scanned PDF, DOCX, PPTX, XLSX, CSV and TSV inputs.
- [x] English, Hindi and Marathi in all six translation directions.
- [x] Local transcription, translation, subtitles, speech, captioned video and translated-audio video.
- [x] Exact organiser size, duration and resolution limits with non-technical recovery messages.
- [x] Integrity-protected offline ZIP outputs and a reusable local library.

### Quality, trust and reuse — complete

- [x] Versioned agriculture glossary, numbers/units/URL/email protection, script checks and unchanged-output detection.
- [x] Reproducible six-direction quality report with chrF++, terminology, latency, memory and backend provenance.
- [x] Side-by-side source/machine output, correction versions, approval and approved corrected packages.
- [x] Exact approved translation-memory reuse with visible provenance and opt-out.

### Production readiness — complete

- [x] First-admin setup, approved users, secure sessions, CSRF protection and login throttling.
- [x] Durable CPU queue, one heavy worker by default, restart recovery, retry, cancellation and safe deletion.
- [x] Windows setup/preflight, dependency/model inventory, disk guard, cleanup, migration, backup/restore and privacy-safe support bundle.
- [x] Stage timings, queue/failure/storage metrics, pinned dependencies, release policy, SBOM and source manifest.

### Evidence and handover — complete

- [x] 43-test clean Ubuntu CI including scanned-PDF OCR.
- [x] Real audio/video E2E, six-direction quality gate, browser/mobile/accessibility checks, recovery checks and full boundary stress harness.
- [x] User, admin, privacy, troubleshooting, support, UAT, release and handover guides.
- [x] Every claim distinguishes engineering evidence from external approval.

## 4. Current winning sprint — work we can do ourselves

These items improve judge-visible impact without breaking scope or depending on external access.

### P0 — make the value obvious

- [x] Add a privacy-safe impact dashboard: completed work, media minutes, language directions, approval rate, reuse, success rate and storage.
- [x] Add a clear trust/provenance card to every result: backend, model profile, processing time, human-review state and warnings.
- [x] Turn the offline `CONTENTS.html` into a field-friendly landing page with direct document links and embedded audio/video playback.

### P1 — multiply trainer productivity

- [x] Add multi-file batch selection and sequential queueing while preserving the one-model-worker CPU limit.
- [x] Show a batch summary with completed/failed files and direct review links for each completed result.
- [x] Add privacy-safe impact export for reporting and demonstration.

### P2 — polish and proof

- [x] Re-run browser E2E for the new dashboard controls, batch affordance, trust card and offline package.
- [x] Add tests for impact calculations, queue-safe behaviour and offline landing-page links/players.
- [x] Update user/admin/handover documents and record final evidence.

## 5. Brownie-point queue

### Build now

- [x] Glossary coverage insights before processing terminology-heavy content.
- [x] Review-difference highlighting between machine and corrected output.
- [x] Downloadable impact report with no raw BAIF content.
- [x] A guided three-step demo mode: translate → review → take offline.

### Build after the current winning sprint

- [ ] Admin-managed glossary overlay with safe JSON/CSV import, version history and rollback.
- [ ] Duplicate/near-duplicate detection to suggest reusable approved content before processing.
- [ ] Batch-level pause/resume and exportable batch manifest.
- [x] Hardware-profile recommender based on preflight RAM/CPU and the confirmed BAIF baseline.

### Avoid unless the panel asks

- Cloud translation dependencies, paid APIs, GPU-only features, live field translation, generic chatbots, unrelated analytics, or decorative features that weaken the core trainer journey.

## 6. Deferred external list — do last

- [ ] Team account accepts and caches the intended IndicTrans2 checkpoints.
- [ ] Hindi and Marathi reviewers approve representative translations and terminology.
- [ ] Clean Windows 11 CPU-only installation/preflight/UAT evidence is recorded.
- [ ] Approved BAIF sample content is used if BAIF supplies it.
- [ ] Release tag and BAIF IT KT session are completed after the three acceptance gates above.

## 7. Current evidence snapshot

- Main branch and GitHub CI are green.
- 47 automated tests pass locally; CI runs the same suite with OCR enabled.
- The 12-sample/six-direction engineering quality gate has no preservation, script, untranslated or backend-provenance failure.
- Real audio and complete video output flows pass.
- The 30-minute audio and 15-minute 1080p stress boundaries pass.
- Desktop and 390×844 mobile browser journeys, including the impact and trust surfaces, pass without console errors or horizontal overflow.
- No known critical/high engineering issue is open.

## 8. Definition of “ready to win”

The core trainer journey can be demonstrated end-to-end in minutes; judges can see quantified impact and safety evidence; every output is reviewable and usable offline; the system remains honest about model and human approval; setup/recovery needs no developer; and every organiser constraint has a direct evidence link.
